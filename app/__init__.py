"""Flask application factory for the Hotel Compliance Tracker."""

import os
import sqlite3

from flask import Flask, g

from app.scheduler import maybe_run_midnight_job

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "compliance.db")


def get_db():
    """Get a database connection for the current request, stored on g."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.secret_key = "hotel-compliance-tracker-dev-key"

    # Ensure database exists by running migrations
    if not os.path.exists(DB_PATH):
        from migrations.migrate import run_migrations
        print("Database not found — running migrations...")
        run_migrations(DB_PATH)

    app.teardown_appcontext(close_db)

    # Register template helpers
    from app.compliance import get_permit_status_label, get_permit_status_class

    @app.template_filter("status_badge")
    def status_badge_filter(status):
        css_class = get_permit_status_class(status)
        label = get_permit_status_label(status)
        return f'<span class="badge {css_class}">{label}</span>'

    @app.context_processor
    def inject_helpers():
        from app.models import get_settings, get_report_state
        conn = get_db()
        settings = get_settings(conn)
        report_state = get_report_state(conn)
        return dict(
            hotel_name=settings.get("hotel_name", "Hotel"),
            report_state=report_state,
        )

    # Register blueprints
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.employees import bp as employees_bp
    from app.routes.permits import bp as permits_bp
    from app.routes.groups import bp as groups_bp
    from app.routes.settings import bp as settings_bp
    from app.routes.audit import bp as audit_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(permits_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(audit_bp)

    # Custom error handlers
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("404.html"), 404

    # Run midnight job on startup if needed
    with app.app_context():
        try:
            maybe_run_midnight_job()
        except Exception as e:
            print(f"Warning: midnight job failed on startup: {e}")

    return app
