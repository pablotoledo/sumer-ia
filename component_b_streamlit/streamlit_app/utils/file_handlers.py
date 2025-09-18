"""
File Handlers
=============

Utilidades para manejo de archivos y conversiones.
"""

import tempfile
import os
from pathlib import Path
from typing import List, Optional, Tuple, Any, Dict
import mimetypes
import zipfile
from datetime import datetime

def save_uploaded_file(uploaded_file, target_dir: str = None) -> str:
    """
    Guarda un archivo subido de Streamlit a disco.
    
    Args:
        uploaded_file: Archivo subido de Streamlit
        target_dir: Directorio destino (opcional)
    
    Returns:
        Ruta del archivo guardado
    """
    
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, uploaded_file.name)
    else:
        # Usar directorio temporal
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, uploaded_file.name)
    
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getvalue())
    
    return file_path

def create_temp_file(content: str, suffix: str = ".txt") -> str:
    """
    Crea un archivo temporal con contenido específico.
    
    Args:
        content: Contenido del archivo
        suffix: Extensión del archivo
    
    Returns:
        Ruta del archivo temporal
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as f:
        f.write(content)
        return f.name

def create_temp_binary_file(content: bytes, suffix: str = ".bin") -> str:
    """
    Crea un archivo temporal con contenido binario.
    
    Args:
        content: Contenido binario del archivo
        suffix: Extensión del archivo
    
    Returns:
        Ruta del archivo temporal
    """
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as f:
        f.write(content)
        return f.name

def cleanup_temp_files(file_paths: List[str]) -> Tuple[int, List[str]]:
    """
    Limpia archivos temporales.
    
    Args:
        file_paths: Lista de rutas de archivos a eliminar
    
    Returns:
        Tuple (archivos_eliminados, errores)
    """
    
    deleted_count = 0
    errors = []
    
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                deleted_count += 1
        except Exception as e:
            errors.append(f"Error eliminando {file_path}: {e}")
    
    return deleted_count, errors

def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Obtiene información detallada de un archivo.
    
    Args:
        file_path: Ruta del archivo
    
    Returns:
        Diccionario con información del archivo
    """
    
    if not os.path.exists(file_path):
        return {'error': 'Archivo no existe'}
    
    path_obj = Path(file_path)
    stat = path_obj.stat()
    
    # Detectar tipo MIME
    mime_type, _ = mimetypes.guess_type(file_path)
    
    return {
        'name': path_obj.name,
        'size_bytes': stat.st_size,
        'size_mb': stat.st_size / (1024 * 1024),
        'extension': path_obj.suffix,
        'mime_type': mime_type,
        'created': datetime.fromtimestamp(stat.st_ctime),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'is_text': mime_type and mime_type.startswith('text/'),
        'is_image': mime_type and mime_type.startswith('image/'),
        'is_pdf': mime_type == 'application/pdf'
    }

def read_text_file_safe(file_path: str, encoding: str = 'utf-8') -> Tuple[bool, str]:
    """
    Lee un archivo de texto de forma segura.
    
    Args:
        file_path: Ruta del archivo
        encoding: Codificación a usar
    
    Returns:
        Tuple (éxito, contenido_o_error)
    """
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        return True, content
    
    except UnicodeDecodeError:
        try:
            # Intentar con latin-1 como fallback
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            return True, content
        except Exception as e:
            return False, f"Error de codificación: {e}"
    
    except Exception as e:
        return False, f"Error leyendo archivo: {e}"

def create_download_package(files: List[Tuple[str, str]], package_name: str = "results") -> str:
    """
    Crea un paquete ZIP con múltiples archivos.
    
    Args:
        files: Lista de tuplas (contenido, nombre_archivo)
        package_name: Nombre base del paquete
    
    Returns:
        Ruta del archivo ZIP creado
    """
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = f"{tempfile.gettempdir()}/{package_name}_{timestamp}.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for content, filename in files:
            zipf.writestr(filename, content)
    
    return zip_path

def generate_filename(base_name: str, extension: str = "txt") -> str:
    """
    Genera un nombre de archivo único con timestamp.
    
    Args:
        base_name: Nombre base del archivo
        extension: Extensión (sin punto)
    
    Returns:
        Nombre de archivo único
    """
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_base = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).strip()
    clean_base = clean_base.replace(' ', '_')
    
    return f"{clean_base}_{timestamp}.{extension}"

def extract_text_from_pdf(file_path: str) -> Tuple[bool, str]:
    """
    Extrae texto de un archivo PDF.
    
    Args:
        file_path: Ruta del archivo PDF
    
    Returns:
        Tuple (éxito, texto_extraído_o_error)
    """
    
    try:
        import PyPDF2
        
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        return True, text.strip()
    
    except ImportError:
        return False, "PyPDF2 no está instalado. Instala con: pip install PyPDF2"
    
    except Exception as e:
        return False, f"Error extrayendo texto del PDF: {e}"

def process_multimodal_files(file_paths: List[str]) -> Dict[str, Any]:
    """
    Procesa archivos multimodales y genera contexto.
    
    Args:
        file_paths: Lista de rutas de archivos
    
    Returns:
        Diccionario con información procesada
    """
    
    result = {
        'text_files': [],
        'pdf_files': [],
        'image_files': [],
        'errors': [],
        'total_text_content': '',
        'file_summaries': []
    }
    
    for file_path in file_paths:
        try:
            file_info = get_file_info(file_path)
            
            if file_info.get('error'):
                result['errors'].append(f"{file_path}: {file_info['error']}")
                continue
            
            if file_info['is_text']:
                success, content = read_text_file_safe(file_path)
                if success:
                    result['text_files'].append({
                        'path': file_path,
                        'name': file_info['name'],
                        'content': content,
                        'word_count': len(content.split())
                    })
                    result['total_text_content'] += f"\n--- {file_info['name']} ---\n{content}\n"
                else:
                    result['errors'].append(f"{file_path}: {content}")
            
            elif file_info['is_pdf']:
                success, content = extract_text_from_pdf(file_path)
                if success:
                    result['pdf_files'].append({
                        'path': file_path,
                        'name': file_info['name'],
                        'content': content,
                        'word_count': len(content.split())
                    })
                    result['total_text_content'] += f"\n--- {file_info['name']} (PDF) ---\n{content}\n"
                else:
                    result['errors'].append(f"{file_path}: {content}")
            
            elif file_info['is_image']:
                result['image_files'].append({
                    'path': file_path,
                    'name': file_info['name'],
                    'size_mb': file_info['size_mb']
                })
            
            # Crear resumen del archivo
            result['file_summaries'].append({
                'name': file_info['name'],
                'type': 'text' if file_info['is_text'] else 'pdf' if file_info['is_pdf'] else 'image',
                'size_mb': file_info['size_mb'],
                'processed': file_info['is_text'] or file_info['is_pdf']
            })
        
        except Exception as e:
            result['errors'].append(f"Error procesando {file_path}: {e}")
    
    return result

def format_file_size(size_bytes: int) -> str:
    """
    Formatea el tamaño de archivo en formato legible.
    
    Args:
        size_bytes: Tamaño en bytes
    
    Returns:
        Tamaño formateado (ej: "1.5 MB")
    """
    
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def sanitize_filename(filename: str) -> str:
    """
    Sanitiza un nombre de archivo removiendo caracteres problemáticos.
    
    Args:
        filename: Nombre de archivo original
    
    Returns:
        Nombre de archivo sanitizado
    """
    
    # Caracteres no permitidos en nombres de archivo
    invalid_chars = '<>:"/\\|?*'
    
    # Reemplazar caracteres inválidos
    sanitized = "".join(c if c not in invalid_chars else "_" for c in filename)
    
    # Remover espacios al inicio/final y puntos al final
    sanitized = sanitized.strip().rstrip('.')
    
    # Asegurar que no esté vacío
    if not sanitized:
        sanitized = "file"
    
    # Limitar longitud
    if len(sanitized) > 200:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:200-len(ext)] + ext
    
    return sanitized

def create_backup_config(config_path: str) -> str:
    """
    Crea una copia de seguridad de un archivo de configuración.
    
    Args:
        config_path: Ruta del archivo de configuración
    
    Returns:
        Ruta del archivo de backup creado
    """
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Archivo de configuración no existe: {config_path}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{config_path}.backup_{timestamp}"
    
    with open(config_path, 'r', encoding='utf-8') as src:
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    
    return backup_path

def count_lines_and_words(text: str) -> Dict[str, int]:
    """
    Cuenta líneas y palabras en un texto.
    
    Args:
        text: Texto a analizar
    
    Returns:
        Diccionario con estadísticas
    """
    
    lines = text.split('\n')
    words = text.split()
    
    # Estadísticas detalladas
    non_empty_lines = [line for line in lines if line.strip()]
    
    return {
        'total_lines': len(lines),
        'non_empty_lines': len(non_empty_lines),
        'total_words': len(words),
        'total_chars': len(text),
        'chars_no_spaces': len(text.replace(' ', '')),
        'average_words_per_line': len(words) / len(non_empty_lines) if non_empty_lines else 0
    }