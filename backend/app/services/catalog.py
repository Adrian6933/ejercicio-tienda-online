from fastapi import HTTPException
from sqlalchemy import select
from ..models import Product, PriceHistory


def product_or_404(db, product_id):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(404, "Producto no encontrado")
    return product


def change_price(db, product_id, price_cents):
    product = db.scalar(select(Product).where(Product.id == product_id).with_for_update(of=Product))
    if product is None:
        raise HTTPException(404, "Producto no encontrado")
    if product.price_cents == price_cents:
        return product
    product.price_cents = price_cents
    db.commit()  # El trigger registra el cambio incluso si se hace desde DBeaver.
    db.refresh(product)
    return product


def history(db, product_id):
    product_or_404(db, product_id)
    return db.scalars(select(PriceHistory).where(PriceHistory.product_id == product_id).order_by(PriceHistory.changed_at, PriceHistory.id)).all()
