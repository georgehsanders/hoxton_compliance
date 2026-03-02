"""Group dashboard routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from app import get_db
from app.models import create_group, log_audit
from app.compliance import compute_group_dashboard

bp = Blueprint("groups", __name__, url_prefix="/groups")


@bp.route("/")
def dashboard():
    conn = get_db()
    group_data = compute_group_dashboard(conn)
    return render_template("groups/dashboard.html", groups=group_data)


@bp.route("/add", methods=["POST"])
def add():
    conn = get_db()
    name = request.form.get("name", "").strip()
    if not name:
        flash("Group name is required.", "error")
        return redirect(url_for("groups.dashboard"))

    try:
        gid = create_group(conn, name)
        log_audit(conn, "Group", gid, "CREATE", f"Created group '{name}'",
                  new_values={"name": name})
        flash(f"Group '{name}' created.", "success")
    except Exception as e:
        flash(f"Error creating group: {e}", "error")

    return redirect(url_for("groups.dashboard"))
