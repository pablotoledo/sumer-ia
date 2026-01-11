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
from typing import List, Dict, Any, Optional, Tuple, Callable
import tempfile
import os

# Añadir el directorio padre para importar módulos de FastAgent
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))


class ProcessingProgress:
    """
    Rastrea el progreso del procesamiento de forma dinámica.
    
    Calcula el progreso basándose en:
    - Número total de segmentos
    - Segmento actual siendo procesado
    - Paso actual dentro del pipeline (puntuación, formato, título, Q&A)
    """
    
    STEPS = ["Puntuando", "Formateando", "Titulando", "Generando Q&A"]
    
    def __init__(self, total_segments: int, steps_per_segment: int = 1):
        self.total_segments = max(1, total_segments)
        self.steps_per_segment = steps_per_segment
        self.current_segment = 0
        self.current_step = 0
        self.phase = "Iniciando"
        self._callback: Optional[Callable[[str, float], None]] = None
    
    def set_callback(self, callback: Callable[[str, float], None]):
        """Establece el callback para notificar progreso."""
        self._callback = callback
    
    def set_phase(self, phase: str):
        """Establece la fase actual (Segmentando, Procesando, Finalizando)."""
        self.phase = phase
        self._notify()
    
    def start_segment(self, segment_number: int, topic: str = ""):
        """Marca el inicio de procesamiento de un segmento."""
        self.current_segment = segment_number
        self.current_step = 0
        self.phase = f"Procesando{': ' + topic[:40] if topic else ''}"
        self._notify()
    
    def advance_step(self, step_name: str = ""):
        """Avanza al siguiente paso dentro del segmento."""
        self.current_step += 1
        if step_name:
            self.phase = step_name
        self._notify()
    
    def complete_segment(self):
        """Marca un segmento como completado."""
        self.current_step = self.steps_per_segment
        self._notify()
    
    @property
    def progress(self) -> float:
        """Retorna el progreso como valor entre 0 y 1."""
        if self.total_segments == 0:
            return 0.0
        
        # Base: 10% para segmentación, 10% para finalización
        # 80% restante dividido entre segmentos
        segment_progress = (self.current_segment - 1) / self.total_segments
        step_progress = self.current_step / max(1, self.steps_per_segment) / self.total_segments
        
        # Escalar al 80% del rango total (10% inicial + 10% final reservados)
        return 0.10 + 0.80 * (segment_progress + step_progress)
    
    @property  
    def status(self) -> str:
        """Retorna mensaje de estado legible."""
        if self.current_segment == 0:
            return self.phase
        return f"Segmento {self.current_segment}/{self.total_segments}: {self.phase}"
    
    def _notify(self):
        """Notifica el progreso actual si hay callback."""
        if self._callback:
            self._callback(self.status, self.progress)
    
    def finalize(self):
        """Marca el procesamiento como completado."""
        self.current_segment = self.total_segments
        self.current_step = self.steps_per_segment
        self.phase = "¡Completado!"
        self._notify()


class AgentInterface:
    """Interfaz para comunicarse con FastAgent."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self._fast_agent = None
        self._meeting_agent = None
    
    async def _initialize_agents(self):
        """Inicializa los agentes FastAgent."""
        try:
            # Importar módulos FastAgent
            from src.enhanced_agents import fast, adaptive_segment_content
            from robust_main import RateLimitHandler

            self._fast_agent = fast
            # Use the same agent for both types for now
            self._meeting_agent = fast
            self._adaptive_segment = adaptive_segment_content

            # Obtener configuración de rate limiting
            rate_config = self.config_manager.get_rate_limiting_config()
            max_retries = rate_config.get('max_retries', 3)
            base_delay = rate_config.get('retry_base_delay', 60)

            self._rate_limit_handler = RateLimitHandler(
                max_retries=max_retries,
                base_delay=base_delay
            )

            print(f"   • Rate limit: {max_retries} retries, {base_delay}s base delay")

            print(f"✅ Agents initialized successfully")
            print(f"   • Fast agent: {self._fast_agent}")
            print(f"   • Adaptive segment function: {self._adaptive_segment}")

            return True

        except Exception as e:
            st.error(f"Error inicializando agentes: {e}")
            print(f"❌ Error detallado: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def process_content(
        self,
        content: str,
        documents: Optional[List[str]] = None,
        progress_callback=None,
        agent_override: Optional[str] = None,
        use_intelligent_segmentation: bool = True,
        enable_qa: bool = True,
        questions_per_section: int = 4
    ) -> Dict[str, Any]:
        """
        Procesa contenido usando FastAgent.

        Args:
            content: Texto STT a procesar
            documents: Lista de rutas a documentos adicionales
            progress_callback: Función para reportar progreso
            agent_override: Agente específico a usar (opcional)
            use_intelligent_segmentation: Si True, usa GPT-4.1 para segmentar
            enable_qa: Si True, genera Q&A (por defecto True)
            questions_per_section: Número de preguntas por sección (2-8)

        Returns:
            Dict con resultado del procesamiento
        """

        if not await self._initialize_agents():
            raise Exception("No se pudieron inicializar los agentes")
        
        try:
            # PASO 1: Segmentación (Inteligente o Programática)
            if progress_callback:
                progress_callback("Analizando contenido para segmentación...", 0.1)

            word_count = len(content.split())

            # Decidir método de segmentación
            if use_intelligent_segmentation and word_count > 3000:
                # Usar segmentación AI para contenido grande
                print(f"🧠 Using AI-powered intelligent segmentation ({word_count:,} words)")
                enriched_segments, recommended_agent = await self._intelligent_segment_with_ai(content)
                segmentation_method = 'intelligent_ai'
            else:
                # Usar método programático para contenido pequeño o si se desactiva AI
                print(f"📐 Using programmatic segmentation ({word_count:,} words)")
                segments, recommended_agent = self._adaptive_segment(content)
                # Convert to enriched format
                enriched_segments = [{'content': seg, 'metadata': {}} for seg in segments]
                segmentation_method = 'programmatic'

            # DEBUG: Log segmentation results
            print(f"\n🔍 SEGMENTATION DEBUG:")
            print(f"   • Number of segments: {len(enriched_segments)}")
            print(f"   • Recommended agent: {recommended_agent}")
            print(f"   • Method: {segmentation_method}")

            # Usar agent_override si se especifica
            if agent_override:
                recommended_agent = agent_override

            if progress_callback:
                progress_callback(f"Segmentación completa: {len(enriched_segments)} segmentos", 0.2)
            
            # Paso 2: Configurar contexto multimodal
            multimodal_context = self._prepare_multimodal_context(documents)
            
            # PASO 3: Procesamiento por segmentos con CONTEXTO LIMPIO
            processed_segments = []
            total_segments = len(enriched_segments)

            # Seleccionar el agente FastAgent apropiado
            if recommended_agent == "meeting_processor":
                agent = self._meeting_agent
            else:
                agent = self._fast_agent

            for i, enriched_segment in enumerate(enriched_segments):
                segment_content = enriched_segment['content']
                segment_metadata = enriched_segment.get('metadata', {})

                if progress_callback:
                    progress = 0.2 + (0.7 * (i + 1) / total_segments)
                    topic = segment_metadata.get('topic', f'Segmento {i + 1}')
                    progress_callback(f"Procesando: {topic[:50]}...", progress)

                # IMPORTANTE: Cada iteración crea una NUEVA sesión = CONTEXTO LIMPIO
                try:
                    async with agent.run() as agent_instance:  # Nueva sesión aquí
                        # Construir prompt enriquecido con metadata y config Q&A
                        segment_prompt = self._build_segment_prompt(
                            segment_content=segment_content,
                            segment_number=i + 1,
                            total_segments=total_segments,
                            metadata=segment_metadata,
                            multimodal_context=multimodal_context,
                            enable_qa=enable_qa,
                            questions_per_section=questions_per_section
                        )

                        result = await self._rate_limit_handler.execute_with_retry(
                            agent_instance.simple_processor.send,
                            segment_prompt
                        )

                        processed_segments.append({
                            'segment_number': i + 1,
                            'original_content': segment_content,
                            'processed_content': result,
                            'agent_used': recommended_agent,
                            'metadata': segment_metadata
                        })

                        # Delay proactivo entre segmentos (excepto el último)
                        if i < len(enriched_segments) - 1:
                            delay = self._get_inter_segment_delay()
                            if delay > 0:
                                if progress_callback:
                                    progress_callback(f"Esperando {delay}s antes del siguiente segmento...", progress)
                                await asyncio.sleep(delay)

                except Exception as e:
                    st.warning(f"Error procesando segmento {i + 1}: {e}")
                    processed_segments.append({
                        'segment_number': i + 1,
                        'original_content': segment_content,
                        'processed_content': f"Error procesando segmento: {e}",
                        'agent_used': recommended_agent,
                        'metadata': segment_metadata,
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
                'multimodal_files': documents or [],
                'segmentation_method': segmentation_method
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
        """Prepara el contexto multimodal para los agentes."""
        if not documents:
            return ""
        
        context_parts = ["\n--- CONTEXTO MULTIMODAL ---"]
        
        for doc_path in documents:
            doc_name = Path(doc_path).name
            context_parts.append(f"• Documento disponible: {doc_name}")
        
        context_parts.append("--- FIN CONTEXTO MULTIMODAL ---\n")
        
        return "\n".join(context_parts)
    
    def _assemble_final_document(
        self,
        processed_segments: List[Dict[str, Any]],
        original_content: str,
        documents: Optional[List[str]]
    ) -> str:
        """
        Ensambla el documento final en Markdown simple.
        Cada segmento incluye su contenido Y sus preguntas juntos, sin duplicaciones.
        """

        doc_parts = []

        # Header del documento
        doc_parts.append("# Documento Procesado")
        doc_parts.append(f"\n**Fecha**: {self._get_timestamp()}")
        doc_parts.append(f"**Segmentos**: {len(processed_segments)}")

        if documents:
            doc_parts.append(f"**Documentos de referencia**: {', '.join([Path(d).name for d in documents])}")

        doc_parts.append("\n---\n")

        # Procesar cada segmento (contenido + preguntas juntos)
        for segment in processed_segments:
            if segment.get('error', False):
                # Segmento con error
                doc_parts.append(f"## ❌ Error en Segmento {segment['segment_number']}\n")
                doc_parts.append(f"{segment['processed_content']}\n")
            else:
                # Extraer título del contenido procesado
                title = self._extract_title(segment['processed_content'])
                metadata = segment.get('metadata', {})

                # Header del segmento
                doc_parts.append(f"## {segment['segment_number']}. {title}\n")

                # Mostrar metadata si existe (del segmentador inteligente)
                if metadata.get('keywords'):
                    keywords_text = ', '.join(metadata['keywords'][:5])
                    doc_parts.append(f"*Palabras clave: {keywords_text}*\n")

                # Contenido del segmento (SIN las preguntas, las extraeremos aparte)
                content_without_qa = self._extract_content_without_qa(segment['processed_content'])
                doc_parts.append(content_without_qa)
                doc_parts.append("\n")

                # Preguntas del segmento como subsección
                qa_content = self._extract_qa_content(segment['processed_content'])
                if qa_content:
                    doc_parts.append("### 📚 Preguntas y Respuestas\n")
                    doc_parts.append(qa_content)
                    doc_parts.append("\n")

                doc_parts.append("---\n")

        # Footer
        doc_parts.append("\n*Generado por FastAgent*")

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
    
    def _extract_content_without_qa(self, content: str) -> str:
        """Extrae el contenido principal SIN la sección de Q&A."""
        lines = content.split('\n')
        content_lines = []

        # Buscar marcadores comunes de inicio de sección Q&A
        qa_markers = [
            'preguntas y respuestas',
            'preguntas',
            'q&a',
            '## preguntas',
            '### preguntas',
            '---'
        ]

        for i, line in enumerate(lines):
            line_lower = line.lower().strip()

            # Si encontramos un marcador de Q&A, detenemos
            if any(marker in line_lower for marker in qa_markers):
                # Verificar si las siguientes líneas son realmente Q&A
                if i + 1 < len(lines):
                    next_lines = '\n'.join(lines[i:i+5]).lower()
                    if 'pregunta' in next_lines or '¿' in next_lines or 'respuesta' in next_lines:
                        break

            content_lines.append(line)

        return '\n'.join(content_lines).strip()

    def _extract_qa_content(self, content: str) -> str:
        """Extrae SOLO la sección Q&A de un segmento procesado."""
        lines = content.split('\n')
        qa_section = []
        in_qa_section = False

        # Marcadores de inicio de Q&A
        qa_start_markers = [
            'preguntas y respuestas',
            'preguntas',
            'q&a',
            '## preguntas',
            '### preguntas'
        ]

        for line in lines:
            line_lower = line.lower().strip()

            # Detectar inicio de sección Q&A
            if not in_qa_section and any(marker in line_lower for marker in qa_start_markers):
                in_qa_section = True
                continue  # Saltar el header "Preguntas y Respuestas"

            # Una vez dentro, capturar todo hasta encontrar separador o fin
            if in_qa_section:
                # Detenerse en separadores de secciones
                if line.strip() == '---' and len(qa_section) > 5:
                    break
                qa_section.append(line)

        return '\n'.join(qa_section).strip() if qa_section else ""
    
    def _get_timestamp(self) -> str:
        """Retorna timestamp formateado."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _get_inter_segment_delay(self) -> int:
        """
        Obtiene el delay configurado entre segmentos para evitar rate limits proactivamente.

        Returns:
            Delay en segundos (0 si no configurado)
        """
        try:
            rate_config = self.config_manager.get_rate_limiting_config()
            delay = rate_config.get('delay_between_requests', 0)
            return int(delay)
        except Exception as e:
            print(f"⚠️ Error obteniendo delay entre requests: {e}")
            return 0

    async def test_agent_connection(self, agent_name: str = "simple_processor") -> bool:
        """Prueba la conexión con un agente específico."""
        try:
            if not await self._initialize_agents():
                return False
            
            # Test básico con el agente
            async with self._fast_agent.run() as agent:
                result = await agent.simple_processor.send("Test de conexión")
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

    async def _intelligent_segment_with_ai(self, content: str) -> Tuple[List[Dict[str, Any]], str]:
        """Wrapper para llamar a la función de segmentación inteligente."""
        from src.enhanced_agents import adaptive_segment_content_v2
        return await adaptive_segment_content_v2(content)

    def _build_segment_prompt(
        self,
        segment_content: str,
        segment_number: int,
        total_segments: int,
        metadata: Dict[str, Any],
        multimodal_context: str,
        enable_qa: bool = True,
        questions_per_section: int = 4
    ) -> str:
        """
        Construye el prompt para procesar un segmento, incluyendo metadata útil.
        """
        prompt_parts = []

        # Header con posición
        prompt_parts.append(f"SEGMENTO {segment_number} de {total_segments}")

        # Metadata si está disponible
        if metadata:
            has_metadata = any(k in metadata for k in ['topic', 'keywords', 'key_concepts', 'section_type'])
            if has_metadata:
                prompt_parts.append("\nMETADATA DEL SEGMENTO:")
                if 'topic' in metadata:
                    prompt_parts.append(f"• Tema principal: {metadata['topic']}")
                if 'keywords' in metadata and metadata['keywords']:
                    prompt_parts.append(f"• Palabras clave: {', '.join(metadata['keywords'][:5])}")
                if 'key_concepts' in metadata and metadata['key_concepts']:
                    prompt_parts.append(f"• Conceptos clave: {', '.join(metadata['key_concepts'][:3])}")
                if 'section_type' in metadata:
                    prompt_parts.append(f"• Tipo de sección: {metadata['section_type']}")

        # Instrucciones de Q&A
        if enable_qa:
            prompt_parts.append(f"\nINSTRUCCIONES Q&A: Genera exactamente {questions_per_section} preguntas y respuestas educativas.")
        else:
            prompt_parts.append("\nINSTRUCCIONES Q&A: NO generes preguntas ni respuestas.")

        # Contenido del segmento
        prompt_parts.append(f"\nCONTENIDO:\n{segment_content}")

        # Contexto multimodal
        if multimodal_context:
            prompt_parts.append(f"\n{multimodal_context}")

        return '\n'.join(prompt_parts)

# Helper functions para Streamlit
def run_async_in_streamlit(coroutine):
    """Ejecuta una coroutine asíncrona en Streamlit de forma simple."""
    import nest_asyncio

    # Aplicar nest_asyncio para permitir event loops anidados
    nest_asyncio.apply()

    # Obtener o crear event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Ejecutar la coroutine en el event loop actual
    return loop.run_until_complete(coroutine)

def create_progress_callback():
    """Crea un callback de progreso para Streamlit."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def callback(message: str, progress: float):
        progress_bar.progress(progress)
        status_text.text(message)
    
    return callback