"""Guardar el tipo de IVA en la línea, sin recalcular ventas históricas."""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("order_items", sa.Column("vat_basis_points", sa.Integer(), server_default="2100", nullable=False))


def downgrade():
    with op.batch_alter_table("order_items") as batch:
        batch.drop_column("vat_basis_points")
