"""
Agent Interface
===============

Interfaz para interactuar con el sistema FastAgent desde Streamlit.
Maneja la comunicación asíncrona y el procesamiento de contenido.
"""

import asyncio
import streamlit as st
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import tempfile
import os

class AgentInterface:
    """Interfaz para comunicarse con FastAgent."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self._fast_agent = None
        self._meeting_agent = None
    
    async def _initialize_agents(self):
        """Inicializa los agentes FastAgent."""
        try:
            # Importar módulos FastAgent desde la estructura src/
            from src.agents.specialized_agents import fast as specialized_fast
            from src.enhanced_agents import meeting_fast, adaptive_segment_content
            from robust_main import RateLimitHandler
            
            self._fast_agent = specialized_fast
            self._meeting_agent = meeting_fast
            self._adaptive_segment = adaptive_segment_content
            self._rate_limit_handler = RateLimitHandler(
                max_retries=3,
                base_delay=60
            )
            
            return True
            
        except Exception as e:
            st.error(f"Error inicializando agentes: {e}")
            return False
    
    async def process_content(
        self,
        content: str,
        documents: Optional[List[str]] = None,
        progress_callback=None,
        agent_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa contenido usando FastAgent.
        
        Args:
            content: Texto STT a procesar
            documents: Lista de rutas a documentos adicionales
            progress_callback: Función para reportar progreso
            agent_override: Agente específico a usar (opcional)
        
        Returns:
            Dict con resultado del procesamiento
        """
        
        if not await self._initialize_agents():
            raise Exception("No se pudieron inicializar los agentes")
        
        try:
            # Paso 1: Segmentación adaptativa
            if progress_callback:
                progress_callback("Analizando formato del contenido...", 0.1)
            
            segments, recommended_agent = self._adaptive_segment(content)
            
            # Usar agent_override si se especifica
            if agent_override:
                recommended_agent = agent_override
            
            if progress_callback:
                progress_callback(f"Usando agente: {recommended_agent}", 0.2)
                progress_callback(f"Procesando {len(segments)} segmentos...", 0.3)
            
            # Paso 2: Configurar contexto multimodal
            multimodal_context = self._prepare_multimodal_context(documents)
            
            # Paso 3: Procesamiento por segmentos con rate limiting
            processed_segments = []
            total_segments = len(segments)
            
            # Seleccionar el agente FastAgent apropiado
            if recommended_agent == "meeting_processor":
                agent = self._meeting_agent
            else:
                agent = self._fast_agent
            
            for i, segment in enumerate(segments):
                if progress_callback:
                    progress = 0.3 + (0.6 * (i + 1) / total_segments)
                    progress_callback(f"Procesando segmento {i + 1}/{total_segments}...", progress)
                
                # Procesar segmento con retry automático
                try:
                    async with agent.run() as agent_instance:
                        segment_context = f"""
Segmento {i + 1} de {total_segments}:

{segment}

{multimodal_context}
"""
                        
                        # Para agentes especializados, usar la cadena de procesamiento
                        if recommended_agent == "simple_processor":
                            result = await self._rate_limit_handler.execute_with_retry(
                                agent_instance.content_pipeline.send,
                                segment_context
                            )
                        else:
                            # Para meeting_processor mantener comportamiento original
                            result = await self._rate_limit_handler.execute_with_retry(
                                agent_instance.simple_processor.send,
                                segment_context
                            )
                        
                        processed_segments.append({
                            'segment_number': i + 1,
                            'original_content': segment,
                            'processed_content': result,
                            'agent_used': recommended_agent
                        })
                
                except Exception as e:
                    st.warning(f"Error procesando segmento {i + 1}: {e}")
                    processed_segments.append({
                        'segment_number': i + 1,
                        'original_content': segment,
                        'processed_content': f"Error procesando segmento: {e}",
                        'agent_used': recommended_agent,
                        'error': True
                    })
            
            if progress_callback:
                progress_callback("Generando documento final...", 0.9)
            
            # Paso 4: Ensamblar resultado final
            final_document = self._assemble_final_document(
                processed_segments,
                content,
                documents
            )
            
            if progress_callback:
                progress_callback("¡Procesamiento completado!", 1.0)
            
            return {
                'success': True,
                'document': final_document,
                'segments': processed_segments,
                'agent_used': recommended_agent,
                'total_segments': total_segments,
                'retry_count': self._rate_limit_handler.retry_count,
                'original_content': content,
                'multimodal_files': documents or []
            }
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error: {e}", 1.0)
            
            return {
                'success': False,
                'error': str(e),
                'agent_used': recommended_agent if 'recommended_agent' in locals() else 'unknown'
            }
    
    def _prepare_multimodal_context(self, documents: Optional[List[str]]) -> str:
        """Prepara el contexto multimodal funcional para los agentes."""
        if not documents:
            return ""

        try:
            from src.utils.multimodal_context import MultimodalContextBuilder

            # Crear builder de contexto multimodal
            builder = MultimodalContextBuilder()

            # Convertir rutas a objetos Path
            doc_paths = [Path(doc) for doc in documents if doc]

            # Validar documentos
            validation = builder.validate_documents(doc_paths)

            context_parts = ["\n--- CONTEXTO MULTIMODAL ---"]

            # Agregar contenido de documentos válidos
            for doc_path in validation["valid"]:
                try:
                    content = builder._extract_document_content(doc_path)
                    if content and not content.startswith("[Error"):
                        context_parts.extend([
                            f"\n--- {doc_path.name} ---",
                            content,
                            ""
                        ])
                    else:
                        context_parts.append(f"• {doc_path.name}: {content}")
                except Exception as e:
                    context_parts.append(f"• {doc_path.name}: Error extrayendo contenido - {e}")

            # Reportar documentos con problemas
            if validation["invalid"]:
                context_parts.append(f"• Documentos con errores: {[p.name for p in validation['invalid']]}")

            if validation["unsupported"]:
                context_parts.append(f"• Tipos no soportados: {[p.name for p in validation['unsupported']]}")

            if validation["missing"]:
                context_parts.append(f"• Archivos no encontrados: {[p.name for p in validation['missing']]}")

            context_parts.append("--- FIN CONTEXTO MULTIMODAL ---\n")

            return "\n".join(context_parts)

        except ImportError as e:
            st.warning(f"No se pudo cargar el módulo de contexto multimodal: {e}")
            # Fallback al comportamiento anterior
            context_parts = ["\n--- CONTEXTO MULTIMODAL (MODO BÁSICO) ---"]
            for doc_path in documents:
                doc_name = Path(doc_path).name
                context_parts.append(f"• Documento disponible: {doc_name}")
            context_parts.append("--- FIN CONTEXTO MULTIMODAL ---\n")
            return "\n".join(context_parts)

        except Exception as e:
            st.error(f"Error preparando contexto multimodal: {e}")
            return "\n--- CONTEXTO MULTIMODAL: ERROR ---\n"
    
    def _assemble_final_document(
        self,
        processed_segments: List[Dict[str, Any]],
        original_content: str,
        documents: Optional[List[str]]
    ) -> str:
        """Ensambla el documento final a partir de los segmentos procesados."""
        
        doc_parts = []
        
        # Header del documento
        doc_parts.append("# Documento Procesado - FastAgent")
        doc_parts.append(f"**Generado**: {self._get_timestamp()}")
        doc_parts.append(f"**Segmentos procesados**: {len(processed_segments)}")
        
        if documents:
            doc_parts.append(f"**Documentos adicionales**: {', '.join([Path(d).name for d in documents])}")
        
        doc_parts.append("\n---\n")
        
        # Tabla de contenidos
        doc_parts.append("## Tabla de Contenidos")
        for segment in processed_segments:
            if not segment.get('error', False):
                # Extraer título del contenido procesado
                title = self._extract_title(segment['processed_content'])
                doc_parts.append(f"- [Segmento {segment['segment_number']}: {title}](#segmento-{segment['segment_number']})")
        
        doc_parts.append("- [Preguntas y Respuestas](#preguntas-y-respuestas)")
        doc_parts.append("\n---\n")
        
        # Contenido principal
        doc_parts.append("## Contenido Principal\n")
        
        for segment in processed_segments:
            if segment.get('error', False):
                doc_parts.append(f"### Segmento {segment['segment_number']}: Error\n")
                doc_parts.append(f"❌ {segment['processed_content']}\n")
            else:
                doc_parts.append(f"### Segmento {segment['segment_number']}\n")
                doc_parts.append(segment['processed_content'])
                doc_parts.append("\n")
        
        # Sección Q&A (extraer de los segmentos procesados)
        doc_parts.append("\n---\n")
        doc_parts.append("## Preguntas y Respuestas\n")
        
        for segment in processed_segments:
            if not segment.get('error', False):
                qa_content = self._extract_qa_content(segment['processed_content'])
                if qa_content:
                    title = self._extract_title(segment['processed_content'])
                    doc_parts.append(f"### Segmento {segment['segment_number']}: {title}\n")
                    doc_parts.append(qa_content)
                    doc_parts.append("\n")
        
        # Footer
        doc_parts.append("\n---\n")
        doc_parts.append("*Documento generado por FastAgent - Sistema Multi-Agente*")
        
        return "\n".join(doc_parts)
    
    def _extract_title(self, content: str) -> str:
        """Extrae el título de un segmento procesado."""
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('#') and not line.startswith('###'):
                return line.lstrip('#').strip()
            elif line and not line.startswith('**') and len(line) > 10:
                return line[:50] + "..." if len(line) > 50 else line
        return "Sin título"
    
    def _extract_qa_content(self, content: str) -> str:
        """Extrae la sección Q&A de un segmento procesado."""
        lines = content.split('\n')
        qa_section = []
        in_qa_section = False
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['pregunta', 'respuesta', '¿', '?', 'q&a']):
                in_qa_section = True
            
            if in_qa_section:
                qa_section.append(line)
        
        return '\n'.join(qa_section) if qa_section else ""
    
    def _get_timestamp(self) -> str:
        """Retorna timestamp formateado."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    async def test_agent_connection(self, agent_name: str = "simple_processor") -> bool:
        """Prueba la conexión con un agente específico."""
        try:
            if not await self._initialize_agents():
                return False
            
            # Test básico con el agente
            async with self._fast_agent.run() as agent:
                result = await agent.content_pipeline.send("Test de conexión")
                return result is not None
                
        except Exception as e:
            st.error(f"Error probando conexión: {e}")
            return False
    
    def get_available_agents(self) -> List[str]:
        """Retorna lista de agentes disponibles."""
        return [
            "simple_processor",
            "meeting_processor"
        ]
    
    def get_agent_description(self, agent_name: str) -> str:
        """Retorna descripción de un agente."""
        descriptions = {
            "simple_processor": "Procesador general para contenido educativo lineal. Ideal para conferencias, clases y presentaciones.",
            "meeting_processor": "Procesador especializado para reuniones diarizadas. Extrae decisiones, action items y participantes."
        }
        return descriptions.get(agent_name, "Agente no encontrado")
    
    async def save_temp_file(self, content: bytes, suffix: str = ".tmp") -> str:
        """Guarda contenido en un archivo temporal y retorna la ruta."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(content)
            return tmp_file.name
    
    def cleanup_temp_files(self, file_paths: List[str]):
        """Limpia archivos temporales."""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                st.warning(f"No se pudo eliminar archivo temporal {file_path}: {e}")

# Helper functions para Streamlit
def run_async_in_streamlit(coroutine):
    """Ejecuta una coroutine asíncrona en Streamlit de forma simple."""
    import concurrent.futures
    import threading

    def run_in_thread():
        # Crear un nuevo event loop para este hilo
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coroutine)
        finally:
            new_loop.close()
            asyncio.set_event_loop(None)

    # Siempre ejecutar en un hilo separado para evitar conflictos
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_thread)
        return future.result()

def create_progress_callback():
    """Crea un callback de progreso para Streamlit."""
    progress_bar = st.progress(0)
    status_text = st.empty()

    def callback(message: str, progress: float):
        progress_bar.progress(progress)
        status_text.text(message)

    return callback