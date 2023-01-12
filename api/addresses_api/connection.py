from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine

from .settings import settings


def get_db():
    """Get the SQLAlchemy DB engine based on the global DB settings."""
    url = URL.create(
        "postgresql+asyncpg",
        username=settings.db_user,
        password=settings.db_pass,
        host=settings.db_host,
        database=settings.db_name,
    )
    return create_async_engine(url)
