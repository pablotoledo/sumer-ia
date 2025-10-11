#!/usr/bin/env python3
"""
FastAgent CLI - Command-line transcription processing
======================================================

Transform STT transcriptions into educational documents with Q&A.
Supports configuration via command-line arguments and environment variables.
"""

import argparse
import sys
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.cli.args_parser import create_parser, validate_args
from src.cli.config_loader import EnvironmentConfig, merge_configs, apply_config_to_manager
from src.cli.validators import (
    validate_input_file,
    validate_output_path,
    validate_documents,
    validate_processing_params,
    estimate_processing_time
)
from streamlit_app.components.config_manager import ConfigManager
from streamlit_app.components.agent_interface import AgentInterface, run_async_in_streamlit


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CLIProgressBar:
    """Simple progress bar for CLI."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.last_message = ""

    def update(self, message: str, progress: float):
        """Update progress bar."""
        if not self.enabled:
            return

        percentage = int(progress * 100)
        bar_length = 40
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)

        # Clear previous line and print new progress
        print(f"\r[{bar}] {percentage}% - {message}", end='', flush=True)
        self.last_message = message

    def finish(self):
        """Finish progress bar."""
        if self.enabled and self.last_message:
            print()  # New line after progress bar


class CLIProcessor:
    """Main CLI processor for FastAgent."""

    def __init__(self, args: argparse.Namespace, config: Dict[str, Any]):
        self.args = args
        self.config = config
        self.config_manager = ConfigManager()
        self.agent_interface = AgentInterface(self.config_manager)

        # Apply config to manager
        apply_config_to_manager(config, self.config_manager)

    def load_input(self) -> str:
        """Load input transcription file."""
        input_path = Path(self.args.input)

        logger.info(f"Loading input file: {input_path}")

        # Read based on file type
        if input_path.suffix.lower() == '.pdf':
            # For PDFs, we'll use the multimodal context extraction
            # For now, raise not implemented
            raise NotImplementedError(
                "Direct PDF reading not yet implemented. "
                "Convert PDF to text first or use as additional document."
            )
        else:
            # Text files
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()

        if not content.strip():
            raise ValueError(f"Input file is empty or contains only whitespace: {input_path}")

        word_count = len(content.split())
        logger.info(f"✓ Loaded {word_count:,} words from {input_path.name}")

        return content

    def load_documents(self) -> Optional[List[str]]:
        """Load additional documents for multimodal context."""
        if not self.args.documents:
            return None

        logger.info(f"Loading {len(self.args.documents)} additional document(s)...")

        valid_docs, errors = validate_documents(self.args.documents)

        if errors:
            logger.warning("Some documents could not be loaded:")
            for error in errors:
                logger.warning(f"  • {error}")

        if not valid_docs:
            logger.warning("No valid documents found, proceeding without multimodal context")
            return None

        logger.info(f"✓ Loaded {len(valid_docs)} document(s) for context")
        for doc in valid_docs:
            logger.info(f"  • {doc.name}")

        return [str(doc) for doc in valid_docs]

    async def process(self) -> Dict[str, Any]:
        """Execute the processing pipeline."""

        # 1. Load content
        content = self.load_input()

        # 2. Load additional documents
        documents = self.load_documents()

        # 3. Configure processing
        use_intelligent_segmentation = self._should_use_intelligent_segmentation(content)
        agent_override = self.args.agent if self.args.agent != 'auto' else None

        # 4. Progress callback
        progress_callback = self._create_progress_callback() if not self.args.no_progress else None

        # 5. Dry run check
        if self.args.dry_run:
            logger.info("🧪 DRY RUN MODE - Simulating processing...")
            word_count = len(content.split())
            estimated_segments = max(1, word_count // 2500)

            return {
                'success': True,
                'document': f"# Dry Run Result\n\nWould process {word_count:,} words into ~{estimated_segments} segments.",
                'segments': [],
                'agent_used': agent_override or 'auto-detect',
                'total_segments': estimated_segments,
                'retry_count': 0,
                'original_content': content,
                'multimodal_files': documents or [],
                'segmentation_method': 'intelligent_ai' if use_intelligent_segmentation else 'programmatic',
                'dry_run': True
            }

        # 6. Process
        logger.info("🚀 Starting processing...")

        result = await self.agent_interface.process_content(
            content=content,
            documents=documents,
            progress_callback=progress_callback,
            agent_override=agent_override,
            use_intelligent_segmentation=use_intelligent_segmentation
        )

        return result

    def _should_use_intelligent_segmentation(self, content: str) -> bool:
        """Determine if intelligent segmentation should be used."""
        word_count = len(content.split())

        if self.config['segmentation'] == 'intelligent':
            return True
        elif self.config['segmentation'] == 'programmatic':
            return False
        else:  # auto
            # Use intelligent for content > 3000 words
            return word_count > 3000

    def _create_progress_callback(self):
        """Create progress bar callback."""
        progress_bar = CLIProgressBar(enabled=not self.args.no_progress)

        def callback(message: str, progress: float):
            progress_bar.update(message, progress)

        # Store progress bar to finish it later
        self._progress_bar = progress_bar
        return callback

    def save_output(self, result: Dict[str, Any], output_path: Path) -> None:
        """Save processing result to output file."""
        logger.info(f"Saving results to: {output_path}")

        document = result['document']

        # Write to file
        output_path.write_text(document, encoding='utf-8')

        file_size_kb = output_path.stat().st_size / 1024
        logger.info(f"✓ Saved {len(document):,} characters ({file_size_kb:.1f}KB) to {output_path.name}")


def print_configuration_summary(args: argparse.Namespace, config: Dict[str, Any]) -> None:
    """Print configuration summary before processing."""
    print("\n" + "="*60)
    print("CONFIGURATION SUMMARY")
    print("="*60)

    print(f"Input:              {args.input}")
    print(f"Output:             {args.output}")

    if args.documents:
        print(f"Documents:          {len(args.documents)} file(s)")

    print(f"Model:              {config.get('model', 'default')}")
    print(f"Agent:              {config.get('agent', 'auto')}")
    print(f"Segmentation:       {config.get('segmentation', 'auto')}")
    print(f"Q&A Generation:     {'Enabled' if config.get('enable_qa') else 'Disabled'}")

    if config.get('enable_qa'):
        print(f"  Questions/segment: {config.get('qa_questions', 4)}")

    print(f"\nRate Limiting:")
    print(f"  Delay:            {config.get('delay_between_requests', 30)}s between requests")
    print(f"  Max retries:      {config.get('max_retries', 3)}")
    print(f"  Retry delay:      {config.get('retry_base_delay', 60)}s base")

    if args.dry_run:
        print(f"\n🧪 DRY RUN MODE - No LLM calls will be made")

    print("="*60 + "\n")


def print_processing_summary(
    result: Dict[str, Any],
    processing_time: float,
    output_path: Path
) -> None:
    """Print processing summary after completion."""
    print("\n" + "="*60)
    print("PROCESSING COMPLETED SUCCESSFULLY")
    print("="*60)

    print(f"\n⏱️  Processing Time: {processing_time:.1f} seconds")
    print(f"📁 Output File: {output_path}")

    if result.get('dry_run'):
        print(f"\n🧪 DRY RUN - No actual processing performed")
        return

    print(f"\n📊 Statistics:")
    print(f"   Agent used:       {result.get('agent_used', 'unknown')}")
    print(f"   Segmentation:     {result.get('segmentation_method', 'unknown')}")
    print(f"   Total segments:   {result.get('total_segments', 0)}")
    print(f"   Retry count:      {result.get('retry_count', 0)}")

    # Word statistics
    original_words = len(result.get('original_content', '').split())
    final_words = len(result.get('document', '').split())

    print(f"\n📝 Content:")
    print(f"   Original words:   {original_words:,}")
    print(f"   Final words:      {final_words:,}")

    if original_words > 0:
        retention = (final_words / original_words) * 100
        print(f"   Retention rate:   {retention:.1f}%")

    # Multimodal files
    if result.get('multimodal_files'):
        print(f"\n📎 Multimodal files used: {len(result['multimodal_files'])}")

    # Rate limiting warnings
    if result.get('retry_count', 0) > 3:
        print(f"\n⚠️  Warning: {result['retry_count']} retries due to rate limiting.")
        print(f"   Consider increasing delay or using a higher tier.")

    print("\n" + "="*60 + "\n")


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Validate arguments
        validate_args(args)

        # Validate input file
        logger.info("Validating input file...")
        input_path = validate_input_file(args.input)
        logger.info(f"✓ Input file: {input_path}")

        # Validate output path
        logger.info("Validating output path...")
        output_path = validate_output_path(args.output)
        logger.info(f"✓ Output path: {output_path}")

        # Merge configurations
        logger.info("Loading configuration...")
        env_config = EnvironmentConfig()
        config = merge_configs(args, env_config)

        # Validate processing parameters
        param_errors = validate_processing_params(
            config.get('qa_questions', 4),
            config.get('delay_between_requests'),
            config.get('max_retries'),
            config.get('retry_base_delay')
        )

        if param_errors:
            logger.error("Configuration validation failed:")
            for error in param_errors:
                logger.error(f"  • {error}")
            sys.exit(1)

        logger.info("✓ Configuration loaded")

        # Print configuration summary
        print_configuration_summary(args, config)

        # Estimate processing time
        with open(input_path, 'r', encoding='utf-8') as f:
            content_preview = f.read()
        word_count = len(content_preview.split())

        estimated_time = estimate_processing_time(
            word_count,
            config.get('segmentation', 'auto'),
            config.get('enable_qa', True)
        )

        print(f"📊 Estimated processing time: {estimated_time}")
        print(f"📝 Content size: {word_count:,} words\n")

        # Create processor
        processor = CLIProcessor(args, config)

        # Run processing
        logger.info(f"Processing {input_path}...")
        start_time = time.time()

        result = run_async_in_streamlit(processor.process())

        processing_time = time.time() - start_time

        # Finish progress bar if exists
        if hasattr(processor, '_progress_bar'):
            processor._progress_bar.finish()

        # Save results
        if result['success']:
            processor.save_output(result, output_path)

            # Print summary
            print_processing_summary(result, processing_time, output_path)

            logger.info("✅ Processing completed successfully!")
            sys.exit(0)
        else:
            logger.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Operation cancelled by user")
        sys.exit(130)
    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"❌ Invalid input: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == '__main__':
    main()
