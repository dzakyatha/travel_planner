# skrip untuk test DELETE API endpoints

import pytest
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4
from tests.utils import sample_rencana_data

# Setup test client
client = TestClient(app)

# test menghapus HariPerjalanan - sukses
def test_delete_hari_perjalanan_success(sample_rencana_data):
    # buat rencana perjalanan dan tambahkan hari
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    hari_data = {"tanggal": "2024-12-01"}
    client.post(f"/api/perencanaan/{rencana_id}/hari", json=hari_data)
    
    # hapus hari
    response = client.delete(f"/api/perencanaan/{rencana_id}/hari/2024-12-01")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["hariPerjalananList"]) == 0

# test menghapus HariPerjalanan yang tidak ada
def test_delete_hari_perjalanan_not_found(sample_rencana_data):
    # buat rencana tanpa hari
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    # hapus hari yang tidak ada
    response = client.delete(f"/api/perencanaan/{rencana_id}/hari/2024-12-01")
    
    assert response.status_code == 404

# test menghapus Pengeluaran - sukses
def test_delete_pengeluaran_success(sample_rencana_data):
    # buat rencana dan tambah pengeluaran
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    pengeluaran_data = {
        "deskripsi": "Pengeluaran",
        "biaya": {"jumlah": 1000000, "mata_uang": "IDR"},
        "tanggalPengeluaran": "2024-12-01"
    }
    add_response = client.post(
        f"/api/perencanaan/{rencana_id}/pengeluaran",
        json=pengeluaran_data
    )
    pengeluaran_id = add_response.json()["pengeluaranList"][0]["idPengeluaran"]
    
    # hapus pengeluaran
    response = client.delete(
        f"/api/perencanaan/{rencana_id}/pengeluaran/{pengeluaran_id}"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["pengeluaranList"]) == 0

# test menghapus Pengeluaran yang tidak ada
def test_delete_pengeluaran_not_found(sample_rencana_data):
    # buat rencana tanpa pengeluaran
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    fake_id = str(uuid4())
    # hapus pengeluaran yang tidak ada
    response = client.delete(
        f"/api/perencanaan/{rencana_id}/pengeluaran/{fake_id}"
    )
    
    assert response.status_code == 404
