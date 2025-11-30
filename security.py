# skrip berisikan logika enkripsi dan autentikasi

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# load environment variables
load_dotenv()

# Konfigurasi JWT
# Environment variable untuk production
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY tidak ditemukan di environment variable"
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Konfigurasi Hashing Password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fungsi untuk verifikasi apakah password plain text cocok dengan hash yang tersimpan dari database
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Fungsi untuk mengubah hashing password plain text
def get_password_hash(password):
    return pwd_context.hash(password)

# Fungsi untuk membuat JWT untuk akses baru
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    # Set waktu expire
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Fungsi untuk verifikasi dan decode JWT
def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Fungsi untuk mendapatkan username dari JWT
def get_username_from_token(token: str) -> Optional[str]:
    # verifikasi token
    payload = verify_token(token)

    if payload: # jika token valid
        return payload.get("sub")
    return None