"""
Simple migration runner for the Hotel Compliance Tracker.

Reads numbered SQL files from the migrations/ directory and applies them
in order, tracking which have already been applied via the schema_version table.

Usage:
    python migrations/migrate.py
"""

import os
import re
import sys
import sqlite3

if getattr(sys, "frozen", False):
    MIGRATIONS_DIR = os.path.join(sys._MEIPASS, "migrations")
    DB_PATH = os.path.join(os.path.dirname(sys.executable), "compliance.db")
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "compliance.db")
    MIGRATIONS_DIR = os.path.dirname(__file__)


def get_migration_files():
    """Return sorted list of (version, filepath) tuples for SQL migration files."""
    files = []
    for fname in os.listdir(MIGRATIONS_DIR):
        match = re.match(r"^(\d+)_.+\.sql$", fname)
        if match:
            version = int(match.group(1))
            files.append((version, os.path.join(MIGRATIONS_DIR, fname)))
    return sorted(files, key=lambda x: x[0])


def get_applied_versions(conn):
    """Return set of already-applied migration versions."""
    try:
        cursor = conn.execute("SELECT version FROM schema_version")
        return {row[0] for row in cursor.fetchall()}
    except sqlite3.OperationalError:
        return set()


def run_migrations(db_path=None):
    """Apply all pending migrations."""
    db_path = db_path or DB_PATH
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    applied = get_applied_versions(conn)
    migrations = get_migration_files()

    for version, filepath in migrations:
        if version in applied:
            print(f"  Skipping migration {version} (already applied)")
            continue

        print(f"  Applying migration {version}: {os.path.basename(filepath)}")
        with open(filepath, "r") as f:
            sql = f.read()
        conn.executescript(sql)
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
        conn.commit()

    conn.close()
    print("  Migrations complete.")


if __name__ == "__main__":
    run_migrations()
