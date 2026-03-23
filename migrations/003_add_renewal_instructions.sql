-- Add renewal_instructions column to permit_type table
ALTER TABLE permit_type ADD COLUMN renewal_instructions TEXT DEFAULT '';
