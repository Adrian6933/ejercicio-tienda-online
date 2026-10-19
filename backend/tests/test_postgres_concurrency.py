from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from sqlalchemy import select
import pytest
from app.models import Product, Order


@pytest.mark.postgres
def test_last_unit_cannot_be_bought_twice(client, app, shipping):
    if app.state.engine.dialect.name != "postgresql":
        pytest.skip("La exclusión entre compradores se comprueba en PostgreSQL")
    tokens = [client.post("/carts").json()["token"] for _ in range(2)]
    for token in tokens:
        assert client.put(f"/carts/{token}/items/1", json={"quantity": 1}).status_code == 200
    with app.state.sessions() as db:
        db.get(Product, 1).stock = 1
        db.commit()
    cookie = client.cookies.get("shop_session")

    def place(token):
        with TestClient(app, headers={"Origin": "http://localhost:5173", "Cookie": "shop_session=" + cookie}) as other:
            return other.post("/orders", json={"cart_token": token}).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(place, tokens))
    assert sorted(statuses) == [201, 409]
    with app.state.sessions() as db:
        assert db.get(Product, 1).stock == 0
        assert len(db.scalars(select(Order)).all()) == 1
