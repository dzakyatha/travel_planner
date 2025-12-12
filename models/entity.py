# skrip berisikan entity

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import time, date
from models.exception import AktivitasKonflikException

if TYPE_CHECKING:
    from models.aggregate_root import RencanaPerjalanan

# merepresentasikan satu kegiatan terjadwal dalam rencana perjalanan
class Aktivitas(SQLModel, table=True):
    idAktivitas: UUID = Field(default_factory=uuid4, primary_key=True)
    waktuMulai: time
    waktuSelesai: time
    deskripsi: str

    # JSONB untuk Value Object Lokasi
    lokasi: Dict[str, Any] = Field(sa_column=Column(JSONB))

    # Foreign Key ke HariPerjalanan
    hari_id: Optional[UUID] = Field(default=None, foreign_key="hariperjalanan.idHari")
    hari: Optional['HariPerjalanan'] = Relationship(back_populates="aktivitasList")

    # cek apakah tumpang tindih dengan aktivitas lain
    def validasi_konflik(self, aktivitas_lain: 'Aktivitas'):
        return (self.waktuMulai < aktivitas_lain.waktuSelesai and 
        self.waktuSelesai > aktivitas_lain.waktuMulai)

# merepresentasikan pengeluaran uang dalam perjalanan
class Pengeluaran(SQLModel, table=True):
    idPengeluaran: UUID = Field(default_factory=uuid4, primary_key=True)
    deskripsi: str
    tanggalPengeluaran: date

    # Flattening Value Object Uang
    biaya_jumlah: float
    biaya_mata_uang: str = "IDR"

    # Foreign Key ke RencanaPerjalanan
    rencana_id: Optional[UUID] = Field(default=None, foreign_key="rencanaperjalanan.id")
    rencana: Optional['RencanaPerjalanan'] = Relationship(back_populates="pengeluaranList")

# merepresentasikan 1 hari dalam rencana perjalanan
class HariPerjalanan(SQLModel, table=True):
    idHari: UUID = Field(default_factory=uuid4, primary_key=True)
    tanggal: date
    
    # Foreign Key ke RencanaPerjalanan
    rencana_id: Optional[UUID] = Field(default=None, foreign_key="rencanaperjalanan.id")
    rencana: Optional['RencanaPerjalanan'] = Relationship(back_populates="hariPerjalananList")

    # Relasi ke Aktivitas
    aktivitasList: List[Aktivitas] = Relationship(back_populates="hari", sa_relationship_kwargs={"cascade": "all, delete"})

    # method untuk menambah aktivitas dalam 1 hari
    def tambahAktivitas(self, aktivitas_baru: Aktivitas):
        # cek apakah aktivitas yang ingin ditambahkan tumpang tindih
        for aktivitas in self.aktivitasList:
            if aktivitas.validasi_konflik(aktivitas_baru):
                raise AktivitasKonflikException(
                    f"Aktivitas '{aktivitas_baru.deskripsi}' tumpang tindih dengan '{aktivitas.deskripsi}'"
                )

        self.aktivitasList.append(aktivitas_baru)