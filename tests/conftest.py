"""Test setup: builds a separate test database from database/schema.sql.

Requires a running MySQL server and the DB_* settings in your .env file.
The test database (TEST_DB_NAME, default doctor_appointment_test) is dropped and
re-created on every run, so your real data is never touched.
"""
import os
import pathlib
import re

import mysql.connector
import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from config import Config

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEST_DB = os.environ.get("TEST_DB_NAME", "doctor_appointment_test")


def _run_script(cursor, path):
    sql = path.read_text(encoding="utf-8").replace("doctor_appointment_db", TEST_DB)
    sql = re.sub(r"--[^\n]*", "", sql)          # strip comments
    for statement in sql.split(";"):
        if statement.strip():
            cursor.execute(statement)


@pytest.fixture(scope="session")
def _database():
    conn = mysql.connector.connect(host=Config.DB_HOST, port=Config.DB_PORT,
                                   user=Config.DB_USER, password=Config.DB_PASSWORD)
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}")
    _run_script(cur, ROOT / "database" / "schema.sql")
    _run_script(cur, ROOT / "database" / "sample_data.sql")
    cur.execute(f"USE {TEST_DB}")
    cur.execute("INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
                ("testadmin", generate_password_hash("correct-horse-battery")))
    conn.commit()
    yield
    cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB}")
    conn.close()


@pytest.fixture()
def app(_database):
    app = create_app({"TESTING": True, "SECRET_KEY": "test-secret",
                      "DB_NAME": TEST_DB, "WTF_CSRF_ENABLED": False})
    yield app
    # clean appointments between tests
    conn = mysql.connector.connect(host=Config.DB_HOST, port=Config.DB_PORT,
                                   user=Config.DB_USER, password=Config.DB_PASSWORD,
                                   database=TEST_DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM appointments")
    conn.commit()
    conn.close()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_client(app):
    c = app.test_client()
    c.post("/admin/login", data={"username": "testadmin", "password": "correct-horse-battery"})
    return c
