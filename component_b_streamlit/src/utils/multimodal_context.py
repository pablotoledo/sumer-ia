"""
Manejo real de contexto multimodal para agentes
"""

from pathlib import Path
from typing import List, Dict, Optional
import pypdf
import logging

logger = logging.getLogger(__name__)


class MultimodalContextBuilder:
    """
    Construye contexto enriquecido con contenido real de documentos
    """

    def __init__(self, max_chars_per_doc: int = 10000):
        self.max_chars_per_doc = max_chars_per_doc

    def build_context(
        self,
        segment: dict,
        uploaded_docs: List[Path]
    ) -> str:
        """
        Construye contexto multimodal funcional
        """
        context_parts = [
            "=== SEGMENT TO PROCESS ===",
            segment.get("text", ""),
            ""
        ]

        # Agregar metadata de segmentación
        if "topic_indicators" in segment:
            context_parts.extend([
                "=== SEGMENT CONTEXT ===",
                f"Main topics: {', '.join(segment['topic_indicators'])}",
                f"Semantic cluster: {segment.get('cluster_id', 'N/A')}",
                ""
            ])

        # Agregar contenido real de documentos
        if uploaded_docs:
            context_parts.append("=== REFERENCE DOCUMENTS ===")
            for doc_path in uploaded_docs:
                doc_content = self._extract_document_content(doc_path)
                if doc_content:
                    context_parts.extend([
                        f"\n--- {doc_path.name} ---",
                        doc_content,
                        ""
                    ])

        return "\n".join(context_parts)

    def _extract_document_content(self, doc_path: Path) -> str:
        """
        Extrae contenido de documento según tipo
        """
        if not doc_path.exists():
            logger.warning(f"Document not found: {doc_path}")
            return ""

        try:
            if doc_path.suffix.lower() == '.pdf':
                return self._extract_pdf(doc_path)
            elif doc_path.suffix.lower() in ['.txt', '.md']:
                return self._extract_text_file(doc_path)
            elif doc_path.suffix.lower() in ['.docx']:
                return self._extract_docx(doc_path)
            else:
                logger.warning(f"Unsupported file type: {doc_path.suffix}")
                return f"[Tipo de archivo no soportado: {doc_path.suffix}]"
        except Exception as e:
            logger.error(f"Error extracting content from {doc_path}: {e}")
            return f"[Error leyendo {doc_path.name}: {str(e)}]"

    def _extract_pdf(self, pdf_path: Path) -> str:
        """
        Extrae texto de PDF usando pypdf
        """
        try:
            reader = pypdf.PdfReader(pdf_path)
            text_parts = []

            # Verificar si el PDF tiene contenido
            if len(reader.pages) == 0:
                return "[PDF vacío o corrupto]"

            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text.strip():  # Solo agregar páginas con contenido
                        text_parts.append(f"[Page {page_num}]\n{text.strip()}")

                    # Limitar tamaño total
                    full_text = "\n\n".join(text_parts)
                    if len(full_text) > self.max_chars_per_doc:
                        return full_text[:self.max_chars_per_doc] + "\n\n[... contenido truncado por límite de tamaño]"

                except Exception as e:
                    logger.warning(f"Error extracting page {page_num} from {pdf_path}: {e}")
                    text_parts.append(f"[Page {page_num}] - Error extrayendo contenido")

            if not text_parts:
                return "[PDF sin contenido extraíble - posiblemente imágenes o texto protegido]"

            return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            return f"[Error extrayendo PDF: {str(e)}]"

    def _extract_text_file(self, file_path: Path) -> str:
        """
        Extrae contenido de archivos de texto plano
        """
        try:
            # Intentar diferentes encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']

            for encoding in encodings:
                try:
                    content = file_path.read_text(encoding=encoding)
                    # Limitar tamaño
                    if len(content) > self.max_chars_per_doc:
                        content = content[:self.max_chars_per_doc] + "\n\n[... contenido truncado por límite de tamaño]"
                    return content
                except UnicodeDecodeError:
                    continue

            # Si todos los encodings fallan
            return f"[Error: No se pudo decodificar el archivo {file_path.name}]"

        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            return f"[Error leyendo archivo de texto: {str(e)}]"

    def _extract_docx(self, docx_path: Path) -> str:
        """
        Extrae contenido de archivos DOCX (requiere python-docx)
        """
        try:
            # Intentar importar python-docx
            try:
                from docx import Document
            except ImportError:
                return f"[Para leer archivos .docx, instala: pip install python-docx]"

            doc = Document(docx_path)
            paragraphs = []

            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text.strip())

            content = "\n\n".join(paragraphs)

            # Limitar tamaño
            if len(content) > self.max_chars_per_doc:
                content = content[:self.max_chars_per_doc] + "\n\n[... contenido truncado por límite de tamaño]"

            return content if content else "[Documento DOCX sin contenido de texto]"

        except Exception as e:
            logger.error(f"Error reading DOCX {docx_path}: {e}")
            return f"[Error extrayendo DOCX: {str(e)}]"

    def get_document_summary(self, doc_path: Path) -> Dict[str, any]:
        """
        Obtiene un resumen del documento sin extraer todo el contenido
        """
        if not doc_path.exists():
            return {"error": "File not found", "path": str(doc_path)}

        try:
            stat = doc_path.stat()
            summary = {
                "name": doc_path.name,
                "path": str(doc_path),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024*1024), 2),
                "extension": doc_path.suffix.lower(),
                "supported": doc_path.suffix.lower() in ['.pdf', '.txt', '.md', '.docx']
            }

            # Información específica por tipo
            if doc_path.suffix.lower() == '.pdf':
                try:
                    reader = pypdf.PdfReader(doc_path)
                    summary["pages"] = len(reader.pages)
                    summary["metadata"] = reader.metadata
                except:
                    summary["pages"] = "unknown"
                    summary["metadata"] = {}

            return summary

        except Exception as e:
            return {"error": str(e), "path": str(doc_path)}

    def validate_documents(self, doc_paths: List[Path]) -> Dict[str, List[Path]]:
        """
        Valida una lista de documentos y los categoriza
        """
        result = {
            "valid": [],
            "invalid": [],
            "unsupported": [],
            "missing": []
        }

        for doc_path in doc_paths:
            if not doc_path.exists():
                result["missing"].append(doc_path)
            elif doc_path.suffix.lower() not in ['.pdf', '.txt', '.md', '.docx']:
                result["unsupported"].append(doc_path)
            else:
                try:
                    # Intentar extraer una muestra pequeña
                    test_content = self._extract_document_content(doc_path)
                    if test_content and not test_content.startswith("[Error"):
                        result["valid"].append(doc_path)
                    else:
                        result["invalid"].append(doc_path)
                except:
                    result["invalid"].append(doc_path)

        return result


# Funciones de conveniencia para usar desde otros módulos
def extract_pdf_content(pdf_path: Path, max_chars: int = 10000) -> str:
    """Función de conveniencia para extraer contenido de PDF"""
    builder = MultimodalContextBuilder(max_chars_per_doc=max_chars)
    return builder._extract_pdf(pdf_path)


def extract_text_content(file_path: Path, max_chars: int = 10000) -> str:
    """Función de conveniencia para extraer contenido de texto"""
    builder = MultimodalContextBuilder(max_chars_per_doc=max_chars)
    return builder._extract_text_file(file_path)


def build_multimodal_context(segment: dict, documents: List[Path]) -> str:
    """Función de conveniencia para construir contexto multimodal"""
    builder = MultimodalContextBuilder()
    return builder.build_context(segment, documents)


# Exportar clases y funciones principales
__all__ = [
    "MultimodalContextBuilder",
    "extract_pdf_content",
    "extract_text_content",
    "build_multimodal_context"
]