"""Audit log route."""

import json
from flask import Blueprint, render_template, request

from app import get_db
from app.models import get_audit_logs

bp = Blueprint("audit", __name__, url_prefix="/audit")


@bp.route("/")
def index():
    conn = get_db()

    entity_type = request.args.get("entity_type", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    page = int(request.args.get("page", 1))

    logs, total = get_audit_logs(
        conn,
        entity_type=entity_type or None,
        page=page,
        date_from=date_from or None,
        date_to=date_to or None,
    )

    per_page = 50
    total_pages = max(1, (total + per_page - 1) // per_page)

    # Parse JSON values for display
    log_entries = []
    for log in logs:
        entry = dict(log)
        entry["old_values"] = json.loads(entry["old_values_json"]) if entry["old_values_json"] else None
        entry["new_values"] = json.loads(entry["new_values_json"]) if entry["new_values_json"] else None
        log_entries.append(entry)

    return render_template(
        "audit.html",
        logs=log_entries,
        page=page,
        total_pages=total_pages,
        total=total,
        entity_type=entity_type,
        date_from=date_from,
        date_to=date_to,
    )
