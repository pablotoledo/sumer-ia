"""
Enhanced Agents - Complete System with Q&A Integration
=====================================================

Enhanced version that combines content processing with intelligent Q&A generation.
"""

from pathlib import Path
from mcp_agent.core.fastagent import FastAgent
from typing import List, Tuple
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


def intelligent_segment_content(content: str) -> List[str]:
    """
    Segment content using intelligent programmatic methods (NO LLM).
    Guarantees 100% content preservation.
    """
    segmenter = IntelligentSegmenter(target_segment_size=1200, max_segments=20)
    
    try:
        segments = segmenter.create_semantic_segments(content)
        
        # Convert to simple string list format expected by fast-agent
        segment_texts = []
        for i, segment in enumerate(segments, 1):
            segment_text = f"[SEGMENT {i}]\n{segment.content}\n---SEGMENT---"
            segment_texts.append(segment_text)
        
        # Verification: Check total word count preservation
        original_words = len(content.split())
        total_segment_words = sum(len(seg.content.split()) for seg in segments)
        
        retention_rate = (total_segment_words / original_words) * 100
        print(f"🔍 Segmentation: {original_words} → {total_segment_words} words ({retention_rate:.1f}% retention)")
        
        return segment_texts
        
    except Exception as e:
        print(f"⚠️ Intelligent segmenter failed: {e}")
        # Fallback: Simple paragraph-based segmentation
        paragraphs = content.split('\n\n')
        segments = []
        current_segment = []
        current_word_count = 0
        
        for para in paragraphs:
            para_words = len(para.split())
            if current_word_count + para_words > 1500 and current_segment:
                segments.append('\n\n'.join(current_segment))
                current_segment = [para]
                current_word_count = para_words
            else:
                current_segment.append(para)
                current_word_count += para_words
        
        if current_segment:
            segments.append('\n\n'.join(current_segment))
        
        # Format for fast-agent
        formatted_segments = []
        for i, seg in enumerate(segments, 1):
            formatted_segments.append(f"[SEGMENT {i}]\n{seg}\n---SEGMENT---")
        
        return formatted_segments


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