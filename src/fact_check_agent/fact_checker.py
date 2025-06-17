"""
Ultra-optimized fact checker with comprehensive bottleneck fixes
Implements caching, concurrent processing, and smart source prioritization
"""
import asyncio
import aiohttp
import logging
import re
import json
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urljoin, urlparse
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from newspaper import Article
from serpapi import GoogleSearch
from tqdm.asyncio import tqdm
import random

from .config import config, FACT_CHECK_SOURCES
from .claim_extractor import Claim, ClaimType
from .checkpoint_monitor import TimedCheckpoint, start_checkpoint, end_checkpoint, add_claim_report
from .performance_cache import search_cache, content_cache, source_cache
from .enhanced_content_extractor import enhanced_extractor
from .search_services import unified_search_service, SearchResult as UnifiedSearchResult


# Backward compatibility imports
from .enhanced_content_extractor import enhanced_extractor
from .performance_cache import search_cache, content_cache, source_cache, get_cache_stats, clear_all_caches

# Ultra-optimization imports
from .ultra_optimized_fact_checker import UltraOptimizedFactChecker, ultra_fact_checker

logger = logging.getLogger(__name__)

@dataclass
class FactCheckResult:
    """Result of fact-checking a single claim"""
    claim: Claim
    verification_status: str  # 'verified', 'disputed', 'unverified', 'error'
    authenticity_score: float  # 0.0 to 1.0
    sources_checked: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    contradictions: List[Dict[str, Any]]
    processing_time: float
    cache_hits: int = 0
    error_message: Optional[str] = None

@dataclass
class Source:
    """Represents a fact-checking source"""
    url: str
    title: str
    content: str
    relevance_score: float
    credibility_score: float
    publication_date: Optional[datetime]
    domain: str

class FactChecker:
    """Ultra-optimized fact-checking engine with bottleneck fixes"""
    
    def __init__(self):
        """Initialize optimized fact checker"""
        
        # Enhanced user agent pool (25 agents for better rotation)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:119.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        # Ultra-aggressive performance optimizations
        self.max_urls = 8  # Reduced from 15 for maximum speed
        self.priority_sources_limit = 5  # Focus on top sources only
        self.delay_between_requests = 0.1  # Minimal delay
        self.timeout = 3  # Aggressive timeout
        self.max_retries = 0  # No retries for speed
        self.concurrent_limit = 12  # Increased concurrency
        self.max_search_queries = 2  # Reduced from 3 queries
        
        # Enhanced blocked domains (40+ domains to avoid 403 errors)
        self.blocked_domains = {
            # Financial paywalls
            'bloomberg.com', 'wsj.com', 'ft.com', 'economist.com',
            'marketwatch.com', 'barrons.com', 'bloomberg.co.uk',
            
            # News paywalls  
            'nytimes.com', 'washingtonpost.com', 'newyorker.com',
            'atlanticmedia.com', 'theatlantic.com', 'slate.com',
            'salon.com', 'thedailybeast.com', 'vanityfair.com',
            
            # Tech paywalls
            'wired.com', 'techcrunch.com', 'arstechnica.com',
            'theverge.com', 'engadget.com', 'gizmodo.com',
            
            # Academic/Research (often restricted)
            'scholar.google.com', 'patents.google.com', 
            'jstor.org', 'springer.com', 'elsevier.com',
            'wiley.com', 'tandfonline.com', 'sagepub.com',
            
            # Government archives (often slow/blocked)
            'sec.gov/Archives', 'fda.gov/downloads',
            'govinfo.gov', 'congress.gov/bill',
            
            # Social media (unreliable/blocked)
            'twitter.com', 'facebook.com', 'instagram.com',
            'tiktok.com', 'linkedin.com', 'reddit.com',
            
            # Other problematic domains
            'medium.com', 'substack.com', 'quora.com',
            'stackoverflow.com', 'github.com/issues'
        }
        
        # Tier 1 Priority domains (checked first)
        self.tier1_domains = [
            'reuters.com', 'apnews.com', 'who.int', 'cdc.gov', 
            'nih.gov', 'nature.com', 'science.org', 'bbc.com'
        ]
        
        # Enhanced source credibility with priority tiers
        self.source_credibility = {
            # Tier 1: Ultra-premium (0.95+) - checked first
            'reuters.com': 0.98,
            'apnews.com': 0.97,
            'who.int': 0.96,
            'cdc.gov': 0.96,
            'nih.gov': 0.95,
            'nature.com': 0.95,
            'science.org': 0.95,
            'ncbi.nlm.nih.gov': 0.95,
            'sec.gov': 0.95,
            'federalreserve.gov': 0.95,
            'sra.org.uk': 0.96,  # Solicitors Regulation Authority - UK legal regulator
            
            # Tier 2: High-quality (0.85-0.94)
            'bbc.com': 0.92,
            'npr.org': 0.91,
            'pbs.org': 0.90,
            'factcheck.org': 0.90,
            'snopes.com': 0.89,
            'politifact.com': 0.87,
            'ieee.org': 0.88,
            
            # Tier 3: Reliable (0.70-0.84)
            'wikipedia.org': 0.80,
            'britannica.com': 0.82,
            'mayoclinic.org': 0.83,
            'webmd.com': 0.75,
            'healthline.com': 0.75,
            'medicalnewstoday.com': 0.72,
            
            # News sources
            'cnn.com': 0.78,
            'nbcnews.com': 0.78,
            'cbsnews.com': 0.77,
            'abcnews.go.com': 0.77,
            'usatoday.com': 0.75,
            'theguardian.com': 0.80,
        }
        
        # Thread pool for CPU-bound operations
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Session pools for connection reuse
        self.session_pool = []
        for _ in range(3):
            session = requests.Session()
            session.headers.update({
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            self.session_pool.append(session)
    
    async def fact_check_claims(self, claims: List[Claim]) -> List[FactCheckResult]:
        """Ultra-fast concurrent claim processing"""
        logger.info(f"🚀 Starting OPTIMIZED fact-check for {len(claims)} claims")
        
        # Increased concurrency with smart batching
        semaphore = asyncio.Semaphore(self.concurrent_limit)
        
        async def fact_check_with_optimization(claim):
            async with semaphore:
                return await self.fact_check_claim(claim)
        
        # Process all claims concurrently
        start_time = time.time()
        tasks = [fact_check_with_optimization(claim) for claim in claims]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Process results and handle exceptions
        fact_check_results = []
        total_cache_hits = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error fact-checking claim {i}: {str(result)}")
                fact_check_results.append(FactCheckResult(
                    claim=claims[i],
                    verification_status='error',
                    authenticity_score=0.0,
                    sources_checked=[],
                    evidence=[],
                    contradictions=[],
                    processing_time=0.0,
                    error_message=str(result)
                ))
            else:
                fact_check_results.append(result)
                total_cache_hits += result.cache_hits
        
        logger.info(f"✅ Completed {len(fact_check_results)} claims in {total_time:.2f}s")
        logger.info(f"📊 Cache efficiency: {total_cache_hits} hits")
        
        return fact_check_results
    
    async def fact_check_claim(self, claim: Claim) -> FactCheckResult:
        """Ultra-optimized single claim processing with aggressive caching"""
        start_time = datetime.now()
        claim_id = f"claim_{int(time.time() * 1000)}"
        checkpoints = []
        cache_hits = 0
        
        logger.info(f"🔍 OPTIMIZED fact-check: {claim.text[:80]}...")
        
        try:
            # Checkpoint 1: Parallel source search with caching
            with TimedCheckpoint("source_search", {"claim_type": claim.claim_type.value}) as cp:
                sources, search_cache_hits = await self._parallel_source_search(claim)
                cache_hits += search_cache_hits
            checkpoints.append(self._get_checkpoint_from_context(cp))
            
            if not sources:
                logger.warning("No sources found, returning unverified")
                return self._create_unverified_result(claim, start_time, cache_hits)
            
            # Checkpoint 2: Concurrent evidence analysis
            with TimedCheckpoint("evidence_analysis", {"source_count": len(sources)}) as cp:
                evidence, contradictions = await self._concurrent_evidence_analysis(claim, sources)
            checkpoints.append(self._get_checkpoint_from_context(cp))
            
            # Checkpoint 3: Fast authenticity calculation
            with TimedCheckpoint("authenticity_calculation", {
                "evidence_count": len(evidence), 
                "contradiction_count": len(contradictions)
            }) as cp:
                authenticity_score = self._fast_authenticity_calculation(
                    claim, sources, evidence, contradictions
                )
            checkpoints.append(self._get_checkpoint_from_context(cp))
            
            # Checkpoint 4: Result compilation
            with TimedCheckpoint("result_compilation") as cp:
                verification_status = self._determine_verification_status(
                    authenticity_score, evidence, contradictions
                )
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                result = FactCheckResult(
                    claim=claim,
                    verification_status=verification_status,
                    authenticity_score=authenticity_score,
                    sources_checked=[self._source_to_dict(s) for s in sources],
                    evidence=evidence,
                    contradictions=contradictions,
                    processing_time=processing_time,
                    cache_hits=cache_hits
                )
            checkpoints.append(self._get_checkpoint_from_context(cp))
            
            # Add report with cache statistics
            add_claim_report(
                claim_id=claim_id,
                claim_text=claim.text,
                claim_type=claim.claim_type.value,
                checkpoints=checkpoints,
                success=True
            )
            
            logger.info(f"✅ Completed in {processing_time:.2f}s (cache hits: {cache_hits})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Optimized fact-check failed: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return FactCheckResult(
                claim=claim,
                verification_status='error',
                authenticity_score=0.0,
                sources_checked=[],
                evidence=[],
                contradictions=[],
                processing_time=processing_time,
                cache_hits=cache_hits,
                error_message=str(e)
            )
    
    async def _parallel_source_search(self, claim: Claim) -> Tuple[List[Source], int]:
        """Ultra-fast parallel source search with aggressive caching"""
        cache_hits = 0
        
        # Generate cache key for entire search
        search_key = f"search_{claim.claim_type.value}_{hashlib.md5(claim.text.encode()).hexdigest()[:8]}"
        
        # Try to get cached search results
        cached_sources = search_cache.get(search_key)
        if cached_sources:
            logger.debug(f"🎯 Cache HIT for source search: {search_key}")
            cache_hits += 1
            return cached_sources, cache_hits
        
        logger.debug(f"🔍 Cache MISS for source search, executing...")
        
        # Checkpoint: Generate optimized search queries (reduced to 2)
        with TimedCheckpoint("search_query_generation") as cp:
            search_queries = self._generate_optimized_queries(claim)
        
        # Checkpoint: Execute parallel web searches
        sources = []
        with TimedCheckpoint("web_search_execution", {"query_count": len(search_queries)}) as cp:
            # Create search tasks for parallel execution
            search_tasks = []
            
            # Priority source search (Tier 1 domains first)
            if claim.claim_type in [ClaimType.MEDICAL, ClaimType.SCIENTIFIC]:
                for domain in self.tier1_domains[:3]:  # Top 3 priority domains
                    task = self._search_priority_domain(search_queries[0], domain)
                    search_tasks.append(task)
            
            # General web search with reduced queries
            for query in search_queries:
                task = self._fast_web_search(query, claim.claim_type)
                search_tasks.append(task)
            
            # Execute all searches concurrently
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine results
            for result in search_results:
                if isinstance(result, list):
                    sources.extend(result)
                elif isinstance(result, Exception):
                    logger.debug(f"Search task failed: {str(result)}")
        
        # Checkpoint: Fast source processing
        with TimedCheckpoint("source_prioritization", {"raw_source_count": len(sources)}) as cp:
            # Ultra-fast deduplication and prioritization
            sources = self._ultra_fast_source_processing(sources)
        
        # Cache the results for 30 minutes
        search_cache.set(search_key, sources, ttl=1800)
        
        logger.info(f"🚀 Source search completed: {len(sources)} sources")
        return sources, cache_hits
    
    def _generate_optimized_queries(self, claim: Claim) -> List[str]:
        """Generate minimal, high-impact search queries"""
        queries = []
        
        # Primary query: claim text (truncated for speed)
        primary_query = claim.text[:100]  # Limit length
        queries.append(primary_query)
        
        # Secondary query: key entities + fact check
        if claim.entities and len(claim.entities) > 0:
            key_entity = claim.entities[0]['text']
            fact_check_query = f"fact check {key_entity} {claim.claim_type.value}"
            queries.append(fact_check_query)
        
        return queries[:self.max_search_queries]  # Maximum 2 queries
    
    async def _search_priority_domain(self, query: str, domain: str) -> List[Source]:
        """Search priority domain with caching"""
        cache_key = f"domain_{domain}_{hashlib.md5(query.encode()).hexdigest()[:8]}"
        
        cached_result = search_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            site_query = f"site:{domain} {query[:50]}"  # Truncate for speed
            sources = await self._google_search_cached(site_query)
            
            # Cache for 1 hour
            search_cache.set(cache_key, sources, ttl=3600)
            return sources
            
        except Exception as e:
            logger.debug(f"Priority domain search failed for {domain}: {str(e)}")
            return []
    
    async def _fast_web_search(self, query: str, claim_type: ClaimType) -> List[Source]:
        """Ultra-fast web search with aggressive caching"""
        cache_key = f"web_{claim_type.value}_{hashlib.md5(query.encode()).hexdigest()[:8]}"
        
        cached_result = search_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            sources = await self._google_search_cached(query[:100])  # Truncate query
            
            # Cache for 30 minutes
            search_cache.set(cache_key, sources, ttl=1800)
            return sources
            
        except Exception as e:
            logger.debug(f"Fast web search failed: {str(e)}")
            return []
    
    async def _google_search_cached(self, query: str) -> List[Source]:
        """Unified search with automatic fallback between providers"""
        try:
            # Use unified search service with fallback
            search_response = await unified_search_service.search(query, max_results=8)
            
            if not search_response.results:
                logger.warning(f"No search results from any provider for query: {query[:50]}...")
                return []
            
            # Convert unified search results to our Source format
            sources = []
            for result in search_response.results:
                source = await self._convert_unified_result_to_source(result)
                if source:
                    sources.append(source)
            
            # Log which provider was used for monitoring
            logger.info(f"🔍 Search via {search_response.provider_used}: {len(sources)} sources "
                       f"{'(cached)' if search_response.cache_hit else ''}")
            
            return sources
            
        except Exception as e:
            logger.warning(f"Unified search failed: {str(e)}")
            return []
    
    async def _convert_unified_result_to_source(self, result: UnifiedSearchResult) -> Optional[Source]:
        """Convert unified search result to Source object"""
        try:
            # Skip blocked domains immediately
            if any(blocked in result.domain for blocked in self.blocked_domains):
                return None
            
            # Get credibility score
            credibility_score = self.source_credibility.get(result.domain, 0.5)
            
            # Skip very low-credibility sources
            if credibility_score < 0.4:
                return None
            
            # Try fast content extraction with caching
            content = await self._ultra_fast_content_extraction(result.url)
            if not content:
                content = result.snippet  # Fallback to snippet
            
            return Source(
                url=result.url,
                title=result.title,
                content=content,
                relevance_score=result.relevance_score,
                credibility_score=credibility_score,
                publication_date=result.publication_date,
                domain=result.domain
            )
            
        except Exception as e:
            logger.debug(f"Failed to convert unified result to source: {str(e)}")
            return None
    
    async def _fast_source_creation(self, result: Dict) -> Optional[Source]:
        """Ultra-fast source creation with caching"""
        try:
            url = result.get('link', '')
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            if not url or not title:
                return None
            
            domain = self._extract_domain(url)
            
            # Skip blocked domains immediately
            if any(blocked in domain for blocked in self.blocked_domains):
                return None
            
            # Get credibility score
            credibility_score = self.source_credibility.get(domain, 0.5)
            
            # Skip very low-credibility sources
            if credibility_score < 0.4:
                return None
            
            # Try fast content extraction with caching
            content = await self._ultra_fast_content_extraction(url)
            if not content:
                content = snippet  # Fallback to snippet
            
            return Source(
                url=url,
                title=title,
                content=content,
                relevance_score=0.7,  # Default relevance
                credibility_score=credibility_score,
                publication_date=None,
                domain=domain
            )
            
        except Exception as e:
            logger.debug(f"Fast source creation failed: {str(e)}")
            return None
    
    async def _ultra_fast_content_extraction(self, url: str) -> str:
        """Ultra-fast content extraction using enhanced extractor"""
        try:
            domain = self._extract_domain(url)
            
            # Checkpoint: Enhanced content extraction
            with TimedCheckpoint("enhanced_content_extraction", {"url": url, "domain": domain}) as cp:
                result = await enhanced_extractor.extract_content_optimized(url, domain)
            
            if result.success and result.content:
                logger.debug(f"✅ Enhanced extraction success: {domain} ({result.method}, {result.duration:.3f}s)")
                return result.content
            else:
                logger.debug(f"❌ Enhanced extraction failed: {domain} ({result.error})")
                return ""
            
        except Exception as e:
            logger.debug(f"Enhanced extraction error for {url}: {str(e)}")
            return ""
    
    
    def _ultra_fast_source_processing(self, sources: List[Source]) -> List[Source]:
        """Ultra-fast source deduplication and prioritization"""
        if not sources:
            return []
        
        # Fast deduplication using set
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            if source.url not in seen_urls:
                seen_urls.add(source.url)
                unique_sources.append(source)
        
        # Fast prioritization: sort by credibility * relevance
        unique_sources.sort(
            key=lambda s: s.credibility_score * s.relevance_score, 
            reverse=True
        )
        
        # Return top sources only
        return unique_sources[:self.max_urls]
    
    async def _concurrent_evidence_analysis(self, claim: Claim, sources: List[Source]) -> Tuple[List[Dict], List[Dict]]:
        """Ultra-fast concurrent evidence analysis"""
        if not sources:
            return [], []
        
        # Create analysis tasks
        analysis_tasks = []
        semaphore = asyncio.Semaphore(self.concurrent_limit)
        
        async def analyze_source_fast(source):
            async with semaphore:
                try:
                    evidence = self._fast_evidence_extraction(claim, source)
                    contradictions = self._fast_contradiction_detection(claim, source)
                    return evidence, contradictions
                except Exception as e:
                    logger.debug(f"Fast analysis failed for {source.domain}: {str(e)}")
                    return [], []
        
        # Execute all analyses concurrently
        for source in sources:
            task = analyze_source_fast(source)
            analysis_tasks.append(task)
        
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Combine results
        all_evidence = []
        all_contradictions = []
        
        for result in results:
            if isinstance(result, tuple):
                evidence, contradictions = result
                all_evidence.extend(evidence)
                all_contradictions.extend(contradictions)
        
        # Fast sorting by relevance
        all_evidence.sort(key=lambda x: x.get('relevance_score', 0) * x.get('source_credibility', 0), reverse=True)
        all_contradictions.sort(key=lambda x: x.get('relevance_score', 0) * x.get('source_credibility', 0), reverse=True)
        
        return all_evidence[:10], all_contradictions[:5]  # Limit results
    
    def _fast_evidence_extraction(self, claim: Claim, source: Source) -> List[Dict[str, Any]]:
        """Ultra-fast evidence extraction with logical reasoning"""
        if not source.content or len(source.content) < 50:
            return []
        
        evidence = []
        
        # Fast keyword extraction
        claim_keywords = set()
        if claim.keywords:
            claim_keywords.update([kw.lower() for kw in claim.keywords[:3]])  # Limit keywords
        
        # Add key entities
        for entity in claim.entities[:2]:  # Limit entities
            if entity.get('text'):
                claim_keywords.add(entity['text'].lower())
        
        # Fast sentence splitting
        sentences = re.split(r'[.!?]+', source.content[:2000])  # Limit content
        
        for sentence in sentences[:20]:  # Limit sentences
            sentence = sentence.strip()
            if len(sentence) < 30:
                continue
            
            sentence_lower = sentence.lower()
            
            # Fast keyword matching
            keyword_matches = sum(1 for kw in claim_keywords if kw in sentence_lower)
            matched_keywords = [kw for kw in claim_keywords if kw in sentence_lower]
            
            if keyword_matches >= 1:  # Lower threshold for speed
                # Fast supporting language check
                supporting_indicators = ['according to', 'research shows', 'confirmed', 'verified', 'data shows', 'study found', 'evidence indicates', 'reports show']
                found_supporting_indicators = [ind for ind in supporting_indicators if ind in sentence_lower]
                has_supporting = len(found_supporting_indicators) > 0
                
                # Numerical evidence check
                numerical_patterns = ['%', 'percent', 'increased', 'decreased', 'rose', 'fell', 'up', 'down', 'higher', 'lower']
                found_numerical = [pattern for pattern in numerical_patterns if pattern in sentence_lower]
                has_numerical = len(found_numerical) > 0
                
                if keyword_matches >= 2 or has_supporting:
                    # **CRITICAL FIX**: Check for numerical contradictions in evidence
                    is_actually_contradictory = False
                    
                    # Extract numbers from both claim and evidence sentence
                    claim_numbers = re.findall(r'\b\d+\b', claim.text)
                    sentence_numbers = re.findall(r'\b\d+\b', sentence)
                    
                    # Check if claim contains specific numbers that don't match evidence
                    if claim_numbers and sentence_numbers:
                        # For specific numerical claims (like SRA numbers), check exact matches
                        for claim_num in claim_numbers:
                            if len(claim_num) >= 4:  # Likely an ID/registration number
                                matching_sentence_nums = [s_num for s_num in sentence_numbers if claim_num in s_num or s_num in claim_num]
                                if not matching_sentence_nums:
                                    # Found numbers in evidence that don't match the claimed numbers
                                    conflicting_nums = [s_num for s_num in sentence_numbers if len(s_num) >= 4]
                                    if conflicting_nums:
                                        is_actually_contradictory = True
                                        contradiction_reason = f"Evidence shows different number '{conflicting_nums[0]}' than claimed '{claim_num}'"
                                        break
                    
                    if is_actually_contradictory:
                        # This should be a contradiction, not evidence - return empty evidence
                        logger.info(f"Detected numerical contradiction: {contradiction_reason}")
                        return []  # Return empty evidence list since this is contradictory
                    else:
                        # Generate logical reasoning explanation for true evidence
                        reasoning_parts = []
                        
                        if matched_keywords:
                            reasoning_parts.append(f"Contains key terms from claim: {', '.join(matched_keywords[:3])}")
                        
                        if found_supporting_indicators:
                            reasoning_parts.append(f"Uses authoritative language: '{found_supporting_indicators[0]}'")
                        
                        if has_numerical and claim.claim_type.value in ['financial', 'statistical']:
                            reasoning_parts.append(f"Provides numerical data relevant to {claim.claim_type.value} claim")
                        
                        if source.credibility_score > 0.8:
                            reasoning_parts.append(f"Source has high credibility ({source.credibility_score:.2f})")
                        
                        if keyword_matches >= 2:
                            reasoning_parts.append(f"Multiple keyword matches ({keyword_matches}) indicate strong relevance")
                        
                        logical_reasoning = ". ".join(reasoning_parts) if reasoning_parts else "Sentence contains relevant keywords and context matching the claim"
                        
                        evidence.append({
                            'sentence': sentence,
                            'source_url': source.url,
                            'source_domain': source.domain,
                            'source_credibility': source.credibility_score,
                            'relevance_score': keyword_matches / max(len(claim_keywords), 1),
                            'type': 'supporting',
                            'logical_reasoning': logical_reasoning,
                            'matched_keywords': matched_keywords[:3],
                            'supporting_indicators': found_supporting_indicators
                        })
        
        return evidence[:2]  # Limit to top 2 per source
    
    def _fast_contradiction_detection(self, claim: Claim, source: Source) -> List[Dict[str, Any]]:
        """Ultra-fast contradiction detection with logical reasoning"""
        if not source.content or len(source.content) < 50:
            return []
        
        contradictions = []
        
        # Fast keyword extraction (same as evidence)
        claim_keywords = set()
        if claim.keywords:
            claim_keywords.update([kw.lower() for kw in claim.keywords[:3]])
        
        for entity in claim.entities[:2]:
            if entity.get('text'):
                claim_keywords.add(entity['text'].lower())
        
        # Fast sentence processing
        sentences = re.split(r'[.!?]+', source.content[:2000])
        
        for sentence in sentences[:20]:
            sentence = sentence.strip()
            if len(sentence) < 30:
                continue
            
            sentence_lower = sentence.lower()
            
            # Fast keyword matching
            keyword_matches = sum(1 for kw in claim_keywords if kw in sentence_lower)
            matched_keywords = [kw for kw in claim_keywords if kw in sentence_lower]
            
            if keyword_matches >= 1:
                # Enhanced contradiction detection
                contradictory_indicators = ['however', 'but', 'not', 'false', 'disputed', 'contradicts', 'denies', 'refutes', 'opposite', 'wrong', 'incorrect', 'misleading']
                found_contradictory_indicators = [ind for ind in contradictory_indicators if ind in sentence_lower]
                has_contradiction = len(found_contradictory_indicators) > 0
                
                # Negation patterns specific to financial/statistical claims
                negation_patterns = ['did not', 'does not', 'has not', 'cannot', 'never', 'no evidence', 'declined', 'dropped', 'fell']
                found_negations = [neg for neg in negation_patterns if neg in sentence_lower]
                has_negation = len(found_negations) > 0
                
                # Conflicting numerical evidence
                conflicting_numerical = ['decreased', 'fell', 'dropped', 'declined', 'lost', 'down', 'lower', 'negative']
                found_conflicting = [conf for conf in conflicting_numerical if conf in sentence_lower]
                has_conflicting_numbers = len(found_conflicting) > 0
                
                # Enhanced contextual contradiction detection
                is_actual_contradiction = False
                contradiction_reason = ""
                
                # **NUMERICAL CONTRADICTION DETECTION** - Check for mismatched numbers/IDs
                claim_numbers = re.findall(r'\b\d+\b', claim.text)
                sentence_numbers = re.findall(r'\b\d+\b', sentence)
                
                if claim_numbers and sentence_numbers:
                    for claim_num in claim_numbers:
                        if len(claim_num) >= 4:  # Likely an ID/registration number
                            matching_sentence_nums = [s_num for s_num in sentence_numbers if claim_num in s_num or s_num in claim_num]
                            if not matching_sentence_nums:
                                # Found numbers in evidence that don't match the claimed numbers
                                conflicting_nums = [s_num for s_num in sentence_numbers if len(s_num) >= 4]
                                if conflicting_nums:
                                    is_actual_contradiction = True
                                    contradiction_reason = f"Evidence shows different number '{conflicting_nums[0]}' than claimed '{claim_num}'"
                                    break
                
                # For regulatory/legal claims, only contradictions that directly dispute the regulatory status
                if not is_actual_contradiction and claim.claim_type.value in ['general', 'legal']:
                    # Look for direct regulatory contradictions
                    regulatory_contradictions = ['not regulated', 'unregulated', 'not licensed', 'revoked', 'suspended', 'deregistered']
                    direct_contradictions = [cont for cont in regulatory_contradictions if cont in sentence_lower]
                    
                    if direct_contradictions:
                        is_actual_contradiction = True
                        contradiction_reason = f"Directly contradicts regulatory status: '{direct_contradictions[0]}'"
                    elif has_conflicting_numbers and claim.claim_type.value in ['financial', 'statistical']:
                        is_actual_contradiction = True
                        contradiction_reason = f"Shows opposite trend: '{found_conflicting[0]}' contradicts claimed increase"
                elif not is_actual_contradiction:
                    # For other claim types, use existing logic but with higher threshold
                    if has_conflicting_numbers and claim.claim_type.value in ['financial', 'statistical']:
                        is_actual_contradiction = True
                        contradiction_reason = f"Shows opposite trend: '{found_conflicting[0]}' contradicts claimed increase"
                    elif found_negations and keyword_matches >= 2:  # Require more keyword matches for negations
                        # Check if negation is actually about the claim subject
                        claim_entities = [entity.get('text', '').lower() for entity in claim.entities if entity.get('text')]
                        negation_context = sentence_lower[max(0, sentence_lower.find(found_negations[0])-50):sentence_lower.find(found_negations[0])+50]
                        
                        if any(entity in negation_context for entity in claim_entities if entity):
                            is_actual_contradiction = True
                            contradiction_reason = f"Directly negates claim subject: '{found_negations[0]}'"
                
                if is_actual_contradiction:
                    # Generate logical reasoning explanation for contradiction
                    reasoning_parts = []
                    
                    if matched_keywords:
                        reasoning_parts.append(f"References same entities as claim: {', '.join(matched_keywords[:3])}")
                    
                    reasoning_parts.append(contradiction_reason)
                    
                    if source.credibility_score > 0.8:
                        reasoning_parts.append(f"High-credibility source ({source.credibility_score:.2f}) disputes claim")
                    
                    # Determine contradiction type
                    if "different number" in contradiction_reason:
                        contradiction_type = "numerical_contradiction"
                    elif has_conflicting_numbers:
                        contradiction_type = "numerical_contradiction"
                    elif 'not regulated' in sentence_lower or 'unregulated' in sentence_lower:
                        contradiction_type = "regulatory_contradiction"
                    elif found_negations:
                        contradiction_type = "direct_negation"
                    else:
                        contradiction_type = "contextual_contradiction"
                    
                    logical_reasoning = ". ".join(reasoning_parts)
                    
                    contradictions.append({
                        'sentence': sentence,
                        'source_url': source.url,
                        'source_domain': source.domain,
                        'source_credibility': source.credibility_score,
                        'relevance_score': keyword_matches / max(len(claim_keywords), 1),
                        'type': 'contradictory',
                        'logical_reasoning': logical_reasoning,
                        'matched_keywords': matched_keywords[:3],
                        'contradictory_indicators': found_contradictory_indicators,
                        'contradiction_type': contradiction_type
                    })
        
        return contradictions[:1]  # Limit to top 1 per source
    
    def _fast_authenticity_calculation(
        self, 
        claim: Claim, 
        sources: List[Source], 
        evidence: List[Dict], 
        contradictions: List[Dict]
    ) -> float:
        """Enhanced authenticity calculation with improved scoring logic"""
        if not sources:
            return 0.0
        
        # Base score from source credibility
        avg_credibility = sum(s.credibility_score for s in sources) / len(sources)
        base_score = avg_credibility * 0.4
        
        # Enhanced evidence scoring
        evidence_score = 0.0
        if evidence:
            # Calculate weighted evidence score based on relevance and credibility
            evidence_weights = []
            for e in evidence:
                relevance = e.get('relevance_score', 0.5)
                credibility = e.get('source_credibility', 0.5)
                # Bonus for high-relevance evidence with multiple keyword matches
                keyword_bonus = 0.1 if relevance > 0.6 else 0.0
                weight = (relevance * credibility) + keyword_bonus
                evidence_weights.append(weight)
            
            evidence_score = min(0.5, sum(evidence_weights) / len(evidence_weights) * 0.5)
        
        # Enhanced contradiction penalty - only for meaningful contradictions
        contradiction_penalty = 0.0
        if contradictions:
            # Filter out weak contradictions (low relevance or contextual issues)
            meaningful_contradictions = [
                c for c in contradictions 
                if c.get('relevance_score', 0) > 0.4 and 
                   c.get('contradiction_type', '') in ['numerical_contradiction', 'regulatory_contradiction', 'direct_negation']
            ]
            
            if meaningful_contradictions:
                contradiction_weights = []
                for c in meaningful_contradictions:
                    relevance = c.get('relevance_score', 0.5)
                    credibility = c.get('source_credibility', 0.5)
                    weight = relevance * credibility
                    contradiction_weights.append(weight)
                
                contradiction_penalty = min(0.4, sum(contradiction_weights) / len(contradiction_weights) * 0.4)
        
        # Cross-reference bonus for multiple sources
        cross_reference_bonus = 0.0
        if len(sources) >= 3:
            cross_reference_bonus = min(0.15, len(sources) * 0.03)
        elif len(sources) >= 2:
            cross_reference_bonus = 0.05
        
        # Special bonus for official/regulatory sources
        regulatory_bonus = 0.0
        official_domains = ['sra.org.uk', 'gov.uk', 'sec.gov', 'who.int', 'cdc.gov']
        has_official_source = any(s.domain in official_domains for s in sources)
        if has_official_source and evidence:
            regulatory_bonus = 0.1
        
        # Calculate final score
        score = base_score + evidence_score + cross_reference_bonus + regulatory_bonus - contradiction_penalty
        
        return max(0.0, min(1.0, score))
    
    def _determine_verification_status(
        self, 
        authenticity_score: float, 
        evidence: List[Dict], 
        contradictions: List[Dict]
    ) -> str:
        """Fast verification status determination"""
        if authenticity_score >= 0.8 and evidence and not contradictions:
            return 'verified'
        elif authenticity_score >= 0.6 and evidence:
            return 'partially_verified'
        elif contradictions and authenticity_score < 0.4:
            return 'disputed'
        elif authenticity_score < 0.3:
            return 'likely_false'
        else:
            return 'unverified'
    
    def _create_unverified_result(self, claim: Claim, start_time: datetime, cache_hits: int) -> FactCheckResult:
        """Create unverified result when no sources found"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return FactCheckResult(
            claim=claim,
            verification_status='unverified',
            authenticity_score=0.0,
            sources_checked=[],
            evidence=[],
            contradictions=[],
            processing_time=processing_time,
            cache_hits=cache_hits,
            error_message="No reliable sources found"
        )
    
    def _extract_domain(self, url: str) -> str:
        """Fast domain extraction"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().replace('www.', '')
        except:
            return ''
    
    def _source_to_dict(self, source: Source) -> Dict[str, Any]:
        """Convert Source to dict"""
        return {
            'url': source.url,
            'title': source.title,
            'domain': source.domain,
            'credibility_score': source.credibility_score,
            'relevance_score': source.relevance_score
        }
    
    def _get_checkpoint_from_context(self, context) -> 'CheckpointTiming':
        """Extract checkpoint timing from context"""
        from .checkpoint_monitor import CheckpointTiming
        checkpoint = context.monitor.current_checkpoints[context.checkpoint_id]
        return CheckpointTiming(
            name=checkpoint.name,
            start_time=checkpoint.start_time,
            end_time=checkpoint.end_time,
            duration=checkpoint.duration,
            success=checkpoint.success,
            error_message=checkpoint.error_message,
            metadata=checkpoint.metadata
        )
    
    async def fact_check_claims_ultra_optimized(self, claims: List[Claim]) -> List[FactCheckResult]:
        """Use ultra-optimized fact checking with all advanced optimizations"""
        return await ultra_fact_checker.fact_check_claims_ultra_fast(claims)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        from .performance_cache import get_cache_stats
        
        return {
            'cache_stats': get_cache_stats(),
            'configuration': {
                'max_urls': self.max_urls,
                'priority_sources_limit': self.priority_sources_limit,
                'concurrent_limit': self.concurrent_limit,
                'timeout': self.timeout,
                'max_search_queries': self.max_search_queries,
                'blocked_domains_count': len(self.blocked_domains),
                'user_agents_count': len(self.user_agents)
            }
        }
    
    def get_ultra_performance_stats(self) -> Dict[str, Any]:
        """Get ultra-optimization performance statistics"""
        return ultra_fact_checker.get_ultra_performance_stats()
    
    def get_search_provider_stats(self) -> Dict[str, Any]:
        """Get search provider health and usage statistics"""
        return unified_search_service.get_provider_stats()