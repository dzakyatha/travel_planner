# skrip berisi fixture untuk test

import pytest
from router import db_rencana_perjalanan

# Fixture untuk membersihkan database sebelum setiap test
@pytest.fixture(autouse=True)
def clear_database():
    db_rencana_perjalanan.clear()
    yield
    db_rencana_perjalanan.clear()

# Fixture data sampel rencana untuk test
@pytest.fixture
def sample_rencana_data():
    return {
        "nama": "Liburan ke Bali",
        "durasi": {
            "tanggalMulai": "2024-12-01",
            "tanggalSelesai": "2024-12-07"
        },
        "anggaran": {
            "jumlah": 5000000,
            "mata_uang": "IDR"
        }
    }

# Fixture data sampel lokasi untuk test
@pytest.fixture
def sample_lokasi():
    return {
        "namaLokasi": "Pantai Kuta",
        "alamat": "Kuta, Bali",
        "latitude": -8.7224,
        "longitude": 115.1707
    }