# skrip berisikan entity

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import time, date
from models.exception import AktivitasKonflikException
import os

if TYPE_CHECKING:
    from models.aggregate_root import RencanaPerjalanan

# fungsi untuk menentukan tipe kolom JSON berdasarkan database yang digunakan
def get_json_column():
    db_url = os.getenv("DATABASE_URL", "sqlite:///./local_travel.db")
    if db_url.startswith("postgresql"):
        return Column(JSONB)
    else:
        return Column(JSON)

# merepresentasikan lokasi perjalanan (ENTITY)
class Lokasi(SQLModel, table=True):
    __tablename__ = "lokasi"

    id_lokasi: UUID = Field(default_factory=uuid4, primary_key=True)
    namaLokasi: str
    alamat: str
    latitude: float
    longitude: float

    # Relasi
    aktivitasList: List['Aktivitas'] = Relationship(back_populates="lokasi")
    rencanaPerjalananList: List['RencanaPerjalanan'] = Relationship(back_populates="lokasi")

# merepresentasikan gambar perjalanan (ENTITY)
class TripImage(SQLModel, table=True):
    __tablename__ = "trip_image"

    trip_image_id: UUID = Field(default_factory=uuid4, primary_key=True)
    image_url: str
    
    # Foreign Key ke RencanaPerjalanan
    plan_id: UUID = Field(foreign_key="rencanaperjalanan.id_rencana")
    plan: 'RencanaPerjalanan' = Relationship(back_populates="trip_images")

# merepresentasikan titik penjemputan (ENTITY)
class TripPickupPoint(SQLModel, table=True):
    __tablename__ = "trip_pickup_point"

    trip_pickup_id: UUID = Field(default_factory=uuid4, primary_key=True)
    lokasi_jemput: str
    
    # Foreign Key ke RencanaPerjalanan
    plan_id: UUID = Field(foreign_key="rencanaperjalanan.id_rencana")
    plan: 'RencanaPerjalanan' = Relationship(back_populates="trip_pickup_points")

# merepresentasikan item yang termasuk dalam paket (ENTITY)
class TripInclude(SQLModel, table=True):
    __tablename__ = "trip_include"

    trip_include_id: UUID = Field(default_factory=uuid4, primary_key=True)
    item_include: str
    
    # Foreign Key ke RencanaPerjalanan
    plan_id: UUID = Field(foreign_key="rencanaperjalanan.id_rencana")
    plan: 'RencanaPerjalanan' = Relationship(back_populates="trip_includes")

# merepresentasikan satu kegiatan terjadwal dalam rencana perjalanan
class Aktivitas(SQLModel, table=True):
    __tablename__ = "aktivitas"

    id_aktivitas: UUID = Field(default_factory=uuid4, primary_key=True)
    waktu_mulai: time
    waktu_selesai: time
    deskripsi: str

    id_lokasi: UUID = Field(foreign_key="lokasi.id_lokasi")
    lokasi: 'Lokasi' = Relationship(back_populates="aktivitasList")

    # Foreign Key ke HariPerjalanan
    hari_id: Optional[UUID] = Field(default=None, foreign_key="hari_perjalanan.id_hari")
    hari: Optional['HariPerjalanan'] = Relationship(back_populates="aktivitasList")

    # cek apakah tumpang tindih dengan aktivitas lain
    def validasi_konflik(self, aktivitas_lain: 'Aktivitas'):
        return (self.waktu_mulai < aktivitas_lain.waktu_selesai and 
        self.waktu_selesai > aktivitas_lain.waktu_mulai)

# merepresentasikan pengeluaran uang dalam perjalanan
class Pengeluaran(SQLModel, table=True):
    idPengeluaran: UUID = Field(default_factory=uuid4, primary_key=True)
    deskripsi: str
    tanggalPengeluaran: date

    # Flattening Value Object Uang
    biaya_jumlah: float
    biaya_mata_uang: str = "IDR"

    # Foreign Key ke RencanaPerjalanan
    rencana_id: Optional[UUID] = Field(default=None, foreign_key="rencanaperjalanan.id_rencana")
    rencana: Optional['RencanaPerjalanan'] = Relationship(back_populates="pengeluaranList")

# merepresentasikan 1 hari dalam rencana perjalanan
class HariPerjalanan(SQLModel, table=True):
    __tablename__ = "hari_perjalanan"

    id_hari: UUID = Field(default_factory=uuid4, primary_key=True)
    tanggal: date
    notes: Optional[str] = None
    
    # Foreign Key ke RencanaPerjalanan
    rencana_id: Optional[UUID] = Field(default=None, foreign_key="rencanaperjalanan.id_rencana")
    rencana: Optional['RencanaPerjalanan'] = Relationship(back_populates="hariPerjalananList")

    # Relasi ke Aktivitas
    aktivitasList: List[Aktivitas] = Relationship(back_populates="hari", sa_relationship_kwargs={"cascade": "all, delete"})

    # method untuk menambah aktivitas dalam 1 hari
    def tambahAktivitas(self, aktivitas_baru: Aktivitas):
        # cek apakah aktivitas yang ingin ditambahkan tumpang tindih
        for aktivitas in self.aktivitasList:
            if aktivitas.validasi_konflik(aktivitas_baru):
                raise AktivitasKonflikException(
                    f"Aktivitas '{aktivitas_baru.deskripsi}' bertabrakan dengan '{aktivitas.deskripsi}'"
                )

        self.aktivitasList.append(aktivitas_baru)