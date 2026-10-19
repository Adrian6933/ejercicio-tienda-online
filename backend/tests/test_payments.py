import hashlib, hmac, json, time
from types import SimpleNamespace
import pytest
from app.models import Order, PaymentEvent
from conftest import make_order


def checkout(client):
    order, _ = make_order(client)
    response = client.post(f"/orders/{order['id']}/checkout")
    assert response.status_code == 200, response.text
    return order


def signed(client, event, secret="whsec_test_only"):
    body = json.dumps(event).encode()
    now = int(time.time())
    signature = hmac.new(secret.encode(), str(now).encode() + b"." + body, hashlib.sha256).hexdigest()
    return client.post("/webhooks/stripe", content=body, headers={"Stripe-Signature": f"t={now},v1={signature}", "Content-Type": "application/json"})


def event_for(app, order, event_id="evt_1", event_type="checkout.session.completed"):
    with app.state.sessions() as db:
        stored = db.get(Order, order["id"])
        return {
            "id": event_id,
            "type": event_type,
            "livemode": False,
            "data": {
                "object": {
                    "id": stored.checkout_session_id,
                    "amount_total": stored.total_cents,
                    "currency": "eur",
                    "payment_status": "paid",
                    "payment_intent": "pi_test_" + str(order["id"]),
                }
            },
        }


def test_demo_checkout_reusable_and_pending_until_paid(client, shipping):
    order = checkout(client)
    first = client.post(f"/orders/{order['id']}/checkout").json()
    assert first["mode"] == "demo" and "/checkout/demo?" in first["url"]
    assert client.get(f"/orders/{order['id']}").json()["status"] == "pending_payment"
    assert client.post(f"/orders/{order['id']}/demo-result", json={"outcome": "declined"}).json()["status"] == "pending_payment"
    assert client.post(f"/orders/{order['id']}/demo-result", json={"outcome": "requires_action"}).json()["status"] == "pending_payment"
    assert client.post(f"/orders/{order['id']}/demo-result", json={"outcome": "paid"}).json()["status"] == "paid"


def test_expiry_returns_stock_once(client, shipping):
    order = checkout(client)
    assert client.get("/products/1").json()["stock"] == 7
    for _ in range(2):
        assert client.post(f"/orders/{order['id']}/demo-result", json={"outcome": "expired"}).json()["status"] == "expired"
    assert client.get("/products/1").json()["stock"] == 8


def test_signed_webhook_idempotent_and_monotonic(client, app, shipping):
    order = checkout(client)
    app.state.settings.payment_mode = "stripe"
    event = event_for(app, order)
    assert signed(client, event).status_code == 200
    assert signed(client, event).json()["duplicate"] is True
    assert client.get(f"/orders/{order['id']}").json()["status"] == "paid"
    late = event_for(app, order, "evt_late", "checkout.session.expired")
    assert signed(client, late).status_code == 200
    assert client.get(f"/orders/{order['id']}").json()["status"] == "paid"
    assert client.get("/products/1").json()["stock"] == 7


@pytest.mark.parametrize("mutation", ["amount", "currency", "live", "signature"])
def test_webhook_rejects_invalid_payment(client, app, shipping, mutation):
    order = checkout(client)
    app.state.settings.payment_mode = "stripe"
    event = event_for(app, order)
    if mutation == "amount":
        event["data"]["object"]["amount_total"] = 1
    if mutation == "currency":
        event["data"]["object"]["currency"] = "usd"
    if mutation == "live":
        event["livemode"] = True
    response = signed(client, event, "wrong_secret" if mutation == "signature" else "whsec_test_only")
    assert response.status_code == 400
    assert client.get(f"/orders/{order['id']}").json()["status"] == "pending_payment"
    with app.state.sessions() as db:
        assert db.get(PaymentEvent, "evt_1") is None


def test_unpaid_checkout_event_does_not_mark_paid(client, app, shipping):
    order = checkout(client)
    app.state.settings.payment_mode = "stripe"
    event = event_for(app, order)
    event["data"]["object"]["payment_status"] = "unpaid"
    assert signed(client, event).status_code == 200
    assert client.get(f"/orders/{order['id']}").json()["status"] == "pending_payment"


def test_stripe_checkout_parameters_with_fake_provider(client, app, shipping, monkeypatch):
    order, _ = make_order(client)
    app.state.settings.payment_mode = "stripe"
    app.state.settings.stripe_secret_key = "sk_test_fake_not_a_real_key"
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id="cs_test_from_provider", url="https://checkout.stripe.test/session")

    monkeypatch.setattr("stripe.checkout.Session.create", fake_create)
    response = client.post(f"/orders/{order['id']}/checkout")
    assert response.json()["url"] == "https://checkout.stripe.test/session"
    assert captured["line_items"][0]["price_data"]["unit_amount"] == 89900
    assert captured["idempotency_key"] == f"checkout-{order['id']}"
    assert "{CHECKOUT_SESSION_ID}" in captured["success_url"]
    assert client.post(f"/orders/{order['id']}/demo-result", json={"outcome": "paid"}).status_code == 404


def test_refund_partial_full_and_idempotent(client, shipping, admin):
    order = checkout(client)
    client.post(f"/orders/{order['id']}/demo-result", json={"outcome": "paid"})
    path = f"/orders/{order['id']}/refund"
    one = {"amount_cents": 100, "request_id": "request_001"}
    assert client.post(path, json=one).json()["status"] == "partially_refunded"
    assert client.post(path, json=one).json()["refunded_cents"] == 100
    assert client.post(path, json={"amount_cents": 200, "request_id": "request_001"}).status_code == 409
    assert client.post(path, json={"amount_cents": 89800, "request_id": "request_002"}).json()["status"] == "refunded"


def test_paymentintent_intro(client, shipping):
    order, _ = make_order(client)
    response = client.post(f"/orders/{order['id']}/payment-intent")
    assert response.status_code == 200
    assert response.json()["payment_intent_id"].startswith("pi_demo_")


def test_demo_does_not_accept_webhook(client, app, shipping):
    order = checkout(client)
    assert signed(client, event_for(app, order)).status_code == 400
