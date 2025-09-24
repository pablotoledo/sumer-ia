"""Tests for the transcription format conversion utilities."""

import json

import pytest

from format_converters import TranscriptionFormatConverter, TranscriptionSummary


@pytest.fixture
def sample_result() -> dict:
    return {
        "language": "en",
        "segments": [
            {
                "start": 0.0,
                "end": 5.0,
                "text": "Hello world from speaker one",
                "speaker": "SPEAKER_00",
                "words": [
                    {"word": "Hello", "start": 0.0, "end": 0.4, "score": 0.9, "speaker": "SPEAKER_00"},
                    {"word": "world", "start": 0.5, "end": 0.9, "score": 0.85, "speaker": "SPEAKER_00"},
                ],
            },
            {
                "start": 6.0,
                "end": 10.0,
                "text": "Response from speaker two",
                "speaker": "SPEAKER_01",
                "words": [
                    {"word": "Response", "start": 6.0, "end": 6.6, "score": 0.95, "speaker": "SPEAKER_01"}
                ],
            },
        ],
        "processing_info": {"total_processing_time": 12.3},
    }


class TestTranscriptionFormatConverter:
    def test_to_json_includes_requested_fields(self, sample_result: dict) -> None:
        converter = TranscriptionFormatConverter(
            include_speaker_labels=True,
            include_word_timestamps=True,
            include_confidence_scores=True,
        )

        json_output = converter.to_json(sample_result, pretty=True)
        parsed = json.loads(json_output)

        assert parsed["language"] == "en"
        assert parsed["processing_info"] == {"total_processing_time": 12.3}
        first_segment = parsed["segments"][0]
        assert first_segment["speaker"] == "SPEAKER_00"
        assert first_segment["words"][0]["confidence"] == 0.9
        assert first_segment["words"][0]["speaker"] == "SPEAKER_00"

    def test_to_json_respects_feature_flags(self, sample_result: dict) -> None:
        converter = TranscriptionFormatConverter(
            include_speaker_labels=False,
            include_word_timestamps=False,
            include_confidence_scores=False,
        )

        parsed = json.loads(converter.to_json(sample_result, pretty=False))

        assert "speaker" not in parsed["segments"][0]
        assert "words" not in parsed["segments"][0]
        assert "\n" not in converter.to_json(sample_result, pretty=False)

    def test_to_srt_structure(self, sample_result: dict) -> None:
        converter = TranscriptionFormatConverter()

        srt_output = converter.to_srt(sample_result)
        lines = [line for line in srt_output.splitlines() if line]

        assert lines[0] == "1"
        assert "00:00:00,000 --> 00:00:05,000" in lines[1]
        assert lines[2] == "[SPEAKER_00]: Hello world from speaker one"
        assert lines[3] == "2"
        assert "00:00:06,000 --> 00:00:10,000" in lines[4]

    def test_to_vtt_structure(self, sample_result: dict) -> None:
        converter = TranscriptionFormatConverter()

        vtt_output = converter.to_vtt(sample_result)
        lines = vtt_output.splitlines()

        assert lines[0] == "WEBVTT"
        assert lines[2].startswith("00:00:00.000 --> 00:00:05.000")
        assert lines[3] == "[SPEAKER_00]: Hello world from speaker one"

    def test_to_txt_with_and_without_timestamps(self, sample_result: dict) -> None:
        converter = TranscriptionFormatConverter()

        plain = converter.to_txt(sample_result)
        with_ts = converter.to_txt(sample_result, include_timestamps=True)

        assert plain.splitlines()[0] == "[SPEAKER_00]: Hello world from speaker one"
        assert with_ts.splitlines()[0].startswith("[00:00] [SPEAKER_00]: Hello world from speaker one")

    def test_timestamp_helpers(self) -> None:
        converter = TranscriptionFormatConverter()

        assert converter._format_timestamp_srt(65.432) == "00:01:05,432"
        assert converter._format_timestamp_vtt(65.432) == "00:01:05.432"
        assert converter._format_timestamp_readable(125) == "02:05"


class TestTranscriptionSummary:
    @pytest.fixture
    def summary(self, sample_result: dict) -> TranscriptionSummary:
        return TranscriptionSummary(sample_result)

    def test_basic_stats(self, summary: TranscriptionSummary) -> None:
        stats = summary.get_basic_stats()

        assert stats["total_duration"] == 10.0
        assert stats["total_segments"] == 2
        assert stats["total_words"] == 9  # 5 words + 4 words
        assert stats["language"] == "en"
        assert stats["words_per_minute"] == pytest.approx(54.0)

    def test_basic_stats_empty(self) -> None:
        empty_summary = TranscriptionSummary({"language": "en", "segments": []})

        stats = empty_summary.get_basic_stats()

        assert stats == {
            "total_duration": 0.0,
            "total_segments": 0,
            "total_words": 0,
            "total_characters": 0,
            "language": "en",
        }

    def test_speaker_stats(self, summary: TranscriptionSummary) -> None:
        speaker_stats = summary.get_speaker_stats()

        assert speaker_stats["speaker_count"] == 2
        first_speaker = speaker_stats["speakers"][0]
        assert first_speaker["speaker"] == "SPEAKER_00"
        assert first_speaker["segments"] == 1
        assert first_speaker["duration"] == 5.0

    def test_confidence_stats(self, summary: TranscriptionSummary) -> None:
        conf = summary.get_confidence_stats()

        assert conf["has_confidence_scores"] is True
        assert conf["total_words_with_scores"] == 3
        assert conf["average_confidence"] == pytest.approx((0.9 + 0.85 + 0.95) / 3, rel=1e-6)
        assert conf["high_confidence_words"] == 2

    def test_confidence_stats_without_scores(self) -> None:
        summary = TranscriptionSummary({"segments": [{"start": 0.0, "end": 1.0, "text": "hello"}]})

        conf = summary.get_confidence_stats()

        assert conf == {"has_confidence_scores": False, "total_words_with_scores": 0}

    def test_full_summary_includes_processing_info(self, summary: TranscriptionSummary) -> None:
        summary_dict = summary.get_full_summary()

        assert "basic_stats" in summary_dict
        assert "speaker_stats" in summary_dict
        assert "confidence_stats" in summary_dict
        assert summary_dict["processing_info"] == {"total_processing_time": 12.3}

    def test_format_duration(self, summary: TranscriptionSummary) -> None:
        assert summary._format_duration(30) == "00:30"
        assert summary._format_duration(90) == "01:30"
        assert summary._format_duration(3665) == "01:01:05"
