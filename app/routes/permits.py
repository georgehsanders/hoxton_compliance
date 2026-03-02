"""Permit directory routes."""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from app import get_db
from app.models import (
    get_all_permit_types, get_permit_type, create_permit_type,
    get_employees_by_permit_type, log_audit,
)
from app.compliance import compute_permit_status, get_settings

bp = Blueprint("permits", __name__, url_prefix="/permits")


@bp.route("/")
def directory():
    conn = get_db()
    settings = get_settings(conn)
    threshold = settings.get("upcoming_threshold_days", 60)
    permit_types = get_all_permit_types(conn)

    pt_data = []
    for pt in permit_types:
        employees = get_employees_by_permit_type(conn, pt["id"])
        emp_list = []
        for e in employees:
            ed = dict(e)
            ed["status"] = compute_permit_status(e["latest_expiration"], threshold)
            ed["full_name"] = f"{e['first_name']} {e['last_name']}"
            emp_list.append(ed)
        # Sort: expired first, then upcoming, then active
        status_order = {"EXPIRED": 0, "UPCOMING_TODAY": 1, "UPCOMING": 2, "ACTIVE": 3, "NO_RENEWAL": 4}
        emp_list.sort(key=lambda x: (status_order.get(x["status"], 5), x["full_name"]))
        pt_data.append({"permit_type": dict(pt), "employees": emp_list})

    return render_template("permits/directory.html", permit_types=pt_data)


@bp.route("/add", methods=["POST"])
def add():
    conn = get_db()
    name = request.form.get("name", "").strip()
    issuing_authority = request.form.get("issuing_authority", "").strip()
    renewal_url = request.form.get("renewal_url", "").strip()
    duration_string = request.form.get("duration_string", "").strip() or None

    if not name:
        flash("Permit type name is required.", "error")
        return redirect(url_for("permits.directory"))

    try:
        pt_id = create_permit_type(conn, name, issuing_authority, renewal_url, duration_string)
        log_audit(conn, "PermitType", pt_id, "CREATE",
                  f"Created permit type '{name}'",
                  new_values={"name": name, "issuing_authority": issuing_authority})
        flash(f"Permit type '{name}' created.", "success")
    except Exception as e:
        flash(f"Error creating permit type: {e}", "error")

    return redirect(url_for("permits.directory"))
