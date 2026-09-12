"""Bound Argon2 memory use to two operations per process, including unknown-user checks."""
import secrets
from threading import BoundedSemaphore
from typing import Literal

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# Shared by hashing and verification, including any additional hasher instances.
# Each process needs its own memory budget when configuring multiple API workers.
_password_slots = BoundedSemaphore(2)


class _LimitedPasswordHasher(PasswordHasher):
    def hash(self, password: str | bytes, *, salt: bytes | None = None) -> str:
        with _password_slots:
            return super().hash(password, salt=salt)

    def verify(self, hash: str | bytes, password: str | bytes) -> Literal[True]:
        with _password_slots:
            return super().verify(hash, password)


hasher = _LimitedPasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))


def verify_password(encoded: str, candidate: str) -> bool:
    try:
        return hasher.verify(encoded, candidate)
    except (VerificationError, InvalidHashError):
        return False
