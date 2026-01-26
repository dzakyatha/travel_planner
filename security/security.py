# skrip berisikan logika enkripsi dan autentikasi

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security, HTTPException, status
from pydantic import BaseModel

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


security = HTTPBearer()

class AuthenticatedUser(BaseModel):
    id: str
    email: str
    role: str

# fungsi untuk mengecek user saat ini berdasarkan token JWT
def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> AuthenticatedUser:
    token = credentials.credentials

    # Exception untuk invalid credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify the signature directly (Stateless)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extract user info that Django put into the token
        user_id = payload.get("user_id")
        
        if user_id is None:
            raise credentials_exception
            
        return AuthenticatedUser(
            id=str(user_id),
            email=payload.get("email"),
            role=payload.get("role", "CUSTOMER")
        )
    
    # Handle JWT errors
    except JWTError:
        raise credentials_exception