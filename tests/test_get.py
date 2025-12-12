# skrip untuk test GET API endpoints
import pytest
from uuid import uuid4

# test mendapatkan RencanaPerjalanan - sukses
def test_get_rencana_perjalanan_success(client, sample_rencana_data, auth_headers):
    # membuat sebuah rencana terlebih dulu
    create_response = client.post(
        "/api/perencanaan/", 
        json=sample_rencana_data,
        headers=auth_headers
    )
    rencana_id = create_response.json()["id"]
    
    # mendapatkan rencana
    response = client.get(f"/api/perencanaan/{rencana_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rencana_id
    assert data["nama"] == sample_rencana_data["nama"]

# test mendapatkan RencanaPerjalanan - tidak ditemukan
def test_get_rencana_perjalanan_not_found(client, auth_headers):
    fake_id = str(uuid4())
    response = client.get(f"/api/perencanaan/{fake_id}", headers=auth_headers)
    assert response.status_code == 404

# test mendapatkan RencanaPerjalanan tanpa autentikasi
def test_get_rencana_perjalanan_unauthorized(client, sample_rencana_data, auth_headers):
    create_response = client.post(
        "/api/perencanaan/", 
        json=sample_rencana_data,
        headers=auth_headers
    )
    
    if create_response.status_code == 201:
        rencana_id = create_response.json()["id"]
        response = client.get(f"/api/perencanaan/{rencana_id}")
        assert response.status_code == 401

# test mendapatkan RencanaPerjalanan dengan ID invalid
def test_get_rencana_perjalanan_invalid_id(client, auth_headers):
    response = client.get("/api/perencanaan/invalid-uuid", headers=auth_headers)
    assert response.status_code == 422  # Validation error