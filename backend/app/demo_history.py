"""Datos ficticios para observar la gráfica de precios."""

from datetime import timedelta
from sqlalchemy import select
from .database import make_engine, factory
from .config import Settings
from .models import Product, PriceHistory, utcnow


def main():
    engine = make_engine(Settings().database_url)
    with factory(engine)() as db:
        product = db.get(Product, 7)
        if not product or product.name != 'Portátil creativo 16"':
            raise ValueError("Este comando solo trabaja con el producto ficticio 7 del seed")
        if db.scalar(select(PriceHistory.id).where(PriceHistory.product_id == 7).limit(1)):
            print("El producto de demo ya tiene histórico; no se modifica")
            return
        original = product.price_cents
        for price in [original - 5000, original - 10000, original]:
            product.price_cents = price
            db.commit()
        rows = db.scalars(select(PriceHistory).where(PriceHistory.product_id == 7).order_by(PriceHistory.id)).all()
        for index, row in enumerate(rows):
            row.changed_at = utcnow() - timedelta(days=len(rows) - index)
        db.commit()
        print("Histórico ficticio creado para el producto 7; el precio actual se conserva")
    engine.dispose()


if __name__ == "__main__":
    main()
