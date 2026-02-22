# skrip berisikan Endpoint API untuk manajemen rencana perjalanan

from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from uuid import UUID
from typing import List
from datetime import date, datetime

# Model Domain
from models.aggregate_root import RencanaPerjalanan
from models.entity import Aktivitas, Pengeluaran, HariPerjalanan, Lokasi, TripImage, TripPickupPoint, TripInclude
from models.exception import AnggaranTerlampauiException, AktivitasKonflikException, TanggalDiLuarDurasiException

# API Schema
from schema import (
    RencanaPerjalananCreate, 
    HariPerjalananCreate, 
    PengeluaranCreate, 
    AktivitasCreate, 
    LokasiCreate,
    TripImageCreate,
    TripPickupPointCreate,
    TripIncludeCreate,
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
    if str(rencana.id_user) != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki izin untuk mengakses rencana ini"
        )

# ==========================================
# LOKASI ENDPOINTS
# ==========================================

@router.post("/lokasi/", status_code=201, response_model=Lokasi)
def create_lokasi(
    lokasi_data: LokasiCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Membuat lokasi baru"""
    lokasi = Lokasi(
        namaLokasi=lokasi_data.namaLokasi,
        alamat=lokasi_data.alamat,
        latitude=lokasi_data.latitude,
        longitude=lokasi_data.longitude
    )
    
    session.add(lokasi)
    session.commit()
    session.refresh(lokasi)
    return lokasi

@router.get("/lokasi/", response_model=List[Lokasi])
def list_lokasi(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Mengambil daftar semua lokasi"""
    statement = select(Lokasi)
    results = session.exec(statement).all()
    return results

@router.get("/lokasi/{lokasi_id}", response_model=Lokasi)
def get_lokasi(
    lokasi_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Mengambil detail lokasi"""
    lokasi = session.get(Lokasi, lokasi_id)
    if not lokasi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lokasi dengan ID {lokasi_id} tidak ditemukan"
        )
    return lokasi

# ==========================================
# RENCANA PERJALANAN ENDPOINTS
# ==========================================

@router.post("/", status_code=201, response_model=RencanaPerjalanan)
def create_rencana_perjalanan(
    rencana_data: RencanaPerjalananCreate, 
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Membuat rencana perjalanan baru"""
    baru = RencanaPerjalanan(
        id_user=UUID(current_user.id),
        nama=rencana_data.nama,
        deskripsi=rencana_data.deskripsi,
        durasi_mulai=rencana_data.durasi.tanggalMulai,
        durasi_selesai=rencana_data.durasi.tanggalSelesai,
        harga=rencana_data.anggaran.jumlah,
        slot=rencana_data.slot,
        slot_tersedia=True,
        provinsi=rencana_data.provinsi,
        negara=rencana_data.negara,
        destination_type=rencana_data.destination_type,
        jumlah_hari=rencana_data.jumlah_hari,
        jumlah_malam=rencana_data.jumlah_malam,
        createdAt=datetime.now().date()
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
    """Mengambil daftar rencana perjalanan milik user"""
    statement = select(RencanaPerjalanan).where(
        RencanaPerjalanan.id_user == UUID(current_user.id)
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
    _ensure_ownership(rencana, current_user)
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
    _ensure_ownership(rencana, current_user)
    
    try:
        rencana.setAnggaran(data.anggaranBaru.jumlah, data.anggaranBaru.mata_uang)
        
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        return rencana
    except (ValueError, AnggaranTerlampauiException) as e:
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
    _ensure_ownership(rencana, current_user)
    
    try:
        rencana.setDurasi(data.durasiBaru.tanggalMulai, data.durasiBaru.tanggalSelesai)
        
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        return rencana
    except TanggalDiLuarDurasiException as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
# TRIP IMAGE ENDPOINTS
# ==========================================

@router.post("/{rencana_id}/images", status_code=201, response_model=RencanaPerjalanan)
def add_trip_image(
    rencana_id: UUID,
    data: TripImageCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Menambahkan gambar ke rencana perjalanan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user)
    
    rencana.tambahTripImage(data.image_url)
    
    session.add(rencana)
    session.commit()
    session.refresh(rencana)
    return rencana

@router.get("/{rencana_id}/images", response_model=List[TripImage])
def list_trip_images(
    rencana_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Mengambil daftar gambar rencana perjalanan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user)
    return rencana.trip_images

@router.delete("/{rencana_id}/images/{image_id}", response_model=RencanaPerjalanan)
def delete_trip_image(
    rencana_id: UUID,
    image_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Menghapus gambar dari rencana perjalanan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user)
    
    berhasil = rencana.hapusTripImage(image_id)
    
    if not berhasil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gambar dengan ID {image_id} tidak ditemukan"
        )
    
    session.add(rencana)
    session.commit()
    session.refresh(rencana)
    return rencana

# ==========================================
# TRIP PICKUP POINT ENDPOINTS
# ==========================================

@router.post("/{rencana_id}/pickup-points", status_code=201, response_model=RencanaPerjalanan)
def add_trip_pickup_point(
    rencana_id: UUID,
    data: TripPickupPointCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Menambahkan titik penjemputan ke rencana perjalanan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user)
    
    rencana.tambahTripPickupPoint(data.lokasi_jemput)
    
    session.add(rencana)
    session.commit()
    session.refresh(rencana)
    return rencana

@router.get("/{rencana_id}/pickup-points", response_model=List[TripPickupPoint])
def list_trip_pickup_points(
    rencana_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Mengambil daftar titik penjemputan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user)
    return rencana.trip_pickup_points

@router.delete("/{rencana_id}/pickup-points/{pickup_id}", response_model=RencanaPerjalanan)
def delete_trip_pickup_point(
    rencana_id: UUID,
    pickup_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Menghapus titik penjemputan dari rencana perjalanan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user)
    
    berhasil = rencana.hapusTripPickupPoint(pickup_id)
    
    if not berhasil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Titik penjemputan dengan ID {pickup_id} tidak ditemukan"
        )
    
    session.add(rencana)
    session.commit()
    session.refresh(rencana)
    return rencana

# ==========================================
# TRIP INCLUDE ENDPOINTS
# ==========================================

@router.post("/{rencana_id}/includes", status_code=201, response_model=RencanaPerjalanan)
def add_trip_include(
    rencana_id: UUID,
    data: TripIncludeCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Menambahkan item yang termasuk dalam paket"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user)
    
    rencana.tambahTripInclude(data.item_include)
    
    session.add(rencana)
    session.commit()
    session.refresh(rencana)
    return rencana

@router.get("/{rencana_id}/includes", response_model=List[TripInclude])
def list_trip_includes(
    rencana_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Mengambil daftar item yang termasuk dalam paket"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user)
    return rencana.trip_includes

@router.delete("/{rencana_id}/includes/{include_id}", response_model=RencanaPerjalanan)
def delete_trip_include(
    rencana_id: UUID,
    include_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Menghapus item yang termasuk dalam paket"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user)
    
    berhasil = rencana.hapusTripInclude(include_id)
    
    if not berhasil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item include dengan ID {include_id} tidak ditemukan"
        )
    
    session.add(rencana)
    session.commit()
    session.refresh(rencana)
    return rencana

# ==========================================
# HARI PERJALANAN ENDPOINTS
# ==========================================

@router.post("/{rencana_id}/hari", status_code=201, response_model=RencanaPerjalanan)
def add_hari_perjalanan(
    rencana_id: UUID, 
    data: HariPerjalananCreate, 
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Menambahkan hari perjalanan ke rencana"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user)

    try:
        hari_baru = rencana.tambahHariPerjalanan(tanggal=data.tanggal)
        if data.notes:
            hari_baru.notes = data.notes
        
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        return rencana
    except (TanggalDiLuarDurasiException, ValueError) as e:
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
    _ensure_ownership(rencana, current_user)
    
    berhasil = rencana.hapusHariPerjalanan(tanggal)
    
    if not berhasil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hari perjalanan dengan tanggal {tanggal} tidak ditemukan"
        )
    
    session.add(rencana)
    session.commit()
    session.refresh(rencana)
    return rencana

# ==========================================
# AKTIVITAS ENDPOINTS
# ==========================================

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
    _ensure_ownership(rencana, current_user)

    try:
        # Cari hari perjalanan yang sesuai
        hari_target = rencana.getHariPerjalanan(tanggal)
        if not hari_target:
            raise HTTPException(
                status_code=404, 
                detail=f"Hari perjalanan tanggal {tanggal} tidak ditemukan"
            )
        
        # Validasi lokasi exists
        lokasi = session.get(Lokasi, data.id_lokasi)
        if not lokasi:
            raise HTTPException(
                status_code=404,
                detail=f"Lokasi dengan ID {data.id_lokasi} tidak ditemukan"
            )
        
        # Buat aktivitas baru
        aktivitas_baru = Aktivitas(
            waktu_mulai=data.waktu_mulai,
            waktu_selesai=data.waktu_selesai,
            deskripsi=data.deskripsi,
            id_lokasi=data.id_lokasi
        )
        
        # Tambahkan ke hari perjalanan
        hari_target.tambahAktivitas(aktivitas_baru)
        
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        return rencana
    except AktivitasKonflikException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{rencana_id}/hari/{tanggal}/aktivitas", response_model=List[Aktivitas])
def list_aktivitas(
    rencana_id: UUID,
    tanggal: date,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Mengambil daftar aktivitas untuk hari tertentu"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user)
    
    hari = rencana.getHariPerjalanan(tanggal)
    if not hari:
        raise HTTPException(
            status_code=404,
            detail=f"Hari perjalanan tanggal {tanggal} tidak ditemukan"
        )
    
    return hari.aktivitasList

# ==========================================
# PENGELUARAN ENDPOINTS
# ==========================================

@router.post("/{rencana_id}/pengeluaran", status_code=201, response_model=RencanaPerjalanan)
def add_pengeluaran(
    rencana_id: UUID, 
    data: PengeluaranCreate, 
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Menambahkan pengeluaran ke rencana perjalanan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user)

    try:
        # Buat Pengeluaran object dengan flattened Uang value object
        pengeluaran_baru = Pengeluaran(
            deskripsi=data.deskripsi,
            biaya_jumlah=data.biaya.jumlah,
            biaya_mata_uang=data.biaya.mata_uang,
            tanggalPengeluaran=data.tanggalPengeluaran
        )
        rencana.tambahPengeluaran(pengeluaran_baru)
        
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        return rencana
    except (AnggaranTerlampauiException, TanggalDiLuarDurasiException) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{rencana_id}/pengeluaran/{id_pengeluaran}", response_model=RencanaPerjalanan)
def delete_pengeluaran(
    rencana_id: UUID, 
    id_pengeluaran: UUID, 
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Menghapus pengeluaran dari rencana perjalanan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user)
    
    berhasil = rencana.hapusPengeluaran(id_pengeluaran)
    
    if not berhasil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pengeluaran dengan ID {id_pengeluaran} tidak ditemukan"
        )
    
    session.add(rencana)
    session.commit()
    session.refresh(rencana)
    return rencana

@router.get("/{rencana_id}/statistik")
def get_statistik_rencana(
    rencana_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Mengambil statistik rencana perjalanan"""
    rencana = _get_rencana(rencana_id, session)
    _ensure_ownership(rencana, current_user)
    
    return {
        "total_pengeluaran": rencana.getTotalPengeluaran(),
        "sisa_anggaran": rencana.getSisaAnggaran(),
        "jumlah_hari": rencana.getJumlahHariPerjalanan(),
        "jumlah_pengeluaran": rencana.getJumlahPengeluaran()
    }