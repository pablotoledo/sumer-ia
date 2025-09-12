"""
Content Format Detector - Automatic Detection of Content Types
============================================================

Automatically detects and classifies different types of transcribed content:
- Diarized meetings (MS Teams, Zoom, etc.)
- Linear presentations/lectures
- Educational content
- Technical documentation
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple, Optional
from collections import Counter


class ContentFormat(Enum):
    DIARIZED_MEETING = "diarized_meeting"
    LINEAR_PRESENTATION = "linear_presentation"
    EDUCATIONAL_LECTURE = "educational_lecture"
    TECHNICAL_DOCUMENTATION = "technical_documentation"
    GENERIC_TRANSCRIPTION = "generic_transcription"


@dataclass
class FormatDetectionResult:
    format_type: ContentFormat
    confidence_score: float  # 0.0 - 1.0
    participants: List[str]  # For meetings
    key_indicators: List[str]
    processing_recommendations: Dict[str, any]


class ContentFormatDetector:
    """Detect and classify content format automatically."""
    
    def __init__(self):
        # Patterns for different content types
        self.meeting_patterns = {
            'speaker_timestamps': r'\[(\d{2}:\d{2}:\d{2})\]\s*([A-Za-z_][A-Za-z0-9_]*):',
            'speaker_names': r'^([A-Za-z_][A-Za-z0-9_]*)\s*[:,]\s*',
            'meeting_language': [
                'acuerdo', 'decidir', 'action item', 'tarea', 'asignar', 
                'pendiente', 'revisar', 'seguimiento', 'deadline', 'entrega'
            ],
            'interruptions': r'(\.\.\.|--|\[interrumpe\]|\[overlapping\])',
            'questions_to_others': r'(\?.*[A-Za-z_]+[,:]|[A-Za-z_]+.*\?)'
        }
        
        self.presentation_patterns = {
            'sequential_topics': r'(primero|segundo|tercero|siguiente|luego|finalmente)',
            'presentation_language': [
                'vamos a ver', 'como pueden observar', 'en esta diapositiva',
                'pasemos a', 'continuando con', 'en resumen', 'para concluir'
            ],
            'slide_references': r'(diapositiva|slide|gráfico|tabla|figura)'
        }
        
        self.educational_patterns = {
            'educational_language': [
                'aprendizaje', 'concepto', 'definición', 'ejemplo', 'ejercicio',
                'pregunta', 'respuesta', 'explicación', 'metodología', 'teoría'
            ],
            'academic_structure': r'(introducción|desarrollo|conclusión|hipótesis|metodología)'
        }
        
        self.technical_patterns = {
            'technical_language': [
                'implementación', 'algoritmo', 'arquitectura', 'sistema', 'código',
                'función', 'método', 'clase', 'variable', 'API', 'endpoint'
            ],
            'code_references': r'(función|method|class|variable|endpoint|API)'
        }

    def detect_format(self, content: str) -> FormatDetectionResult:
        """Main method to detect content format."""
        
        # Calculate confidence scores for each format
        meeting_score = self._calculate_meeting_score(content)
        presentation_score = self._calculate_presentation_score(content)
        educational_score = self._calculate_educational_score(content)
        technical_score = self._calculate_technical_score(content)
        
        # Determine primary format
        scores = {
            ContentFormat.DIARIZED_MEETING: meeting_score,
            ContentFormat.LINEAR_PRESENTATION: presentation_score,
            ContentFormat.EDUCATIONAL_LECTURE: educational_score,
            ContentFormat.TECHNICAL_DOCUMENTATION: technical_score
        }
        
        primary_format = max(scores, key=scores.get)
        confidence = scores[primary_format]
        
        # If confidence is too low, mark as generic
        if confidence < 0.3:
            primary_format = ContentFormat.GENERIC_TRANSCRIPTION
            confidence = 0.5
        
        # Extract specific information based on detected format
        participants = self._extract_participants(content) if primary_format == ContentFormat.DIARIZED_MEETING else []
        key_indicators = self._get_key_indicators(content, primary_format)
        recommendations = self._get_processing_recommendations(primary_format, confidence, len(participants))
        
        return FormatDetectionResult(
            format_type=primary_format,
            confidence_score=confidence,
            participants=participants,
            key_indicators=key_indicators,
            processing_recommendations=recommendations
        )
    
    def _calculate_meeting_score(self, content: str) -> float:
        """Calculate confidence score for meeting format."""
        score = 0.0
        
        # Check for speaker identification patterns
        speaker_timestamp_matches = len(re.findall(self.meeting_patterns['speaker_timestamps'], content))
        speaker_name_matches = len(re.findall(self.meeting_patterns['speaker_names'], content, re.MULTILINE))
        
        if speaker_timestamp_matches > 0:
            score += 0.6  # Strong indicator
        elif speaker_name_matches >= 3:
            score += 0.4  # Moderate indicator
        
        # Check for meeting language
        meeting_words = sum(1 for word in self.meeting_patterns['meeting_language'] 
                           if word.lower() in content.lower())
        score += min(meeting_words * 0.05, 0.3)
        
        # Check for interruptions/overlapping speech
        interruption_matches = len(re.findall(self.meeting_patterns['interruptions'], content))
        if interruption_matches > 0:
            score += 0.1
        
        # Check for questions directed at specific people
        directed_questions = len(re.findall(self.meeting_patterns['questions_to_others'], content))
        if directed_questions > 0:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_presentation_score(self, content: str) -> float:
        """Calculate confidence score for presentation format."""
        score = 0.0
        
        # Sequential indicators
        sequential_matches = len(re.findall(self.presentation_patterns['sequential_topics'], content, re.IGNORECASE))
        score += min(sequential_matches * 0.1, 0.3)
        
        # Presentation language
        presentation_words = sum(1 for phrase in self.presentation_patterns['presentation_language']
                               if phrase.lower() in content.lower())
        score += min(presentation_words * 0.08, 0.4)
        
        # Slide references
        slide_matches = len(re.findall(self.presentation_patterns['slide_references'], content, re.IGNORECASE))
        score += min(slide_matches * 0.1, 0.2)
        
        return min(score, 1.0)
    
    def _calculate_educational_score(self, content: str) -> float:
        """Calculate confidence score for educational content."""
        score = 0.0
        
        # Educational vocabulary
        educational_words = sum(1 for word in self.educational_patterns['educational_language']
                              if word.lower() in content.lower())
        score += min(educational_words * 0.06, 0.5)
        
        # Academic structure
        structure_matches = len(re.findall(self.educational_patterns['academic_structure'], content, re.IGNORECASE))
        score += min(structure_matches * 0.15, 0.3)
        
        return min(score, 1.0)
    
    def _calculate_technical_score(self, content: str) -> float:
        """Calculate confidence score for technical content."""
        score = 0.0
        
        # Technical vocabulary
        technical_words = sum(1 for word in self.technical_patterns['technical_language']
                            if word.lower() in content.lower())
        score += min(technical_words * 0.05, 0.4)
        
        # Code references
        code_matches = len(re.findall(self.technical_patterns['code_references'], content, re.IGNORECASE))
        score += min(code_matches * 0.1, 0.3)
        
        return min(score, 1.0)
    
    def _extract_participants(self, content: str) -> List[str]:
        """Extract participant names from meeting content."""
        participants = set()
        
        # Extract from timestamp format: [HH:MM:SS] Name:
        timestamp_pattern = self.meeting_patterns['speaker_timestamps']
        matches = re.findall(timestamp_pattern, content)
        for _, name in matches:
            participants.add(name)
        
        # Extract from simple format: Name:
        name_pattern = self.meeting_patterns['speaker_names']
        matches = re.findall(name_pattern, content, re.MULTILINE)
        for name in matches:
            # Clean up the name
            clean_name = re.sub(r'[:\s]+$', '', name.strip())
            if len(clean_name) > 1 and clean_name.isalpha():
                participants.add(clean_name)
        
        return sorted(list(participants))
    
    def _get_key_indicators(self, content: str, format_type: ContentFormat) -> List[str]:
        """Get key indicators that led to format detection."""
        indicators = []
        
        if format_type == ContentFormat.DIARIZED_MEETING:
            participants = self._extract_participants(content)
            if participants:
                indicators.append(f"Participants detected: {', '.join(participants[:3])}")
            if 'acuerdo' in content.lower() or 'decidir' in content.lower():
                indicators.append("Decision-making language detected")
            if re.search(self.meeting_patterns['interruptions'], content):
                indicators.append("Conversational interruptions found")
        
        elif format_type == ContentFormat.LINEAR_PRESENTATION:
            if any(phrase in content.lower() for phrase in self.presentation_patterns['presentation_language']):
                indicators.append("Presentation language patterns")
            if re.search(self.presentation_patterns['sequential_topics'], content, re.IGNORECASE):
                indicators.append("Sequential topic structure")
        
        elif format_type == ContentFormat.EDUCATIONAL_LECTURE:
            if any(word in content.lower() for word in self.educational_patterns['educational_language']):
                indicators.append("Educational vocabulary")
            if re.search(self.educational_patterns['academic_structure'], content, re.IGNORECASE):
                indicators.append("Academic structure patterns")
        
        elif format_type == ContentFormat.TECHNICAL_DOCUMENTATION:
            if any(word in content.lower() for word in self.technical_patterns['technical_language']):
                indicators.append("Technical vocabulary")
            if re.search(self.technical_patterns['code_references'], content, re.IGNORECASE):
                indicators.append("Code/API references")
        
        return indicators
    
    def _get_processing_recommendations(self, format_type: ContentFormat, 
                                     confidence: float, participants_count: int) -> Dict[str, any]:
        """Get processing recommendations based on detected format."""
        
        base_recommendations = {
            "agent_type": "simple_processor",
            "segmentation_method": "semantic",
            "qa_questions_per_segment": 3,
            "retention_target": 0.75
        }
        
        if format_type == ContentFormat.DIARIZED_MEETING:
            return {
                **base_recommendations,
                "agent_type": "meeting_processor",
                "segmentation_method": "conversational_topics",
                "qa_questions_per_segment": 4,
                "qa_focus": "decisions_and_actions",
                "special_extraction": ["decisions", "action_items", "participants"],
                "output_format": "meeting_summary"
            }
        
        elif format_type == ContentFormat.LINEAR_PRESENTATION:
            return {
                **base_recommendations,
                "segmentation_method": "topic_transitions",
                "qa_questions_per_segment": 4,
                "qa_focus": "key_concepts",
                "retention_target": 0.85
            }
        
        elif format_type == ContentFormat.EDUCATIONAL_LECTURE:
            return {
                **base_recommendations,
                "qa_questions_per_segment": 5,
                "qa_focus": "learning_objectives",
                "retention_target": 0.90
            }
        
        elif format_type == ContentFormat.TECHNICAL_DOCUMENTATION:
            return {
                **base_recommendations,
                "qa_questions_per_segment": 4,
                "qa_focus": "implementation_details",
                "retention_target": 0.85,
                "preserve_technical_terms": True
            }
        
        else:  # GENERIC_TRANSCRIPTION
            return base_recommendations


def analyze_content_format(content: str) -> FormatDetectionResult:
    """Convenience function to analyze content format."""
    detector = ContentFormatDetector()
    return detector.detect_format(content)


# Test with sample content
if __name__ == "__main__":
    # Test meeting content
    meeting_sample = """
    [10:30:15] Juan_Martinez: Buenos días equipo, vamos a revisar el tema del rate limiting.
    
    [10:30:28] Maria_Lopez: Perfecto Juan. Como comenté ayer, hemos detectado problemas en la API de pagos.
    
    [10:30:45] Pablo_Rodriguez: Sí, he revisado los logs y el problema viene del endpoint /transactions. Propongo implementar un circuit breaker.
    
    [10:31:02] Juan_Martinez: Me parece bien Pablo. ¿Cuándo podrías tenerlo listo?
    
    [10:31:10] Pablo_Rodriguez: Si empezamos hoy, para el viernes podríamos tenerlo en producción.
    """
    
    result = analyze_content_format(meeting_sample)
    print(f"Format: {result.format_type}")
    print(f"Confidence: {result.confidence_score:.2f}")
    print(f"Participants: {result.participants}")
    print(f"Key Indicators: {result.key_indicators}")
    print(f"Recommendations: {result.processing_recommendations}")