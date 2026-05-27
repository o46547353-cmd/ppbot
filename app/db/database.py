from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.models import Base

# SQLite database URL for development
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./sqlite.db"

# Create async engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, # Needed for SQLite
    echo=True, # Log SQL queries
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False
)

async def init_models():
    """
    Initializes database tables.
    """
    async with engine.begin() as conn:
        # Create all tables defined in Base.metadata
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """
    Dependency for getting a database session.
    """
    async with AsyncSessionLocal() as session:
        yield session
