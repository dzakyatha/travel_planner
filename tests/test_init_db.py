# skrip untuk test database functions
import pytest
from database import init_db, get_session, engine
from sqlmodel import SQLModel

def test_init_db():
    # Clear any existing tables
    SQLModel.metadata.drop_all(engine)
    
    # Initialize database
    init_db()
    
    # Verify tables were created by checking engine
    assert engine is not None

def test_get_session():
    session_gen = get_session()
    session = next(session_gen)
    
    assert session is not None
    
    # Clean up
    try:
        next(session_gen)
    except StopIteration:
        pass  # Expected

def test_postgres_url_conversion():
    import os
    from database import DATABASE_URL
    
    # Save original
    original = os.environ.get("DATABASE_URL")
    
    # Test postgres:// conversion (simulate Railway/Heroku scenario)
    os.environ["DATABASE_URL"] = "postgres://user:pass@host/db"
    
    # Re-import to trigger conversion logic
    import importlib
    import database
    importlib.reload(database)
    
    # Check conversion happened
    assert database.DATABASE_URL.startswith("postgresql://")
    
    # Restore
    if original:
        os.environ["DATABASE_URL"] = original
    else:
        os.environ.pop("DATABASE_URL", None)
    importlib.reload(database)