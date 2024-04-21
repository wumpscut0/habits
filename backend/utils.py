from fastapi import HTTPException
from passlib.handlers.pbkdf2 import pbkdf2_sha256


async def verify_password(password: str, hash_):
    if not pbkdf2_sha256.verify(password, hash_):
        raise HTTPException(
            status_code=401, detail="Wrong password"
        )
