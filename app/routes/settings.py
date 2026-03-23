"""Settings route."""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from app import get_db
from app.models import get_settings, save_settings, log_audit

bp = Blueprint("settings", __name__, url_prefix="/settings")


@bp.route("/", methods=["GET", "POST"])
def index():
    conn = get_db()

    if request.method == "POST":
        old_settings = get_settings(conn)

        new_settings = {
            "hotel_name": request.form.get("hotel_name", "Hotel").strip(),
            "upcoming_threshold_days": int(request.form.get("upcoming_threshold_days", 60)),
            "change_list_days": int(request.form.get("change_list_days", 1)),
            "default_recipient_emails": request.form.get("default_recipient_emails", "").strip(),
            "default_email_intro": request.form.get("default_email_intro", "").strip(),
            "last_midnight_run": old_settings.get("last_midnight_run"),
        }

        save_settings(conn, new_settings)
        log_audit(conn, "Settings", 1, "UPDATE", "Updated application settings",
                  old_values=old_settings, new_values=new_settings)
        flash("Settings saved successfully.", "success")
        return redirect(url_for("settings.index"))

    settings = get_settings(conn)
    return render_template("settings.html", settings=settings)
