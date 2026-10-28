import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES"))

"""
create a url token and hash it, 
then send the hashed token via email, 
while also assigning an expiration 
time to the token
"""

def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)

def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def reset_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)