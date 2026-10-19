from sqlalchemy import text


def test_catalog_filters_pagination_and_missing_product(client):
    page = client.get("/products", params={"limit": 2}).json()
    assert len(page["items"]) == 2
    next_page = client.get("/products", params={"limit": 2, "cursor": page["next_cursor"]}).json()
    assert not {p["id"] for p in page["items"]} & {p["id"] for p in next_page["items"]}
    filtered = client.get("/products?category=audio").json()["items"]
    assert filtered and all(p["category"]["slug"] == "audio" for p in filtered)
    assert client.get("/products/999999").status_code == 404
    assert client.get("/products?limit=0").status_code == 422


def test_categories_endpoint_dynamic(client, admin):
    response = client.post("/categories", json={"name": "Nuevos", "slug": "nuevos"})
    assert response.status_code == 201
    assert any(c["slug"] == "nuevos" for c in client.get("/categories").json())
    assert client.delete("/categories/1").status_code == 409


def test_images_and_views(client):
    assert client.post("/products/1/views").status_code == 204
    assert client.post("/products/999999/views").status_code == 404


def test_history_empty_versus_missing(client):
    assert client.get("/products/1/price-history").json() == []
    assert client.get("/products/999999/price-history").status_code == 404


def test_price_change_requires_admin(client, user):
    assert client.put("/products/1/price", json={"price_cents": 10000}).status_code == 403


def test_price_history_records_only_changes(client, admin, app):
    original = client.get("/products/1").json()["price_cents"]
    assert client.put("/products/1/price", json={"price_cents": original}).status_code == 200
    assert client.get("/products/1/price-history").json() == []
    assert client.put("/products/1/price", json={"price_cents": original - 100}).status_code == 200
    rows = client.get("/products/1/price-history").json()
    assert len(rows) == 1
    assert rows[0]["previous_price_cents"] == original
    assert rows[0]["price_cents"] == original - 100
    with app.state.engine.begin() as con:
        con.execute(text("UPDATE products SET price_cents=:price WHERE id=1"), {"price": original + 100})
    assert len(client.get("/products/1/price-history").json()) == 2
    assert client.put("/products/1/price", json={"price_cents": -1}).status_code == 422


def test_search_is_parameterized(client):
    assert client.get("/products", params={"q": "' OR 1=1 --"}).json()["items"] == []
    assert len(client.get("/products").json()["items"]) > 0


def test_health_and_version(client):
    assert client.get("/health").json()["status"] == "ok"
    response = client.get("/version")
    assert response.status_code == 200 and response.headers["x-request-id"]
