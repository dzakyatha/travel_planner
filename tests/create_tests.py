# skrip untuk test CREATE API endpoints

import pytest
from fastapi.testclient import TestClient
from main import app
from tests.utils import sample_rencana_data

# setup test client
client = TestClient(app)

# test membuat RencanaPerjalanan baru - sukses
def test_create_rencana_perjalanan_success(sample_rencana_data):
    response = client.post("/api/perencanaan/", json=sample_rencana_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["nama"] == sample_rencana_data["nama"]
    assert data["durasi"]["tanggalMulai"] == sample_rencana_data["durasi"]["tanggalMulai"]
    assert data["anggaran"]["jumlah"] == sample_rencana_data["anggaran"]["jumlah"]
    assert "id" in data

# test membuat RencanaPerjalanan dengan durasi tidak valid
def test_create_rencana_perjalanan_invalid_durasi():
    data = {
        "nama": "Test",
        "durasi": {
            "tanggalMulai": "2024-12-07",
            "tanggalSelesai": "2024-12-01"  # tanggalMulai > tanggalSelesai
        },
        "anggaran": {
            "jumlah": 1000000,
            "mata_uang": "IDR"
        }
    }

    response = client.post("/api/perencanaan/", json=data)
    assert response.status_code == 422

# test membuat RencanaPerjalanan dengan jumlah uang negatif
def test_create_rencana_perjalanan_negative_uang():
    """T"""
    data = {
        "nama": "Test",
        "durasi": {
            "tanggalMulai": "2024-12-01",
            "tanggalSelesai": "2024-12-07"
        },
        "anggaran": {
            "jumlah": -1000,  # negatif
            "mata_uang": "IDR"
        }
    }
    
    response = client.post("/api/perencanaan/", json=data)
    assert response.status_code == 422