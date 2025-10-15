# src/warehouse/application/services/export_service.py

"""
Export Service - Application Layer fuer das Warehouse Management System.

Verwaltet Excel- und CSV-Exporte von Datenbankdaten.
"""

import logging
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import tempfile

# External dependencies
try:
    import pandas as pd
except ImportError:
    logging.warning("pandas not installed - Excel exports not available")
    pd = None

logger = logging.getLogger(__name__)


class ExportService:
    """
    Service fuer den Export von Daten in verschiedene Formate.
    
    Unterstuetzt:
    - Excel (.xlsx)
    - CSV
    - JSON
    """
    
    def __init__(self):
        """Initialisiert den ExportService."""
        try:
            self.output_dir = Path.home() / ".medealis" / "exports"
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info("ExportService initialisiert")
            logger.info(f"Export-Verzeichnis: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Fehler bei ExportService Initialisierung: {e}")
            raise

    def _generate_filename(self, base_name: str, extension: str) -> str:
        """
        Generiert Dateinamen mit Zeitstempel.
        
        Args:
            base_name: Basis-Dateiname
            extension: Dateiendung (ohne Punkt)
            
        Returns:
            Vollstaendiger Dateiname
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}.{extension}"

    # === EXCEL EXPORTS ===
    
    def export_suppliers_to_excel(self, suppliers_data: List[Dict[str, Any]]) -> Path:
        """
        Exportiert Suppliers nach Excel.
        
        Args:
            suppliers_data: Liste von Supplier-Dictionaries
            
        Returns:
            Pfad zur Excel-Datei
        """
        try:
            if not pd:
                raise ImportError("pandas nicht verfuegbar fuer Excel-Export")
            
            logger.info(f"Exportiere {len(suppliers_data)} Suppliers nach Excel")
            
            # DataFrame erstellen
            df = pd.DataFrame(suppliers_data)
            
            # Spalten umbenennen (deutsch)
            column_mapping = {
                'supplier_id': 'Lieferanten-ID',
                'name': 'Name',
                'notes': 'Notizen',
                'created_at': 'Erstellt am',
                'updated_at': 'Aktualisiert am'
            }
            df = df.rename(columns=column_mapping)
            
            # Dateiname und Pfad
            filename = self._generate_filename("Suppliers", "xlsx")
            file_path = self.output_dir / filename
            
            # Excel schreiben (mit Fallback)
            try:
                with pd.ExcelWriter(str(file_path), engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Suppliers', index=False)
                    
                    # Spaltenbreite anpassen
                    worksheet = writer.sheets['Suppliers']
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            except ImportError:
                # Fallback zu CSV wenn openpyxl nicht verfuegbar
                csv_filename = self._generate_filename("Suppliers", "csv")
                csv_file_path = self.output_dir / csv_filename
                df.to_csv(str(csv_file_path), index=False, encoding='utf-8')
                logger.warning(f"openpyxl nicht verfuegbar - CSV erstellt statt Excel: {csv_file_path}")
                return csv_file_path
            
            logger.info(f"Suppliers-Export erstellt: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Fehler beim Suppliers-Excel-Export: {e}")
            raise

    def export_deliveries_to_excel(self, deliveries_data: List[Dict[str, Any]]) -> Path:
        """
        Exportiert Deliveries nach Excel.
        
        Args:
            deliveries_data: Liste von Delivery-Dictionaries
            
        Returns:
            Pfad zur Excel-Datei
        """
        try:
            if not pd:
                raise ImportError("pandas nicht verfügbar für Excel-Export")
            
            logger.info(f"Exportiere {len(deliveries_data)} Deliveries nach Excel")
            
            # DataFrame erstellen
            df = pd.DataFrame(deliveries_data)
            
            # Spalten umbenennen
            column_mapping = {
                'delivery_number': 'Lieferschein-Nr.',
                'supplier_id': 'Lieferant',
                'delivery_date': 'Lieferdatum',
                'status': 'Status',
                'employee_name': 'Bearbeiter',
                'items_count': 'Anzahl Items',
                'created_at': 'Erstellt am'
            }
            df = df.rename(columns=column_mapping)
            
            # Datums-Formatierung
            if 'Lieferdatum' in df.columns:
                df['Lieferdatum'] = pd.to_datetime(df['Lieferdatum']).dt.strftime('%d.%m.%Y')
            if 'Erstellt am' in df.columns:
                df['Erstellt am'] = pd.to_datetime(df['Erstellt am']).dt.strftime('%d.%m.%Y %H:%M')
            
            # Excel schreiben
            filename = self._generate_filename("Deliveries", "xlsx")
            file_path = self.output_dir / filename
            
            with pd.ExcelWriter(str(file_path), engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Deliveries', index=False)
                
                # Formatierung
                worksheet = writer.sheets['Deliveries']
                for column in worksheet.columns:
                    max_length = max(len(str(cell.value)) for cell in column)
                    adjusted_width = min(max_length + 2, 30)
                    worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
            
            logger.info(f"Deliveries-Export erstellt: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Fehler beim Deliveries-Excel-Export: {e}")
            raise

    def export_items_to_excel(self, items_data: List[Dict[str, Any]]) -> Path:
        """
        Exportiert Items nach Excel.
        
        Args:
            items_data: Liste von Item-Dictionaries
            
        Returns:
            Pfad zur Excel-Datei
        """
        try:
            if not pd:
                raise ImportError("pandas nicht verfügbar für Excel-Export")
            
            logger.info(f"Exportiere {len(items_data)} Items nach Excel")
            
            df = pd.DataFrame(items_data)
            
            column_mapping = {
                'article_number': 'Artikelnummer',
                'batch_number': 'Chargennummer', 
                'delivery_number': 'Lieferung',
                'quantity': 'Menge',
                'status': 'Status',
                'employee_name': 'Bearbeiter',
                'created_at': 'Erstellt am'
            }
            df = df.rename(columns=column_mapping)
            
            # Datums-Formatierung
            if 'Erstellt am' in df.columns:
                df['Erstellt am'] = pd.to_datetime(df['Erstellt am']).dt.strftime('%d.%m.%Y %H:%M')
            
            filename = self._generate_filename("Items", "xlsx")
            file_path = self.output_dir / filename
            
            with pd.ExcelWriter(str(file_path), engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Items', index=False)
                
                worksheet = writer.sheets['Items']
                for column in worksheet.columns:
                    max_length = max(len(str(cell.value)) for cell in column)
                    adjusted_width = min(max_length + 2, 25)
                    worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
            
            logger.info(f"Items-Export erstellt: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Fehler beim Items-Excel-Export: {e}")
            raise

    def export_orders_to_excel(self, orders_data: List[Dict[str, Any]]) -> Path:
        """
        Exportiert Orders nach Excel.
        
        Args:
            orders_data: Liste von Order-Dictionaries
            
        Returns:
            Pfad zur Excel-Datei
        """
        try:
            if not pd:
                raise ImportError("pandas nicht verfügbar für Excel-Export")
            
            logger.info(f"Exportiere {len(orders_data)} Orders nach Excel")
            
            df = pd.DataFrame(orders_data)
            
            column_mapping = {
                'order_number': 'Bestellnummer',
                'supplier_id': 'Lieferant',
                'order_date': 'Bestelldatum',
                'expected_delivery_date': 'Erwartetes Lieferdatum',
                'status': 'Status',
                'employee_name': 'Bearbeiter',
                'notes': 'Notizen',
                'created_at': 'Erstellt am'
            }
            df = df.rename(columns=column_mapping)
            
            # Datums-Formatierung
            date_columns = ['Bestelldatum', 'Erwartetes Lieferdatum', 'Erstellt am']
            for col in date_columns:
                if col in df.columns:
                    if col == 'Erstellt am':
                        df[col] = pd.to_datetime(df[col]).dt.strftime('%d.%m.%Y %H:%M')
                    else:
                        df[col] = pd.to_datetime(df[col]).dt.strftime('%d.%m.%Y')
            
            filename = self._generate_filename("Orders", "xlsx")
            file_path = self.output_dir / filename
            
            with pd.ExcelWriter(str(file_path), engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Orders', index=False)
                
                worksheet = writer.sheets['Orders']
                for column in worksheet.columns:
                    max_length = max(len(str(cell.value)) for cell in column)
                    adjusted_width = min(max_length + 2, 30)
                    worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
            
            logger.info(f"Orders-Export erstellt: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Fehler beim Orders-Excel-Export: {e}")
            raise

    # === COMBINED EXPORTS ===
    
    def export_full_warehouse_report(
        self, 
        suppliers_data: List[Dict[str, Any]],
        deliveries_data: List[Dict[str, Any]],
        items_data: List[Dict[str, Any]],
        orders_data: List[Dict[str, Any]]
    ) -> Path:
        """
        Erstellt einen vollständigen Warehouse-Report mit allen Daten.
        
        Args:
            suppliers_data: Supplier-Daten
            deliveries_data: Delivery-Daten  
            items_data: Items-Daten
            orders_data: Orders-Daten
            
        Returns:
            Pfad zur Excel-Datei
        """
        try:
            if not pd:
                raise ImportError("pandas nicht verfügbar für Excel-Export")
            
            logger.info("Erstelle vollständigen Warehouse-Report")
            
            filename = self._generate_filename("Warehouse_Report", "xlsx")
            file_path = self.output_dir / filename
            
            with pd.ExcelWriter(str(file_path), engine='openpyxl') as writer:
                # Suppliers Sheet
                if suppliers_data:
                    df_suppliers = pd.DataFrame(suppliers_data)
                    df_suppliers.to_excel(writer, sheet_name='Suppliers', index=False)
                
                # Deliveries Sheet
                if deliveries_data:
                    df_deliveries = pd.DataFrame(deliveries_data)
                    df_deliveries.to_excel(writer, sheet_name='Deliveries', index=False)
                
                # Items Sheet
                if items_data:
                    df_items = pd.DataFrame(items_data)
                    df_items.to_excel(writer, sheet_name='Items', index=False)
                
                # Orders Sheet
                if orders_data:
                    df_orders = pd.DataFrame(orders_data)
                    df_orders.to_excel(writer, sheet_name='Orders', index=False)
                
                # Summary Sheet
                summary_data = {
                    'Kategorie': ['Suppliers', 'Deliveries', 'Items', 'Orders'],
                    'Anzahl': [len(suppliers_data), len(deliveries_data), len(items_data), len(orders_data)],
                    'Export-Datum': [datetime.now().strftime('%d.%m.%Y %H:%M')] * 4
                }
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            logger.info(f"Vollständiger Warehouse-Report erstellt: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Warehouse-Reports: {e}")
            raise


# Test-Funktion
if __name__ == "__main__":
    print("Testing ExportService...")
    try:
        service = ExportService()
        print("✅ ExportService erfolgreich erstellt!")
        
        # Test-Daten
        test_suppliers = [
            {'supplier_id': 'SUP-001', 'name': 'Test Supplier 1', 'notes': 'Test'},
            {'supplier_id': 'SUP-002', 'name': 'Test Supplier 2', 'notes': None}
        ]
        
        # Test Export
        # export_path = service.export_suppliers_to_excel(test_suppliers)
        # print(f"✅ Test-Export erstellt: {export_path}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()