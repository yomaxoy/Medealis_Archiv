"""
Database Helper Functions - Working implementations from streamlit_app.py
"""

import logging
import pprint

logger = logging.getLogger(__name__)


def save_claude_extracted_delivery_to_db(delivery_data):
    """Save Claude-extracted delivery data to database using existing services"""
    print("\n" + "="*80)
    print("SAVE TO DATABASE - DEBUG")
    print("="*80)
    print("INPUT delivery_data:")
    pprint.pprint(delivery_data, width=80, depth=3)
    print("="*80)

    try:
        from warehouse.application.services import DeliveryService, ItemService, SupplierService

        # Initialize services
        delivery_service = DeliveryService()
        item_service = ItemService()
        supplier_service = SupplierService()

        print("Services initialized successfully")

        # DEBUG: Check DeliveryService.create_delivery signature
        import inspect
        create_delivery_sig = inspect.signature(delivery_service.create_delivery)
        print(f"DeliveryService.create_delivery signature: {create_delivery_sig}")
        print(f"Parameters: {list(create_delivery_sig.parameters.keys())}")

        # 1. Handle Supplier - create or find existing with intelligent mapping
        supplier_name = delivery_data.get('supplier_name', '').strip()
        supplier_id_input = delivery_data.get('supplier_id', '').strip()

        print(f"SUPPLIER DEBUG:")
        print(f"   supplier_name: '{supplier_name}'")
        print(f"   supplier_id_input: '{supplier_id_input}'")

        # NEW: Intelligentes Supplier-Mapping wenn supplier_name vorhanden aber supplier_id leer
        if supplier_name and not supplier_id_input:
            print(f"Using intelligent supplier mapping for: '{supplier_name}'")
            try:
                # Use the new mapping function from DeliveryService
                mapped_supplier_id = delivery_service.map_supplier_name_to_id(supplier_name)
                if mapped_supplier_id:
                    supplier_id_input = mapped_supplier_id
                    print(f"Mapped supplier: '{supplier_name}' -> '{mapped_supplier_id}'")
                else:
                    print(f"No mapping found for: '{supplier_name}', will create new")
            except Exception as e:
                print(f"Supplier mapping failed: {e}, will fallback to manual search")

        # Use supplier_id if provided (including mapped), otherwise use supplier_name
        supplier_lookup_value = supplier_id_input if supplier_id_input else supplier_name

        if not supplier_lookup_value:
            return {'success': False, 'error': 'Lieferantenname oder Supplier ID ist erforderlich'}

        # Try to find existing supplier by name or ID
        existing_suppliers = supplier_service.get_all_suppliers()
        found_supplier = None

        print(f"Looking for supplier with value: '{supplier_lookup_value}'")
        print(f"Available suppliers: {[s.get('name') + ' (ID: ' + str(s.get('id', 'N/A')) + ')' for s in existing_suppliers]}")

        # First try by ID (if supplier_lookup_value looks like an ID)
        for supplier in existing_suppliers:
            supplier_id = supplier.get('id') or supplier.get('supplier_id')
            if str(supplier_id) == supplier_lookup_value:
                found_supplier = supplier
                print(f"Found supplier by ID: {supplier.get('name')} (ID: {supplier_id})")
                break

        # If not found by ID, try by name
        if not found_supplier:
            for supplier in existing_suppliers:
                if supplier.get('name', '').lower() == supplier_lookup_value.lower():
                    found_supplier = supplier
                    print(f"Found supplier by name: {supplier.get('name')} (ID: {supplier.get('id')})")
                    break

        if found_supplier:
            final_supplier_id = found_supplier.get('id') or found_supplier.get('supplier_id')
            print(f"Using existing supplier ID: {final_supplier_id}")
        else:
            # Create new supplier - use name if available, otherwise use lookup value
            new_supplier_name = supplier_name if supplier_name else supplier_lookup_value
            print(f"Creating new supplier: {new_supplier_name}")
            supplier_result = supplier_service.create_supplier({
                'name': new_supplier_name,
                'contact_person': '',
                'address': '',
                'phone': '',
                'email': '',
                'notes': f'Automatisch erstellt via Claude Import'
            })
            if supplier_result.get('success'):
                final_supplier_id = supplier_result.get('supplier_id')
                print(f"Created new supplier with ID: {final_supplier_id}")
            else:
                print(f"Supplier creation failed: {supplier_result.get('error')}")
                return {'success': False, 'error': f'Fehler beim Erstellen des Lieferanten: {supplier_result.get("error")}'}

        # 2. Create Delivery WITH ITEMS in one transaction
        delivery_number = delivery_data.get('delivery_number', '').strip()
        if not delivery_number:
            from datetime import datetime
            delivery_number = f"CLAUDE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Parse delivery_date string to date object
        from datetime import datetime, date
        delivery_date_str = delivery_data.get('delivery_date', str(date.today()))
        try:
            if isinstance(delivery_date_str, str):
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y']:
                    try:
                        delivery_date_obj = datetime.strptime(delivery_date_str, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    # If no format worked, use today
                    delivery_date_obj = date.today()
            else:
                delivery_date_obj = delivery_date_str  # Assume it's already a date object
        except:
            delivery_date_obj = date.today()

        print(f"Delivery date: {delivery_date_obj} (from: {delivery_date_str})")

        # Prepare delivery data for service (match actual service signature)
        delivery_create_data = {
            'delivery_number': delivery_number,
            'supplier_id': str(final_supplier_id),
            'delivery_date': delivery_date_obj,
            'employee_name': delivery_data.get('employee_name', 'Claude-Import'),
            'document_path': None,  # Optional parameter from signature
            'notes': delivery_data.get('notes', 'Imported via Claude AI')
        }

        print(f"Creating delivery with data:")
        pprint.pprint(delivery_create_data, width=80, depth=2)

        # Create delivery
        delivery_result = delivery_service.create_delivery(**delivery_create_data)

        # DeliveryService.create_delivery returns a string (delivery_id) on success, not a dict
        if not delivery_result or not isinstance(delivery_result, str):
            print(f"Delivery creation failed: {delivery_result}")
            return {'success': False, 'error': f'Delivery creation failed: {delivery_result}'}

        print(f"Delivery created successfully: {delivery_number} (ID: {delivery_result})")
        created_delivery_id = delivery_result

        # 3. Create Items
        items_created = 0
        items_failed = 0
        error_messages = []

        items = delivery_data.get('items', [])
        print(f"Processing {len(items)} items...")

        for i, item in enumerate(items):
            try:
                # Extract item data
                article_number = item.get('article_number', '').strip()
                batch_number = item.get('batch_number', '').strip()
                quantity = item.get('quantity', 1)

                if not article_number:
                    article_number = f"ITEM-{i+1:03d}"
                    print(f"No article number, using: {article_number}")

                if not batch_number:
                    batch_number = f"BATCH-{delivery_number}-{i+1:03d}"
                    print(f"No batch number, using: {batch_number}")

                # Convert quantity to int
                try:
                    quantity = int(quantity)
                except (ValueError, TypeError):
                    quantity = 1
                    print(f"Invalid quantity, using: {quantity}")

                # Parse expiry date if available
                expiry_date = None
                if item.get('expiry_date'):
                    try:
                        expiry_date_str = item.get('expiry_date')
                        for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y']:
                            try:
                                expiry_date = datetime.strptime(expiry_date_str, fmt).date()
                                break
                            except ValueError:
                                continue
                    except:
                        expiry_date = None

                # === DREI MENGENTYPEN FÜR OCR-IMPORT ===
                # OCR extrahiert Lieferscheinmenge, Liefermenge muss manuell bestätigt werden
                item_create_data = {
                    'article_number': article_number,
                    'batch_number': batch_number,
                    'delivery_slip_quantity': quantity,  # OCR = Lieferscheinmenge
                    'delivered_quantity': quantity,  # Default: gleich wie Lieferschein (muss bestätigt werden!)
                    'ordered_quantity': None,  # Wird später aus Bestellung ergänzt
                    'delivery_number': delivery_number,
                    'order_number': item.get('order_number', ''),
                    'expiry_date': expiry_date,
                    'storage_location': item.get('storage_location', ''),
                    'description': item.get('description', 'Claude Import'),
                    'status': 'received'
                }

                print(f"Creating item {i+1}/{len(items)}: {article_number}")
                print(f"   Data: {item_create_data}")

                item_result = item_service.create_item(**item_create_data)

                # Handle both string (item_id) and dict return types
                if item_result:
                    if isinstance(item_result, str):
                        # ItemService returns string (item_id) on success
                        items_created += 1
                        print(f"Item {i+1} created successfully (ID: {item_result})")
                    elif isinstance(item_result, dict) and item_result.get('success'):
                        # Dict format with success flag
                        items_created += 1
                        print(f"Item {i+1} created successfully")
                    else:
                        items_failed += 1
                        error_msg = item_result.get('error', 'Unknown error') if isinstance(item_result, dict) else str(item_result)
                        error_messages.append(f"Item {i+1} ({article_number}): {error_msg}")
                        print(f"Item {i+1} failed: {error_msg}")
                else:
                    items_failed += 1
                    error_messages.append(f"Item {i+1} ({article_number}): No result returned")
                    print(f"Item {i+1} failed: No result returned")

            except Exception as e:
                items_failed += 1
                error_messages.append(f"Item {i+1}: {str(e)}")
                print(f"Item {i+1} exception: {e}")

        # 4. Return results
        success_message = f"Delivery '{delivery_number}' created with {items_created} items"
        if items_failed > 0:
            success_message += f" ({items_failed} items failed)"

        result = {
            'success': True,
            'message': success_message,
            'delivery_number': delivery_number,
            'items_created': items_created,
            'items_failed': items_failed,
            'errors': error_messages if error_messages else None
        }

        print(f"FINAL RESULT:")
        pprint.pprint(result, width=80, depth=2)
        print("="*80)

        return result

    except Exception as e:
        error_msg = f"Database save error: {str(e)}"
        print(f"{error_msg}")
        print("="*80)
        return {'success': False, 'error': error_msg}