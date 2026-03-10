"""Managers route — view employees grouped by their 'reports to' value."""

from flask import Blueprint, render_template

from app import get_db
from app.models import get_all_employees, get_employee_permits, get_all_reports_to_values
from app.compliance import compute_employee_compliance, compute_permit_status, get_settings

bp = Blueprint("managers", __name__, url_prefix="/managers")


@bp.route("/")
def index():
    conn = get_db()
    settings = get_settings(conn)
    threshold = settings.get("upcoming_threshold_days", 60)
    employees = get_all_employees(conn, include_archived=False)

    # Build employee data with compliance info
    employee_data = []
    for emp in employees:
        permits = get_employee_permits(conn, emp["id"], active_only=True)
        category, details = compute_employee_compliance(permits, threshold)
        emp_data = dict(emp)
        emp_data["compliance_category"] = category
        emp_data["compliance_details"] = details
        emp_data["full_name"] = f"{emp['first_name']} {emp['last_name']}"
        employee_data.append(emp_data)

    # Group by reports_to
    managers = {}
    unassigned = []
    for emp in employee_data:
        rt = emp.get("reports_to", "").strip()
        if rt:
            managers.setdefault(rt, []).append(emp)
        else:
            unassigned.append(emp)

    # Sort manager names and employee lists
    sorted_managers = sorted(managers.items(), key=lambda x: x[0])

    return render_template(
        "managers/index.html",
        managers=sorted_managers,
        unassigned=unassigned,
    )
