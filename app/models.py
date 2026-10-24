"""All database access. Every query is parameterized (%s placeholders)."""
import mysql.connector
from flask import current_app, g
from mysql.connector import errorcode


class SlotTakenError(Exception):
    """Another active appointment already uses this doctor/date/time."""


class DoctorUnavailableError(Exception):
    """Doctor does not exist or is not active."""


def get_db():
    if "db" not in g:
        cfg = current_app.config
        g.db = mysql.connector.connect(
            host=cfg["DB_HOST"], port=cfg["DB_PORT"], user=cfg["DB_USER"],
            password=cfg["DB_PASSWORD"], database=cfg["DB_NAME"],
            autocommit=True, connection_timeout=5)
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)


def _query(sql, params=(), one=False):
    cur = get_db().cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        return cur.fetchone() if one else cur.fetchall()
    finally:
        cur.close()


def _execute(sql, params=()):
    cur = get_db().cursor()
    try:
        cur.execute(sql, params)
        return cur.rowcount, cur.lastrowid
    finally:
        cur.close()


# ----------------------------------------------------------- doctors (read)
def get_stats():
    return _query(
        """SELECT
             (SELECT COUNT(*) FROM doctors WHERE is_active = 1)            AS active_doctors,
             (SELECT COUNT(DISTINCT specialization) FROM doctors
                WHERE is_active = 1)                                       AS specializations,
             (SELECT COUNT(*) FROM appointments)                           AS total_appointments,
             (SELECT COUNT(*) FROM appointments
                WHERE status = 'Booked' AND appointment_date >= CURDATE()) AS upcoming""",
        one=True)


def list_doctors(search="", specialization="", include_inactive=False):
    sql = "SELECT * FROM doctors WHERE 1=1"
    params = []
    if not include_inactive:
        sql += " AND is_active = 1"
    if search:
        sql += " AND name LIKE %s"
        params.append(f"%{search}%")
    if specialization:
        sql += " AND specialization = %s"
        params.append(specialization)
    sql += " ORDER BY name"
    return _query(sql, params)


def list_specializations():
    rows = _query("SELECT DISTINCT specialization FROM doctors WHERE is_active = 1 "
                  "ORDER BY specialization")
    return [r["specialization"] for r in rows]


def get_doctor(doctor_id):
    return _query("SELECT * FROM doctors WHERE doctor_id = %s", (doctor_id,), one=True)


# --------------------------------------------------------- doctors (admin)
def add_doctor(name, specialization, qualification, fee):
    _, new_id = _execute(
        "INSERT INTO doctors (name, specialization, qualification, consultation_fee) "
        "VALUES (%s, %s, %s, %s)", (name, specialization, qualification, fee))
    return new_id


def update_doctor(doctor_id, name, specialization, qualification, fee):
    _execute(
        "UPDATE doctors SET name=%s, specialization=%s, qualification=%s, "
        "consultation_fee=%s WHERE doctor_id=%s",
        (name, specialization, qualification, fee, doctor_id))


def set_doctor_active(doctor_id, active):
    count, _ = _execute("UPDATE doctors SET is_active=%s WHERE doctor_id=%s",
                        (1 if active else 0, doctor_id))
    return count


# ------------------------------------------------------------ appointments
def booked_times(doctor_id, date_str):
    """Times ('HH:MM') already taken by active appointments for a doctor/date."""
    rows = _query(
        "SELECT LEFT(CAST(appointment_time AS CHAR), 5) AS t FROM appointments "
        "WHERE doctor_id=%s AND appointment_date=%s AND status <> 'Cancelled'",
        (doctor_id, date_str))
    return {r["t"] for r in rows}


_APPT_SELECT = """
    SELECT a.appointment_id, a.doctor_id, a.patient_name, a.patient_email,
           a.patient_phone, a.appointment_date,
           LEFT(CAST(a.appointment_time AS CHAR), 5) AS appointment_time,
           a.reason, a.status, a.created_at,
           d.name AS doctor_name, d.specialization, d.consultation_fee
    FROM appointments a JOIN doctors d ON d.doctor_id = a.doctor_id
"""


def create_appointment(doctor_id, name, email, phone, date_str, time_str, reason):
    """Insert inside a transaction. Returns the new appointment_id.

    The UNIQUE index uq_active_slot is the final guard against double booking,
    even if two patients submit at the same instant.
    """
    db = get_db()
    cur = db.cursor()
    try:
        db.start_transaction()
        cur.execute("SELECT doctor_id FROM doctors WHERE doctor_id=%s AND is_active=1 "
                    "FOR UPDATE", (doctor_id,))
        if cur.fetchone() is None:
            db.rollback()
            raise DoctorUnavailableError()
        cur.execute(
            "INSERT INTO appointments (doctor_id, patient_name, patient_email, "
            "patient_phone, appointment_date, appointment_time, reason) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (doctor_id, name, email, phone, date_str, time_str, reason))
        new_id = cur.lastrowid
        db.commit()
        return new_id
    except mysql.connector.IntegrityError as exc:
        db.rollback()
        if exc.errno == errorcode.ER_DUP_ENTRY:
            raise SlotTakenError() from exc
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def get_appointment(appointment_id):
    return _query(_APPT_SELECT + " WHERE a.appointment_id = %s", (appointment_id,), one=True)


def find_appointment(appointment_id, email):
    """Return the appointment only if BOTH id and email match."""
    return _query(
        _APPT_SELECT + " WHERE a.appointment_id = %s AND a.patient_email = %s",
        (appointment_id, email), one=True)


def cancel_appointment(appointment_id):
    """Logical cancellation (history is kept). Only 'Booked' can be cancelled."""
    count, _ = _execute(
        "UPDATE appointments SET status='Cancelled' "
        "WHERE appointment_id=%s AND status='Booked'", (appointment_id,))
    return count == 1


def search_appointments(appointment_id=None, status="", date_str=""):
    sql = _APPT_SELECT + " WHERE 1=1"
    params = []
    if appointment_id:
        sql += " AND a.appointment_id = %s"
        params.append(appointment_id)
    if status:
        sql += " AND a.status = %s"
        params.append(status)
    if date_str:
        sql += " AND a.appointment_date = %s"
        params.append(date_str)
    sql += " ORDER BY a.appointment_date DESC, a.appointment_time DESC LIMIT 200"
    return _query(sql, params)


def update_appointment_status(appointment_id, new_status):
    """Admin: Booked -> Completed/Cancelled only."""
    count, _ = _execute(
        "UPDATE appointments SET status=%s WHERE appointment_id=%s AND status='Booked'",
        (new_status, appointment_id))
    return count == 1


# ------------------------------------------------------------------ admins
def get_admin_by_username(username):
    return _query("SELECT * FROM admins WHERE username=%s", (username,), one=True)
