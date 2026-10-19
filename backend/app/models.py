from datetime import datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (CheckConstraint("price_cents > 0"), CheckConstraint("stock >= 0"), CheckConstraint("weight_grams IS NULL OR weight_grams > 0"))
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text)
    price_cents: Mapped[int] = mapped_column(Integer)
    stock: Mapped[int] = mapped_column(Integer)
    weight_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str] = mapped_column(String(500))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), index=True)
    category: Mapped[Category] = relationship(lazy="joined")

    def is_available(self):
        return self.stock > 0

    def to_dict(self):
        return {k: getattr(self, k) for k in ("id", "name", "description", "price_cents", "stock", "weight_grams", "image_url")} | {
            "category": {"id": self.category.id, "name": self.category.name, "slug": self.category.slug}
        }


class PriceHistory(Base):
    __tablename__ = "product_price_history"
    __table_args__ = (CheckConstraint("price_cents > 0"), Index("ix_history_product_date", "product_id", "changed_at"))
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    previous_price_cents: Mapped[int] = mapped_column(Integer)
    price_cents: Mapped[int] = mapped_column(Integer)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(400))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LoginSession(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = (
        Index("ux_address_active", "user_id", "kind", unique=True, sqlite_where=text("is_active = 1"), postgresql_where=text("is_active = true")),
        CheckConstraint("kind IN ('shipping','billing')"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(20))
    recipient: Mapped[str] = mapped_column(String(100))
    street: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def to_dict(self):
        return {k: getattr(self, k) for k in ("id", "kind", "recipient", "street", "city", "postal_code", "country", "is_active")}


class Cart(Base):
    __tablename__ = "carts"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    items: Mapped[list["CartItem"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (CheckConstraint("quantity > 0"),)
    cart_hash: Mapped[str] = mapped_column(ForeignKey("carts.token_hash", ondelete="CASCADE"), primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer)
    product: Mapped[Product] = relationship(lazy="joined")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (CheckConstraint("total_cents > 0"), CheckConstraint("refunded_cents >= 0 AND refunded_cents <= total_cents"))
    id: Mapped[int] = mapped_column(primary_key=True)
    cart_hash: Mapped[str] = mapped_column(ForeignKey("carts.token_hash"), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    shipping_address_id: Mapped[int] = mapped_column(ForeignKey("addresses.id"))
    total_cents: Mapped[int] = mapped_column(Integer)
    refunded_cents: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="pending_payment")
    payment_intent_id: Mapped[str | None] = mapped_column(String(150), nullable=True, unique=True)
    checkout_session_id: Mapped[str | None] = mapped_column(String(150), nullable=True, unique=True)
    checkout_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    items: Mapped[list["OrderItem"]] = relationship(cascade="all, delete-orphan", lazy="selectin")

    def to_dict(self):
        return {
            k: getattr(self, k)
            for k in ("id", "total_cents", "refunded_cents", "status", "created_at", "shipping_address_id", "checkout_session_id", "payment_intent_id")
        } | {"items": [{"product_id": i.product_id, "name": i.name, "price_cents": i.price_cents, "quantity": i.quantity} for i in self.items]}


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_order_item_quantity"), CheckConstraint("price_cents > 0", name="ck_order_item_price"))
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    name: Mapped[str] = mapped_column(String(180))
    price_cents: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    vat_basis_points: Mapped[int] = mapped_column(Integer, default=2100, server_default="2100")


class PaymentEvent(Base):
    __tablename__ = "payment_events"
    event_id: Mapped[str] = mapped_column(String(150), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100))
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    operation_key: Mapped[str] = mapped_column(String(150), unique=True)
    provider_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[str] = mapped_column(String(30))
    amount_cents: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
