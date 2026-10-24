"""Public (patient-facing) routes."""
from datetime import date

from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, session, url_for)

from . import models
from .services.validation import parse_appointment_id, validate_booking

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html", stats=models.get_stats())


@bp.route("/about")
def about():
    return render_template("about.html")


@bp.route("/doctors")
def doctors():
    search = request.args.get("q", "").strip()[:100]
    spec = request.args.get("specialization", "").strip()[:80]
    return render_template(
        "doctors.html", doctors=models.list_doctors(search, spec),
        specializations=models.list_specializations(), q=search, selected_spec=spec)


@bp.route("/api/slots")
def api_slots():
    """JSON list of free slots for a doctor on a date (used by main.js)."""
    doctor_id = request.args.get("doctor_id", "")
    date_str = request.args.get("date", "")
    try:
        d = date.fromisoformat(date_str)
    except ValueError:
        return jsonify(error="Invalid date"), 400
    if not doctor_id.isdigit() or models.get_doctor(int(doctor_id)) is None:
        return jsonify(error="Unknown doctor"), 404
    taken = models.booked_times(int(doctor_id), d.isoformat())
    slots = [{"time": t, "available": t not in taken}
             for t in current_app.config["CLINIC_SLOTS"]]
    return jsonify(slots=slots)


@bp.route("/book", methods=["GET", "POST"])
def book():
    cfg = current_app.config
    doctors_list = models.list_doctors()
    form = request.form if request.method == "POST" else request.args
    if request.method == "POST":
        clean, errors = validate_booking(form, cfg)
        if not errors:
            try:
                new_id = models.create_appointment(
                    clean["doctor_id"], clean["patient_name"], clean["patient_email"],
                    clean["patient_phone"], clean["appointment_date"].isoformat(),
                    clean["appointment_time"], clean["reason"])
            except models.DoctorUnavailableError:
                errors.append("The selected doctor is not available for booking.")
            except models.SlotTakenError:
                errors.append("Sorry, that time slot was just taken. Please choose another slot.")
            else:
                session["last_appointment_id"] = new_id  # allows viewing confirmation
                return redirect(url_for("main.confirmation", appointment_id=new_id))
        for message in errors:
            flash(message, "error")
        return render_template("book_appointment.html", doctors=doctors_list,
                               form=form, slots=cfg["CLINIC_SLOTS"],
                               today=date.today().isoformat()), 400
    return render_template("book_appointment.html", doctors=doctors_list, form=form,
                           slots=cfg["CLINIC_SLOTS"], today=date.today().isoformat())


@bp.route("/confirmation/<int:appointment_id>")
def confirmation(appointment_id):
    # Only the browser session that just made the booking may see the confirmation.
    if session.get("last_appointment_id") != appointment_id:
        flash("Use 'Find my appointment' with your appointment ID and email to view a booking.", "error")
        return redirect(url_for("main.appointments"))
    appt = models.get_appointment(appointment_id)
    if appt is None:
        return render_template("404.html"), 404
    return render_template("confirmation.html", appt=appt)


@bp.route("/appointments", methods=["GET", "POST"])
def appointments():
    """Look up an appointment by ID + booking email."""
    if request.method == "POST":
        appt_id = parse_appointment_id(request.form.get("appointment_id"))
        email = (request.form.get("email") or "").strip().lower()
        appt = models.find_appointment(appt_id, email) if appt_id and email else None
        if appt is None:
            flash("No appointment found for that ID and email.", "error")
            return render_template("appointments.html",
                                   appointment_id=request.form.get("appointment_id", "")), 404
        return render_template("appointment_details.html", appt=appt)
    return render_template("appointments.html", appointment_id="")


@bp.route("/appointments/cancel", methods=["POST"])
def cancel():
    appt_id = parse_appointment_id(request.form.get("appointment_id"))
    email = (request.form.get("email") or "").strip().lower()
    appt = models.find_appointment(appt_id, email) if appt_id and email else None
    if appt is None:
        flash("Cancellation failed: appointment ID and email do not match.", "error")
        return render_template("appointments.html",
                               appointment_id=request.form.get("appointment_id", "")), 404
    if appt["status"] != "Booked":
        flash(f"This appointment is already {appt['status'].lower()} and cannot be cancelled.", "error")
        return render_template("appointment_details.html", appt=appt), 409
    if models.cancel_appointment(appt_id):
        flash("Your appointment has been cancelled.", "success")
    else:
        flash("The appointment could not be cancelled. Please try again.", "error")
    return render_template("appointment_details.html", appt=models.get_appointment(appt_id))
