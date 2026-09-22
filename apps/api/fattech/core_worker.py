"""Run Core-Engine consumers independently of external n8n delivery."""
import argparse
import logging
import signal
import threading

from .config import get_settings
from .core_engine import run_once
from .db import make_engine, session_factory
from .worker_health import HEARTBEAT_PATH, write_heartbeat


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Process one bounded round for every tenant")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    engine = make_engine(settings.database_url)
    factory = session_factory(engine)
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    HEARTBEAT_PATH.unlink(missing_ok=True)
    try:
        while not stop.is_set():
            try:
                count = run_once(factory, settings, on_progress=write_heartbeat)
                write_heartbeat()
            except Exception as exc:
                HEARTBEAT_PATH.unlink(missing_ok=True)
                logging.error("core_iteration_failed type=%s", type(exc).__name__)
                if args.once:
                    raise SystemExit(1) from None
                count = 0
            if args.once:
                break
            stop.wait(0.05 if count else settings.worker_poll_seconds)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
