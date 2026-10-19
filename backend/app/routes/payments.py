import stripe
from fastapi import APIRouter, HTTPException, Request
from ..dependencies import DB, UserDep, AdminDep
from ..schemas import DemoResult, Refund
from ..services.commerce import owned_order
from ..services import payments
from ..models import Order
from sqlalchemy import select

router = APIRouter(tags=["Pagos de prueba"])


@router.post("/orders/{order_id}/checkout")
def checkout(order_id: int, request: Request, user: UserDep, db: DB):
    order = owned_order(db, user, order_id, True)
    return {"url": payments.create_checkout(db, order, request.app.state.settings), "mode": request.app.state.settings.payment_mode}


@router.post("/orders/{order_id}/payment-intent")
def intent(order_id: int, request: Request, user: UserDep, db: DB):
    return payments.create_intent(db, owned_order(db, user, order_id, True), request.app.state.settings)


@router.post("/orders/{order_id}/demo-result")
def demo(order_id: int, payload: DemoResult, request: Request, user: UserDep, db: DB):
    return payments.demo_result(db, owned_order(db, user, order_id, True), payload.outcome, request.app.state.settings)


@router.post("/orders/{order_id}/refund")
def refund(order_id: int, payload: Refund, request: Request, admin: AdminDep, db: DB):
    order = db.scalar(select(Order).where(Order.id == order_id).with_for_update())
    if not order:
        raise HTTPException(404, "Pedido no encontrado")
    return payments.refund(db, order, payload.amount_cents, payload.request_id, request.app.state.settings)


@router.post("/webhooks/stripe")
async def webhook(request: Request, db: DB):
    settings = request.app.state.settings
    if not settings.stripe_webhook_secret:
        raise HTTPException(503, "Configura STRIPE_WEBHOOK_SECRET para recibir eventos")
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(payload, request.headers.get("stripe-signature", ""), settings.stripe_webhook_secret)
        event = event.to_dict()
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(400, "Firma de Stripe no válida")
    if settings.payment_mode != "stripe" or event.get("livemode", False):
        raise HTTPException(400, "Esta práctica solo acepta eventos de Stripe en pruebas")
    return payments.process_event(db, event)
