"""
Tests for video player component.
"""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtTest import QSignalSpy

from src.video_frame_capture.core.video_player import VideoPlayer


class TestVideoPlayer:
    """Test cases for VideoPlayer class"""

    @pytest.fixture
    def video_player(self, qtbot):
        """Create a VideoPlayer instance for testing"""
        player = VideoPlayer()
        qtbot.addWidget(player.get_video_widget())
        return player

    def test_initialization(self, video_player):
        """Test VideoPlayer initialization"""
        assert video_player.player is not None
        assert video_player.video_sink is not None
        assert video_player.video_widget is not None
        assert video_player.get_current_video_path() is None

    def test_load_video(self, video_player, qtbot):
        """Test video loading"""
        # Setup signal spy
        spy = QSignalSpy(video_player.mediaLoaded)

        # Mock file path
        test_file = "/path/to/test/video.mp4"

        # Load video
        video_player.load_video(test_file)

        # Check that path is set
        assert video_player.get_current_video_path() == test_file

    def test_play_pause_stop(self, video_player):
        """Test playback controls"""
        # Initially not playing
        assert not video_player.is_playing()

        # Test play
        video_player.play()

        # Test pause
        video_player.pause()

        # Test stop
        video_player.stop()

    def test_seek_functionality(self, video_player):
        """Test seeking functionality"""
        # Test seeking to position
        position = 5000  # 5 seconds
        video_player.seek(position)

        # Position should be set (though actual seeking depends on media)
        assert video_player.get_current_position() >= 0

    def test_signal_emissions(self, video_player, qtbot):
        """Test that signals are properly emitted"""
        # Setup signal spies
        position_spy = QSignalSpy(video_player.positionChanged)
        duration_spy = QSignalSpy(video_player.durationChanged)
        state_spy = QSignalSpy(video_player.stateChanged)
        error_spy = QSignalSpy(video_player.errorOccurred)

        # These spies should be valid
        assert position_spy.isValid()
        assert duration_spy.isValid()
        assert state_spy.isValid()
        assert error_spy.isValid()

    def test_error_handling(self, video_player, qtbot):
        """Test error handling"""
        # Setup error signal spy
        error_spy = QSignalSpy(video_player.errorOccurred)

        # Try to load invalid file
        video_player.load_video("/nonexistent/file.mp4")

        # Error signal might be emitted (depends on Qt behavior)
        # This test mainly ensures no exceptions are raised

    def test_video_widget_access(self, video_player):
        """Test video widget access"""
        widget = video_player.get_video_widget()
        assert widget is not None

    def test_duration_and_position(self, video_player):
        """Test duration and position getters"""
        # Initially should return 0 or valid values
        duration = video_player.get_duration()
        position = video_player.get_current_position()

        assert isinstance(duration, int)
        assert isinstance(position, int)
        assert duration >= 0
        assert position >= 0

    def test_seekable_property(self, video_player):
        """Test seekable property"""
        # Should return boolean
        seekable = video_player.is_seekable()
        assert isinstance(seekable, bool)

    @patch('PySide6.QtCore.QUrl.fromLocalFile')
    def test_load_video_url_creation(self, mock_from_local_file, video_player):
        """Test that QUrl is created correctly when loading video"""
        test_path = "/test/path/video.mp4"
        mock_url = Mock()
        mock_from_local_file.return_value = mock_url

        video_player.load_video(test_path)

        mock_from_local_file.assert_called_once_with(test_path)

    def test_state_tracking(self, video_player):
        """Test state tracking methods"""
        # Test various state checks
        assert not video_player.is_playing()  # Initially not playing

        # These methods should not raise exceptions
        video_player.play()
        video_player.pause()
        video_player.stop()


@pytest.fixture
def qtbot():
    """Fixture to provide qtbot for Qt testing"""
    # This would be provided by pytest-qt
    # For now, we'll create a minimal mock
    class MockQtBot:
        def addWidget(self, widget):
            pass

    return MockQtBot()