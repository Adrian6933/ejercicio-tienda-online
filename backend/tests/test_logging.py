import json
from pathlib import Path


def test_logs_are_searchable_and_do_not_contain_identity_or_tokens(client, app, user):
    token = client.post("/carts").json()["token"]
    response = client.get("/carts/" + token)
    assert response.status_code == 200
    lines = Path(app.state.settings.log_file).read_text(encoding="utf-8")
    assert user["email"] not in lines
    assert token not in lines
    assert client.cookies.get("shop_session") not in lines
    events = [json.loads(line) for line in lines.splitlines()]
    assert any(e.get("http.route") == "/carts/{token}" and e.get("trace.id") for e in events)
