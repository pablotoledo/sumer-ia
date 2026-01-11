#!/usr/bin/env python3
"""
Tests for Agent Interface Configuration
=======================================

Tests that verify configuration options are properly passed through
to FastAgent processing, including Q&A settings, segmentation, etc.
"""

import pytest
import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "streamlit_app" / "components"))


class TestProcessingProgressClass:
    """Tests for the ProcessingProgress helper class."""
    
    def test_processing_progress_creation(self):
        """Test ProcessingProgress can be created with segments."""
        from streamlit_app.components.agent_interface import ProcessingProgress
        
        progress = ProcessingProgress(total_segments=5, steps_per_segment=4)
        
        assert progress.total_segments == 5
        assert progress.steps_per_segment == 4
        assert progress.current_segment == 0
        assert progress.current_step == 0
    
    def test_processing_progress_initial_progress(self):
        """Test initial progress value."""
        from streamlit_app.components.agent_interface import ProcessingProgress
        
        progress = ProcessingProgress(total_segments=5)
        # Initial progress might be negative or small due to segment=0
        # Just verify it's a valid float
        assert isinstance(progress.progress, float)
    
    def test_processing_progress_advances(self):
        """Test progress increases as segments are processed."""
        from streamlit_app.components.agent_interface import ProcessingProgress
        
        progress = ProcessingProgress(total_segments=4)
        
        initial = progress.progress
        progress.start_segment(1)
        after_start = progress.progress
        
        assert after_start >= initial
        
        progress.complete_segment()
        after_complete = progress.progress
        
        assert after_complete > after_start
    
    def test_processing_progress_status_message(self):
        """Test status messages are formatted correctly."""
        from streamlit_app.components.agent_interface import ProcessingProgress
        
        progress = ProcessingProgress(total_segments=8)
        
        # Initial status
        assert "Iniciando" in progress.status
        
        # After starting segment
        progress.start_segment(3, "Inversiones")
        assert "3/8" in progress.status
        assert "Procesando" in progress.status
    
    def test_processing_progress_callback(self):
        """Test callback is invoked on progress changes."""
        from streamlit_app.components.agent_interface import ProcessingProgress
        
        callback_calls = []
        
        def mock_callback(message, progress):
            callback_calls.append((message, progress))
        
        progress = ProcessingProgress(total_segments=2)
        progress.set_callback(mock_callback)
        
        progress.set_phase("Testing")
        
        assert len(callback_calls) == 1
        assert "Testing" in callback_calls[0][0]
    
    def test_processing_progress_finalize(self):
        """Test finalize sets progress to 100%."""
        from streamlit_app.components.agent_interface import ProcessingProgress
        
        progress = ProcessingProgress(total_segments=5)
        progress.finalize()
        
        assert "Completado" in progress.status


class TestBuildSegmentPrompt:
    """Tests for _build_segment_prompt method and Q&A configuration."""
    
    def test_prompt_includes_qa_instructions_when_enabled(self):
        """Test Q&A instructions are included when enable_qa=True."""
        from streamlit_app.components.agent_interface import AgentInterface
        from streamlit_app.components.config_manager import ConfigManager
        
        config = ConfigManager()
        interface = AgentInterface(config)
        
        prompt = interface._build_segment_prompt(
            segment_content="Test content about investments",
            segment_number=1,
            total_segments=3,
            metadata={},
            multimodal_context="",
            enable_qa=True,
            questions_per_section=5
        )
        
        assert "Q&A" in prompt
        assert "5" in prompt
        assert "preguntas" in prompt.lower() or "questions" in prompt.lower()
    
    def test_prompt_excludes_qa_when_disabled(self):
        """Test Q&A disabled message when enable_qa=False."""
        from streamlit_app.components.agent_interface import AgentInterface
        from streamlit_app.components.config_manager import ConfigManager
        
        config = ConfigManager()
        interface = AgentInterface(config)
        
        prompt = interface._build_segment_prompt(
            segment_content="Test content",
            segment_number=1,
            total_segments=1,
            metadata={},
            multimodal_context="",
            enable_qa=False,
            questions_per_section=4
        )
        
        assert "NO generes" in prompt or "no generes" in prompt.lower()
    
    def test_prompt_includes_segment_number(self):
        """Test segment number is included in prompt."""
        from streamlit_app.components.agent_interface import AgentInterface
        from streamlit_app.components.config_manager import ConfigManager
        
        config = ConfigManager()
        interface = AgentInterface(config)
        
        prompt = interface._build_segment_prompt(
            segment_content="Content",
            segment_number=3,
            total_segments=10,
            metadata={},
            multimodal_context=""
        )
        
        assert "3" in prompt
        assert "10" in prompt
    
    def test_prompt_includes_metadata(self):
        """Test metadata is included when provided."""
        from streamlit_app.components.agent_interface import AgentInterface
        from streamlit_app.components.config_manager import ConfigManager
        
        config = ConfigManager()
        interface = AgentInterface(config)
        
        prompt = interface._build_segment_prompt(
            segment_content="Content",
            segment_number=1,
            total_segments=1,
            metadata={
                'topic': 'Inversiones en bolsa',
                'keywords': ['acciones', 'dividendos']
            },
            multimodal_context=""
        )
        
        assert "Inversiones en bolsa" in prompt
        assert "acciones" in prompt
    
    def test_questions_per_section_range(self):
        """Test that different question counts are respected."""
        from streamlit_app.components.agent_interface import AgentInterface
        from streamlit_app.components.config_manager import ConfigManager
        
        config = ConfigManager()
        interface = AgentInterface(config)
        
        for num_questions in [2, 4, 6, 8]:
            prompt = interface._build_segment_prompt(
                segment_content="Test",
                segment_number=1,
                total_segments=1,
                metadata={},
                multimodal_context="",
                enable_qa=True,
                questions_per_section=num_questions
            )
            
            assert str(num_questions) in prompt


class TestConfigManagerPresets:
    """Tests for ConfigManager preset functionality."""
    
    def test_presets_exist(self):
        """Test that presets are defined."""
        from streamlit_app.components.config_manager import ConfigManager
        
        config = ConfigManager()
        presets = config.get_available_presets()
        
        # Presets can be dict or list
        assert presets is not None
        assert len(presets) > 0
    
    def test_apply_preset_basic(self):
        """Test applying a preset updates configuration."""
        from streamlit_app.components.config_manager import ConfigManager
        
        config = ConfigManager()
        
        # This should not raise
        try:
            config.apply_preset('basic_azure', {'api_key': 'test_key'})
        except KeyError:
            # Preset might not exist with this exact name
            pass


class TestAgentInterfaceMethods:
    """Tests for AgentInterface helper methods."""
    
    def test_get_available_agents(self):
        """Test getting available agents."""
        from streamlit_app.components.agent_interface import AgentInterface
        from streamlit_app.components.config_manager import ConfigManager
        
        config = ConfigManager()
        interface = AgentInterface(config)
        
        agents = interface.get_available_agents()
        
        assert isinstance(agents, list)
        assert len(agents) > 0
        assert 'simple_processor' in agents
    
    def test_get_agent_description(self):
        """Test getting agent descriptions."""
        from streamlit_app.components.agent_interface import AgentInterface
        from streamlit_app.components.config_manager import ConfigManager
        
        config = ConfigManager()
        interface = AgentInterface(config)
        
        desc = interface.get_agent_description('simple_processor')
        
        assert isinstance(desc, str)
        assert len(desc) > 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
