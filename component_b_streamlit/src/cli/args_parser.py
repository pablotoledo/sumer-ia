"""
Argument Parser for FastAgent CLI
==================================

Defines all command-line arguments and their validation.
"""

import argparse
from typing import Optional


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for FastAgent CLI."""

    parser = argparse.ArgumentParser(
        prog='fastagent-cli',
        description='FastAgent CLI - Transform STT transcriptions into educational documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic processing
  %(prog)s -i transcription.txt -o output.md

  # With Azure OpenAI
  %(prog)s -i input.txt -o output.md --model azure.gpt-4.1

  # With preset for rate-limited environments
  %(prog)s -i input.txt -o output.md --preset conservative

  # With additional documents (multimodal)
  %(prog)s -i input.txt -o output.md -d slides.pdf notes.txt

  # Intelligent segmentation for large content
  %(prog)s -i input.txt -o output.md --segmentation intelligent

  # Meeting processing with specific agent
  %(prog)s -i meeting.txt -o output.md --agent meeting_processor

  # Using environment variables
  export FASTAGENT_MODEL=azure.gpt-4.1
  export FASTAGENT_DELAY=45
  %(prog)s -i input.txt -o output.md

  # Verbose mode with dry run
  %(prog)s -i input.txt -o output.md -v --dry-run

Configuration Priority (highest to lowest):
  1. Command-line arguments
  2. Environment variables
  3. fastagent.config.yaml
  4. Default values

Environment Variables:
  FASTAGENT_PROVIDER       - LLM provider (azure, ollama, openai, anthropic)
  FASTAGENT_MODEL          - Model name (azure.gpt-4.1, generic.llama3.1, etc.)
  FASTAGENT_DELAY          - Delay between requests in seconds (default: 30)
  FASTAGENT_MAX_RETRIES    - Maximum retries for rate limits (default: 3)
  FASTAGENT_RETRY_DELAY    - Base retry delay in seconds (default: 60)
  FASTAGENT_OUTPUT_DIR     - Default output directory

  # Azure OpenAI
  AZURE_API_KEY            - Azure OpenAI API key
  AZURE_BASE_URL           - Azure resource base URL
  AZURE_DEPLOYMENT         - Azure deployment name
  AZURE_API_VERSION        - Azure API version

  # Ollama
  OLLAMA_BASE_URL          - Ollama server URL (default: http://localhost:11434/v1)

  # OpenAI
  OPENAI_API_KEY           - OpenAI API key

  # Anthropic
  ANTHROPIC_API_KEY        - Anthropic API key

Presets:
  fast         - Quick processing, programmatic segmentation, no Q&A
  balanced     - Good balance of speed and quality (default)
  conservative - For rate-limited environments (S0 tier Azure)
  intelligent  - Best quality, AI-powered segmentation, full Q&A
        """
    )

    # Required arguments
    required_group = parser.add_argument_group('Required Arguments')
    required_group.add_argument(
        '-i', '--input',
        type=str,
        required=True,
        help='Input transcription file (TXT, MD, PDF, DOCX)'
    )
    required_group.add_argument(
        '-o', '--output',
        type=str,
        required=True,
        help='Output file path (MD or TXT)'
    )

    # Input/Output options
    io_group = parser.add_argument_group('Input/Output Options')
    io_group.add_argument(
        '-d', '--documents',
        type=str,
        nargs='*',
        default=[],
        help='Additional documents for multimodal context (PDF, TXT, MD, images)'
    )
    io_group.add_argument(
        '--output-format',
        type=str,
        choices=['md', 'txt', 'markdown', 'text'],
        default='md',
        help='Output format (default: md)'
    )

    # Model and Provider configuration
    model_group = parser.add_argument_group('Model Configuration')
    model_group.add_argument(
        '--model',
        type=str,
        default=None,
        help='Model to use (e.g., azure.gpt-4.1, generic.llama3.1) (env: FASTAGENT_MODEL)'
    )
    model_group.add_argument(
        '--provider',
        type=str,
        choices=['azure', 'ollama', 'openai', 'anthropic', 'generic'],
        default=None,
        help='LLM provider (env: FASTAGENT_PROVIDER)'
    )
    model_group.add_argument(
        '--config',
        type=str,
        default='fastagent.config.yaml',
        help='Configuration file path (default: fastagent.config.yaml)'
    )

    # Processing configuration
    processing_group = parser.add_argument_group('Processing Options')
    processing_group.add_argument(
        '--agent',
        type=str,
        choices=['auto', 'simple_processor', 'meeting_processor'],
        default='auto',
        help='Agent to use for processing (default: auto-detect)'
    )
    processing_group.add_argument(
        '--segmentation',
        type=str,
        choices=['intelligent', 'programmatic', 'auto'],
        default='auto',
        help='Segmentation method (default: auto - intelligent for >3000 words)'
    )
    processing_group.add_argument(
        '--enable-qa',
        action='store_true',
        default=True,
        help='Enable Q&A generation (default: enabled)'
    )
    processing_group.add_argument(
        '--no-qa',
        action='store_false',
        dest='enable_qa',
        help='Disable Q&A generation'
    )
    processing_group.add_argument(
        '--qa-questions',
        type=int,
        default=4,
        help='Number of Q&A questions per segment (default: 4)'
    )

    # Rate limiting configuration
    rate_group = parser.add_argument_group('Rate Limiting Options')
    rate_group.add_argument(
        '--preset',
        type=str,
        choices=['fast', 'balanced', 'conservative', 'intelligent'],
        default=None,
        help='Configuration preset (overrides individual rate limit settings)'
    )
    rate_group.add_argument(
        '--delay',
        type=int,
        default=None,
        help='Delay between requests in seconds (env: FASTAGENT_DELAY)'
    )
    rate_group.add_argument(
        '--max-retries',
        type=int,
        default=None,
        help='Maximum retries for rate limits (env: FASTAGENT_MAX_RETRIES)'
    )
    rate_group.add_argument(
        '--retry-delay',
        type=int,
        default=None,
        help='Base retry delay in seconds (env: FASTAGENT_RETRY_DELAY)'
    )

    # General options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bar'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate processing without making LLM calls'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='FastAgent CLI v1.0.0'
    )

    return parser


def validate_args(args: argparse.Namespace) -> bool:
    """
    Validate parsed arguments for consistency.

    Returns:
        True if valid, raises ValueError otherwise
    """
    # Validate Q&A questions count
    if args.qa_questions < 1 or args.qa_questions > 10:
        raise ValueError("Q&A questions must be between 1 and 10")

    # Validate delays
    if args.delay is not None and args.delay < 0:
        raise ValueError("Delay must be non-negative")

    if args.retry_delay is not None and args.retry_delay < 0:
        raise ValueError("Retry delay must be non-negative")

    if args.max_retries is not None and args.max_retries < 0:
        raise ValueError("Max retries must be non-negative")

    # Validate output format matches output file extension
    output_ext = args.output.split('.')[-1].lower()
    if output_ext not in ['md', 'txt', 'markdown']:
        raise ValueError(f"Output file must have .md or .txt extension, got: .{output_ext}")

    return True
