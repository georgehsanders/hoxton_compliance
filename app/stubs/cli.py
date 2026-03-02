"""
CLI entrypoint for Task Scheduler integration (STUB).

Will provide command-line interface for automated operations:
  - python -m app export-report    : Generate and publish Excel report
  - python -m app run-midnight     : Run the midnight boundary job
  - python -m app import-adp FILE  : Import ADP CSV roster

Designed to be called from Windows Task Scheduler for unattended operation.
"""


def main():
    """Parse CLI arguments and dispatch to appropriate function."""
    # TODO: Implement argparse-based CLI
    pass


if __name__ == "__main__":
    main()
