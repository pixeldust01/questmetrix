import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date


@pytest.fixture
def mock_event_queue():
    """Prevents tests from writing to the actual Redis Stream."""
    with patch("event_queue.publish_event"):
        yield


@pytest.fixture
def mock_analytics_data():
    # Patch where it's USED (analytics), not DEFINED (database)
    with patch("analytics.get_db_connection") as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_cursor.fetchall.return_value = [
            (1, 2, 2, 100.0, 0, 0, 0.0, 450.0),
            (2, 2, 2, 100.0, 1, 1, 0.5, 600.0),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn

        yield mock_cursor


@pytest.fixture
def session_test_data():
    with patch("analytics.get_db_connection") as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (
                "session_test_player",
                "pytest_session_game",
                1,
                datetime.fromisoformat("2026-09-01T10:00:00"),
                datetime.fromisoformat("2026-09-01T10:20:00"),
                3,
            ),
            (
                "session_test_player",
                "pytest_session_game",
                2,
                datetime.fromisoformat("2026-09-01T11:00:00"),
                datetime.fromisoformat("2026-09-01T11:05:00"),
                2,
            ),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn

        yield mock_cursor


@pytest.fixture
def retention_test_data():
    with patch("analytics.get_db_connection") as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (date(2026, 9, 1), 4, 2, 50.0),
            (date(2026, 9, 2), 2, 0, 0.0),
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn

        yield mock_cursor