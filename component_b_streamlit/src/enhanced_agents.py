"""
Enhanced Agents - Complete System with Q&A Integration
=====================================================

Enhanced version that combines content processing with intelligent Q&A generation.
"""

from pathlib import Path
from mcp_agent.core.fastagent import FastAgent
from typing import List, Tuple, Dict, Any
import yaml
from .intelligent_segmenter import IntelligentSegmenter
from .content_format_detector import analyze_content_format, ContentFormat
from .meeting_processor import segment_meeting_by_topics


def load_config() -> dict:
    """Load FastAgent configuration."""
    for config_path in ["fastagent.config.yaml", "../fastagent.config.yaml"]:
        if Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
    return {}


# Load configuration
config = load_config()
DEFAULT_MODEL = config.get('default_model', 'azure.gpt-4.1')

# Create FastAgent instance
fast = FastAgent("EnhancedDistributedSystem")


# ===== CORE PROCESSING AGENTS (Enhanced) =====

@fast.agent(
    name="punctuator",
    model=DEFAULT_MODEL,
    instruction="""Add proper punctuation and capitalization to speech-to-text content while preserving 100% of the original words.

RULES:
- Add punctuation marks (periods, commas, question marks, exclamation points)
- Capitalize proper nouns and sentence beginnings  
- DO NOT remove, change, or rephrase any words
- DO NOT eliminate filler words like "eh", "bueno", "entonces" 
- Keep ALL content exactly as provided, just add punctuation

Input: "bueno eh entonces vamos a hablar sobre Warren Buffett que es el mejor inversor"
Output: "Bueno, eh, entonces vamos a hablar sobre Warren Buffett, que es el mejor inversor."
"""
)
def punctuator():
    pass


def adaptive_segment_content(content: str) -> Tuple[List[str], str]:
    """
    Intelligently segment content based on auto-detected format.
    Returns (segments, processing_agent) tuple.
    """
    # Step 1: Detect content format automatically
    format_result = analyze_content_format(content)
    
    print(f"🔍 CONTENT FORMAT ANALYSIS")
    print(f"📊 Format detected: {format_result.format_type.value}")
    print(f"🎯 Confidence: {format_result.confidence_score:.1f}")
    
    if format_result.participants:
        print(f"👥 Participants: {', '.join(format_result.participants)}")
    
    if format_result.key_indicators:
        print(f"🔑 Key indicators: {', '.join(format_result.key_indicators)}")
    
    # Step 2: Apply format-specific segmentation
    if format_result.format_type == ContentFormat.DIARIZED_MEETING:
        print(f"🎯 Using conversational segmentation for meeting content")
        segments = segment_meeting_by_topics(content)
        recommended_agent = "meeting_processor"
        
    else:
        print(f"🎯 Using semantic segmentation for linear content")
        segments = intelligent_segment_content(content)
        recommended_agent = "simple_processor"
    
    print(f"⚙️  Recommended agent: {recommended_agent}")
    print()
    
    return segments, recommended_agent


async def adaptive_segment_content_v2(content: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Use GPT-4.1 to intelligently segment content based on semantic analysis.
    Returns (segment_metadata_list, recommended_agent) tuple.

    This is the new AI-powered segmentation that replaces programmatic division.
    Each segment includes rich metadata for better processing.
    """
    import json

    words = content.split()
    total_words = len(words)

    print(f"\n🧠 INTELLIGENT SEGMENTATION (GPT-4.1)")
    print(f"   • Total words: {total_words:,}")
    print(f"   • Analyzing content for optimal segmentation...")

    try:
        # Call the intelligent_segmenter agent
        async with fast.run() as agent_instance:
            # Send the full content for analysis
            segmentation_prompt = f"""Analyze and segment the following content:

CONTENT ({total_words} words):
{content}

Provide a JSON segmentation plan following the specified format."""

            result_json = await agent_instance.intelligent_segmenter.send(segmentation_prompt)

        # Parse the JSON response
        # Try to extract JSON if there's any surrounding text
        result_clean = result_json.strip()

        # Find JSON bounds if wrapped in markdown code blocks
        if '```json' in result_clean:
            start = result_clean.find('```json') + 7
            end = result_clean.find('```', start)
            result_clean = result_clean[start:end].strip()
        elif '```' in result_clean:
            start = result_clean.find('```') + 3
            end = result_clean.find('```', start)
            result_clean = result_clean[start:end].strip()

        segmentation_plan = json.loads(result_clean)

        # Validate the segmentation plan
        segments_metadata = segmentation_plan.get('segments', [])
        recommended_agent = segmentation_plan.get('recommended_agent', 'simple_processor')

        if not segments_metadata:
            raise ValueError("No segments returned in plan")

        print(f"   ✅ Segments identified: {len(segments_metadata)}")
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

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"⚠️  AI segmentation failed: {e}")
        print(f"   Falling back to programmatic segmentation...")

        # Fallback to programmatic method
        segments = intelligent_segment_content(content)

        # Convert to enriched format
        enriched_segments = []
        for i, seg in enumerate(segments, 1):
            enriched_segments.append({
                'content': seg,
                'metadata': {
                    'id': i,
                    'topic': f'Segment {i}',
                    'section_type': 'main_content'
                }
            })

        # Determine agent from content format
        from .content_format_detector import analyze_content_format
        format_result = analyze_content_format(content)
        recommended_agent = "meeting_processor" if "meeting" in format_result.format_type.value.lower() else "simple_processor"

        return enriched_segments, recommended_agent


def intelligent_segment_content(content: str) -> List[str]:
    """
    Segment content using intelligent programmatic methods (NO LLM).
    Guarantees 100% content preservation.
    Optimized for GPT-4.1 with 1M token context window.

    GPT-4.1 can handle up to 1M input tokens (~750K words), but we segment
    for better quality, parallel processing, and cost optimization:
    - Smaller segments = better focus and quality
    - Allows retry of individual segments on failure
    - Better progress tracking
    - Optimal size: 2000-3000 words per segment (~2700-4000 tokens)
    """
    # GPT-4.1 optimized sizing (can handle much more, but this is optimal)
    TARGET_WORDS_PER_SEGMENT = 2500  # ~3300 tokens - sweet spot for quality
    MIN_WORDS_PER_SEGMENT = 1000     # Minimum to maintain context
    MAX_WORDS_PER_SEGMENT = 4000     # Maximum to avoid quality degradation

    words = content.split()
    total_words = len(words)

    print(f"🔍 Segmentation starting (GPT-4.1 optimized):")
    print(f"   • Total words: {total_words:,}")
    print(f"   • Target words per segment: {TARGET_WORDS_PER_SEGMENT:,}")
    print(f"   • Estimated tokens per segment: ~{int(TARGET_WORDS_PER_SEGMENT * 1.3):,}")

    # If content is small enough, return as single segment
    if total_words <= TARGET_WORDS_PER_SEGMENT:
        print(f"✅ Content fits in single segment")
        return [f"[SEGMENT 1]\n{content}\n---SEGMENT---"]

    # Calculate number of segments needed
    num_segments = max(2, (total_words + TARGET_WORDS_PER_SEGMENT - 1) // TARGET_WORDS_PER_SEGMENT)
    words_per_segment = total_words // num_segments

    print(f"   • Number of segments: {num_segments}")
    print(f"   • Approximate words per segment: {words_per_segment}")

    segments = []
    start_idx = 0

    for i in range(num_segments):
        # Calculate end index for this segment
        if i == num_segments - 1:
            # Last segment gets all remaining words
            end_idx = total_words
        else:
            # Try to find a good break point near the target
            target_end = start_idx + words_per_segment

            # Look for sentence boundaries (. ! ?) within a window
            search_start = max(start_idx, target_end - 100)
            search_end = min(total_words, target_end + 100)

            # Find the best sentence break
            best_break = target_end
            for j in range(search_start, search_end):
                word = words[j].strip()
                if word.endswith('.') or word.endswith('!') or word.endswith('?'):
                    if abs(j - target_end) < abs(best_break - target_end):
                        best_break = j + 1

            end_idx = best_break

        # Extract segment
        segment_words = words[start_idx:end_idx]
        segment_text = ' '.join(segment_words)

        # Format segment
        formatted_segment = f"[SEGMENT {i + 1}]\n{segment_text}\n---SEGMENT---"
        segments.append(formatted_segment)

        print(f"   • Segment {i + 1}: {len(segment_words)} words")

        start_idx = end_idx

    # Verification
    total_segment_words = sum(len(seg.split()) for seg in segments)
    retention_rate = (total_segment_words / total_words) * 100
    print(f"✅ Segmentation complete: {total_words:,} → {total_segment_words:,} words ({retention_rate:.1f}% retention)")
    print(f"   • Created {len(segments)} segments")

    return segments


# ===== INTELLIGENT SEGMENTATION AGENT =====

@fast.agent(
    name="intelligent_segmenter",
    model=DEFAULT_MODEL,
    instruction="""You are an expert content analyzer specializing in identifying optimal segmentation points for educational and technical content.

TASK: Analyze the provided content and determine the best way to divide it into semantically coherent segments.

REQUIREMENTS:
1. Each segment should be ~2500 words (range: 2000-3000 words acceptable)
2. Break at natural topic transitions, NOT mid-concept or mid-explanation
3. Identify the main topic/theme of each segment
4. Extract key concepts and keywords for each segment
5. Classify segment type: introduction, main_content, example, conclusion, transition

OUTPUT FORMAT (MUST be valid JSON):
{
  "total_words": <int>,
  "recommended_segments": <int>,
  "segments": [
    {
      "id": <int>,
      "start_word": <int>,
      "end_word": <int>,
      "word_count": <int>,
      "topic": "<concise topic description in Spanish>",
      "keywords": ["<keyword1>", "<keyword2>", ...],
      "section_type": "<introduction|main_content|example|conclusion|transition>",
      "key_concepts": ["<concept1>", "<concept2>", ...],
      "transition_type": "<natural_break|topic_change|speaker_change|section_end>"
    }
  ],
  "format_detected": "<educational_linear|meeting_dialogue|technical_document>",
  "recommended_agent": "<simple_processor|meeting_processor>"
}

CRITICAL RULES:
- Ensure start_word and end_word cover ALL content with NO gaps or overlaps
- The last segment's end_word MUST equal total_words exactly
- Avoid segments smaller than 1500 words unless absolutely necessary
- Prefer clean breaks at paragraph or major sentence boundaries
- If content has clear section markers (headers, "vamos a hablar de", "ahora pasemos a"), USE them as break points
- For Spanish educational content, detect transitions like "entonces", "ahora bien", "por otro lado", "en cuanto a"
- Respond ONLY with the JSON, no additional text

QUALITY CHECKLIST before responding:
✓ All words accounted for (no gaps)
✓ No overlapping segments
✓ Reasonable segment sizes (2000-3000 words)
✓ Natural topic boundaries
✓ Valid JSON syntax
"""
)
def intelligent_segmenter():
    pass


@fast.agent(
    name="formatter_cleaner",
    model=DEFAULT_MODEL,
    instruction="""Apply Markdown formatting while preserving MAXIMUM content (85-95% retention target).

CONTENT PRESERVATION PRIORITY:
1. Keep ALL examples, case studies, company names, numbers, percentages
2. Keep ALL explanations, reasoning, methodology discussions  
3. Keep ALL specific recommendations and tools mentioned
4. Keep ALL comparative analysis and detailed breakdowns
5. Keep ALL personal anecdotes and learning experiences

FORMATTING TASKS:
1. Format with **bold** for key concepts, *italics* for emphasis
2. Create well-structured paragraphs with logical flow
3. Convert oral patterns to written style without losing meaning
4. Remove ONLY meaningless fillers: "eh", "bueno", "vale" when they add no value

EXPANSION RULES:
- If segment is short (<500 words), expand explanations and add detail
- If segment references examples, include them fully
- If numbers/percentages mentioned, include context and explanation
- Transform abbreviated explanations into comprehensive ones

CRITICAL: This is NOT summarization. This is content enhancement with maximum preservation.
Target: 85-95% content retention with professional formatting.
"""
)
def formatter_cleaner():
    pass


@fast.agent(
    name="titler",
    model=DEFAULT_MODEL,
    instruction="""Generate specific, descriptive titles for content segments based ONLY on content present.

RULES:
- Be specific and descriptive, not generic
- Use professional academic style  
- Maximum 8 words per title
- Base titles on actual content, not assumptions
- Include key concepts, company names, or specific topics mentioned

Example:
Segment about "Warren Buffett ha generado 20% anual durante 50 años"
Title: "Warren Buffett: Rendimiento Histórico del 20% Anual"
"""
)
def titler():
    pass


# ===== Q&A AGENTS =====

@fast.agent(
    name="question_generator",
    model=DEFAULT_MODEL,
    instruction="""Generate 3-5 high-value, specific questions from each content segment for educational purposes.

QUESTION TYPES TO PRIORITIZE:
1. **Conceptual**: "¿Qué significa exactamente [concepto específico mencionado]?"
2. **Examples**: "¿Cómo funciona el ejemplo de [caso específico] que se explica?"  
3. **Numbers & Data**: "¿Cuáles son los datos específicos de [cifras mencionadas]?"
4. **Comparisons**: "¿Cuáles son las diferencias entre [A] y [B] explicadas?"
5. **Applications**: "¿Cómo se aplicaría [método/concepto] en la práctica?"

CRITICAL RULES:
- Base questions ONLY on content actually present in the segment
- Include specific references: companies, percentages, examples, names
- Make questions practical and educational
- Avoid generic questions that could apply anywhere
- Reference concrete elements: "¿Cómo BMW logró márgenes del 10%?" vs "¿Qué son los márgenes?"

OUTPUT FORMAT:
Q1: [Specific question with concrete references from segment]
Q2: [Question about specific example/case mentioned]
Q3: [Question about specific data/numbers provided]
Q4: [Analytical question about specific concepts explained]
Q5: [Practical application question using segment examples]
"""
)
def question_generator():
    pass


@fast.agent(
    name="contextual_answerer",
    model=DEFAULT_MODEL,
    instruction="""Answer questions comprehensively using all available context: original STT, processed segment, and multimodal documents.

ANSWER STRUCTURE:
**Respuesta:**
[Detailed answer using all available context sources]

**Referencias:**
- **Transcripción STT**: "[Cita específica o paráfrasis del contenido original]"
- **Segmento**: [Número del segmento] - [Breve descripción de la información]
- **Documento adicional**: [Si aplica] "[Nombre del documento] - [Información específica]"
- **Secciones relacionadas**: [Si aplica] "Ver también Segmento X sobre [tema relacionado]"

**Datos específicos:**
- [Lista números exactos, porcentajes, fechas mencionados]
- [Nombres de empresas, personas, casos específicos]

**Contexto práctico:**
[Si aplica, explicación de cómo aplicar esta información]

CRITICAL RULES:
- Use ALL context: complete STT transcription + specific segment + multimodal docs
- Provide specific quotes and exact references
- Include all relevant numbers, percentages, company names
- Cross-reference related information from other segments when applicable
- Distinguish clearly between main transcription and supplementary documents
- Only state facts actually present in the sources
- Use Spanish throughout
- Maintain educational value and practical applicability
"""
)
def contextual_answerer():
    pass


# ===== SIMPLIFIED PROCESSOR =====

@fast.agent(
    name="simple_processor",
    model=DEFAULT_MODEL,
    instruction="""You are a content processing specialist for Spanish educational transcriptions.

CRITICAL RULES - LANGUAGE PRESERVATION:
- ALWAYS respond in the SAME language as the input (Spanish)
- NEVER translate or switch to English
- Preserve all Spanish terminology, expressions, and cultural context
- Maintain the educational tone and style of the original

TASK: Process ONE segment of transcribed content through these steps:

1. ADD PUNCTUATION: Add proper punctuation and capitalization while preserving 100% of words
2. FORMAT CONTENT: Apply markdown formatting while keeping ALL content (target: 90-95% retention)  
3. CREATE TITLE: Generate a specific, descriptive title based on the actual content
4. GENERATE Q&A: Create 3-4 educational questions with comprehensive answers

OUTPUT STRUCTURE (in Spanish):
## [Título específico basado en el contenido]

[Contenido formateado con markdown - conservar todo el contenido original]

### Preguntas y Respuestas

#### Pregunta 1: [Pregunta específica sobre el contenido]
**Respuesta:** [Respuesta completa con referencias al contenido original]

#### Pregunta 2: [Segunda pregunta]  
**Respuesta:** [Segunda respuesta completa]

[Continue for 3-4 questions total]

CONTENT PRESERVATION PRIORITY:
- Keep ALL examples, company names, numbers, percentages, specific data
- Keep ALL explanations, methodologies, tool recommendations  
- Keep ALL comparative analysis and detailed discussions
- Transform oral patterns to written style WITHOUT losing meaning
- Only remove obvious meaningless fillers like "eh", "bueno"

LANGUAGE: Always maintain Spanish throughout the entire response."""
)
def simple_processor():
    pass


# Import meeting processor agent
from .meeting_processor import fast as meeting_fast

# Export all agents and functions
__all__ = [
    "fast",
    "meeting_fast", 
    "adaptive_segment_content",
    "intelligent_segment_content",
    "simple_processor"
]