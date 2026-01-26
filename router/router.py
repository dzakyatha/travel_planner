# skrip berisikan Endpoint API untuk manajemen rencana perjalanan

from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from uuid import UUID
from typing import List
from datetime import date

# Model Domain
from models.aggregate_root import RencanaPerjalanan
from models.exception import AnggaranTerlampauiException, AktivitasKonflikException, TanggalDiLuarDurasiException

# API Schema
from schema import (
    RencanaPerjalananCreate, 
    HariPerjalananCreate, 
    PengeluaranCreate, 
    AktivitasCreate, 
    AnggaranUpdate, 
    DurasiUpdate
)

# Security (Stateless Auth)
from security import get_current_user, AuthenticatedUser

# Database
from database import get_session

# Router
router = APIRouter()

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def _get_rencana(rencana_id: UUID, session: Session) -> RencanaPerjalanan:
    """
    Mengambil rencana perjalanan berdasarkan ID
    Jika tidak ditemukan, raise 404
    """
    rencana = session.get(RencanaPerjalanan, rencana_id)
    if not rencana:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rencana Perjalanan dengan ID {rencana_id} tidak ditemukan"
        )
    return rencana

def _ensure_ownership(rencana: RencanaPerjalanan, user: AuthenticatedUser):
    """
    Memastikan user yang request adalah pemilik rencana perjalanan
    Jika bukan, raise 403 Forbidden
    """
    # Pastikan membandingkan string dengan string (UUID vs str handling)
    if str(rencana.user_id) != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki izin untuk mengakses rencana ini"
        )

# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/", status_code=201, response_model=RencanaPerjalanan)
def create_rencana_perjalanan(
    rencana_data: RencanaPerjalananCreate, 
    current_user: AuthenticatedUser = Depends(get_current_user), # User didapatkan dari token JWT
    session: Session = Depends(get_session)
):
    """Membuat rencana perjalanan baru"""
    # Menggunakan user_id dari token
    baru = RencanaPerjalanan.create(
        user_id=UUID(current_user.id),  # Konversi string ID dari token ke UUID
        nama=rencana_data.nama,
        tanggal_mulai=rencana_data.tanggal_mulai,
        tanggal_selesai=rencana_data.tanggal_selesai,
        total_anggaran=rencana_data.total_anggaran
    )
    
    session.add(baru)
    session.commit()
    session.refresh(baru)
    return baru

@router.get("/", response_model=List[RencanaPerjalanan])
def read_rencana_perjalanan_list(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Mengambil daftar rencana perjalanan"""
    # Hanya mengambil rencana milik user yang sedang login
    statement = select(RencanaPerjalanan).where(
        RencanaPerjalanan.user_id == UUID(current_user.id)
    )
    results = session.exec(statement).all()
    return results

@router.get("/{rencana_id}", response_model=RencanaPerjalanan)
def read_rencana_perjalanan_detail(
    rencana_id: UUID, 
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Mengambil detail rencana perjalanan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user) # Hanya pemilik yang boleh mengakses
    return rencana

@router.put("/{rencana_id}/anggaran", response_model=RencanaPerjalanan)
def update_rencana_anggaran(
    rencana_id: UUID, 
    data: AnggaranUpdate, 
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Memperbarui anggaran rencana perjalanan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user) # Hanya pemilik yang boleh mengakses
    
    try:
        rencana.ubahAnggaran(data.total_anggaran)
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        return rencana
    except AnggaranTerlampauiException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{rencana_id}/durasi", response_model=RencanaPerjalanan)
def update_rencana_durasi(
    rencana_id: UUID, 
    data: DurasiUpdate, 
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Memperbarui durasi rencana perjalanan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user) # Hanya pemilik yang boleh mengakses
    
    try:
        rencana.ubahDurasi(data.tanggal_mulai, data.tanggal_selesai)
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        return rencana
    except (TanggalDiLuarDurasiException, AnggaranTerlampauiException) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{rencana_id}/hari", status_code=201, response_model=RencanaPerjalanan)
def add_hari_perjalanan(
    rencana_id: UUID, 
    data: HariPerjalananCreate, 
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Menambahkan hari perjalanan ke rencana"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user) # Hanya pemilik yang boleh mengakses

    try:
        rencana.tambahHariPerjalanan(tanggal=data.tanggal, catatan=data.catatan)
        
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        return rencana
    except TanggalDiLuarDurasiException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{rencana_id}/hari/{tanggal}/aktivitas", status_code=201, response_model=RencanaPerjalanan)
def add_aktivitas(
    rencana_id: UUID, 
    tanggal: date, 
    data: AktivitasCreate, 
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Menambahkan aktivitas ke hari perjalanan tertentu dalam rencana"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user) # Hanya pemilik yang boleh mengakses

    try:
        # Cari hari perjalanan yang sesuai
        hari_target = next((h for h in rencana.list_hari_perjalanan if h.tanggal == tanggal), None)
        if not hari_target:
            raise HTTPException(status_code=404, detail=f"Hari perjalanan tanggal {tanggal} tidak ditemukan")

        rencana.tambahAktivitas(
            hari_perjalanan=hari_target,
            nama=data.nama,
            waktu_mulai=data.waktu_mulai,
            waktu_selesai=data.waktu_selesai,
            lokasi=data.lokasi,
            deskripsi=data.deskripsi
        )
        
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        return rencana
    except (AktivitasKonflikException, AnggaranTerlampauiException) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{rencana_id}/pengeluaran", status_code=201, response_model=RencanaPerjalanan)
def add_pengeluaran(
    rencana_id: UUID, 
    data: PengeluaranCreate, 
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Menambahkan pengeluaran ke rencana perjalanan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user) # Hanya pemilik yang boleh mengakses

    try:
        rencana.tambahPengeluaran(
            deskripsi=data.deskripsi,
            jumlah=data.jumlah,
            kategori=data.kategori
        )
        
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        return rencana
    except AnggaranTerlampauiException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{rencana_id}/hari/{tanggal}", response_model=RencanaPerjalanan)
def delete_hari_perjalanan(
    rencana_id: UUID, 
    tanggal: date, 
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Menghapus hari perjalanan dari rencana perjalanan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user) # Hanya pemilik yang boleh mengakses
    
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

@router.delete("/{rencana_id}/pengeluaran/{id_pengeluaran}", response_model=RencanaPerjalanan)
def delete_pengeluaran(
    rencana_id: UUID, 
    id_pengeluaran: UUID, 
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Menghapus pengeluaran dari rencana perjalanan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user) # Hanya pemilik yang boleh mengakses
    
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