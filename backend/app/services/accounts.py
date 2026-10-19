from datetime import timedelta
import secrets
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from ..models import User, LoginSession, Address, utcnow
from ..security import hash_password, verify_password, token_hash

DUMMY_HASH = hash_password("only-used-to-normalize-login-timing")


def register(db, payload):
    user = User(email=payload.email, name=payload.name, password_hash=hash_password(payload.password), is_admin=False)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "No se ha podido registrar esa cuenta")
    db.refresh(user)
    return user


def login(db, email, password, hours):
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    valid = verify_password(password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "Email o contraseña incorrectos")
    token = secrets.token_urlsafe(32)
    db.add(LoginSession(token_hash=token_hash(token), user_id=user.id, expires_at=utcnow() + timedelta(hours=hours)))
    db.commit()
    return token, user


def save_address(db, user, kind, payload):
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    db.execute(update(Address).where(Address.user_id == user.id, Address.kind == kind, Address.is_active.is_(True)).values(is_active=False))
    address = Address(user_id=user.id, kind=kind, **payload.model_dump())
    db.add(address)
    db.commit()
    return address
