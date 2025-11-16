# skrip untuk test GET API endpoints

import pytest
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4
from tests.utils import sample_rencana_data

# Setup test client
client = TestClient(app)

# test mendapatkan RencanaPerjalanan - sukses
def test_get_rencana_perjalanan_success(sample_rencana_data):
    # membuat sebuah rencana terlebih dulu
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    # mendapatkan rencana
    response = client.get(f"/api/perencanaan/{rencana_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rencana_id
    assert data["nama"] == sample_rencana_data["nama"]

# test mendapatkan RencanaPerjalanan - tidak ditemukan
def test_get_rencana_perjalanan_not_found():
    fake_id = str(uuid4())
    response = client.get(f"/api/perencanaan/{fake_id}")
    
    assert response.status_code == 404