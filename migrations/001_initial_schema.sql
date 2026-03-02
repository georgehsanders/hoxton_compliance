-- 001_initial_schema.sql
-- Creates all tables for the Hotel Compliance Tracker

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "group" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employee (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    employee_id TEXT UNIQUE,
    group_id INTEGER NOT NULL REFERENCES "group"(id),
    role TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    archived INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS permit_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    default_issuing_authority TEXT NOT NULL DEFAULT '',
    default_renewal_url TEXT NOT NULL DEFAULT '',
    default_duration_string TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employee_permit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employee(id),
    permit_type_id INTEGER REFERENCES permit_type(id),
    custom_name TEXT,
    permit_number TEXT NOT NULL DEFAULT '',
    issuing_authority TEXT NOT NULL DEFAULT '',
    renewal_url TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS permit_renewal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_permit_id INTEGER NOT NULL REFERENCES employee_permit(id),
    renewal_date TEXT NOT NULL,
    duration_string TEXT,
    expiration_date TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    old_values_json TEXT,
    new_values_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    settings_json TEXT NOT NULL DEFAULT '{}'
);

INSERT OR IGNORE INTO settings (id, settings_json) VALUES (1, '{}');

CREATE TABLE IF NOT EXISTS report_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    report_dirty INTEGER NOT NULL DEFAULT 1,
    last_published_at TIMESTAMP,
    last_published_snapshot_json TEXT,
    last_export_status TEXT NOT NULL DEFAULT 'NEVER',
    last_export_error_text TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO report_state (id) VALUES (1);

CREATE TABLE IF NOT EXISTS status_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT,
    summary_text TEXT NOT NULL,
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    snapshot_version INTEGER NOT NULL,
    snapshot_gzip_blob BLOB
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_employee_group ON employee(group_id);
CREATE INDEX IF NOT EXISTS idx_employee_archived ON employee(archived);
CREATE INDEX IF NOT EXISTS idx_employee_permit_employee ON employee_permit(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_permit_type ON employee_permit(permit_type_id);
CREATE INDEX IF NOT EXISTS idx_permit_renewal_permit ON permit_renewal(employee_permit_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_status_event_entity ON status_event(entity_type, entity_id);
