"""
Intelligent Query Optimization with Claim-Type Specific Strategies
Reduces query execution time through smart query generation and optimization
"""
import re
import logging
from typing import List, Dict, Any, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import hashlib

from .claim_extractor import Claim, ClaimType

logger = logging.getLogger(__name__)

@dataclass
class OptimizedQuery:
    """Represents an optimized search query"""
    query: str
    priority: int  # 1 (highest) to 5 (lowest)
    query_type: str  # 'fact_check', 'source_specific', 'entity_based', 'general'
    expected_domains: List[str]
    confidence: float  # Expected relevance (0.0 to 1.0)

class IntelligentQueryOptimizer:
    """Advanced query optimization with claim-type specific strategies"""
    
    def __init__(self):
        """Initialize intelligent query optimizer"""
        
        # Claim-type specific optimization strategies
        self.claim_type_strategies = {
            ClaimType.MEDICAL: {
                'priority_sources': ['who.int', 'cdc.gov', 'nih.gov', 'mayoclinic.org', 'webmd.com'],
                'query_templates': [
                    'medical fact check {entity} {condition}',
                    'WHO CDC {entity} guidelines',
                    '{entity} medical research study',
                    'health {entity} clinical trial'
                ],
                'key_terms': ['study', 'research', 'clinical', 'trial', 'guideline', 'recommendation'],
                'avoid_terms': ['opinion', 'blog', 'personal'],
                'max_queries': 2
            },
            ClaimType.SCIENTIFIC: {
                'priority_sources': ['nature.com', 'science.org', 'ncbi.nlm.nih.gov', 'ieee.org'],
                'query_templates': [
                    'scientific study {entity} research',
                    'peer reviewed {entity} journal',
                    '{entity} academic paper',
                    'research {entity} findings'
                ],
                'key_terms': ['research', 'study', 'journal', 'peer-reviewed', 'academic'],
                'avoid_terms': ['opinion', 'blog', 'unverified'],
                'max_queries': 2
            },
            ClaimType.POLITICAL: {
                'priority_sources': ['reuters.com', 'apnews.com', 'factcheck.org', 'politifact.com'],
                'query_templates': [
                    'fact check {entity} political claim',
                    '{entity} voting record policy',
                    'political fact {entity} verification',
                    'government {entity} official statement'
                ],
                'key_terms': ['fact check', 'verification', 'official', 'statement'],
                'avoid_terms': ['opinion', 'editorial', 'partisan'],
                'max_queries': 3
            },
            ClaimType.FINANCIAL: {
                'priority_sources': ['reuters.com', 'sec.gov', 'federalreserve.gov'],
                'query_templates': [
                    '{entity} financial report SEC',
                    'stock market {entity} data',
                    '{entity} earnings financial',
                    'economic {entity} statistics'
                ],
                'key_terms': ['financial', 'earnings', 'SEC', 'report', 'data'],
                'avoid_terms': ['prediction', 'opinion', 'speculation'],
                'max_queries': 2
            },
            ClaimType.STATISTICAL: {
                'priority_sources': ['bls.gov', 'census.gov', 'who.int', 'worldbank.org'],
                'query_templates': [
                    '{entity} government statistics data',
                    'official {entity} census bureau',
                    '{entity} statistical report',
                    'government data {entity} official'
                ],
                'key_terms': ['statistics', 'data', 'official', 'government', 'census'],
                'avoid_terms': ['estimate', 'projection', 'opinion'],
                'max_queries': 2
            },
            ClaimType.TECHNOLOGY: {
                'priority_sources': ['ieee.org', 'techcrunch.com', 'arstechnica.com'],
                'query_templates': [
                    '{entity} technology research',
                    'tech {entity} development',
                    '{entity} innovation study',
                    'technology {entity} report'
                ],
                'key_terms': ['technology', 'research', 'development', 'innovation'],
                'avoid_terms': ['rumor', 'speculation', 'leak'],
                'max_queries': 2
            }
        }
        
        # Default strategy for general claims
        self.default_strategy = {
            'priority_sources': ['reuters.com', 'apnews.com', 'bbc.com', 'factcheck.org'],
            'query_templates': [
                'fact check {entity}',
                '{entity} news verification',
                '{entity} reliable source'
            ],
            'key_terms': ['fact', 'verify', 'source', 'news'],
            'avoid_terms': ['opinion', 'blog', 'rumor'],
            'max_queries': 2
        }
        
        # Entity type patterns for better extraction
        self.entity_patterns = {
            'person': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            'organization': r'\b[A-Z]{2,}|[A-Z][a-z]+ (?:Inc|Corp|LLC|Organization|Agency|Department)\b',
            'location': r'\b[A-Z][a-z]+ (?:City|State|Country|County)\b',
            'date': r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2},? \d{4}\b',
            'percentage': r'\b\d+(?:\.\d+)?%\b',
            'money': r'\$\d+(?:,\d{3})*(?:\.\d{2})?\b',
            'number': r'\b\d+(?:,\d{3})*(?:\.\d+)?\b'
        }
        
        # Query quality metrics
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'the', 'this', 'they', 'have', 'had'
        }
        
        # Performance settings
        self.max_total_queries = 3  # Global limit
        self.min_query_length = 10
        self.max_query_length = 100
    
    def optimize_queries(self, claim: Claim) -> List[OptimizedQuery]:
        """Generate optimized queries for a claim using intelligent strategies"""
        
        strategy = self.claim_type_strategies.get(claim.claim_type, self.default_strategy)
        
        # Extract key entities and terms
        entities = self._extract_key_entities(claim)
        key_terms = self._extract_key_terms(claim, strategy['key_terms'])
        
        # Generate optimized queries
        optimized_queries = []
        
        # 1. Generate template-based queries
        template_queries = self._generate_template_queries(claim, entities, strategy)
        optimized_queries.extend(template_queries)
        
        # 2. Generate entity-based queries
        entity_queries = self._generate_entity_queries(claim, entities, strategy)
        optimized_queries.extend(entity_queries)
        
        # 3. Generate fact-check specific queries
        fact_check_queries = self._generate_fact_check_queries(claim, entities, strategy)
        optimized_queries.extend(fact_check_queries)
        
        # 4. Rank and filter queries
        final_queries = self._rank_and_filter_queries(optimized_queries, strategy)
        
        logger.debug(f"Generated {len(final_queries)} optimized queries for {claim.claim_type.value} claim")
        
        return final_queries[:self.max_total_queries]
    
    def _extract_key_entities(self, claim: Claim) -> Dict[str, List[str]]:
        """Extract key entities from claim using patterns"""
        entities = defaultdict(list)
        
        # Use existing entities from claim
        for entity in claim.entities:
            entity_text = entity.get('text', '').strip()
            entity_label = entity.get('label', 'UNKNOWN').lower()
            
            if entity_text and len(entity_text) > 2:
                if entity_label in ['person', 'org', 'gpe']:
                    entities['named_entities'].append(entity_text)
                elif entity_label in ['date', 'time']:
                    entities['dates'].append(entity_text)
                elif entity_label in ['money', 'percent', 'cardinal']:
                    entities['numbers'].append(entity_text)
                else:
                    entities['general'].append(entity_text)
        
        # Extract additional entities using patterns
        text = claim.text
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                entities[entity_type].extend(matches)
        
        # Clean and deduplicate
        for entity_type in entities:
            entities[entity_type] = list(set(entities[entity_type]))[:3]  # Limit to top 3
        
        return dict(entities)
    
    def _extract_key_terms(self, claim: Claim, strategy_terms: List[str]) -> List[str]:
        """Extract key terms relevant to the claim type"""
        key_terms = []
        
        # Use claim keywords if available
        if claim.keywords:
            key_terms.extend(claim.keywords[:3])
        
        # Extract important words from claim text
        words = re.findall(r'\b[a-zA-Z]{3,}\b', claim.text.lower())
        important_words = [w for w in words if w not in self.stop_words and len(w) > 3]
        
        # Prioritize strategy-specific terms
        for term in strategy_terms:
            if term.lower() in claim.text.lower():
                key_terms.append(term)
        
        # Add other important words
        key_terms.extend(important_words[:5])
        
        return list(set(key_terms))[:5]  # Limit and deduplicate
    
    def _generate_template_queries(
        self, 
        claim: Claim, 
        entities: Dict[str, List[str]], 
        strategy: Dict[str, Any]
    ) -> List[OptimizedQuery]:
        """Generate queries using claim-type specific templates"""
        queries = []
        
        templates = strategy['query_templates']
        
        # Get primary entity for template substitution
        primary_entity = self._get_primary_entity(entities)
        
        for template in templates[:2]:  # Limit templates
            try:
                # Simple template substitution
                query = template.format(
                    entity=primary_entity,
                    condition=self._extract_condition(claim.text)
                )
                
                # Clean the query
                query = self._clean_query(query)
                
                if self._is_valid_query(query):
                    optimized_query = OptimizedQuery(
                        query=query,
                        priority=1,  # High priority for template queries
                        query_type='template_based',
                        expected_domains=strategy['priority_sources'],
                        confidence=0.8
                    )
                    queries.append(optimized_query)
                    
            except Exception as e:
                logger.debug(f"Template query generation failed: {str(e)}")
                continue
        
        return queries
    
    def _generate_entity_queries(
        self, 
        claim: Claim, 
        entities: Dict[str, List[str]], 
        strategy: Dict[str, Any]
    ) -> List[OptimizedQuery]:
        """Generate entity-focused queries"""
        queries = []
        
        # Focus on named entities
        named_entities = entities.get('named_entities', [])
        numbers = entities.get('numbers', [])
        
        if named_entities:
            primary_entity = named_entities[0]
            
            # Basic entity query
            query = f"{primary_entity} {claim.claim_type.value}"
            query = self._clean_query(query)
            
            if self._is_valid_query(query):
                optimized_query = OptimizedQuery(
                    query=query,
                    priority=2,
                    query_type='entity_based',
                    expected_domains=strategy['priority_sources'],
                    confidence=0.7
                )
                queries.append(optimized_query)
            
            # Entity with numbers (if available)
            if numbers:
                query = f"{primary_entity} {numbers[0]}"
                query = self._clean_query(query)
                
                if self._is_valid_query(query):
                    optimized_query = OptimizedQuery(
                        query=query,
                        priority=2,
                        query_type='entity_number',
                        expected_domains=strategy['priority_sources'],
                        confidence=0.75
                    )
                    queries.append(optimized_query)
        
        return queries
    
    def _generate_fact_check_queries(
        self, 
        claim: Claim, 
        entities: Dict[str, List[str]], 
        strategy: Dict[str, Any]
    ) -> List[OptimizedQuery]:
        """Generate fact-check specific queries"""
        queries = []
        
        primary_entity = self._get_primary_entity(entities)
        
        # Fact-check query
        query = f"fact check {primary_entity}"
        query = self._clean_query(query)
        
        if self._is_valid_query(query):
            optimized_query = OptimizedQuery(
                query=query,
                priority=1,  # High priority for fact-check queries
                query_type='fact_check',
                expected_domains=['factcheck.org', 'snopes.com', 'politifact.com'],
                confidence=0.9
            )
            queries.append(optimized_query)
        
        # Verification query
        query = f"{primary_entity} verification"
        query = self._clean_query(query)
        
        if self._is_valid_query(query):
            optimized_query = OptimizedQuery(
                query=query,
                priority=2,
                query_type='verification',
                expected_domains=strategy['priority_sources'],
                confidence=0.7
            )
            queries.append(optimized_query)
        
        return queries
    
    def _get_primary_entity(self, entities: Dict[str, List[str]]) -> str:
        """Get the most important entity for query generation"""
        
        # Priority order for entity types
        priority_types = ['named_entities', 'person', 'organization', 'general']
        
        for entity_type in priority_types:
            if entities.get(entity_type):
                return entities[entity_type][0]
        
        # Fallback to any available entity
        for entity_list in entities.values():
            if entity_list:
                return entity_list[0]
        
        return "information"  # Default fallback
    
    def _extract_condition(self, text: str) -> str:
        """Extract condition or context from claim text"""
        # Simple extraction of key descriptive terms
        descriptors = []
        
        # Look for adjectives and important terms
        pattern = r'\b(?:effective|safe|dangerous|beneficial|harmful|increased|decreased|new|old)\b'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        if matches:
            return matches[0]
        
        return "claim"  # Default fallback
    
    def _clean_query(self, query: str) -> str:
        """Clean and optimize query string"""
        # Remove extra spaces
        query = re.sub(r'\s+', ' ', query)
        
        # Remove special characters that might interfere with search
        query = re.sub(r'[^\w\s%$-]', '', query)
        
        # Truncate if too long
        if len(query) > self.max_query_length:
            query = query[:self.max_query_length].rsplit(' ', 1)[0]
        
        return query.strip()
    
    def _is_valid_query(self, query: str) -> bool:
        """Check if query is valid for search"""
        return (
            len(query) >= self.min_query_length and
            len(query) <= self.max_query_length and
            len(query.split()) >= 2 and
            not query.lower().startswith('http')
        )
    
    def _rank_and_filter_queries(
        self, 
        queries: List[OptimizedQuery], 
        strategy: Dict[str, Any]
    ) -> List[OptimizedQuery]:
        """Rank and filter queries based on quality and strategy"""
        
        # Remove duplicates
        seen_queries = set()
        unique_queries = []
        
        for query in queries:
            query_key = query.query.lower()
            if query_key not in seen_queries:
                seen_queries.add(query_key)
                unique_queries.append(query)
        
        # Sort by priority and confidence
        unique_queries.sort(key=lambda q: (q.priority, -q.confidence))
        
        # Apply strategy limits
        max_queries = strategy.get('max_queries', 2)
        
        return unique_queries[:max_queries]
    
    def get_query_optimization_stats(self) -> Dict[str, Any]:
        """Get query optimization statistics"""
        return {
            'supported_claim_types': list(self.claim_type_strategies.keys()),
            'max_total_queries': self.max_total_queries,
            'entity_patterns': len(self.entity_patterns),
            'stop_words': len(self.stop_words),
            'query_length_limits': {
                'min': self.min_query_length,
                'max': self.max_query_length
            }
        }

# Global query optimizer
query_optimizer = IntelligentQueryOptimizer()