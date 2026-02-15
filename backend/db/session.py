from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings

_url = settings.database_url
# Railway Postgres provides postgres:// but SQLAlchemy 2.x requires postgresql://
if _url.startswith("postgres://"):
    _url = _url.replace("postgres://", "postgresql://", 1)

engine = (
    create_engine(
        _url,
        pool_pre_ping=True,
        echo=(settings.log_level == "DEBUG"),
    )
    if _url
    else None
)

SessionLocal = sessionmaker(bind=engine) if engine else None
