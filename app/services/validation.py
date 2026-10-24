"""Server-side validation. Never trust the browser."""
import re
from datetime import date, datetime, timedelta

NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'\-]{1,99}$")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^[6-9][0-9]{9}$")


def normalize_phone(raw):
    digits = re.sub(r"[\s\-()]", "", raw or "")
    if digits.startswith("+91"):
        digits = digits[3:]
    return digits


def parse_appointment_id(raw):
    """Accept '12' or 'APT-00012'. Returns int or None."""
    raw = (raw or "").strip().upper()
    if raw.startswith("APT-"):
        raw = raw[4:]
    return int(raw) if raw.isdigit() and 0 < int(raw) < 2**31 else None


def validate_booking(form, config, today=None, now=None):
    """Return (clean_dict, errors_list)."""
    errors = []
    today = today or date.today()
    now = now or datetime.now()

    name = (form.get("patient_name") or "").strip()
    email = (form.get("patient_email") or "").strip().lower()
    phone = normalize_phone(form.get("patient_phone"))
    doctor_raw = (form.get("doctor_id") or "").strip()
    date_raw = (form.get("appointment_date") or "").strip()
    time_raw = (form.get("appointment_time") or "").strip()
    reason = (form.get("reason") or "").strip()

    if not name:
        errors.append("Patient name is required.")
    elif not NAME_RE.match(name):
        errors.append("Patient name may contain only letters, spaces, . ' and - (2-100 characters).")

    if not email:
        errors.append("Email address is required.")
    elif len(email) > 120 or not EMAIL_RE.match(email):
        errors.append("Please enter a valid email address.")

    if not phone:
        errors.append("Phone number is required.")
    elif not PHONE_RE.match(phone):
        errors.append("Phone number must be a valid 10-digit Indian mobile number.")

    doctor_id = int(doctor_raw) if doctor_raw.isdigit() and 0 < int(doctor_raw) < 2**31 else None
    if doctor_id is None:
        errors.append("Please select a doctor.")

    appt_date = None
    if not date_raw:
        errors.append("Appointment date is required.")
    else:
        try:
            appt_date = datetime.strptime(date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Appointment date is not a valid date.")
    if appt_date is not None:
        if appt_date < today:
            errors.append("Appointment date cannot be in the past.")
        elif appt_date > today + timedelta(days=config["MAX_BOOKING_DAYS_AHEAD"]):
            errors.append(f"Appointments can be booked up to {config['MAX_BOOKING_DAYS_AHEAD']} days ahead.")

    if not time_raw:
        errors.append("Please choose a time slot.")
    elif time_raw not in config["CLINIC_SLOTS"]:
        errors.append("The selected time slot is not valid.")
    elif appt_date == today:
        hour, minute = map(int, time_raw.split(":"))
        if (hour, minute) <= (now.hour, now.minute):
            errors.append("That time slot has already passed today.")

    if not reason:
        errors.append("Reason for consultation is required.")
    elif not 5 <= len(reason) <= 500:
        errors.append("Reason must be between 5 and 500 characters.")

    clean = dict(patient_name=name, patient_email=email, patient_phone=phone,
                 doctor_id=doctor_id, appointment_date=appt_date,
                 appointment_time=time_raw, reason=reason)
    return clean, errors


def validate_doctor(form):
    errors = []
    name = (form.get("name") or "").strip()
    spec = (form.get("specialization") or "").strip()
    qual = (form.get("qualification") or "").strip()
    fee_raw = (form.get("consultation_fee") or "").strip()
    if not 3 <= len(name) <= 100:
        errors.append("Doctor name must be 3-100 characters.")
    if not 2 <= len(spec) <= 80:
        errors.append("Specialization must be 2-80 characters.")
    if not 2 <= len(qual) <= 120:
        errors.append("Qualification must be 2-120 characters.")
    fee = None
    try:
        fee = round(float(fee_raw), 2)
        if not 0 <= fee <= 100000:
            raise ValueError
    except ValueError:
        errors.append("Consultation fee must be a number between 0 and 100000.")
    return dict(name=name, specialization=spec, qualification=qual, consultation_fee=fee), errors
