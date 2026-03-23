"""Export routes — CSV export, print-friendly view, and compliance email draft."""

import csv
import io
from datetime import date

from flask import Blueprint, Response, render_template

from app import get_db
from app.models import (
    get_settings, get_all_employees, get_employee_permits,
    get_all_permit_types, get_permit_type,
)
from app.compliance import (
    compute_dashboard_data, compute_permit_status,
    compute_employee_compliance, get_permit_status_label,
)

bp = Blueprint("export", __name__, url_prefix="/export")


@bp.route("/csv")
def export_csv():
    """Export full raw data dump as CSV: all employees, their permits, and compliance status."""
    conn = get_db()
    settings = get_settings(conn)
    threshold = settings.get("upcoming_threshold_days", 60)
    employees = get_all_employees(conn, include_archived=False)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Employee ID", "First Name", "Last Name", "Email", "Role",
        "Group", "Reports To", "Permit Name", "Permit Number",
        "Issuing Authority", "Expiration Date", "Permit Status",
        "Employee Compliance Status",
    ])

    for emp in employees:
        permits = get_employee_permits(conn, emp["id"], active_only=True)
        category, _ = compute_employee_compliance(permits, threshold)

        if permits:
            for p in permits:
                status = compute_permit_status(p["latest_expiration"], threshold)
                writer.writerow([
                    emp["employee_id"] or "",
                    emp["first_name"],
                    emp["last_name"],
                    emp["email"] or "",
                    emp["role"] or "",
                    emp["group_name"],
                    emp["reports_to"] or "",
                    p["display_name"],
                    p["permit_number"] or "",
                    p["issuing_authority"] or "",
                    p["latest_expiration"] or "",
                    get_permit_status_label(status),
                    category,
                ])
        else:
            writer.writerow([
                emp["employee_id"] or "",
                emp["first_name"],
                emp["last_name"],
                emp["email"] or "",
                emp["role"] or "",
                emp["group_name"],
                emp["reports_to"] or "",
                "", "", "", "", "",
                category,
            ])

    hotel_name = settings.get("hotel_name", "Hotel").replace(" ", "_")
    filename = f"{hotel_name}_Compliance_{date.today().isoformat()}.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@bp.route("/print")
def print_view():
    """Render a print-optimized dashboard that triggers the browser print dialog."""
    conn = get_db()
    data = compute_dashboard_data(conn)
    settings = get_settings(conn)
    return render_template("export/print_report.html", **data, settings=settings, today=date.today().isoformat())


@bp.route("/email-draft")
def email_draft():
    """Generate a copy-pasteable compliance email draft."""
    conn = get_db()
    settings = get_settings(conn)
    threshold = settings.get("upcoming_threshold_days", 60)
    data = compute_dashboard_data(conn)

    # Collect permit type renewal instructions for referenced permits
    permit_type_instructions = {}
    all_flagged = data["expired_employees"] + data["upcoming_employees"]

    for emp in all_flagged:
        permits = get_employee_permits(conn, emp["id"], active_only=True)
        for p in permits:
            status = compute_permit_status(p["latest_expiration"], threshold)
            if status in ("EXPIRED", "UPCOMING", "UPCOMING_TODAY"):
                pt_id = p["permit_type_id"]
                if pt_id and pt_id not in permit_type_instructions:
                    pt = get_permit_type(conn, pt_id)
                    if pt:
                        try:
                            instructions = pt["renewal_instructions"]
                        except (IndexError, KeyError):
                            instructions = ""
                        permit_type_instructions[pt_id] = {
                            "name": pt["name"],
                            "renewal_instructions": instructions or "",
                        }
        # Attach permit details to employee dict for template
        emp["flagged_permits"] = [
            {
                "display_name": p["display_name"],
                "latest_expiration": p["latest_expiration"],
                "status": compute_permit_status(p["latest_expiration"], threshold),
                "status_label": get_permit_status_label(compute_permit_status(p["latest_expiration"], threshold)),
                "permit_type_id": p["permit_type_id"],
            }
            for p in permits
            if compute_permit_status(p["latest_expiration"], threshold) in ("EXPIRED", "UPCOMING", "UPCOMING_TODAY")
        ]

    return render_template(
        "export/email_draft.html",
        settings=settings,
        expired_employees=data["expired_employees"],
        upcoming_employees=data["upcoming_employees"],
        permit_type_instructions=permit_type_instructions,
        today=date.today().isoformat(),
    )
