"""
Data Validation Module - Application Layer
Validates and cleans extracted data from various sources.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import pprint

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates and cleans extracted delivery data."""
    
    def validate_extracted_json(self, data: Dict[str, Any], debug: bool = False) -> Optional[Dict[str, Any]]:
        """Validate and clean extracted JSON data - handles Claude JSON format."""
        if debug:
            logger.info("Validating extracted JSON data")
            logger.debug(f"Input data: {pprint.pformat(data, width=80, depth=3)}")
        
        if not isinstance(data, dict):
            logger.error("Data is not a dictionary")
            return None
        
        # Handle Claude's nested JSON format { "delivery": {...}, "items": [...] }
        delivery_data = data.get("delivery", {})
        items_data = data.get("items", [])
        
        if debug:
            logger.debug(f"Delivery Data Keys: {list(delivery_data.keys())}")
            logger.debug(f"Items Count: {len(items_data)}")
        
        # Extract from nested delivery object (Claude format)
        validated = {
            "delivery_number": str(delivery_data.get("delivery_number", "")).strip() or f"AUTO-{datetime.now().strftime('%Y%m%d')}-001",
            "supplier_name": str(delivery_data.get("supplier_name", "")).strip() or "Unbekannter Lieferant", 
            "supplier_id": str(delivery_data.get("supplier_id", "")).strip(),
            "delivery_date": delivery_data.get("delivery_date", datetime.now().strftime('%Y-%m-%d')),
            "employee_name": str(delivery_data.get("employee_name", "")).strip() or "OCR-Import",
            "order_number": str(delivery_data.get("order_number", "")).strip(),
            "notes": str(delivery_data.get("notes", "")).strip() or "Importiert via Claude API",
            "items": [],
            "total_items": 0
        }
        
        if debug:
            logger.debug(f"Extracted Values:")
            logger.debug(f"  - delivery_number: '{validated['delivery_number']}'")
            logger.debug(f"  - supplier_name: '{validated['supplier_name']}'")
            logger.debug(f"  - employee_name: '{validated['employee_name']}'")
            logger.debug(f"  - delivery_date: '{validated['delivery_date']}'")
            logger.debug(f"  - items to process: {len(items_data)}")
        
        # Validate and clean items
        if isinstance(items_data, list):
            for i, item in enumerate(items_data):
                if debug:
                    logger.debug(f"Processing Item {i+1}: {item}")
                
                if isinstance(item, dict):
                    # If item has no order_number, use global order_number as fallback
                    item_order_number = str(item.get("order_number", "")).strip()
                    if not item_order_number and validated.get("order_number"):
                        item_order_number = validated["order_number"]
                    
                    clean_item = {
                        "article_number": str(item.get("article_number", "")).strip(),
                        "description": (str(item.get("description", "")).strip() or 
                                      str(item.get("designation", "")).strip() or 
                                      "Unbekannter Artikel"),
                        "batch_number": str(item.get("batch_number", "")).strip(),
                        "quantity": max(int(item.get("quantity", 1)), 1),
                        "unit": str(item.get("unit", "Stück")).strip(),
                        "order_number": item_order_number
                    }
                    
                    if debug:
                        logger.debug(f"  → Cleaned: {clean_item}")
                    
                    if clean_item["article_number"]:  # Only add items with article numbers
                        validated["items"].append(clean_item)
                        if debug:
                            logger.debug(f"  Added to validated items")
                    else:
                        if debug:
                            logger.debug(f"  Skipped - no article number")
        
        validated["total_items"] = len(validated["items"])
        
        if debug:
            logger.debug(f"Validation Results:")
            logger.debug(f"  - Total items processed: {validated['total_items']}")
            logger.debug(f"  - Final delivery_number: '{validated['delivery_number']}'")
            logger.debug(f"  - Final supplier_name: '{validated['supplier_name']}'")
        
        # Add at least one item if none found
        if validated["total_items"] == 0:
            if debug:
                logger.warning("No items found - adding placeholder")
            
            validated["items"].append({
                "article_number": "MANUAL-001", 
                "description": "Manuell hinzufügen - OCR fand keine Artikel",
                "batch_number": "",
                "quantity": 1,
                "unit": "Stück",
                "order_number": ""
            })
            validated["total_items"] = 1
        
        if debug:
            logger.debug(f"Final validated data: {pprint.pformat(validated, width=80, depth=3)}")
        
        return validated
    
    def validate_delivery_data(self, delivery_data: Dict[str, Any]) -> bool:
        """Validate basic delivery data structure."""
        required_fields = ['delivery_number', 'supplier_name']
        
        for field in required_fields:
            if not delivery_data.get(field):
                logger.error(f"Missing required field: {field}")
                return False
        
        return True
    
    def validate_item_data(self, item_data: Dict[str, Any]) -> bool:
        """Validate basic item data structure."""
        required_fields = ['article_number', 'quantity']
        
        for field in required_fields:
            if not item_data.get(field):
                logger.error(f"Missing required item field: {field}")
                return False
        
        # Validate quantity is positive integer
        try:
            quantity = int(item_data['quantity'])
            if quantity <= 0:
                logger.error(f"Invalid quantity: {quantity}")
                return False
        except (ValueError, TypeError):
            logger.error(f"Invalid quantity type: {item_data['quantity']}")
            return False
        
        return True
    
    def clean_delivery_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize delivery data."""
        cleaned = {}
        
        # Clean string fields
        string_fields = ['delivery_number', 'supplier_name', 'supplier_id', 
                        'employee_name', 'order_number', 'notes']
        
        for field in string_fields:
            value = raw_data.get(field, "")
            cleaned[field] = str(value).strip() if value else ""
        
        # Handle date field
        delivery_date = raw_data.get('delivery_date')
        if delivery_date:
            # Ensure proper date format
            if isinstance(delivery_date, str):
                cleaned['delivery_date'] = delivery_date
            else:
                cleaned['delivery_date'] = str(delivery_date)
        else:
            cleaned['delivery_date'] = datetime.now().strftime('%Y-%m-%d')
        
        # Handle items
        items = raw_data.get('items', [])
        cleaned_items = []
        
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    cleaned_item = self.clean_item_data(item)
                    if cleaned_item and self.validate_item_data(cleaned_item):
                        cleaned_items.append(cleaned_item)
        
        cleaned['items'] = cleaned_items
        cleaned['total_items'] = len(cleaned_items)
        
        return cleaned
    
    def clean_item_data(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize item data."""
        cleaned = {}
        
        # Clean string fields
        string_fields = ['article_number', 'description', 'batch_number', 'unit', 'order_number']
        
        for field in string_fields:
            value = raw_item.get(field, "")
            cleaned[field] = str(value).strip() if value else ""
        
        # Handle quantity
        try:
            quantity = int(raw_item.get('quantity', 1))
            cleaned['quantity'] = max(quantity, 1)  # Ensure positive
        except (ValueError, TypeError):
            cleaned['quantity'] = 1
        
        # Set defaults
        if not cleaned.get('unit'):
            cleaned['unit'] = 'Stück'
        
        if not cleaned.get('description'):
            cleaned['description'] = 'Unbekannter Artikel'
        
        return cleaned


# Global instance
data_validator = DataValidator()