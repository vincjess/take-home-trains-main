"""Tests for the Train Schedule API."""

import threading
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient

from app import app, db, train_service


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    """Clear the database before each test to ensure isolation."""
    db.clear()
    yield
    db.clear()


client = TestClient(app)


# Health Check


def test_startup() -> None:
    """Asserts that your service starts and responds"""
    response = client.get("/")
    assert response.status_code == 200 and response.text == '"OK"'


# POST /trains - Add/Update Train Schedules


@pytest.mark.parametrize(
    "train",
    [
        # I removed 1440 from the original test case because 0-1439 is the valid range.
        # I also removed the 1 test case because train IDs must be 1-6 alphabetic characters.
        {"id": "TOMO", "schedule": [180, 640, 1439]},
        {"id": "FOMO", "schedule": [440, 640]},
    ],
)
def test_add(train: dict[str, Any]) -> None:
    """Asserts that schedules are added and returned as expected."""
    post_response = client.post("/trains", json=train)
    assert post_response.status_code == 201
    response = client.get(f"/trains/{train['id']}")
    assert response.json() == sorted(train["schedule"])


def test_add_train_validates_id() -> None:
    """Test that invalid train IDs are rejected."""
    # Empty ID
    response = client.post("/trains", json={"id": "", "schedule": [100]})
    assert response.status_code == 422

    # Numbers not allowed
    response = client.post("/trains", json={"id": "ABC123", "schedule": [100]})
    assert response.status_code == 422

    # Too long
    response = client.post("/trains", json={"id": "TOOLONG", "schedule": [100]})
    assert response.status_code == 422


def test_add_train_validates_schedule() -> None:
    """Test that invalid schedule times are rejected."""
    # Negative time
    response = client.post("/trains", json={"id": "TEST", "schedule": [-1]})
    assert response.status_code == 422

    # Time >= 1440
    response = client.post("/trains", json={"id": "TEST", "schedule": [1440]})
    assert response.status_code == 422


def test_add_empty_schedule_rejected() -> None:
    """Test that empty schedules are rejected."""
    response = client.post("/trains", json={"id": "TEST", "schedule": []})
    assert response.status_code == 422


def test_update_schedule_removes_from_time_index() -> None:
    """Test that updating a schedule removes the train from old time slots."""
    # Create two trains that overlap at 100
    client.post("/trains", json={"id": "ALPHA", "schedule": [100, 200]})
    client.post("/trains", json={"id": "BETA", "schedule": [100, 300]})

    # Verify they overlap at 100
    response = client.get("/trains/next")
    assert response.json()["time"] == 100
    assert sorted(response.json()["trains"]) == ["ALPHA", "BETA"]

    # Update ALPHA to no longer arrive at 100
    client.post("/trains", json={"id": "ALPHA", "schedule": [200, 400]})

    # Now there should be no overlap (BETA is alone at 100 and 300)
    response = client.get("/trains/next")
    assert response.json()["time"] is None


# GET /trains/{train_id} - Get Train Schedule


def test_get_schedule_not_found() -> None:
    """Test 404 when train doesn't exist."""
    response = client.get("/trains/NOPE")
    assert response.status_code == 404


def test_get_schedule_validates_train_id() -> None:
    """Test 422 when train_id path parameter is invalid."""
    response = client.get("/trains/ABC123")
    assert response.status_code == 422


def test_train_id_canonicalized_to_uppercase() -> None:
    """Train IDs should be normalized to uppercase on write/read."""
    post_response = client.post("/trains", json={"id": "alpha", "schedule": [60, 120]})
    assert post_response.status_code == 201
    assert post_response.json()["id"] == "ALPHA"

    get_response = client.get("/trains/alpha")
    assert get_response.status_code == 200
    assert get_response.json() == [60, 120]


# GET /trains/next - Find Simultaneous Arrivals


def test_next() -> None:
    """Test /trains/next finds simultaneous arrivals."""
    client.post("/trains", json={"id": "TOMO", "schedule": [180, 640]})
    client.post("/trains", json={"id": "FOMO", "schedule": [440, 640]})

    response = client.get("/trains/next")
    assert response.status_code == 200
    data = response.json()
    assert data["time"] == 640
    assert sorted(data["trains"]) == ["FOMO", "TOMO"]


def test_next_no_overlap() -> None:
    """Test /trains/next when trains never overlap."""
    client.post("/trains", json={"id": "ALPHA", "schedule": [100, 200]})
    client.post("/trains", json={"id": "BETA", "schedule": [300, 400]})

    response = client.get("/trains/next")
    data = response.json()
    assert data["time"] is None
    assert data["trains"] == []


def test_next_wrap_around() -> None:
    """Test /trains/next wraps around when no more times today."""
    client.post("/trains", json={"id": "ALPHA", "schedule": [100, 500]})
    client.post("/trains", json={"id": "BETA", "schedule": [100, 500]})

    # Ask for next after last overlap - should wrap to first
    response = client.get("/trains/next?after=500")
    data = response.json()
    assert data["time"] == 100


def test_next_min_trains() -> None:
    """Test /trains/next with custom min_trains threshold."""
    client.post("/trains", json={"id": "ALPHA", "schedule": [100, 200]})
    client.post("/trains", json={"id": "BETA", "schedule": [100, 200]})
    client.post("/trains", json={"id": "GAMMA", "schedule": [200]})

    # Default min_trains=2: first overlap at 100
    response = client.get("/trains/next")
    assert response.json()["time"] == 100

    # min_trains=3: only 200 has 3 trains
    response = client.get("/trains/next?min_trains=3")
    data = response.json()
    assert data["time"] == 200
    assert sorted(data["trains"]) == ["ALPHA", "BETA", "GAMMA"]


def test_concurrent_updates_and_next_queries() -> None:
    """Concurrent writes and reads should not raise and should remain valid."""
    errors: list[Exception] = []

    def writer(train_id: str) -> None:
        try:
            for i in range(100):
                train_service.upsert_schedule(train_id, [i % 1440, (i + 300) % 1440])
        except Exception as e:
            errors.append(e)

    def reader() -> None:
        try:
            for _ in range(200):
                result = train_service.find_next_simultaneous(after=0, min_trains=2)
                assert "time" in result
                assert "trains" in result
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=writer, args=("ALPHA",)),
        threading.Thread(target=writer, args=("BETA",)),
        threading.Thread(target=reader),
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
