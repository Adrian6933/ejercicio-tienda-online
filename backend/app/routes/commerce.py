from fastapi import APIRouter, Request
from sqlalchemy import select
from ..dependencies import DB, UserDep
from ..models import Order
from ..schemas import Quantity, NewOrder, CartOut, OrderOut
from ..services import commerce

router = APIRouter(tags=["Carrito y pedidos"])


@router.post("/carts", status_code=201)
def new_cart(db: DB):
    return {"token": commerce.new_cart(db)}


@router.get("/carts/{token}", response_model=CartOut)
def cart(token: str, db: DB):
    return commerce.serialize_cart(commerce.get_cart(db, token))


@router.put("/carts/{token}/items/{product_id}", response_model=CartOut)
def set_item(token: str, product_id: int, payload: Quantity, db: DB):
    return commerce.serialize_cart(commerce.set_item(db, token, product_id, payload.quantity))


@router.delete("/carts/{token}/items/{product_id}", response_model=CartOut)
def remove_item(token: str, product_id: int, db: DB):
    return commerce.serialize_cart(commerce.set_item(db, token, product_id, 0))


@router.post("/orders", status_code=201, response_model=OrderOut)
def order(payload: NewOrder, request: Request, user: UserDep, db: DB):
    return commerce.create_order(db, user, payload.cart_token, request.app.state.settings.payment_minutes).to_dict()


@router.get("/me/orders", response_model=list[OrderOut])
def my_orders(user: UserDep, db: DB):
    return [o.to_dict() for o in db.scalars(select(Order).where(Order.user_id == user.id).order_by(Order.id.desc()))]


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, user: UserDep, db: DB):
    return commerce.owned_order(db, user, order_id).to_dict()
