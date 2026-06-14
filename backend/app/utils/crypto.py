import os
import base64
import hashlib
import json
from cryptography.fernet import Fernet


def _fernet() -> Fernet:
    key = os.getenv('SECRET_KEY', 'change-me-in-production')
    derived = hashlib.sha256(key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


def encrypt(data: dict) -> str:
    return _fernet().encrypt(json.dumps(data).encode()).decode()


def decrypt(token: str) -> dict:
    return json.loads(_fernet().decrypt(token.encode()).decode())
