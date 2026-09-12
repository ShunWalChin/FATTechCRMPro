from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, Lock

import pytest
from argon2 import PasswordHasher
from argon2.exceptions import HashingError, InvalidHashError, VerificationError, VerifyMismatchError

from fattech import passwords


def test_hash_and_verify_share_two_slots_across_instances(monkeypatch):
    """Eight contenders, mixed operations, fake backend: no expensive parallel hashes."""
    ready = Barrier(9)
    two_entered, over_limit, release = Event(), Event(), Event()
    lock = Lock()
    active = peak = completed = 0

    def slow_backend():
        nonlocal active, peak, completed
        with lock:
            active += 1
            peak = max(peak, active)
            if active == 2:
                two_entered.set()
            if active > 2:
                over_limit.set()
        try:
            assert release.wait(3), "Test backend was not released"
        finally:
            with lock:
                active -= 1
                completed += 1

    def fake_hash(self, password, *, salt=None):
        assert password == b"candidate" and salt == b"test-salt"
        slow_backend()
        return "fake-hash"

    def fake_verify(self, hash, password):
        assert hash == "fake-hash" and password == b"candidate"
        slow_backend()
        return True

    monkeypatch.setattr(PasswordHasher, "hash", fake_hash)
    monkeypatch.setattr(PasswordHasher, "verify", fake_verify)
    hashers = [passwords.hasher, passwords._LimitedPasswordHasher()]

    def operation(index):
        ready.wait(timeout=3)
        hasher = hashers[(index // 2) % 2]
        return (hasher.hash(b"candidate", salt=b"test-salt") if index % 2 == 0
                else hasher.verify("fake-hash", b"candidate"))

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(operation, index) for index in range(8)]
        try:
            ready.wait(timeout=3)
            assert two_entered.wait(3), "Both permitted operations must be able to run"
            assert not over_limit.wait(0.1), "More than two operations entered the backend"
        finally:
            release.set()
        assert [future.result(timeout=3) for future in futures] == ["fake-hash", True] * 4
    assert peak == 2 and active == 0 and completed == 8


@pytest.mark.parametrize("operation,error", [
    ("hash", HashingError),
    ("verify", InvalidHashError),
    ("verify", VerificationError),
    ("verify", VerifyMismatchError),
])
def test_argon2_errors_release_both_slots_and_keep_contract(monkeypatch, operation, error):
    def fail(*args, **kwargs):
        raise error("simulated backend failure")

    monkeypatch.setattr(PasswordHasher, operation, fail)
    if operation == "hash":
        with pytest.raises(error):
            passwords.hasher.hash("candidate")
    else:
        assert passwords.verify_password("encoded", "candidate") is False

    # Nonblocking acquisition detects leaked capacity without hanging the test suite.
    acquired = 0
    try:
        for _ in range(2):
            assert passwords._password_slots.acquire(blocking=False), "Argon2 failure leaked a slot"
            acquired += 1
    finally:
        for _ in range(acquired):
            passwords._password_slots.release()


def test_argon2_parameters_and_successful_verification_contract(monkeypatch):
    assert (passwords.hasher.memory_cost, passwords.hasher.time_cost, passwords.hasher.parallelism) == (
        65536, 3, 2,
    )
    monkeypatch.setattr(PasswordHasher, "verify", lambda *args, **kwargs: True)
    assert passwords.verify_password("encoded", "candidate") is True
