"""Tests for the Database class."""

import threading

from db import Database

# Basic Operations


def test_storage() -> None:
    """Asserts that a value can be stored and retrieved from your database"""
    d = Database()
    k, v = "A", "1"
    d.set(k, v)
    assert v == d.get(k)


def test_get_nonexistent_key() -> None:
    """Test that getting a nonexistent key returns None."""
    d = Database()
    assert d.get("nonexistent") is None


# Keys


def test_keys() -> None:
    """Asserts that a keys() call to your database returns a key set"""
    d = Database()
    data = {"A": "1", "B": object, "C": 3}

    for k, v in data.items():
        d.set(k, v)
    assert data.keys() == d.keys()


def test_keys_empty() -> None:
    """Test that keys() returns empty when no keys defined."""
    d = Database()
    assert list(d.keys()) == []


# Thread Safety


def test_thread_safety() -> None:
    """Test that concurrent writes don't corrupt data."""
    d = Database()
    errors: list[Exception] = []

    def write_values(prefix: str, count: int) -> None:
        try:
            for i in range(count):
                d.set(f"{prefix}_{i}", f"value_{prefix}_{i}")
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=write_values, args=("A", 100)),
        threading.Thread(target=write_values, args=("B", 100)),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(list(d.keys())) == 200
