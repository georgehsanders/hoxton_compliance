"""Dashboard route — main compliance overview."""

from flask import Blueprint, render_template

from app import get_db
from app.compliance import compute_dashboard_data

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    conn = get_db()
    data = compute_dashboard_data(conn)
    return render_template("dashboard/index.html", **data)
