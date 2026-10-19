from sqlalchemy import select
from app.models import User, LoginSession, Address
from app.security import hash_password, verify_password
from conftest import account, make_order


def test_password_hash_has_unique_salt_and_verifies():
    one, two = hash_password("contraseña"), hash_password("contraseña")
    assert one != two
    assert verify_password("contraseña", one)
    assert not verify_password("incorrecta", one)


def test_register_duplicate_login_and_logout(client, app, user):
    assert client.post("/auth/register", json={"name": "Otro", "email": user["email"], "password": "Una-clave-larga-2026"}).status_code == 409
    assert client.post("/auth/login", json={"email": user["email"], "password": "mal"}).status_code == 401
    with app.state.sessions() as db:
        stored = db.get(User, user["id"])
        assert stored.password_hash.startswith("scrypt$")
        sessions = db.scalars(select(LoginSession)).all()
        assert all(s.token_hash != client.cookies.get("shop_session") for s in sessions)
    assert client.post("/auth/logout").status_code == 204
    assert client.get("/me").status_code == 401


def test_role_cannot_be_injected_at_registration(client):
    response = client.post("/auth/register", json={"name": "Persona", "email": "inject@example.test", "password": "Una-clave-larga-2026", "is_admin": True})
    assert response.status_code == 422


def test_session_expiration(client, app, user):
    from datetime import timedelta
    from app.models import utcnow

    with app.state.sessions() as db:
        for session in db.scalars(select(LoginSession)):
            session.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.get("/me").status_code == 401


def test_cookie_origin_is_checked(client, user):
    response = client.put(
        "/me/addresses/shipping",
        headers={"Origin": "https://untrusted.example"},
        json={"recipient": "Persona", "street": "Calle prueba", "city": "Madrid", "postal_code": "28000", "country": "ES"},
    )
    assert response.status_code == 403


def test_address_versioning_keeps_order_snapshot(client, app, shipping):
    order, _ = make_order(client)
    previous = shipping["id"]
    new_data = {k: v for k, v in shipping.items() if k in {"recipient", "street", "city", "postal_code", "country"}}
    new_data["street"] = "Otra calle 2"
    assert client.put("/me/addresses/shipping", json=new_data).status_code == 200
    assert client.get("/orders/" + str(order["id"])).json()["shipping_address_id"] == previous
    with app.state.sessions() as db:
        addresses = db.scalars(select(Address)).all()
        assert len(addresses) == 2 and sum(a.is_active for a in addresses) == 1


def test_users_cannot_read_others_orders(client, app, shipping):
    order, _ = make_order(client)
    client.post("/auth/logout")
    account(client, "other@example.test")
    assert client.get("/orders/" + str(order["id"])).status_code == 404
    assert client.get("/me/orders").json() == []


def test_unauthenticated_checkout_is_rejected(client):
    assert client.post("/orders", json={"cart_token": "x" * 30}).status_code == 401
