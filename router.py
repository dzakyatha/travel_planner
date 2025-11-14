# skrip berisikan router & endpoint API

from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from typing import List
from datetime import date

# model domain
from models.aggregate_root import RencanaPerjalanan
from models.entity import HariPerjalanan, Aktivitas, Pengeluaran
from models.exception import AnggaranTerlampauiException, AktivitasKonflikException, TanggalDiLuarDurasiException

# API Schema
from schema import RencanaPerjalananCreate, HariPerjalananCreate, PengeluaranCreate, AktivitasCreate, AnggaranUpdate, DurasiUpdate

# Database sederhana (Dictionary)
db_rencana_perjalanan: dict[UUID, RencanaPerjalanan] = {}

router = APIRouter(
    prefix="/perencanaan",
    tags=["Perencanaan Perjalanan"]
)

# API untuk membuat RencanaPerjalanan baru
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RencanaPerjalanan)
def create_rencana_perjalanan(request: RencanaPerjalananCreate) -> RencanaPerjalanan:
    try:
        # Membuat objek domain dari skema request
        rencana_baru = RencanaPerjalanan(
            nama=request.nama,
            durasi=request.durasi,
            anggaran=request.anggaran
        )
        
        # Menyimpan ke database
        db_rencana_perjalanan[rencana_baru.id] = rencana_baru
        
        return rencana_baru

    except ValueError as e:
        # Menangkap error validasi dari Value Object
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# API untuk mendapatkan RencanaPerjalanan berdasarkan ID
@router.get("/{rencana_id}", response_model=RencanaPerjalanan)
def get_rencana_perjalanan(rencana_id: UUID) -> RencanaPerjalanan:

    # mengambil rencana dari database
    rencana = db_rencana_perjalanan.get(rencana_id)

    # jika rencana tidak ditemukan
    if not rencana:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rencana Perjalanan dengan ID {rencana_id} tidak ditemukan"
        )

    return rencana

# API untuk menambahkan HariPerjalanan ke RencanaPerjalanan
@router.post("/{rencana_id}/hari", response_model=RencanaPerjalanan)
def add_hari_perjalanan_ke_rencana(rencana_id: UUID, request: HariPerjalananCreate) -> RencanaPerjalanan:
    # mencari rencana perjalanan berdasarkan ID
    rencana = get_rencana_perjalanan(rencana_id)

    try:
        # panggil method menambah HariPerjalanan dari rencana
        rencana.tambahHariPerjalanan(tanggal=request.tanggal)
        
        # simpan perubahan
        db_rencana_perjalanan[rencana_id] = rencana
        
        return rencana
        
    # menangkap exception
    except TanggalDiLuarDurasiException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk menambahkan Pengeluaran ke RencanaPerjalanan
@router.post("/{rencana_id}/pengeluaran", response_model=RencanaPerjalanan)
def add_pengeluaran_ke_rencana(rencana_id: UUID, request: PengeluaranCreate) -> RencanaPerjalanan:
    # mencari RencanaPerjalanan berdasarkan ID
    rencana = get_rencana_perjalanan(rencana_id)

    try:
        # Buat objek Pengeluaran dari request
        pengeluaran_baru = Pengeluaran(
            deskripsi=request.deskripsi,
            biaya=request.biaya,
            tanggalPengeluaran=request.tanggalPengeluaran
        )

        # panggil method tambah Pengeluaran dari rencan
        rencana.tambahPengeluaran(pengeluaran_baru)
        
        # simpan perubahan
        db_rencana_perjalanan[rencana_id] = rencana
        
        return rencana

    # menangkap exception
    except AnggaranTerlampauiException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e: # error dari value objects
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk menambahkan Aktivitas ke HariPerjalanan
@router.post("/{rencana_id}/hari/{tanggal}/aktivitas", response_model=RencanaPerjalanan)
def add_aktivitas_ke_hari(rencana_id: UUID, tanggal: date, request: AktivitasCreate) -> RencanaPerjalanan:
    # mencari RencanaPerjalanan berdasarkan ID
    rencana = get_rencana_perjalanan(rencana_id)
    
    # cari HariPerjalanan berdasarkan tanggal
    hari = rencana.getHariPerjalanan(tanggal)
    if not hari:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hari perjalanan pada tanggal {tanggal} tidak ditemukan dalam rencana perjalanan"
        )
    
    try:
        # buat objek Aktivitas dari request
        aktivitas_baru = Aktivitas(
            waktuMulai=request.waktuMulai,
            waktuSelesai=request.waktuSelesai,
            lokasi=request.lokasi,
            deskripsi=request.deskripsi
        )
        
        # panggil method untuk menambah aktivitas dari HariPerjalanan
        hari.tambahAktivitas(aktivitas_baru)
        
        # simpan perubahan
        db_rencana_perjalanan[rencana_id] = rencana
        
        return rencana
        
    # menangkap exception
    except AktivitasKonflikException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e: # error dari value objects
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk mengupdate Anggaran RencanaPerjalanan
@router.put("/{rencana_id}/anggaran", response_model=RencanaPerjalanan)
def update_anggaran_rencana(rencana_id: UUID, request: AnggaranUpdate) -> RencanaPerjalanan:
    # mencari RencanaPerjalanan berdasarkan ID
    rencana = get_rencana_perjalanan(rencana_id)
    
    try:
        # panggil method untuk kelola Anggaran dari rencana
        rencana.setAnggaran(request.anggaranBaru)
        
        # simpan perubahan
        db_rencana_perjalanan[rencana_id] = rencana
        return rencana
        
    # menangkap exception
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk mengupdate Durasi RencanaPerjalanan
@router.put("/{rencana_id}/durasi", response_model=RencanaPerjalanan)
def update_durasi_rencana(rencana_id: UUID, request: DurasiUpdate) -> RencanaPerjalanan:
    # mencari RencanaPerjalanan berdasarkan ID
    rencana = get_rencana_perjalanan(rencana_id)
    
    try:
        # panggil method untuk kelola durasi dari rencana
        rencana.setDurasi(request.durasiBaru)
        
        # simpan perubahan
        db_rencana_perjalanan[rencana_id] = rencana
        return rencana
        
    # menangkap exception
    except TanggalDiLuarDurasiException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk menghapus HariPerjalanan dari Rencana Perjalanan
@router.delete("/{rencana_id}/hari/{tanggal}", response_model=RencanaPerjalanan)
def delete_hari_perjalanan(rencana_id: UUID, tanggal: date) -> RencanaPerjalanan:
    # mencari RencanaPerjalanan berdasarkan ID
    rencana = get_rencana_perjalanan(rencana_id)
    
    # panggil method untuk hapus HariPerjalanan dari rencana
    hari_perjalanan = rencana.hapusHariPerjalanan(tanggal)
    
    # jika HariPerjalanan tidak ditemukan
    if not hari_perjalanan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hari perjalanan dengan tanggal {tanggal} tidak ditemukan"
        )
    
    # simpan perubahan
    db_rencana_perjalanan[rencana_id] = rencana

    return rencana

# API untuk menghapus Pengeluaran dari RencanaPerjalanan
@router.delete("/{rencana_id}/pengeluaran/{id_pengeluaran}", response_model=RencanaPerjalanan)
def delete_pengeluaran(rencana_id: UUID, id_pengeluaran: UUID) -> RencanaPerjalanan:
    # mencari RencanaPerjalanan berdasarkan ID
    rencana = get_rencana_perjalanan(rencana_id)
    
    # panggil method untuk hapus Pengeluaran dari rencana berdasarkan ID
    pengeluaran = rencana.hapusPengeluaran(id_pengeluaran)
    
    # jika Pengeluaran tidak ada
    if not pengeluaran:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pengeluaran dengan ID {id_pengeluaran} tidak ditemukan"
        )
    
    # simpan perubahan
    db_rencana_perjalanan[rencana_id] = rencana

    return rencana