# skrip berisikan entity

from pydantic import BaseModel, Field, model_validator
from typing import List
from uuid import UUID, uuid4
from datetime import time, date
from models.value_objects import Lokasi, Uang
from models.exception import AktivitasKonflikException

# merepresentasikan satu kegiatan terjadwal dalam rencana perjalanan
class Aktivitas(BaseModel):
    idAktivitas: UUID = Field(default_factory=uuid4)
    waktuMulai: time
    waktuSelesai: time
    lokasi: Lokasi
    deskripsi: str

    # validasi waktu aktivitas tidak boleh melebihi waktu selesai
    @model_validator(mode='after')
    def validasi_waktu_aktivitas(self):
        if self.waktuMulai and self.waktuSelesai and self.waktuMulai > self.waktuSelesai:
            raise ValueError("Waktu mulai aktivitas tidak boleh melebihi waktu selesai")
        return self

    # cek apakah tumpang tindih dengan aktivitas lain
    def validasi_konflik(self, aktivitas_lain: 'Aktivitas'):
        return (self.waktuMulai < aktivitas_lain.waktuSelesai and 
        self.waktuSelesai > aktivitas_lain.waktuMulai)

# merepresentasikan pengeluaran uang dalam perjalanan
class Pengeluaran(BaseModel):
    idPengeluaran: UUID = Field(default_factory=uuid4)
    deskripsi: str
    biaya: Uang
    tanggalPengeluaran: date

# merepresentasikan 1 hari dalam rencana perjalanan
class HariPerjalanan(BaseModel):
    idHari: UUID = Field(default_factory=uuid4)
    tanggal: date
    aktivitasList: List[Aktivitas] = Field(default_factory=list)

    # method untuk menambah aktivitas dalam 1 hari
    def tambahAktivitas(self, aktivitas_baru: Aktivitas):
        # cek apakah aktivitas yang ingin ditambahkan tumpang tindih
        for aktivitas in self.aktivitasList:
            if aktivitas.validasi_konflik(aktivitas_baru):
                raise AktivitasKonflikException(
                    f"Aktivitas '{aktivitas_baru.deskripsi}' tumpang tindih dengan '{aktivitas.deskripsi}'"
                )

        self.aktivitasList.append(aktivitas_baru)