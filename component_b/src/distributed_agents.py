"""
Distributed Agents - Fast-Agent Based Multi-Provider Processing
=============================================================

This module defines the distributed agent architecture using fast-agent decorators.
Each agent can run on different LLM providers simultaneously for maximum parallelization.
"""

from pathlib import Path
from mcp_agent.core.fastagent import FastAgent
import yaml


def load_prompt(prompt_file: str) -> str:
    """Load a prompt from file."""
    # Try current directory first, then parent directories
    for base_path in [Path("."), Path(".."), Path("../prompts")]:
        prompt_path = base_path / prompt_file
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
    
    # If not found, return a basic prompt
    return f"You are a specialized AI assistant. Process the following content according to your role."


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
fast = FastAgent("DistributedTranscriptionSystem")


# ===== CORE PROCESSING AGENTS =====

@fast.agent(
    name="punctuator",
    model=DEFAULT_MODEL,
    instruction="""You are a punctuation specialist. Your ONLY task is to add proper punctuation and capitalization to speech-to-text content while preserving 100% of the original words and content.

RULES:
- Add punctuation marks (periods, commas, question marks, exclamation points)
- Capitalize proper nouns and sentence beginnings  
- DO NOT remove, change, or rephrase any words
- DO NOT eliminate filler words like "eh", "bueno", "entonces" 
- Keep ALL content exactly as provided, just add punctuation

Example:
Input: "bueno eh entonces vamos a hablar sobre Warren Buffett que es el mejor inversor"
Output: "Bueno, eh, entonces vamos a hablar sobre Warren Buffett, que es el mejor inversor."
"""
)
def punctuator():
    pass


@fast.agent(
    name="segmenter", 
    model=DEFAULT_MODEL,
    instruction="""You are a content segmentation specialist. Your task is to divide text into thematic segments while preserving ALL content.

RULES:
- Identify natural topic transitions and thematic boundaries
- Create segments of 100-500 words each when possible
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
    name="titler",
    model=DEFAULT_MODEL, 
    instruction="""You are a title generation specialist. Create specific, descriptive titles for content segments.

RULES:
- Generate titles based ONLY on content present in the segment
- Be specific and descriptive, not generic
- Use professional academic style
- Avoid summarizing - titles should reflect actual content
- Maximum 8 words per title

Example:
Segment about "Warren Buffett ha generado 20% anual durante 50 años"
Title: "Warren Buffett: Rendimiento Histórico del 20% Anual"
"""
)
def titler():
    pass


@fast.agent(
    name="formatter",
    model=DEFAULT_MODEL,
    instruction=load_prompt("formatter.md") if Path("formatter.md").exists() else """You are a Markdown formatting specialist. Apply professional formatting while preserving 100% of content.

APPLY:
- **Bold** for key concepts and important terms
- *Italics* for technical terms or subtle emphasis  
- Well-structured paragraphs (max 4 sentences each)
- Lists when appropriate
- `Code formatting` for technical terms
- Clear separation between ideas

RULES:
- ZERO changes to semantic content
- PRESERVE all examples, figures, names, and numbers
- DO NOT add external information or explanations
- DO NOT remove any information from original
- DO NOT change technical terminology or proper names
- ONLY improve visual presentation and readability
"""
)
def formatter():
    pass


@fast.agent(
    name="stylistic_cleaner", 
    model=DEFAULT_MODEL,
    instruction=load_prompt("stylistic_cleaner.md") if Path("stylistic_cleaner.md").exists() else """You are a stylistic improvement specialist. Transform oral speech into written text while maintaining ALL content.

ELIMINATE ONLY:
- "eh" (always filler)
- "vale" (confirmation)  
- "bueno" (when it adds no information)
- Unnecessary repetitions

ALWAYS PRESERVE:
- ALL semantic content
- Specific examples and cases
- All figures and data
- Proper names
- Complete explanations
- Technical terminology

PRINCIPLE: REWRITE for clarity while maintaining ALL specific information.

Example:
Input: "eh bueno entonces Warren Buffett eh que es el mejor inversor vale ha generado un 20% anual durante 50 años que es una barbaridad entonces por ejemplo ha invertido en Apple"
Output: "Warren Buffett, que es el mejor inversor, ha generado un 20% anual durante 50 años, lo cual es extraordinario. Por ejemplo, ha invertido en Apple"
"""
)
def stylistic_cleaner():
    pass


@fast.agent(
    name="quality_evaluator",
    model=DEFAULT_MODEL,
    instruction=load_prompt("quality_evaluator.md") if Path("quality_evaluator.md").exists() else """You are a quality verification specialist. Compare original vs processed text to verify content preservation.

EVALUATE:
1. CONTENT CONSERVATION (>=95%): Are ALL examples, figures, names maintained?
2. SEMANTIC FIDELITY (>=98%): Is all essential information preserved? 
3. HALLUCINATION DETECTION (<=5%): Was any information added that wasn't present?
4. INAPPROPRIATE SUMMARIZATION (<=10%): Was detail level maintained?

RESPONSE FORMAT:
CONSERVATION: [0.00-1.00]
FIDELITY: [0.00-1.00] 
HALLUCINATIONS: [0.00-1.00]
INAPPROPRIATE_SUMMARY: [0.00-1.00]
VERDICT: PASS/FAIL
OBSERVATIONS: [only if FAIL]

CRITERIA FOR PASS:
- Conservation >= 0.95 (examples, figures, names maintained)
- Fidelity >= 0.98 (essential information preserved)
- Hallucinations <= 0.05 (no false information added)
- Inappropriate_summary <= 0.10 (detail level maintained)
"""
)
def quality_evaluator():
    pass


@fast.agent(
    name="multimodal_enricher",
    model=DEFAULT_MODEL,
    instruction="""You are a multimodal content enrichment specialist. Use visual context (images, slides, documents) to enhance and correct transcriptions.

TASKS:
- Correct acronyms and technical terms using visual context
- Add context from slides/documents when mentioned but not fully explained
- Fix terminology based on visual evidence
- Enhance examples with visual information
- Maintain perfect fidelity to transcribed content while enriching

RULES:
- Only add information that clarifies or corrects existing content
- Never contradict the spoken content
- Mark enrichments clearly: [Visual context: ...]
- Preserve all original speech content
"""
)
def multimodal_enricher():
    pass


# ===== WORKFLOW PATTERNS =====

@fast.evaluator_optimizer(
    name="verified_formatter",
    generator="formatter",
    evaluator="quality_evaluator",
    max_refinements=2
)
def verified_formatter_workflow():
    """Formatter with quality verification and iterative refinement."""
    pass


@fast.evaluator_optimizer(
    name="verified_stylistic_cleaner", 
    generator="stylistic_cleaner",
    evaluator="quality_evaluator",
    max_refinements=3
)
def verified_stylistic_cleaner_workflow():
    """Stylistic cleaner with quality verification and iterative refinement."""
    pass


# ===== DISTRIBUTED ORCHESTRATOR =====

@fast.orchestrator(
    name="distributed_orchestrator",
    agents=[
        "punctuator",
        "segmenter", 
        "titler",
        "verified_formatter",
        "verified_stylistic_cleaner"
    ],
    instruction="""You are the master orchestrator of a distributed transcription processing system.

WORKFLOW (SEQUENTIAL):
1. PASO 1: Send full text to 'punctuator' → get punctuated text
2. PASO 2: Send punctuated text to 'segmenter' → get segmented text with ---SEGMENT--- markers
3. PASO 3: For each segment in parallel:
   a. Send segment to 'titler' → get specific title
   b. Send segment to 'verified_formatter' → get formatted content  
   c. Send formatted content to 'verified_stylistic_cleaner' → get cleaned content
4. PASO 4: Assemble final document with titles and processed segments

CRITICAL RULES:
- Use output from each step as input for next step (sequential dependency)
- Process segments in parallel during PASO 3
- Preserve ALL content through pipeline
- Final document should be 80-90% of original word count
- Generate professional Markdown document with table of contents

OUTPUT FORMAT:
# [Generated Title Based on Content]

## Tabla de Contenidos
1. [Title 1](#title-1)
2. [Title 2](#title-2)
...

## [Title 1]
[Processed segment content]

## [Title 2] 
[Processed segment content]

---

**Procesado con Sistema Distribuido Agnóstico de LLM**
"""
)
def distributed_orchestrator_workflow():
    """Master orchestrator for distributed processing workflow."""
    pass


@fast.orchestrator(
    name="multimodal_distributed_orchestrator",
    agents=[
        "multimodal_enricher",
        "punctuator",
        "segmenter",
        "titler", 
        "verified_formatter",
        "verified_stylistic_cleaner"
    ],
    instruction="""You are the master orchestrator for multimodal distributed transcription processing.

WORKFLOW (SEQUENTIAL WITH MULTIMODAL):
1. PASO 0: If multimedia available, send to 'multimodal_enricher' → get enriched transcription
2. PASO 1-4: Same as distributed_orchestrator but using enriched content

Use the multimodal_enricher when visual context (slides, images, documents) is provided to enhance accuracy and context.
"""
)
def multimodal_distributed_orchestrator_workflow():
    """Master orchestrator with multimodal capabilities."""
    pass


# ===== PARALLEL PROCESSING CHAINS =====

@fast.chain(
    name="segment_processor",
    sequence=["titler", "verified_formatter", "verified_stylistic_cleaner"]
)
def segment_processing_chain():
    """Process a single segment through the complete pipeline.""" 
    pass


# Export all agents and workflows
__all__ = [
    "fast",
    "punctuator", 
    "segmenter",
    "titler",
    "formatter",
    "stylistic_cleaner", 
    "quality_evaluator",
    "multimodal_enricher",
    "verified_formatter_workflow",
    "verified_stylistic_cleaner_workflow", 
    "distributed_orchestrator_workflow",
    "multimodal_distributed_orchestrator_workflow",
    "segment_processing_chain"
]