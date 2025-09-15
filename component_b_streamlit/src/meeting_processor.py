"""
Meeting Processor - Specialized Processing for Diarized Meetings
==============================================================

Specialized agents and segmentation for processing diarized meeting transcripts
from MS Teams, Zoom, and other conferencing platforms.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from mcp_agent.core.fastagent import FastAgent
import yaml


@dataclass 
class ConversationalSegment:
    """Represents a segment of conversation focused on a specific topic."""
    topic: str
    content: str
    participants: List[str]
    decisions: List[str]
    action_items: List[str]
    start_time: Optional[str] = None
    end_time: Optional[str] = None


@dataclass
class MeetingStructure:
    """Represents the overall structure of a meeting."""
    participants: List[str]
    total_duration: Optional[str]
    main_topics: List[str]
    decisions_made: List[str]
    action_items: List[Dict[str, str]]  # {"task": "", "assignee": "", "deadline": ""}
    unresolved_questions: List[str]


class ConversationalSegmenter:
    """Segments meeting content by conversational topics rather than length."""
    
    def __init__(self, min_segment_length: int = 300, max_segment_length: int = 1500):
        self.min_segment_length = min_segment_length
        self.max_segment_length = max_segment_length
        
        # Patterns for detecting topic transitions
        self.topic_transition_patterns = [
            r'(cambiando de tema|siguiente punto|pasemos a|ahora vamos con)',
            r'(otro tema|diferente tema|nueva cuestión|siguiente asunto)',
            r'(well|so|now|moving on to|let\'s talk about|next topic)',
            r'(vale|bueno|perfecto|bien).*?(entonces|ahora|vamos)',
        ]
        
        # Patterns for decisions and action items
        self.decision_patterns = [
            r'(decidimos|acordamos|está decidido|aprobado|confirmed)',
            r'(vamos a hacer|haremos|implementaremos|we will|let\'s do)',
            r'(conclusion|final decision|agreed)',
        ]
        
        self.action_item_patterns = [
            r'([A-Za-z_]+).*?(va a|will|going to|tiene que|needs to|debe)',
            r'(tarea para|task for|assigned to|asignado a).*?([A-Za-z_]+)',
            r'(deadline|entrega|para el|by|antes del).*?(lunes|martes|miércoles|jueves|viernes|monday|tuesday|wednesday|thursday|friday|\d+)',
        ]
    
    def segment_by_conversation_topics(self, content: str) -> List[ConversationalSegment]:
        """Segment content by conversational topics and speaker interactions."""
        
        # Split content into speaker turns
        speaker_turns = self._extract_speaker_turns(content)
        
        # Group turns into topical segments
        segments = self._group_turns_by_topic(speaker_turns)
        
        # Extract decisions and action items for each segment
        enriched_segments = []
        for segment in segments:
            enriched_segment = self._enrich_segment_with_structure(segment)
            enriched_segments.append(enriched_segment)
        
        return enriched_segments
    
    def _extract_speaker_turns(self, content: str) -> List[Dict]:
        """Extract individual speaker turns with timestamps."""
        turns = []
        
        # Pattern for timestamp + speaker: [HH:MM:SS] Speaker_Name: content
        timestamp_pattern = r'\[(\d{2}:\d{2}:\d{2})\]\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+?)(?=\[|\Z)'
        matches = re.findall(timestamp_pattern, content, re.DOTALL)
        
        for timestamp, speaker, turn_content in matches:
            turns.append({
                'timestamp': timestamp,
                'speaker': speaker,
                'content': turn_content.strip(),
                'word_count': len(turn_content.split())
            })
        
        # Fallback: simple speaker pattern without timestamps
        if not turns:
            simple_pattern = r'^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+?)(?=^[A-Za-z_]|\Z)'
            matches = re.findall(simple_pattern, content, re.MULTILINE | re.DOTALL)
            
            for speaker, turn_content in matches:
                turns.append({
                    'timestamp': None,
                    'speaker': speaker,
                    'content': turn_content.strip(),
                    'word_count': len(turn_content.split())
                })
        
        return turns
    
    def _group_turns_by_topic(self, speaker_turns: List[Dict]) -> List[ConversationalSegment]:
        """Group speaker turns into topical conversation segments."""
        if not speaker_turns:
            return []
        
        segments = []
        current_segment_turns = []
        current_word_count = 0
        
        for i, turn in enumerate(speaker_turns):
            # Check if this turn indicates a topic transition
            is_topic_transition = self._is_topic_transition(turn['content'])
            
            # Check if we should start a new segment
            should_start_new_segment = (
                is_topic_transition or 
                current_word_count > self.max_segment_length or
                (current_word_count > self.min_segment_length and 
                 self._is_natural_break_point(current_segment_turns, turn))
            )
            
            if should_start_new_segment and current_segment_turns:
                # Create segment from current turns
                segment = self._create_segment_from_turns(current_segment_turns)
                segments.append(segment)
                
                # Start new segment
                current_segment_turns = [turn]
                current_word_count = turn['word_count']
            else:
                # Add to current segment
                current_segment_turns.append(turn)
                current_word_count += turn['word_count']
        
        # Add final segment
        if current_segment_turns:
            segment = self._create_segment_from_turns(current_segment_turns)
            segments.append(segment)
        
        return segments
    
    def _is_topic_transition(self, content: str) -> bool:
        """Check if content indicates a topic transition."""
        content_lower = content.lower()
        
        for pattern in self.topic_transition_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _is_natural_break_point(self, current_turns: List[Dict], next_turn: Dict) -> bool:
        """Check if this is a natural break point between topics."""
        if not current_turns:
            return False
        
        # Check if there's a significant speaker change pattern
        last_speakers = [turn['speaker'] for turn in current_turns[-3:]]
        if next_turn['speaker'] not in last_speakers:
            return True
        
        # Check for question/answer patterns that might indicate topic closure
        last_content = current_turns[-1]['content'].lower()
        next_content = next_turn['content'].lower()
        
        if ('?' in last_content and 
            any(word in next_content for word in ['sí', 'no', 'correcto', 'exacto', 'perfecto', 'yes', 'no', 'correct'])):
            return True
        
        return False
    
    def _create_segment_from_turns(self, turns: List[Dict]) -> ConversationalSegment:
        """Create a ConversationalSegment from a list of speaker turns."""
        if not turns:
            return None
        
        # Combine all content
        content_parts = []
        for turn in turns:
            if turn['timestamp']:
                content_parts.append(f"[{turn['timestamp']}] {turn['speaker']}: {turn['content']}")
            else:
                content_parts.append(f"{turn['speaker']}: {turn['content']}")
        
        combined_content = '\n\n'.join(content_parts)
        
        # Extract participants
        participants = list(set(turn['speaker'] for turn in turns))
        
        # Infer topic from content
        topic = self._infer_topic_from_content(combined_content)
        
        # Extract timestamps
        start_time = turns[0].get('timestamp')
        end_time = turns[-1].get('timestamp') if turns else None
        
        return ConversationalSegment(
            topic=topic,
            content=combined_content,
            participants=participants,
            decisions=[],  # Will be filled by _enrich_segment_with_structure
            action_items=[],  # Will be filled by _enrich_segment_with_structure
            start_time=start_time,
            end_time=end_time
        )
    
    def _infer_topic_from_content(self, content: str) -> str:
        """Infer the main topic from the content."""
        # Simple topic inference based on most common technical terms
        words = re.findall(r'\b[A-Za-z]{4,}\b', content.lower())
        word_freq = {}
        
        # Filter out common words and focus on potential topic words
        stop_words = {'que', 'para', 'con', 'una', 'por', 'como', 'más', 'este', 'esta', 
                     'the', 'and', 'for', 'with', 'that', 'this', 'have', 'will'}
        
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        if word_freq:
            # Get top 2-3 most frequent meaningful words
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
            topic_words = [word.capitalize() for word, count in top_words if count > 1]
            
            if topic_words:
                return " - ".join(topic_words)
        
        return "Conversación General"
    
    def _enrich_segment_with_structure(self, segment: ConversationalSegment) -> ConversationalSegment:
        """Enrich segment with decisions and action items."""
        
        decisions = []
        action_items = []
        
        # Extract decisions
        for pattern in self.decision_patterns:
            matches = re.finditer(pattern, segment.content, re.IGNORECASE)
            for match in matches:
                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(segment.content), match.end() + 100)
                decision_context = segment.content[start:end].strip()
                decisions.append(decision_context)
        
        # Extract action items
        for pattern in self.action_item_patterns:
            matches = re.finditer(pattern, segment.content, re.IGNORECASE)
            for match in matches:
                start = max(0, match.start() - 50)
                end = min(len(segment.content), match.end() + 100)
                action_context = segment.content[start:end].strip()
                action_items.append(action_context)
        
        # Update segment
        segment.decisions = list(set(decisions))  # Remove duplicates
        segment.action_items = list(set(action_items))
        
        return segment


def load_config() -> dict:
    """Load FastAgent configuration."""
    for config_path in ["fastagent.config.yaml", "../fastagent.config.yaml"]:
        if Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
    return {}


# Load configuration
config = load_config()
DEFAULT_MODEL = config.get('default_model', 'azure.gpt-4.1')

# Create FastAgent instance for meeting processing
fast = FastAgent("MeetingDistributedSystem")


@fast.agent(
    name="meeting_processor",
    model=DEFAULT_MODEL,
    instruction="""You are a specialist in processing technical meeting transcripts with speaker identification.

MEETING PROCESSING TASKS:
1. **Structure Analysis**: Identify meeting flow, main topics discussed, and participant roles
2. **Decision Extraction**: Clearly identify decisions made, who proposed them, and approval status
3. **Action Items**: Extract specific tasks assigned, ownership, and deadlines mentioned
4. **Technical Discussion Summary**: Summarize technical topics with key points and context
5. **Unresolved Questions**: Identify questions or issues left unresolved

OUTPUT STRUCTURE (in Spanish):

## [Título basado en el tema principal discutido]

### 👥 Participantes
- [Lista de participantes identificados]

### 🎯 Decisiones Tomadas
1. **[Decisión]** - Propuesta por: [Persona] - Estado: [Aprobada/Pendiente]

### 📋 Action Items
- [ ] **[Persona]**: [Tarea específica] - [Deadline si se menciona]

### 🔍 Temas Técnicos Discutidos

#### [Subtema 1]
**Participantes principales**: [Nombres]
**Problema/Tema**: [Descripción]
**Soluciones propuestas**: [Lista]
**Estado**: [Resuelto/Pendiente/En progreso]

### ❓ Preguntas y Respuestas

#### Pregunta 1: [Pregunta específica sobre decisiones tomadas]
**Respuesta**: [Respuesta basada en el contenido de la reunión, incluyendo quién dijo qué]

#### Pregunta 2: [Pregunta sobre action items o tareas asignadas]
**Respuesta**: [Respuesta con detalles específicos y referencias]

CRITICAL RULES:
- Extract information ONLY from what was actually discussed
- Identify specific speakers for decisions and commitments  
- Preserve technical terminology and specific references
- Focus on actionable outcomes and follow-up items
- Always include Q&A section with meeting-specific questions
- Use Spanish throughout the response
- Quote specific phrases when referencing decisions or commitments
"""
)
def meeting_processor():
    pass


@fast.agent(
    name="conversation_analyzer", 
    model=DEFAULT_MODEL,
    instruction="""You are a conversation flow analyzer that identifies the structure and key elements of meeting discussions.

ANALYSIS TASKS:
1. **Identify Main Topics**: What were the 3-5 main topics discussed?
2. **Track Decision Points**: Where were decisions made and by whom?
3. **Extract Commitments**: Who committed to what and when?
4. **Identify Unresolved Issues**: What questions or problems remain open?
5. **Map Participant Roles**: Who were the main contributors for each topic?

OUTPUT FORMAT:
Return a structured analysis that can be used by the meeting_processor to create comprehensive meeting summaries.

Focus on factual extraction rather than interpretation - let the content speak for itself.
"""
)
def conversation_analyzer():
    pass


def segment_meeting_by_topics(content: str) -> List[str]:
    """
    Segment meeting content by conversational topics.
    Returns list of formatted segments ready for processing.
    """
    segmenter = ConversationalSegmenter()
    
    try:
        segments = segmenter.segment_by_conversation_topics(content)
        
        # Convert to simple string format expected by fast-agent
        segment_texts = []
        for i, segment in enumerate(segments, 1):
            # Add metadata to help the agent understand the context
            metadata = f"""[MEETING SEGMENT {i}]
TOPIC: {segment.topic}
PARTICIPANTS: {', '.join(segment.participants)}
TIMESPAN: {segment.start_time or 'N/A'} - {segment.end_time or 'N/A'}
DECISIONS DETECTED: {len(segment.decisions)}
ACTION ITEMS DETECTED: {len(segment.action_items)}

---CONTENT---
{segment.content}
---END SEGMENT---"""
            segment_texts.append(metadata)
        
        # Verification info
        total_words = len(content.split())
        segment_words = sum(len(seg.content.split()) for seg in segments)
        retention_rate = (segment_words / total_words) * 100 if total_words > 0 else 0
        
        print(f"🔍 Meeting Segmentation: {total_words} → {segment_words} words ({retention_rate:.1f}% retention)")
        print(f"📊 Created {len(segments)} conversational segments")
        
        return segment_texts
        
    except Exception as e:
        print(f"⚠️ Meeting segmenter failed: {e}")
        # Fallback to simple paragraph splitting
        paragraphs = content.split('\n\n')
        segments = []
        current_segment = []
        current_word_count = 0
        
        for para in paragraphs:
            para_words = len(para.split())
            if current_word_count + para_words > 1200 and current_segment:
                segments.append('\n\n'.join(current_segment))
                current_segment = [para]
                current_word_count = para_words
            else:
                current_segment.append(para)
                current_word_count += para_words
        
        if current_segment:
            segments.append('\n\n'.join(current_segment))
        
        # Format for fast-agent
        formatted_segments = []
        for i, seg in enumerate(segments, 1):
            formatted_segments.append(f"[MEETING SEGMENT {i}]\n{seg}\n---END SEGMENT---")
        
        return formatted_segments


# Export key functions
__all__ = [
    "fast",
    "segment_meeting_by_topics", 
    "ConversationalSegmenter",
    "MeetingStructure",
    "ConversationalSegment"
]