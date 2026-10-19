import argparse
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from .config import Settings
from .database import make_engine, factory
from .models import User, Order, utcnow
from .security import hash_password
from .seed import seed
from .services.commerce import expire_order


def migration_config(url=None):
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    if url:
        cfg.attributes["url"] = url
    return cfg


def main():
    parser = argparse.ArgumentParser(description="Administración local de la tienda")
    parser.add_argument("action", choices=["migrate", "seed", "expire", "create-admin", "audit"])
    parser.add_argument("--email")
    parser.add_argument("--name", default="Administrador")
    args = parser.parse_args()
    settings = Settings()
    if args.action == "migrate":
        command.upgrade(migration_config(), "head")
        return
    engine = make_engine(settings.database_url)
    with factory(engine)() as db:
        if args.action == "seed":
            seed(db)
        elif args.action == "expire":
            # Solo demo/PaymentIntent local: Checkout real se libera al recibir
            # checkout.session.expired, evitando expirar un pago aún no notificado.
            statement = select(Order).where(Order.status == "pending_payment", Order.payment_expires_at < utcnow())
            if settings.payment_mode == "stripe":
                statement = statement.where(Order.checkout_session_id.is_(None), Order.payment_intent_id.is_(None))
            count = 0
            for order in db.scalars(statement.with_for_update()):
                count += expire_order(db, order)
            db.commit()
            print(f"{count} reservas caducadas liberadas")
        elif args.action == "create-admin":
            import getpass

            email = args.email or settings.demo_admin_email
            if not email or "@" not in email:
                parser.error("Indica --email con un email válido")
            if db.scalar(select(User).where(User.email == email.lower())):
                parser.error("Ese usuario ya existe; no se cambia su rol automáticamente")
            password = getpass.getpass("Contraseña del administrador (mínimo 10 caracteres): ")
            if len(password) < 10:
                parser.error("Contraseña demasiado corta")
            db.add(User(email=email.lower(), name=args.name, password_hash=hash_password(password), is_admin=True))
            db.commit()
        else:
            from sqlalchemy import text

            print({"database": db.execute(text("SELECT 1")).scalar(), "payment_mode": settings.payment_mode, "version": settings.version})
    engine.dispose()


if __name__ == "__main__":
    main()
