# Hotel Compliance Tracker

A local compliance tracking application for boutique hotels. Tracks employee permits, certifications, and their expiration status.

## Requirements

- Python 3.11+
- pip

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Seed the database with sample data
python seed.py

# Start the application
python run.py
```

Then open **http://localhost:5000** in your browser.

## Features (MVP)

- **Dashboard** — Headline compliance metrics, employees sorted by status
- **Group Dashboard** — Per-department compliance breakdown
- **Employee Roster** — Searchable employee list with expandable permit details
- **Employee Profile** — Edit employee info, manage permits, record renewals
- **Permit Directory** — All permit types with employee assignments
- **Settings** — Configurable thresholds, hotel name, report settings
- **Audit Log** — Full history of all changes with before/after values

## How It Works

Status is **never stored** — it's always computed from permit expiration dates:

| Status | Condition |
|---|---|
| **Expired** | Expiration date is in the past |
| **Upcoming** | Expiration date is within the threshold (default: 60 days) |
| **Active** | Expiration date is beyond the threshold |

Employee compliance is the worst status across all their active permits.

## Database

SQLite database stored as `compliance.db` in the project root. Migrations are in the `migrations/` folder — numbered SQL files applied automatically on first run.

To reset the database, delete `compliance.db` and re-run `python seed.py`.

## Stubbed Features (Coming Later)

These modules exist as placeholders with documented interfaces:

- **Excel Export** (`app/stubs/exporter.py`) — Generate .xlsx compliance reports
- **Shared Drive Publishing** (`app/stubs/publisher.py`) — Auto-publish to network drive
- **ADP Import** (`app/stubs/adp_import.py`) — Sync employee roster from ADP CSV
- **Email Templates** (`app/stubs/email_templates.py`) — Outlook draft generation
- **CLI / Task Scheduler** (`app/stubs/cli.py`) — Automated scheduled operations
