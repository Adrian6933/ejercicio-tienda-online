"""Registrar cada cambio de precio, también el SQL ejecutado fuera de la API."""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute("""CREATE FUNCTION record_price_change() RETURNS trigger AS $$
        BEGIN
            IF OLD.price_cents IS DISTINCT FROM NEW.price_cents THEN
                INSERT INTO product_price_history(product_id,previous_price_cents,price_cents,changed_at)
                VALUES(NEW.id,OLD.price_cents,NEW.price_cents,CURRENT_TIMESTAMP AT TIME ZONE 'UTC');
            END IF;
            RETURN NEW;
        END; $$ LANGUAGE plpgsql""")
        op.execute("CREATE TRIGGER trg_product_price AFTER UPDATE OF price_cents ON products FOR EACH ROW EXECUTE FUNCTION record_price_change()")
    elif dialect == "sqlite":
        op.execute("""CREATE TRIGGER trg_product_price AFTER UPDATE OF price_cents ON products
        WHEN OLD.price_cents != NEW.price_cents
        BEGIN
            INSERT INTO product_price_history(product_id,previous_price_cents,price_cents,changed_at)
            VALUES(NEW.id,OLD.price_cents,NEW.price_cents,STRFTIME('%Y-%m-%d %H:%M:%f','now'));
        END""")
    else:
        raise RuntimeError("La práctica soporta PostgreSQL y SQLite")


def downgrade():
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_product_price ON products")
        op.execute("DROP FUNCTION IF EXISTS record_price_change()")
    else:
        op.execute("DROP TRIGGER IF EXISTS trg_product_price")
