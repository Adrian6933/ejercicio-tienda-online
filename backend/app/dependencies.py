from typing import Annotated
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .database import get_db
from .models import LoginSession, User, utcnow
from .security import token_hash

DB = Annotated[Session, Depends(get_db)]


def current_user(request: Request, db: DB):
    header = request.headers.get("authorization", "")
    token = header[7:] if header.startswith("Bearer ") else request.cookies.get("shop_session")
    if not token:
        raise HTTPException(401, "Inicia sesión para continuar")
    session = db.get(LoginSession, token_hash(token))
    if session is None or session.expires_at <= utcnow():
        raise HTTPException(401, "La sesión ha caducado")
    if not header and request.method not in {"GET", "HEAD", "OPTIONS"}:
        if request.headers.get("origin", "").rstrip("/") not in request.app.state.settings.origins:
            raise HTTPException(403, "Origen de la petición no autorizado")
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(401, "Sesión no válida")
    return user


UserDep = Annotated[User, Depends(current_user)]


def admin_user(user: UserDep):
    if not user.is_admin:
        raise HTTPException(403, "Esta operación requiere un administrador")
    return user


AdminDep = Annotated[User, Depends(admin_user)]
