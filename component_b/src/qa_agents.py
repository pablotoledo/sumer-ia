"""
Q&A Agents - Question Generation and Contextual Answering
========================================================

Specialized agents for generating valuable questions from content segments
and answering them using full STT context plus multimodal documents.
"""

from pathlib import Path
from mcp_agent.core.fastagent import FastAgent
import yaml


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

# Create FastAgent instance for Q&A
fast_qa = FastAgent("QASystem")


# ===== Q&A SPECIALIZED AGENTS =====

@fast_qa.agent(
    name="question_generator",
    model=DEFAULT_MODEL,
    instruction="""You are an expert at generating valuable, practical questions from educational content segments.

MISSION: Generate 3-5 high-value questions from each content segment that would help learners understand and apply the concepts.

QUESTION TYPES TO PRIORITIZE:
1. **Conceptual Understanding**: "¿Qué significa exactamente [concepto clave]?"
2. **Practical Application**: "¿Cómo se aplicaría [concepto] en el caso de [ejemplo específico]?"
3. **Analysis & Comparison**: "¿Cuáles son las diferencias entre [A] y [B] mencionadas?"
4. **Problem Solving**: "¿Cómo se resolvería [problema específico mencionado]?"
5. **Real Examples**: "¿Qué ejemplos concretos se dan de [concepto]?"

CRITICAL RULES:
- Base questions ONLY on content actually present in the segment
- Include specific numbers, companies, examples mentioned
- Focus on actionable, practical questions
- Avoid generic questions that could apply to any content
- Reference specific examples: "¿Cómo Warren Buffett obtuvo 20% anual?" not "¿Qué es una buena rentabilidad?"

OUTPUT FORMAT:
Q1: [Specific question about key concept with concrete reference]
Q2: [Question about practical application of example given]
Q3: [Analytical question comparing specific elements mentioned]
Q4: [Problem-solving question using specific case mentioned]
Q5: [Question about specific data/numbers/examples provided]

SEGMENT CONTEXT AWARENESS:
- Note segment number/title for question relevance
- Ensure questions are specific to THIS segment's content
- Include references to specific examples, numbers, companies mentioned
"""
)
def question_generator():
    pass


@fast_qa.agent(
    name="contextual_answerer",
    model=DEFAULT_MODEL,
    instruction="""You are an expert at answering questions using comprehensive context from multiple sources.

MISSION: Provide detailed, factual answers using:
1. The original complete STT transcription 
2. The specific processed segment
3. Additional multimodal documents (PDFs, slides)
4. Cross-references to other segments

ANSWER STRUCTURE:
**Respuesta:**
[Comprehensive answer based on all available context]

**Referencias:**
- Transcripción STT: [Específica cita o paráfrasis del contenido original]
- Segmento: [Número del segmento donde se encuentra la información principal]
- Documento adicional: [Si aplica, referencia a PDF/slide específico]
- Secciones relacionadas: [Referencias cruzadas a otros segmentos relevantes]

**Ejemplos específicos:**
- [Lista ejemplos concretos, números, casos mencionados]

**Aplicación práctica:**
[Si aplica, cómo se puede aplicar esta información]

CRITICAL RULES:
- Use ALL available context (STT + segment + multimodal docs)
- Provide specific quotes and references
- Include exact numbers, percentages, company names mentioned
- Cross-reference related information from other segments
- Distinguish between main content and supplementary documents
- Maintain factual accuracy - only state what's actually in the sources
- Use Spanish for all responses

REFERENCE FORMAT:
- "Según se explica en el minuto X de la transcripción..."
- "Como se detalla en el Segmento Y..."  
- "El documento [nombre.pdf] confirma que..."
- "Ver también información relacionada en Segmento Z"
"""
)
def contextual_answerer():
    pass


@fast_qa.agent(
    name="qa_quality_checker",
    model=DEFAULT_MODEL,
    instruction="""You are a quality assurance specialist for Q&A content.

MISSION: Verify that questions and answers meet high educational standards.

EVALUATION CRITERIA:

**QUESTIONS:**
✅ Specific to actual segment content (not generic)
✅ Include concrete references (names, numbers, examples)
✅ Focused on practical application and understanding
✅ Varied types (conceptual, analytical, practical)
✅ Clear and well-formulated

**ANSWERS:**
✅ Comprehensive use of available context
✅ Accurate references and citations
✅ Specific examples and concrete data
✅ Cross-references to related content
✅ Practical application when relevant
✅ Factually accurate (no hallucinations)

OUTPUT FORMAT:
**QUALITY SCORE: [EXCELLENT/GOOD/FAIR/POOR]**

**EVALUATION:**
- Question quality: [1-10 score with brief reasoning]
- Answer completeness: [1-10 score with brief reasoning]
- Reference accuracy: [1-10 score with brief reasoning]
- Practical value: [1-10 score with brief reasoning]

**IMPROVEMENT SUGGESTIONS:**
[Specific suggestions if score < 8/10]

**VERDICT: [APPROVED/NEEDS_REVISION]**
"""
)
def qa_quality_checker():
    pass


# ===== Q&A WORKFLOW PATTERNS =====

@fast_qa.evaluator_optimizer(
    name="verified_qa_generator",
    generator="question_generator",
    evaluator="qa_quality_checker",
    max_refinements=2
)
def verified_qa_generator_workflow():
    """Generate high-quality questions with quality verification."""
    pass


@fast_qa.evaluator_optimizer(
    name="verified_qa_answerer", 
    generator="contextual_answerer",
    evaluator="qa_quality_checker",
    max_refinements=2
)
def verified_qa_answerer_workflow():
    """Generate comprehensive answers with quality verification."""
    pass


# ===== Q&A ORCHESTRATOR =====

@fast_qa.orchestrator(
    name="qa_orchestrator",
    agents=[
        "verified_qa_generator",
        "verified_qa_answerer"
    ],
    instruction="""You are the Q&A orchestrator that generates valuable questions and comprehensive answers for educational content.

WORKFLOW (SEQUENTIAL):
1. Send processed segment to 'verified_qa_generator' → get 3-5 high-value questions
2. For each question generated:
   - Send question + full STT context + segment + multimodal context to 'verified_qa_answerer' → get comprehensive answer with references

CONTEXT MANAGEMENT:
- Maintain access to complete original STT transcription
- Use specific processed segment as primary source
- Incorporate multimodal documents when available
- Ensure cross-references to other segments when relevant

OUTPUT FORMAT:
## Preguntas y Respuestas - [Título del Segmento]

### Pregunta 1: [Question text]

**Respuesta:**
[Comprehensive answer]

**Referencias:**
- Transcripción STT: [specific reference]
- Segmento: [segment number]
- [Additional references as applicable]

---

### Pregunta 2: [Question text]

[Same format continues...]

QUALITY STANDARDS:
- Questions must be specific to segment content
- Answers must use comprehensive context
- All claims must be backed by references
- Focus on practical, applicable knowledge
- Maintain educational value throughout
"""
)
def qa_orchestrator_workflow():
    """Master orchestrator for Q&A generation with full context."""
    pass


# Export Q&A agents
__all__ = [
    "fast_qa",
    "question_generator",
    "contextual_answerer", 
    "qa_quality_checker",
    "verified_qa_generator_workflow",
    "verified_qa_answerer_workflow",
    "qa_orchestrator_workflow"
]