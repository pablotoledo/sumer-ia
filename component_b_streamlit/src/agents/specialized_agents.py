"""
Agentes especializados siguiendo arquitectura FastAgent
Cada agente tiene una responsabilidad única y bien definida
"""

from pathlib import Path
from mcp_agent.core.fastagent import FastAgent
from mcp_agent.core.request_params import RequestParams
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

# Create FastAgent instance for specialized agents
fast = FastAgent("Content Processing Pipeline")


# ============================================
# AGENTE 1: PUNCTUATOR
# Responsabilidad: Solo agregar puntuación
# ============================================
@fast.agent(
    name="punctuator",
    model=DEFAULT_MODEL,
    instruction="""You are a punctuation specialist.

TASK: Add proper punctuation to unpunctuated text.

RULES:
- Add periods, commas, question marks, exclamation marks where needed
- Preserve original wording completely
- DO NOT change words or add/remove content
- DO NOT format or restructure
- Output only the punctuated text
- Maintain Spanish language if input is Spanish

INPUT: unpunctuated text
OUTPUT: same text with proper punctuation""",
    request_params=RequestParams(
        maxTokens=4096,
        use_history=False,
        temperature=0.3  # Baja temperatura para tarea mecánica
    )
)
def punctuator():
    pass


# ============================================
# AGENTE 2: FORMATTER
# Responsabilidad: Solo formatear estructura
# ============================================
@fast.agent(
    name="formatter",
    model=DEFAULT_MODEL,
    instruction="""You are a content formatting specialist.

TASK: Transform oral speech patterns into written prose.

TRANSFORMATIONS:
- "gonna" → "going to" (for English)
- "vamos a ver" → maintain as is (for Spanish)
- Remove filler words: "um", "uh", "like", "you know", "eh", "bueno" (when meaningless)
- Consolidate repetitions
- Organize into paragraphs
- Apply basic markdown formatting (**bold**, *italic*)

PRESERVE:
- All substantive content
- Technical terms
- Names and specific references
- Overall meaning
- Original language (Spanish/English)

CRITICAL RULES:
- NEVER translate between languages
- Maintain educational tone
- If input is Spanish, output must be Spanish

TARGET: 85-95% content retention
OUTPUT: Clean formatted text only""",
    request_params=RequestParams(
        maxTokens=4096,
        use_history=False,
        temperature=0.4
    )
)
def formatter():
    pass


# ============================================
# AGENTE 3: TITLER
# Responsabilidad: Solo crear títulos
# ============================================
@fast.agent(
    name="titler",
    model=DEFAULT_MODEL,
    instruction="""You are a title generation specialist.

TASK: Create a descriptive title for a text segment.

RULES:
- Title must be 3-8 words
- Must capture main topic/theme
- Use title case (or Spanish title conventions if content is Spanish)
- No special characters except hyphens
- Include specific references (company names, concepts) when present
- DO NOT modify the content itself
- Match the language of the input content

EXAMPLES:
- Content about "Warren Buffett 20% returns" → "Warren Buffett: Rendimiento Histórico del 20%"
- Content about AI → "Artificial Intelligence Applications"

INPUT: text segment
OUTPUT: A single title line only""",
    request_params=RequestParams(
        maxTokens=256,
        use_history=False,
        temperature=0.5
    )
)
def titler():
    pass


# ============================================
# AGENTE 4: QA_GENERATOR
# Responsabilidad: Solo generar Q&A
# ============================================
@fast.agent(
    name="qa_generator",
    model=DEFAULT_MODEL,
    instruction="""You are a Q&A generation specialist.

TASK: Generate high-quality questions and answers from content.

QUESTION TYPES:
1. Factual (What/When/Where)
2. Conceptual (Why/How)
3. Application (How would you...)

RULES:
- Generate 3-5 questions per segment
- Questions must be answerable from the content
- Answers must be comprehensive (2-4 sentences)
- Cover different aspects of the content
- Progressive difficulty (easy → medium → hard)
- Include specific references from the content
- Match the language of the input (if Spanish input, generate Spanish Q&A)

OUTPUT FORMAT (adapt language to input):
#### Pregunta 1: [question]
**Respuesta:** [answer]

#### Pregunta 2: [question]
**Respuesta:** [answer]

[continue...]

CRITICAL: Base questions ONLY on content actually present. Include specific data, names, examples mentioned.""",
    request_params=RequestParams(
        maxTokens=2048,
        use_history=False,
        temperature=0.6  # Temperatura media para creatividad controlada
    )
)
def qa_generator():
    pass


# ============================================
# CADENA DE PROCESAMIENTO
# ============================================
@fast.chain(
    name="content_pipeline",
    sequence=["punctuator", "formatter", "titler", "qa_generator"],
    instruction="Complete content processing pipeline with specialized agents",
    cumulative=True  # Cada agente recibe resultado del anterior
)
def content_pipeline():
    pass


# Export the FastAgent instance for use in other modules
__all__ = ["fast", "content_pipeline"]