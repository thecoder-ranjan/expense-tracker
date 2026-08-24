import hashlib
import hmac
import os
import database

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2 with SHA-256 and a random salt."""
    salt = os.urandom(16)
    # Use 100,000 iterations of SHA-256
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    # Combine salt and hash into a hex-encoded string for storage
    return salt.hex() + ":" + pwd_hash.hex()

def verify_password(password: str, stored_hash_str: str) -> bool:
    """Verifies a password against a stored hash string."""
    try:
        salt_hex, hash_hex = stored_hash_str.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        # Compute the hash of the input password using the stored salt
        actual_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(expected_hash, actual_hash)
    except (ValueError, TypeError):
        return False

def register_user(username: str, password: str) -> bool:
    """Registers a new user after hashing the password."""
    username = username.strip().lower()
    if not username or not password:
        return False
    
    # Check if user already exists
    existing_user = database.get_user_by_username(username)
    if existing_user:
        return False
    
    hashed_pwd = hash_password(password)
    user_id = database.create_user(username, hashed_pwd)
    return user_id is not None

def authenticate_user(username: str, password: str):
    """Authenticates a user and returns the user object if successful."""
    username = username.strip().lower()
    if not username or not password:
        return None
    
    user = database.get_user_by_username(username)
    if user and verify_password(password, user['password_hash']):
        return dict(user)
    return None
