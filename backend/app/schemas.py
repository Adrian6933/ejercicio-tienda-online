from typing import Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Register(Payload):
    email: str = Field(min_length=5, max_length=254)
    name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def email_format(cls, value):
        if "@" not in value or "." not in value.rsplit("@", 1)[-1] or any(c.isspace() for c in value):
            raise ValueError("Email no válido")
        return value.lower()


class Login(Payload):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)


class AddressInput(Payload):
    recipient: str = Field(min_length=2, max_length=100)
    street: str = Field(min_length=3, max_length=200)
    city: str = Field(min_length=2, max_length=100)
    postal_code: str = Field(min_length=2, max_length=20)
    country: str = Field(min_length=2, max_length=2, pattern="^[A-Z]{2}$")


class Quantity(Payload):
    quantity: int = Field(strict=True, ge=0, le=100)


class NewOrder(Payload):
    cart_token: str = Field(min_length=20, max_length=100)


class NewPrice(Payload):
    price_cents: int = Field(strict=True, gt=0, le=100000000)


class NewCategory(Payload):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=100, pattern="^[a-z0-9-]+$")


class DemoResult(Payload):
    outcome: Literal["paid", "declined", "requires_action", "expired"]


class Refund(Payload):
    amount_cents: int = Field(strict=True, gt=0)
    request_id: str = Field(min_length=8, max_length=80, pattern="^[A-Za-z0-9_-]+$")


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str


class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    price_cents: int
    stock: int
    weight_grams: int | None
    image_url: str
    category: CategoryOut


class ProductPage(BaseModel):
    items: list[ProductOut]
    next_cursor: int | None


class HistoryOut(BaseModel):
    id: int
    previous_price_cents: int
    price_cents: int
    changed_at: datetime


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    is_admin: bool


class CartLineOut(BaseModel):
    product: ProductOut
    quantity: int


class CartOut(BaseModel):
    items: list[CartLineOut]
    total_cents: int


class OrderLineOut(BaseModel):
    product_id: int
    name: str
    price_cents: int
    quantity: int


class OrderOut(BaseModel):
    id: int
    total_cents: int
    refunded_cents: int
    status: str
    created_at: datetime
    shipping_address_id: int
    checkout_session_id: str | None
    payment_intent_id: str | None
    items: list[OrderLineOut]
