"""Application configuration. All secrets come from environment variables."""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", "3306"))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "doctor_appointment_db")

    # Session / cookie hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    WTF_CSRF_TIME_LIMIT = 7200  # seconds

    # Clinic rules (fixed daily slots shared by all doctors)
    CLINIC_SLOTS = ["09:00", "10:00", "11:00", "12:00",
                    "14:00", "15:00", "16:00", "17:00"]
    MAX_BOOKING_DAYS_AHEAD = 60
