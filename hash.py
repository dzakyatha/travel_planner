# skrip untuk hashing password plain_text

from security import get_password_hash

password = "rahasia2"
hashed = get_password_hash(password)
print(f"Hash for 'rahasia': {hashed}")