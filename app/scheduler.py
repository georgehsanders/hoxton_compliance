"""
Midnight boundary job and scheduling helpers.

Recomputes status transitions at the day boundary, writes StatusEvents,
and marks the report as dirty when meaningful changes occur.

Called:
  - On app startup if it hasn't run today
  - By the future CLI entrypoint / Task Scheduler
"""

from datetime import date, datetime

from app.models import (
    get_settings, save_settings, get_all_employees, get_employee_permits,
    create_status_event, set_report_dirty,
)
from app.compliance import compute_permit_status, compute_employee_compliance


def run_midnight_job(conn):
    """
    Recompute all permit statuses and log transitions.

    Compares current computed statuses against the last known state
    (stored as status events) and writes new events for any changes.
    Sets report_dirty = true if any status changed.
    """
    settings = get_settings(conn)
    threshold = settings.get("upcoming_threshold_days", 60)
    employees = get_all_employees(conn, include_archived=False)
    changes_found = False

    for emp in employees:
        permits = get_employee_permits(conn, emp["id"], active_only=True)
        for p in permits:
            exp = p["latest_expiration"]
            new_status = compute_permit_status(exp, threshold)

            # Check last known status for this permit
            last_event = conn.execute(
                """SELECT to_status FROM status_event
                   WHERE entity_type = 'permit' AND entity_id = ?
                   ORDER BY created_at DESC LIMIT 1""",
                (p["id"],),
            ).fetchone()

            old_status = last_event["to_status"] if last_event else None

            if old_status != new_status:
                display_name = p["display_name"] or "Unknown Permit"
                emp_name = f"{emp['first_name']} {emp['last_name']}"
                summary = f"{display_name} for {emp_name}: {old_status or 'UNKNOWN'} → {new_status}"

                create_status_event(
                    conn,
                    entity_type="permit",
                    entity_id=p["id"],
                    event_type="STATUS_CHANGED",
                    summary_text=summary,
                    from_status=old_status,
                    to_status=new_status,
                )
                changes_found = True

    if changes_found:
        set_report_dirty(conn, True)

    # Update last run timestamp
    settings["last_midnight_run"] = date.today().isoformat()
    save_settings(conn, settings)

    return changes_found


def maybe_run_midnight_job():
    """Run the midnight job if it hasn't run today. Called from app startup."""
    from app import get_db
    conn = get_db()
    settings = get_settings(conn)
    last_run = settings.get("last_midnight_run")
    today = date.today().isoformat()

    if last_run != today:
        print(f"Running midnight boundary job (last run: {last_run})...")
        changed = run_midnight_job(conn)
        print(f"  Midnight job complete. Changes detected: {changed}")
