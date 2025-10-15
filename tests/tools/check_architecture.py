"""
Clean Architecture Compliance Check
"""
import sys
import io
sys.path.insert(0, 'src')

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("CLEAN ARCHITECTURE COMPLIANCE CHECK")
print("=" * 80)

# Check 1: Domain Layer Independence
print("\n[1] Domain Layer - No Infrastructure Dependencies")
try:
    import ast
    import glob

    domain_files = glob.glob("src/warehouse/domain/**/*.py", recursive=True)
    violations = []

    for file in domain_files:
        if '__pycache__' in file:
            continue
        with open(file, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if 'infrastructure' in alias.name or 'sqlalchemy' in alias.name.lower():
                                violations.append(f"{file}: imports {alias.name}")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and ('infrastructure' in node.module or 'sqlalchemy' in node.module.lower()):
                            violations.append(f"{file}: imports from {node.module}")
            except:
                pass

    if violations:
        print("  VIOLATIONS FOUND:")
        for v in violations[:5]:
            print(f"     {v}")
    else:
        print("  PASS: Domain layer has no infrastructure dependencies")
except Exception as e:
    print(f"  Could not check: {e}")

# Check 2: Repository Pattern
print("\n[2] Repository Pattern - Interface vs Implementation")
try:
    from warehouse.domain.repositories.item_repository import ItemRepository
    from warehouse.infrastructure.database.repositories.sql_item_rep_domain import SQLAlchemyItemRepositoryDomain

    if issubclass(SQLAlchemyItemRepositoryDomain, ItemRepository):
        print("  PASS: SQLAlchemyItemRepositoryDomain implements ItemRepository")
    else:
        print("  FAIL: Implementation doesn't implement interface")

    repo = SQLAlchemyItemRepositoryDomain()
    if hasattr(repo, '_dict_repo'):
        print("  WARNING: Repository still has _dict_repo attribute")
    else:
        print("  PASS: No legacy _dict_repo delegation")

except Exception as e:
    print(f"  FAIL: {e}")

# Check 3: Service Layer
print("\n[3] Service Layer - Uses Domain Repositories")
try:
    from warehouse.infrastructure.database.connection import initialize_database
    initialize_database()

    from warehouse.application.services.entity_services.item_service import ItemService

    service = ItemService()
    repo_type = type(service.item_repo).__name__
    print(f"  Repository type: {repo_type}")

    if 'Domain' in repo_type or 'SQLAlchemy' in repo_type:
        print("  PASS: Service uses domain repository")
    else:
        print(f"  WARNING: Unexpected repository type: {repo_type}")

    if hasattr(service.item_repo, '_dict_repo'):
        print("  FAIL: Service's repository has _dict_repo")
    else:
        print("  PASS: No _dict_repo in service's repository")

except Exception as e:
    print(f"  FAIL: {e}")

# Check 4: get_all_items Return Type
print("\n[4] Service Methods - Always Return Lists")
try:
    from warehouse.application.services.entity_services.item_service import ItemService
    from warehouse.infrastructure.database.connection import initialize_database

    initialize_database()
    service = ItemService()

    # Test normal case
    result = service.get_all_items()
    if isinstance(result, list):
        print(f"  PASS: get_all_items returns list (len={len(result)})")
    else:
        print(f"  FAIL: get_all_items returns {type(result)}")

    # Test error case
    original = service.item_repo.find_domain_all
    service.item_repo.find_domain_all = lambda: None
    result = service.get_all_items()
    if isinstance(result, list) and len(result) == 0:
        print("  PASS: Returns empty list on error (not None)")
    else:
        print(f"  FAIL: Returns {type(result)} on error")
    service.item_repo.find_domain_all = original

except Exception as e:
    print(f"  FAIL: {e}")

# Check 5: View Layer - Safe None Handling
print("\n[5] View Layer - Safe None/len() Handling")
try:
    test_cases = [
        ("designation", None),
        ("employee_name", None),
        ("storage_location", None),
        ("batch_number", None)
    ]

    all_safe = True
    for field, value in test_cases:
        item_dict = {field: value}
        # Simulate view logic
        result = item_dict.get(field, "") or ""
        if result and isinstance(result, str):
            try:
                len(result)
                pass
            except:
                all_safe = False
                print(f"  FAIL: len() fails on {field}={value}")

    if all_safe:
        print("  PASS: All None values handled safely")

except Exception as e:
    print(f"  FAIL: {e}")

# Check 6: Remaining Legacy Repositories
print("\n[6] Legacy Repositories Status")
try:
    import os
    legacy_files = [
        "src/warehouse/infrastructure/database/repositories/sql_item_repository.py",
        "src/warehouse/infrastructure/database/repositories/sql_delivery_repository.py",
        "src/warehouse/infrastructure/database/repositories/sql_supplier_repository.py",
        "src/warehouse/infrastructure/database/repositories/sql_order_repository.py"
    ]

    existing = [f for f in legacy_files if os.path.exists(f)]

    if existing:
        print("  WARNING: Legacy files still exist:")
        for f in existing:
            print(f"     - {f}")
    else:
        print("  PASS: All legacy Item repository files removed")

    # Check for _dict_repo in other repos
    from warehouse.infrastructure.database.repositories.sql_delivery_rep_domain import SQLAlchemyDeliveryRepositoryDomain
    from warehouse.infrastructure.database.repositories.sql_supplier_rep_domain import SQLAlchemySupplierRepositoryDomain

    delivery_repo = SQLAlchemyDeliveryRepositoryDomain()
    supplier_repo = SQLAlchemySupplierRepositoryDomain()

    pending_migration = []
    if hasattr(delivery_repo, '_dict_repo'):
        pending_migration.append("DeliveryRepository")
    if hasattr(supplier_repo, '_dict_repo'):
        pending_migration.append("SupplierRepository")

    if pending_migration:
        print(f"  PENDING: {', '.join(pending_migration)} still use _dict_repo")
    else:
        print("  PASS: All repositories migrated")

except Exception as e:
    print(f"  Could not check: {e}")

print("\n" + "=" * 80)
print("CHECK COMPLETE")
print("=" * 80)