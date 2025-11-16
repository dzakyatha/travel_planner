# skrip untuk test POST API endpoints

import pytest
from fastapi.testclient import TestClient
from main import app
from tests.utils import sample_rencana_data, sample_lokasi

# Setup test client
client = TestClient(app)

# test menambahkan HariPerjalanan - sukses
def test_add_hari_perjalanan_success(sample_rencana_data):
    # buat rencana perjalanan terlebih dulu
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    # menambahkan hari
    hari_data = {"tanggal": "2024-12-01"}
    response = client.post(f"/api/perencanaan/{rencana_id}/hari", json=hari_data)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["hariPerjalananList"]) == 1
    assert data["hariPerjalananList"][0]["tanggal"] == "2024-12-01"

# test menambahkan HariPerjalanan di luar durasi rencana
def test_add_hari_perjalanan_outside_duration(sample_rencana_data):
    # membuat rencana perjalanan terlebih dulu
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    # menambahkan hari dengan tanggal di luar durasi rencana
    hari_data = {"tanggal": "2024-12-10"} 
    response = client.post(f"/api/perencanaan/{rencana_id}/hari", json=hari_data)
    
    assert response.status_code == 400

# test menambahkan HariPerjalanan duplikat
def test_add_hari_perjalanan_duplicate(sample_rencana_data):
    # membuat rencana perjalanan terlebih dulu
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    # menambahkan hari pertama
    hari_data = {"tanggal": "2024-12-01"}
    client.post(f"/api/perencanaan/{rencana_id}/hari", json=hari_data)
    
    # menambahkan hari yang sama (duplikat)
    response = client.post(f"/api/perencanaan/{rencana_id}/hari", json=hari_data)
    
    assert response.status_code == 500

# test menambahkan Aktivitas - sukses
def test_add_aktivitas_success(sample_rencana_data, sample_lokasi):
    # membuat rencana perjalanan dan hari
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    hari_data = {"tanggal": "2024-12-01"}
    client.post(f"/api/perencanaan/{rencana_id}/hari", json=hari_data)
    
    # menambahkan aktivitas
    aktivitas_data = {
        "waktuMulai": "09:00:00",
        "waktuSelesai": "12:00:00",
        "lokasi": sample_lokasi,
        "deskripsi": "Berjemur di pantai"
    }
    response = client.post(
        f"/api/perencanaan/{rencana_id}/hari/2024-12-01/aktivitas",
        json=aktivitas_data
    )
    
    assert response.status_code == 200
    data = response.json()
    hari = next(h for h in data["hariPerjalananList"] if h["tanggal"] == "2024-12-01")
    assert len(hari["aktivitasList"]) == 1
    assert hari["aktivitasList"][0]["deskripsi"] == "Berjemur di pantai"

# test menambahkan Aktivitas dengan waktu tumpang tindih dengan Aktivitas lain
def test_add_aktivitas_conflict(sample_rencana_data, sample_lokasi):
    # membuat rencana dan hari
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    hari_data = {"tanggal": "2024-12-01"}
    client.post(f"/api/perencanaan/{rencana_id}/hari", json=hari_data)
    
    # menambahkan aktivitas pertama
    aktivitas1 = {
        "waktuMulai": "09:00:00",
        "waktuSelesai": "12:00:00",
        "lokasi": sample_lokasi,
        "deskripsi": "Aktivitas 1"
    }
    client.post(
        f"/api/perencanaan/{rencana_id}/hari/2024-12-01/aktivitas",
        json=aktivitas1
    )
    
    # menambahkan aktivitas kedua dengan waktu yang tumpang tindih 
    aktivitas2 = {
        "waktuMulai": "10:00:00", 
        "waktuSelesai": "13:00:00",
        "lokasi": sample_lokasi,
        "deskripsi": "Aktivitas 2"
    }
    response = client.post(
        f"/api/perencanaan/{rencana_id}/hari/2024-12-01/aktivitas",
        json=aktivitas2
    )
    
    assert response.status_code == 400

# test menambahkan Aktivitas dengan waktu tidak valid
def test_add_aktivitas_invalid_time(sample_rencana_data, sample_lokasi):
    # membuat rencana dan hari
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    hari_data = {"tanggal": "2024-12-01"}
    client.post(f"/api/perencanaan/{rencana_id}/hari", json=hari_data)
    
    # menambahkan aktivitas dengan waktu mulai > waktu selesai
    aktivitas_data = {
        "waktuMulai": "12:00:00",
        "waktuSelesai": "09:00:00", 
        "lokasi": sample_lokasi,
        "deskripsi": "Aktivitas invalid"
    }
    response = client.post(
        f"/api/perencanaan/{rencana_id}/hari/2024-12-01/aktivitas",
        json=aktivitas_data
    )
    
    assert response.status_code == 400

# test menambahkan Aktivitas ke hari yang tidak ada
def test_add_aktivitas_hari_not_found(sample_rencana_data, sample_lokasi):
    # buat rencana tanpa hari
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    # tambah aktivitas ke hari yang tidak ada
    aktivitas_data = {
        "waktuMulai": "09:00:00",
        "waktuSelesai": "12:00:00",
        "lokasi": sample_lokasi,
        "deskripsi": "Aktivitas"
    }
    response = client.post(
        f"/api/perencanaan/{rencana_id}/hari/2024-12-01/aktivitas",
        json=aktivitas_data
    )
    
    assert response.status_code == 404

# test menambahkan Pengeluaran - sukses
def test_add_pengeluaran_success(sample_rencana_data):
    # buat rencana terlebih dulu
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    # tambah pengeluaran
    pengeluaran_data = {
        "deskripsi": "Tiket pesawat",
        "biaya": {
            "jumlah": 2000000,
            "mata_uang": "IDR"
        },
        "tanggalPengeluaran": "2024-12-01"
    }
    response = client.post(
        f"/api/perencanaan/{rencana_id}/pengeluaran",
        json=pengeluaran_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["pengeluaranList"]) == 1
    assert data["pengeluaranList"][0]["deskripsi"] == "Tiket pesawat"

# test menambahkan Pengeluaran yang melebihi anggaran
def test_add_pengeluaran_exceeds_budget(sample_rencana_data):
    # membuat rencana dengan anggaran
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    # menambah pengeluaran yang melebihi anggaran
    pengeluaran_data = {
        "deskripsi": "Pengeluaran besar",
        "biaya": {
            "jumlah": 6000000,  # melebihi anggaran (>5000000)
            "mata_uang": "IDR"
        },
        "tanggalPengeluaran": "2024-12-01"
    }
    response = client.post(
        f"/api/perencanaan/{rencana_id}/pengeluaran",
        json=pengeluaran_data
    )
    
    assert response.status_code == 400

# test menambahkan Pengeluaran di luar durasi
def test_add_pengeluaran_outside_duration(sample_rencana_data):
    # membuat rencana terlebih dulu
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    # menambah pengeluaran di luar durasi
    pengeluaran_data = {
        "deskripsi": "Pengeluaran",
        "biaya": {
            "jumlah": 1000000,
            "mata_uang": "IDR"
        },
        "tanggalPengeluaran": "2024-12-10"  # di luar durasi
    }
    response = client.post(
        f"/api/perencanaan/{rencana_id}/pengeluaran",
        json=pengeluaran_data
    )
    
    assert response.status_code == 400

# test mengupdate anggaran - sukses
def test_update_anggaran_success(sample_rencana_data):
    # membuat rencana dan tambah pengeluaran
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    pengeluaran_data = {
        "deskripsi": "Pengeluaran",
        "biaya": {"jumlah": 2000000, "mata_uang": "IDR"},
        "tanggalPengeluaran": "2024-12-01"
    }
    client.post(f"/api/perencanaan/{rencana_id}/pengeluaran", json=pengeluaran_data)
    
    # update anggaran
    update_data = {
        "anggaranBaru": {
            "jumlah": 10000000,
            "mata_uang": "IDR"
        }
    }
    response = client.put(f"/api/perencanaan/{rencana_id}/anggaran", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["anggaran"]["jumlah"] == 10000000

# test mengupdate anggaran di bawah total pengeluaran
def test_update_anggaran_below_expenses(sample_rencana_data):
    # membuat rencana dan tambah pengeluaran
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    pengeluaran_data = {
        "deskripsi": "Pengeluaran",
        "biaya": {"jumlah": 3000000, "mata_uang": "IDR"},
        "tanggalPengeluaran": "2024-12-01"
    }
    client.post(f"/api/perencanaan/{rencana_id}/pengeluaran", json=pengeluaran_data)
    
    # update anggaran di bawah pengeluaran
    update_data = {
        "anggaranBaru": {
            "jumlah": 2000000,  # < 3000000
            "mata_uang": "IDR"
        }
    }
    response = client.put(f"/api/perencanaan/{rencana_id}/anggaran", json=update_data)
    
    assert response.status_code == 400

# test mengupdate durasi - sukses
def test_update_durasi_success(sample_rencana_data):
    # membuat rencana dan tambah hari
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    hari_data = {"tanggal": "2024-12-02"}
    client.post(f"/api/perencanaan/{rencana_id}/hari", json=hari_data)
    
    # update durasi
    update_data = {
        "durasiBaru": {
            "tanggalMulai": "2024-12-01",
            "tanggalSelesai": "2024-12-10"
        }
    }
    response = client.put(f"/api/perencanaan/{rencana_id}/durasi", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["durasi"]["tanggalSelesai"] == "2024-12-10"

# test mengupdate durasi yang mengecualikan hari yang ada
def test_update_durasi_invalid(sample_rencana_data):
    # membuat rencana dan menambah hari
    create_response = client.post("/api/perencanaan/", json=sample_rencana_data)
    rencana_id = create_response.json()["id"]
    
    hari_data = {"tanggal": "2024-12-05"}
    client.post(f"/api/perencanaan/{rencana_id}/hari", json=hari_data)
    
    # update durasi
    update_data = {
        "durasiBaru": {
            "tanggalMulai": "2024-12-01",
            "tanggalSelesai": "2024-12-03"  # tanggal 05 berada di luar durasi baru
        }
    }
    response = client.put(f"/api/perencanaan/{rencana_id}/durasi", json=update_data)
    
    assert response.status_code == 400
