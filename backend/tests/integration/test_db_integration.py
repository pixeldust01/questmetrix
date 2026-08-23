import pytest
from database import get_db_connection

# These tests assume Docker Compose is running locally
def test_postgres_connection_and_query():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1") # Real DB call
    assert cursor.fetchone()[0] == 1
    cursor.close()
    conn.close()