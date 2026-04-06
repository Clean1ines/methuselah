import asyncpg
from app.core.config import settings
from app.core.logger import get_logger
from typing import Union

logger = get_logger(__name__)

class Database:
    """Manages robust async connection pooling to Postgres."""
    pool: Union[asyncpg.Pool, None] = None

    @classmethod
    async def connect(cls) -> None:
        """Initializes connection pool using central configuration safely."""
        if cls.pool is None:
            try:
                cls.pool = await asyncpg.create_pool(
                    dsn=settings.DATABASE_URL,
                    min_size=5,
                    max_size=20
                )
                logger.info("database_pool_established")
            except Exception as e:
                logger.error("database_pool_creation_failed", error=str(e))
                raise e

    @classmethod
    async def disconnect(cls) -> None:
        """Closes connection gracefully."""
        if cls.pool:
            await cls.pool.close()
            logger.info("database_pool_closed")
