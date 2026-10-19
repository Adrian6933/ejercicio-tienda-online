from dataclasses import dataclass, field
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@dataclass
class Settings:
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./tienda.db"))
    cors_origins: str = field(default_factory=lambda: os.getenv("CORS_ORIGIN", "http://localhost:5173,http://127.0.0.1:5173"))
    public_web_url: str = field(default_factory=lambda: os.getenv("PUBLIC_WEB_URL", "http://localhost:5173"))
    payment_mode: str = field(default_factory=lambda: os.getenv("PAYMENT_MODE", "demo"))
    stripe_secret_key: str = field(default_factory=lambda: os.getenv("STRIPE_SECRET_KEY", ""))
    stripe_webhook_secret: str = field(default_factory=lambda: os.getenv("STRIPE_WEBHOOK_SECRET", ""))
    cookie_secure: bool = field(default_factory=lambda: os.getenv("COOKIE_SECURE", "false").lower() == "true")
    log_file: str = field(default_factory=lambda: os.getenv("LOG_FILE", "logs/tienda.jsonl"))
    version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "local"))
    demo_admin_email: str = field(default_factory=lambda: os.getenv("ADMIN_EMAIL", ""))
    session_hours: int = 24
    payment_minutes: int = 30

    @property
    def origins(self):
        return [s.strip().rstrip("/") for s in self.cors_origins.split(",") if s.strip()]

    def validate(self):
        if self.payment_mode not in {"demo", "stripe"}:
            raise ValueError("PAYMENT_MODE debe ser demo o stripe")
        if self.payment_mode == "stripe" and not self.stripe_secret_key.startswith("sk_test_"):
            raise ValueError("Esta práctica solo admite claves Stripe de prueba sk_test_")
        if "*" in self.origins:
            raise ValueError("CORS debe enumerar orígenes concretos, sin comodines")
        if self.cookie_secure and not self.public_web_url.startswith("https://"):
            raise ValueError("COOKIE_SECURE necesita una web HTTPS")
