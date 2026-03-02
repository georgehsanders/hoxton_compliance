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
            "shared_drive_path": request.form.get("shared_drive_path", "").strip(),
            "archive_retention_days": int(request.form.get("archive_retention_days", 7)),
            "publish_interval_minutes": int(request.form.get("publish_interval_minutes", 5)),
            "pause_reports": "pause_reports" in request.form,
            "last_midnight_run": old_settings.get("last_midnight_run"),
        }

        save_settings(conn, new_settings)
        log_audit(conn, "Settings", 1, "UPDATE", "Updated application settings",
                  old_values=old_settings, new_values=new_settings)
        flash("Settings saved successfully.", "success")
        return redirect(url_for("settings.index"))

    settings = get_settings(conn)
    return render_template("settings.html", settings=settings)
