"""Automated tests (pytest). Run:  python -m pytest -v"""
import re
from datetime import date, timedelta

import mysql.connector

from app import models

FUTURE = (date.today() + timedelta(days=3)).isoformat()
PAST = (date.today() - timedelta(days=1)).isoformat()
EMAIL = "patient@example.com"


def payload(**over):
    data = dict(patient_name="Test Patient", patient_email=EMAIL, patient_phone="9876543210",
                doctor_id="1", appointment_date=FUTURE, appointment_time="10:00",
                reason="Regular health check-up")
    data.update(over)
    return data


def book(client, **over):
    return client.post("/book", data=payload(**over))


def book_ok(client, **over):
    resp = book(client, **over)
    assert resp.status_code == 302
    return int(re.search(r"/confirmation/(\d+)", resp.headers["Location"]).group(1))


# 1
def test_homepage_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200 and b"Book Appointment" in resp.data


# 2
def test_doctor_list_and_filters(client):
    resp = client.get("/doctors")
    assert b"Ananya Rao" in resp.data
    assert b"Vikram Shah" not in resp.data          # inactive doctor hidden
    assert b"Ananya Rao" not in client.get("/doctors?specialization=ENT").data
    assert b"Meera Iyer" in client.get("/doctors?q=meera").data


# 3 + 9
def test_valid_booking_and_retrieval(client):
    appt_id = book_ok(client, patient_name="Asha K")
    confirm = client.get(f"/confirmation/{appt_id}")
    assert confirm.status_code == 200 and f"APT-{appt_id:05d}".encode() in confirm.data
    found = client.post("/appointments", data={"appointment_id": f"APT-{appt_id:05d}", "email": EMAIL})
    assert found.status_code == 200 and b"Asha K" in found.data


def test_confirmation_requires_same_session(app):
    c1, c2 = app.test_client(), app.test_client()
    appt_id = book_ok(c1)
    assert c2.get(f"/confirmation/{appt_id}").status_code == 302


# 4
def test_missing_fields_rejected(client):
    resp = client.post("/book", data={})
    assert resp.status_code == 400 and b"required" in resp.data


# 4b
def test_invalid_phone_rejected(client):
    assert book(client, patient_phone="12345").status_code == 400


# 5
def test_invalid_email_rejected(client):
    assert book(client, patient_email="not-an-email").status_code == 400


# 6
def test_past_date_rejected(client):
    resp = book(client, appointment_date=PAST)
    assert resp.status_code == 400 and b"past" in resp.data


# 7
def test_unknown_and_inactive_doctor_handled(client):
    assert b"Please select a doctor" in book(client, doctor_id="abc").data
    assert b"not available" in book(client, doctor_id="9999").data
    assert b"not available" in book(client, doctor_id="8").data   # inactive sample doctor
    assert client.get("/api/slots?doctor_id=9999&date=" + FUTURE).status_code == 404


def test_sql_injection_text_is_harmless(client):
    book_ok(client, patient_name="Robert", reason="'); DROP TABLE appointments;--")
    assert client.get("/").status_code == 200


# 8
def test_duplicate_slot_prevented(client):
    book_ok(client)
    resp = book(client, patient_name="Someone Else", patient_email="other@example.com")
    assert resp.status_code == 400 and b"just taken" in resp.data


def test_database_unique_constraint_blocks_duplicates(app):
    with app.app_context():
        models.create_appointment(1, "A B", EMAIL, "9876543210", FUTURE, "11:00", "check up")
        try:
            models.create_appointment(1, "C D", "c@d.com", "9876543211", FUTURE, "11:00", "check up")
            assert False, "duplicate should have raised"
        except models.SlotTakenError:
            pass


def test_slot_api_marks_booked_slot(client):
    book_ok(client)
    slots = client.get(f"/api/slots?doctor_id=1&date={FUTURE}").get_json()["slots"]
    assert {s["time"]: s["available"] for s in slots}["10:00"] is False


# 10
def test_cancel_succeeds_and_slot_reusable(client):
    appt_id = book_ok(client)
    resp = client.post("/appointments/cancel", data={"appointment_id": str(appt_id), "email": EMAIL})
    assert resp.status_code == 200 and b"has been cancelled" in resp.data
    book_ok(client, patient_name="New Patient", patient_email="new@example.com")  # slot freed


# 11
def test_wrong_id_or_email_does_not_cancel(client, app):
    appt_id = book_ok(client)
    r1 = client.post("/appointments/cancel", data={"appointment_id": str(appt_id), "email": "wrong@example.com"})
    r2 = client.post("/appointments/cancel", data={"appointment_id": "99999", "email": EMAIL})
    assert r1.status_code == 404 and r2.status_code == 404
    with app.app_context():
        assert models.get_appointment(appt_id)["status"] == "Booked"


# 12
def test_cannot_cancel_twice(client):
    appt_id = book_ok(client)
    data = {"appointment_id": str(appt_id), "email": EMAIL}
    client.post("/appointments/cancel", data=data)
    again = client.post("/appointments/cancel", data=data)
    assert again.status_code == 409 and b"already cancelled" in again.data


# 13
def test_sql_error_does_not_leak_secrets(client, monkeypatch):
    def boom(*a, **k):
        raise mysql.connector.Error("Access denied for user 'root'@'localhost' password SECRETPW")
    monkeypatch.setattr(models, "get_stats", boom)
    resp = client.get("/")
    assert resp.status_code == 500
    assert b"SECRETPW" not in resp.data and b"Access denied" not in resp.data


def test_csrf_protection_enabled(app):
    app.config["WTF_CSRF_ENABLED"] = True
    resp = app.test_client().post("/book", data=payload())
    assert resp.status_code == 400


# 14
def test_admin_pages_require_login(client):
    for path in ["/admin/", "/admin/doctors", "/admin/doctors/new"]:
        assert client.get(path).status_code == 302
    assert client.post("/admin/doctors/1/toggle").status_code == 302
    assert client.post("/admin/appointments/1/status", data={"status": "Completed"}).status_code == 302


def test_admin_login_wrong_password(client):
    resp = client.post("/admin/login", data={"username": "testadmin", "password": "nope"})
    assert resp.status_code == 401


def test_admin_can_manage_doctors_and_appointments(admin_client, client):
    resp = admin_client.post("/admin/doctors/new", data=dict(
        name="Dr. Test Doctor", specialization="Oncology", qualification="MBBS, DM", consultation_fee="750"))
    assert resp.status_code == 302
    assert b"Test Doctor" in admin_client.get("/admin/doctors").data
    appt_id = book_ok(client)
    admin_client.post(f"/admin/appointments/{appt_id}/status", data={"status": "Completed"})
    assert b"Completed" in admin_client.get("/admin/?status=Completed").data
    again = admin_client.post(f"/admin/appointments/{appt_id}/status", data={"status": "Cancelled"}, follow_redirects=True)
    assert b"Only appointments" in again.data


def test_admin_can_deactivate_doctor(admin_client, client):
    admin_client.post("/admin/doctors/5/toggle")
    assert b"not available" in book(client, doctor_id="5").data
    admin_client.post("/admin/doctors/5/toggle")   # restore


def test_doctor_with_appointments_cannot_be_deleted(app):
    with app.app_context():
        models.create_appointment(2, "A B", EMAIL, "9876543210", FUTURE, "12:00", "check up")
        try:
            models._execute("DELETE FROM doctors WHERE doctor_id = 2")
            assert False, "FK RESTRICT should block this"
        except mysql.connector.IntegrityError:
            pass
