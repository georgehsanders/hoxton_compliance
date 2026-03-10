-- 002_add_reports_to.sql
-- Adds reports_to field to employee table for manager tracking

ALTER TABLE employee ADD COLUMN reports_to TEXT NOT NULL DEFAULT '';
