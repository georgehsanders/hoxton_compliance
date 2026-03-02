"""
Seed script for the Hotel Compliance Tracker.

Populates the database with realistic sample data for testing:
- 3 groups
- 10 employees
- 5 permit types
- Mix of permit statuses: expired, upcoming, active, and employees with no permits

Usage:
    python seed.py
"""

import os
import sqlite3
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "compliance.db")


def seed():
    # Run migrations first
    from migrations.migrate import run_migrations
    run_migrations(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")

    # Check if data already exists
    count = conn.execute("SELECT COUNT(*) FROM employee").fetchone()[0]
    if count > 0:
        print("Database already has data. Delete compliance.db and re-run to reset.")
        conn.close()
        return

    today = date.today()

    # ── Groups ────────────────────────────────────────────────────────────
    groups = [
        ("Front Desk",),
        ("Housekeeping",),
        ("Food & Beverage",),
    ]
    conn.executemany('INSERT INTO "group" (name) VALUES (?)', groups)
    conn.commit()

    # Fetch group IDs
    gid = {}
    for row in conn.execute('SELECT id, name FROM "group"'):
        gid[row[1]] = row[0]

    # ── Permit Types ──────────────────────────────────────────────────────
    permit_types = [
        ("Food Handler", "County Health Dept", "https://health.county.gov/food-handler", "2 years"),
        ("First Aid / CPR", "American Red Cross", "https://redcross.org/first-aid", "2 years"),
        ("Alcohol Service (TIPS)", "TIPS Program", "https://www.tipsalcohol.com", "3 years"),
        ("Fire Safety", "City Fire Marshal", "https://fire.city.gov/training", "1 year"),
        ("Pool Operator", "County Health Dept", "https://health.county.gov/pool-operator", "5 years"),
    ]
    conn.executemany(
        """INSERT INTO permit_type (name, default_issuing_authority, default_renewal_url, default_duration_string)
           VALUES (?, ?, ?, ?)""",
        permit_types,
    )
    conn.commit()

    # Fetch permit type IDs
    ptid = {}
    for row in conn.execute("SELECT id, name FROM permit_type"):
        ptid[row[1]] = row[0]

    # ── Employees ─────────────────────────────────────────────────────────
    employees = [
        ("Maria", "Santos", gid["Front Desk"], "Front Desk Manager", "maria.santos@hotel.com"),
        ("James", "Chen", gid["Front Desk"], "Night Auditor", "james.chen@hotel.com"),
        ("Sofia", "Rodriguez", gid["Front Desk"], "Concierge", "sofia.rodriguez@hotel.com"),
        ("David", "Kim", gid["Housekeeping"], "Housekeeping Supervisor", "david.kim@hotel.com"),
        ("Ana", "Petrov", gid["Housekeeping"], "Room Attendant", "ana.petrov@hotel.com"),
        ("Marcus", "Johnson", gid["Housekeeping"], "Room Attendant", "marcus.johnson@hotel.com"),
        ("Isabella", "Moretti", gid["Food & Beverage"], "F&B Manager", "isabella.moretti@hotel.com"),
        ("Tyler", "Brooks", gid["Food & Beverage"], "Bartender", "tyler.brooks@hotel.com"),
        ("Priya", "Sharma", gid["Food & Beverage"], "Line Cook", "priya.sharma@hotel.com"),
        ("Liam", "O'Brien", gid["Food & Beverage"], "Server", "liam.obrien@hotel.com"),
    ]
    for first, last, group_id, role, email in employees:
        conn.execute(
            "INSERT INTO employee (first_name, last_name, group_id, role, email) VALUES (?, ?, ?, ?, ?)",
            (first, last, group_id, role, email),
        )
    conn.commit()

    # Fetch employee IDs
    eid = {}
    for row in conn.execute("SELECT id, first_name, last_name FROM employee"):
        eid[f"{row[1]} {row[2]}"] = row[0]

    # ── Helper to add a permit + renewal ──────────────────────────────────
    def add_permit(emp_name, permit_name, permit_number, renewal_date, expiration_date, duration=None):
        emp_id = eid[emp_name]
        pt_id = ptid[permit_name]
        pt = conn.execute("SELECT * FROM permit_type WHERE id = ?", (pt_id,)).fetchone()
        cursor = conn.execute(
            """INSERT INTO employee_permit (employee_id, permit_type_id, permit_number,
               issuing_authority, renewal_url)
               VALUES (?, ?, ?, ?, ?)""",
            (emp_id, pt_id, permit_number, pt[2], pt[3]),  # default_issuing_authority, default_renewal_url
        )
        permit_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO permit_renewal (employee_permit_id, renewal_date, expiration_date, duration_string) VALUES (?, ?, ?, ?)",
            (permit_id, renewal_date, expiration_date, duration),
        )
        # Write an audit log entry
        conn.execute(
            """INSERT INTO audit_log (entity_type, entity_id, action_type, summary_text)
               VALUES (?, ?, ?, ?)""",
            ("EmployeePermit", permit_id, "CREATE",
             f"Seeded {permit_name} for {emp_name} — expires {expiration_date}"),
        )

    # ── Assign permits with various statuses ──────────────────────────────

    # Maria Santos — Front Desk Manager: all compliant
    add_permit("Maria Santos", "First Aid / CPR", "FA-2024-101",
               (today - timedelta(days=180)).isoformat(),
               (today + timedelta(days=545)).isoformat(), "2 years")
    add_permit("Maria Santos", "Fire Safety", "FS-2024-101",
               (today - timedelta(days=90)).isoformat(),
               (today + timedelta(days=275)).isoformat(), "1 year")

    # James Chen — Night Auditor: one UPCOMING permit (expires in 30 days)
    add_permit("James Chen", "First Aid / CPR", "FA-2023-102",
               (today - timedelta(days=700)).isoformat(),
               (today + timedelta(days=30)).isoformat(), "2 years")
    add_permit("James Chen", "Fire Safety", "FS-2024-102",
               (today - timedelta(days=60)).isoformat(),
               (today + timedelta(days=305)).isoformat(), "1 year")

    # Sofia Rodriguez — Concierge: one EXPIRED (30 days ago)
    add_permit("Sofia Rodriguez", "First Aid / CPR", "FA-2022-103",
               (today - timedelta(days=760)).isoformat(),
               (today - timedelta(days=30)).isoformat(), "2 years")
    add_permit("Sofia Rodriguez", "Fire Safety", "FS-2024-103",
               (today - timedelta(days=45)).isoformat(),
               (today + timedelta(days=320)).isoformat(), "1 year")

    # David Kim — Housekeeping Supervisor: all compliant
    add_permit("David Kim", "First Aid / CPR", "FA-2024-201",
               (today - timedelta(days=120)).isoformat(),
               (today + timedelta(days=610)).isoformat(), "2 years")
    add_permit("David Kim", "Fire Safety", "FS-2024-201",
               (today - timedelta(days=30)).isoformat(),
               (today + timedelta(days=335)).isoformat(), "1 year")

    # Ana Petrov — Room Attendant: EXPIRED fire safety (90 days ago)
    add_permit("Ana Petrov", "Fire Safety", "FS-2023-202",
               (today - timedelta(days=455)).isoformat(),
               (today - timedelta(days=90)).isoformat(), "1 year")

    # Marcus Johnson — Room Attendant: no permits at all (NO_PERMITS)
    # (no permits added)

    # Isabella Moretti — F&B Manager: all compliant, multiple permits
    add_permit("Isabella Moretti", "Food Handler", "FH-2024-301",
               (today - timedelta(days=150)).isoformat(),
               (today + timedelta(days=580)).isoformat(), "2 years")
    add_permit("Isabella Moretti", "Alcohol Service (TIPS)", "TIPS-2024-301",
               (today - timedelta(days=200)).isoformat(),
               (today + timedelta(days=895)).isoformat(), "3 years")
    add_permit("Isabella Moretti", "First Aid / CPR", "FA-2024-301",
               (today - timedelta(days=100)).isoformat(),
               (today + timedelta(days=630)).isoformat(), "2 years")

    # Tyler Brooks — Bartender: UPCOMING alcohol service (expires in 15 days)
    add_permit("Tyler Brooks", "Food Handler", "FH-2024-302",
               (today - timedelta(days=90)).isoformat(),
               (today + timedelta(days=640)).isoformat(), "2 years")
    add_permit("Tyler Brooks", "Alcohol Service (TIPS)", "TIPS-2021-302",
               (today - timedelta(days=1080)).isoformat(),
               (today + timedelta(days=15)).isoformat(), "3 years")

    # Priya Sharma — Line Cook: EXPIRED food handler (14 days ago)
    add_permit("Priya Sharma", "Food Handler", "FH-2022-303",
               (today - timedelta(days=744)).isoformat(),
               (today - timedelta(days=14)).isoformat(), "2 years")
    add_permit("Priya Sharma", "Fire Safety", "FS-2024-303",
               (today - timedelta(days=60)).isoformat(),
               (today + timedelta(days=305)).isoformat(), "1 year")

    # Liam O'Brien — Server: UPCOMING food handler (45 days), active TIPS
    add_permit("Liam O'Brien", "Food Handler", "FH-2023-304",
               (today - timedelta(days=685)).isoformat(),
               (today + timedelta(days=45)).isoformat(), "2 years")
    add_permit("Liam O'Brien", "Alcohol Service (TIPS)", "TIPS-2024-304",
               (today - timedelta(days=60)).isoformat(),
               (today + timedelta(days=1035)).isoformat(), "3 years")

    conn.commit()
    conn.close()

    print("Seed data loaded successfully!")
    print("  3 groups, 10 employees, 5 permit types")
    print("  Status mix: 3 expired permits, 3 upcoming, rest active")
    print("  1 employee with no permits (Marcus Johnson)")
    print()
    print("Run the app with: python run.py")


if __name__ == "__main__":
    seed()
