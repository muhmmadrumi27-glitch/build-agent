"""Pytest configuration and fixtures."""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database import Base


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/buildagent_test"


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def sample_screenshot():
    """Create a sample screenshot for testing."""
    import numpy as np
    return np.zeros((1080, 1920, 3), dtype=np.uint8)


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "goal": "Test goal",
        "context": {
            "assumptions": [],
            "constraints": [],
        },
        "steps": [
            {
                "description": "Take screenshot",
                "action_type": "screenshot",
                "parameters": {},
                "expected_result": "Screenshot captured",
            }
        ],
    }
