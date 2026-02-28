"""Fixtures y datos compartidos para los tests."""
import pytest


SAMPLE_PAST_LAUNCH = {
    "id": "5eb87cd9ffd86e000604b32a",
    "name": "FalconSat",
    "date_utc": "2006-03-24T22:30:00.000Z",
    "rocket": "5e9d0d95aebc876801sdfsd",
    "launchpad": "5e9e4502f5090995de566f86",
    "flight_number": 1,
    "details": "Engine failure at T+33 seconds",
    "upcoming": False,
    "success": False,
    "links": {
        "patch": {"small": "https://example.com/small.png", "large": None},
        "webcast": "https://www.youtube.com/watch?v=0a_00nJ_Y88",
        "article": None,
        "wikipedia": "https://en.wikipedia.org/wiki/DemoSat",
    },
    "payloads": ["5eb0e4b5b6c3bb0006eeb1e1"],
}

SAMPLE_UPCOMING_LAUNCH = {
    "id": "620f9cbeceaec5672a107320",
    "name": "Starlink Group 4-20",
    "date_utc": "2026-05-01T00:00:00.000Z",
    "rocket": "5e9d0d95aebc876801sdfsd",
    "launchpad": "5e9e4502f5090995de566f86",
    "flight_number": 200,
    "details": None,
    "upcoming": True,
    "success": None,
    "links": {
        "patch": {"small": None, "large": None},
        "webcast": None,
        "article": None,
        "wikipedia": None,
    },
    "payloads": [],
}


@pytest.fixture
def past_launch():
    return SAMPLE_PAST_LAUNCH.copy()


@pytest.fixture
def upcoming_launch():
    return SAMPLE_UPCOMING_LAUNCH.copy()


@pytest.fixture
def sample_launches(past_launch, upcoming_launch):
    return [past_launch, upcoming_launch]
