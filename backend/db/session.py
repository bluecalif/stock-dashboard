from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings

engine = (
    create_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=(settings.log_level == "DEBUG"),
    )
    if settings.database_url
    else None
)

SessionLocal = sessionmaker(bind=engine) if engine else None
