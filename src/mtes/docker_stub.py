"""Stub entrypoint for Docker Compose services until full daemon implementation."""

import signal
import sys
import time

_SHUTDOWN = False


def _handle_signal(_signum: int, _frame: object) -> None:
    global _SHUTDOWN
    _SHUTDOWN = True


def main() -> None:
    service_name = sys.argv[1] if len(sys.argv) > 1 else "mtes"
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
    print(f"MTES stub service started: {service_name}", flush=True)
    while not _SHUTDOWN:
        time.sleep(1)
    print(f"MTES stub service stopped: {service_name}", flush=True)


if __name__ == "__main__":
    main()
