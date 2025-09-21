from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool
from .config import settings

engine = create_async_engine(
    settings.database_url,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.environment == "development",
)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()


async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)