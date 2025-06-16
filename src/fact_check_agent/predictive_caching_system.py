"""
Predictive Caching System with ML-Based Pre-caching
Implements intelligent caching that predicts and pre-fetches likely needed content
"""
import asyncio
import time
import logging
from typing import Dict, List, Any, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import hashlib
import json
import threading

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

from .performance_cache import HighPerformanceCache
from .claim_extractor import ClaimType

logger = logging.getLogger(__name__)

@dataclass
class CacheAccessPattern:
    """Tracks cache access patterns for prediction"""
    key: str
    access_times: List[float]
    claim_types: List[str]
    keywords: List[str]
    frequency: int
    last_access: float
    prediction_score: float = 0.0

@dataclass
class TrendingTopic:
    """Represents a trending topic for predictive caching"""
    keywords: List[str]
    claim_types: List[str]
    confidence: float
    predicted_queries: List[str]
    cache_priority: int  # 1 (highest) to 5 (lowest)

class PredictiveCachingSystem:
    """Advanced caching system with ML-based prediction and pre-fetching"""
    
    def __init__(self):
        """Initialize predictive caching system"""
        
        # Enhanced cache instances
        self.search_cache = HighPerformanceCache(max_size=1000, default_ttl=3600)
        self.content_cache = HighPerformanceCache(max_size=2000, default_ttl=7200)
        self.prediction_cache = HighPerformanceCache(max_size=500, default_ttl=1800)
        
        # Pattern tracking
        self.access_patterns: Dict[str, CacheAccessPattern] = {}
        self.trending_topics: List[TrendingTopic] = []
        
        # ML components
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.topic_clusters = None
        self.last_model_update = 0
        
        # Threading for background tasks
        self.prediction_lock = threading.RLock()
        self.background_tasks_running = False
        
        # Performance settings
        self.min_pattern_observations = 3
        self.prediction_window_hours = 24
        self.model_update_interval = 3600  # 1 hour
        self.max_trending_topics = 20
        
        # Claim type weightings for prediction
        self.claim_type_weights = {
            'medical': 1.3,      # Higher weight for medical claims (often searched repeatedly)
            'scientific': 1.2,   # Scientific claims often have follow-up searches
            'financial': 1.1,    # Financial claims during market hours
            'political': 1.4,    # Political claims trend heavily
            'statistical': 1.0,  # Baseline
            'general': 0.9       # Lower weight for general claims
        }
        
        # Domain popularity for prediction
        self.high_value_domains = {
            'reuters.com': 2.0,
            'apnews.com': 2.0,
            'who.int': 1.8,
            'cdc.gov': 1.8,
            'bbc.com': 1.7,
            'nature.com': 1.6,
            'science.org': 1.6
        }
    
    def track_access(self, cache_key: str, claim_type: str, keywords: List[str]) -> None:
        """Track cache access for pattern learning"""
        with self.prediction_lock:
            current_time = time.time()
            
            if cache_key in self.access_patterns:
                pattern = self.access_patterns[cache_key]
                pattern.access_times.append(current_time)
                pattern.claim_types.append(claim_type)
                pattern.keywords.extend(keywords)
                pattern.frequency += 1
                pattern.last_access = current_time
                
                # Limit history size
                if len(pattern.access_times) > 20:
                    pattern.access_times = pattern.access_times[-20:]
                    pattern.claim_types = pattern.claim_types[-20:]
                    pattern.keywords = pattern.keywords[-50:]
            else:
                pattern = CacheAccessPattern(
                    key=cache_key,
                    access_times=[current_time],
                    claim_types=[claim_type],
                    keywords=keywords.copy(),
                    frequency=1,
                    last_access=current_time
                )
                self.access_patterns[cache_key] = pattern
    
    async def get_with_prediction(
        self, 
        cache_key: str, 
        cache_instance: HighPerformanceCache,
        claim_type: str = "general",
        keywords: List[str] = None
    ) -> Optional[Any]:
        """Get from cache and track access for prediction"""
        if keywords is None:
            keywords = []
        
        # Track the access
        self.track_access(cache_key, claim_type, keywords)
        
        # Get from cache
        result = cache_instance.get(cache_key)
        
        # Trigger background prediction update if needed
        if not self.background_tasks_running:
            asyncio.create_task(self._background_prediction_update())
        
        return result
    
    async def set_with_prediction(
        self,
        cache_key: str,
        value: Any,
        cache_instance: HighPerformanceCache,
        claim_type: str = "general",
        keywords: List[str] = None,
        ttl: Optional[float] = None
    ) -> None:
        """Set cache value and update prediction models"""
        if keywords is None:
            keywords = []
        
        # Set in cache
        cache_instance.set(cache_key, value, ttl)
        
        # Track the access
        self.track_access(cache_key, claim_type, keywords)
    
    async def _background_prediction_update(self) -> None:
        """Background task to update prediction models and pre-cache content"""
        if self.background_tasks_running:
            return
        
        self.background_tasks_running = True
        
        try:
            current_time = time.time()
            
            # Update models if enough time has passed
            if current_time - self.last_model_update > self.model_update_interval:
                await self._update_prediction_models()
                self.last_model_update = current_time
            
            # Identify trending topics
            await self._identify_trending_topics()
            
            # Pre-cache predicted content
            await self._execute_predictive_caching()
            
        except Exception as e:
            logger.error(f"Background prediction update failed: {str(e)}")
        finally:
            self.background_tasks_running = False
    
    async def _update_prediction_models(self) -> None:
        """Update ML models for prediction"""
        with self.prediction_lock:
            try:
                # Prepare training data from access patterns
                patterns = [p for p in self.access_patterns.values() 
                          if p.frequency >= self.min_pattern_observations]
                
                if len(patterns) < 10:  # Need minimum data
                    return
                
                # Create feature vectors from keywords
                all_keywords = []
                for pattern in patterns:
                    keyword_text = ' '.join(pattern.keywords[-10:])  # Recent keywords
                    all_keywords.append(keyword_text)
                
                if all_keywords:
                    # Fit vectorizer
                    X = self.vectorizer.fit_transform(all_keywords)
                    
                    # Cluster similar patterns
                    n_clusters = min(10, len(patterns) // 2)
                    if n_clusters >= 2:
                        self.topic_clusters = KMeans(n_clusters=n_clusters, random_state=42)
                        self.topic_clusters.fit(X)
                        
                        logger.info(f"Updated prediction models with {len(patterns)} patterns, {n_clusters} clusters")
                
            except Exception as e:
                logger.error(f"Model update failed: {str(e)}")
    
    async def _identify_trending_topics(self) -> None:
        """Identify trending topics from recent access patterns"""
        with self.prediction_lock:
            current_time = time.time()
            cutoff_time = current_time - (self.prediction_window_hours * 3600)
            
            # Analyze recent access patterns
            recent_keywords = Counter()
            recent_claim_types = Counter()
            
            for pattern in self.access_patterns.values():
                # Only consider recent accesses
                recent_accesses = [t for t in pattern.access_times if t > cutoff_time]
                
                if recent_accesses:
                    # Weight by frequency and recency
                    weight = len(recent_accesses) * (pattern.last_access - cutoff_time) / (self.prediction_window_hours * 3600)
                    
                    # Count keywords
                    for keyword in pattern.keywords[-10:]:  # Recent keywords
                        recent_keywords[keyword.lower()] += weight
                    
                    # Count claim types
                    for claim_type in pattern.claim_types[-5:]:  # Recent claim types
                        recent_claim_types[claim_type] += weight
            
            # Identify trending topics
            trending_topics = []
            
            # Get top keywords
            top_keywords = [kw for kw, count in recent_keywords.most_common(50) if count > 1.0]
            
            if top_keywords:
                # Group keywords into topics
                keyword_groups = self._group_related_keywords(top_keywords)
                
                for group in keyword_groups:
                    # Determine most likely claim types for this topic
                    topic_claim_types = [ct for ct, count in recent_claim_types.most_common(3)]
                    
                    # Calculate confidence based on frequency and diversity
                    total_weight = sum(recent_keywords[kw] for kw in group)
                    confidence = min(1.0, total_weight / 10.0)
                    
                    # Generate predicted queries
                    predicted_queries = self._generate_predicted_queries(group, topic_claim_types)
                    
                    # Determine cache priority
                    priority = self._calculate_cache_priority(group, topic_claim_types, confidence)
                    
                    topic = TrendingTopic(
                        keywords=group,
                        claim_types=topic_claim_types,
                        confidence=confidence,
                        predicted_queries=predicted_queries,
                        cache_priority=priority
                    )
                    
                    trending_topics.append(topic)
            
            # Sort by confidence and limit
            trending_topics.sort(key=lambda t: t.confidence, reverse=True)
            self.trending_topics = trending_topics[:self.max_trending_topics]
            
            logger.info(f"Identified {len(self.trending_topics)} trending topics")
    
    def _group_related_keywords(self, keywords: List[str]) -> List[List[str]]:
        """Group related keywords using semantic similarity"""
        if not self.vectorizer or len(keywords) < 2:
            return [[kw] for kw in keywords]
        
        try:
            # Vectorize keywords
            X = self.vectorizer.transform(keywords)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(X)
            
            # Simple clustering based on similarity
            groups = []
            used = set()
            
            for i, keyword in enumerate(keywords):
                if keyword in used:
                    continue
                
                group = [keyword]
                used.add(keyword)
                
                # Find similar keywords
                for j, other_keyword in enumerate(keywords):
                    if (other_keyword not in used and 
                        similarity_matrix[i][j] > 0.3):  # Similarity threshold
                        group.append(other_keyword)
                        used.add(other_keyword)
                
                groups.append(group)
            
            return groups
            
        except Exception as e:
            logger.debug(f"Keyword grouping failed: {str(e)}")
            return [[kw] for kw in keywords]
    
    def _generate_predicted_queries(self, keywords: List[str], claim_types: List[str]) -> List[str]:
        """Generate predicted search queries for a topic"""
        queries = []
        
        # Basic query combinations
        main_keywords = keywords[:3]  # Top 3 keywords
        
        for claim_type in claim_types[:2]:  # Top 2 claim types
            # Fact-check query
            query = f"fact check {' '.join(main_keywords[:2])} {claim_type}"
            queries.append(query)
            
            # Direct search query
            if len(main_keywords) >= 2:
                query = f"{main_keywords[0]} {main_keywords[1]} {claim_type}"
                queries.append(query)
        
        # General queries
        if len(main_keywords) >= 2:
            queries.append(' '.join(main_keywords[:3]))
        
        return queries[:5]  # Limit to 5 predicted queries
    
    def _calculate_cache_priority(
        self, 
        keywords: List[str], 
        claim_types: List[str], 
        confidence: float
    ) -> int:
        """Calculate cache priority (1=highest, 5=lowest)"""
        
        base_priority = 3  # Default medium priority
        
        # Adjust based on claim type weights
        if claim_types:
            claim_type_weight = self.claim_type_weights.get(claim_types[0], 1.0)
            if claim_type_weight > 1.2:
                base_priority -= 1  # Higher priority
            elif claim_type_weight < 1.0:
                base_priority += 1  # Lower priority
        
        # Adjust based on confidence
        if confidence > 0.7:
            base_priority -= 1
        elif confidence < 0.3:
            base_priority += 1
        
        # Keep in valid range
        return max(1, min(5, base_priority))
    
    async def _execute_predictive_caching(self) -> None:
        """Execute predictive caching based on trending topics"""
        if not self.trending_topics:
            return
        
        try:
            # Cache high-priority topics
            high_priority_topics = [t for t in self.trending_topics if t.cache_priority <= 2]
            
            for topic in high_priority_topics[:5]:  # Limit to top 5 for performance
                await self._pre_cache_topic(topic)
                
        except Exception as e:
            logger.error(f"Predictive caching execution failed: {str(e)}")
    
    async def _pre_cache_topic(self, topic: TrendingTopic) -> None:
        """Pre-cache content for a specific topic"""
        try:
            # Generate cache keys for predicted queries
            for query in topic.predicted_queries:
                for claim_type in topic.claim_types:
                    # Create cache key as the system would
                    cache_key = f"web_{claim_type}_{hashlib.md5(query.encode()).hexdigest()[:8]}"
                    
                    # Check if already cached
                    if not self.search_cache.get(cache_key):
                        # Mark for potential pre-caching
                        # In a real implementation, this would trigger a background search
                        logger.debug(f"Would pre-cache: {query} ({claim_type})")
                        
                        # Set a placeholder to prevent duplicate work
                        self.prediction_cache.set(f"precache_{cache_key}", True, ttl=300)
        
        except Exception as e:
            logger.debug(f"Pre-caching topic failed: {str(e)}")
    
    def get_trending_topics_summary(self) -> List[Dict[str, Any]]:
        """Get summary of current trending topics"""
        return [
            {
                'keywords': topic.keywords[:5],
                'claim_types': topic.claim_types[:3],
                'confidence': topic.confidence,
                'priority': topic.cache_priority,
                'predicted_queries': len(topic.predicted_queries)
            }
            for topic in self.trending_topics
        ]
    
    def get_prediction_stats(self) -> Dict[str, Any]:
        """Get comprehensive prediction system statistics"""
        with self.prediction_lock:
            patterns_count = len(self.access_patterns)
            recent_patterns = sum(1 for p in self.access_patterns.values() 
                                if time.time() - p.last_access < 3600)
            
            return {
                'total_patterns': patterns_count,
                'recent_patterns': recent_patterns,
                'trending_topics': len(self.trending_topics),
                'model_last_updated': datetime.fromtimestamp(self.last_model_update).isoformat(),
                'cache_stats': {
                    'search_cache': self.search_cache.stats(),
                    'content_cache': self.content_cache.stats(),
                    'prediction_cache': self.prediction_cache.stats()
                },
                'clustering_enabled': self.topic_clusters is not None,
                'vectorizer_features': self.vectorizer.get_feature_names_out().shape[0] if hasattr(self.vectorizer, 'vocabulary_') else 0
            }
    
    def clear_prediction_data(self) -> None:
        """Clear all prediction data and reset models"""
        with self.prediction_lock:
            self.access_patterns.clear()
            self.trending_topics.clear()
            self.topic_clusters = None
            self.last_model_update = 0
            
            # Clear caches
            self.search_cache.clear()
            self.content_cache.clear()
            self.prediction_cache.clear()
            
            logger.info("Cleared all prediction data")

# Global predictive caching system
predictive_cache = PredictiveCachingSystem()