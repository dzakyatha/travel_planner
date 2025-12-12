# skrip berisikan logika enkripsi dan autentikasi

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status

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

# Konfigurasi OAuth2 (Endpoint untuk mendapatkan token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Dummy Database User
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
    except JWTError:
        raise credentials_exception
    
    # Cek apakah user ada di dummy DB
    if username not in fake_users_db:
        raise credentials_exception
        
    return username

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