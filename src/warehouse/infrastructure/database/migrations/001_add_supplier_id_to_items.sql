-- Migration: Add supplier_id to items table
-- Purpose: Denormalize supplier_id from deliveries for faster queries
-- Ensures supplier_id is properly mapped on items

-- Step 1: Add the column if it doesn't exist
ALTER TABLE items
ADD COLUMN supplier_id VARCHAR(20) NULL;

-- Step 2: Create foreign key constraint
ALTER TABLE items
ADD CONSTRAINT fk_items_supplier_id
FOREIGN KEY (supplier_id)
REFERENCES suppliers(supplier_id);

-- Step 3: Create index for better query performance
CREATE INDEX idx_items_supplier_id ON items(supplier_id);

-- Step 4: Populate existing items with supplier_id from deliveries
UPDATE items
SET supplier_id = (
    SELECT d.supplier_id
    FROM deliveries d
    WHERE d.delivery_number = items.delivery_number
    LIMIT 1
)
WHERE supplier_id IS NULL;

-- Verification: Count items that were updated
-- SELECT COUNT(*) as updated_count FROM items WHERE supplier_id IS NOT NULL;
