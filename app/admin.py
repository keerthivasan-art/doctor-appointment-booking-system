"""Administrator module: login, doctor management, appointment management."""
from functools import wraps

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash

from . import models
from .services.validation import parse_appointment_id, validate_doctor

bp = Blueprint("admin", __name__)


def admin_required(view):
    """Server-side authorization: every admin route is wrapped with this."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please log in as administrator.", "error")
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        admin = models.get_admin_by_username(username)
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()  # prevents session fixation
            session["admin_id"] = admin["admin_id"]
            session["admin_name"] = admin["username"]
            return redirect(url_for("admin.dashboard"))
        flash("Invalid username or password.", "error")
        return render_template("admin/login.html"), 401
    return render_template("admin/login.html")


@bp.route("/logout", methods=["POST"])
@admin_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("admin.login"))


@bp.route("/")
@admin_required
def dashboard():
    appt_id = parse_appointment_id(request.args.get("appointment_id"))
    status = request.args.get("status", "")
    if status not in ("Booked", "Completed", "Cancelled"):
        status = ""
    date_str = request.args.get("date", "")
    rows = models.search_appointments(appt_id, status, date_str or None)
    return render_template("admin/dashboard.html", appointments=rows,
                           f_id=request.args.get("appointment_id", ""),
                           f_status=status, f_date=date_str)


@bp.route("/appointments/<int:appointment_id>/status", methods=["POST"])
@admin_required
def set_status(appointment_id):
    new_status = request.form.get("status")
    if new_status not in ("Completed", "Cancelled"):
        flash("Invalid status.", "error")
    elif models.update_appointment_status(appointment_id, new_status):
        flash(f"Appointment marked {new_status}.", "success")
    else:
        flash("Only appointments with status 'Booked' can be changed.", "error")
    return redirect(url_for("admin.dashboard"))


@bp.route("/doctors")
@admin_required
def doctors():
    return render_template("admin/doctors.html",
                           doctors=models.list_doctors(include_inactive=True))


@bp.route("/doctors/new", methods=["GET", "POST"])
@admin_required
def doctor_new():
    if request.method == "POST":
        clean, errors = validate_doctor(request.form)
        if not errors:
            models.add_doctor(clean["name"], clean["specialization"],
                              clean["qualification"], clean["consultation_fee"])
            flash("Doctor added.", "success")
            return redirect(url_for("admin.doctors"))
        for e in errors:
            flash(e, "error")
        return render_template("admin/doctor_form.html", doctor=request.form, editing=False), 400
    return render_template("admin/doctor_form.html", doctor={}, editing=False)


@bp.route("/doctors/<int:doctor_id>/edit", methods=["GET", "POST"])
@admin_required
def doctor_edit(doctor_id):
    doctor = models.get_doctor(doctor_id)
    if doctor is None:
        return render_template("404.html"), 404
    if request.method == "POST":
        clean, errors = validate_doctor(request.form)
        if not errors:
            models.update_doctor(doctor_id, clean["name"], clean["specialization"],
                                 clean["qualification"], clean["consultation_fee"])
            flash("Doctor updated.", "success")
            return redirect(url_for("admin.doctors"))
        for e in errors:
            flash(e, "error")
        return render_template("admin/doctor_form.html", doctor=request.form,
                               editing=True, doctor_id=doctor_id), 400
    return render_template("admin/doctor_form.html", doctor=doctor,
                           editing=True, doctor_id=doctor_id)


@bp.route("/doctors/<int:doctor_id>/toggle", methods=["POST"])
@admin_required
def doctor_toggle(doctor_id):
    doctor = models.get_doctor(doctor_id)
    if doctor is None:
        return render_template("404.html"), 404
    models.set_doctor_active(doctor_id, not doctor["is_active"])
    flash("Doctor " + ("deactivated." if doctor["is_active"] else "activated."), "success")
    return redirect(url_for("admin.doctors"))
