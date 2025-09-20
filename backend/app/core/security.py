from passlib.context import CryptContext
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTAuthentication,
)
from ..config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

jwt_authentication = JWTAuthentication(
    secret=settings.secret_key,
    lifetime_seconds=settings.access_token_expire_minutes * 60,
    tokenUrl="auth/jwt/login",
)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=lambda: jwt_authentication,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)