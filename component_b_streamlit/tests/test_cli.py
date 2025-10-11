"""
Unit Tests for FastAgent CLI
=============================

Tests for CLI argument parsing, validation, and configuration loading.
"""

import pytest
import sys
from pathlib import Path
import tempfile
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli.args_parser import create_parser, validate_args
from src.cli.config_loader import (
    EnvironmentConfig,
    merge_configs,
    get_preset_config,
    load_fastagent_config
)
from src.cli.validators import (
    validate_input_file,
    validate_output_path,
    validate_documents,
    validate_processing_params,
    estimate_processing_time
)


class TestArgsParser:
    """Test argument parser functionality."""

    def test_parser_creation(self):
        """Test that parser is created successfully."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == 'fastagent-cli'

    def test_required_arguments(self):
        """Test that required arguments are enforced."""
        parser = create_parser()

        # Missing both required args should fail
        with pytest.raises(SystemExit):
            parser.parse_args([])

        # Missing output should fail
        with pytest.raises(SystemExit):
            parser.parse_args(['-i', 'input.txt'])

        # Missing input should fail
        with pytest.raises(SystemExit):
            parser.parse_args(['-o', 'output.md'])

    def test_basic_args_parsing(self):
        """Test basic argument parsing."""
        parser = create_parser()
        args = parser.parse_args(['-i', 'input.txt', '-o', 'output.md'])

        assert args.input == 'input.txt'
        assert args.output == 'output.md'
        assert args.verbose is False
        assert args.dry_run is False

    def test_optional_args_parsing(self):
        """Test optional argument parsing."""
        parser = create_parser()
        args = parser.parse_args([
            '-i', 'input.txt',
            '-o', 'output.md',
            '-v',
            '--dry-run',
            '--model', 'azure.gpt-4.1',
            '--agent', 'meeting_processor',
            '--preset', 'conservative'
        ])

        assert args.verbose is True
        assert args.dry_run is True
        assert args.model == 'azure.gpt-4.1'
        assert args.agent == 'meeting_processor'
        assert args.preset == 'conservative'

    def test_documents_parsing(self):
        """Test multiple documents parsing."""
        parser = create_parser()
        args = parser.parse_args([
            '-i', 'input.txt',
            '-o', 'output.md',
            '-d', 'doc1.pdf', 'doc2.txt', 'image.png'
        ])

        assert len(args.documents) == 3
        assert 'doc1.pdf' in args.documents
        assert 'doc2.txt' in args.documents
        assert 'image.png' in args.documents

    def test_qa_options(self):
        """Test Q&A generation options."""
        parser = create_parser()

        # Enable QA (default)
        args1 = parser.parse_args(['-i', 'input.txt', '-o', 'output.md'])
        assert args1.enable_qa is True

        # Disable QA
        args2 = parser.parse_args(['-i', 'input.txt', '-o', 'output.md', '--no-qa'])
        assert args2.enable_qa is False

        # Custom Q&A questions count
        args3 = parser.parse_args([
            '-i', 'input.txt',
            '-o', 'output.md',
            '--qa-questions', '7'
        ])
        assert args3.qa_questions == 7

    def test_validate_args_success(self):
        """Test argument validation with valid args."""
        parser = create_parser()
        args = parser.parse_args(['-i', 'input.txt', '-o', 'output.md'])

        # Should not raise
        assert validate_args(args) is True

    def test_validate_args_invalid_qa_questions(self):
        """Test argument validation with invalid Q&A questions."""
        parser = create_parser()
        args = parser.parse_args([
            '-i', 'input.txt',
            '-o', 'output.md',
            '--qa-questions', '15'
        ])

        with pytest.raises(ValueError, match="Q&A questions must be between 1 and 10"):
            validate_args(args)

    def test_validate_args_negative_delay(self):
        """Test argument validation with negative delay."""
        parser = create_parser()
        args = parser.parse_args([
            '-i', 'input.txt',
            '-o', 'output.md',
            '--delay', '-5'
        ])

        with pytest.raises(ValueError, match="Delay must be non-negative"):
            validate_args(args)


class TestConfigLoader:
    """Test configuration loading functionality."""

    def test_get_preset_config(self):
        """Test preset configuration loading."""
        # Test conservative preset
        conservative = get_preset_config('conservative')
        assert conservative['delay_between_requests'] == 45
        assert conservative['max_retries'] == 5
        assert conservative['enable_qa'] is True

        # Test fast preset
        fast = get_preset_config('fast')
        assert fast['delay_between_requests'] == 10
        assert fast['enable_qa'] is False

        # Test unknown preset (should return balanced)
        unknown = get_preset_config('unknown')
        assert unknown['delay_between_requests'] == 20

    def test_environment_config_methods(self):
        """Test EnvironmentConfig methods."""
        env = EnvironmentConfig()

        # These should return None if not set
        assert env.get_provider() is None or isinstance(env.get_provider(), str)
        assert env.get_model() is None or isinstance(env.get_model(), str)
        assert env.get_delay() is None or isinstance(env.get_delay(), int)

    def test_merge_configs_basic(self):
        """Test basic configuration merging."""
        parser = create_parser()
        args = parser.parse_args(['-i', 'input.txt', '-o', 'output.md'])
        env = EnvironmentConfig()

        config = merge_configs(args, env)

        assert 'input' in config
        assert 'output' in config
        assert config['input'] == 'input.txt'
        assert config['output'] == 'output.md'

    def test_merge_configs_with_preset(self):
        """Test configuration merging with preset."""
        parser = create_parser()
        args = parser.parse_args([
            '-i', 'input.txt',
            '-o', 'output.md',
            '--preset', 'fast'
        ])
        env = EnvironmentConfig()

        config = merge_configs(args, env)

        # Should inherit from fast preset
        assert config['delay_between_requests'] == 10
        # Note: enable_qa comes from args (default True), not preset
        # because args have higher priority. To get preset value, use --no-qa
        assert config['max_retries'] == 2


class TestValidators:
    """Test input validation functionality."""

    def test_validate_input_file_success(self):
        """Test successful input file validation."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            path = validate_input_file(temp_path)
            assert path.exists()
            assert path.is_file()
        finally:
            os.unlink(temp_path)

    def test_validate_input_file_not_found(self):
        """Test validation with non-existent file."""
        with pytest.raises(FileNotFoundError):
            validate_input_file('/nonexistent/file.txt')

    def test_validate_input_file_unsupported_format(self):
        """Test validation with unsupported file format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.exe', delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                validate_input_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_validate_input_file_empty(self):
        """Test validation with empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = f.name  # Don't write anything

        try:
            with pytest.raises(ValueError, match="empty"):
                validate_input_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_validate_output_path_success(self):
        """Test successful output path validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'output.md')
            path = validate_output_path(output_path)
            assert path.suffix == '.md'

    def test_validate_output_path_invalid_extension(self):
        """Test validation with invalid output extension."""
        with pytest.raises(ValueError, match="Unsupported output format"):
            validate_output_path('/tmp/output.exe')

    def test_validate_output_path_nonexistent_directory(self):
        """Test validation with non-existent directory."""
        with pytest.raises(ValueError, match="directory does not exist"):
            validate_output_path('/nonexistent/dir/output.md')

    def test_validate_documents_success(self):
        """Test successful documents validation."""
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f1:
            f1.write("PDF content")
            pdf_path = f1.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
            f2.write("Text content")
            txt_path = f2.name

        try:
            valid_docs, errors = validate_documents([pdf_path, txt_path])
            assert len(valid_docs) == 2
            assert len(errors) == 0
        finally:
            os.unlink(pdf_path)
            os.unlink(txt_path)

    def test_validate_documents_with_errors(self):
        """Test documents validation with some invalid files."""
        valid_docs, errors = validate_documents([
            '/nonexistent/file.pdf',
            '/another/missing.txt'
        ])

        assert len(valid_docs) == 0
        assert len(errors) == 2

    def test_validate_processing_params_success(self):
        """Test successful processing params validation."""
        errors = validate_processing_params(
            qa_questions=4,
            delay=30,
            max_retries=3,
            retry_delay=60
        )

        assert len(errors) == 0

    def test_validate_processing_params_invalid_qa(self):
        """Test processing params validation with invalid Q&A count."""
        errors = validate_processing_params(
            qa_questions=15,  # Invalid
            delay=30,
            max_retries=3,
            retry_delay=60
        )

        assert len(errors) > 0
        assert any('Q&A questions' in err for err in errors)

    def test_estimate_processing_time(self):
        """Test processing time estimation."""
        # Small content
        time1 = estimate_processing_time(100, 'programmatic', False)
        assert 'seconds' in time1

        # Medium content
        time2 = estimate_processing_time(5000, 'intelligent', True)
        assert 'minutes' in time2

        # Large content
        time3 = estimate_processing_time(20000, 'intelligent', True)
        assert 'h' in time3 or 'minutes' in time3


class TestCLIIntegration:
    """Integration tests for CLI workflow."""

    def test_full_cli_workflow_dry_run(self):
        """Test complete CLI workflow with dry run."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test transcription with some content.")
            input_path = f.name

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'output.md')

            try:
                # Parse arguments
                parser = create_parser()
                args = parser.parse_args([
                    '-i', input_path,
                    '-o', output_path,
                    '--dry-run'
                ])

                # Validate arguments
                assert validate_args(args) is True

                # Validate input
                input_file = validate_input_file(args.input)
                assert input_file.exists()

                # Validate output
                output_file = validate_output_path(args.output)
                assert output_file.parent.exists()

                # Merge configurations
                env = EnvironmentConfig()
                config = merge_configs(args, env)

                assert config['dry_run'] is True
                assert config['input'] == input_path
                assert config['output'] == output_path

            finally:
                os.unlink(input_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
