from collections import defaultdict, deque
from time import monotonic
from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy import select, delete
from ..dependencies import DB, UserDep
from ..models import Address, LoginSession
from ..schemas import Register, Login, AddressInput, UserOut
from ..security import token_hash
from ..services import accounts

router = APIRouter(tags=["Cuenta"])
_attempts = defaultdict(deque)


def public_user(user):
    return {"id": user.id, "email": user.email, "name": user.name, "is_admin": user.is_admin}


@router.post("/auth/register", status_code=201, response_model=UserOut)
def register(payload: Register, db: DB):
    return public_user(accounts.register(db, payload))


@router.post("/auth/login", response_model=UserOut)
def login(payload: Login, request: Request, response: Response, db: DB):
    if request.headers.get("origin") and request.headers["origin"].rstrip("/") not in request.app.state.settings.origins:
        raise HTTPException(403, "Origen de inicio de sesión no autorizado")
    # Limitador local para la práctica. En varias réplicas usar almacenamiento compartido.
    key = (request.client.host if request.client else "unknown", payload.email.strip().lower())
    attempts = _attempts[key]
    now = monotonic()
    while attempts and attempts[0] < now - 60:
        attempts.popleft()
    if len(attempts) >= 12:
        raise HTTPException(429, "Espera un minuto antes de volver a intentarlo")
    attempts.append(now)
    settings = request.app.state.settings
    token, user = accounts.login(db, payload.email, payload.password, settings.session_hours)
    attempts.clear()
    response.set_cookie(
        "shop_session",
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="none" if settings.cookie_secure else "lax",
        max_age=settings.session_hours * 3600,
        path="/",
    )
    return public_user(user)


@router.get("/me", response_model=UserOut)
def me(user: UserDep):
    return public_user(user)


@router.post("/auth/logout", status_code=204)
def logout(request: Request, response: Response, user: UserDep, db: DB):
    token = request.cookies.get("shop_session")
    header = request.headers.get("authorization", "")
    if header.startswith("Bearer "):
        token = header[7:]
    if token:
        db.execute(delete(LoginSession).where(LoginSession.token_hash == token_hash(token)))
        db.commit()
    response.delete_cookie("shop_session", path="/")
    response.status_code = 204


@router.get("/me/addresses/{kind}")
def address(kind: str, user: UserDep, db: DB):
    if kind not in {"shipping", "billing"}:
        raise HTTPException(404, "Tipo de dirección no encontrado")
    value = db.scalar(select(Address).where(Address.user_id == user.id, Address.kind == kind, Address.is_active.is_(True)))
    return value.to_dict() if value else None


@router.put("/me/addresses/{kind}")
def save_address(kind: str, payload: AddressInput, user: UserDep, db: DB):
    if kind not in {"shipping", "billing"}:
        raise HTTPException(404, "Tipo de dirección no encontrado")
    return accounts.save_address(db, user, kind, payload).to_dict()
