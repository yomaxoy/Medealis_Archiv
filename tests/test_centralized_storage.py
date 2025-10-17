"""
Test Suite für das zentralisierte Storage-System

Testet alle neuen Storage-Komponenten:
- StorageContext
- PathResolver
- StorageValidator
- DocumentStorageService
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# Import storage components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from warehouse.application.services.document_storage import (
    StorageContext,
    StorageContextData,
    PathResolver,
    PathResult,
    StorageValidator,
    ValidationResult,
    ValidationLevel,
    DocumentStorageService,
    StorageResult,
    validate_storage_setup
)


class TestStorageContext:
    """Tests für StorageContext - zentrale Datenkontext-Verwaltung."""

    def test_get_complete_storage_context_basic(self):
        """Test basic context creation."""
        context = StorageContext()

        result = context.get_complete_storage_context(
            batch_number="P-123456789012",
            delivery_number="DEL-001"
        )

        assert isinstance(result, StorageContextData)
        assert result.batch_number == "P-123456789012"
        assert result.delivery_number == "DEL-001"
        assert result.is_complete_for_storage()

    def test_context_validation_missing_required(self):
        """Test validation with missing required fields."""
        context = StorageContext()

        result = context.get_complete_storage_context(
            batch_number="",  # Missing required field
            delivery_number="DEL-001"
        )

        assert not result.is_complete_for_storage()
        issues = result.get_validation_issues()
        assert any("batch_number ist erforderlich" in issue for issue in issues)

    def test_supplier_normalization(self):
        """Test supplier name normalization."""
        context = StorageContext()

        result = context.get_complete_storage_context(
            batch_number="P-123456789012",
            delivery_number="DEL-001",
            supplier_name="primec"
        )

        assert result.supplier_normalized == "Primec"

    def test_manufacturer_determination(self):
        """Test manufacturer determination from article number."""
        context = StorageContext()

        result = context.get_complete_storage_context(
            batch_number="P-123456789012",
            delivery_number="DEL-001",
            article_number="CT0001"
        )

        assert result.manufacturer == "C-Tech"

    def test_completeness_score_calculation(self):
        """Test completeness score calculation."""
        context = StorageContext()

        # Full context
        full_result = context.get_complete_storage_context(
            batch_number="P-123456789012",
            delivery_number="DEL-001",
            article_number="CT0001",
            supplier_name="Primec"
        )

        # Minimal context
        minimal_result = context.get_complete_storage_context(
            batch_number="P-123456789012",
            delivery_number="DEL-001"
        )

        assert full_result.completeness_score > minimal_result.completeness_score


class TestPathResolver:
    """Tests für PathResolver - einheitliche Pfad-Auflösung."""

    @pytest.fixture
    def temp_base_path(self):
        """Temporäres Verzeichnis für Tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_path_resolver(self, temp_base_path):
        """PathResolver mit temporärem Basis-Pfad."""
        resolver = PathResolver()
        resolver._base_storage_path = temp_base_path
        return resolver

    def test_resolve_storage_path_success(self, mock_path_resolver):
        """Test successful path resolution."""
        context = StorageContextData(
            batch_number="P-123456789012",
            delivery_number="DEL-001",
            article_number="CT0001",
            supplier_normalized="Primec",
            manufacturer="C-Tech"
        )

        result = mock_path_resolver.resolve_storage_path(context, create_folders=True)

        assert result.success
        assert result.path.exists()
        assert "Primec" in str(result.path)
        assert "C-Tech" in str(result.path)

    def test_resolve_storage_path_incomplete_context(self, mock_path_resolver):
        """Test path resolution with incomplete context."""
        context = StorageContextData(
            batch_number="",  # Missing required
            delivery_number="DEL-001"
        )

        result = mock_path_resolver.resolve_storage_path(context)

        assert not result.success
        assert "Incomplete storage context" in result.error

    def test_clean_path_component(self, mock_path_resolver):
        """Test path component cleaning."""
        # Test dangerous characters
        cleaned = mock_path_resolver._clean_path_component("Test/Path\\With:Bad*Chars")
        assert "/" not in cleaned
        assert "\\" not in cleaned
        assert ":" not in cleaned
        assert "*" not in cleaned

        # Test empty input
        cleaned_empty = mock_path_resolver._clean_path_component("")
        assert cleaned_empty == "Unknown"

    def test_move_file(self, mock_path_resolver, temp_base_path):
        """Test file moving functionality."""
        # Erstelle Test-Datei
        test_content = b"Test content"
        temp_file = temp_base_path / "temp_test.pdf"
        temp_file.write_bytes(test_content)

        # Erstelle Kontext
        context = StorageContextData(
            batch_number="P-123456789012",
            delivery_number="DEL-001",
            supplier_normalized="Test",
            manufacturer="Test"
        )

        # Verschiebe Datei
        result = mock_path_resolver.move_file(temp_file, context, "moved_test.pdf")

        assert result.success
        assert result.path.name == "moved_test.pdf"
        assert result.path.read_bytes() == test_content
        assert not temp_file.exists()


class TestStorageValidator:
    """Tests für StorageValidator - Validierung und Sicherheit."""

    @pytest.fixture
    def validator(self):
        return StorageValidator(ValidationLevel.STANDARD)

    def test_validate_document_data_success(self, validator):
        """Test successful document validation."""
        test_data = b"PDF content here"
        result = validator.validate_document_data(test_data, "test.pdf")

        # Should not fail on basic validation
        assert len(result.errors) == 0  # Basic validation should pass

    def test_validate_document_data_empty(self, validator):
        """Test validation with empty document."""
        result = validator.validate_document_data(b"", "test.pdf")

        assert not result.is_valid
        assert any("empty" in error.lower() for error in result.errors)

    def test_validate_document_data_oversized(self, validator):
        """Test validation with oversized document."""
        # Create oversized data
        large_data = b"x" * (validator.max_file_size + 1)
        result = validator.validate_document_data(large_data, "test.pdf")

        assert not result.is_valid
        assert any("exceeds limit" in error for error in result.errors)

    def test_sanitize_filename(self, validator):
        """Test filename sanitization."""
        dangerous_name = "test<file>name:with*bad|chars.pdf"
        safe_name, warnings = validator.sanitize_filename(dangerous_name)

        assert "<" not in safe_name
        assert ">" not in safe_name
        assert ":" not in safe_name
        assert "*" not in safe_name
        assert "|" not in safe_name
        assert len(warnings) > 0

    def test_validate_storage_context(self, validator):
        """Test storage context validation."""
        # Valid context
        valid_context = StorageContextData(
            batch_number="P-123456789012",
            delivery_number="DEL-001"
        )
        result = validator.validate_storage_context(valid_context)
        assert result.is_valid

        # Invalid context
        invalid_context = StorageContextData(
            batch_number="",
            delivery_number=""
        )
        result = validator.validate_storage_context(invalid_context)
        assert not result.is_valid

    def test_security_risk_detection(self, validator):
        """Test security risk detection."""
        # Test dangerous filename
        result = validator._validate_filename("../../../etc/passwd")
        risks = [risk for risk, _ in result.security_risks]
        assert any(risk.value in ["high", "critical"] for risk in risks)


class TestDocumentStorageService:
    """Tests für DocumentStorageService - zentrale Storage-API."""

    @pytest.fixture
    def temp_base_path(self):
        """Temporäres Verzeichnis für Tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_storage_service(self, temp_base_path):
        """DocumentStorageService mit temporären Pfaden."""
        service = DocumentStorageService()
        service.path_resolver._base_storage_path = temp_base_path
        return service

    def test_save_document_success(self, mock_storage_service):
        """Test successful document saving."""
        test_data = b"PDF test content"

        result = mock_storage_service.save_document(
            document_data=test_data,
            document_name="test_document.pdf",
            document_type="PDB",
            batch_number="P-123456789012",
            delivery_number="DEL-001"
        )

        assert isinstance(result, StorageResult)
        assert result.success
        assert result.file_path is not None
        assert Path(result.file_path).exists()

    def test_save_document_invalid_context(self, mock_storage_service):
        """Test document saving with invalid context."""
        result = mock_storage_service.save_document(
            document_data=b"test",
            document_name="test.pdf",
            document_type="PDB",
            batch_number="",  # Invalid
            delivery_number=""  # Invalid
        )

        assert isinstance(result, StorageResult)
        assert not result.success
        assert "Invalid storage context" in result.error

    def test_get_document_path(self, mock_storage_service):
        """Test document path resolution."""
        path, warnings = mock_storage_service.get_document_path(
            batch_number="P-123456789012",
            delivery_number="DEL-001",
            create_folders=True
        )

        assert isinstance(path, Path)
        assert path.exists()
        assert isinstance(warnings, list)

    def test_move_temp_document(self, mock_storage_service, temp_base_path):
        """Test temporary document moving."""
        # Erstelle temporäre Datei
        temp_file = temp_base_path / "temp_doc.pdf"
        test_content = b"Temporary document content"
        temp_file.write_bytes(test_content)

        result = mock_storage_service.move_temp_document(
            temp_file_path=str(temp_file),
            filename="final_document.pdf",
            batch_number="P-123456789012",
            delivery_number="DEL-001"
        )

        assert result.success
        assert Path(result.file_path).exists()
        assert Path(result.file_path).read_bytes() == test_content


class TestIntegration:
    """Integrationstests für das gesamte Storage-System."""

    def test_validate_storage_setup(self):
        """Test storage system setup validation."""
        results = validate_storage_setup()

        assert isinstance(results, dict)
        assert 'storage_context' in results
        assert 'path_resolver' in results
        assert 'storage_validator' in results
        assert 'all_components_working' in results

        # Check that basic components work
        assert results['storage_context'] is True
        assert results['path_resolver'] is True
        assert results['storage_validator'] is True

    @pytest.fixture
    def temp_storage_system(self):
        """Vollständiges Storage-System mit temporären Pfaden."""
        temp_dir = tempfile.mkdtemp()
        base_path = Path(temp_dir)

        # Setup service with temp paths
        service = DocumentStorageService()
        service.path_resolver._base_storage_path = base_path
        service.path_resolver._document_output_path = base_path / "documents"
        service.path_resolver._temp_path = base_path / "temp"

        yield service, base_path
        shutil.rmtree(temp_dir)

    def test_full_document_workflow(self, temp_storage_system):
        """Test kompletten Dokument-Workflow."""
        service, base_path = temp_storage_system

        # 1. Dokument speichern
        test_document = b"Complete workflow test document content"

        save_result = service.save_document(
            document_data=test_document,
            document_name="workflow_test.pdf",
            document_type="test",
            batch_number="P-123456789012",
            delivery_number="DEL-001",
            article_number="CT0001",
            supplier_name="Primec"
        )

        assert save_result.success
        assert save_result.metadata['context_completeness'] > 0.8

        # 2. Pfad abrufen
        path, warnings = service.get_document_path(
            batch_number="P-123456789012",
            delivery_number="DEL-001"
        )

        assert path.exists()
        assert str(save_result.storage_folder) == str(path)

        # 3. Statistiken abrufen
        stats = service.get_storage_statistics()
        assert stats['base_storage_exists'] is True
        assert 'storage_file_count' in stats

    def test_error_handling_and_recovery(self, temp_storage_system):
        """Test Fehlerbehandlung und Recovery."""
        service, base_path = temp_storage_system

        # Test mit unvollständigen Daten
        result = service.save_document(
            document_data=b"test",
            document_name="error_test.pdf",
            document_type="test",
            batch_number="INVALID",  # Too short
            delivery_number=""  # Missing
        )

        # Should handle gracefully
        assert not result.success
        assert result.error is not None
        assert len(result.warnings) >= 0  # May have warnings


if __name__ == "__main__":
    # Run basic tests if called directly
    print("Testing centralized storage system...")

    # Test setup validation
    setup_results = validate_storage_setup()
    print(f"Setup validation: {setup_results}")

    # Run pytest if available
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic tests...")

        # Basic test without pytest
        try:
            context = StorageContext()
            test_context = context.get_complete_storage_context(
                batch_number="TEST-123",
                delivery_number="TEST-DEL"
            )
            print(f"StorageContext test: {'PASS' if test_context.batch_number == 'TEST-123' else 'FAIL'}")

        except Exception as e:
            print(f"Basic test failed: {e}")

    print("Test run completed.")