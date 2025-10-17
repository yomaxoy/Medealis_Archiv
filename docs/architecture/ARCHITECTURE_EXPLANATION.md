# Clean Architecture Komponenten - Detaillierte Erklärung

## Übersicht der aktuellen Architektur-Schichten

```
PRESENTATION LAYER (Streamlit Views + Popups)
       ↓
APPLICATION LAYER (Services: DeliveryService, ItemService)
       ↓
DOMAIN LAYER (Entities + Value Objects + Enums + Repository Interfaces)
       ↓ (Dependency Inversion)
INFRASTRUCTURE LAYER (Database Models + Repository Implementations + Mappers)
```

## 1. Domain Entities vs. Infrastructure Models

### Domain Entities - Geschäftslogik ohne Infrastruktur
```python
# domain/entities/item.py
from warehouse.domain.value_objects.article_number import ArticleNumber
from warehouse.domain.enums.item_status import ItemStatus

class Item:
    """Pure Geschäftsobjekt - KEINE Datenbankdetails"""

    def __init__(self, article_number: ArticleNumber, batch_number: BatchNumber, ...):
        self.article_number = article_number  # Value Object
        self.batch_number = batch_number      # Value Object
        self.status_steps: Dict[ItemStatus, StatusStep] = {}

    def complete_inspection(self, employee: str) -> None:
        """GESCHÄFTSLOGIK: Prüfung abschließen"""
        if not self.can_complete_inspection():
            raise InvalidStatusTransitionException("Prüfung kann nicht abgeschlossen werden")

        self.status_steps[ItemStatus.SICHT_GEPRUEFT].complete(employee)
        self._update_overall_status()

    def calculate_waste_percentage(self) -> Decimal:
        """GESCHÄFTSLOGIK: Ausschussquote berechnen"""
        if self.quantity <= 0:
            return Decimal("0")
        waste = self.inspection_result.waste_quantity if self.inspection_result else 0
        return Decimal(waste) / Decimal(self.quantity) * Decimal("100")
```

**Zweck:**
- ✅ **Reine Geschäftslogik** - Wie soll sich ein Item verhalten?
- ✅ **Framework-unabhängig** - Keine SQLAlchemy Imports
- ✅ **Testbarkeit** - Ohne Datenbank testbar
- ✅ **Wiederverwendbarkeit** - Kann mit verschiedenen Persistierung-Strategien verwendet werden

### Infrastructure Models - Datenbankschema
```python
# infrastructure/database/models/item_model.py
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

class ItemModel(Base):
    """SQLAlchemy Model - NUR für Datenbankpersistierung"""

    __tablename__ = "items"

    # COMPOSITE PRIMARY KEY (Datenbank-spezifisch)
    article_number = Column(String(7), ForeignKey("item_info.article_number"), primary_key=True)
    batch_number = Column(String(19), primary_key=True)
    delivery_number = Column(String(10), ForeignKey("deliveries.delivery_number"), primary_key=True)

    # BUSINESS FIELDS (als primitive Typen)
    quantity = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="Artikel angelegt")

    # ZERTIFIKATE (als Boolean Flags)
    material_certificate = Column(Boolean, nullable=False, default=False)
    measurement_protocol = Column(Boolean, nullable=False, default=False)

    # RELATIONSHIPS (SQLAlchemy-spezifisch)
    # delivery = relationship("DeliveryModel", back_populates="items")
    # item_info = relationship("ItemInfoModel", back_populates="items")

    # KEINE GESCHÄFTSLOGIK!
```

**Zweck:**
- ✅ **Datenbankschema definieren** - Tabellen, Spalten, Constraints
- ✅ **SQLAlchemy-spezifisch** - Foreign Keys, Relationships
- ✅ **Persistierung-Optimierung** - Indizes, Datentypen
- ❌ **KEINE Geschäftslogik** - Nur Datenstruktur

## 2. Repository Pattern - Interfaces vs. Implementations

### Domain Repository Interface - Contract Definition
```python
# domain/repositories/item_repository.py
from abc import ABC, abstractmethod
from warehouse.domain.entities.item import Item

class ItemRepository(ABC):
    """Interface - definiert WAS möglich ist, nicht WIE"""

    @abstractmethod
    def save(self, item: Item) -> Item:
        """Speichere Domain Entity - WIE ist egal"""
        pass

    @abstractmethod
    def find_by_composite_key(self, article_number: str, batch_number: str, delivery_number: str) -> Optional[Item]:
        """Finde Item anhand Business-Identifikator"""
        pass

    @abstractmethod
    def find_items_by_status(self, status: ItemStatus) -> List[Item]:
        """Finde Items nach Geschäftsstatus"""
        pass

    @abstractmethod
    def find_items_needing_inspection(self) -> List[Item]:
        """Geschäfts-spezifische Abfrage"""
        pass
```

**Zweck:**
- ✅ **Dependency Inversion** - Domain definiert was Infrastructure implementieren muss
- ✅ **Testbarkeit** - Mock-Implementations für Unit Tests
- ✅ **Flexibilität** - Verschiedene Persistence-Strategien möglich
- ✅ **Geschäfts-orientiert** - Methoden entsprechen Use Cases

### Infrastructure Repository Implementation - Konkrete Umsetzung
```python
# infrastructure/database/repositories/sql_item_repository.py
from warehouse.domain.repositories.item_repository import ItemRepository
from warehouse.domain.entities.item import Item
from warehouse.domain.enums.item_status import ItemStatus
from warehouse.infrastructure.database.models.item_model import ItemModel
from warehouse.infrastructure.database.mappers.item_mapper import ItemMapper

class SQLItemRepository(ItemRepository):
    """SQLAlchemy Implementation des Repository Interface"""

    def __init__(self):
        self.mapper = ItemMapper()

    def save(self, item: Item) -> Item:
        """KONKRETE Implementation mit SQLAlchemy"""
        with get_session() as session:
            # 1. Domain Entity → Database Model (über Mapper)
            item_model = self.mapper.to_model(item)

            # 2. SQLAlchemy Persistierung
            session.merge(item_model)  # INSERT oder UPDATE
            session.flush()  # Damit wir ID bekommen

            # 3. Database Model → Domain Entity (über Mapper)
            return self.mapper.to_domain(item_model)

    def find_by_composite_key(self, article_number: str, batch_number: str, delivery_number: str) -> Optional[Item]:
        """SQL-spezifische Abfrage"""
        with get_session() as session:
            model = session.query(ItemModel).filter(
                ItemModel.article_number == article_number,
                ItemModel.batch_number == batch_number,
                ItemModel.delivery_number == delivery_number
            ).first()

            if model:
                return self.mapper.to_domain(model)  # Model → Entity
            return None

    def find_items_by_status(self, status: ItemStatus) -> List[Item]:
        """Status-basierte Abfrage mit Enum-Konvertierung"""
        with get_session() as session:
            models = session.query(ItemModel).filter(
                ItemModel.status == status.value  # Enum → String
            ).all()

            return [self.mapper.to_domain(model) for model in models]

    def find_items_needing_inspection(self) -> List[Item]:
        """Komplexe geschäfts-spezifische SQL-Abfrage"""
        with get_session() as session:
            models = session.query(ItemModel).filter(
                ItemModel.status.in_(["Artikel angelegt", "Daten geprüft"]),
                ItemModel.visual_inspector.is_(None)
            ).all()

            return [self.mapper.to_domain(model) for model in models]
```

**Zweck:**
- ✅ **SQLAlchemy-spezifische Implementierung**
- ✅ **Session-Management** für Transaktionen
- ✅ **SQL-Optimierung** für Performance
- ✅ **Mapper-Verwendung** für Entity ↔ Model Konvertierung

## 3. Mappers - Die Übersetzungsschicht

### Warum Mappers notwendig sind
```python
# PROBLEM: Domain Entity und Database Model sind unterschiedlich

# Domain Entity
class Item:
    article_number: ArticleNumber      # Value Object
    batch_number: BatchNumber          # Value Object
    status_steps: Dict[ItemStatus, StatusStep]  # Complex Object
    priority_level: PriorityLevel      # Enum

# Database Model
class ItemModel:
    article_number: str                # Primitive String
    batch_number: str                  # Primitive String
    status: str                        # Primitive String
    priority_level: str                # Primitive String
```

### Item Mapper - Bidirektionale Konvertierung
```python
# infrastructure/database/mappers/item_mapper.py
class ItemMapper(BaseMapper):

    def to_domain(self, model: ItemModel) -> Item:
        """Database Model → Domain Entity"""
        try:
            # 1. Primitive → Value Objects
            article_number = ArticleNumber(model.article_number)
            batch_number = BatchNumber(model.batch_number)

            # 2. String → Enum
            priority = PriorityLevel.MEDIUM
            if model.priority_level:
                priority = PriorityLevel(model.priority_level)

            # 3. Domain Entity erstellen
            item = Item(
                article_number=article_number,
                batch_number=batch_number,
                delivery_number=model.delivery_number,
                supplier_id=self._get_supplier_id_safe(model),
                quantity=model.delivery_quantity or 0,
                priority_level=priority
            )

            # 4. Komplexe Objekte rekonstruieren
            self._reconstruct_status_steps(item, model)
            self._reconstruct_certificates(item, model)

            return item

        except Exception as e:
            # Robustes Error-Handling
            return self._create_fallback_item(model)

    def to_model(self, entity: Item) -> ItemModel:
        """Domain Entity → Database Model"""
        return ItemModel(
            # 1. Value Objects → Primitive
            article_number=str(entity.article_number),
            batch_number=str(entity.batch_number),

            # 2. Enum → String
            status=entity.get_current_status().value,
            priority_level=entity.priority_level.value,

            # 3. Complex Objects → Primitive
            delivery_quantity=entity.quantity,
            material_certificate=entity.has_certificate(CertificateType.MATERIALZEUGNIS),
            measurement_protocol=entity.has_certificate(CertificateType.MESSPROTOKOLL),

            # 4. Metadaten
            notes=entity.notes,
            employee=entity.created_by
        )

    def _reconstruct_status_steps(self, item: Item, model: ItemModel):
        """Komplexe Status-Rekonstruktion"""
        # Logik um aus primitiven Datenbank-Feldern
        # komplexe Domain-Objekte zu rekonstruieren
        pass
```

**Zweck:**
- ✅ **Typen-Konvertierung** - Value Objects ↔ Primitive Types
- ✅ **Struktur-Mapping** - Complex Objects ↔ Flat Database Fields
- ✅ **Error-Handling** - Robuste Konvertierung mit Fallbacks
- ✅ **Bidirektional** - Entity ↔ Model in beide Richtungen

## 4. Warum diese Trennung? - Praktische Vorteile

### Beispiel: Status-System
```python
# DOMAIN: Flexibles Status-System
class Item:
    status_steps: Dict[ItemStatus, StatusStep] = {
        ItemStatus.ARTIKEL_ANGELEGT: StatusStep(completed=True, employee="Hans"),
        ItemStatus.DATEN_GEPRUEFT: StatusStep(completed=False),
        ItemStatus.SICHT_GEPRUEFT: StatusStep(completed=False),
    }

    def get_current_status(self) -> ItemStatus:
        # Komplexe Geschäftslogik
        completed_steps = [status for status, step in self.status_steps.items() if step.completed]
        return max(completed_steps) if completed_steps else ItemStatus.ARTIKEL_ANGELEGT

# DATABASE: Einfaches String-Feld
class ItemModel:
    status: str = "Artikel angelegt"  # Aktueller Status als String
```

### Beispiel: Zertifikate-System
```python
# DOMAIN: Typsichere Zertifikate
class Item:
    certificates: Set[CertificateType] = {
        CertificateType.MATERIALZEUGNIS,
        CertificateType.MESSPROTOKOLL
    }

    def has_certificate(self, cert_type: CertificateType) -> bool:
        return cert_type in self.certificates

    def add_certificate(self, cert_type: CertificateType):
        self.certificates.add(cert_type)

# DATABASE: Boolean Flags (Normalisiert)
class ItemModel:
    material_certificate: bool = True
    measurement_protocol: bool = True
    coating_certificate: bool = False
    hardness_certificate: bool = False
```

## 5. Datenfluss-Beispiel: Item speichern

```python
# 1. APPLICATION LAYER
def create_item_use_case(request: CreateItemRequest):
    # Domain Entity erstellen
    item = Item(
        article_number=ArticleNumber(request.article_number),
        batch_number=BatchNumber(request.batch_number),
        # ...
    )

    # Repository Interface verwenden (Dependency Injection)
    saved_item = item_repository.save(item)  # Interface!
    return saved_item

# 2. INFRASTRUCTURE REPOSITORY
class SQLItemRepository(ItemRepository):
    def save(self, item: Item) -> Item:
        with get_session() as session:
            # 3. MAPPER: Domain → Database
            item_model = self.mapper.to_model(item)

            # 4. SQLAlchemy Persistierung
            session.merge(item_model)

            # 5. MAPPER: Database → Domain
            return self.mapper.to_domain(item_model)
```

## 6. Vorteile dieser Architektur

### ✅ **Testbarkeit**
```python
# Unit Test - Nur Domain Logic
def test_item_inspection_logic():
    item = Item(ArticleNumber("A0001"), BatchNumber("P-123-456"), ...)
    item.complete_inspection("TestUser")
    assert item.get_current_status() == ItemStatus.SICHT_GEPRUEFT

# Integration Test - Mit Mock Repository
def test_item_save_use_case():
    mock_repository = Mock(spec=ItemRepository)
    use_case = CreateItemUseCase(mock_repository)
    # Test ohne echte Datenbank
```

### ✅ **Flexibilität**
```python
# Verschiedene Persistierung-Strategien
class SqliteItemRepository(ItemRepository): pass
class PostgreSQLItemRepository(ItemRepository): pass
class MongoDBItemRepository(ItemRepository): pass
class InMemoryItemRepository(ItemRepository): pass  # Für Tests
```

### ✅ **Evolution**
```python
# Domain kann sich ändern ohne Database-Schema zu brechen
class Item:
    # NEU: Komplexeres Status-System
    workflow_state: ItemWorkflowState  # Neue Abstraktion

    # Mapper handle die Konvertierung
    # Database Schema bleibt gleich
```

### ✅ **Single Responsibility**
- **Domain Entities**: Geschäftslogik
- **Infrastructure Models**: Datenbankschema
- **Mappers**: Übersetzung
- **Repositories**: Datenzugriff

## 7. Aktueller Implementierungsstand

### Domain Layer
**Vollständig implementiert:**
- ✅ **Entities**: Item, Delivery, Supplier, Order mit Geschäftslogik
- ✅ **Value Objects**: ArticleNumber, BatchNumber mit Validierung
- ✅ **Enums**: ItemStatus, DeliveryStatus für Typsicherheit
- ✅ **Exceptions**: Domain-spezifische Fehlerbehandlung
- ✅ **Repository Interfaces**: Abstrakte Verträge für Datenzugriff

### Application Layer
**Services implementiert:**
- ✅ **DeliveryService**: Lieferungs-Workflows und Status-Management
- ✅ **ItemService**: Artikel-Verwaltung und Sichtprüfung
- ✅ **SupplierService**: Lieferanten-Management mit find-or-create Pattern
- ✅ **DocumentService**: Dokumentenerstellung mit Template-System

### Infrastructure Layer
**Database-Implementierung:**
- ✅ **Models**: SQLAlchemy-Models für alle Entities
- ✅ **Repositories**: Sowohl Standard- als auch Domain-orientierte Implementierungen
- ✅ **Connection**: Robustes Datenbankverbindungs-Management
- 🔄 **Mappers**: Teilweise implementiert (Infrastructure → Domain)

### Presentation Layer
**Streamlit-basierte Admin-Interface:**
- ✅ **Views**: Delivery Management, Item Management, Document Generation
- ✅ **Popups**: Modal Dialoge für komplexe Operationen
- ✅ **Utils**: UI-spezifische Hilfsfunktionen
- ✅ **Main App**: Zentrale Streamlit-Anwendung

### Nächste Schritte für vollständige Clean Architecture
1. **Mapper-Schicht vervollständigen** für bidirektionale Entity ↔ Model Konvertierung
2. **Repository-Konsolidierung** zu einem einheitlichen Domain-orientierten Ansatz
3. **Use Case Layer** einführen für explizite Geschäftsabläufe
4. **Domain Events** für lose Kopplung zwischen Bounded Contexts

Die Architektur zeigt excellentes Software Engineering mit klarer Trennung der Verantwortlichkeiten und konsequenter Umsetzung der Clean Architecture Prinzipien!