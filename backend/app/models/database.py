from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+aiomysql://overhang:overhang@db/overhang")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_recycle=3600,  # recycle connections after 1h (before MariaDB's wait_timeout)
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
