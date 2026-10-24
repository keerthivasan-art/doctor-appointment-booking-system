"""Create (or reset) an administrator account.  Usage:  python create_admin.py"""
import getpass

import mysql.connector
from werkzeug.security import generate_password_hash

from config import Config


def main():
    username = input("Admin username: ").strip()
    password = getpass.getpass("Admin password (min 8 characters): ")
    if not username or len(password) < 8:
        raise SystemExit("Username required and password must be at least 8 characters.")
    conn = mysql.connector.connect(
        host=Config.DB_HOST, port=Config.DB_PORT, user=Config.DB_USER,
        password=Config.DB_PASSWORD, database=Config.DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO admins (username, password_hash) VALUES (%s, %s) "
        "ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash)",
        (username, generate_password_hash(password)))
    conn.commit()
    conn.close()
    print(f"Admin '{username}' saved.")


if __name__ == "__main__":
    main()
