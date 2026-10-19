from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from ..dependencies import DB, AdminDep
from ..models import Category, Product
from ..schemas import NewPrice, NewCategory, CategoryOut, ProductOut, ProductPage, HistoryOut
from ..services.catalog import product_or_404, history, change_price

router = APIRouter(tags=["Catálogo"])


@router.get("/categories", response_model=list[CategoryOut])
def categories(db: DB):
    return [{"id": c.id, "name": c.name, "slug": c.slug} for c in db.scalars(select(Category).order_by(Category.name))]


@router.post("/categories", status_code=201)
def add_category(payload: NewCategory, db: DB, admin: AdminDep):
    category = Category(**payload.model_dump())
    db.add(category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ya existe esa categoría")
    return {"id": category.id, "name": category.name, "slug": category.slug}


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: DB, admin: AdminDep):
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(404, "Categoría no encontrada")
    db.delete(category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "No se puede borrar una categoría con productos")
    return Response(status_code=204)


@router.get("/products", response_model=ProductPage)
def products(db: DB, category: str | None = None, limit: int = Query(8, ge=1, le=100), cursor: int = Query(0, ge=0), q: str = Query("", max_length=100)):
    statement = select(Product).where(Product.id > cursor).order_by(Product.id)
    if category:
        statement = statement.join(Category).where(Category.slug == category)
    if q:
        # SQLAlchemy parametriza la búsqueda; no se concatena SQL con datos de usuario.
        statement = statement.where(Product.name.ilike("%" + q.replace("%", "\\%").replace("_", "\\_") + "%", escape="\\"))
    values = db.scalars(statement.limit(limit + 1)).all()
    return {"items": [p.to_dict() for p in values[:limit]], "next_cursor": values[limit - 1].id if len(values) > limit else None}


@router.get("/products/{product_id}", response_model=ProductOut)
def product(product_id: int, db: DB):
    return product_or_404(db, product_id).to_dict()


@router.get("/products/{product_id}/price-history", response_model=list[HistoryOut])
def prices(product_id: int, db: DB):
    return [
        {"id": h.id, "previous_price_cents": h.previous_price_cents, "price_cents": h.price_cents, "changed_at": h.changed_at} for h in history(db, product_id)
    ]


@router.put("/products/{product_id}/price", response_model=ProductOut)
def price(product_id: int, payload: NewPrice, db: DB, admin: AdminDep):
    return change_price(db, product_id, payload.price_cents).to_dict()


@router.post("/products/{product_id}/views", status_code=204)
def view(product_id: int, db: DB):
    product_or_404(db, product_id)
    return Response(status_code=204)
