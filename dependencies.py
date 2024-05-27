
from passlib.context import CryptContext

from database import AsyncSessionLocal


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
        await session.commit()
        