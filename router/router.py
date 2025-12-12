# skrip berisikan router & endpoint API

from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from uuid import UUID
from typing import List
from datetime import date

# model domain
from models.aggregate_root import RencanaPerjalanan
from models.entity import HariPerjalanan, Aktivitas, Pengeluaran
from models.exception import AnggaranTerlampauiException, AktivitasKonflikException, TanggalDiLuarDurasiException

# API Schema
from schema import RencanaPerjalananCreate, HariPerjalananCreate, PengeluaranCreate, AktivitasCreate, AnggaranUpdate, DurasiUpdate, RencanaPerjalananCreate

# import security
from security import get_current_user

# import Database
from database import get_session, get_db

# router utama
router = APIRouter(
    prefix="/perencanaan",
    tags=["Perencanaan Perjalanan"]
)

# Helper function untuk mendapatkan rencana dari database
def _get_rencana_dari_db(rencana_id: UUID, session: Session) -> RencanaPerjalanan:
    rencana = session.get(RencanaPerjalanan, rencana_id)
    if not rencana:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rencana Perjalanan dengan ID {rencana_id} tidak ditemukan"
        )
    return rencana

# API untuk membuat RencanaPerjalanan baru
@router.post("/", status_code=201)
def create_rencana_perjalanan(
    request: RencanaPerjalananCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rencana = RencanaPerjalanan(
        nama=request.nama,
        durasi_mulai=request.durasi.tanggalMulai,
        durasi_selesai=request.durasi.tanggalSelesai,
        anggaran_jumlah=request.anggaran.jumlah,
        anggaran_mata_uang=request.anggaran.mata_uang
    )
    
    # Menyimpan ke database
    db.add(rencana)
    db.commit()
    db.refresh(rencana)
    
    return {
        "id": rencana.id,
        "nama": rencana.nama,
        "durasi": {
            "tanggalMulai": rencana.durasi_mulai,
            "tanggalSelesai": rencana.durasi_selesai
        },
        "anggaran": {
            "jumlah": rencana.anggaran_jumlah,
            "mata_uang": rencana.anggaran_mata_uang
        }
    }

# API untuk mendapatkan RencanaPerjalanan berdasarkan ID
@router.get("/{rencana_id}")
def get_rencana_perjalanan(rencana_id: UUID, current_user: str = Depends(get_current_user), session: Session = Depends(get_session)):
    return _get_rencana_dari_db(rencana_id, session)

# API untuk menambahkan HariPerjalanan ke RencanaPerjalanan
@router.post("/{rencana_id}/hari")
def add_hari_perjalanan_ke_rencana(rencana_id: UUID, request: HariPerjalananCreate, current_user: str = Depends(get_current_user), session: Session = Depends(get_session)):
    rencana = _get_rencana_dari_db(rencana_id, session)

    try:
        rencana.tambahHariPerjalanan(tanggal=request.tanggal)
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        
        return rencana
        
    except TanggalDiLuarDurasiException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk menambahkan Pengeluaran ke RencanaPerjalanan
@router.post("/{rencana_id}/pengeluaran")
def add_pengeluaran_ke_rencana(rencana_id: UUID, request: PengeluaranCreate, current_user: str = Depends(get_current_user), session: Session = Depends(get_session)):  # pragma: no cover
    rencana = _get_rencana_dari_db(rencana_id, session)

    try:
        pengeluaran_baru = Pengeluaran(
            deskripsi=request.deskripsi,
            biaya_jumlah=request.biaya_jumlah,
            biaya_mata_uang=request.biaya_mata_uang,
            tanggalPengeluaran=request.tanggalPengeluaran
        )

        rencana.tambahPengeluaran(pengeluaran_baru)
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        
        return rencana

    except AnggaranTerlampauiException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except TanggalDiLuarDurasiException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk menambahkan Aktivitas ke HariPerjalanan
@router.post("/{rencana_id}/hari/{tanggal}/aktivitas")
def add_aktivitas_ke_hari(rencana_id: UUID, tanggal: date, request: AktivitasCreate, current_user: str = Depends(get_current_user), session: Session = Depends(get_session)):  # pragma: no cover
    rencana = _get_rencana_dari_db(rencana_id, session)
    
    hari = rencana.getHariPerjalanan(tanggal)
    if not hari:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hari perjalanan pada tanggal {tanggal} tidak ditemukan dalam rencana perjalanan"
        )
    
    try:
        aktivitas_baru = Aktivitas(
            waktuMulai=request.waktuMulai,
            waktuSelesai=request.waktuSelesai,
            lokasi=request.lokasi,
            deskripsi=request.deskripsi
        )
        
        hari.tambahAktivitas(aktivitas_baru)
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        
        return rencana
        
    except AktivitasKonflikException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk mengupdate Anggaran RencanaPerjalanan
@router.put("/{rencana_id}/anggaran")
def update_anggaran_rencana(rencana_id: UUID, request: AnggaranUpdate, current_user: str = Depends(get_current_user), session: Session = Depends(get_session)):  # pragma: no cover
    rencana = _get_rencana_dari_db(rencana_id, session)
    
    try:
        rencana.setAnggaran(request.jumlah, request.mata_uang)
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        return rencana
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk mengupdate Durasi RencanaPerjalanan
@router.put("/{rencana_id}/durasi")
def update_durasi_rencana(rencana_id: UUID, request: DurasiUpdate, current_user: str = Depends(get_current_user), session: Session = Depends(get_session)):  # pragma: no cover
    rencana = _get_rencana_dari_db(rencana_id, session)
    
    try:
        rencana.setDurasi(request.tanggal_mulai, request.tanggal_selesai)
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        return rencana
        
    except TanggalDiLuarDurasiException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk menghapus HariPerjalanan dari Rencana Perjalanan
@router.delete("/{rencana_id}/hari/{tanggal}")
def delete_hari_perjalanan(rencana_id: UUID, tanggal: date, current_user: str = Depends(get_current_user), session: Session = Depends(get_session)):
    rencana = _get_rencana_dari_db(rencana_id, session)
    
    hari_perjalanan = rencana.hapusHariPerjalanan(tanggal)
    
    if not hari_perjalanan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hari perjalanan dengan tanggal {tanggal} tidak ditemukan"
        )
    
    session.add(rencana)
    session.commit()
    session.refresh(rencana)

    return rencana

# API untuk menghapus Pengeluaran dari RencanaPerjalanan
@router.delete("/{rencana_id}/pengeluaran/{id_pengeluaran}")
def delete_pengeluaran(rencana_id: UUID, id_pengeluaran: UUID, current_user: str = Depends(get_current_user), session: Session = Depends(get_session)):
    rencana = _get_rencana_dari_db(rencana_id, session)
    
    pengeluaran = rencana.hapusPengeluaran(id_pengeluaran)
    
    if not pengeluaran:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pengeluaran dengan ID {id_pengeluaran} tidak ditemukan"
        )
    
    session.add(rencana)
    session.commit()
    session.refresh(rencana)

    return rencana