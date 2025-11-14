# skrip berisikan Aggregate Root untuk Konteks Perencanaan Perjalanan

from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import date
from models.value_objects import Durasi, Uang
from models.entity import HariPerjalanan, Pengeluaran
from models.exception import TanggalDiLuarDurasiException, AnggaranTerlampauiException

# Kelas ini adalah satu-satunya titik masuk untuk memodifikasi state internal
class RencanaPerjalanan(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    nama: str
    durasi: Durasi
    anggaran: Uang
    hariPerjalananList: List[HariPerjalanan] = Field(default_factory=list)
    pengeluaranList: List[Pengeluaran] = Field(default_factory=list)

    # method untuk Menghitung total pengeluaran dari list
    def _totalPengeluaranSaatIni(self):
        return sum(p.biaya.jumlah for p in self.pengeluaranList)

    # method untuk membuat dan menambahkan HariPerjalanan baru ke rencana
    def tambahHariPerjalanan(self, tanggal: date) -> HariPerjalanan:
        # cek apakah tanggal HariPerjalanan melebihi durasi
        if not (self.durasi.tanggalMulai <= tanggal <= self.durasi.tanggalSelesai):
            raise TanggalDiLuarDurasiException(
                f"Tanggal {tanggal} berada di luar durasi rencana ({self.durasi.tanggalMulai} s/d {self.durasi.tanggalSelesai})"
            )
        
        # cek apakah tanggal sudah ada
        if any(hari.tanggal == tanggal for hari in self.hariPerjalananList):
            raise ValueError(f"Hari perjalanan dengan tanggal {tanggal} sudah ada")
        
        hari_baru = HariPerjalanan(tanggal=tanggal)
        self.hariPerjalananList.append(hari_baru)
        return hari_baru

    # method untuk menambahkan item pengeluaran baru ke rencana
    def tambahPengeluaran(self, pengeluaran_baru: Pengeluaran):
        total_setelah_tambah = self._totalPengeluaranSaatIni() + pengeluaran_baru.biaya.jumlah

        # cek apakah pengeluaran melebihi anggaran
        if total_setelah_tambah > self.anggaran.jumlah:
            raise AnggaranTerlampauiException(
                f"Pengeluaran '{pengeluaran_baru.deskripsi}' sejumlah ({pengeluaran_baru.biaya.jumlah}) melebihi anggaran"
            )
        
        # validasi tanggal pengeluaran harus dalam durasi rencana
        if not (self.durasi.tanggalMulai <= pengeluaran_baru.tanggalPengeluaran <= self.durasi.tanggalSelesai):
            raise TanggalDiLuarDurasiException(
                f"Tanggal pengeluaran {pengeluaran_baru.tanggalPengeluaran} berada di luar durasi rencana"
            )
        
        self.pengeluaranList.append(pengeluaran_baru)

    # method untuk mengelola anggaran rencana perjalanan
    def setAnggaran(self, anggaran_baru: Uang):
        # validasi anggaran baru tidak boleh lebih kecil dari pengeluaran saat ini
        if anggaran_baru.jumlah < self._totalPengeluaranSaatIni():
            raise ValueError("Anggaran baru tidak boleh lebih kecil dari total pengeluaran saat ini")

        self.anggaran = anggaran_baru

    # method untuk mengelola durasi rencana perjalanan
    def setDurasi(self, durasi_baru: Durasi):
        # cek apakah ada hari yang berada di luar durasi baru
        hari_di_luar_durasi = [
            hari for hari in self.hariPerjalananList
            if not (durasi_baru.tanggalMulai <= hari.tanggal <= durasi_baru.tanggalSelesai)
        ]
        
        if hari_di_luar_durasi:
            tanggal_invalid = [hari.tanggal for hari in hari_di_luar_durasi]
            raise TanggalDiLuarDurasiException(
                f"Tidak dapat mengubah durasi: terdapat hari perjalanan di luar durasi baru: {tanggal_invalid}"
            )
        
        # cek apakah ada pengeluaran yang berada di luar durasi baru
        pengeluaran_di_luar_durasi = [
            p for p in self.pengeluaranList
            if not (durasi_baru.tanggalMulai <= p.tanggalPengeluaran <= durasi_baru.tanggalSelesai)
        ]
        
        if pengeluaran_di_luar_durasi:
            tanggal_invalid = [p.tanggalPengeluaran for p in pengeluaran_di_luar_durasi]
            raise TanggalDiLuarDurasiException(
                f"Tidak dapat mengubah durasi: terdapat pengeluaran di luar durasi baru: {tanggal_invalid}"
            )
        
        self.durasi = durasi_baru

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
        return self._totalPengeluaranSaatIni()

    # method untuk mendapatkan sisa anggaran
    def getSisaAnggaran(self) -> float:
        return self.anggaran.jumlah - self._totalPengeluaranSaatIni()

    # method untuk mendapatkan jumlah hari perjalanan
    def getJumlahHariPerjalanan(self) -> int:
        return len(self.hariPerjalananList)

    # method untuk mendapatkan jumlah pengeluaran
    def getJumlahPengeluaran(self) -> int:
        return len(self.pengeluaranList)

