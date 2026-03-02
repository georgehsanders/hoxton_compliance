"""Employee routes — roster, profile, permit management."""

import json
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from app import get_db
from app.models import (
    get_all_employees, get_employee, create_employee, update_employee,
    archive_employee, get_all_groups, get_all_permit_types,
    get_employee_permits, get_permit_with_renewals,
    create_employee_permit, create_renewal, deactivate_permit, activate_permit,
    log_audit, get_permit_type,
)
from app.compliance import compute_permit_status, compute_employee_compliance, get_settings

bp = Blueprint("employees", __name__, url_prefix="/employees")


def _parse_duration_string(raw):
    """Normalize duration input: '6 months', '6m', '1 year', '1y' -> stored as-is for display."""
    if not raw or not raw.strip():
        return None
    return raw.strip()


@bp.route("/")
def roster():
    conn = get_db()
    settings = get_settings(conn)
    threshold = settings.get("upcoming_threshold_days", 60)
    employees = get_all_employees(conn, include_archived=False)

    employee_data = []
    for emp in employees:
        permits = get_employee_permits(conn, emp["id"], active_only=True)
        category, details = compute_employee_compliance(permits, threshold)
        emp_data = dict(emp)
        emp_data["compliance_category"] = category
        emp_data["compliance_details"] = details
        emp_data["full_name"] = f"{emp['first_name']} {emp['last_name']}"
        emp_data["permits"] = [dict(p) for p in permits]
        # Add status to each permit
        for p in emp_data["permits"]:
            p["status"] = compute_permit_status(p["latest_expiration"], threshold)
        employee_data.append(emp_data)

    return render_template("employees/roster.html", employees=employee_data)


@bp.route("/<int:emp_id>")
def profile(emp_id):
    conn = get_db()
    emp = get_employee(conn, emp_id)
    if not emp:
        abort(404)

    settings = get_settings(conn)
    threshold = settings.get("upcoming_threshold_days", 60)
    permits = get_employee_permits(conn, emp_id, active_only=False)
    groups = get_all_groups(conn)
    permit_types = get_all_permit_types(conn)
    category, details = compute_employee_compliance(
        [p for p in permits if p["active"]], threshold
    )

    permits_with_status = []
    for p in permits:
        pd = dict(p)
        if p["active"]:
            pd["status"] = compute_permit_status(p["latest_expiration"], threshold)
        else:
            pd["status"] = "INACTIVE"
        # Get renewal history
        _, renewals = get_permit_with_renewals(conn, p["id"])
        pd["renewals"] = [dict(r) for r in renewals]
        permits_with_status.append(pd)

    return render_template(
        "employees/profile.html",
        emp=dict(emp),
        permits=permits_with_status,
        groups=groups,
        permit_types=permit_types,
        compliance_category=category,
        compliance_details=details,
        threshold=threshold,
    )


@bp.route("/add", methods=["GET", "POST"])
def add():
    conn = get_db()
    groups = get_all_groups(conn)

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        group_id = request.form.get("group_id")
        role = request.form.get("role", "").strip()
        email = request.form.get("email", "").strip()
        employee_id_field = request.form.get("employee_id", "").strip()

        if not first_name or not last_name or not group_id:
            flash("First name, last name, and group are required.", "error")
            return render_template("employees/add.html", groups=groups)

        try:
            new_id = create_employee(
                conn, first_name, last_name, int(group_id),
                role=role, email=email, employee_id=employee_id_field or None,
            )
            log_audit(conn, "Employee", new_id, "CREATE",
                      f"Added employee {first_name} {last_name}",
                      new_values={"first_name": first_name, "last_name": last_name,
                                  "group_id": int(group_id), "role": role, "email": email})
            flash(f"Employee {first_name} {last_name} added successfully.", "success")
            return redirect(url_for("employees.profile", emp_id=new_id))
        except Exception as e:
            flash(f"Error adding employee: {e}", "error")

    return render_template("employees/add.html", groups=groups)


@bp.route("/<int:emp_id>/edit", methods=["POST"])
def edit(emp_id):
    conn = get_db()
    emp = get_employee(conn, emp_id)
    if not emp:
        abort(404)

    old_values = {
        "first_name": emp["first_name"], "last_name": emp["last_name"],
        "role": emp["role"], "email": emp["email"],
        "group_id": emp["group_id"], "employee_id": emp["employee_id"],
    }

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    group_id = request.form.get("group_id")
    role = request.form.get("role", "").strip()
    email = request.form.get("email", "").strip()
    employee_id_field = request.form.get("employee_id", "").strip()

    if not first_name or not last_name or not group_id:
        flash("First name, last name, and group are required.", "error")
        return redirect(url_for("employees.profile", emp_id=emp_id))

    new_values = {
        "first_name": first_name, "last_name": last_name,
        "role": role, "email": email,
        "group_id": int(group_id), "employee_id": employee_id_field or None,
    }

    update_employee(conn, emp_id, **new_values)
    log_audit(conn, "Employee", emp_id, "UPDATE",
              f"Updated employee {first_name} {last_name}",
              old_values=old_values, new_values=new_values)
    flash("Employee updated successfully.", "success")
    return redirect(url_for("employees.profile", emp_id=emp_id))


@bp.route("/<int:emp_id>/archive", methods=["POST"])
def toggle_archive(emp_id):
    conn = get_db()
    emp = get_employee(conn, emp_id)
    if not emp:
        abort(404)

    new_archived = not emp["archived"]
    archive_employee(conn, emp_id, new_archived)
    action = "Archived" if new_archived else "Unarchived"
    log_audit(conn, "Employee", emp_id, "ARCHIVE",
              f"{action} employee {emp['first_name']} {emp['last_name']}",
              old_values={"archived": emp["archived"]},
              new_values={"archived": 1 if new_archived else 0})
    flash(f"{action} {emp['first_name']} {emp['last_name']}.", "success")
    return redirect(url_for("employees.profile", emp_id=emp_id))


@bp.route("/<int:emp_id>/permits/add", methods=["POST"])
def add_permit(emp_id):
    conn = get_db()
    emp = get_employee(conn, emp_id)
    if not emp:
        abort(404)

    permit_type_id = request.form.get("permit_type_id")
    custom_name = request.form.get("custom_name", "").strip()
    permit_number = request.form.get("permit_number", "").strip()
    issuing_authority = request.form.get("issuing_authority", "").strip()
    renewal_url = request.form.get("renewal_url", "").strip()

    if not permit_type_id and not custom_name:
        flash("Select a permit type or enter a custom name.", "error")
        return redirect(url_for("employees.profile", emp_id=emp_id))

    # Pre-fill from permit type defaults if selected
    if permit_type_id:
        pt = get_permit_type(conn, int(permit_type_id))
        if pt:
            if not issuing_authority:
                issuing_authority = pt["default_issuing_authority"]
            if not renewal_url:
                renewal_url = pt["default_renewal_url"]

    permit_id = create_employee_permit(
        conn, emp_id,
        permit_type_id=int(permit_type_id) if permit_type_id else None,
        custom_name=custom_name or None,
        permit_number=permit_number,
        issuing_authority=issuing_authority,
        renewal_url=renewal_url,
    )

    display_name = custom_name or (pt["name"] if permit_type_id and pt else "Unknown")
    log_audit(conn, "EmployeePermit", permit_id, "CREATE",
              f"Added permit '{display_name}' for {emp['first_name']} {emp['last_name']}",
              new_values={"permit_type_id": permit_type_id, "custom_name": custom_name,
                          "permit_number": permit_number})
    flash(f"Permit '{display_name}' added.", "success")
    return redirect(url_for("employees.profile", emp_id=emp_id))


@bp.route("/<int:emp_id>/permits/<int:permit_id>/renew", methods=["POST"])
def renew_permit(emp_id, permit_id):
    conn = get_db()
    emp = get_employee(conn, emp_id)
    if not emp:
        abort(404)

    permit, _ = get_permit_with_renewals(conn, permit_id)
    if not permit or permit["employee_id"] != emp_id:
        abort(404)

    renewal_date = request.form.get("renewal_date", "").strip()
    expiration_date = request.form.get("expiration_date", "").strip()
    duration_string = _parse_duration_string(request.form.get("duration_string", ""))

    if not renewal_date or not expiration_date:
        flash("Renewal date and expiration date are required.", "error")
        return redirect(url_for("employees.profile", emp_id=emp_id))

    # Validate date formats
    try:
        from datetime import datetime
        datetime.strptime(renewal_date, "%Y-%m-%d")
        datetime.strptime(expiration_date, "%Y-%m-%d")
    except ValueError:
        flash("Invalid date format. Use YYYY-MM-DD.", "error")
        return redirect(url_for("employees.profile", emp_id=emp_id))

    renewal_id = create_renewal(conn, permit_id, renewal_date, expiration_date, duration_string)
    display_name = permit["display_name"] or "Unknown Permit"
    log_audit(conn, "PermitRenewal", renewal_id, "CREATE",
              f"Renewed {display_name} for {emp['first_name']} {emp['last_name']} — expires {expiration_date}",
              new_values={"renewal_date": renewal_date, "expiration_date": expiration_date,
                          "duration_string": duration_string})
    flash(f"Renewal recorded for '{display_name}'. New expiration: {expiration_date}.", "success")
    return redirect(url_for("employees.profile", emp_id=emp_id))


@bp.route("/<int:emp_id>/permits/<int:permit_id>/toggle", methods=["POST"])
def toggle_permit(emp_id, permit_id):
    conn = get_db()
    permit, _ = get_permit_with_renewals(conn, permit_id)
    if not permit or permit["employee_id"] != emp_id:
        abort(404)

    emp = get_employee(conn, emp_id)
    if permit["active"]:
        deactivate_permit(conn, permit_id)
        action = "Deactivated"
    else:
        activate_permit(conn, permit_id)
        action = "Reactivated"

    display_name = permit["display_name"] or "Unknown Permit"
    log_audit(conn, "EmployeePermit", permit_id, "UPDATE",
              f"{action} permit '{display_name}' for {emp['first_name']} {emp['last_name']}",
              old_values={"active": permit["active"]},
              new_values={"active": 0 if permit["active"] else 1})
    flash(f"{action} permit '{display_name}'.", "success")
    return redirect(url_for("employees.profile", emp_id=emp_id))
