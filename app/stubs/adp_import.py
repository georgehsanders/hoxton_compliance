"""
ADP CSV roster import module (STUB).

Will import employee roster data from ADP-exported CSV files.
Handles:
  - Matching employees by ADP employee_id
  - Creating new employees not yet in the system
  - Flagging employees in the system but not in ADP (possible terminations)
  - Updating group assignments and roles from ADP data
  - Writing audit log entries for all changes
"""


def import_adp_csv(db_path, csv_path):
    """Import employee data from an ADP CSV export."""
    # TODO: Implement CSV parsing and employee sync
    pass


def preview_adp_import(csv_path):
    """Dry-run an import and return a summary of what would change."""
    # TODO: Return dict with new/updated/missing employee counts
    pass
