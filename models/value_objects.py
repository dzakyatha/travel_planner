# skrip berisikan value objects

from pydantic import BaseModel, model_validator, field_validator
from datetime import date

# merepresentasikan nilai moneter
class Uang(BaseModel):
    jumlah: float
    mata_uang: str = "IDR" # mata uang default

    # validasi: jumlah uang tidak boleh negatif
    @field_validator('jumlah')
    @classmethod
    def validasi_uang(cls, v):
        if v < 0: raise ValueError("Jumlah uang tidak boleh negatif")
        return v

# merepresentasikan rentang waktu perjalanan
class Durasi(BaseModel):
    tanggalMulai: date
    tanggalSelesai: date

    # validasi: tanggal mulai tidak boleh melebihi tanggal selesai
    @model_validator(mode='after')
    def validasi_durasi(self):
        if self.tanggalMulai and self.tanggalSelesai and self.tanggalMulai > self.tanggalSelesai:
            raise ValueError("Tanggal mulai tidak boleh melebihi tanggal selesai")
        return self

# merepresentasikan lokasi perjalanan
class Lokasi(BaseModel):
    namaLokasi: str
    alamat: str
    latitude: float
    longitude: float

