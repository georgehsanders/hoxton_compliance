"""
Database access helpers using raw sqlite3.

All functions take a sqlite3 connection as their first argument.
"""

import json
import sqlite3
from datetime import datetime

# ── Default settings ──────────────────────────────────────────────────────────

DEFAULT_SETTINGS = {
    "hotel_name": "Hotel",
    "upcoming_threshold_days": 60,
    "change_list_days": 1,
    "shared_drive_path": "",
    "archive_retention_days": 7,
    "publish_interval_minutes": 5,
    "pause_reports": False,
    "last_midnight_run": None,
}


# ── Settings ──────────────────────────────────────────────────────────────────

def get_settings(conn):
    """Return merged settings dict (defaults + stored overrides)."""
    row = conn.execute("SELECT settings_json FROM settings WHERE id = 1").fetchone()
    stored = json.loads(row["settings_json"]) if row else {}
    merged = {**DEFAULT_SETTINGS, **stored}
    return merged


def save_settings(conn, settings_dict):
    """Persist settings dict to the single-row settings table."""
    conn.execute(
        "UPDATE settings SET settings_json = ? WHERE id = 1",
        (json.dumps(settings_dict),),
    )
    conn.commit()


# ── Report State ──────────────────────────────────────────────────────────────

def get_report_state(conn):
    row = conn.execute("SELECT * FROM report_state WHERE id = 1").fetchone()
    if row:
        return dict(row)
    return {
        "report_dirty": 1,
        "last_published_at": None,
        "last_export_status": "NEVER",
        "last_export_error_text": None,
    }


def set_report_dirty(conn, dirty=True):
    conn.execute(
        "UPDATE report_state SET report_dirty = ?, updated_at = ? WHERE id = 1",
        (1 if dirty else 0, datetime.utcnow().isoformat()),
    )
    conn.commit()


# ── Groups ────────────────────────────────────────────────────────────────────

def get_all_groups(conn):
    return conn.execute('SELECT * FROM "group" ORDER BY name').fetchall()


def get_group(conn, group_id):
    return conn.execute('SELECT * FROM "group" WHERE id = ?', (group_id,)).fetchone()


def create_group(conn, name):
    cursor = conn.execute('INSERT INTO "group" (name) VALUES (?)', (name,))
    conn.commit()
    return cursor.lastrowid


# ── Employees ─────────────────────────────────────────────────────────────────

def get_all_employees(conn, include_archived=False):
    if include_archived:
        sql = """
            SELECT e.*, g.name as group_name
            FROM employee e
            JOIN "group" g ON e.group_id = g.id
            ORDER BY e.last_name, e.first_name
        """
    else:
        sql = """
            SELECT e.*, g.name as group_name
            FROM employee e
            JOIN "group" g ON e.group_id = g.id
            WHERE e.archived = 0
            ORDER BY e.last_name, e.first_name
        """
    return conn.execute(sql).fetchall()


def get_employee(conn, employee_id):
    return conn.execute(
        """SELECT e.*, g.name as group_name
           FROM employee e
           JOIN "group" g ON e.group_id = g.id
           WHERE e.id = ?""",
        (employee_id,),
    ).fetchone()


def create_employee(conn, first_name, last_name, group_id, role="", email="", employee_id=None):
    now = datetime.utcnow().isoformat()
    cursor = conn.execute(
        """INSERT INTO employee (first_name, last_name, employee_id, group_id, role, email, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (first_name, last_name, employee_id or None, group_id, role, email, now, now),
    )
    conn.commit()
    return cursor.lastrowid


def update_employee(conn, emp_id, **kwargs):
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [emp_id]
    conn.execute(f"UPDATE employee SET {sets} WHERE id = ?", vals)
    conn.commit()


def archive_employee(conn, emp_id, archived=True):
    update_employee(conn, emp_id, archived=1 if archived else 0)


def get_all_reports_to_values(conn):
    """Return sorted list of distinct non-empty reports_to values."""
    rows = conn.execute(
        "SELECT DISTINCT reports_to FROM employee WHERE reports_to != '' ORDER BY reports_to"
    ).fetchall()
    return [row["reports_to"] for row in rows]


# ── Permit Types ──────────────────────────────────────────────────────────────

def get_all_permit_types(conn):
    return conn.execute("SELECT * FROM permit_type ORDER BY name").fetchall()


def get_permit_type(conn, pt_id):
    return conn.execute("SELECT * FROM permit_type WHERE id = ?", (pt_id,)).fetchone()


def create_permit_type(conn, name, issuing_authority="", renewal_url="", duration_string=None):
    cursor = conn.execute(
        """INSERT INTO permit_type (name, default_issuing_authority, default_renewal_url, default_duration_string)
           VALUES (?, ?, ?, ?)""",
        (name, issuing_authority, renewal_url, duration_string),
    )
    conn.commit()
    return cursor.lastrowid


# ── Employee Permits ──────────────────────────────────────────────────────────

def get_employee_permits(conn, employee_id, active_only=True):
    """Get all permits for an employee, with their latest renewal info."""
    where = "ep.employee_id = ?"
    if active_only:
        where += " AND ep.active = 1"
    sql = f"""
        SELECT ep.*, pt.name as permit_type_name,
               COALESCE(ep.custom_name, pt.name) as display_name,
               lr.expiration_date as latest_expiration,
               lr.renewal_date as latest_renewal_date,
               lr.duration_string as latest_duration_string
        FROM employee_permit ep
        LEFT JOIN permit_type pt ON ep.permit_type_id = pt.id
        LEFT JOIN (
            SELECT employee_permit_id, expiration_date, renewal_date, duration_string
            FROM permit_renewal pr1
            WHERE pr1.id = (
                SELECT pr2.id FROM permit_renewal pr2
                WHERE pr2.employee_permit_id = pr1.employee_permit_id
                ORDER BY pr2.expiration_date DESC
                LIMIT 1
            )
        ) lr ON lr.employee_permit_id = ep.id
        WHERE {where}
        ORDER BY COALESCE(ep.custom_name, pt.name)
    """
    return conn.execute(sql, (employee_id,)).fetchall()


def get_permit_with_renewals(conn, permit_id):
    """Get a single permit with all its renewal history."""
    permit = conn.execute(
        """SELECT ep.*, pt.name as permit_type_name,
                  COALESCE(ep.custom_name, pt.name) as display_name
           FROM employee_permit ep
           LEFT JOIN permit_type pt ON ep.permit_type_id = pt.id
           WHERE ep.id = ?""",
        (permit_id,),
    ).fetchone()
    if not permit:
        return None, []
    renewals = conn.execute(
        "SELECT * FROM permit_renewal WHERE employee_permit_id = ? ORDER BY expiration_date DESC",
        (permit_id,),
    ).fetchall()
    return permit, renewals


def create_employee_permit(conn, employee_id, permit_type_id=None, custom_name=None,
                           permit_number="", issuing_authority="", renewal_url=""):
    cursor = conn.execute(
        """INSERT INTO employee_permit (employee_id, permit_type_id, custom_name,
           permit_number, issuing_authority, renewal_url)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (employee_id, permit_type_id, custom_name, permit_number, issuing_authority, renewal_url),
    )
    conn.commit()
    return cursor.lastrowid


def deactivate_permit(conn, permit_id):
    conn.execute("UPDATE employee_permit SET active = 0 WHERE id = ?", (permit_id,))
    conn.commit()


def activate_permit(conn, permit_id):
    conn.execute("UPDATE employee_permit SET active = 1 WHERE id = ?", (permit_id,))
    conn.commit()


# ── Permit Renewals ──────────────────────────────────────────────────────────

def create_renewal(conn, employee_permit_id, renewal_date, expiration_date, duration_string=None):
    cursor = conn.execute(
        """INSERT INTO permit_renewal (employee_permit_id, renewal_date, expiration_date, duration_string)
           VALUES (?, ?, ?, ?)""",
        (employee_permit_id, renewal_date, expiration_date, duration_string),
    )
    conn.commit()
    return cursor.lastrowid


def get_latest_renewal(conn, employee_permit_id):
    return conn.execute(
        """SELECT * FROM permit_renewal
           WHERE employee_permit_id = ?
           ORDER BY expiration_date DESC LIMIT 1""",
        (employee_permit_id,),
    ).fetchone()


# ── Audit Log ─────────────────────────────────────────────────────────────────

def log_audit(conn, entity_type, entity_id, action_type, summary_text,
              old_values=None, new_values=None):
    """Write a row to the audit log. old_values and new_values are dicts."""
    conn.execute(
        """INSERT INTO audit_log (entity_type, entity_id, action_type, summary_text,
           old_values_json, new_values_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            entity_type, entity_id, action_type, summary_text,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
        ),
    )
    conn.commit()


def get_audit_logs(conn, entity_type=None, page=1, per_page=50, date_from=None, date_to=None):
    """Return paginated audit log entries with optional filters."""
    conditions = []
    params = []
    if entity_type:
        conditions.append("entity_type = ?")
        params.append(entity_type)
    if date_from:
        conditions.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("created_at <= ?")
        params.append(date_to + " 23:59:59")

    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * per_page

    count_row = conn.execute(f"SELECT COUNT(*) as cnt FROM audit_log{where}", params).fetchone()
    total = count_row["cnt"]

    rows = conn.execute(
        f"SELECT * FROM audit_log{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [per_page, offset],
    ).fetchall()

    return rows, total


# ── Status Events ─────────────────────────────────────────────────────────────

def create_status_event(conn, entity_type, entity_id, event_type, summary_text,
                        from_status=None, to_status=None, metadata=None):
    conn.execute(
        """INSERT INTO status_event (entity_type, entity_id, event_type, summary_text,
           from_status, to_status, metadata_json)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (entity_type, entity_id, event_type, summary_text,
         from_status, to_status, json.dumps(metadata) if metadata else None),
    )
    conn.commit()


# ── Helpers for permits by type ───────────────────────────────────────────────

def get_employees_by_permit_type(conn, permit_type_id):
    """Get all active employees holding a given permit type."""
    return conn.execute(
        """SELECT e.*, g.name as group_name, ep.id as permit_id,
                  ep.permit_number, ep.active as permit_active,
                  lr.expiration_date as latest_expiration
           FROM employee_permit ep
           JOIN employee e ON ep.employee_id = e.id
           JOIN "group" g ON e.group_id = g.id
           LEFT JOIN (
               SELECT employee_permit_id, expiration_date
               FROM permit_renewal pr1
               WHERE pr1.id = (
                   SELECT pr2.id FROM permit_renewal pr2
                   WHERE pr2.employee_permit_id = pr1.employee_permit_id
                   ORDER BY pr2.expiration_date DESC LIMIT 1
               )
           ) lr ON lr.employee_permit_id = ep.id
           WHERE ep.permit_type_id = ? AND ep.active = 1 AND e.archived = 0
           ORDER BY e.last_name, e.first_name""",
        (permit_type_id,),
    ).fetchall()
