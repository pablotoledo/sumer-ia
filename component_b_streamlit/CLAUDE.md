# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Sistema Multi-Agente de Procesamiento de Transcripciones** - An LLM-agnostic system that transforms Speech-to-Text transcriptions into structured educational documents with automatic Q&A generation. Built on FastAgent framework with specialized agents for distributed processing.

## Development Commands

### Installation & Setup
```bash
# Install dependencies (uses UV package manager)
uv sync

# Install UV if not present
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Running the Application
```bash
# Run Streamlit web interface (preferred)
uv run streamlit run streamlit_app/streamlit_app.py
# Alternative: fastagent-ui

# CLI processing
uv run python scripts/cli.py --input archivo.txt --output resultado.md

# Direct processing with robust_main.py
uv run python robust_main.py --input file.txt --output result.md
```

### Testing
```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test suites
uv run pytest tests/test_specialized_agents.py -v
uv run pytest tests/test_multimodal_context.py -v

# Integration test
uv run python tests/integration/test_streamlit_integration.py
```

## Architecture

### Multi-Agent Processing Pipeline

The system uses **FastAgent** for LLM orchestration with specialized agents, each having a single responsibility:

```
Content → Format Detection → Segmentation → Agent Pipeline → Assembled Output
```

**Key Design Principles:**
- **Clean Context Per Segment**: Each segment is processed with `async with agent.run()` creating a new session with no memory from previous segments
- **LLM-Agnostic**: Works with Azure OpenAI, Ollama, OpenAI, Anthropic Claude
- **Specialized Agents**: Each agent has one task (punctuation, formatting, titling, Q&A)
- **Intelligent Segmentation**: Two modes - GPT-4.1 semantic analysis (>3000 words) or programmatic splits (<3000 words)

### Core Components

**1. Segmentation System** (`src/intelligent_segmenter.py`)
- `IntelligentSegmenter`: Creates semantic segments using sentence transformers and clustering
- Target: 1000-2500 word segments with natural topic boundaries
- Uses `ContentSegment` dataclass with metadata (topics, complexity, tokens)

**2. Format Detection** (`src/content_format_detector.py`)
- Auto-detects: `DIARIZED_MEETING` vs `LINEAR_CONTENT`
- Returns `ContentFormat` enum with confidence score
- Triggers specialized processing pipeline

**3. Meeting Processor** (`src/meeting_processor.py`)
- `ConversationalSegmenter`: Segments meetings by topics, not length
- Extracts: decisions, action items, participants, timestamps
- Uses `ConversationalSegment` dataclass
- Agent: `meeting_processor` (different instruction set for meetings)

**4. Specialized Agents** (`src/agents/specialized_agents.py`)
- **punctuator** (temp=0.3): Adds punctuation only, preserves all words
- **formatter** (temp=0.4): Oral → written, removes fillers
- **titler** (temp=0.5): Generates 3-8 word titles
- **qa_generator** (temp=0.6): Creates 3-5 educational Q&A pairs
- **content_pipeline**: Chain sequence of all agents with `cumulative=True`

**5. Enhanced Agents** (`src/enhanced_agents.py`)
- `adaptive_segment_content()`: Entry point that auto-detects format and segments
- Returns `(segments, processing_agent)` tuple
- Delegates to meeting or standard processor based on format

**6. Rate Limit Handler** (`robust_main.py`)
- `RateLimitHandler`: Automatic retry with exponential backoff for 429 errors
- Configurable via `fastagent.config.yaml` rate_limiting section
- Presets: Conservative (45s), Balanced (30s), Aggressive (15s)

### Streamlit Interface

**Structure:**
- `streamlit_app/streamlit_app.py`: Main entry with navigation
- `streamlit_app/pages/0_inicio.py`: Processing page
- `streamlit_app/pages/1_configuracion.py`: LLM config management
- `streamlit_app/components/`: Reusable UI components
  - `config_manager.py`: YAML config CRUD operations
  - `ui_components.py`: Shared UI elements
  - `ui_widgets.py`: Custom widgets
  - `agent_interface.py`: Agent execution wrapper

**Session State Management:**
- `config_manager`: ConfigManager instance (persists across pages)
- Config loaded from `fastagent.config.yaml`

## Configuration

### fastagent.config.yaml

**Critical settings:**
```yaml
default_model: azure.gpt-4.1  # or generic.llama3.1 for Ollama

rate_limiting:
  requests_per_minute: 3
  delay_between_requests: 30      # Proactive prevention (delay between segments)
  max_retries: 3                  # Retries on 429 errors
  retry_base_delay: 60           # Initial backoff delay
  max_tokens_per_request: 50000
```

**Provider Examples:**
```yaml
# Azure OpenAI (recommended for production)
azure:
  api_key: "your-key"
  base_url: "https://your-resource.cognitiveservices.azure.com/"
  azure_deployment: "gpt-4.1"
  api_version: "2025-01-01-preview"

# Ollama (local development)
generic:
  api_key: "ollama"
  base_url: "http://localhost:11434/v1"
```

## Key File Locations

**Entry Points:**
- `streamlit_app/streamlit_app.py` - Web UI main
- `scripts/cli.py` - Command-line interface
- `robust_main.py` - Direct processing with rate limit handling

**Core Logic:**
- `src/enhanced_agents.py` - Main processing orchestration
- `src/agents/specialized_agents.py` - FastAgent definitions
- `src/intelligent_segmenter.py` - Semantic segmentation
- `src/meeting_processor.py` - Meeting-specific processing
- `src/content_format_detector.py` - Format auto-detection

**Utilities:**
- `src/utils/multimodal_context.py` - PDF/image/PPTX processing
- `src/qa_agents.py` - Standalone Q&A generation

**Tests:**
- `tests/test_specialized_agents.py` - Agent behavior tests
- `tests/integration/test_streamlit_integration.py` - E2E tests

## Important Patterns

### Agent Definition Pattern
```python
from mcp_agent.core.fastagent import FastAgent
from mcp_agent.core.request_params import RequestParams

fast = FastAgent("SystemName")

@fast.agent(
    name="agent_name",
    model=DEFAULT_MODEL,
    instruction="...",
    request_params=RequestParams(
        maxTokens=4096,
        use_history=False,  # Clean context per segment
        temperature=0.3
    )
)
def agent_name():
    pass
```

### Processing with Clean Context
```python
# Each segment gets a fresh session (no memory)
for segment in segments:
    async with agent.run() as agent_instance:
        result = await agent_instance.process(segment)
```

### Configuration Loading
```python
def load_config() -> dict:
    for config_path in ["fastagent.config.yaml", "../fastagent.config.yaml"]:
        if Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
    return {}
```

## Working with This Codebase

### When Adding New Agents
1. Define in `src/agents/specialized_agents.py` or appropriate module
2. Use `@fast.agent()` decorator with clear single-responsibility instruction
3. Set appropriate temperature (0.3 for mechanical, 0.6 for creative)
4. Add to chain if sequential processing needed
5. Use `use_history=False` for segment-level processing

### When Modifying Segmentation
- Programmatic segmentation: `IntelligentSegmenter` in `src/intelligent_segmenter.py`
- Meeting segmentation: `ConversationalSegmenter` in `src/meeting_processor.py`
- Format detection: `analyze_content_format()` in `src/content_format_detector.py`

### When Adjusting Rate Limits
- Edit `fastagent.config.yaml` rate_limiting section
- S0 tier Azure OpenAI: Use Conservative preset (45s delay_between_requests)
- Standard tier: Balanced preset (30s)
- Local Ollama: Aggressive preset (0s delay, high RPM)

### Common Debugging
- Check `fastagent.jsonl` for agent interaction logs
- Set `logger.level: debug` in config for verbose output
- Use `logger.show_tools: true` to see tool calls
- Verify config with `ConfigManager.validate_config()` in Streamlit

## Language & Style

**Code:** Python 3.10+, async/await patterns
**UI Text:** Spanish (transcriptions typically in Spanish)
**Documentation:** Mixed Spanish/English
**Agent Instructions:** English (for LLM clarity)

## Dependencies

**Core:**
- `fast-agent-mcp` - FastAgent framework
- `streamlit` - Web interface
- `sentence-transformers` - Semantic embeddings
- `nltk` - Text tokenization
- `tiktoken` - Token counting

**ML/AI:**
- `torch` - PyTorch backend
- `transformers` - HuggingFace models
- `hdbscan`, `scikit-learn` - Clustering

**Documents:**
- `PyPDF2`, `pypdf` - PDF processing
- `python-pptx` - PowerPoint processing
- `Pillow` - Image handling
