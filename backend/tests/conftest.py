import os
from uuid import uuid4
import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from app.config import Settings
from app.main import create_app
from app.manage import migration_config
from app.seed import seed
from app.models import User


@pytest.fixture
def app(tmp_path):
    postgres = os.getenv("TEST_DATABASE_URL")
    admin_engine = None
    schema = None
    url = "sqlite:///" + str(tmp_path / "test.db").replace("\\", "/")
    if postgres:
        admin_engine = create_engine(postgres)
        schema = "test_" + uuid4().hex
        with admin_engine.begin() as con:
            con.execute(text(f"CREATE SCHEMA {schema}"))
        url = make_url(postgres).update_query_dict({"options": f"-csearch_path={schema}"}).render_as_string(hide_password=False)
    settings = Settings(
        database_url=url,
        log_file=str(tmp_path / "events.jsonl"),
        payment_mode="demo",
        stripe_secret_key="",
        stripe_webhook_secret="whsec_test_only",
        cookie_secure=False,
    )
    command.upgrade(migration_config(url), "head")
    application = create_app(settings)
    with application.state.sessions() as db:
        seed(db)
    yield application
    application.state.engine.dispose()
    if admin_engine:
        with admin_engine.begin() as con:
            con.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        admin_engine.dispose()


@pytest.fixture
def client(app):
    with TestClient(app, headers={"Origin": "http://localhost:5173"}) as c:
        yield c


def account(client, email="learner@example.test"):
    payload = {"email": email, "name": "Estudiante", "password": "Una-clave-larga-2026"}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/login", json={"email": email, "password": payload["password"]}).status_code == 200
    return client.get("/me").json()


@pytest.fixture
def user(client):
    return account(client)


@pytest.fixture
def admin(client, app, user):
    with app.state.sessions() as db:
        value = db.get(User, user["id"])
        value.is_admin = True
        db.commit()
    return user


@pytest.fixture
def shipping(client, user):
    data = {"recipient": "Persona de prueba", "street": "Calle de prueba 1", "city": "Madrid", "postal_code": "28000", "country": "ES"}
    response = client.put("/me/addresses/shipping", json=data)
    assert response.status_code == 200, response.text
    return response.json()


def make_order(client, product_id=1, quantity=1):
    token = client.post("/carts").json()["token"]
    assert client.put(f"/carts/{token}/items/{product_id}", json={"quantity": quantity}).status_code == 200
    response = client.post("/orders", json={"cart_token": token})
    assert response.status_code == 201, response.text
    return response.json(), token
