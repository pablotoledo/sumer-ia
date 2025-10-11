#!/usr/bin/env python3
"""
WhisperX CLI - Command-line transcription tool
Supports configuration via command-line arguments and environment variables.
"""

import argparse
import os
import sys
import logging
from pathlib import Path
from typing import Optional, List
import json

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import HardwareConfig, ProcessingConfig, OutputConfig, ConfigValidator
from whisperx_processor import WhisperXProcessor
from format_converters import TranscriptionFormatConverter, TranscriptionSummary


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnvironmentConfig:
    """Load configuration from environment variables."""

    @staticmethod
    def get_model() -> Optional[str]:
        """Get model from environment (WHISPERX_MODEL)."""
        return os.getenv('WHISPERX_MODEL')

    @staticmethod
    def get_device() -> Optional[str]:
        """Get device from environment (WHISPERX_DEVICE)."""
        return os.getenv('WHISPERX_DEVICE')

    @staticmethod
    def get_language() -> Optional[str]:
        """Get language from environment (WHISPERX_LANGUAGE)."""
        return os.getenv('WHISPERX_LANGUAGE')

    @staticmethod
    def get_hf_token() -> Optional[str]:
        """Get HuggingFace token from environment (HF_TOKEN or HUGGINGFACE_TOKEN)."""
        return os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')

    @staticmethod
    def get_batch_size() -> Optional[int]:
        """Get batch size from environment (WHISPERX_BATCH_SIZE)."""
        batch_size = os.getenv('WHISPERX_BATCH_SIZE')
        return int(batch_size) if batch_size else None

    @staticmethod
    def get_compute_type() -> Optional[str]:
        """Get compute type from environment (WHISPERX_COMPUTE_TYPE)."""
        return os.getenv('WHISPERX_COMPUTE_TYPE')

    @staticmethod
    def get_output_dir() -> Optional[str]:
        """Get output directory from environment (WHISPERX_OUTPUT_DIR)."""
        return os.getenv('WHISPERX_OUTPUT_DIR')

    @staticmethod
    def get_formats() -> Optional[List[str]]:
        """Get output formats from environment (WHISPERX_FORMATS)."""
        formats = os.getenv('WHISPERX_FORMATS')
        return formats.split(',') if formats else None


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description='WhisperX CLI - Advanced audio transcription with speaker diarization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic transcription
  %(prog)s audio.mp3 --output-dir ./results

  # With speaker diarization
  %(prog)s audio.mp3 --enable-diarization --min-speakers 2 --max-speakers 4

  # Custom model and formats
  %(prog)s audio.mp3 --model large-v2 --formats json,srt,vtt --language es

  # Using environment variables
  export WHISPERX_MODEL=small
  export HF_TOKEN=hf_xxxxx
  %(prog)s audio.mp3

  # GPU optimization
  %(prog)s audio.mp3 --device cuda --batch-size 32 --compute-type float16

Configuration Priority (highest to lowest):
  1. Command-line arguments
  2. Environment variables
  3. Default values

Environment Variables:
  WHISPERX_MODEL          - Model name (base, small, medium, large-v2, large-v3)
  WHISPERX_DEVICE         - Device (auto, cuda, mps, cpu)
  WHISPERX_LANGUAGE       - Language code (en, es, fr, etc.)
  WHISPERX_BATCH_SIZE     - Batch size (1-64)
  WHISPERX_COMPUTE_TYPE   - Compute type (float16, int8, float32)
  WHISPERX_OUTPUT_DIR     - Output directory path
  WHISPERX_FORMATS        - Output formats (comma-separated: json,srt,vtt,txt)
  HF_TOKEN               - HuggingFace token for diarization
  HUGGINGFACE_TOKEN      - Alternative HF token variable
        """
    )

    # Required arguments
    parser.add_argument(
        'input',
        type=str,
        help='Input audio file path'
    )

    # Output configuration
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '-o', '--output-dir',
        type=str,
        default=None,
        help='Output directory (default: same as input file, env: WHISPERX_OUTPUT_DIR)'
    )
    output_group.add_argument(
        '-f', '--formats',
        type=str,
        default=None,
        help='Output formats (comma-separated: json,srt,vtt,txt) (default: json,srt, env: WHISPERX_FORMATS)'
    )
    output_group.add_argument(
        '--no-word-timestamps',
        action='store_true',
        help='Disable word-level timestamps'
    )
    output_group.add_argument(
        '--no-confidence',
        action='store_true',
        help='Disable confidence scores'
    )
    output_group.add_argument(
        '--no-speaker-labels',
        action='store_true',
        help='Disable speaker labels in output'
    )

    # Model configuration
    model_group = parser.add_argument_group('Model Configuration')
    model_group.add_argument(
        '-m', '--model',
        type=str,
        choices=['base', 'small', 'medium', 'large-v2', 'large-v3'],
        default=None,
        help='WhisperX model size (default: small, env: WHISPERX_MODEL)'
    )
    model_group.add_argument(
        '-l', '--language',
        type=str,
        default=None,
        help='Language code (e.g., en, es, fr) - auto-detect if not specified (env: WHISPERX_LANGUAGE)'
    )
    model_group.add_argument(
        '-p', '--preset',
        type=str,
        choices=['fast', 'balanced', 'accurate', 'long_audio'],
        default=None,
        help='Configuration preset (overrides individual model settings)'
    )

    # Hardware configuration
    hardware_group = parser.add_argument_group('Hardware Options')
    hardware_group.add_argument(
        '-d', '--device',
        type=str,
        choices=['auto', 'cuda', 'mps', 'cpu'],
        default='auto',
        help='Processing device (default: auto, env: WHISPERX_DEVICE)'
    )
    hardware_group.add_argument(
        '-b', '--batch-size',
        type=int,
        default=None,
        help='Batch size for processing (default: auto-detected, env: WHISPERX_BATCH_SIZE)'
    )
    hardware_group.add_argument(
        '-c', '--compute-type',
        type=str,
        choices=['float16', 'int8', 'float32'],
        default=None,
        help='Compute precision type (default: auto-detected, env: WHISPERX_COMPUTE_TYPE)'
    )

    # Speaker diarization
    diarization_group = parser.add_argument_group('Speaker Diarization')
    diarization_group.add_argument(
        '--enable-diarization',
        action='store_true',
        help='Enable speaker diarization (requires HF token)'
    )
    diarization_group.add_argument(
        '--min-speakers',
        type=int,
        default=1,
        help='Minimum number of speakers (default: 1)'
    )
    diarization_group.add_argument(
        '--max-speakers',
        type=int,
        default=20,
        help='Maximum number of speakers (default: 20)'
    )
    diarization_group.add_argument(
        '--hf-token',
        type=str,
        default=None,
        help='HuggingFace token for diarization models (env: HF_TOKEN or HUGGINGFACE_TOKEN)'
    )

    # Additional options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='WhisperX CLI v1.0.0'
    )

    return parser


def merge_configs(args: argparse.Namespace, env: EnvironmentConfig) -> dict:
    """Merge command-line args and environment variables (args take precedence)."""
    config = {}

    # Model configuration (args > env > defaults)
    config['model'] = args.model or env.get_model() or 'small'
    config['language'] = args.language or env.get_language()
    config['preset'] = args.preset

    # Hardware configuration
    config['device'] = args.device if args.device != 'auto' else (env.get_device() or 'auto')
    config['batch_size'] = args.batch_size or env.get_batch_size()
    config['compute_type'] = args.compute_type or env.get_compute_type()

    # Output configuration
    config['output_dir'] = args.output_dir or env.get_output_dir()

    if args.formats:
        config['formats'] = [f.strip().upper() for f in args.formats.split(',')]
    elif env.get_formats():
        config['formats'] = [f.strip().upper() for f in env.get_formats()]
    else:
        config['formats'] = ['JSON', 'SRT']

    config['include_word_timestamps'] = not args.no_word_timestamps
    config['include_confidence'] = not args.no_confidence
    config['include_speaker_labels'] = not args.no_speaker_labels

    # Diarization configuration
    config['enable_diarization'] = args.enable_diarization
    config['min_speakers'] = args.min_speakers
    config['max_speakers'] = args.max_speakers
    config['hf_token'] = args.hf_token or env.get_hf_token()

    # Misc
    config['verbose'] = args.verbose

    return config


def validate_input_file(input_path: str) -> Path:
    """Validate input audio file."""
    path = Path(input_path)

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not path.is_file():
        raise ValueError(f"Input path is not a file: {input_path}")

    # Check file extension
    allowed_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.mp4', '.ogg', '.wma', '.aac'}
    if path.suffix.lower() not in allowed_extensions:
        raise ValueError(
            f"Unsupported file format: {path.suffix}\n"
            f"Supported formats: {', '.join(allowed_extensions)}"
        )

    return path


def setup_output_directory(input_path: Path, output_dir: Optional[str]) -> Path:
    """Create and return output directory path."""
    if output_dir:
        out_path = Path(output_dir)
    else:
        # Create output directory next to input file
        out_path = input_path.parent / f"{input_path.stem}_transcription"

    out_path.mkdir(parents=True, exist_ok=True)
    return out_path


def create_hardware_config(config: dict) -> HardwareConfig:
    """Create hardware configuration from merged config."""
    if config['device'] == 'auto':
        # Auto-detect hardware
        hw_config = HardwareConfig.auto_detect()

        # Override with user-specified values if provided
        if config['batch_size']:
            hw_config.batch_size = config['batch_size']
        if config['compute_type']:
            hw_config.compute_type = config['compute_type']

        return hw_config
    else:
        # Manual configuration
        from config import detect_hardware
        hw_info = detect_hardware()

        return HardwareConfig(
            device=config['device'],
            batch_size=config['batch_size'] or (32 if config['device'] == 'mps' else 16),
            compute_type=config['compute_type'] or ('float16' if config['device'] != 'cpu' else 'int8'),
            memory_threshold_gb=16.0 if config['device'] == 'mps' else 8.0,
            hardware_type=hw_info.get('type', 'unknown'),
            hardware_name=hw_info.get('name', 'Unknown Hardware'),
            expected_speedup=hw_info.get('speedup', 1.0)
        )


def create_processing_config(config: dict) -> ProcessingConfig:
    """Create processing configuration from merged config."""
    if config['preset']:
        # Use preset
        proc_config = ProcessingConfig.get_preset(config['preset'])

        # Override with user-specified values
        if config['language']:
            proc_config.language = config['language']
        if config['enable_diarization']:
            proc_config.enable_diarization = True
            proc_config.min_speakers = config['min_speakers']
            proc_config.max_speakers = config['max_speakers']

        return proc_config
    else:
        # Custom configuration
        return ProcessingConfig(
            model_name=config['model'],
            language=config['language'],
            enable_diarization=config['enable_diarization'],
            min_speakers=config['min_speakers'],
            max_speakers=config['max_speakers'],
            segment_length_hours=2.0
        )


def create_output_config(config: dict) -> OutputConfig:
    """Create output configuration from merged config."""
    return OutputConfig(
        formats=config['formats'],
        include_word_timestamps=config['include_word_timestamps'],
        include_confidence_scores=config['include_confidence'],
        speaker_labels=config['include_speaker_labels']
    )


def save_transcription_results(result: dict, output_dir: Path, formats: List[str],
                               converter: TranscriptionFormatConverter) -> None:
    """Save transcription results in all requested formats."""
    logger.info(f"Saving results to: {output_dir}")

    # Save each format
    for format_name in formats:
        try:
            if format_name == 'JSON':
                content = converter.to_json(result)
                output_file = output_dir / 'transcription.json'
            elif format_name == 'SRT':
                content = converter.to_srt(result)
                output_file = output_dir / 'transcription.srt'
            elif format_name == 'VTT':
                content = converter.to_vtt(result)
                output_file = output_dir / 'transcription.vtt'
            elif format_name == 'TXT':
                content = converter.to_txt(result)
                output_file = output_dir / 'transcription.txt'
            else:
                logger.warning(f"Unknown format: {format_name}")
                continue

            output_file.write_text(content, encoding='utf-8')
            logger.info(f"✓ Saved {format_name}: {output_file}")

        except Exception as e:
            logger.error(f"✗ Failed to save {format_name}: {e}")

    # Save summary
    try:
        summary = TranscriptionSummary(result)
        summary_content = json.dumps(summary.get_full_summary(), indent=2, ensure_ascii=False)
        summary_file = output_dir / 'summary.json'
        summary_file.write_text(summary_content, encoding='utf-8')
        logger.info(f"✓ Saved summary: {summary_file}")
    except Exception as e:
        logger.error(f"✗ Failed to save summary: {e}")


def print_summary(result: dict, processing_time: float, output_dir: Path) -> None:
    """Print transcription summary to console."""
    summary = TranscriptionSummary(result)
    stats = summary.get_full_summary()
    basic = stats['basic_stats']

    print("\n" + "="*60)
    print("TRANSCRIPTION COMPLETED SUCCESSFULLY")
    print("="*60)
    print(f"\n⏱️  Processing Time: {processing_time:.1f} seconds")
    print(f"📁 Output Directory: {output_dir}")
    print(f"\n📊 Statistics:")
    print(f"   Duration: {basic['total_duration_formatted']}")
    print(f"   Language: {basic['language'].upper()}")
    print(f"   Segments: {basic['total_segments']:,}")
    print(f"   Words:    {basic['total_words']:,}")

    # Speaker statistics
    speaker_stats = stats['speaker_stats']
    if speaker_stats['speaker_count'] > 0:
        print(f"\n👥 Speakers: {speaker_stats['speaker_count']}")
        for speaker_data in speaker_stats['speakers'][:5]:  # Show top 5
            print(f"   {speaker_data['speaker']}: {speaker_data['duration_formatted']} "
                  f"({speaker_data['percentage']}%), {speaker_data['words']:,} words")

    # Confidence statistics
    confidence = stats['confidence_stats']
    if confidence['has_confidence_scores']:
        print(f"\n📈 Confidence:")
        print(f"   Average: {confidence['average_confidence']:.2f}")
        print(f"   High confidence words: {confidence['high_confidence_words']:,}")
        print(f"   Low confidence words:  {confidence['low_confidence_words']:,}")

    print("\n" + "="*60 + "\n")


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Validate input file
        logger.info("Validating input file...")
        input_path = validate_input_file(args.input)
        logger.info(f"✓ Input file: {input_path}")

        # Merge configurations
        env = EnvironmentConfig()
        config = merge_configs(args, env)

        # Validate diarization requirements
        if config['enable_diarization'] and not config['hf_token']:
            logger.error(
                "Speaker diarization requires HuggingFace token.\n"
                "Provide via --hf-token argument or HF_TOKEN environment variable.\n"
                "Get token at: https://huggingface.co/settings/tokens"
            )
            sys.exit(1)

        # Create configurations
        logger.info("Initializing configuration...")
        hardware_config = create_hardware_config(config)
        processing_config = create_processing_config(config)
        output_config = create_output_config(config)

        # Validate configurations
        hw_valid, hw_msg = ConfigValidator.validate_hardware_config(hardware_config)
        proc_valid, proc_msg = ConfigValidator.validate_processing_config(processing_config)
        out_valid, out_msg = ConfigValidator.validate_output_config(output_config)

        if not (hw_valid and proc_valid and out_valid):
            logger.error("Configuration validation failed:")
            if not hw_valid:
                logger.error(f"  Hardware: {hw_msg}")
            if not proc_valid:
                logger.error(f"  Processing: {proc_msg}")
            if not out_valid:
                logger.error(f"  Output: {out_msg}")
            sys.exit(1)

        # Setup output directory
        output_dir = setup_output_directory(input_path, config['output_dir'])
        logger.info(f"✓ Output directory: {output_dir}")

        # Print configuration summary
        print("\n" + "="*60)
        print("CONFIGURATION SUMMARY")
        print("="*60)
        print(f"Model:        {processing_config.model_name}")
        print(f"Device:       {hardware_config.device.upper()} ({hardware_config.hardware_name})")
        print(f"Batch Size:   {hardware_config.batch_size}")
        print(f"Compute Type: {hardware_config.compute_type}")
        print(f"Language:     {processing_config.language or 'Auto-detect'}")
        print(f"Diarization:  {'Enabled' if processing_config.enable_diarization else 'Disabled'}")
        if processing_config.enable_diarization:
            print(f"  Speakers:   {processing_config.min_speakers}-{processing_config.max_speakers}")
        print(f"Formats:      {', '.join(config['formats'])}")
        print("="*60 + "\n")

        # Initialize processor
        logger.info("Initializing WhisperX processor...")
        processor = WhisperXProcessor(
            hardware_config=hardware_config,
            processing_config=processing_config,
            output_config=output_config
        )

        # Progress callback
        def progress_callback(progress: float, message: str):
            percentage = int(progress * 100)
            bar_length = 40
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r[{bar}] {percentage}% - {message}", end='', flush=True)

        # Process audio
        logger.info("Starting transcription...")
        import time
        start_time = time.time()

        result = processor.process_audio_file(
            str(input_path),
            hf_token=config['hf_token'],
            progress_callback=progress_callback
        )

        processing_time = time.time() - start_time
        print()  # New line after progress bar

        # Save results
        converter = TranscriptionFormatConverter(
            include_speaker_labels=config['include_speaker_labels'],
            include_word_timestamps=config['include_word_timestamps'],
            include_confidence_scores=config['include_confidence']
        )

        save_transcription_results(result, output_dir, config['formats'], converter)

        # Print summary
        print_summary(result, processing_time, output_dir)

        logger.info("Transcription completed successfully!")
        sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == '__main__':
    main()
