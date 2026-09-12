"""Container-local evidence that the worker completed useful work or an idle poll."""
import os
import tempfile
import time
from pathlib import Path

from .config import get_settings

HEARTBEAT_PATH = Path(tempfile.gettempdir()) / "fattech-worker.heartbeat"


def write_heartbeat(path: Path = HEARTBEAT_PATH) -> None:
    """Atomic replacement prevents the health probe from observing a partial write."""
    with tempfile.NamedTemporaryFile(mode="w", encoding="ascii", dir=path.parent,
                                     prefix=".fattech-heartbeat-", delete=False) as temporary:
        temporary_path = Path(temporary.name)
        temporary.write(str(time.monotonic()))
    try:
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def heartbeat_is_fresh(path: Path = HEARTBEAT_PATH, *, max_age: float = 120) -> bool:
    try:
        with path.open(encoding="ascii") as heartbeat:
            last_success = float(heartbeat.read(128))
        return 0 <= time.monotonic() - last_success <= max_age
    except (OSError, ValueError, UnicodeError):
        return False


def main() -> None:
    settings = get_settings()
    if not heartbeat_is_fresh(max_age=max(120, settings.worker_poll_seconds * 3)):
        raise SystemExit("worker heartbeat missing or stale")


if __name__ == "__main__":
    main()
