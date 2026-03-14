# skrip berisikan skema Pydantic untuk Request/Response API

from pydantic import BaseModel
from datetime import date, time
from uuid import UUID
from typing import Optional, List, Dict

# === Skema untuk Value Objects ===

class Uang(BaseModel):
    jumlah: float
    mata_uang: str = "IDR"

class Durasi(BaseModel):
    tanggalMulai: date
    tanggalSelesai: date

class Lokasi(BaseModel):
    namaLokasi: str
    alamat: str
    latitude: float
    longitude: float

# === Skema untuk Model ===

# untuk membuat RencanaPerjalanan baru
class RencanaPerjalananCreate(BaseModel):
    nama: str
    deskripsi: Optional[str] = None
    durasi: Durasi
    anggaran: Uang
    slot: int
    provinsi: str
    negara: str
    destination_type: str
    jumlah_hari: int
    jumlah_malam: int

# untuk menambahkan HariPerjalanan ke RencanaPerjalanan
class HariPerjalananCreate(BaseModel):
    tanggal: date
    notes: Optional[str] = None

# untuk menambahkan Pengeluaran ke RencanaPerjalanan
class PengeluaranCreate(BaseModel):
    deskripsi: str
    biaya: Uang
    tanggalPengeluaran: date

# untuk menambahkan Aktivitas ke HariPerjalanan
class AktivitasCreate(BaseModel):
    waktu_mulai: time
    duration: int
    deskripsi: str
    id_lokasi: UUID

# untuk membuat Lokasi baru
class LokasiCreate(BaseModel):
    namaLokasi: str
    alamat: str
    latitude: float
    longitude: float

# untuk menambahkan gambar trip
class TripImageCreate(BaseModel):
    image_url: str

# untuk menambahkan titik penjemputan
class TripPickupPointCreate(BaseModel):
    lokasi_jemput: str

# untuk menambahkan item yang termasuk dalam paket
class TripIncludeCreate(BaseModel):
    item_include: str

# untuk memperbarui anggaran RencanaPerjalanan
class AnggaranUpdate(BaseModel):
    anggaranBaru: Uang

# untuk memperbarui durasi RencanaPerjalanan
class DurasiUpdate(BaseModel):
    durasiBaru: Durasi

# untuk memperbarui trip secara keseluruhan
class TripUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    provinsi: Optional[str] = None
    country: Optional[str] = None
    slot: Optional[int] = None
    days: Optional[int] = None
    nights: Optional[int] = None
    destinationType: Optional[str] = None
    durasi_mulai: Optional[date] = None
    durasi_selesai: Optional[date] = None
    images: Optional[List[str]] = None
    includes: Optional[List[str]] = None
    pickup_points: Optional[List[str]] = None
    trip_planner: Optional[Dict[str, List[dict]]] = None


class TripPlannerActivityCreate(BaseModel):
    time: Optional[str] = None
    duration: Optional[str] = None
    activity: Optional[str] = None
    location: Optional[str] = None


class SlotReservationRequest(BaseModel):
    participant_count: int = 1

# untuk bulk save trip dengan semua data terkait
class BulkTripCreate(BaseModel):
    """Schema untuk membuat trip lengkap dengan images, includes, dan pickup points dalam satu request"""
    # Main trip data
    nama: str
    deskripsi: Optional[str] = None
    harga: float
    slot: int
    provinsi: str
    negara: str
    destination_type: str
    jumlah_hari: int
    jumlah_malam: int
    durasi_mulai: date
    durasi_selesai: date
    id_lokasi: Optional[UUID] = None
    
    # Related data (arrays)
    images: List[str] = []  # list of image URLs
    includes: List[str] = []  # list of include item names
    pickup_points: List[str] = []  # list of pickup point locations
    trip_planner: Dict[str, List[TripPlannerActivityCreate]] = {}

# === Skema untuk Autentikasi ===

# untuk JWT
class Token(BaseModel):
    access_token: str
    token_type: str

# untuk data dari JWT
class TokenData(BaseModel):
    username: str | None = None

# untuk respon user
class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

# untuk hash password user di Database
class UserInDB(User):
    hashed_password: str