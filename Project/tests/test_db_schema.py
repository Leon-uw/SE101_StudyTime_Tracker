# tests/test_db_schema.py
import os
import mysql.connector
import pytest

TEST_DB_HOST = os.getenv("GC_DB_HOST", "localhost")
TEST_DB_PORT = int(os.getenv("GC_DB_PORT", "3306"))
TEST_DB_USER = os.getenv("GC_DB_USER", "root")
TEST_DB_PASS = os.getenv("GC_DB_PASS", "")
TEST_DB_NAME = os.getenv("GC_TEST_DB_NAME", "gradecalc_test")
TEST_TABLE_NAME = os.getenv("GC_TABLE_NAME", "grades")

# default: keep the test DB (won't drop unless you set GC_DROP_TEST_DB=1)
DROP_TEST_DB = os.getenv("GC_DROP_TEST_DB", "0") == "1"

@pytest.fixture(scope="session")
def test_conn():
    admin = mysql.connector.connect(
        host=TEST_DB_HOST, port=TEST_DB_PORT, user=TEST_DB_USER, password=TEST_DB_PASS
    )
    admin.autocommit = True
    cur = admin.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {TEST_DB_NAME} DEFAULT CHARSET utf8mb4")
    cur.close()
    admin.close()

    conn = mysql.connector.connect(
        host=TEST_DB_HOST, port=TEST_DB_PORT, user=TEST_DB_USER, password=TEST_DB_PASS, database=TEST_DB_NAME
    )
    yield conn

    conn.close()
    if DROP_TEST_DB:
        admin2 = mysql.connector.connect(
            host=TEST_DB_HOST, port=TEST_DB_PORT, user=TEST_DB_USER, password=TEST_DB_PASS
        )
        admin2.autocommit = True
        c2 = admin2.cursor()
        c2.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
        c2.close()
        admin2.close()

def test_table_exists(test_conn, monkeypatch):
    # point src.db at our test DB
    monkeypatch.setenv("GC_DB_HOST", TEST_DB_HOST)
    monkeypatch.setenv("GC_DB_PORT", str(TEST_DB_PORT))
    monkeypatch.setenv("GC_DB_USER", TEST_DB_USER)
    monkeypatch.setenv("GC_DB_PASS", TEST_DB_PASS)
    monkeypatch.setenv("GC_DB_NAME", TEST_DB_NAME)
    monkeypatch.setenv("GC_TABLE_NAME", TEST_TABLE_NAME)

    from src import db
    db.init_db()

    cur = test_conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema=%s AND table_name=%s
    """, (TEST_DB_NAME, TEST_TABLE_NAME))
    (count,) = cur.fetchone()
    assert count == 1, f"Expected table {TEST_TABLE_NAME} in {TEST_DB_NAME}"

def test_required_columns_exist(test_conn):
    cur = test_conn.cursor()
    cur.execute(f"DESCRIBE {TEST_TABLE_NAME}")
    cols = {row[0] for row in cur.fetchall()}
    expected = {"id","course","time_spent","assignment_no","grade","weight","user_id"}
    missing = expected - cols
    assert not missing, f"Missing columns: {missing}"
