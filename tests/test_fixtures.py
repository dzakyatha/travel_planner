def test_client_fixture(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_auth_headers_fixture(auth_headers):
    assert "Authorization" in auth_headers
    assert auth_headers["Authorization"].startswith("Bearer ")

def test_sample_data_fixture(sample_rencana_data):
    assert "nama" in sample_rencana_data
    assert "durasi" in sample_rencana_data
    assert "tanggalMulai" in sample_rencana_data["durasi"]  # Changed from tanggal_mulai
    assert "tanggalSelesai" in sample_rencana_data["durasi"]  # Changed from tanggal_selesai
    assert "anggaran" in sample_rencana_data
    assert "jumlah" in sample_rencana_data["anggaran"]
    assert "mata_uang" in sample_rencana_data["anggaran"]