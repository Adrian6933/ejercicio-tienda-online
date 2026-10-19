import pytest
from sqlalchemy import select
from app.models import Product, Order
from conftest import make_order


def test_cart_put_is_idempotent_and_price_is_server_owned(client):
    token = client.post("/carts").json()["token"]
    path = f"/carts/{token}/items/1"
    client.put(path, json={"quantity": 2})
    response = client.put(path, json={"quantity": 2})
    assert response.json()["items"][0]["quantity"] == 2
    assert response.json()["total_cents"] == 89900 * 2
    assert client.put(path, json={"quantity": 2, "price_cents": 1}).status_code == 422
    assert client.delete(path).json()["items"] == []


@pytest.mark.parametrize("quantity", [-1, 101, 1.5, True])
def test_cart_invalid_quantities(client, quantity):
    token = client.post("/carts").json()["token"]
    assert client.put(f"/carts/{token}/items/1", json={"quantity": quantity}).status_code == 422


def test_no_stock(client):
    token = client.post("/carts").json()["token"]
    assert client.put(f"/carts/{token}/items/4", json={"quantity": 1}).status_code == 409


def test_order_needs_shipping_address(client, user):
    token = client.post("/carts").json()["token"]
    client.put(f"/carts/{token}/items/1", json={"quantity": 1})
    assert client.post("/orders", json={"cart_token": token}).status_code == 409


def test_order_idempotent_copies_price_and_decrements_once(client, app, shipping, admin):
    order, token = make_order(client, quantity=2)
    repeat = client.post("/orders", json={"cart_token": token}).json()
    assert repeat["id"] == order["id"]
    assert order["items"][0]["price_cents"] == 89900
    assert order["total_cents"] == 179800
    assert client.get("/products/1").json()["stock"] == 6
    assert client.put("/products/1/price", json={"price_cents": 90000}).status_code == 200
    assert client.get("/orders/" + str(order["id"])).json()["items"][0]["price_cents"] == 89900
    assert client.put(f"/carts/{token}/items/1", json={"quantity": 3}).status_code == 409


def test_insufficient_stock_rolls_back_entire_order(client, app, shipping):
    token = client.post("/carts").json()["token"]
    client.put(f"/carts/{token}/items/1", json={"quantity": 1})
    client.put(f"/carts/{token}/items/2", json={"quantity": 2})
    with app.state.sessions() as db:
        db.get(Product, 2).stock = 1
        db.commit()
    assert client.post("/orders", json={"cart_token": token}).status_code == 409
    assert client.get("/products/1").json()["stock"] == 8
    with app.state.sessions() as db:
        assert db.scalars(select(Order)).all() == []


def test_empty_and_missing_cart(client, shipping):
    token = client.post("/carts").json()["token"]
    assert client.post("/orders", json={"cart_token": token}).status_code == 409
    assert client.get("/carts/does-not-exist").status_code == 404
