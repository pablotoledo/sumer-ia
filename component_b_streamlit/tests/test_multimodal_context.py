"""
Tests para MultimodalContextBuilder
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.multimodal_context import (
    MultimodalContextBuilder,
    extract_pdf_content,
    extract_text_content,
    build_multimodal_context
)


@pytest.fixture
def temp_text_file():
    """Crea un archivo temporal de texto para testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("Este es un archivo de prueba.\nContiene múltiples líneas.\n¡Con contenido en español!")
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_markdown_file():
    """Crea un archivo temporal markdown para testing"""
    content = """# Test Document

## Section 1
This is a test markdown document.

## Section 2
- Item 1
- Item 2
- Item 3

**Bold text** and *italic text*.
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


def test_multimodal_context_builder_creation():
    """Verifica que el builder se puede crear correctamente"""
    builder = MultimodalContextBuilder()
    assert builder.max_chars_per_doc == 10000

    # Con parámetros personalizados
    builder2 = MultimodalContextBuilder(max_chars_per_doc=5000)
    assert builder2.max_chars_per_doc == 5000


def test_extract_text_file(temp_text_file):
    """Verifica extracción de archivos de texto"""
    builder = MultimodalContextBuilder()
    content = builder._extract_text_file(temp_text_file)

    assert "archivo de prueba" in content
    assert "múltiples líneas" in content
    assert "español" in content


def test_extract_markdown_file(temp_markdown_file):
    """Verifica extracción de archivos markdown"""
    builder = MultimodalContextBuilder()
    content = builder._extract_text_file(temp_markdown_file)

    assert "# Test Document" in content
    assert "Section 1" in content
    assert "**Bold text**" in content


def test_extract_nonexistent_file():
    """Verifica manejo de archivos inexistentes"""
    builder = MultimodalContextBuilder()
    fake_path = Path("/path/that/does/not/exist.txt")

    content = builder._extract_document_content(fake_path)
    assert content == ""


def test_extract_unsupported_file():
    """Verifica manejo de tipos de archivo no soportados"""
    builder = MultimodalContextBuilder()

    # Crear archivo temporal con extensión no soportada
    with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
        temp_path = Path(f.name)

    try:
        content = builder._extract_document_content(temp_path)
        assert "no soportado" in content.lower()
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_build_context_with_segment():
    """Verifica construcción de contexto con segmento"""
    builder = MultimodalContextBuilder()

    segment = {
        "text": "This is a test segment",
        "topic_indicators": ["test", "segment"],
        "cluster_id": "cluster_1"
    }

    context = builder.build_context(segment, [])

    assert "=== SEGMENT TO PROCESS ===" in context
    assert "This is a test segment" in context
    assert "=== SEGMENT CONTEXT ===" in context
    assert "test, segment" in context
    assert "cluster_1" in context


def test_build_context_with_documents(temp_text_file):
    """Verifica construcción de contexto con documentos"""
    builder = MultimodalContextBuilder()

    segment = {"text": "Test segment"}

    context = builder.build_context(segment, [temp_text_file])

    assert "=== SEGMENT TO PROCESS ===" in context
    assert "=== REFERENCE DOCUMENTS ===" in context
    assert temp_text_file.name in context
    assert "archivo de prueba" in context


def test_document_summary(temp_text_file):
    """Verifica generación de resumen de documento"""
    builder = MultimodalContextBuilder()

    summary = builder.get_document_summary(temp_text_file)

    assert summary["name"] == temp_text_file.name
    assert summary["extension"] == ".txt"
    assert summary["supported"] is True
    assert summary["size_bytes"] > 0


def test_validate_documents(temp_text_file, temp_markdown_file):
    """Verifica validación de documentos"""
    builder = MultimodalContextBuilder()

    # Crear archivo inexistente
    missing_file = Path("/fake/path/missing.txt")

    # Crear archivo no soportado
    with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
        unsupported_file = Path(f.name)

    try:
        doc_paths = [temp_text_file, temp_markdown_file, missing_file, unsupported_file]
        validation = builder.validate_documents(doc_paths)

        assert temp_text_file in validation["valid"]
        assert temp_markdown_file in validation["valid"]
        assert missing_file in validation["missing"]
        assert unsupported_file in validation["unsupported"]

    finally:
        if unsupported_file.exists():
            unsupported_file.unlink()


def test_content_size_limiting():
    """Verifica que el contenido se limita según max_chars_per_doc"""
    builder = MultimodalContextBuilder(max_chars_per_doc=50)

    # Crear archivo con contenido largo
    long_content = "A" * 1000  # 1000 caracteres
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(long_content)
        temp_path = Path(f.name)

    try:
        content = builder._extract_text_file(temp_path)
        assert len(content) <= 100  # Debe ser limitado + mensaje de truncado
        assert "truncado" in content

    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_convenience_functions(temp_text_file):
    """Verifica que las funciones de conveniencia funcionan"""

    # Test extract_text_content
    content = extract_text_content(temp_text_file)
    assert "archivo de prueba" in content

    # Test build_multimodal_context
    segment = {"text": "Test"}
    context = build_multimodal_context(segment, [temp_text_file])
    assert "=== SEGMENT TO PROCESS ===" in context


def test_encoding_handling():
    """Verifica manejo de diferentes encodings"""
    builder = MultimodalContextBuilder()

    # Crear archivo con caracteres especiales
    special_content = "Contenido con ñ, ü, é, ç, और हिंदी"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(special_content)
        temp_path = Path(f.name)

    try:
        content = builder._extract_text_file(temp_path)
        assert "Contenido con ñ" in content

    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_empty_file_handling():
    """Verifica manejo de archivos vacíos"""
    builder = MultimodalContextBuilder()

    # Crear archivo vacío
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        temp_path = Path(f.name)

    try:
        content = builder._extract_text_file(temp_path)
        assert isinstance(content, str)
        assert len(content.strip()) == 0

    finally:
        if temp_path.exists():
            temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])