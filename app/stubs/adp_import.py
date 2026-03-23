"""
ADP CSV roster import module (STUB).

Will import employee roster data from ADP-exported CSV files.
Handles:
  - Matching employees by ADP employee_id
  - Creating new employees not yet in the system
  - Flagging employees in the system but not in ADP (possible terminations)
  - Updating group assignments and roles from ADP data
  - Writing audit log entries for all changes

NOTE: Column mapping is not yet implemented. The ADP export format has not
been confirmed. Once we receive a sample ADP CSV export, the column names
below (first_name, last_name, employee_id, department, role, email) will
need to be mapped to the actual ADP column headers. Until then, this module
is a placeholder.
"""


def import_adp_csv(db_path, csv_path):
    """Import employee data from an ADP CSV export.

    TODO: Implement CSV parsing and employee sync once ADP export format
    is confirmed. Column mapping will need to be configured based on
    the actual ADP CSV column headers.
    """
    raise NotImplementedError(
        "ADP import is not yet implemented. Column mapping must be "
        "configured once the ADP export format is confirmed."
    )


def preview_adp_import(csv_path):
    """Dry-run an import and return a summary of what would change.

    TODO: Implement once ADP export format is confirmed.
    """
    raise NotImplementedError(
        "ADP import preview is not yet implemented. Column mapping must be "
        "configured once the ADP export format is confirmed."
    )
