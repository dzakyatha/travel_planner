# skrip berisi helper functions untuk test

def create_sample_rencana(client, auth_headers, data=None):
    if data is None:
        data = {
            "nama": "Test Rencana",
            "durasi": {
                "tanggalMulai": "2024-12-01",
                "tanggalSelesai": "2024-12-07"
            },
            "anggaran": {
                "jumlah": 5000000.0,
                "mata_uang": "IDR"
            }
        }
    
    response = client.post(
        "/api/perencanaan/",
        json=data,
        headers=auth_headers
    )
    return response.json()

def create_sample_hari(client, rencana_id, auth_headers, tanggal="2024-12-03"):
    hari_data = {"tanggal": tanggal}
    response = client.post(
        f"/api/perencanaan/{rencana_id}/hari",
        json=hari_data,
        headers=auth_headers
    )
    return response.json()

def create_sample_aktivitas(client, rencana_id, tanggal, auth_headers, lokasi=None):
    if lokasi is None:
        lokasi = {
            "namaLokasi": "Default Location",
            "alamat": "Default Address",
            "latitude": 0.0,
            "longitude": 0.0
        }
    
    aktivitas_data = {
        "waktuMulai": "09:00:00",
        "waktuSelesai": "11:00:00",
        "deskripsi": "Sample Activity",
        "lokasi": lokasi
    }
    
    response = client.post(
        f"/api/perencanaan/{rencana_id}/hari/{tanggal}/aktivitas",
        json=aktivitas_data,
        headers=auth_headers
    )
    return response.json()

def create_sample_pengeluaran(client, rencana_id, auth_headers):
    pengeluaran_data = {
        "deskripsi": "Sample Expense",
        "biaya_jumlah": 1000000.0,
        "biaya_mata_uang": "IDR",
        "tanggalPengeluaran": "2024-12-02"
    }
    
    response = client.post(
        f"/api/perencanaan/{rencana_id}/pengeluaran",
        json=pengeluaran_data,
        headers=auth_headers
    )
    return response.json()