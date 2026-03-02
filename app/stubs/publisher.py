"""
Shared drive publish pipeline (STUB).

Handles the full publish workflow:
  1. Export report to a temp file
  2. Archive the previous report (if exists) to an archive subfolder
  3. Copy new report to the shared drive folder
  4. Update ReportState with success/failure status
  5. Handle file locking (detect if report is open in Excel)

Configuration: shared_drive_path from Settings table.
"""


def publish_report(db_path, shared_drive_path):
    """Run the full publish pipeline: export -> archive -> copy."""
    # TODO: Implement publish pipeline
    pass


def check_file_lock(filepath):
    """Check if a file is locked (open in another application)."""
    # TODO: Implement Windows file lock detection
    pass


def archive_old_report(shared_drive_path, archive_retention_days=7):
    """Move old reports to archive subfolder, clean up expired archives."""
    # TODO: Implement archive rotation
    pass
