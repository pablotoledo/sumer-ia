# Arquitectura: Segmentación Inteligente con GPT-4.1

## Objetivo
Reemplazar la segmentación programática simple por un agente inteligente que aproveche GPT-4.1 (1M token context) para identificar puntos de corte semánticos óptimos.

## Ventajas del Nuevo Diseño

### 1. Calidad Superior
- ✅ Cortes en transiciones naturales de tema
- ✅ Cada segmento es una unidad lógica coherente
- ✅ Mejor comprensión del contenido por el modelo
- ✅ Metadata útil (títulos, keywords, tipos)

### 2. Aprovecha GPT-4.1
- ✅ 24k palabras = ~31k tokens (3% del límite de 1M)
- ✅ Una sola llamada para todo el análisis
- ✅ Costo mínimo adicional (~$0.03 por 24k palabras)

### 3. Contexto Limpio
- ✅ Cada segmento se procesa con contexto fresco
- ✅ No hay "arrastre" de conversación anterior
- ✅ Procesamiento paralelo sin interferencias

---

## Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────────────────┐
│                        FASE 1: ANÁLISIS                         │
│                   (1 llamada, contexto único)                   │
└─────────────────────────────────────────────────────────────────┘

Input: Todo el contenido (24k palabras)
  ↓
┌──────────────────────────────────────────┐
│   Agente: intelligent_segmenter          │
│   Modelo: GPT-4.1                        │
│   Contexto: ~31k tokens (3% del límite)  │
│                                          │
│   Instrucción:                           │
│   "Analiza este contenido y determina   │
│    los mejores puntos de segmentación   │
│    para dividirlo en unidades            │
│    semánticamente coherentes de          │
│    ~2500 palabras cada una"              │
└──────────────────────────────────────────┘
  ↓
Output: JSON estructurado
{
  "total_words": 24000,
  "recommended_segments": 10,
  "segments": [
    {
      "id": 1,
      "start_word": 0,
      "end_word": 2450,
      "word_count": 2450,
      "topic": "Introducción: Identificar empresas de calidad",
      "keywords": ["Warren Buffett", "calidad", "valoración", "BMW", "Renault"],
      "section_type": "introduction",
      "key_concepts": [
        "Diferencia entre precio y calidad",
        "Herramientas de análisis (Morningstar, TKR)"
      ],
      "transition_type": "natural_break"
    },
    {
      "id": 2,
      "start_word": 2450,
      "end_word": 4920,
      "word_count": 2470,
      "topic": "Métricas clave: ROE, márgenes y ratios",
      "keywords": ["ROE", "ROIC", "márgenes operativos", "free cash flow"],
      "section_type": "main_content",
      "key_concepts": [
        "Retorno sobre capital invertido",
        "Comparación entre BMW, Ford y Renault"
      ],
      "transition_type": "topic_change"
    },
    // ... 8 segmentos más
  ],
  "format_detected": "educational_linear",
  "recommended_agent": "simple_processor"
}


┌─────────────────────────────────────────────────────────────────┐
│                    FASE 2: PROCESAMIENTO                        │
│              (10 llamadas, contextos independientes)            │
└─────────────────────────────────────────────────────────────────┘

Para cada segmento del JSON:
  ↓
┌──────────────────────────────────────────┐
│   Agente: simple_processor               │
│   Modelo: GPT-4.1                        │
│   Contexto: LIMPIO (nueva sesión)        │
│   Input: ~2500 palabras del segmento    │
│                                          │
│   Metadata adicional del segmento:      │
│   - Topic: "..."                         │
│   - Keywords: [...]                      │
│   - Key concepts: [...]                  │
│   - Position: 2/10                       │
└──────────────────────────────────────────┘
  ↓
Output: Contenido procesado con Q&A


┌─────────────────────────────────────────────────────────────────┐
│                      FASE 3: ENSAMBLADO                         │
│                     (sin llamadas LLM)                          │
└─────────────────────────────────────────────────────────────────┘

Combinar todos los segmentos procesados en documento final
```

---

## Implementación Detallada

### 1. Nuevo Agente: `intelligent_segmenter`

**Ubicación**: `src/enhanced_agents.py`

```python
@fast.agent(
    name="intelligent_segmenter",
    model=DEFAULT_MODEL,  # GPT-4.1
    instruction="""You are an expert content analyzer specializing in identifying optimal segmentation points.

TASK: Analyze the provided content and determine the best way to divide it into semantically coherent segments.

REQUIREMENTS:
1. Each segment should be ~2500 words (range: 2000-3000 words)
2. Break at natural topic transitions, not mid-concept
3. Identify the main topic/theme of each segment
4. Extract key concepts and keywords for each segment
5. Classify segment type: introduction, main_content, example, conclusion, transition

OUTPUT FORMAT (valid JSON):
{
  "total_words": <int>,
  "recommended_segments": <int>,
  "segments": [
    {
      "id": <int>,
      "start_word": <int>,
      "end_word": <int>,
      "word_count": <int>,
      "topic": "<concise topic description>",
      "keywords": ["<keyword1>", "<keyword2>", ...],
      "section_type": "<introduction|main_content|example|conclusion|transition>",
      "key_concepts": ["<concept1>", "<concept2>", ...],
      "transition_type": "<natural_break|topic_change|speaker_change|section_end>"
    }
  ],
  "format_detected": "<educational_linear|meeting_dialogue|technical_document>",
  "recommended_agent": "<simple_processor|meeting_processor>"
}

IMPORTANT:
- Ensure start_word and end_word cover ALL content with no gaps
- The last segment's end_word must equal total_words
- Avoid segments smaller than 1000 words unless necessary
- Prefer clean breaks at paragraph or sentence boundaries
- If content has clear section markers (headers, transitions), use them
"""
)
def intelligent_segmenter():
    pass
```

### 2. Nueva Función: `adaptive_segment_content_v2`

**Ubicación**: `src/enhanced_agents.py`

```python
import json
from typing import Dict, Any

async def adaptive_segment_content_v2(content: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Use GPT-4.1 to intelligently segment content based on semantic analysis.
    Returns (segment_metadata_list, recommended_agent) tuple.

    This replaces the programmatic segmentation with AI-driven analysis.
    """
    words = content.split()
    total_words = len(words)

    print(f"\n🧠 INTELLIGENT SEGMENTATION (GPT-4.1)")
    print(f"   • Total words: {total_words:,}")
    print(f"   • Analyzing content for optimal segmentation...")

    # Call the intelligent_segmenter agent
    async with fast.run() as agent_instance:
        # Send the full content for analysis
        segmentation_prompt = f"""Analyze and segment the following content:

CONTENT ({total_words} words):
{content}

Provide a JSON segmentation plan following the specified format."""

        result_json = await agent_instance.intelligent_segmenter.send(segmentation_prompt)

    # Parse the JSON response
    try:
        segmentation_plan = json.loads(result_json)
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parsing failed: {e}")
        print(f"   Falling back to programmatic segmentation...")
        # Fallback to old method
        return adaptive_segment_content(content)

    # Validate the segmentation plan
    segments_metadata = segmentation_plan.get('segments', [])
    recommended_agent = segmentation_plan.get('recommended_agent', 'simple_processor')

    print(f"   • Segments identified: {len(segments_metadata)}")
    print(f"   • Format detected: {segmentation_plan.get('format_detected', 'unknown')}")
    print(f"   • Recommended agent: {recommended_agent}")

    # Extract actual text for each segment
    enriched_segments = []
    for seg_meta in segments_metadata:
        start = seg_meta['start_word']
        end = seg_meta['end_word']

        segment_words = words[start:end]
        segment_text = ' '.join(segment_words)

        # Enrich with metadata
        enriched_segments.append({
            'content': segment_text,
            'metadata': seg_meta
        })

        print(f"   • Segment {seg_meta['id']}: {seg_meta['word_count']} words - {seg_meta['topic'][:60]}...")

    return enriched_segments, recommended_agent
```

### 3. Modificar `AgentInterface.process_content`

**Ubicación**: `streamlit_app/components/agent_interface.py`

**Cambios clave:**

```python
async def process_content(
    self,
    content: str,
    documents: Optional[List[str]] = None,
    progress_callback=None,
    agent_override: Optional[str] = None,
    use_intelligent_segmentation: bool = True  # NUEVO PARÁMETRO
) -> Dict[str, Any]:
    """
    Procesa contenido usando FastAgent.

    Args:
        use_intelligent_segmentation: Si True, usa GPT-4.1 para segmentar.
                                      Si False, usa método programático.
    """

    if not await self._initialize_agents():
        raise Exception("No se pudieron inicializar los agentes")

    try:
        # PASO 1: Segmentación (con o sin IA)
        if progress_callback:
            progress_callback("Analizando contenido para segmentación...", 0.1)

        if use_intelligent_segmentation and len(content.split()) > 3000:
            # Usar agente inteligente para contenido grande
            print("🧠 Using AI-powered intelligent segmentation")
            enriched_segments, recommended_agent = await self._intelligent_segment_with_ai(content)
        else:
            # Usar método programático para contenido pequeño
            print("📐 Using programmatic segmentation")
            segments, recommended_agent = self._adaptive_segment(content)
            enriched_segments = [{'content': seg, 'metadata': {}} for seg in segments]

        # Usar agent_override si se especifica
        if agent_override:
            recommended_agent = agent_override

        if progress_callback:
            progress_callback(f"Segmentación completa: {len(enriched_segments)} segmentos", 0.2)

        # PASO 2: Configurar contexto multimodal
        multimodal_context = self._prepare_multimodal_context(documents)

        # PASO 3: Procesar cada segmento con CONTEXTO LIMPIO
        processed_segments = []
        total_segments = len(enriched_segments)

        # Seleccionar agente
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

            # IMPORTANTE: Cada iteración crea una NUEVA sesión con contexto limpio
            try:
                async with agent.run() as agent_instance:  # Nueva sesión = contexto limpio
                    # Construir prompt con metadata enriquecida
                    segment_prompt = self._build_segment_prompt(
                        segment_content=segment_content,
                        segment_number=i + 1,
                        total_segments=total_segments,
                        metadata=segment_metadata,
                        multimodal_context=multimodal_context
                    )

                    # Procesar con retry
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

            except Exception as e:
                st.warning(f"Error procesando segmento {i + 1}: {e}")
                processed_segments.append({
                    'segment_number': i + 1,
                    'original_content': segment_content,
                    'processed_content': f"Error: {e}",
                    'agent_used': recommended_agent,
                    'metadata': segment_metadata,
                    'error': True
                })

        # PASO 4: Ensamblar documento final
        if progress_callback:
            progress_callback("Ensamblando documento final...", 0.95)

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
            'segmentation_method': 'intelligent_ai' if use_intelligent_segmentation else 'programmatic'
        }

    except Exception as e:
        # ... error handling ...


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
    multimodal_context: str
) -> str:
    """
    Construye el prompt para procesar un segmento, incluyendo metadata útil.
    """
    prompt_parts = []

    # Header con posición
    prompt_parts.append(f"SEGMENTO {segment_number} de {total_segments}")

    # Metadata si está disponible
    if metadata:
        prompt_parts.append("\nMETADATA DEL SEGMENTO:")
        if 'topic' in metadata:
            prompt_parts.append(f"• Tema principal: {metadata['topic']}")
        if 'keywords' in metadata:
            prompt_parts.append(f"• Palabras clave: {', '.join(metadata['keywords'])}")
        if 'key_concepts' in metadata:
            prompt_parts.append(f"• Conceptos clave: {', '.join(metadata['key_concepts'])}")
        if 'section_type' in metadata:
            prompt_parts.append(f"• Tipo de sección: {metadata['section_type']}")

    # Contenido del segmento
    prompt_parts.append(f"\nCONTENIDO:\n{segment_content}")

    # Contexto multimodal
    if multimodal_context:
        prompt_parts.append(f"\n{multimodal_context}")

    return '\n'.join(prompt_parts)
```

---

## Contexto Limpio: Cómo Funciona

### Mecanismo de Limpieza

En fast-agent, **cada vez que se usa `async with agent.run() as agent_instance:`**, se crea una **nueva sesión** con:

1. ✅ **Contexto vacío** - Sin historial de conversación
2. ✅ **Estado fresco** - Sin memoria de llamadas anteriores
3. ✅ **Independencia total** - Cada segmento se procesa aislado

### Código Actual vs Nuevo

**❌ ANTES (contexto compartido):**
```python
# UNA SOLA sesión para TODOS los segmentos
async with agent.run() as agent_instance:
    for segment in segments:
        # Todos comparten el mismo contexto
        result = await agent_instance.simple_processor.send(segment)
```

**✅ AHORA (contexto limpio):**
```python
# NUEVA sesión para CADA segmento
for segment in segments:
    async with agent.run() as agent_instance:  # Nueva sesión
        # Contexto limpio, sin memoria del anterior
        result = await agent_instance.simple_processor.send(segment)
```

### Verificación

Puedes verificar que el contexto se limpia observando los logs de fast-agent:
- Cada `agent.run()` inicia una nueva sesión
- El contador de `turns` se resetea a 1 en cada segmento
- No hay "arrastre" de tokens de contexto entre segmentos

---

## Configuración y Uso

### Streamlit UI: Toggle para elegir método

En la página de procesamiento, agregar:

```python
# En show_input_tab()
st.subheader("🧠 Método de Segmentación")

segmentation_method = st.radio(
    "¿Cómo dividir el contenido?",
    options=[
        "🧠 Inteligente (GPT-4.1 analiza y segmenta)",
        "📐 Programático (división fija cada 2500 palabras)"
    ],
    help="""
    Inteligente: GPT-4.1 analiza tu contenido y encuentra los mejores puntos
    de corte semánticos. Recomendado para >5000 palabras.

    Programático: División simple cada 2500 palabras. Más rápido pero menos preciso.
    """
)

st.session_state.use_intelligent_segmentation = (
    "Inteligente" in segmentation_method
)
```

En `process_content()`:
```python
result = run_async_in_streamlit(
    agent_interface.process_content(
        content=content,
        documents=document_paths,
        progress_callback=None,
        agent_override=selected_agent,
        use_intelligent_segmentation=st.session_state.get('use_intelligent_segmentation', True)
    )
)
```

---

## Estimación de Costos

### GPT-4.1 Pricing (Azure/OpenAI)
- Input: ~$2.50 por 1M tokens
- Output: ~$10.00 por 1M tokens

### Para contenido de 24,000 palabras (~31k tokens):

**Fase 1 - Segmentación Inteligente:**
- Input: 31k tokens × $2.50/1M = **$0.078**
- Output: ~2k tokens × $10/1M = **$0.020**
- **Subtotal Fase 1: $0.10**

**Fase 2 - Procesamiento (10 segmentos):**
- Input: 10 × 3.3k tokens = 33k × $2.50/1M = **$0.083**
- Output: 10 × 2k tokens = 20k × $10/1M = **$0.200**
- **Subtotal Fase 2: $0.28**

**TOTAL: ~$0.38 por documento de 24k palabras**

**vs Método Anterior (30 segmentos pequeños):**
- Input: 30 × 1.1k = 33k tokens = $0.083
- Output: 30 × 1k = 30k tokens = $0.300
- **Total anterior: $0.38**

✅ **Costo similar, pero MUCHA mejor calidad**

---

## Rollout Plan

### Fase 1: Implementación (Sin tocar código existente)
1. ✅ Crear `intelligent_segmenter` agent en `enhanced_agents.py`
2. ✅ Crear `adaptive_segment_content_v2()` function
3. ✅ Mantener `adaptive_segment_content()` como fallback

### Fase 2: Integración
1. ✅ Modificar `AgentInterface.process_content()` con parámetro `use_intelligent_segmentation`
2. ✅ Implementar `_intelligent_segment_with_ai()` y `_build_segment_prompt()`
3. ✅ Agregar UI toggle en Streamlit

### Fase 3: Testing
1. ✅ Test con contenido pequeño (< 3k palabras) → debe usar método programático
2. ✅ Test con contenido mediano (5-10k palabras) → debe usar IA, pocos segmentos
3. ✅ Test con contenido grande (24k palabras) → debe usar IA, ~10 segmentos
4. ✅ Verificar contexto limpio (logs muestran nueva sesión cada vez)
5. ✅ Validar JSON parsing y fallback

### Fase 4: Production
1. ✅ Default: `use_intelligent_segmentation=True` para contenido > 5k palabras
2. ✅ Monitorear costos y tiempos
3. ✅ Ajustar prompts según feedback

---

## Métricas de Éxito

### Calidad
- ✅ Cada segmento es coherente temáticamente
- ✅ No hay cortes en mitad de conceptos importantes
- ✅ Títulos y metadata útiles

### Performance
- ✅ Tiempo total < 3 minutos para 24k palabras
- ✅ Menos llamadas API (10 vs 30)
- ✅ Procesamiento paralelo eficiente

### Robustez
- ✅ Fallback automático si falla segmentación IA
- ✅ Manejo de errores por segmento
- ✅ Validación de JSON response

---

## Preguntas Frecuentes

### ¿Por qué no procesar todo de una sola vez?
Aunque GPT-4.1 puede manejar 1M tokens, dividir en segmentos:
- Mejora la calidad del output (foco)
- Permite retry granular si algo falla
- Facilita progreso tracking
- Permite procesamiento paralelo futuro

### ¿Cuándo usar método programático?
- Contenido < 3k palabras (no justifica el overhead)
- Procesamiento batch donde velocidad > calidad
- Fallback si la segmentación IA falla

### ¿Se puede cachear la segmentación?
Sí, futura optimización: guardar el plan de segmentación en session_state
para permitir re-procesamiento sin re-analizar.

### ¿Funciona con contenido diarizado?
Sí, el `intelligent_segmenter` puede detectar reuniones y recomendar
`meeting_processor` como agente, además de segmentar por cambios de speaker.

---

## Próximos Pasos

1. **Implementar el diseño** siguiendo el plan de Fase 1-4
2. **Testing exhaustivo** con diferentes tipos de contenido
3. **Optimización de prompts** basada en resultados reales
4. **Caching inteligente** para re-procesamiento
5. **Procesamiento paralelo** de segmentos (futura optimización)
