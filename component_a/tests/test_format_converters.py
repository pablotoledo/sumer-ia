"""Tests for format converters module."""

import pytest
import json
from src.format_converters import TranscriptionFormatConverter, TranscriptionSummary


class TestTranscriptionFormatConverter:
    """Test transcription format converter functionality."""
    
    @pytest.fixture
    def sample_result(self):
        """Sample WhisperX result for testing."""
        return {
            "language": "en",
            "segments": [
                {
                    "start": 0.663,
                    "end": 7.751,
                    "text": "Welcome back. Here we go again.",
                    "speaker": "SPEAKER_00",
                    "words": [
                        {
                            "word": "Welcome",
                            "start": 0.663,
                            "end": 0.903,
                            "score": 0.906,
                            "speaker": "SPEAKER_00"
                        },
                        {
                            "word": "back.",
                            "start": 0.943,
                            "end": 1.143,
                            "score": 0.928,
                            "speaker": "SPEAKER_00"
                        }
                    ]
                },
                {
                    "start": 8.184,
                    "end": 12.745,
                    "text": "This is the second speaker talking.",
                    "speaker": "SPEAKER_01",
                    "words": [
                        {
                            "word": "This",
                            "start": 8.184,
                            "end": 8.324,
                            "score": 0.766,
                            "speaker": "SPEAKER_01"
                        }
                    ]
                }
            ]
        }
    
    @pytest.fixture
    def converter(self):
        """Default converter instance."""
        return TranscriptionFormatConverter(
            include_speaker_labels=True,
            include_word_timestamps=True,
            include_confidence_scores=True
        )
    
    def test_to_json_pretty(self, converter, sample_result):
        """Test JSON conversion with pretty printing."""
        json_output = converter.to_json(sample_result, pretty=True)
        
        # Should be valid JSON
        parsed = json.loads(json_output)
        
        assert parsed["language"] == "en"
        assert len(parsed["segments"]) == 2
        assert parsed["segments"][0]["text"] == "Welcome back. Here we go again."
        assert parsed["segments"][0]["speaker"] == "SPEAKER_00"
        assert "words" in parsed["segments"][0]
        
        # Check word-level data
        words = parsed["segments"][0]["words"]
        assert len(words) == 2
        assert words[0]["word"] == "Welcome"
        assert words[0]["confidence"] == 0.906
        assert words[0]["speaker"] == "SPEAKER_00"
    
    def test_to_json_compact(self, converter, sample_result):
        """Test JSON conversion without pretty printing."""
        json_output = converter.to_json(sample_result, pretty=False)
        
        # Should be valid JSON without indentation
        parsed = json.loads(json_output)
        assert "\n" not in json_output  # No newlines in compact JSON
        assert parsed["language"] == "en"
    
    def test_to_json_no_speaker_labels(self, sample_result):
        """Test JSON conversion without speaker labels."""
        converter = TranscriptionFormatConverter(
            include_speaker_labels=False,
            include_word_timestamps=True,
            include_confidence_scores=True
        )
        
        json_output = converter.to_json(sample_result)
        parsed = json.loads(json_output)
        
        # Speaker labels should be excluded
        assert "speaker" not in parsed["segments"][0]
        assert "speaker" not in parsed["segments"][0]["words"][0]
    
    def test_to_json_no_word_timestamps(self, sample_result):
        """Test JSON conversion without word timestamps."""
        converter = TranscriptionFormatConverter(
            include_speaker_labels=True,
            include_word_timestamps=False,
            include_confidence_scores=True
        )
        
        json_output = converter.to_json(sample_result)
        parsed = json.loads(json_output)
        
        # Word-level data should be excluded
        assert "words" not in parsed["segments"][0]
    
    def test_to_json_no_confidence_scores(self, sample_result):
        """Test JSON conversion without confidence scores."""
        converter = TranscriptionFormatConverter(
            include_speaker_labels=True,
            include_word_timestamps=True,
            include_confidence_scores=False
        )
        
        json_output = converter.to_json(sample_result)
        parsed = json.loads(json_output)
        
        # Confidence scores should be excluded
        assert "confidence" not in parsed["segments"][0]["words"][0]
    
    def test_to_srt(self, converter, sample_result):
        """Test SRT format conversion."""
        srt_output = converter.to_srt(sample_result)
        
        lines = srt_output.strip().split('\n')
        
        # Check SRT structure
        assert lines[0] == "1"  # First subtitle number
        assert "00:00:00,663 --> 00:00:07,751" in lines[1]  # Timestamp
        assert "[SPEAKER_00]: Welcome back. Here we go again." in lines[2]  # Text with speaker
        
        assert lines[4] == "2"  # Second subtitle number
        assert "00:00:08,184 --> 00:00:12,745" in lines[5]  # Second timestamp
        assert "[SPEAKER_01]: This is the second speaker talking." in lines[6]  # Second text
    
    def test_to_srt_no_speakers(self, sample_result):
        """Test SRT format without speaker labels."""
        converter = TranscriptionFormatConverter(include_speaker_labels=False)
        srt_output = converter.to_srt(sample_result)
        
        # Should not contain speaker labels
        assert "[SPEAKER_00]" not in srt_output
        assert "[SPEAKER_01]" not in srt_output
        assert "Welcome back. Here we go again." in srt_output
    
    def test_to_vtt(self, converter, sample_result):
        """Test VTT format conversion."""
        vtt_output = converter.to_vtt(sample_result)
        
        lines = vtt_output.strip().split('\n')
        
        # Check VTT structure
        assert lines[0] == "WEBVTT"  # VTT header
        assert lines[1] == ""  # Empty line after header
        assert "00:00:00.663 --> 00:00:07.751" in lines[2]  # Timestamp (dots, not commas)
        assert "[SPEAKER_00]: Welcome back. Here we go again." in lines[3]  # Text
    
    def test_to_txt(self, converter, sample_result):
        """Test plain text format conversion."""
        txt_output = converter.to_txt(sample_result)
        
        lines = txt_output.strip().split('\n')
        
        assert len(lines) == 2
        assert "[SPEAKER_00]: Welcome back. Here we go again." in lines[0]
        assert "[SPEAKER_01]: This is the second speaker talking." in lines[1]
    
    def test_to_txt_with_timestamps(self, converter, sample_result):
        """Test plain text with timestamps."""
        txt_output = converter.to_txt(sample_result, include_timestamps=True)
        
        lines = txt_output.strip().split('\n')
        
        # Should include timestamps in readable format
        assert "[00:00] [SPEAKER_00]: Welcome back. Here we go again." in lines[0]
        assert "[00:08] [SPEAKER_01]: This is the second speaker talking." in lines[1]
    
    def test_to_csv(self, converter, sample_result):
        """Test CSV format conversion."""
        csv_output = converter.to_csv(sample_result)
        
        lines = csv_output.strip().split('\n')
        
        # Check header
        assert "start,end,duration,speaker,text" in lines[0]
        
        # Check first data row
        assert lines[1].startswith("0.663,7.751,7.088,SPEAKER_00")
        assert '"Welcome back. Here we go again."' in lines[1]
        
        # Check second data row
        assert lines[2].startswith("8.184,12.745,4.561,SPEAKER_01")
        assert '"This is the second speaker talking."' in lines[2]
    
    def test_to_csv_no_speakers(self, sample_result):
        """Test CSV format without speakers."""
        converter = TranscriptionFormatConverter(include_speaker_labels=False)
        csv_output = converter.to_csv(sample_result)
        
        lines = csv_output.strip().split('\n')
        
        # Header should not include speaker column
        assert "speaker" not in lines[0]
        assert "start,end,duration,text" in lines[0]
    
    def test_to_word_level_json(self, converter, sample_result):
        """Test word-level JSON format conversion."""
        word_json = converter.to_word_level_json(sample_result)
        parsed = json.loads(word_json)
        
        assert parsed["language"] == "en"
        assert "words" in parsed
        assert parsed["total_words"] == 3  # Welcome, back., This
        
        words = parsed["words"]
        assert len(words) == 3
        
        # Check first word
        assert words[0]["word"] == "Welcome"
        assert words[0]["start"] == 0.663
        assert words[0]["confidence"] == 0.906
        assert words[0]["speaker"] == "SPEAKER_00"
    
    def test_to_word_level_json_no_word_data(self, converter):
        """Test word-level JSON when no word data available."""
        result_no_words = {
            "language": "en",
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Hello world test",
                    "speaker": "SPEAKER_00"
                }
            ]
        }
        
        word_json = converter.to_word_level_json(result_no_words)
        parsed = json.loads(word_json)
        
        # Should create words from segment text
        words = parsed["words"]
        assert len(words) == 3  # Hello, world, test
        assert words[0]["word"] == "Hello"
        assert words[0]["speaker"] == "SPEAKER_00"
        assert words[0]["duration"] > 0
    
    def test_format_timestamp_srt(self, converter):
        """Test SRT timestamp formatting."""
        # Test various timestamps
        assert converter._format_timestamp_srt(0.663) == "00:00:00,663"
        assert converter._format_timestamp_srt(65.5) == "00:01:05,500"
        assert converter._format_timestamp_srt(3665.123) == "01:01:05,123"
    
    def test_format_timestamp_vtt(self, converter):
        """Test VTT timestamp formatting."""
        # Test various timestamps
        assert converter._format_timestamp_vtt(0.663) == "00:00:00.663"
        assert converter._format_timestamp_vtt(65.5) == "00:01:05.500"
        assert converter._format_timestamp_vtt(3665.123) == "01:01:05.123"
    
    def test_format_timestamp_readable(self, converter):
        """Test readable timestamp formatting."""
        assert converter._format_timestamp_readable(0.663) == "00:00"
        assert converter._format_timestamp_readable(65.5) == "01:05"
        assert converter._format_timestamp_readable(3665.123) == "61:05"
    
    def test_empty_result(self, converter):
        """Test handling of empty result."""
        empty_result = {"language": "en", "segments": []}
        
        json_output = converter.to_json(empty_result)
        parsed = json.loads(json_output)
        assert parsed["segments"] == []
        
        srt_output = converter.to_srt(empty_result)
        assert srt_output.strip() == ""
        
        txt_output = converter.to_txt(empty_result)
        assert txt_output.strip() == ""


class TestTranscriptionSummary:
    """Test transcription summary functionality."""
    
    @pytest.fixture
    def sample_result_with_speakers(self):
        """Sample result with multiple speakers."""
        return {
            "language": "en",
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Hello world from speaker one",
                    "speaker": "SPEAKER_00",
                    "words": [
                        {"word": "Hello", "start": 0.0, "end": 0.5, "score": 0.9, "speaker": "SPEAKER_00"},
                        {"word": "world", "start": 0.6, "end": 1.0, "score": 0.8, "speaker": "SPEAKER_00"}
                    ]
                },
                {
                    "start": 6.0,
                    "end": 10.0,
                    "text": "Response from speaker two",
                    "speaker": "SPEAKER_01",
                    "words": [
                        {"word": "Response", "start": 6.0, "end": 6.8, "score": 0.95, "speaker": "SPEAKER_01"}
                    ]
                },
                {
                    "start": 11.0,
                    "end": 15.0,
                    "text": "More from speaker one",
                    "speaker": "SPEAKER_00"
                }
            ],
            "processing_info": {
                "total_processing_time": 45.5,
                "memory_report": {"peak_usage": {"total_gb": 4.2}}
            }
        }
    
    def test_get_basic_stats(self, sample_result_with_speakers):
        """Test basic statistics calculation."""
        summary = TranscriptionSummary(sample_result_with_speakers)
        stats = summary.get_basic_stats()
        
        assert stats["total_duration"] == 15.0  # End of last segment
        assert stats["total_segments"] == 3
        assert stats["total_words"] == 11  # Total words across segments
        assert stats["language"] == "en"
        assert stats["words_per_minute"] == 44.0  # 11 words / (15/60) minutes
        assert "total_duration_formatted" in stats
    
    def test_get_basic_stats_empty(self):
        """Test basic statistics with empty result."""
        empty_result = {"language": "en", "segments": []}
        summary = TranscriptionSummary(empty_result)
        stats = summary.get_basic_stats()
        
        assert stats["total_duration"] == 0.0
        assert stats["total_segments"] == 0
        assert stats["total_words"] == 0
        assert stats["language"] == "en"
    
    def test_get_speaker_stats(self, sample_result_with_speakers):
        """Test speaker statistics calculation."""
        summary = TranscriptionSummary(sample_result_with_speakers)
        speaker_stats = summary.get_speaker_stats()
        
        assert speaker_stats["speaker_count"] == 2
        
        speakers = speaker_stats["speakers"]
        assert len(speakers) == 2
        
        # Speakers should be sorted by duration (longest first)
        speaker_00 = next(s for s in speakers if s["speaker"] == "SPEAKER_00")
        speaker_01 = next(s for s in speakers if s["speaker"] == "SPEAKER_01")
        
        assert speaker_00["duration"] == 9.0  # 5.0 + 4.0 (two segments)
        assert speaker_00["segments"] == 2
        assert speaker_00["words"] == 7  # "Hello world from speaker one" + "More from speaker one"
        
        assert speaker_01["duration"] == 4.0
        assert speaker_01["segments"] == 1
        assert speaker_01["words"] == 4  # "Response from speaker two"
        
        # Check percentages
        total_duration = speaker_00["duration"] + speaker_01["duration"]
        assert abs(speaker_00["percentage"] - (9.0 / total_duration * 100)) < 0.1
    
    def test_get_speaker_stats_no_speakers(self):
        """Test speaker statistics without speaker data."""
        result_no_speakers = {
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "Hello world"}
            ]
        }
        
        summary = TranscriptionSummary(result_no_speakers)
        speaker_stats = summary.get_speaker_stats()
        
        assert speaker_stats["speaker_count"] == 1
        assert speaker_stats["speakers"][0]["speaker"] == "UNKNOWN"
    
    def test_get_confidence_stats(self, sample_result_with_speakers):
        """Test confidence score statistics."""
        summary = TranscriptionSummary(sample_result_with_speakers)
        confidence_stats = summary.get_confidence_stats()
        
        assert confidence_stats["has_confidence_scores"] is True
        assert confidence_stats["total_words_with_scores"] == 3  # 3 words have scores
        
        # Average of [0.9, 0.8, 0.95]
        expected_avg = (0.9 + 0.8 + 0.95) / 3
        assert abs(confidence_stats["average_confidence"] - expected_avg) < 0.001
        
        assert confidence_stats["min_confidence"] == 0.8
        assert confidence_stats["max_confidence"] == 0.95
        assert confidence_stats["low_confidence_words"] == 0  # None below 0.7
        assert confidence_stats["high_confidence_words"] == 2  # 0.9 and 0.95 >= 0.9
    
    def test_get_confidence_stats_no_scores(self):
        """Test confidence statistics without confidence scores."""
        result_no_scores = {
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "Hello world"}
            ]
        }
        
        summary = TranscriptionSummary(result_no_scores)
        confidence_stats = summary.get_confidence_stats()
        
        assert confidence_stats["has_confidence_scores"] is False
        assert confidence_stats["total_words_with_scores"] == 0
    
    def test_get_full_summary(self, sample_result_with_speakers):
        """Test comprehensive summary generation."""
        summary = TranscriptionSummary(sample_result_with_speakers)
        full_summary = summary.get_full_summary()
        
        # Should include all sub-summaries
        assert "basic_stats" in full_summary
        assert "speaker_stats" in full_summary
        assert "confidence_stats" in full_summary
        assert "processing_info" in full_summary
        
        # Check that processing info is included
        assert full_summary["processing_info"]["total_processing_time"] == 45.5
    
    def test_format_duration(self):
        """Test duration formatting."""
        summary = TranscriptionSummary({"segments": []})
        
        assert summary._format_duration(30) == "00:30"
        assert summary._format_duration(90) == "01:30"
        assert summary._format_duration(3665) == "61:05"
        assert summary._format_duration(3720) == "01:02:00"


if __name__ == "__main__":
    pytest.main([__file__])