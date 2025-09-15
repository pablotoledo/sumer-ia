"""
Simple Agents - Fast-Agent Based Processing Without Complex Evaluators
=====================================================================

Simplified version that focuses on core functionality without complex evaluation.
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

# Create FastAgent instance
fast = FastAgent("SimpleDistributedSystem")


# ===== CORE PROCESSING AGENTS =====

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


@fast.agent(
    name="segmenter", 
    model=DEFAULT_MODEL,
    instruction="""Divide text into thematic segments while preserving ALL content.

RULES:
- Identify natural topic transitions and thematic boundaries
- Create segments of 200-800 words each when possible
- Mark segment boundaries with "---SEGMENT---"
- Preserve ALL original content - no summarizing or condensing
- Look for transition phrases like "entonces ahora", "por otro lado", "pasemos a"

Output format:
[First thematic segment with complete content]
---SEGMENT---  
[Second thematic segment with complete content]
---SEGMENT---
[Continue for all segments]
"""
)
def segmenter():
    pass


@fast.agent(
    name="formatter_cleaner",
    model=DEFAULT_MODEL,
    instruction="""Apply Markdown formatting and clean up speech patterns while preserving ALL content.

TASKS:
1. Format with **bold** for key concepts, *italics* for emphasis
2. Create well-structured paragraphs 
3. Remove ONLY obvious filler words: "eh", "bueno" (when meaningless), "vale"
4. Improve readability by rewriting oral patterns to written style

CRITICAL RULES:
- PRESERVE all examples, names, numbers, technical terms
- PRESERVE all semantic content and meaning
- Only remove/rewrite obvious speech patterns
- Transform "eh entonces Warren Buffett eh que es..." to "Warren Buffett, que es..."
- Keep ALL substantial information

Target: Transform oral speech to professional written text maintaining 90-95% of original content.
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

Example:
Segment about "Warren Buffett ha generado 20% anual durante 50 años"
Title: "Warren Buffett: Rendimiento Histórico del 20% Anual"
"""
)
def titler():
    pass


# ===== SIMPLE ORCHESTRATOR =====

@fast.orchestrator(
    name="simple_orchestrator",
    agents=[
        "punctuator",
        "segmenter", 
        "formatter_cleaner",
        "titler"
    ],
    instruction="""Process transcription through sequential workflow to create professional document.

WORKFLOW (SEQUENTIAL):
1. Send full text to 'punctuator' → get punctuated text
2. Send punctuated text to 'segmenter' → get segmented text with ---SEGMENT--- markers
3. For each segment:
   a. Send segment to 'formatter_cleaner' → get formatted and cleaned content  
   b. Send segment to 'titler' → get specific title
4. Assemble final document

ASSEMBLY FORMAT:
# [Generated Main Title Based on Content]

## Tabla de Contenidos
1. [Title 1](#title-1)
2. [Title 2](#title-2)

## [Title 1]
[Processed segment content]

## [Title 2] 
[Processed segment content]

---
**Procesado con Sistema Distribuido - LLM Agnóstico**
*Conservación de contenido: 85-95%*

CRITICAL: Final document should preserve 85-95% of original content while being professionally formatted.
"""
)
def simple_orchestrator_workflow():
    pass


# Export
__all__ = [
    "fast",
    "punctuator", 
    "segmenter",
    "formatter_cleaner",
    "titler",
    "simple_orchestrator_workflow"
]