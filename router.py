# skrip berisikan router & endpoint API

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from uuid import UUID
from typing import List
from datetime import date, timedelta
from jose import JWTError, jwt

# model domain
from models.aggregate_root import RencanaPerjalanan
from models.entity import HariPerjalanan, Aktivitas, Pengeluaran
from models.exception import AnggaranTerlampauiException, AktivitasKonflikException, TanggalDiLuarDurasiException

# API Schema
from schema import RencanaPerjalananCreate, HariPerjalananCreate, PengeluaranCreate, AktivitasCreate, AnggaranUpdate, DurasiUpdate

# import dari security dan skema baru
from security import verify_password, create_access_token, SECRET_KEY, ALGORITHM
from schema import Token, TokenData, User, UserInDB

# Database sederhana (Dictionary)
db_rencana_perjalanan: dict[UUID, RencanaPerjalanan] = {}

# Konfigurasi autentikasi
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/perencanaan/token")

# Database User Sederhana (In-Memory)
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$0uRzXvbsgekbRC2tdMTvyeKWb/iCLE1wKsWQ1C.V6dGqmDGAIfKg.", # password: "rahasia"
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderland",
        "email": "alice@example.com",
        "hashed_password": "$2b$12$I/PaEyhwO0IH3qFYejMv3uZa2hjvFBTz5IZYJLfrTI/HMY.3zKJQm", # password: "rahasia2"
        "disabled": False,
    }
}

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None

# dependensi untuk memproteksi endpoint dan validasi JWT
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# router utama
router = APIRouter(
    prefix="/perencanaan",
    tags=["Perencanaan Perjalanan"]
)

# API Login untuk menghasilkan token
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(fake_users_db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# API untuk membuat RencanaPerjalanan baru
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RencanaPerjalanan)
def create_rencana_perjalanan(request: RencanaPerjalananCreate, current_user: User = Depends(get_current_user)) -> RencanaPerjalanan:
    try:
        # Membuat objek domain dari skema request
        rencana_baru = RencanaPerjalanan(
            nama=request.nama,
            durasi=request.durasi,
            anggaran=request.anggaran
        )
        
        # Menyimpan ke database
        db_rencana_perjalanan[rencana_baru.id] = rencana_baru
        
        return rencana_baru

    except ValueError as e:
        # Menangkap error validasi dari Value Object
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Helper function untuk mendapatkan rencana dari database
def _get_rencana_dari_db(rencana_id: UUID) -> RencanaPerjalanan:
    rencana = db_rencana_perjalanan.get(rencana_id)
    if not rencana:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rencana Perjalanan dengan ID {rencana_id} tidak ditemukan"
        )
    return rencana

# API untuk mendapatkan RencanaPerjalanan berdasarkan ID
@router.get("/{rencana_id}", response_model=RencanaPerjalanan)
def get_rencana_perjalanan(rencana_id: UUID, current_user: User = Depends(get_current_user)) -> RencanaPerjalanan:
    return _get_rencana_dari_db(rencana_id)

# API untuk menambahkan HariPerjalanan ke RencanaPerjalanan
@router.post("/{rencana_id}/hari", response_model=RencanaPerjalanan)
def add_hari_perjalanan_ke_rencana(rencana_id: UUID, request: HariPerjalananCreate, current_user: User = Depends(get_current_user)) -> RencanaPerjalanan:
    # mencari rencana perjalanan berdasarkan ID
    rencana = _get_rencana_dari_db(rencana_id)

    try:
        # panggil method menambah HariPerjalanan dari rencana
        rencana.tambahHariPerjalanan(tanggal=request.tanggal)
        
        # simpan perubahan
        db_rencana_perjalanan[rencana_id] = rencana
        
        return rencana
        
    # menangkap exception
    except TanggalDiLuarDurasiException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk menambahkan Pengeluaran ke RencanaPerjalanan
@router.post("/{rencana_id}/pengeluaran", response_model=RencanaPerjalanan)
def add_pengeluaran_ke_rencana(rencana_id: UUID, request: PengeluaranCreate, current_user: User = Depends(get_current_user)) -> RencanaPerjalanan:
    # mencari RencanaPerjalanan berdasarkan ID
    rencana = _get_rencana_dari_db(rencana_id)

    try:
        # Buat objek Pengeluaran dari request
        pengeluaran_baru = Pengeluaran(
            deskripsi=request.deskripsi,
            biaya=request.biaya,
            tanggalPengeluaran=request.tanggalPengeluaran
        )

        # panggil method tambah Pengeluaran dari rencana
        rencana.tambahPengeluaran(pengeluaran_baru)
        
        # simpan perubahan
        db_rencana_perjalanan[rencana_id] = rencana
        
        return rencana

    # menangkap exception
    except AnggaranTerlampauiException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except TanggalDiLuarDurasiException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e: # error dari value objects
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk menambahkan Aktivitas ke HariPerjalanan
@router.post("/{rencana_id}/hari/{tanggal}/aktivitas", response_model=RencanaPerjalanan)
def add_aktivitas_ke_hari(rencana_id: UUID, tanggal: date, request: AktivitasCreate, current_user: User = Depends(get_current_user)) -> RencanaPerjalanan:
    # mencari RencanaPerjalanan berdasarkan ID
    rencana = _get_rencana_dari_db(rencana_id)
    
    # cari HariPerjalanan berdasarkan tanggal
    hari = rencana.getHariPerjalanan(tanggal)
    if not hari:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hari perjalanan pada tanggal {tanggal} tidak ditemukan dalam rencana perjalanan"
        )
    
    try:
        # buat objek Aktivitas dari request
        aktivitas_baru = Aktivitas(
            waktuMulai=request.waktuMulai,
            waktuSelesai=request.waktuSelesai,
            lokasi=request.lokasi,
            deskripsi=request.deskripsi
        )
        
        # panggil method untuk menambah aktivitas dari HariPerjalanan
        hari.tambahAktivitas(aktivitas_baru)
        
        # simpan perubahan
        db_rencana_perjalanan[rencana_id] = rencana
        
        return rencana
        
    # menangkap exception
    except AktivitasKonflikException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e: # error dari value objects
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk mengupdate Anggaran RencanaPerjalanan
@router.put("/{rencana_id}/anggaran", response_model=RencanaPerjalanan)
def update_anggaran_rencana(rencana_id: UUID, request: AnggaranUpdate, current_user: User = Depends(get_current_user)) -> RencanaPerjalanan:
    # mencari RencanaPerjalanan berdasarkan ID
    rencana = _get_rencana_dari_db(rencana_id)
    
    try:
        # panggil method untuk kelola Anggaran dari rencana
        rencana.setAnggaran(request.anggaranBaru)
        
        # simpan perubahan
        db_rencana_perjalanan[rencana_id] = rencana
        return rencana
        
    # menangkap exception
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk mengupdate Durasi RencanaPerjalanan
@router.put("/{rencana_id}/durasi", response_model=RencanaPerjalanan)
def update_durasi_rencana(rencana_id: UUID, request: DurasiUpdate, current_user: User = Depends(get_current_user)) -> RencanaPerjalanan:
    # mencari RencanaPerjalanan berdasarkan ID
    rencana = _get_rencana_dari_db(rencana_id)
    
    try:
        # panggil method untuk kelola durasi dari rencana
        rencana.setDurasi(request.durasiBaru)
        
        # simpan perubahan
        db_rencana_perjalanan[rencana_id] = rencana
        return rencana
        
    # menangkap exception
    except TanggalDiLuarDurasiException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# API untuk menghapus HariPerjalanan dari Rencana Perjalanan
@router.delete("/{rencana_id}/hari/{tanggal}", response_model=RencanaPerjalanan)
def delete_hari_perjalanan(rencana_id: UUID, tanggal: date, current_user: User = Depends(get_current_user)) -> RencanaPerjalanan:
    # mencari RencanaPerjalanan berdasarkan ID
    rencana = _get_rencana_dari_db(rencana_id)
    
    # panggil method untuk hapus HariPerjalanan dari rencana
    hari_perjalanan = rencana.hapusHariPerjalanan(tanggal)
    
    # jika HariPerjalanan tidak ditemukan
    if not hari_perjalanan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hari perjalanan dengan tanggal {tanggal} tidak ditemukan"
        )
    
    # simpan perubahan
    db_rencana_perjalanan[rencana_id] = rencana

    return rencana

# API untuk menghapus Pengeluaran dari RencanaPerjalanan
@router.delete("/{rencana_id}/pengeluaran/{id_pengeluaran}", response_model=RencanaPerjalanan)
def delete_pengeluaran(rencana_id: UUID, id_pengeluaran: UUID, current_user: User = Depends(get_current_user)) -> RencanaPerjalanan:
    # mencari RencanaPerjalanan berdasarkan ID
    rencana = _get_rencana_dari_db(rencana_id)
    
    # panggil method untuk hapus Pengeluaran dari rencana berdasarkan ID
    pengeluaran = rencana.hapusPengeluaran(id_pengeluaran)
    
    # jika Pengeluaran tidak ada
    if not pengeluaran:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pengeluaran dengan ID {id_pengeluaran} tidak ditemukan"
        )
    
    # simpan perubahan
    db_rencana_perjalanan[rencana_id] = rencana

    return rencana