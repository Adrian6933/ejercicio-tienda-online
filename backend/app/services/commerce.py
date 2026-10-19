from datetime import timedelta
import secrets
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from ..models import Cart, CartItem, Product, Order, OrderItem, Address, utcnow
from ..security import token_hash


def new_cart(db):
    token = secrets.token_urlsafe(32)
    db.add(Cart(token_hash=token_hash(token)))
    db.commit()
    return token


def get_cart(db, token, lock=False):
    statement = select(Cart).where(Cart.token_hash == token_hash(token))
    if lock:
        statement = statement.with_for_update()
    cart = db.scalar(statement)
    if cart is None:
        raise HTTPException(404, "Carrito no encontrado")
    return cart


def serialize_cart(cart):
    return {
        "items": [{"product": i.product.to_dict(), "quantity": i.quantity} for i in cart.items],
        "total_cents": sum(i.product.price_cents * i.quantity for i in cart.items),
    }


def set_item(db, token, product_id, quantity):
    cart = get_cart(db, token, True)
    if db.scalar(select(Order.id).where(Order.cart_hash == cart.token_hash)):
        raise HTTPException(409, "Este carrito ya se ha convertido en pedido")
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(404, "Producto no encontrado")
    if quantity > product.stock:
        raise HTTPException(409, "No hay stock suficiente")
    item = db.get(CartItem, (cart.token_hash, product_id))
    if quantity == 0:
        if item:
            db.delete(item)
    elif item:
        item.quantity = quantity
    else:
        db.add(CartItem(cart_hash=cart.token_hash, product_id=product_id, quantity=quantity))
    db.commit()
    db.expire(cart, ["items"])
    return cart


def create_order(db, user, token, payment_minutes):
    cart = get_cart(db, token, True)
    existing = db.scalar(select(Order).where(Order.cart_hash == cart.token_hash))
    if existing:
        if existing.user_id != user.id:
            raise HTTPException(403, "El carrito pertenece a otro pedido")
        return existing
    address = db.scalar(select(Address).where(Address.user_id == user.id, Address.kind == "shipping", Address.is_active.is_(True)))
    if address is None:
        raise HTTPException(409, "Añade una dirección de envío antes de comprar")
    if not cart.items:
        raise HTTPException(409, "El carrito está vacío")
    ids = sorted(i.product_id for i in cart.items)
    products = {p.id: p for p in db.scalars(select(Product).where(Product.id.in_(ids)).order_by(Product.id).with_for_update(of=Product))}
    for item in cart.items:
        if products[item.product_id].stock < item.quantity:
            raise HTTPException(409, "No hay stock suficiente")
    order = Order(
        cart_hash=cart.token_hash,
        user_id=user.id,
        shipping_address_id=address.id,
        total_cents=0,
        status="pending_payment",
        payment_expires_at=utcnow() + timedelta(minutes=payment_minutes),
    )
    for item in cart.items:
        product = products[item.product_id]
        result = db.execute(update(Product).where(Product.id == product.id, Product.stock >= item.quantity).values(stock=Product.stock - item.quantity))
        if result.rowcount != 1:
            db.rollback()
            raise HTTPException(409, "El stock ha cambiado; actualiza el carrito")
        order.items.append(OrderItem(product_id=product.id, name=product.name, price_cents=product.price_cents, quantity=item.quantity))
        order.total_cents += product.price_cents * item.quantity
    db.add(order)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(Order).where(Order.cart_hash == cart.token_hash, Order.user_id == user.id))
        if existing:
            return existing
        raise
    return order


def owned_order(db, user, order_id, lock=False):
    statement = select(Order).where(Order.id == order_id, Order.user_id == user.id)
    if lock:
        statement = statement.with_for_update()
    order = db.scalar(statement)
    if order is None:
        raise HTTPException(404, "Pedido no encontrado")
    return order


def expire_order(db, order):
    if order.status != "pending_payment":
        return False
    for item in sorted(order.items, key=lambda i: i.product_id):
        db.execute(update(Product).where(Product.id == item.product_id).values(stock=Product.stock + item.quantity))
    order.status = "expired"
    return True
