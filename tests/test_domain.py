# skrip unit test untuk domain RencanaPerjalanan

import pytest
from models.aggregate_root import RencanaPerjalanan
from models.entity import Pengeluaran, HariPerjalanan, Aktivitas
from models.exception import AnggaranTerlampauiException, TanggalDiLuarDurasiException, AktivitasKonflikException
from datetime import date, time

def test_tambah_pengeluaran_exceeds_budget():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=1000,
        anggaran_mata_uang="IDR"
    )
    
    pengeluaran = Pengeluaran(
        deskripsi="Expensive",
        biaya_jumlah=2000,
        biaya_mata_uang="IDR",
        tanggalPengeluaran=date(2024, 12, 1)
    )
    
    with pytest.raises(AnggaranTerlampauiException):
        rencana.tambahPengeluaran(pengeluaran)

def test_tambah_pengeluaran_outside_duration():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000,
        anggaran_mata_uang="IDR"
    )
    
    pengeluaran = Pengeluaran(
        deskripsi="Outside",
        biaya_jumlah=500,
        biaya_mata_uang="IDR",
        tanggalPengeluaran=date(2024, 12, 15)  # Outside duration
    )
    
    with pytest.raises(TanggalDiLuarDurasiException):
        rencana.tambahPengeluaran(pengeluaran)

def test_tambah_hari_perjalanan_outside_duration():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000,
        anggaran_mata_uang="IDR"
    )
    
    with pytest.raises(TanggalDiLuarDurasiException):
        rencana.tambahHariPerjalanan(date(2024, 12, 15))

def test_aktivitas_conflict():
    hari = HariPerjalanan(tanggal=date(2024, 12, 3))
    
    aktivitas1 = Aktivitas(
        waktuMulai=time(9, 0),
        waktuSelesai=time(11, 0),
        deskripsi="Activity 1",
        lokasi={"namaLokasi": "Place 1"}
    )
    
    aktivitas2 = Aktivitas(
        waktuMulai=time(10, 0),
        waktuSelesai=time(12, 0),
        deskripsi="Activity 2",
        lokasi={"namaLokasi": "Place 2"}
    )
    
    hari.tambahAktivitas(aktivitas1)
    
    with pytest.raises(AktivitasKonflikException):
        hari.tambahAktivitas(aktivitas2)

def test_total_pengeluaran():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000,
        anggaran_mata_uang="IDR"
    )
    
    p1 = Pengeluaran(
        deskripsi="Expense 1",
        biaya_jumlah=1000,
        biaya_mata_uang="IDR",
        tanggalPengeluaran=date(2024, 12, 1)
    )
    
    p2 = Pengeluaran(
        deskripsi="Expense 2",
        biaya_jumlah=500,
        biaya_mata_uang="IDR",
        tanggalPengeluaran=date(2024, 12, 2)
    )
    
    rencana.tambahPengeluaran(p1)
    rencana.tambahPengeluaran(p2)
    
    assert rencana.totalPengeluaranSaatIni() == 1500

def test_sisa_anggaran():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000,
        anggaran_mata_uang="IDR"
    )
    
    p1 = Pengeluaran(
        deskripsi="Expense",
        biaya_jumlah=1000,
        biaya_mata_uang="IDR",
        tanggalPengeluaran=date(2024, 12, 1)
    )
    
    rencana.tambahPengeluaran(p1)
    assert rencana.getSisaAnggaran() == 4000

# test untuk getter methods
def test_get_total_pengeluaran():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    assert rencana.totalPengeluaranSaatIni() == 0.0
    
    # Tambah pengeluaran
    p1 = Pengeluaran(deskripsi="Hotel", biaya_jumlah=1000000.0, biaya_mata_uang="IDR", tanggalPengeluaran=date(2024, 12, 2))
    rencana.tambahPengeluaran(p1)
    
    assert rencana.totalPengeluaranSaatIni() == 1000000.0

def test_get_sisa_anggaran_extended():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    assert rencana.getSisaAnggaran() == 5000000.0
    
    # Tambah pengeluaran
    p1 = Pengeluaran(deskripsi="Hotel", biaya_jumlah=1000000.0, biaya_mata_uang="IDR", tanggalPengeluaran=date(2024, 12, 2))
    rencana.tambahPengeluaran(p1)
    
    assert rencana.getSisaAnggaran() == 4000000.0

def test_get_jumlah_hari_perjalanan():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    assert len(rencana.hariPerjalananList) == 0
    
    rencana.tambahHariPerjalanan(date(2024, 12, 1))
    rencana.tambahHariPerjalanan(date(2024, 12, 2))
    
    assert len(rencana.hariPerjalananList) == 2

def test_get_jumlah_pengeluaran():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    assert len(rencana.pengeluaranList) == 0
    
    p1 = Pengeluaran(deskripsi="Hotel", biaya_jumlah=1000000.0, biaya_mata_uang="IDR", tanggalPengeluaran=date(2024, 12, 2))
    rencana.tambahPengeluaran(p1)
    
    assert len(rencana.pengeluaranList) == 1

def test_set_anggaran_below_current_spending():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    
    # Add spending
    p1 = Pengeluaran(deskripsi="Hotel", biaya_jumlah=3000000.0, biaya_mata_uang="IDR", tanggalPengeluaran=date(2024, 12, 2))
    rencana.tambahPengeluaran(p1)
    
    # Try to set anggaran below current spending
    with pytest.raises(ValueError):
        rencana.setAnggaran(2000000.0, "IDR")

def test_set_anggaran_success():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    
    rencana.setAnggaran(7000000.0, "USD")
    assert rencana.anggaran_jumlah == 7000000.0
    assert rencana.anggaran_mata_uang == "USD"

def test_set_durasi_with_existing_hari():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 10),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    
    # Add hari on Dec 5
    rencana.tambahHariPerjalanan(date(2024, 12, 5))
    
    # Try to set durasi that excludes Dec 5
    with pytest.raises(TanggalDiLuarDurasiException):
        rencana.setDurasi(date(2024, 12, 6), date(2024, 12, 10))

def test_set_durasi_with_existing_pengeluaran():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 10),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    
    # Add pengeluaran on Dec 5
    p1 = Pengeluaran(deskripsi="Hotel", biaya_jumlah=1000000.0, biaya_mata_uang="IDR", tanggalPengeluaran=date(2024, 12, 5))
    rencana.tambahPengeluaran(p1)
    
    # Try to set durasi that excludes Dec 5
    with pytest.raises(TanggalDiLuarDurasiException):
        rencana.setDurasi(date(2024, 12, 6), date(2024, 12, 10))

def test_set_durasi_success():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    
    rencana.setDurasi(date(2024, 12, 1), date(2024, 12, 15))
    assert rencana.durasi_mulai == date(2024, 12, 1)
    assert rencana.durasi_selesai == date(2024, 12, 15)

def test_hapus_hari_perjalanan_not_found():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    
    result = rencana.hapusHariPerjalanan(date(2024, 12, 5))
    assert result is False

def test_hapus_pengeluaran_not_found():
    from uuid import uuid4
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    
    result = rencana.hapusPengeluaran(uuid4())
    assert result is False

def test_hapus_hari_perjalanan_success():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    
    # Add hari
    rencana.tambahHariPerjalanan(date(2024, 12, 5))
    assert len(rencana.hariPerjalananList) == 1
    
    # Delete it
    result = rencana.hapusHariPerjalanan(date(2024, 12, 5))
    assert result is True
    assert len(rencana.hariPerjalananList) == 0

def test_hapus_pengeluaran_success():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    
    # Add pengeluaran
    p1 = Pengeluaran(deskripsi="Hotel", biaya_jumlah=1000000.0, biaya_mata_uang="IDR", tanggalPengeluaran=date(2024, 12, 2))
    rencana.tambahPengeluaran(p1)
    assert len(rencana.pengeluaranList) == 1
    
    # Delete it
    result = rencana.hapusPengeluaran(p1.idPengeluaran)
    assert result is True
    assert len(rencana.pengeluaranList) == 0

def test_tambah_hari_perjalanan_success():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    
    result = rencana.tambahHariPerjalanan(date(2024, 12, 3))
    assert result is not None
    assert len(rencana.hariPerjalananList) == 1
    assert rencana.hariPerjalananList[0].tanggal == date(2024, 12, 3)

def test_tambah_pengeluaran_success():
    rencana = RencanaPerjalanan(
        nama="Test",
        durasi_mulai=date(2024, 12, 1),
        durasi_selesai=date(2024, 12, 7),
        anggaran_jumlah=5000000.0,
        anggaran_mata_uang="IDR"
    )
    
    p1 = Pengeluaran(deskripsi="Hotel", biaya_jumlah=1000000.0, biaya_mata_uang="IDR", tanggalPengeluaran=date(2024, 12, 2))
    rencana.tambahPengeluaran(p1)
    
    assert len(rencana.pengeluaranList) == 1
    assert rencana.totalPengeluaranSaatIni() == 1000000.0