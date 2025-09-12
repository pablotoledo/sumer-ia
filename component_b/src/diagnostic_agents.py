"""
Diagnostic Agents - Content Retention Analysis
============================================

Simple agents to test where content is being lost in the pipeline.
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
fast = FastAgent("DiagnosticSystem")


@fast.agent(
    name="content_preserver",
    model=DEFAULT_MODEL,
    instruction="""You are a content preservation specialist. Your ONLY job is to preserve content.

TASK: Take the input text and return it with MINIMAL changes while adding basic formatting.

RULES:
1. PRESERVE EVERY SINGLE WORD from input
2. Add basic Markdown formatting: **bold** for key terms, *italics* for emphasis
3. Structure into paragraphs for readability 
4. DO NOT summarize, compress, or shorten anything
5. DO NOT remove examples, numbers, names, or explanations
6. If you must remove filler words ("eh", "bueno"), replace them with [...]

VERIFICATION: Your output word count should be 90-100% of input word count.

EXAMPLE:
Input (20 words): "Bueno, eh, entonces Warren Buffett eh que es el mejor inversor del mundo, eh, ha ganado mucho dinero."
Output (18 words): "Bueno, [...], entonces **Warren Buffett**, que es el mejor inversor del mundo, [...], ha ganado mucho dinero."

CRITICAL: This is content PRESERVATION, not content IMPROVEMENT through reduction.
"""
)
def content_preserver():
    pass


@fast.agent(
    name="word_counter",
    model=DEFAULT_MODEL,
    instruction="""You are a word counting specialist.

TASK: Count the exact number of words in the provided text and provide a detailed breakdown.

OUTPUT FORMAT:
```
WORD COUNT ANALYSIS:
- Total words: [NUMBER]
- Estimated characters: [NUMBER]
- Paragraphs: [NUMBER]
- Key entities mentioned: [LIST OF 5-10 KEY TERMS]
- Content density: [High/Medium/Low]
```

Count every word including articles, prepositions, and filler words.
"""
)
def word_counter():
    pass


@fast.orchestrator(
    name="diagnostic_orchestrator",
    agents=["word_counter", "content_preserver", "word_counter"],
    instruction="""Run diagnostic analysis to identify content loss points.

WORKFLOW:
1. Send input to 'word_counter' → get input word count baseline
2. Send input to 'content_preserver' → get preserved content  
3. Send preserved content to 'word_counter' → get output word count

ANALYSIS:
- Calculate retention percentage: (output_words / input_words) * 100
- Identify specific content losses
- Report retention success/failure

TARGET: 90-100% retention for this simple preservation test.

OUTPUT FORMAT:
# Diagnostic Analysis Results

## Input Analysis
[Results from step 1]

## Preserved Content
[Results from step 2]  

## Output Analysis  
[Results from step 3]

## Retention Summary
- **Input words**: [NUMBER]
- **Output words**: [NUMBER] 
- **Retention rate**: [PERCENTAGE]%
- **Status**: [SUCCESS/FAILURE - if <90% retention]
- **Content lost**: [Description of what was lost]
"""
)
def diagnostic_orchestrator_workflow():
    pass


# Export diagnostic agents
__all__ = [
    "fast",
    "content_preserver",
    "word_counter", 
    "diagnostic_orchestrator_workflow"
]