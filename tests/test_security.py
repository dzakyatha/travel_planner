import pytest
import sys
from pathlib import Path
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError

#parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    get_username_from_token,
    get_current_user,
    SECRET_KEY,
    ALGORITHM,
    fake_users_db
)
from fastapi import HTTPException

# ==================== Password Hashing Tests ====================

def test_hash_password():
    password = "mysecretpassword"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert hashed.startswith("$2b$")
    assert len(hashed) == 60

def test_verify_password_correct():
    password = "correctpassword"
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed) is True

def test_verify_password_incorrect():
    password = "correctpassword"
    wrong_password = "wrongpassword"
    hashed = get_password_hash(password)
    
    assert verify_password(wrong_password, hashed) is False

def test_hash_password_different_each_time():
    password = "samepassword"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    
    assert hash1 != hash2
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True

def test_verify_empty_password():
    hashed = get_password_hash("password123")
    assert verify_password("", hashed) is False

# ==================== JWT Token Creation Tests ====================

def test_create_access_token_basic():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0

def test_create_access_token_with_expiration():
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=15)
    token = create_access_token(data, expires_delta)
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert "exp" in payload
    assert "sub" in payload
    assert payload["sub"] == "testuser"

def test_create_access_token_payload_preserved():
    data = {
        "sub": "testuser",
        "role": "admin",
        "email": "test@example.com"
    }
    token = create_access_token(data)
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "testuser"
    assert payload["role"] == "admin"
    assert payload["email"] == "test@example.com"

def test_create_access_token_expiration_time():
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=30)
    
    before_creation = datetime.now(timezone.utc)
    token = create_access_token(data, expires_delta)
    after_creation = datetime.now(timezone.utc)
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    
    expected_exp = before_creation + expires_delta
    assert abs((exp_time - expected_exp).total_seconds()) < 5  # 5 second tolerance

# ==================== JWT Token Verification Tests ====================

def test_verify_token_valid():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    payload = verify_token(token)
    
    assert payload is not None
    assert payload["sub"] == "testuser"

def test_verify_token_invalid_signature():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    tampered_token = token[:-10] + "tamperedXX"
    
    payload = verify_token(tampered_token)
    assert payload is None

def test_verify_token_expired():
    data = {"sub": "testuser"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))
    
    payload = verify_token(token)
    assert payload is None

def test_verify_token_malformed():
    malformed_tokens = [
        "not.a.token",
        "invalid",
        "",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    ]
    
    for token in malformed_tokens:
        payload = verify_token(token)
        assert payload is None

def test_verify_token_wrong_algorithm():
    data = {"sub": "testuser"}
    wrong_token = jwt.encode(data, SECRET_KEY, algorithm="HS512")
    
    payload = verify_token(wrong_token)
    assert payload is None

# ==================== Get Username from Token Tests ====================

def test_get_username_from_token_valid():
    data = {"sub": "johndoe"}
    token = create_access_token(data)
    
    username = get_username_from_token(token)
    assert username == "johndoe"

def test_get_username_from_token_invalid():
    username = get_username_from_token("invalid.token.here")
    assert username is None

def test_get_username_from_token_no_sub():
    data = {"user": "johndoe"}
    token = create_access_token(data)
    
    username = get_username_from_token(token)
    assert username is None

def test_get_username_from_token_expired():
    data = {"sub": "johndoe"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))
    
    username = get_username_from_token(token)
    assert username is None

# ==================== Get Current User Tests ====================

@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    data = {"sub": "johndoe"}
    token = create_access_token(data)
    
    username = await get_current_user(token)
    assert username == "johndoe"

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("invalid.token")
    
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail

@pytest.mark.asyncio
async def test_get_current_user_expired_token():
    data = {"sub": "johndoe"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token)
    
    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user_no_sub_claim():
    data = {"user": "johndoe"}
    token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token)
    
    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user_empty_token():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("")
    
    assert exc_info.value.status_code == 401

# ==================== Authentication Flow Tests ====================

def test_fake_users_db_structure():
    assert "johndoe" in fake_users_db
    assert "alice" in fake_users_db
    
    user = fake_users_db["johndoe"]
    assert "username" in user
    assert "hashed_password" in user
    assert "email" in user
    assert "disabled" in user

def test_fake_users_password_verification():
    johndoe_hash = fake_users_db["johndoe"]["hashed_password"]
    alice_hash = fake_users_db["alice"]["hashed_password"]
    
    assert verify_password("rahasia", johndoe_hash) is True
    assert verify_password("rahasia2", alice_hash) is True
    assert verify_password("wrongpassword", johndoe_hash) is False

# ==================== Security Edge Cases ====================

def test_token_with_special_characters_in_username():
    special_usernames = [
        "user@example.com",
        "user_name-123",
        "user.name",
    ]
    
    for username in special_usernames:
        data = {"sub": username}
        token = create_access_token(data)
        decoded_username = get_username_from_token(token)
        assert decoded_username == username

def test_token_with_unicode_username():
    data = {"sub": "用户名"}
    token = create_access_token(data)
    username = get_username_from_token(token)
    assert username == "用户名"

def test_password_hash_with_special_characters():
    passwords = [
        "p@ssw0rd!",
        "密码123",
        "pass word with spaces",
        "🔐secure🔑",
    ]
    
    for password in passwords:
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

def test_very_long_password():
    long_password = "a" * 1000
    hashed = get_password_hash(long_password)
    assert verify_password(long_password, hashed) is True

def test_token_tampering_detection():
    data = {"sub": "admin"}
    token = create_access_token(data)
    
    parts = token.split('.')
    tampered_tokens = [
        parts[0] + "." + parts[1] + ".tampered",
        "tampered." + parts[1] + "." + parts[2],
        parts[0] + ".tampered." + parts[2],
    ]
    
    for tampered in tampered_tokens:
        payload = verify_token(tampered)
        assert payload is None

# ==================== Integration Tests ====================

@pytest.mark.asyncio
async def test_complete_authentication_flow():
    username = "johndoe"
    data = {"sub": username}
    token = create_access_token(data, expires_delta=timedelta(minutes=30))
    
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == username
    
    extracted_username = get_username_from_token(token)
    assert extracted_username == username
    
    current_user = await get_current_user(token)
    assert current_user == username

def test_password_change_flow():
    old_password = "oldpassword"
    new_password = "newpassword"
    
    # hash password lama
    old_hash = get_password_hash(old_password)
    
    # memverifikasi password lama
    assert verify_password(old_password, old_hash) is True
    
    # hash password baru
    new_hash = get_password_hash(new_password)
    
    # memverifikasi password baru
    assert verify_password(new_password, new_hash) is True
    
    # memverifikasi password lama tidak cocok dengan hash baru
    assert verify_password(old_password, new_hash) is False