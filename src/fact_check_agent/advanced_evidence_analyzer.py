"""
Advanced Evidence Analysis Engine with Ultra-Fast Processing
Addresses the 5.74s evidence analysis bottleneck through parallel processing and optimized algorithms
"""
import asyncio
import re
import time
import logging
from typing import List, Dict, Any, Set, Tuple, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import hashlib
from collections import defaultdict

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .claim_extractor import Claim
from .checkpoint_monitor import TimedCheckpoint
from .performance_cache import content_cache

logger = logging.getLogger(__name__)

@dataclass
class EvidenceMatch:
    """Optimized evidence match representation"""
    sentence: str
    relevance_score: float
    credibility_score: float
    match_type: str  # 'supporting', 'contradictory', 'neutral'
    source_info: Dict[str, Any]
    keywords_matched: List[str]
    semantic_similarity: float = 0.0

class AdvancedEvidenceAnalyzer:
    """Ultra-fast evidence analysis with semantic understanding and parallel processing"""
    
    def __init__(self):
        """Initialize advanced evidence analyzer"""
        
        # Lightweight sentence transformer for semantic analysis
        self.sentence_model = None
        self.model_loading = False
        
        # Thread pool for CPU-intensive operations
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Optimized keyword patterns
        self.supporting_patterns = [
            r'\b(?:according to|research shows|study found|data indicates|evidence suggests)\b',
            r'\b(?:confirmed|verified|proven|demonstrated|established)\b',
            r'\b(?:statistics show|reports indicate|found that|concluded that)\b',
            r'\b(?:documented|recorded|measured|observed|detected)\b'
        ]
        
        self.contradictory_patterns = [
            r'\b(?:however|but|although|despite|contrary to)\b',
            r'\b(?:not|no evidence|disproven|false|incorrect)\b',
            r'\b(?:disputed|refuted|contradicts|debunked|challenged)\b',
            r'\b(?:actually|in fact|rather than|instead of)\b'
        ]
        
        # Compiled regex patterns for speed
        self.supporting_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.supporting_patterns]
        self.contradictory_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.contradictory_patterns]
        
        # Performance settings
        self.max_sentences_per_source = 30  # Limit for speed
        self.min_sentence_length = 25
        self.max_sentence_length = 500
        self.semantic_threshold = 0.6  # Minimum semantic similarity
        
    def _load_sentence_model(self):
        """Lazy load sentence transformer model"""
        if self.sentence_model is None and not self.model_loading:
            self.model_loading = True
            try:
                # Use lightweight model for speed
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence transformer model for semantic analysis")
            except Exception as e:
                logger.warning(f"Failed to load sentence model: {str(e)}")
                self.sentence_model = None
            finally:
                self.model_loading = False
    
    async def analyze_evidence_ultra_fast(
        self, 
        claim: Claim, 
        sources: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Ultra-fast evidence analysis with parallel processing"""
        
        if not sources:
            return [], []
        
        # Checkpoint: Prepare analysis data
        with TimedCheckpoint("evidence_preparation", {"source_count": len(sources)}) as cp:
            analysis_data = self._prepare_analysis_data(claim, sources)
        
        # Checkpoint: Parallel evidence extraction
        with TimedCheckpoint("parallel_evidence_extraction", {"sources": len(sources)}) as cp:
            evidence_matches = await self._extract_evidence_parallel(analysis_data)
        
        # Checkpoint: Semantic analysis (optional, if model available)
        with TimedCheckpoint("semantic_analysis", {"matches": len(evidence_matches)}) as cp:
            if self.sentence_model:
                evidence_matches = await self._enhance_with_semantic_analysis(claim, evidence_matches)
        
        # Checkpoint: Final ranking and filtering
        with TimedCheckpoint("evidence_ranking", {"matches": len(evidence_matches)}) as cp:
            evidence, contradictions = self._rank_and_filter_evidence(evidence_matches)
        
        logger.debug(f"Advanced analysis: {len(evidence)} evidence, {len(contradictions)} contradictions")
        return evidence, contradictions
    
    def _prepare_analysis_data(self, claim: Claim, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare optimized data structures for analysis"""
        
        # Extract claim keywords efficiently
        claim_keywords = set()
        
        if claim.keywords:
            claim_keywords.update([kw.lower().strip() for kw in claim.keywords[:5]])
        
        # Add entity text
        for entity in claim.entities[:3]:
            if entity.get('text'):
                text = entity['text'].lower().strip()
                if len(text) > 2:
                    claim_keywords.add(text)
        
        # Extract key terms from claim text
        claim_words = []
        for word in claim.text.split():
            word = word.lower().strip('.,!?()[]{}";:')
            if len(word) > 3 and word.isalpha():
                claim_words.append(word)
        
        claim_keywords.update(claim_words[:10])  # Limit for performance
        
        # Prepare source content
        source_data = []
        for source in sources:
            content = source.get('content', '')
            if content and len(content) > 50:
                # Pre-process sentences
                sentences = self._extract_sentences_fast(content)
                
                source_info = {
                    'url': source.get('url', ''),
                    'title': source.get('title', ''),
                    'domain': source.get('domain', ''),
                    'credibility_score': source.get('credibility_score', 0.5)
                }
                
                source_data.append({
                    'sentences': sentences,
                    'source_info': source_info
                })
        
        return {
            'claim_text': claim.text.lower(),
            'claim_keywords': claim_keywords,
            'source_data': source_data,
            'claim_type': claim.claim_type.value
        }
    
    def _extract_sentences_fast(self, content: str) -> List[str]:
        """Fast sentence extraction with length filtering"""
        # Split on sentence boundaries
        sentences = re.split(r'[.!?]+', content)
        
        # Filter and clean sentences
        clean_sentences = []
        for sentence in sentences[:self.max_sentences_per_source]:
            sentence = sentence.strip()
            if (self.min_sentence_length <= len(sentence) <= self.max_sentence_length and
                not sentence.startswith('http') and
                not sentence.startswith('www.')):
                clean_sentences.append(sentence)
        
        return clean_sentences
    
    async def _extract_evidence_parallel(self, analysis_data: Dict[str, Any]) -> List[EvidenceMatch]:
        """Extract evidence using parallel processing"""
        
        # Create analysis tasks for each source
        tasks = []
        for source_data in analysis_data['source_data']:
            task = self._analyze_source_sentences(
                analysis_data['claim_text'],
                analysis_data['claim_keywords'],
                source_data['sentences'],
                source_data['source_info']
            )
            tasks.append(task)
        
        # Execute all analyses in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        all_matches = []
        for result in results:
            if isinstance(result, list):
                all_matches.extend(result)
            elif isinstance(result, Exception):
                logger.debug(f"Evidence analysis task failed: {str(result)}")
        
        return all_matches
    
    async def _analyze_source_sentences(
        self,
        claim_text: str,
        claim_keywords: Set[str],
        sentences: List[str],
        source_info: Dict[str, Any]
    ) -> List[EvidenceMatch]:
        """Analyze sentences from a single source"""
        
        def _sync_analysis():
            matches = []
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                
                # Fast keyword matching
                keywords_matched = []
                for keyword in claim_keywords:
                    if keyword in sentence_lower:
                        keywords_matched.append(keyword)
                
                if len(keywords_matched) == 0:
                    continue
                
                # Calculate relevance score
                relevance_score = len(keywords_matched) / max(len(claim_keywords), 1)
                
                # Pattern matching for evidence type
                match_type = 'neutral'
                
                # Check for supporting patterns
                supporting_matches = sum(1 for pattern in self.supporting_regex 
                                       if pattern.search(sentence))
                
                # Check for contradictory patterns
                contradictory_matches = sum(1 for pattern in self.contradictory_regex 
                                          if pattern.search(sentence))
                
                # Determine match type
                if supporting_matches > 0 and len(keywords_matched) >= 1:
                    match_type = 'supporting'
                    relevance_score += 0.3  # Boost for supporting language
                elif contradictory_matches > 0 and len(keywords_matched) >= 1:
                    match_type = 'contradictory'
                    relevance_score += 0.2  # Boost for contradictory language
                
                # Only include matches with sufficient relevance
                if relevance_score > 0.2:
                    match = EvidenceMatch(
                        sentence=sentence,
                        relevance_score=min(1.0, relevance_score),
                        credibility_score=source_info['credibility_score'],
                        match_type=match_type,
                        source_info=source_info,
                        keywords_matched=keywords_matched
                    )
                    matches.append(match)
            
            return matches
        
        # Execute in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, _sync_analysis)
    
    async def _enhance_with_semantic_analysis(
        self, 
        claim: Claim, 
        evidence_matches: List[EvidenceMatch]
    ) -> List[EvidenceMatch]:
        """Enhance evidence matches with semantic similarity analysis"""
        
        if not self.sentence_model or len(evidence_matches) == 0:
            return evidence_matches
        
        try:
            def _semantic_analysis():
                # Encode claim text
                claim_embedding = self.sentence_model.encode([claim.text])
                
                # Encode evidence sentences
                sentences = [match.sentence for match in evidence_matches]
                sentence_embeddings = self.sentence_model.encode(sentences)
                
                # Calculate similarities
                similarities = cosine_similarity(claim_embedding, sentence_embeddings)[0]
                
                # Update matches with semantic scores
                for i, match in enumerate(evidence_matches):
                    match.semantic_similarity = float(similarities[i])
                    
                    # Boost relevance for high semantic similarity
                    if match.semantic_similarity > self.semantic_threshold:
                        match.relevance_score = min(1.0, match.relevance_score + 0.2)
                
                return evidence_matches
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.thread_pool, _semantic_analysis)
            
        except Exception as e:
            logger.debug(f"Semantic analysis failed: {str(e)}")
            return evidence_matches
    
    def _rank_and_filter_evidence(
        self, 
        evidence_matches: List[EvidenceMatch]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Rank and filter evidence matches into supporting and contradictory"""
        
        supporting = []
        contradictory = []
        
        # Separate by match type
        for match in evidence_matches:
            if match.match_type == 'supporting':
                supporting.append(match)
            elif match.match_type == 'contradictory':
                contradictory.append(match)
        
        # Sort by combined score (relevance * credibility + semantic)
        def calculate_score(match):
            base_score = match.relevance_score * match.credibility_score
            semantic_boost = match.semantic_similarity * 0.1
            return base_score + semantic_boost
        
        supporting.sort(key=calculate_score, reverse=True)
        contradictory.sort(key=calculate_score, reverse=True)
        
        # Convert to output format and limit results
        supporting_evidence = []
        for match in supporting[:10]:  # Top 10 supporting
            supporting_evidence.append({
                'sentence': match.sentence,
                'source_url': match.source_info['url'],
                'source_title': match.source_info['title'],
                'source_domain': match.source_info['domain'],
                'source_credibility': match.credibility_score,
                'relevance_score': match.relevance_score,
                'semantic_similarity': match.semantic_similarity,
                'keywords_matched': len(match.keywords_matched),
                'type': 'supporting'
            })
        
        contradictory_evidence = []
        for match in contradictory[:5]:  # Top 5 contradictory
            contradictory_evidence.append({
                'sentence': match.sentence,
                'source_url': match.source_info['url'],
                'source_title': match.source_info['title'],
                'source_domain': match.source_info['domain'],
                'source_credibility': match.credibility_score,
                'relevance_score': match.relevance_score,
                'semantic_similarity': match.semantic_similarity,
                'keywords_matched': len(match.keywords_matched),
                'type': 'contradictory'
            })
        
        return supporting_evidence, contradictory_evidence
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get analyzer performance statistics"""
        return {
            'model_loaded': self.sentence_model is not None,
            'max_sentences_per_source': self.max_sentences_per_source,
            'min_sentence_length': self.min_sentence_length,
            'semantic_threshold': self.semantic_threshold,
            'supporting_patterns': len(self.supporting_patterns),
            'contradictory_patterns': len(self.contradictory_patterns),
            'thread_pool_workers': self.thread_pool._max_workers
        }

# Global instance
advanced_evidence_analyzer = AdvancedEvidenceAnalyzer()