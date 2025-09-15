"""
Intelligent Segmenter - Content-Based Smart Segmentation
=======================================================

Uses semantic analysis to divide content into optimal sections for distributed processing.
Fast-agent handles the LLM communication, this focuses on the segmentation logic.
"""

from typing import List, Dict, Any, Tuple
import re
import nltk
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from dataclasses import dataclass
import tiktoken


@dataclass
class ContentSegment:
    """Represents a content segment with metadata."""
    content: str
    segment_id: int
    topic_indicators: List[str]
    word_count: int
    estimated_tokens: int
    complexity_score: float
    section_type: str  # 'intro', 'main', 'conclusion', 'transition'


class IntelligentSegmenter:
    """
    Content-first segmentation that creates optimal chunks based on semantic structure.
    Designed to work with fast-agent's distributed processing capabilities.
    """
    
    def __init__(self, target_segment_size: int = 1000, max_segments: int = 16):
        """
        Initialize the segmenter.
        
        Args:
            target_segment_size: Target word count per segment
            max_segments: Maximum number of segments to create
        """
        self.target_segment_size = target_segment_size
        self.max_segments = max_segments
        self.sentence_model = None
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
    
    def _lazy_load_sentence_model(self):
        """Lazy load sentence transformer to avoid startup delay."""
        if self.sentence_model is None:
            print("🔄 Loading sentence transformer model...")
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Model loaded")
    
    def analyze_content_structure(self, text: str) -> Dict[str, Any]:
        """Analyze the overall structure and characteristics of the content."""
        
        # Basic statistics
        sentences = nltk.sent_tokenize(text)
        words = text.split()
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Detect topic transition indicators
        transition_patterns = [
            r'\b(?:entonces|ahora|luego|después|por otro lado|además|finalmente)\b',
            r'\b(?:cambiando de tema|pasemos a|vamos a hablar|otro punto)\b',
            r'\b(?:en cuanto a|respecto a|en relación a)\b'
        ]
        
        transitions = []
        for i, sentence in enumerate(sentences):
            for pattern in transition_patterns:
                if re.search(pattern, sentence.lower()):
                    transitions.append({
                        'sentence_idx': i,
                        'sentence': sentence,
                        'pattern': pattern
                    })
        
        return {
            'total_words': len(words),
            'total_sentences': len(sentences),
            'total_paragraphs': len(paragraphs),
            'estimated_tokens': len(self.encoding.encode(text)),
            'transitions': transitions,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'complexity_indicators': self._detect_complexity(text)
        }
    
    def _detect_complexity(self, text: str) -> Dict[str, Any]:
        """Detect complexity indicators in the text."""
        
        # Technical terms (simplified detection)
        technical_patterns = [
            r'\b(?:algoritm[oa]s?|machine learning|deep learning|neural networks?)\b',
            r'\b(?:inteligencia artificial|procesamiento|análisis)\b',
            r'\b(?:modelo[s]?|función|variable[s]?|datos)\b'
        ]
        
        technical_count = 0
        for pattern in technical_patterns:
            technical_count += len(re.findall(pattern, text.lower()))
        
        # Calculate complexity score (0-1)
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        complexity_score = min(1.0, (technical_count * 0.1 + avg_word_length / 20))
        
        return {
            'technical_terms': technical_count,
            'avg_word_length': avg_word_length,
            'complexity_score': complexity_score
        }
    
    def create_semantic_segments(self, text: str) -> List[ContentSegment]:
        """
        Create content segments based on semantic analysis and structure.
        This is the main segmentation logic.
        """
        
        print("🔍 Analyzing content structure...")
        structure = self.analyze_content_structure(text)
        
        print(f"📊 Content analysis:")
        print(f"   • Total words: {structure['total_words']:,}")
        print(f"   • Estimated tokens: {structure['estimated_tokens']:,}")
        print(f"   • Topic transitions found: {len(structure['transitions'])}")
        print(f"   • Complexity score: {structure['complexity_indicators']['complexity_score']:.2f}")
        
        # If content is small, return as single segment
        if structure['total_words'] <= self.target_segment_size:
            return [ContentSegment(
                content=text,
                segment_id=1,
                topic_indicators=['complete_document'],
                word_count=structure['total_words'],
                estimated_tokens=structure['estimated_tokens'],
                complexity_score=structure['complexity_indicators']['complexity_score'],
                section_type='complete'
            )]
        
        # Split by natural transitions first
        if structure['transitions']:
            segments = self._split_by_transitions(text, structure)
        else:
            segments = self._split_by_semantic_similarity(text, structure)
        
        # Balance segment sizes
        segments = self._balance_segment_sizes(segments)
        
        print(f"✅ Created {len(segments)} segments")
        for i, segment in enumerate(segments, 1):
            print(f"   Segment {i}: {segment.word_count} words, type: {segment.section_type}")
        
        return segments
    
    def _split_by_transitions(self, text: str, structure: Dict[str, Any]) -> List[ContentSegment]:
        """Split text using detected topic transitions."""
        
        sentences = nltk.sent_tokenize(text)
        transitions = structure['transitions']
        
        # Create split points
        split_points = [0]  # Start
        for transition in transitions:
            split_points.append(transition['sentence_idx'])
        split_points.append(len(sentences))  # End
        
        # Remove duplicates and sort
        split_points = sorted(list(set(split_points)))
        
        segments = []
        for i in range(len(split_points) - 1):
            start_idx = split_points[i]
            end_idx = split_points[i + 1]
            
            segment_sentences = sentences[start_idx:end_idx]
            segment_text = ' '.join(segment_sentences)
            
            if segment_text.strip():
                # Extract topic indicators from the segment
                topic_indicators = self._extract_topics(segment_text)
                
                segments.append(ContentSegment(
                    content=segment_text.strip(),
                    segment_id=len(segments) + 1,
                    topic_indicators=topic_indicators,
                    word_count=len(segment_text.split()),
                    estimated_tokens=len(self.encoding.encode(segment_text)),
                    complexity_score=structure['complexity_indicators']['complexity_score'],
                    section_type='main'
                ))
        
        return segments
    
    def _split_by_semantic_similarity(self, text: str, structure: Dict[str, Any]) -> List[ContentSegment]:
        """Split text using semantic similarity clustering."""
        
        self._lazy_load_sentence_model()
        
        sentences = nltk.sent_tokenize(text)
        if len(sentences) < 4:
            # Too few sentences for clustering
            return [ContentSegment(
                content=text,
                segment_id=1,
                topic_indicators=['unified_topic'],
                word_count=structure['total_words'],
                estimated_tokens=structure['estimated_tokens'],
                complexity_score=structure['complexity_indicators']['complexity_score'],
                section_type='complete'
            )]
        
        # Get sentence embeddings
        print("🧠 Computing semantic embeddings...")
        embeddings = self.sentence_model.encode(sentences)
        
        # Determine optimal number of clusters
        max_clusters = min(self.max_segments, max(2, len(sentences) // 3))
        n_clusters = min(max_clusters, max(2, structure['total_words'] // self.target_segment_size))
        
        print(f"🎯 Creating {n_clusters} semantic clusters...")
        
        # Cluster sentences
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Group sentences by cluster
        clusters = {}
        for i, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append((i, sentences[i]))
        
        # Create segments from clusters (maintain order)
        segments = []
        for cluster_id in sorted(clusters.keys()):
            cluster_sentences = sorted(clusters[cluster_id], key=lambda x: x[0])
            segment_text = ' '.join([sent[1] for sent in cluster_sentences])
            
            topic_indicators = self._extract_topics(segment_text)
            
            segments.append(ContentSegment(
                content=segment_text,
                segment_id=len(segments) + 1,
                topic_indicators=topic_indicators,
                word_count=len(segment_text.split()),
                estimated_tokens=len(self.encoding.encode(segment_text)),
                complexity_score=structure['complexity_indicators']['complexity_score'],
                section_type='main'
            ))
        
        return segments
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topic indicators from a text segment."""
        
        # Simple keyword extraction based on frequency and technical terms
        technical_terms = re.findall(
            r'\b(?:machine learning|deep learning|neural networks?|algoritm[oa]s?|'
            r'inteligencia artificial|procesamiento|análisis|modelo[s]?)\b',
            text.lower()
        )
        
        # Also look for proper nouns and important concepts
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Combine and deduplicate
        topics = list(set(technical_terms + [noun.lower() for noun in proper_nouns]))
        
        return topics[:5]  # Limit to top 5
    
    def _balance_segment_sizes(self, segments: List[ContentSegment]) -> List[ContentSegment]:
        """Balance segment sizes to avoid very small or very large segments."""
        
        if not segments:
            return segments
        
        balanced = []
        
        for segment in segments:
            # If segment is too small, try to merge with previous
            if (segment.word_count < self.target_segment_size * 0.3 and 
                balanced and 
                balanced[-1].word_count < self.target_segment_size * 1.5):
                
                # Merge with previous segment
                prev = balanced[-1]
                merged = ContentSegment(
                    content=prev.content + "\n\n" + segment.content,
                    segment_id=prev.segment_id,
                    topic_indicators=list(set(prev.topic_indicators + segment.topic_indicators)),
                    word_count=prev.word_count + segment.word_count,
                    estimated_tokens=prev.estimated_tokens + segment.estimated_tokens,
                    complexity_score=(prev.complexity_score + segment.complexity_score) / 2,
                    section_type='merged'
                )
                balanced[-1] = merged
                
            # If segment is too large, split it
            elif segment.word_count > self.target_segment_size * 2:
                sub_segments = self._split_large_segment(segment)
                balanced.extend(sub_segments)
            else:
                balanced.append(segment)
        
        # Renumber segments
        for i, segment in enumerate(balanced, 1):
            segment.segment_id = i
        
        return balanced
    
    def _split_large_segment(self, segment: ContentSegment) -> List[ContentSegment]:
        """Split a segment that's too large."""
        
        sentences = nltk.sent_tokenize(segment.content)
        if len(sentences) <= 2:
            return [segment]  # Can't split further
        
        # Split roughly in half
        mid_point = len(sentences) // 2
        
        first_half = ' '.join(sentences[:mid_point])
        second_half = ' '.join(sentences[mid_point:])
        
        return [
            ContentSegment(
                content=first_half,
                segment_id=segment.segment_id,
                topic_indicators=segment.topic_indicators,
                word_count=len(first_half.split()),
                estimated_tokens=len(self.encoding.encode(first_half)),
                complexity_score=segment.complexity_score,
                section_type='split_part'
            ),
            ContentSegment(
                content=second_half,
                segment_id=segment.segment_id + 1,
                topic_indicators=segment.topic_indicators,
                word_count=len(second_half.split()),
                estimated_tokens=len(self.encoding.encode(second_half)),
                complexity_score=segment.complexity_score,
                section_type='split_part'
            )
        ]
    
    def generate_segment_summaries(self, segments: List[ContentSegment]) -> Dict[str, Any]:
        """Generate summaries and metadata for the segmentation."""
        
        total_words = sum(seg.word_count for seg in segments)
        total_tokens = sum(seg.estimated_tokens for seg in segments)
        
        return {
            'total_segments': len(segments),
            'total_words': total_words,
            'total_tokens': total_tokens,
            'avg_segment_size': total_words // len(segments) if segments else 0,
            'segments_metadata': [
                {
                    'id': seg.segment_id,
                    'words': seg.word_count,
                    'tokens': seg.estimated_tokens,
                    'topics': seg.topic_indicators,
                    'type': seg.section_type
                }
                for seg in segments
            ]
        }


# Test function
async def test_segmenter():
    """Test the segmenter with sample content."""
    
    sample_text = """
    Bueno, entonces vamos a hablar sobre machine learning que es básicamente un conjunto de algoritmos que aprenden de los datos. Estos algoritmos pueden identificar patrones y hacer predicciones sobre nuevos datos. Hay diferentes tipos de machine learning como el aprendizaje supervisado donde tenemos datos etiquetados y el modelo aprende a mapear entradas a salidas.
    
    También está el aprendizaje no supervisado donde el modelo encuentra patrones ocultos en datos sin etiquetas. Entonces ahora cambiando de tema vamos a hablar sobre redes neuronales que son un tipo específico de modelo de machine learning inspirado en el cerebro humano.
    
    Están compuestas por neuronas artificiales organizadas en capas. Cada neurona recibe entradas las procesa y produce una salida. Las redes profundas o deep learning tienen muchas capas ocultas y pueden aprender representaciones muy complejas.
    
    Por otro lado el procesamiento de lenguaje natural es otra área importante que se enfoca en enseñar a las máquinas a entender y generar texto humano. Incluye tareas como traducción automática análisis de sentimientos reconocimiento de entidades nombradas y generación de texto.
    
    Finalmente quiero mencionar que todas estas tecnologías están relacionadas y se complementan entre sí. El futuro de la inteligencia artificial dependerá de la integración de estos diferentes enfoques.
    """
    
    segmenter = IntelligentSegmenter(target_segment_size=150)
    
    print("🧪 Testing Intelligent Segmenter...")
    segments = segmenter.create_semantic_segments(sample_text)
    
    print("\n📊 Segmentation Summary:")
    summary = segmenter.generate_segment_summaries(segments)
    print(f"   • Total segments: {summary['total_segments']}")
    print(f"   • Total words: {summary['total_words']}")
    print(f"   • Avg segment size: {summary['avg_segment_size']} words")
    
    print("\n📝 Segments Preview:")
    for i, segment in enumerate(segments, 1):
        preview = segment.content[:100] + "..." if len(segment.content) > 100 else segment.content
        print(f"   Segment {i} ({segment.word_count} words): {preview}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_segmenter())