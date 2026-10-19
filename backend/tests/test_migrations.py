from alembic import command
from sqlalchemy import text,inspect
from app.manage import migration_config


def test_trigger_downgrade_upgrade_and_schema_match(app):
    url = app.state.settings.database_url
    cfg = migration_config(url)
    command.downgrade(cfg, "0001")
    with app.state.engine.begin() as con:
        con.execute(text("UPDATE products SET price_cents=90000 WHERE id=1"))
        assert con.execute(text("SELECT count(*) FROM product_price_history")).scalar() == 0
    command.upgrade(cfg, "head")
    with app.state.engine.begin() as con:
        con.execute(text("UPDATE products SET price_cents=91000 WHERE id=1"))
        assert con.execute(text("SELECT count(*) FROM product_price_history")).scalar() == 1
    command.check(cfg)
    checks={c['name'] for c in inspect(app.state.engine).get_check_constraints('order_items')}
    assert {'ck_order_item_price','ck_order_item_quantity'} <= checks
