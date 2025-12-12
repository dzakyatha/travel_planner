# skrip berisikan Aggregate Root untuk Konteks Perencanaan Perjalanan

from sqlmodel import SQLModel, Field, Relationship
from typing import List
from uuid import UUID, uuid4
from datetime import date
from models.entity import HariPerjalanan, Pengeluaran
from models.exception import TanggalDiLuarDurasiException, AnggaranTerlampauiException

# Kelas ini adalah satu-satunya titik masuk untuk memodifikasi state internal
class RencanaPerjalanan(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    nama: str

    # Flattening Value Object Durasi dan Anggaran
    durasi_mulai: date
    durasi_selesai: date
    anggaran_jumlah: float
    anggaran_mata_uang: str = "IDR"

    # Relasi One-to-Many
    hariPerjalananList: List[HariPerjalanan] = Relationship(back_populates="rencana", sa_relationship_kwargs={"cascade": "all, delete"})
    pengeluaranList: List[Pengeluaran] = Relationship(back_populates="rencana", sa_relationship_kwargs={"cascade": "all, delete"})

    # method untuk Menghitung total pengeluaran dari list
    def totalPengeluaranSaatIni(self):
        return sum(p.biaya_jumlah for p in self.pengeluaranList)
    
    # method untuk membuat dan menambahkan HariPerjalanan baru ke rencana
    def tambahHariPerjalanan(self, tanggal: date) -> HariPerjalanan:
        # cek apakah tanggal HariPerjalanan melebihi durasi
        if not (self.durasi_mulai <= tanggal <= self.durasi_selesai):
            raise TanggalDiLuarDurasiException(
                f"Tanggal {tanggal} berada di luar durasi rencana ({self.durasi_mulai} s/d {self.durasi_selesai})"
            )
        
        # cek apakah tanggal sudah ada
        if any(hari.tanggal == tanggal for hari in self.hariPerjalananList):
            raise ValueError(f"Hari perjalanan dengan tanggal {tanggal} sudah ada")
        
        hari_baru = HariPerjalanan(tanggal=tanggal)
        self.hariPerjalananList.append(hari_baru)
        return hari_baru

    # method untuk menambahkan item pengeluaran baru ke rencana
    def tambahPengeluaran(self, pengeluaran_baru: Pengeluaran):
        total_setelah_tambah = self.totalPengeluaranSaatIni() + pengeluaran_baru.biaya_jumlah

        # cek apakah pengeluaran melebihi anggaran
        if total_setelah_tambah > self.anggaran_jumlah:
            raise AnggaranTerlampauiException(
                f"Pengeluaran '{pengeluaran_baru.deskripsi}' sejumlah ({pengeluaran_baru.biaya_jumlah}) melebihi anggaran"
            )
        
        # validasi tanggal pengeluaran harus dalam durasi rencana
        if not (self.durasi_mulai <= pengeluaran_baru.tanggalPengeluaran <= self.durasi_selesai):
            raise TanggalDiLuarDurasiException(
                f"Tanggal pengeluaran {pengeluaran_baru.tanggalPengeluaran} berada di luar durasi rencana"
            )
        
        self.pengeluaranList.append(pengeluaran_baru)

    # method untuk mengelola anggaran rencana perjalanan
    def setAnggaran(self, jumlah_baru: float, mata_uang: str = "IDR"):
        # validasi anggaran baru tidak boleh lebih kecil dari pengeluaran saat ini
        if jumlah_baru < self.totalPengeluaranSaatIni():
            raise ValueError("Anggaran baru tidak boleh lebih kecil dari total pengeluaran saat ini")

        self.anggaran_jumlah = jumlah_baru
        self.anggaran_mata_uang = mata_uang

    # method untuk mengelola durasi rencana perjalanan
    def setDurasi(self, tanggal_mulai: date, tanggal_selesai: date):
        # cek apakah ada hari yang berada di luar durasi baru
        hari_di_luar_durasi = [
            hari for hari in self.hariPerjalananList
            if not (tanggal_mulai <= hari.tanggal <= tanggal_selesai)
        ]
        
        if hari_di_luar_durasi:
            tanggal_invalid = [hari.tanggal for hari in hari_di_luar_durasi]
            raise TanggalDiLuarDurasiException(
                f"Tidak dapat mengubah durasi: terdapat hari perjalanan di luar durasi baru: {tanggal_invalid}"
            )
        
        # cek apakah ada pengeluaran yang berada di luar durasi baru
        pengeluaran_di_luar_durasi = [
            p for p in self.pengeluaranList
            if not (tanggal_mulai <= p.tanggalPengeluaran <= tanggal_selesai)
        ]
        
        if pengeluaran_di_luar_durasi:
            tanggal_invalid = [p.tanggalPengeluaran for p in pengeluaran_di_luar_durasi]
            raise TanggalDiLuarDurasiException(
                f"Tidak dapat mengubah durasi: terdapat pengeluaran di luar durasi baru: {tanggal_invalid}"
            )
        
        self.durasi_mulai = tanggal_mulai
        self.durasi_selesai = tanggal_selesai

    # method untuk mendapatkan hari perjalanan berdasarkan tanggal
    def getHariPerjalanan(self, tanggal: date):
        for hari in self.hariPerjalananList:
            if hari.tanggal == tanggal:
                return hari
        return None

    # method untuk menghapus hari perjalanan
    def hapusHariPerjalanan(self, tanggal: date):
        hari = self.getHariPerjalanan(tanggal)
        if hari:
            self.hariPerjalananList.remove(hari)
            return True
        return False

    # method untuk menghapus pengeluaran berdasarkan ID
    def hapusPengeluaran(self, id_pengeluaran: UUID):
        pengeluaran = next((p for p in self.pengeluaranList if p.idPengeluaran == id_pengeluaran), None)
        if pengeluaran:
            self.pengeluaranList.remove(pengeluaran)
            return True
        return False

    # method untuk mendapatkan total pengeluaran saat ini
    def getTotalPengeluaran(self) -> float:
        return self.totalPengeluaranSaatIni()

    # method untuk mendapatkan sisa anggaran
    def getSisaAnggaran(self) -> float:
        return self.anggaran_jumlah - self.totalPengeluaranSaatIni()

    # method untuk mendapatkan jumlah hari perjalanan
    def getJumlahHariPerjalanan(self) -> int:
        return len(self.hariPerjalananList)

    # method untuk mendapatkan jumlah pengeluaran
    def getJumlahPengeluaran(self) -> int:
        return len(self.pengeluaranList)

