import secrets
import string
import time
from datetime import datetime, timedelta, timezone

import json

import bcrypt
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import OKPKey

from app.config import settings


def generate_random_password(length: int = 8) -> str:
    """
    生成包含字母和数字的随机密码
    使用 Python secrets 模块确保密码安全
    """
    if length < 2:
        raise ValueError("密码长度至少为2")

    alphabets = string.ascii_letters
    digits = string.digits

    password = [
        secrets.choice(alphabets),
        secrets.choice(digits),
    ]

    all_chars = alphabets + digits
    for _ in range(length - 2):
        password.append(secrets.choice(all_chars))

    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict, expires_delta: timedelta | None = None, token_version: int | None = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": now})
    if token_version is not None:
        to_encode["token_version"] = token_version
    private_key_data = json.loads(settings.JWT_PRIVATE_KEY)
    key = OKPKey.import_key(private_key_data)
    header = {"alg": "Ed25519"}
    return jwt.encode(header, to_encode, key, algorithms=["Ed25519"])


def decode_access_token(token: str) -> dict | None:
    try:
        public_key_data = json.loads(settings.JWT_PUBLIC_KEY)
        key = OKPKey.import_key(public_key_data)
        token_obj = jwt.decode(token, key, algorithms=["Ed25519"])
        claims = token_obj.claims
        exp = claims.get("exp")
        if exp is None or exp < time.time():
            return None
        return claims
    except JoseError:
        return None
