"""Thread-safe key-value store."""

import threading
from collections.abc import KeysView
from typing import Any


class Database:
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            return self._store.get(key)

    def set(self, key: str, val: Any) -> None:
        with self._lock:
            self._store[key] = val

    def keys(self) -> KeysView[str]:
        with self._lock:
            return self._store.keys()

    def clear(self) -> None:
        """For testing only."""
        with self._lock:
            self._store.clear()
