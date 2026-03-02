"""
Compliance computation engine.

All compliance logic lives here — never scattered through routes.
Status is always computed from PermitRenewal.expiration_date, never stored.
"""

from datetime import date, datetime, timedelta

from app.models import get_settings, get_all_employees, get_employee_permits


# ── Permit-level status ──────────────────────────────────────────────────────

def compute_permit_status(expiration_date_str, threshold_days=60):
    """
    Compute a single permit's status from its latest expiration date.

    Returns one of: EXPIRED, UPCOMING, UPCOMING_TODAY, ACTIVE, NO_RENEWAL
    """
    if not expiration_date_str:
        return "NO_RENEWAL"

    today = date.today()
    try:
        exp = datetime.strptime(expiration_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return "NO_RENEWAL"

    if exp < today:
        return "EXPIRED"
    elif exp == today:
        return "UPCOMING_TODAY"
    elif exp <= today + timedelta(days=threshold_days):
        return "UPCOMING"
    else:
        return "ACTIVE"


def get_permit_status_label(status):
    """Human-readable label for a permit status."""
    labels = {
        "EXPIRED": "Expired",
        "UPCOMING": "Upcoming",
        "UPCOMING_TODAY": "Today",
        "ACTIVE": "Active",
        "NO_RENEWAL": "No Renewal",
    }
    return labels.get(status, status)


def get_permit_status_class(status):
    """CSS class for status badge."""
    classes = {
        "EXPIRED": "badge-expired",
        "UPCOMING": "badge-upcoming",
        "UPCOMING_TODAY": "badge-upcoming",
        "ACTIVE": "badge-active",
        "NO_RENEWAL": "badge-no-renewal",
        "COMPLIANT": "badge-active",
        "NO_PERMITS": "badge-active",
    }
    return classes.get(status, "badge-default")


# ── Employee-level compliance ─────────────────────────────────────────────────

def compute_employee_compliance(permits, threshold_days=60):
    """
    Compute an employee's overall compliance category from their active permits.

    permits: list of permit dicts/rows that have 'latest_expiration' key
    Returns: (category, details_dict)
        category: EXPIRED, UPCOMING, COMPLIANT, NO_PERMITS
        details_dict: {active: int, upcoming: int, expired: int, no_renewal: int, soonest_expiration: str}
    """
    if not permits:
        return "NO_PERMITS", {"active": 0, "upcoming": 0, "expired": 0, "no_renewal": 0, "soonest_expiration": None}

    counts = {"active": 0, "upcoming": 0, "expired": 0, "no_renewal": 0}
    soonest = None

    for p in permits:
        exp = p["latest_expiration"] if isinstance(p, dict) else p["latest_expiration"]
        status = compute_permit_status(exp, threshold_days)

        if status == "EXPIRED":
            counts["expired"] += 1
        elif status in ("UPCOMING", "UPCOMING_TODAY"):
            counts["upcoming"] += 1
            if exp and (soonest is None or exp < soonest):
                soonest = exp
        elif status == "ACTIVE":
            counts["active"] += 1
        else:
            counts["no_renewal"] += 1

    if counts["expired"] > 0:
        category = "EXPIRED"
    elif counts["upcoming"] > 0:
        category = "UPCOMING"
    else:
        category = "COMPLIANT"

    counts["soonest_expiration"] = soonest
    return category, counts


def get_employee_compliance_label(category):
    labels = {
        "EXPIRED": "Expired",
        "UPCOMING": "Upcoming",
        "COMPLIANT": "Compliant",
        "NO_PERMITS": "Compliant",
    }
    return labels.get(category, category)


# ── Dashboard-level aggregations ─────────────────────────────────────────────

def compute_dashboard_data(conn):
    """
    Compute full compliance dashboard data.

    Returns dict with:
        - metrics: headline %, fully compliant %, upcoming %, expired %
        - expired_employees: list sorted by longest overdue first
        - upcoming_employees: list sorted by soonest expiration first
        - compliant_employees: list sorted alphabetically
    """
    settings = get_settings(conn)
    threshold = settings.get("upcoming_threshold_days", 60)
    employees = get_all_employees(conn, include_archived=False)

    expired_list = []
    upcoming_list = []
    compliant_list = []
    total = len(employees)

    for emp in employees:
        permits = get_employee_permits(conn, emp["id"], active_only=True)
        category, details = compute_employee_compliance(permits, threshold)

        emp_data = dict(emp)
        emp_data["compliance_category"] = category
        emp_data["compliance_details"] = details
        emp_data["full_name"] = f"{emp['first_name']} {emp['last_name']}"

        # Find the most overdue/soonest expiration for sorting
        if permits:
            expirations = [p["latest_expiration"] for p in permits if p["latest_expiration"]]
            emp_data["worst_expiration"] = min(expirations) if expirations else None
        else:
            emp_data["worst_expiration"] = None

        if category == "EXPIRED":
            expired_list.append(emp_data)
        elif category == "UPCOMING":
            upcoming_list.append(emp_data)
        else:
            compliant_list.append(emp_data)

    # Sort: expired by longest overdue first (earliest date first)
    expired_list.sort(key=lambda e: e["worst_expiration"] or "9999-99-99")
    # Upcoming by soonest expiration first
    upcoming_list.sort(key=lambda e: e["compliance_details"]["soonest_expiration"] or "9999-99-99")
    # Compliant alphabetically
    compliant_list.sort(key=lambda e: e["full_name"])

    expired_count = len(expired_list)
    upcoming_count = len(upcoming_list)
    compliant_count = len(compliant_list)

    headline_pct = ((compliant_count + upcoming_count) / total * 100) if total > 0 else 100
    fully_compliant_pct = (compliant_count / total * 100) if total > 0 else 100
    upcoming_pct = (upcoming_count / total * 100) if total > 0 else 0
    expired_pct = (expired_count / total * 100) if total > 0 else 0

    return {
        "metrics": {
            "total": total,
            "headline_pct": round(headline_pct, 1),
            "compliant_count": compliant_count,
            "fully_compliant_pct": round(fully_compliant_pct, 1),
            "upcoming_count": upcoming_count,
            "upcoming_pct": round(upcoming_pct, 1),
            "expired_count": expired_count,
            "expired_pct": round(expired_pct, 1),
        },
        "expired_employees": expired_list,
        "upcoming_employees": upcoming_list,
        "compliant_employees": compliant_list,
    }


def compute_group_dashboard(conn):
    """Compute per-group compliance data for the group dashboard."""
    settings = get_settings(conn)
    threshold = settings.get("upcoming_threshold_days", 60)
    groups = conn.execute('SELECT * FROM "group" ORDER BY name').fetchall()
    employees = get_all_employees(conn, include_archived=False)

    group_data = []
    for grp in groups:
        grp_employees = [e for e in employees if e["group_id"] == grp["id"]]
        expired_list = []
        upcoming_list = []
        compliant_list = []

        for emp in grp_employees:
            permits = get_employee_permits(conn, emp["id"], active_only=True)
            category, details = compute_employee_compliance(permits, threshold)
            emp_data = dict(emp)
            emp_data["compliance_category"] = category
            emp_data["compliance_details"] = details
            emp_data["full_name"] = f"{emp['first_name']} {emp['last_name']}"

            if permits:
                expirations = [p["latest_expiration"] for p in permits if p["latest_expiration"]]
                emp_data["worst_expiration"] = min(expirations) if expirations else None
            else:
                emp_data["worst_expiration"] = None

            if category == "EXPIRED":
                expired_list.append(emp_data)
            elif category == "UPCOMING":
                upcoming_list.append(emp_data)
            else:
                compliant_list.append(emp_data)

        expired_list.sort(key=lambda e: e["worst_expiration"] or "9999-99-99")
        upcoming_list.sort(key=lambda e: e["compliance_details"]["soonest_expiration"] or "9999-99-99")
        compliant_list.sort(key=lambda e: e["full_name"])

        total_grp = len(grp_employees)
        ec = len(expired_list)
        uc = len(upcoming_list)
        cc = len(compliant_list)

        group_data.append({
            "group": dict(grp),
            "employees": expired_list + upcoming_list + compliant_list,
            "total": total_grp,
            "expired_count": ec,
            "upcoming_count": uc,
            "compliant_count": cc,
            "headline_pct": round(((cc + uc) / total_grp * 100), 1) if total_grp > 0 else 100,
        })

    return group_data
