from datetime import timedelta, datetime, timezone
import logging
import secrets
import stripe
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from ..models import Order, PaymentEvent, PaymentAttempt, utcnow
from .commerce import expire_order

log = logging.getLogger("shop.payments")


def create_checkout(db, order, settings):
    if order.status != "pending_payment":
        raise HTTPException(409, "El pedido no admite otro pago")
    if order.payment_intent_id and not order.checkout_session_id:
        raise HTTPException(409, "Este pedido ya tiene un intento de pago directo")
    if order.checkout_url:
        return order.checkout_url
    if settings.payment_mode == "demo":
        session_id = "cs_demo_" + secrets.token_urlsafe(18)
        url = f"{settings.public_web_url}/checkout/demo?order={order.id}"
    else:
        try:
            stripe.api_key = settings.stripe_secret_key
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[
                    {"price_data": {"currency": "eur", "product_data": {"name": i.name}, "unit_amount": i.price_cents}, "quantity": i.quantity}
                    for i in order.items
                ],
                success_url=settings.public_web_url + "/checkout/success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.public_web_url + f"/checkout/cancel?order={order.id}",
                metadata={"order_id": str(order.id)},
                expires_at=int((datetime.now(timezone.utc) + timedelta(minutes=31)).timestamp()),
                idempotency_key=f"checkout-{order.id}",
            )
            session_id, url = session.id, session.url
        except stripe.StripeError:
            log.warning("El proveedor de pagos no está disponible", extra={"event_action": "payment.provider_error"})
            raise HTTPException(502, "No se pudo abrir Stripe. Puedes reintentar desde tus pedidos")
    order.checkout_session_id = session_id
    order.checkout_url = url
    order.payment_expires_at = utcnow() + timedelta(minutes=32)
    db.add(PaymentAttempt(order_id=order.id, operation_key=f"checkout-{order.id}", provider_id=session_id, status="created", amount_cents=order.total_cents))
    db.commit()
    return url


def create_intent(db, order, settings):
    if order.status != "pending_payment" or order.checkout_session_id:
        raise HTTPException(409, "El pedido ya usa otro flujo de pago")
    if order.payment_intent_id:
        return {"payment_intent_id": order.payment_intent_id}
    if settings.payment_mode == "demo":
        pid = "pi_demo_" + secrets.token_urlsafe(12)
    else:
        stripe.api_key = settings.stripe_secret_key
        try:
            intent = stripe.PaymentIntent.create(
                amount=order.total_cents,
                currency="eur",
                payment_method="pm_card_visa",
                payment_method_types=["card"],
                confirm=True,
                metadata={"order_id": str(order.id)},
                idempotency_key=f"intent-{order.id}",
            )
            pid = intent.id
        except stripe.StripeError:
            raise HTTPException(502, "No se pudo crear el intento de pago de prueba")
    order.payment_intent_id = pid
    db.add(PaymentAttempt(order_id=order.id, operation_key=f"intent-{order.id}", provider_id=pid, status="created", amount_cents=order.total_cents))
    db.commit()
    return {"payment_intent_id": pid, "status": order.status}


def process_event(db, event):
    event_id = event["id"]
    if db.get(PaymentEvent, event_id):
        return {"received": True, "duplicate": True}
    obj = event["data"]["object"]
    event_type = event["type"]
    statement = select(Order)
    if event_type.startswith("checkout.session."):
        statement = statement.where(Order.checkout_session_id == obj.get("id"))
    elif event_type.startswith("payment_intent."):
        statement = statement.where(Order.payment_intent_id == obj.get("id"))
    else:
        return {"received": True, "ignored": True}
    order = db.scalar(statement.with_for_update())
    if order is None:
        raise HTTPException(400, "Evento sin pedido asociado")
    # Insertar el ID y modificar el pedido pertenecen a la misma transacción.
    db.add(PaymentEvent(event_id=event_id, event_type=event_type))
    paid = event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded", "payment_intent.succeeded"}
    if paid:
        amount = obj.get("amount_total") if event_type.startswith("checkout") else obj.get("amount_received")
        if amount != order.total_cents or obj.get("currency") != "eur":
            raise HTTPException(400, "Importe o moneda del evento no coincide con el pedido")
        if event_type.startswith("checkout") and obj.get("payment_status") != "paid":
            paid = False
        if paid and order.status == "pending_payment":
            order.status = "paid"
            order.payment_intent_id = obj.get("payment_intent", order.payment_intent_id)
    elif event_type == "checkout.session.expired":
        expire_order(db, order)
    elif event_type in {"payment_intent.payment_failed", "checkout.session.async_payment_failed"}:
        log.warning("Intento de pago fallido", extra={"event_action": "payment.failed"})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.get(PaymentEvent, event_id):
            return {"received": True, "duplicate": True}
        raise
    return {"received": True, "duplicate": False}


def demo_result(db, order, outcome, settings):
    if settings.payment_mode != "demo":
        raise HTTPException(404, "Ruta disponible solo en modo demo")
    if order.status != "pending_payment":
        return order.to_dict()
    if outcome == "paid":
        order.status = "paid"
        order.payment_intent_id = "pi_demo_" + str(order.id)
    elif outcome == "expired":
        expire_order(db, order)
    db.add(PaymentAttempt(order_id=order.id, operation_key="demo-" + secrets.token_hex(12), status=outcome, amount_cents=order.total_cents))
    db.commit()
    return order.to_dict()


def refund(db, order, amount, request_id, settings):
    key = f"refund-{order.id}-{request_id}"
    existing = db.scalar(select(PaymentAttempt).where(PaymentAttempt.operation_key == key))
    if existing:
        if existing.amount_cents != amount:
            raise HTTPException(409, "La clave de reembolso ya se usó con otro importe")
        return order.to_dict()
    if order.status not in {"paid", "partially_refunded"} or amount > order.total_cents - order.refunded_cents:
        raise HTTPException(409, "Importe de reembolso no disponible")
    provider_id = "re_demo_" + secrets.token_hex(12)
    if settings.payment_mode == "stripe":
        stripe.api_key = settings.stripe_secret_key
        try:
            result = stripe.Refund.create(payment_intent=order.payment_intent_id, amount=amount, idempotency_key=key)
            provider_id = result.id
            if result.status != "succeeded":
                raise HTTPException(409, "El proveedor todavía no ha completado el reembolso; revisa Stripe antes de reintentar")
        except stripe.StripeError:
            raise HTTPException(502, "El proveedor no ha confirmado el reembolso")
    order.refunded_cents += amount
    order.status = "refunded" if order.refunded_cents == order.total_cents else "partially_refunded"
    db.add(PaymentAttempt(order_id=order.id, operation_key=key, status="refunded", provider_id=provider_id, amount_cents=amount))
    db.commit()
    return order.to_dict()
