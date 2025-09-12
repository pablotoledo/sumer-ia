"""Format converters for WhisperX transcription results."""

import json
from typing import Dict, Any, List
from datetime import timedelta
import re


class TranscriptionFormatConverter:
    """Converts WhisperX results to various output formats."""
    
    def __init__(self, include_speaker_labels: bool = True, 
                 include_word_timestamps: bool = True,
                 include_confidence_scores: bool = True):
        """Initialize format converter.
        
        Args:
            include_speaker_labels: Include speaker labels in output
            include_word_timestamps: Include word-level timestamps
            include_confidence_scores: Include confidence scores where available
        """
        self.include_speaker_labels = include_speaker_labels
        self.include_word_timestamps = include_word_timestamps
        self.include_confidence_scores = include_confidence_scores
    
    def to_json(self, result: Dict[str, Any], pretty: bool = True) -> str:
        """Convert result to JSON format.
        
        Args:
            result: WhisperX transcription result
            pretty: Pretty print JSON with indentation
            
        Returns:
            JSON string representation
        """
        # Create a clean copy of the result
        output = {
            'language': result.get('language', 'unknown'),
            'segments': []
        }
        
        # Process segments
        for segment in result.get('segments', []):
            segment_data = {
                'start': segment.get('start', 0.0),
                'end': segment.get('end', 0.0),
                'text': segment.get('text', '').strip()
            }
            
            # Add speaker information
            if self.include_speaker_labels and 'speaker' in segment:
                segment_data['speaker'] = segment['speaker']
            
            # Add word-level information
            if self.include_word_timestamps and 'words' in segment:
                words = []
                for word in segment['words']:
                    word_data = {
                        'word': word.get('word', ''),
                        'start': word.get('start', 0.0),
                        'end': word.get('end', 0.0)
                    }
                    
                    # Add confidence score if available and requested
                    if self.include_confidence_scores and 'score' in word:
                        word_data['confidence'] = round(word['score'], 3)
                    
                    # Add speaker label to word if available and requested
                    if self.include_speaker_labels and 'speaker' in word:
                        word_data['speaker'] = word['speaker']
                    
                    words.append(word_data)
                
                segment_data['words'] = words
            
            output['segments'].append(segment_data)
        
        # Add processing metadata if available
        if 'processing_info' in result:
            output['processing_info'] = result['processing_info']
        
        if 'segment_processing_info' in result:
            output['segment_processing_info'] = result['segment_processing_info']
        
        # Convert to JSON
        if pretty:
            return json.dumps(output, indent=2, ensure_ascii=False)
        else:
            return json.dumps(output, ensure_ascii=False)
    
    def to_srt(self, result: Dict[str, Any]) -> str:
        """Convert result to SRT subtitle format.
        
        Args:
            result: WhisperX transcription result
            
        Returns:
            SRT format string
        """
        srt_content = []
        
        for i, segment in enumerate(result.get('segments', []), 1):
            start_time = self._format_timestamp_srt(segment.get('start', 0.0))
            end_time = self._format_timestamp_srt(segment.get('end', 0.0))
            
            # Format text with speaker label if available
            text = segment.get('text', '').strip()
            if self.include_speaker_labels and 'speaker' in segment:
                text = f"[{segment['speaker']}]: {text}"
            
            srt_entry = f"{i}\n{start_time} --> {end_time}\n{text}\n"
            srt_content.append(srt_entry)
        
        return '\n'.join(srt_content)
    
    def to_vtt(self, result: Dict[str, Any]) -> str:
        """Convert result to WebVTT format.
        
        Args:
            result: WhisperX transcription result
            
        Returns:
            VTT format string
        """
        vtt_content = ["WEBVTT", ""]
        
        for segment in result.get('segments', []):
            start_time = self._format_timestamp_vtt(segment.get('start', 0.0))
            end_time = self._format_timestamp_vtt(segment.get('end', 0.0))
            
            # Format text with speaker label if available
            text = segment.get('text', '').strip()
            if self.include_speaker_labels and 'speaker' in segment:
                text = f"[{segment['speaker']}]: {text}"
            
            vtt_entry = f"{start_time} --> {end_time}\n{text}\n"
            vtt_content.append(vtt_entry)
        
        return '\n'.join(vtt_content)
    
    def to_txt(self, result: Dict[str, Any], include_timestamps: bool = False) -> str:
        """Convert result to plain text format.
        
        Args:
            result: WhisperX transcription result
            include_timestamps: Include timestamps in text output
            
        Returns:
            Plain text string
        """
        txt_content = []
        
        for segment in result.get('segments', []):
            text = segment.get('text', '').strip()
            
            # Add timestamp if requested
            if include_timestamps:
                start_time = self._format_timestamp_readable(segment.get('start', 0.0))
                prefix = f"[{start_time}] "
            else:
                prefix = ""
            
            # Add speaker label if available
            if self.include_speaker_labels and 'speaker' in segment:
                speaker_label = f"[{segment['speaker']}]: "
            else:
                speaker_label = ""
            
            line = f"{prefix}{speaker_label}{text}"
            txt_content.append(line)
        
        return '\n'.join(txt_content)
    
    def to_csv(self, result: Dict[str, Any]) -> str:
        """Convert result to CSV format.
        
        Args:
            result: WhisperX transcription result
            
        Returns:
            CSV format string
        """
        csv_lines = []
        
        # Header
        headers = ['start', 'end', 'duration', 'text']
        if self.include_speaker_labels:
            headers.insert(-1, 'speaker')
        csv_lines.append(','.join(headers))
        
        # Data rows
        for segment in result.get('segments', []):
            start = segment.get('start', 0.0)
            end = segment.get('end', 0.0)
            duration = end - start
            text = segment.get('text', '').strip().replace('"', '""')  # Escape quotes
            
            row = [
                f"{start:.3f}",
                f"{end:.3f}",
                f"{duration:.3f}",
                f'"{text}"'
            ]
            
            if self.include_speaker_labels:
                speaker = segment.get('speaker', 'UNKNOWN')
                row.insert(-1, speaker)
            
            csv_lines.append(','.join(row))
        
        return '\n'.join(csv_lines)
    
    def to_word_level_json(self, result: Dict[str, Any]) -> str:
        """Convert result to word-level JSON format.
        
        Args:
            result: WhisperX transcription result
            
        Returns:
            Word-level JSON string
        """
        words_list = []
        
        for segment in result.get('segments', []):
            if 'words' in segment:
                for word in segment['words']:
                    word_data = {
                        'word': word.get('word', ''),
                        'start': word.get('start', 0.0),
                        'end': word.get('end', 0.0),
                        'duration': word.get('end', 0.0) - word.get('start', 0.0)
                    }
                    
                    if self.include_confidence_scores and 'score' in word:
                        word_data['confidence'] = round(word['score'], 3)
                    
                    if self.include_speaker_labels and 'speaker' in word:
                        word_data['speaker'] = word['speaker']
                    
                    words_list.append(word_data)
            else:
                # If no word-level data, create from segment
                segment_words = segment.get('text', '').split()
                segment_start = segment.get('start', 0.0)
                segment_end = segment.get('end', 0.0)
                segment_duration = segment_end - segment_start
                word_duration = segment_duration / len(segment_words) if segment_words else 0
                
                for i, word_text in enumerate(segment_words):
                    word_start = segment_start + (i * word_duration)
                    word_end = word_start + word_duration
                    
                    word_data = {
                        'word': word_text,
                        'start': word_start,
                        'end': word_end,
                        'duration': word_duration
                    }
                    
                    if self.include_speaker_labels and 'speaker' in segment:
                        word_data['speaker'] = segment['speaker']
                    
                    words_list.append(word_data)
        
        output = {
            'language': result.get('language', 'unknown'),
            'words': words_list,
            'total_words': len(words_list)
        }
        
        return json.dumps(output, indent=2, ensure_ascii=False)
    
    def _format_timestamp_srt(self, seconds: float) -> str:
        """Format timestamp for SRT format (HH:MM:SS,mmm).
        
        Args:
            seconds: Timestamp in seconds
            
        Returns:
            Formatted timestamp string
        """
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = int((td.total_seconds() - total_seconds) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def _format_timestamp_vtt(self, seconds: float) -> str:
        """Format timestamp for VTT format (HH:MM:SS.mmm).
        
        Args:
            seconds: Timestamp in seconds
            
        Returns:
            Formatted timestamp string
        """
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds_part = total_seconds % 60
        milliseconds = int((td.total_seconds() - total_seconds) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds_part:02d}.{milliseconds:03d}"
    
    def _format_timestamp_readable(self, seconds: float) -> str:
        """Format timestamp in human-readable format (MM:SS).
        
        Args:
            seconds: Timestamp in seconds
            
        Returns:
            Formatted timestamp string
        """
        minutes = int(seconds // 60)
        seconds_part = int(seconds % 60)
        return f"{minutes:02d}:{seconds_part:02d}"


class TranscriptionSummary:
    """Generate summaries and statistics from transcription results."""
    
    def __init__(self, result: Dict[str, Any]):
        """Initialize with transcription result.
        
        Args:
            result: WhisperX transcription result
        """
        self.result = result
        self.segments = result.get('segments', [])
    
    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the transcription.
        
        Returns:
            Dictionary with basic statistics
        """
        if not self.segments:
            return {
                'total_duration': 0.0,
                'total_segments': 0,
                'total_words': 0,
                'total_characters': 0,
                'language': self.result.get('language', 'unknown')
            }
        
        total_duration = max(seg.get('end', 0.0) for seg in self.segments)
        total_words = sum(len(seg.get('text', '').split()) for seg in self.segments)
        total_characters = sum(len(seg.get('text', '')) for seg in self.segments)
        
        return {
            'total_duration': total_duration,
            'total_duration_formatted': self._format_duration(total_duration),
            'total_segments': len(self.segments),
            'total_words': total_words,
            'total_characters': total_characters,
            'language': self.result.get('language', 'unknown'),
            'words_per_minute': (total_words / (total_duration / 60)) if total_duration > 0 else 0
        }
    
    def get_speaker_stats(self) -> Dict[str, Any]:
        """Get speaker-related statistics.
        
        Returns:
            Dictionary with speaker statistics
        """
        if not self.segments:
            return {'speakers': [], 'speaker_count': 0}
        
        speaker_stats = {}
        
        for segment in self.segments:
            speaker = segment.get('speaker', 'UNKNOWN')
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    'duration': 0.0,
                    'segments': 0,
                    'words': 0,
                    'characters': 0
                }
            
            duration = segment.get('end', 0.0) - segment.get('start', 0.0)
            text = segment.get('text', '')
            
            speaker_stats[speaker]['duration'] += duration
            speaker_stats[speaker]['segments'] += 1
            speaker_stats[speaker]['words'] += len(text.split())
            speaker_stats[speaker]['characters'] += len(text)
        
        # Convert to list and add percentages
        total_duration = sum(stats['duration'] for stats in speaker_stats.values())
        speakers_list = []
        
        for speaker, stats in speaker_stats.items():
            percentage = (stats['duration'] / total_duration * 100) if total_duration > 0 else 0
            speakers_list.append({
                'speaker': speaker,
                'duration': stats['duration'],
                'duration_formatted': self._format_duration(stats['duration']),
                'percentage': round(percentage, 1),
                'segments': stats['segments'],
                'words': stats['words'],
                'characters': stats['characters']
            })
        
        # Sort by duration (longest first)
        speakers_list.sort(key=lambda x: x['duration'], reverse=True)
        
        return {
            'speakers': speakers_list,
            'speaker_count': len(speakers_list)
        }
    
    def get_confidence_stats(self) -> Dict[str, Any]:
        """Get confidence score statistics (if available).
        
        Returns:
            Dictionary with confidence statistics
        """
        all_scores = []
        
        for segment in self.segments:
            if 'words' in segment:
                for word in segment['words']:
                    if 'score' in word:
                        all_scores.append(word['score'])
        
        if not all_scores:
            return {
                'has_confidence_scores': False,
                'total_words_with_scores': 0
            }
        
        return {
            'has_confidence_scores': True,
            'total_words_with_scores': len(all_scores),
            'average_confidence': round(sum(all_scores) / len(all_scores), 3),
            'min_confidence': round(min(all_scores), 3),
            'max_confidence': round(max(all_scores), 3),
            'low_confidence_words': len([s for s in all_scores if s < 0.7]),
            'high_confidence_words': len([s for s in all_scores if s >= 0.9])
        }
    
    def get_full_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of transcription.
        
        Returns:
            Complete summary dictionary
        """
        summary = {
            'basic_stats': self.get_basic_stats(),
            'speaker_stats': self.get_speaker_stats(),
            'confidence_stats': self.get_confidence_stats()
        }
        
        # Add processing info if available
        if 'processing_info' in self.result:
            summary['processing_info'] = self.result['processing_info']
        
        if 'segment_processing_info' in self.result:
            summary['segment_processing_info'] = self.result['segment_processing_info']
        
        return summary
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds_part = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds_part:02d}"
        else:
            return f"{minutes:02d}:{seconds_part:02d}"