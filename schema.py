# skrip berisikan skema Pydantic untuk Request/Response API

from pydantic import BaseModel
from datetime import date, time
from models.value_objects import Uang, Durasi, Lokasi

# === Skema untuk Model ===

# untuk membuat RencanaPerjalanan baru
class RencanaPerjalananCreate(BaseModel):
    nama: str
    durasi: Durasi
    anggaran: Uang

# untuk menambahkan HariPerjalanan ke RencanaPerjalanan
class HariPerjalananCreate(BaseModel):
    tanggal: date

# untuk menambahkan Pengeluaran ke RencanaPerjalanan
class PengeluaranCreate(BaseModel):
    deskripsi: str
    biaya: Uang
    tanggalPengeluaran: date

# untuk menambahkan Aktivitas ke HariPerjalanan
class AktivitasCreate(BaseModel):
    waktuMulai: time
    waktuSelesai: time
    lokasi: Lokasi
    deskripsi: str

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