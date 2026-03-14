# skrip berisikan Aggregate Root untuk Konteks Perencanaan Perjalanan

from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import date
from models.entity import HariPerjalanan, Pengeluaran, Lokasi, TripImage, TripPickupPoint, TripInclude
from models.exception import TanggalDiLuarDurasiException, AnggaranTerlampauiException

# merepresentasikan rencana perjalanan
class RencanaPerjalanan(SQLModel, table=True):
    __tablename__ = "rencanaperjalanan"

    id_rencana: UUID = Field(default_factory=uuid4, primary_key=True)
    id_user: UUID
    nama: str
    deskripsi: Optional[str] = None
    harga: float
    durasi_mulai: date
    durasi_selesai: date
    slot: int
    slot_tersedia: int = 0
    provinsi: str
    negara: str
    destination_type: str
    jumlah_hari: int
    jumlah_malam: int
    createdAt: date

    # Foreign Key untuk Lokasi
    id_lokasi: Optional[UUID] = Field(default=None, foreign_key="lokasi.id_lokasi")
    lokasi: Optional[Lokasi] = Relationship(back_populates="rencanaPerjalananList")

    # Relasi One-to-Many
    hariPerjalananList: List[HariPerjalanan] = Relationship(back_populates="rencana", sa_relationship_kwargs={"cascade": "all, delete"})
    pengeluaranList: List[Pengeluaran] = Relationship(back_populates="rencana", sa_relationship_kwargs={"cascade": "all, delete"})
    trip_images: List[TripImage] = Relationship(back_populates="plan", sa_relationship_kwargs={"cascade": "all, delete"})
    trip_pickup_points: List[TripPickupPoint] = Relationship(back_populates="plan", sa_relationship_kwargs={"cascade": "all, delete"})
    trip_includes: List[TripInclude] = Relationship(back_populates="plan", sa_relationship_kwargs={"cascade": "all, delete"})

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
        if total_setelah_tambah > self.harga:
            raise AnggaranTerlampauiException(
                f"Pengeluaran '{pengeluaran_baru.deskripsi}' sejumlah ({pengeluaran_baru.biaya_jumlah}) melebihi anggaran"
            )
        
        # validasi tanggal pengeluaran harus dalam durasi rencana
        if not (self.durasi_mulai <= pengeluaran_baru.tanggalPengeluaran <= self.durasi_selesai):
            raise TanggalDiLuarDurasiException(
                f"Tanggal pengeluaran {pengeluaran_baru.tanggalPengeluaran} berada di luar durasi rencana"
            )
        
        self.pengeluaranList.append(pengeluaran_baru)

    # method untuk menambahkan gambar ke rencana
    def tambahTripImage(self, image_url: str) -> TripImage:
        trip_image = TripImage(image_url=image_url)
        self.trip_images.append(trip_image)
        return trip_image

    # method untuk menambahkan titik penjemputan ke rencana
    def tambahTripPickupPoint(self, lokasi_jemput: str) -> TripPickupPoint:
        pickup_point = TripPickupPoint(lokasi_jemput=lokasi_jemput)
        self.trip_pickup_points.append(pickup_point)
        return pickup_point

    # method untuk menambahkan item yang termasuk dalam paket
    def tambahTripInclude(self, item_include: str) -> TripInclude:
        trip_include = TripInclude(item_include=item_include)
        self.trip_includes.append(trip_include)
        return trip_include

    # method untuk menghapus gambar
    def hapusTripImage(self, trip_image_id: UUID) -> bool:
        trip_image = next((img for img in self.trip_images if img.trip_image_id == trip_image_id), None)
        if trip_image:
            self.trip_images.remove(trip_image)
            return True
        return False

    # method untuk menghapus titik penjemputan
    def hapusTripPickupPoint(self, trip_pickup_id: UUID) -> bool:
        pickup_point = next((p for p in self.trip_pickup_points if p.trip_pickup_id == trip_pickup_id), None)
        if pickup_point:
            self.trip_pickup_points.remove(pickup_point)
            return True
        return False

    # method untuk menghapus item include
    def hapusTripInclude(self, trip_include_id: UUID) -> bool:
        trip_include = next((inc for inc in self.trip_includes if inc.trip_include_id == trip_include_id), None)
        if trip_include:
            self.trip_includes.remove(trip_include)
            return True
        return False

    # method untuk mengelola anggaran rencana perjalanan
    def setAnggaran(self, jumlah_baru: float, mata_uang: str = "IDR"):
        # validasi anggaran baru tidak boleh lebih kecil dari pengeluaran saat ini
        if jumlah_baru < self.totalPengeluaranSaatIni():
            raise AnggaranTerlampauiException(
                f"Anggaran baru ({jumlah_baru}) tidak boleh lebih kecil dari total pengeluaran saat ini ({self.totalPengeluaranSaatIni()})"
            )

        self.harga = jumlah_baru

    # method untuk mengelola durasi rencana perjalanan
    def setDurasi(self, tanggal_mulai: date, tanggal_selesai: date):
        # cek apakah ada hari yang berada di luar durasi baru
        hari_di_luar_durasi = [
            hari for hari in self.hariPerjalananList
            if not (tanggal_mulai <= hari.tanggal <= tanggal_selesai)
        ]
        
        if hari_di_luar_durasi:
            raise TanggalDiLuarDurasiException(
                f"Ada {len(hari_di_luar_durasi)} hari perjalanan yang berada di luar durasi baru"
            )
        
        # cek apakah ada pengeluaran yang berada di luar durasi baru
        pengeluaran_di_luar_durasi = [
            p for p in self.pengeluaranList
            if not (tanggal_mulai <= p.tanggalPengeluaran <= tanggal_selesai)
        ]
        
        if pengeluaran_di_luar_durasi:
            raise TanggalDiLuarDurasiException(
                f"Ada {len(pengeluaran_di_luar_durasi)} pengeluaran yang berada di luar durasi baru"
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
        return self.harga - self.totalPengeluaranSaatIni()

    # method untuk mendapatkan jumlah hari perjalanan
    def getJumlahHariPerjalanan(self) -> int:
        return len(self.hariPerjalananList)

    # method untuk mendapatkan jumlah pengeluaran
    def getJumlahPengeluaran(self) -> int:
        return len(self.pengeluaranList)

