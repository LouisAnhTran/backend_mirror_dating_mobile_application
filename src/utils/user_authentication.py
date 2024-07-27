
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from src.config import SECRET_KEY,ALGORITHM
from passlib.context import CryptContext
from fastapi import Cookie, HTTPException
from typing import Optional
from jose import JWTError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_access_token_cookie(access_token: Optional[str] = Cookie(None)) -> str:
    if access_token is None:
        raise HTTPException(status_code=401, detail="Cookie not found")
    return access_token

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token payload invalid")
        exp = payload.get("exp")
        if not exp or datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Token expired")
        return username
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token invalid")

