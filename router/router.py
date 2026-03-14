# skrip berisikan Endpoint API untuk manajemen rencana perjalanan

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from sqlalchemy import update as sql_update
from uuid import UUID
from typing import List, Optional
from datetime import date, datetime, time, timedelta
from sqlmodel import select
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
    DurasiUpdate,
    TripUpdate,
    BulkTripCreate,
    SlotReservationRequest
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


def _recalculate_remaining_slots(rencana: RencanaPerjalanan, new_capacity: int) -> int:
    booked = max((rencana.slot or 0) - (rencana.slot_tersedia or 0), 0)
    return max(new_capacity - booked, 0)


def _compute_available(slot_tersedia: Optional[int], slot: Optional[int]) -> bool:
    # Availability is derived from remaining slots in rencanaperjalanan.
    total_slot = int(slot or 0)
    remaining_slot = int(slot_tersedia or 0)
    if total_slot <= 0:
        return False
    return remaining_slot > 0

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
        slot_tersedia=max(rencana_data.slot, 0),
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

@router.post("/bulk-create", status_code=201)
def bulk_create_trip(
    trip_data: BulkTripCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Membuat rencana perjalanan lengkap dengan gambar, poin penjemputan, dan item include dalam satu transaksi."""
    try:
        # 1. Validasi input dasar
        if not trip_data.nama or trip_data.nama.strip() == "":
            raise HTTPException(status_code=400, detail="Nama trip harus diisi")
        
        if trip_data.durasi_selesai < trip_data.durasi_mulai:
            raise HTTPException(status_code=400, detail="Tanggal selesai tidak boleh lebih kecil dari tanggal mulai")
        
        # 2. Buat entitas RencanaPerjalanan utama
        rencana = RencanaPerjalanan(
            id_user=UUID(current_user.id),
            nama=trip_data.nama.strip(),
            deskripsi=trip_data.deskripsi.strip() if trip_data.deskripsi else None,
            durasi_mulai=trip_data.durasi_mulai,
            durasi_selesai=trip_data.durasi_selesai,
            harga=trip_data.harga,
            slot=trip_data.slot,
            slot_tersedia=max(trip_data.slot, 0),
            provinsi=trip_data.provinsi.strip(),
            negara=trip_data.negara.strip(),
            destination_type=trip_data.destination_type.strip(),
            jumlah_hari=trip_data.jumlah_hari,
            jumlah_malam=trip_data.jumlah_malam,
            createdAt=datetime.now().date(),
            id_lokasi=trip_data.id_lokasi
        )
        
        session.add(rencana)
        session.flush()  # Flush untuk generate ID tanpa commit
        
        # 3. Tambahkan gambar-gambar
        if trip_data.images and len(trip_data.images) > 0:
            for image_url in trip_data.images:
                if image_url and image_url.strip():
                    trip_image = TripImage(
                        image_url=image_url.strip(),
                        plan_id=rencana.id_rencana
                    )
                    session.add(trip_image)
        
        # 4. Tambahkan poin penjemputan
        if trip_data.pickup_points and len(trip_data.pickup_points) > 0:
            for location in trip_data.pickup_points:
                if location and location.strip():
                    pickup_point = TripPickupPoint(
                        lokasi_jemput=location.strip(),
                        plan_id=rencana.id_rencana
                    )
                    session.add(pickup_point)
        
        # 5. Tambahkan item include
        if trip_data.includes and len(trip_data.includes) > 0:
            for item_name in trip_data.includes:
                if item_name and item_name.strip():
                    trip_include = TripInclude(
                        item_include=item_name.strip(),
                        plan_id=rencana.id_rencana
                    )
                    session.add(trip_include)
        
        # 6. Tambahkan data trip planner (hari_perjalanan, aktivitas, lokasi)
        if trip_data.trip_planner:
            location_cache = {}

            def _parse_start_time(raw_text: Optional[str]) -> time:
                """Terima 1 input waktu; jika user kirim range, ambil bagian awal saja."""
                if not raw_text:
                    return time(hour=8, minute=0)

                text = str(raw_text).strip()
                # dukung input lama: "06.00-07.00" / "06:00-07:00"
                start_part = text.split('-')[0].strip()
                normalized = start_part.replace('.', ':')
                try:
                    return datetime.strptime(normalized, "%H:%M").time()
                except Exception:
                    return time(hour=8, minute=0)

            def _parse_duration(raw_val: Optional[str]) -> int:
                if raw_val is None:
                    return 0
                try:
                    return max(0, int(float(str(raw_val).strip())))
                except Exception:
                    return 0

            for day_key, activities in trip_data.trip_planner.items():
                try:
                    day_num = int(day_key)
                except Exception:
                    continue

                if day_num < 1:
                    continue

                tanggal_hari = trip_data.durasi_mulai + timedelta(days=day_num - 1)

                # Susun notes dari aktivitas pertama pada hari tsb jika ada
                notes = None
                if activities and len(activities) > 0:
                    first_desc = (activities[0].activity or '').strip()
                    notes = first_desc if first_desc else f"Hari ke-{day_num}"

                hari = HariPerjalanan(
                    tanggal=tanggal_hari,
                    notes=notes,
                    rencana_id=rencana.id_rencana
                )
                session.add(hari)
                session.flush()

                for act in activities or []:
                    deskripsi = (act.activity or '').strip()
                    lokasi_nama = (act.location or '').strip()

                    # skip row kosong
                    if not deskripsi and not lokasi_nama and not (act.time or '').strip():
                        continue

                    if not deskripsi:
                        deskripsi = "Aktivitas"
                    if not lokasi_nama:
                        lokasi_nama = "Lokasi"

                    cache_key = lokasi_nama.lower()
                    lokasi_id = location_cache.get(cache_key)
                    if not lokasi_id:
                        lokasi = Lokasi(
                            namaLokasi=lokasi_nama,
                            alamat=lokasi_nama,
                            latitude=0.0,
                            longitude=0.0
                        )
                        session.add(lokasi)
                        session.flush()
                        lokasi_id = lokasi.id_lokasi
                        location_cache[cache_key] = lokasi_id

                    aktivitas = Aktivitas(
                        waktu_mulai=_parse_start_time(act.time),
                        duration=_parse_duration(act.duration),
                        deskripsi=deskripsi,
                        id_lokasi=lokasi_id,
                        hari_id=hari.id_hari
                    )
                    session.add(aktivitas)

        # 7. Commit semua perubahan (transaksi atomik)
        session.commit()
        session.refresh(rencana)
        
        # 8. Return response sukses
        return {
            "success": True,
            "trip_id": str(rencana.id_rencana),
            "trip_name": rencana.nama,
            "message": "Trip berhasil dibuat dengan foto, poin penjemputan, dan item include"
        }
        
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error creating trip: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Gagal membuat trip: {str(e)}"
        )

@router.get("/", response_model=List[RencanaPerjalanan])
def read_rencana_perjalanan_list(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Mengambil daftar rencana perjalanan milik user"""
    statement = select(RencanaPerjalanan).where(
        RencanaPerjalanan.id_user == UUID(current_user.id)
    ).options(
        selectinload(RencanaPerjalanan.trip_images)
    )
    results = session.exec(statement).all()
    return results


@router.get("/all", response_model=List[RencanaPerjalanan])
def read_all_rencana_perjalanan(
    session: Session = Depends(get_session)
):
    """Mengambil daftar semua rencana perjalanan (tanpa filter user)."""
    statement = select(RencanaPerjalanan).options(
        selectinload(RencanaPerjalanan.trip_images)
    )
    results = session.exec(statement).all()
    return results

@router.get("/trips/latest")
def get_latest_trip(
    email: Optional[str] = Query(None, description="User email to filter trips"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Query latest trip for the current user
    statement = select(RencanaPerjalanan).where(
        RencanaPerjalanan.id_user == UUID(current_user.id)
    ).options(
        selectinload(RencanaPerjalanan.trip_images)
    ).order_by(RencanaPerjalanan.createdAt.desc())
    
    results = session.exec(statement).all()
    
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No trips found for this user"
        )
    
    latest = results[0]
    is_available = _compute_available(latest.slot_tersedia, latest.slot)
    
    # Get first image URL if available
    image_url = latest.trip_images[0].image_url if latest.trip_images else None
    
    # Return in format expected by frontend
    return {
        "trip_id": str(latest.id_rencana),
        "trip_name": latest.nama,
        "start_date": str(latest.durasi_mulai) if latest.durasi_mulai else None,
        "startDate": str(latest.durasi_mulai) if latest.durasi_mulai else None,
        "endDate": str(latest.durasi_selesai) if latest.durasi_selesai else None,
        "price": float(latest.harga) if latest.harga else 0.0,
        "location": latest.provinsi or "",
        "destination_type": latest.destination_type or "",
        "status": "Upcoming",  # Default status
        "created_at": str(latest.createdAt) if latest.createdAt else None,
        "id_rencana": str(latest.id_rencana),
        "nama": latest.nama,
        "deskripsi": latest.deskripsi,
        "harga": float(latest.harga) if latest.harga else 0.0,
        "provinsi": latest.provinsi,
        "negara": latest.negara,
        "jumlah_hari": latest.jumlah_hari,
        "jumlah_malam": latest.jumlah_malam,
        "slot": latest.slot,
        "slot_tersedia": latest.slot_tersedia,
        "slot_available": latest.slot_tersedia,
        "available": is_available,
        "is_available": is_available,
        "image_url": image_url,
    }


@router.get("/trips/all")
def get_all_trips(
    session: Session = Depends(get_session)
):
    statement = select(RencanaPerjalanan).options(
        selectinload(RencanaPerjalanan.trip_images)
    )
    results = session.exec(statement).all()

    mapped = []
    for r in results:
        # Get first image URL if available
        image_url = r.trip_images[0].image_url if r.trip_images else None
        is_available = _compute_available(r.slot_tersedia, r.slot)
        
        mapped.append({
            "trip_id": str(r.id_rencana),
            "trip_name": r.nama,
            "start_date": str(r.durasi_mulai) if r.durasi_mulai else None,
            "startDate": str(r.durasi_mulai) if r.durasi_mulai else None,
            "endDate": str(r.durasi_selesai) if r.durasi_selesai else None,
            "price": float(r.harga) if r.harga else 0.0,
            "location": r.provinsi or "",
            "destination_type": r.destination_type or "",
            "status": "Upcoming",
            "created_at": str(r.createdAt) if r.createdAt else None,
            "id_rencana": str(r.id_rencana),
            "nama": r.nama,
            "deskripsi": r.deskripsi,
            "harga": float(r.harga) if r.harga else 0.0,
            "provinsi": r.provinsi,
            "negara": r.negara,
            "jumlah_hari": r.jumlah_hari,
            "jumlah_malam": r.jumlah_malam,
            "slot": r.slot,
            "slot_tersedia": r.slot_tersedia,
            "slot_available": r.slot_tersedia,
            "available": is_available,
            "is_available": is_available,
            "image_url": image_url,
        })

    return mapped


@router.get("/trips/{trip_id}")
def get_trip_detail(
    trip_id: UUID,
    session: Session = Depends(get_session)
):
    try:
        # Use select with eager loading to get all relationships
        stmt = (
            select(RencanaPerjalanan)
            .where(RencanaPerjalanan.id_rencana == trip_id)
            .options(
                selectinload(RencanaPerjalanan.trip_images),
                selectinload(RencanaPerjalanan.trip_pickup_points),
                selectinload(RencanaPerjalanan.trip_includes),
                selectinload(RencanaPerjalanan.hariPerjalananList).selectinload(HariPerjalanan.aktivitasList).selectinload(Aktivitas.lokasi)
            )
        )
        result = session.exec(stmt).first()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip dengan ID {trip_id} tidak ditemukan"
            )
        
        rencana = result
        is_available = _compute_available(rencana.slot_tersedia, rencana.slot)
        
        # Map images from trip_images relationship
        images = [img.image_url for img in rencana.trip_images] if rencana.trip_images else []
        
        # Map pickup points from trip_pickup_points relationship
        pickup_points = []
        for point in rencana.trip_pickup_points or []:
            pickup_points.append({
                "id": str(point.trip_pickup_id),
                "location": point.lokasi_jemput,
                "price": ""  # Price is not stored in the model currently
            })
        
        # Map includes from trip_includes relationship
        includes = [inc.item_include for inc in rencana.trip_includes] if rencana.trip_includes else []
        
        # Map rundowns from hariPerjalananList with activities
        rundowns = {}
        for hari in rencana.hariPerjalananList or []:
            day_number = (hari.tanggal - rencana.durasi_mulai).days + 1
            activities = []
            for act in hari.aktivitasList or []:
                activities.append({
                    "time": str(act.waktu_mulai) if act.waktu_mulai else "",
                    "duration": act.duration if act.duration is not None else 0,
                    "activity": act.deskripsi or "",
                    "location": act.lokasi.namaLokasi if act.lokasi else ""
                })
            if activities:
                rundowns[str(day_number)] = activities
        
        # Return complete trip data with relationships
        return {
            "trip_id": str(rencana.id_rencana),
            "tripId": str(rencana.id_rencana),
            "trip_name": rencana.nama,
            "name": rencana.nama,
            "deskripsi": rencana.deskripsi or "",
            "description": rencana.deskripsi or "",
            "harga": float(rencana.harga) if rencana.harga else 0.0,
            "price": float(rencana.harga) if rencana.harga else 0.0,
            "provinsi": rencana.provinsi or "",
            "negara": rencana.negara or "",
            "location": {
                "state": rencana.provinsi or "",
                "country": rencana.negara or ""
            },
            "startDate": str(rencana.durasi_mulai) if rencana.durasi_mulai else None,
            "endDate": str(rencana.durasi_selesai) if rencana.durasi_selesai else None,
            "jumlah_hari": rencana.jumlah_hari or 0,
            "jumlah_malam": rencana.jumlah_malam or 0,
            "duration": {
                "days": rencana.jumlah_hari or 0,
                "nights": rencana.jumlah_malam or 0
            },
            "slot": rencana.slot or 0,
            "slot_tersedia": rencana.slot_tersedia,
            "slot_available": rencana.slot_tersedia,
            "available": is_available,
            "is_available": is_available,
            "destination_type": rencana.destination_type or "",
            "destinationType": rencana.destination_type or "",
            "created_at": str(rencana.createdAt) if rencana.createdAt else None,
            "images": images,
            "pickup_points": pickup_points,
            "includes": includes,
            "rundowns": rundowns
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_trip_detail: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading trip: {str(e)}"
        )


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

@router.put("/trips/{trip_id}")
def update_trip(
    trip_id: UUID,
    data: TripUpdate,
    session: Session = Depends(get_session)
):
    try:
        # Get the trip
        rencana = session.get(RencanaPerjalanan, trip_id)
        if not rencana:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip dengan ID {trip_id} tidak ditemukan"
            )
        
        # Update only provided fields
        if data.name is not None:
            rencana.nama = data.name
        if data.description is not None:
            rencana.deskripsi = data.description
        if data.price is not None:
            rencana.harga = data.price
        if data.provinsi is not None:
            rencana.provinsi = data.provinsi
        if data.country is not None:
            rencana.negara = data.country
        if data.slot is not None:
            if data.slot < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="slot tidak boleh negatif"
                )
            rencana.slot_tersedia = _recalculate_remaining_slots(rencana, data.slot)
            rencana.slot = data.slot
        if data.days is not None:
            rencana.jumlah_hari = data.days
        if data.nights is not None:
            rencana.jumlah_malam = data.nights
        if data.destinationType is not None:
            rencana.destination_type = data.destinationType
        if data.durasi_mulai is not None:
            rencana.durasi_mulai = data.durasi_mulai
        if data.durasi_selesai is not None:
            rencana.durasi_selesai = data.durasi_selesai

        if rencana.durasi_selesai < rencana.durasi_mulai:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tanggal selesai tidak boleh lebih kecil dari tanggal mulai"
            )

        # Add-only image update when payload is provided.
        # Existing images are preserved; use dedicated DELETE endpoint to remove.
        if data.images is not None:
            existing_images = session.exec(
                select(TripImage).where(TripImage.plan_id == trip_id)
            ).all()
            existing_urls = {
                (img.image_url or "").strip()
                for img in existing_images
                if img.image_url
            }

            for image_url in data.images:
                normalized_url = str(image_url).strip() if image_url is not None else ""
                if normalized_url and normalized_url not in existing_urls:
                    session.add(
                        TripImage(
                            image_url=normalized_url,
                            plan_id=rencana.id_rencana
                        )
                    )
                    existing_urls.add(normalized_url)

        # Replace pickup points when payload is provided
        if data.pickup_points is not None:
            existing_pickups = session.exec(
                select(TripPickupPoint).where(TripPickupPoint.plan_id == trip_id)
            ).all()
            for pickup in existing_pickups:
                session.delete(pickup)

            for location in data.pickup_points:
                if location and str(location).strip():
                    session.add(
                        TripPickupPoint(
                            lokasi_jemput=str(location).strip(),
                            plan_id=rencana.id_rencana
                        )
                    )

        # Replace includes when payload is provided
        if data.includes is not None:
            existing_includes = session.exec(
                select(TripInclude).where(TripInclude.plan_id == trip_id)
            ).all()
            for include in existing_includes:
                session.delete(include)

            for item_name in data.includes:
                if item_name and str(item_name).strip():
                    session.add(
                        TripInclude(
                            item_include=str(item_name).strip(),
                            plan_id=rencana.id_rencana
                        )
                    )

        # Replace trip planner data when payload is provided
        if data.trip_planner is not None:
            existing_days = session.exec(
                select(HariPerjalanan).where(HariPerjalanan.rencana_id == trip_id)
            ).all()
            for day in existing_days:
                session.delete(day)
            session.flush()

            location_cache = {}

            def _parse_start_time(raw_text: Optional[str]) -> time:
                if not raw_text:
                    return time(hour=8, minute=0)

                text = str(raw_text).strip()
                start_part = text.split('-')[0].strip()
                normalized = start_part.replace('.', ':')
                try:
                    return datetime.strptime(normalized, "%H:%M").time()
                except Exception:
                    return time(hour=8, minute=0)

            def _parse_duration(raw_val: Optional[str]) -> int:
                if raw_val is None:
                    return 0
                try:
                    return max(0, int(float(str(raw_val).strip())))
                except Exception:
                    return 0

            for day_key, activities in data.trip_planner.items():
                try:
                    day_num = int(day_key)
                except Exception:
                    continue

                if day_num < 1:
                    continue

                tanggal_hari = rencana.durasi_mulai + timedelta(days=day_num - 1)

                notes = None
                if activities and len(activities) > 0:
                    first_desc = (activities[0].get("activity") or "").strip()
                    notes = first_desc if first_desc else f"Hari ke-{day_num}"

                hari = HariPerjalanan(
                    tanggal=tanggal_hari,
                    notes=notes,
                    rencana_id=rencana.id_rencana
                )
                session.add(hari)
                session.flush()

                for act in activities or []:
                    if not isinstance(act, dict):
                        continue

                    deskripsi = (act.get("activity") or "").strip()
                    lokasi_nama = (act.get("location") or "").strip()
                    raw_time = (act.get("time") or "").strip()

                    if not deskripsi and not lokasi_nama and not raw_time:
                        continue

                    if not deskripsi:
                        deskripsi = "Aktivitas"
                    if not lokasi_nama:
                        lokasi_nama = "Lokasi"

                    cache_key = lokasi_nama.lower()
                    lokasi_id = location_cache.get(cache_key)
                    if not lokasi_id:
                        lokasi = Lokasi(
                            namaLokasi=lokasi_nama,
                            alamat=lokasi_nama,
                            latitude=0.0,
                            longitude=0.0
                        )
                        session.add(lokasi)
                        session.flush()
                        lokasi_id = lokasi.id_lokasi
                        location_cache[cache_key] = lokasi_id

                    session.add(
                        Aktivitas(
                            waktu_mulai=_parse_start_time(raw_time),
                            duration=_parse_duration(act.get("duration")),
                            deskripsi=deskripsi,
                            id_lokasi=lokasi_id,
                            hari_id=hari.id_hari
                        )
                    )
        
        # Commit changes
        session.add(rencana)
        session.commit()
        session.refresh(rencana)
        
        # Return updated trip in frontend format
        return {
            "trip_id": str(rencana.id_rencana),
            "tripId": str(rencana.id_rencana),
            "name": rencana.nama,
            "description": rencana.deskripsi or "",
            "price": float(rencana.harga) if rencana.harga else 0.0,
            "provinsi": rencana.provinsi or "",
            "country": rencana.negara or "",
            "location": {
                "state": rencana.provinsi or "",
                "country": rencana.negara or ""
            },
            "slot": rencana.slot or 0,
            "duration": {
                "days": rencana.jumlah_hari or 0,
                "nights": rencana.jumlah_malam or 0
            },
            "destinationType": rencana.destination_type or "",
            "startDate": str(rencana.durasi_mulai) if rencana.durasi_mulai else None,
            "endDate": str(rencana.durasi_selesai) if rencana.durasi_selesai else None,
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in update_trip: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating trip: {str(e)}"
        )


@router.post("/trips/{trip_id}/reserve-slots")
def reserve_trip_slots(
    trip_id: UUID,
    payload: SlotReservationRequest,
    session: Session = Depends(get_session)
):
    requested = payload.participant_count if payload and payload.participant_count else 1
    if requested <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="participant_count harus lebih dari 0"
        )

    stmt = (
        sql_update(RencanaPerjalanan)
        .where(
            RencanaPerjalanan.id_rencana == trip_id,
            RencanaPerjalanan.slot_tersedia >= requested
        )
        .values(slot_tersedia=RencanaPerjalanan.slot_tersedia - requested)
    )
    result = session.exec(stmt)
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot tidak tersedia untuk jumlah peserta yang diminta"
        )

    session.commit()
    refreshed = session.get(RencanaPerjalanan, trip_id)
    slot = int(refreshed.slot if refreshed and refreshed.slot is not None else 0)
    slot_tersedia = int(refreshed.slot_tersedia if refreshed and refreshed.slot_tersedia is not None else 0)
    is_available = _compute_available(slot_tersedia, slot)
    return {
        "success": True,
        "trip_id": str(trip_id),
        "slot": slot,
        "slot_tersedia": slot_tersedia,
        "slot_available": slot_tersedia,
        "available": is_available,
        "is_available": is_available
    }


@router.post("/trips/{trip_id}/release-slots")
def release_trip_slots(
    trip_id: UUID,
    payload: SlotReservationRequest,
    session: Session = Depends(get_session)
):
    released = payload.participant_count if payload and payload.participant_count else 1
    if released <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="participant_count harus lebih dari 0"
        )

    rencana = session.get(RencanaPerjalanan, trip_id)
    if not rencana:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip dengan ID {trip_id} tidak ditemukan"
        )

    rencana.slot_tersedia = min((rencana.slot_tersedia or 0) + released, rencana.slot or 0)
    session.add(rencana)
    session.commit()
    session.refresh(rencana)
    is_available = _compute_available(rencana.slot_tersedia, rencana.slot)

    return {
        "success": True,
        "trip_id": str(trip_id),
        "slot": int(rencana.slot or 0),
        "slot_tersedia": int(rencana.slot_tersedia or 0),
        "slot_available": int(rencana.slot_tersedia or 0),
        "available": is_available,
        "is_available": is_available
    }


@router.post("/trips/{trip_id}/sync-slots")
def sync_trip_slots(
    trip_id: UUID,
    payload: SlotReservationRequest,
    session: Session = Depends(get_session)
):
    participant_count = payload.participant_count if payload and payload.participant_count is not None else 0
    if participant_count < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="participant_count tidak boleh negatif"
        )

    rencana = session.get(RencanaPerjalanan, trip_id)
    if not rencana:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip dengan ID {trip_id} tidak ditemukan"
        )

    rencana.slot_tersedia = max((rencana.slot or 0) - participant_count, 0)
    session.add(rencana)
    session.commit()
    session.refresh(rencana)
    is_available = _compute_available(rencana.slot_tersedia, rencana.slot)

    return {
        "success": True,
        "trip_id": str(trip_id),
        "slot": int(rencana.slot or 0),
        "participant_count": int(participant_count),
        "slot_tersedia": int(rencana.slot_tersedia or 0),
        "slot_available": int(rencana.slot_tersedia or 0),
        "available": is_available,
        "is_available": is_available
    }

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

@router.get("/trip-pickup-points", response_model=List[TripPickupPoint])
def get_pickup_points_by_plan_id(plan_id: UUID = Query(...), session: Session = Depends(get_session)):
    stmt = select(TripPickupPoint).where(TripPickupPoint.plan_id == plan_id)
    return session.exec(stmt).all()


@router.get("/pickup_points", response_model=List[TripPickupPoint])
def get_pickup_points_by_trip_id(trip_id: Optional[UUID] = Query(None), session: Session = Depends(get_session)):
    if not trip_id:
        return []
    stmt = select(TripPickupPoint).where(TripPickupPoint.plan_id == trip_id)
    return session.exec(stmt).all()

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
            duration=data.duration,
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
