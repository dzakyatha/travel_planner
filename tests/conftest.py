# skrip konfigurasi fixture untuk testing

import pytest
import os
import sys
from pathlib import Path
from datetime import timedelta

# test environment variables sebelum import
os.environ["SECRET_KEY"] = "test-secret-key-at-least-32-characters-long-for-testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# tambahkan root project ke Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient
from main import app
from database import get_session
from security.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

# ==================== Database Fixtures ====================

# buat database SQLite in-memory untuk testing
@pytest.fixture(name="session", scope="function")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session
    
    SQLModel.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture(name="client", scope="function")
def client_fixture(session: Session):
    def get_session_override():
        yield session
    
    app.dependency_overrides[get_session] = get_session_override
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

# ==================== Authentication Fixtures ====================

@pytest.fixture
def auth_token():
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": "johndoe"}, 
        expires_delta=access_token_expires
    )
    return token

@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}

# ==================== Data Fixtures ====================

@pytest.fixture
def sample_rencana_data():
    """Fixture untuk data RencanaPerjalanan yang valid"""
    return {
        "nama": "Liburan ke Bali",
        "durasi": {
            "tanggalMulai": "2024-12-01",  # Changed from tanggal_mulai
            "tanggalSelesai": "2024-12-07"  # Changed from tanggal_selesai
        },
        "anggaran": {
            "jumlah": 5000000.0,
            "mata_uang": "IDR"
        }
    }

@pytest.fixture
def sample_rencana_data_flat():
    """Sample data with flat structure (if API uses flat format)"""
    return {
        "nama": "Liburan ke Bali",
        "durasi_mulai": "2024-12-01",
        "durasi_selesai": "2024-12-07",
        "anggaran_jumlah": 5000000.0,
        "anggaran_mata_uang": "IDR"
    }

@pytest.fixture
def sample_lokasi():
    return {
        "namaLokasi": "Pantai Kuta",
        "alamat": "Kuta, Bali",
        "latitude": -8.7224,
        "longitude": 115.1707
    }