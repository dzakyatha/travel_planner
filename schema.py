# skrip berisikan skema Pydantic untuk Request/Response API

from pydantic import BaseModel
from datetime import date, time
from uuid import UUID
from typing import Optional

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
    waktu_selesai: time
    deskripsi: str
    id_lokasi: UUID

# untuk membuat Lokasi baru
class LokasiCreate(BaseModel):
    namaLokasi: str
    alamat: str
    latitude: float
    longitude: float

# untuk memperbarui anggaran RencanaPerjalanan
class AnggaranUpdate(BaseModel):
    anggaranBaru: Uang

# untuk memperbarui durasi RencanaPerjalanan
class DurasiUpdate(BaseModel):
    durasiBaru: Durasi

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