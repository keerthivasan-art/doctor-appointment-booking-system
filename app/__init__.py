"""Flask application factory."""
import logging

import mysql.connector
from flask import Flask, render_template
from flask_wtf.csrf import CSRFError, CSRFProtect

from config import Config

csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY is not set. Copy .env.example to .env and set SECRET_KEY.")

    csrf.init_app(app)

    from . import models
    models.init_app(app)

    from .routes import bp as public_bp
    from .admin import bp as admin_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.template_filter("apt_code")
    def apt_code(appointment_id):
        return f"APT-{int(appointment_id):05d}"

    @app.template_filter("pretty_date")
    def pretty_date(value):
        return value.strftime("%d %b %Y") if value else ""

    @app.template_filter("pretty_time")
    def pretty_time(value):
        # value is "HH:MM" text coming from TIME_FORMAT in SQL
        hour, minute = map(int, str(value).split(":")[:2])
        suffix = "AM" if hour < 12 else "PM"
        return f"{(hour % 12) or 12}:{minute:02d} {suffix}"

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("404.html"), 404

    @app.errorhandler(CSRFError)
    def csrf_error(_e):
        return render_template(
            "500.html", title="Session expired",
            message="Your form session expired or was invalid. Please go back, refresh the page and try again."), 400

    @app.errorhandler(mysql.connector.Error)
    def db_error(e):
        # Log the real error on the server; show a safe message to the user.
        app.logger.error("Database error: %s", e)
        return render_template("500.html"), 500

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("500.html"), 500

    logging.basicConfig(level=logging.INFO)
    return app
