"""
Input Validators for FastAgent CLI
===================================

Validate input files, output paths, and other CLI parameters.
"""

from pathlib import Path
from typing import List, Optional, Tuple


def validate_input_file(input_path: str) -> Path:
    """
    Validate input transcription file.

    Args:
        input_path: Path to input file

    Returns:
        Path object if valid

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported
    """
    path = Path(input_path)

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not path.is_file():
        raise ValueError(f"Input path is not a file: {input_path}")

    # Check file extension
    allowed_extensions = {'.txt', '.md', '.pdf', '.docx', '.markdown'}
    if path.suffix.lower() not in allowed_extensions:
        raise ValueError(
            f"Unsupported file format: {path.suffix}\n"
            f"Supported formats: {', '.join(allowed_extensions)}"
        )

    # Check file is not empty
    if path.stat().st_size == 0:
        raise ValueError(f"Input file is empty: {input_path}")

    return path


def validate_output_path(output_path: str) -> Path:
    """
    Validate output file path.

    Args:
        output_path: Path to output file

    Returns:
        Path object if valid

    Raises:
        ValueError: If output format is unsupported or directory doesn't exist
    """
    path = Path(output_path)

    # Check parent directory exists
    if not path.parent.exists():
        raise ValueError(
            f"Output directory does not exist: {path.parent}\n"
            f"Create the directory first or use an existing path."
        )

    # Check file extension
    allowed_extensions = {'.md', '.txt', '.markdown'}
    if path.suffix.lower() not in allowed_extensions:
        raise ValueError(
            f"Unsupported output format: {path.suffix}\n"
            f"Supported formats: {', '.join(allowed_extensions)}"
        )

    # Warn if file exists (don't fail, just warn)
    if path.exists():
        print(f"Warning: Output file already exists and will be overwritten: {output_path}")

    return path


def validate_documents(document_paths: List[str]) -> Tuple[List[Path], List[str]]:
    """
    Validate additional document files.

    Args:
        document_paths: List of paths to additional documents

    Returns:
        Tuple of (valid_paths, error_messages)
    """
    valid_paths = []
    errors = []

    allowed_extensions = {'.pdf', '.txt', '.md', '.markdown', '.png', '.jpg', '.jpeg', '.docx'}

    for doc_path in document_paths:
        path = Path(doc_path)

        # Check if exists
        if not path.exists():
            errors.append(f"Document not found: {doc_path}")
            continue

        # Check if file
        if not path.is_file():
            errors.append(f"Not a file: {doc_path}")
            continue

        # Check extension
        if path.suffix.lower() not in allowed_extensions:
            errors.append(
                f"Unsupported document format: {path.suffix} ({doc_path})\n"
                f"Supported: {', '.join(allowed_extensions)}"
            )
            continue

        # Check file size (max 50MB per document)
        max_size_mb = 50
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > max_size_mb:
            errors.append(
                f"Document too large: {doc_path} ({size_mb:.1f}MB)\n"
                f"Maximum size: {max_size_mb}MB"
            )
            continue

        valid_paths.append(path)

    return valid_paths, errors


def validate_config_file(config_path: str) -> Optional[Path]:
    """
    Validate configuration file path.

    Args:
        config_path: Path to config file

    Returns:
        Path object if valid, None if not found (will use defaults)

    Raises:
        ValueError: If file exists but is invalid
    """
    path = Path(config_path)

    # If file doesn't exist, return None (will use defaults)
    if not path.exists():
        return None

    # If exists, must be a file
    if not path.is_file():
        raise ValueError(f"Config path is not a file: {config_path}")

    # Must be YAML
    if path.suffix.lower() not in {'.yaml', '.yml'}:
        raise ValueError(
            f"Config file must be YAML format (.yaml or .yml): {path.suffix}"
        )

    return path


def validate_processing_params(
    qa_questions: int,
    delay: Optional[int],
    max_retries: Optional[int],
    retry_delay: Optional[int]
) -> List[str]:
    """
    Validate processing parameters.

    Args:
        qa_questions: Number of Q&A questions per segment
        delay: Delay between requests
        max_retries: Maximum retries
        retry_delay: Retry delay

    Returns:
        List of error messages (empty if all valid)
    """
    errors = []

    # Q&A questions
    if qa_questions < 1 or qa_questions > 10:
        errors.append("Q&A questions must be between 1 and 10")

    # Delay
    if delay is not None and delay < 0:
        errors.append("Delay between requests must be non-negative")

    if delay is not None and delay > 300:
        errors.append(
            f"Delay of {delay}s seems excessive. Consider a lower value (max recommended: 300s)"
        )

    # Max retries
    if max_retries is not None and max_retries < 0:
        errors.append("Max retries must be non-negative")

    if max_retries is not None and max_retries > 10:
        errors.append(
            f"Max retries of {max_retries} seems excessive. Consider a lower value (max recommended: 10)"
        )

    # Retry delay
    if retry_delay is not None and retry_delay < 0:
        errors.append("Retry delay must be non-negative")

    if retry_delay is not None and retry_delay > 600:
        errors.append(
            f"Retry delay of {retry_delay}s seems excessive. Consider a lower value (max recommended: 600s)"
        )

    return errors


def estimate_processing_time(word_count: int, segmentation: str, enable_qa: bool) -> str:
    """
    Estimate processing time based on content and settings.

    Args:
        word_count: Number of words in content
        segmentation: Segmentation method
        enable_qa: Whether Q&A is enabled

    Returns:
        Human-readable time estimate
    """
    # Base processing rate: ~200 words per minute
    base_minutes = word_count / 200

    # Intelligent segmentation adds overhead
    if segmentation == 'intelligent' and word_count > 3000:
        base_minutes *= 1.5

    # Q&A generation adds time
    if enable_qa:
        base_minutes *= 1.3

    # Convert to human-readable format
    if base_minutes < 1:
        return f"~{int(base_minutes * 60)} seconds"
    elif base_minutes < 60:
        return f"~{int(base_minutes)} minutes"
    else:
        hours = int(base_minutes // 60)
        minutes = int(base_minutes % 60)
        return f"~{hours}h {minutes}m"
