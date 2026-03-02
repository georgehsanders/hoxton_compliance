"""
Outlook draft and clipboard email templates (STUB).

Will generate pre-formatted email content for compliance notifications:
  - Expiring permit reminders (per-employee)
  - Manager summary emails (per-group)
  - Escalation emails for overdue permits
  - Copy-to-clipboard for quick pasting into Outlook

Uses Jinja2 templates for email body formatting.
"""


def generate_reminder_email(employee, permits):
    """Generate an expiring-permit reminder email for an employee."""
    # TODO: Return dict with subject, body, recipient
    pass


def generate_manager_summary(group_name, employees):
    """Generate a manager summary email for a group."""
    # TODO: Return dict with subject, body
    pass


def copy_to_clipboard(text):
    """Copy text to system clipboard (cross-platform)."""
    # TODO: Use pyperclip or subprocess for clipboard access
    pass
