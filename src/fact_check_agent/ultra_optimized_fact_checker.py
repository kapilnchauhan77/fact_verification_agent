"""
Ultra-Optimized Fact Checker with All Advanced Optimizations
Integrates all performance improvements to achieve maximum speed and accuracy
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
from .search_services import unified_search_service, SearchResult as UnifiedSearchResult

# Import all advanced optimization modules
from .predictive_caching_system import predictive_cache
from .advanced_evidence_analyzer import advanced_evidence_analyzer
from .custom_scrapers import custom_scraper
from .intelligent_query_optimizer import query_optimizer

logger = logging.getLogger(__name__)

@dataclass
class FactCheckResult:
    """Enhanced result of fact-checking with advanced metrics"""
    claim: Claim
    verification_status: str
    authenticity_score: float
    sources_checked: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    contradictions: List[Dict[str, Any]]
    processing_time: float
    cache_hits: int = 0
    optimization_stats: Dict[str, Any] = None
    error_message: Optional[str] = None

@dataclass
class Source:
    """Enhanced source representation"""
    url: str
    title: str
    content: str
    relevance_score: float
    credibility_score: float
    publication_date: Optional[datetime]
    domain: str
    extraction_method: str = "unknown"

class UltraOptimizedFactChecker:
    """Ultra-optimized fact-checking engine with all advanced optimizations"""
    
    def __init__(self):
        """Initialize ultra-optimized fact checker"""
        
        # Ultra-aggressive performance settings
        self.max_urls = 6  # Further reduced for ultra-speed
        self.priority_sources_limit = 4  # Focus on absolute top sources
        self.delay_between_requests = 0.05  # Minimal delay
        self.timeout = 2  # Ultra-aggressive timeout
        self.max_retries = 0  # No retries for maximum speed
        self.concurrent_limit = 15  # Increased concurrency
        self.max_search_queries = 2  # Keep reduced
        
        # Enhanced user agent pool
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # Further expanded blocked domains (50+ domains)
        self.blocked_domains = {
            # Paywalls and subscription sites
            'bloomberg.com', 'wsj.com', 'ft.com', 'economist.com',
            'nytimes.com', 'washingtonpost.com', 'newyorker.com',
            'theatlantic.com', 'harpers.org', 'vanityfair.com',
            
            # Tech paywalls
            'wired.com', 'techcrunch.com', 'arstechnica.com',
            'theverge.com', 'engadget.com', 'gizmodo.com',
            
            # Academic/Research restrictions
            'scholar.google.com', 'patents.google.com',
            'jstor.org', 'springer.com', 'elsevier.com',
            'wiley.com', 'tandfonline.com', 'sagepub.com',
            
            # Government archives (slow)
            'sec.gov/Archives', 'fda.gov/downloads',
            'govinfo.gov', 'congress.gov/bill',
            
            # Social media and unreliable
            'twitter.com', 'facebook.com', 'instagram.com',
            'tiktok.com', 'linkedin.com', 'reddit.com',
            'medium.com', 'substack.com', 'quora.com',
            
            # Additional problematic sites
            'pinterest.com', 'tumblr.com', 'yahoo.com/news',
            'msn.com', 'aol.com', 'ask.com', 'answers.com',
            'ehow.com', 'wikihow.com', 'buzzfeed.com',
            'huffpost.com', 'vox.com', 'slate.com',
            'salon.com', 'dailybeast.com'
        }
        
        # Ultra-priority domains (checked first)
        self.ultra_priority_domains = [
            'reuters.com', 'apnews.com', 'who.int', 'cdc.gov',
            'factcheck.org', 'snopes.com'
        ]
        
        # Enhanced source credibility
        self.source_credibility = {
            # Ultra-tier (0.97+)
            'reuters.com': 0.99,
            'apnews.com': 0.98,
            'who.int': 0.97,
            'cdc.gov': 0.97,
            
            # Premium tier (0.90-0.96)
            'factcheck.org': 0.95,
            'snopes.com': 0.94,
            'nature.com': 0.96,
            'science.org': 0.96,
            'bbc.com': 0.93,
            'npr.org': 0.92,
            'pbs.org': 0.91,
            'politifact.com': 0.90,
            
            # High-quality tier (0.80-0.89)
            'ncbi.nlm.nih.gov': 0.89,
            'nih.gov': 0.88,
            'sec.gov': 0.87,
            'federalreserve.gov': 0.86,
            'mayoclinic.org': 0.85,
            'ieee.org': 0.84,
            'wikipedia.org': 0.82,
            'britannica.com': 0.83,
            'theguardian.com': 0.81,
            'usatoday.com': 0.80
        }
        
        # Thread pool for CPU operations
        self.thread_pool = ThreadPoolExecutor(max_workers=6)
        
        # Performance tracking
        self.optimization_metrics = {
            'predictive_cache_hits': 0,
            'custom_scraper_uses': 0,
            'intelligent_query_uses': 0,
            'advanced_evidence_uses': 0
        }
    
    async def fact_check_claims_ultra_fast(self, claims: List[Claim]) -> List[FactCheckResult]:
        """Ultra-fast claim processing with all optimizations"""
        logger.info(f"🚀 Starting ULTRA-OPTIMIZED fact-check for {len(claims)} claims")
        
        # Increased concurrency for ultra-speed
        semaphore = asyncio.Semaphore(self.concurrent_limit)
        
        async def fact_check_with_ultra_optimization(claim):
            async with semaphore:
                return await self.fact_check_claim_ultra_fast(claim)
        
        # Process all claims concurrently
        start_time = time.time()
        tasks = [fact_check_with_ultra_optimization(claim) for claim in claims]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Process results
        fact_check_results = []
        total_cache_hits = 0
        total_optimization_stats = {
            'predictive_cache_hits': 0,
            'custom_scraper_successes': 0,
            'intelligent_queries_generated': 0,
            'advanced_evidence_matches': 0
        }
        
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
                
                # Aggregate optimization stats
                if result.optimization_stats:
                    for key, value in result.optimization_stats.items():
                        total_optimization_stats[key] = total_optimization_stats.get(key, 0) + value
        
        logger.info(f"✅ ULTRA-OPTIMIZED processing completed {len(fact_check_results)} claims in {total_time:.2f}s")
        logger.info(f"📊 Total cache hits: {total_cache_hits}")
        logger.info(f"🎯 Optimization stats: {total_optimization_stats}")
        
        return fact_check_results
    
    async def fact_check_claim_ultra_fast(self, claim: Claim) -> FactCheckResult:
        """Ultra-optimized single claim processing"""
        start_time = datetime.now()
        claim_id = f"ultra_claim_{int(time.time() * 1000)}"
        checkpoints = []
        cache_hits = 0
        optimization_stats = {
            'predictive_cache_hits': 0,
            'custom_scraper_successes': 0,
            'intelligent_queries_generated': 0,
            'advanced_evidence_matches': 0
        }
        
        logger.info(f"🔍 ULTRA-OPTIMIZED fact-check: {claim.text[:60]}...")
        
        try:
            # Checkpoint 1: Ultra-fast intelligent source search
            with TimedCheckpoint("ultra_source_search", {"claim_type": claim.claim_type.value}) as cp:
                sources, search_cache_hits = await self._ultra_fast_source_search(claim, optimization_stats)
                cache_hits += search_cache_hits
            checkpoints.append(self._get_checkpoint_from_context(cp))
            
            if not sources:
                logger.warning("No sources found with ultra-optimization")
                return self._create_unverified_result(claim, start_time, cache_hits, optimization_stats)
            
            # Checkpoint 2: Advanced evidence analysis with semantic understanding
            with TimedCheckpoint("advanced_evidence_analysis", {"source_count": len(sources)}) as cp:
                evidence, contradictions = await self._advanced_evidence_analysis(claim, sources, optimization_stats)
            checkpoints.append(self._get_checkpoint_from_context(cp))
            
            # Checkpoint 3: Enhanced authenticity calculation
            with TimedCheckpoint("enhanced_authenticity_calculation", {
                "evidence_count": len(evidence), 
                "contradiction_count": len(contradictions)
            }) as cp:
                authenticity_score = self._enhanced_authenticity_calculation(
                    claim, sources, evidence, contradictions
                )
            checkpoints.append(self._get_checkpoint_from_context(cp))
            
            # Checkpoint 4: Final result compilation
            with TimedCheckpoint("ultra_result_compilation") as cp:
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
                    cache_hits=cache_hits,
                    optimization_stats=optimization_stats
                )
            checkpoints.append(self._get_checkpoint_from_context(cp))
            
            # Add comprehensive report
            add_claim_report(
                claim_id=claim_id,
                claim_text=claim.text,
                claim_type=claim.claim_type.value,
                checkpoints=checkpoints,
                success=True
            )
            
            logger.info(f"✅ ULTRA-OPTIMIZED completed in {processing_time:.2f}s (cache: {cache_hits}, optimizations: {sum(optimization_stats.values())})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ultra-optimized fact-check failed: {str(e)}")
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
                optimization_stats=optimization_stats,
                error_message=str(e)
            )
    
    async def _ultra_fast_source_search(
        self, 
        claim: Claim, 
        optimization_stats: Dict[str, int]
    ) -> Tuple[List[Source], int]:
        """Ultra-fast source search with intelligent query optimization and predictive caching"""
        cache_hits = 0
        
        # Checkpoint: Intelligent query generation
        with TimedCheckpoint("intelligent_query_generation") as cp:
            optimized_queries = query_optimizer.optimize_queries(claim)
            optimization_stats['intelligent_queries_generated'] += len(optimized_queries)
        
        logger.debug(f"Generated {len(optimized_queries)} intelligent queries")
        
        # Checkpoint: Predictive cache check
        sources = []
        with TimedCheckpoint("predictive_cache_check") as cp:
            for opt_query in optimized_queries:
                cache_key = f"ultra_{claim.claim_type.value}_{hashlib.md5(opt_query.query.encode()).hexdigest()[:8]}"
                
                cached_sources = await predictive_cache.get_with_prediction(
                    cache_key,
                    predictive_cache.search_cache,
                    claim.claim_type.value,
                    [claim.text[:50]]
                )
                
                if cached_sources:
                    sources.extend(cached_sources)
                    cache_hits += 1
                    optimization_stats['predictive_cache_hits'] += 1
        
        # If we have enough cached sources, use them
        if len(sources) >= self.max_urls // 2:
            logger.debug(f"Using {len(sources)} cached sources from predictive cache")
            return sources[:self.max_urls], cache_hits
        
        # Checkpoint: Ultra-priority source search
        with TimedCheckpoint("ultra_priority_search") as cp:
            if claim.claim_type in [ClaimType.MEDICAL, ClaimType.SCIENTIFIC]:
                priority_sources = await self._search_ultra_priority_domains(
                    optimized_queries[0] if optimized_queries else claim.text[:50],
                    claim.claim_type
                )
                sources.extend(priority_sources)
        
        # Checkpoint: General search if needed
        if len(sources) < self.max_urls:
            with TimedCheckpoint("ultra_general_search") as cp:
                for opt_query in optimized_queries[:1]:  # Only use best query
                    try:
                        general_sources = await self._ultra_fast_web_search(opt_query, claim.claim_type)
                        sources.extend(general_sources)
                        
                        # Cache results
                        cache_key = f"ultra_{claim.claim_type.value}_{hashlib.md5(opt_query.query.encode()).hexdigest()[:8]}"
                        await predictive_cache.set_with_prediction(
                            cache_key,
                            general_sources,
                            predictive_cache.search_cache,
                            claim.claim_type.value,
                            [claim.text[:50]],
                            ttl=1800
                        )
                        
                    except Exception as e:
                        logger.debug(f"Ultra-fast search failed: {str(e)}")
                        continue
        
        # Checkpoint: Ultra-fast source processing
        with TimedCheckpoint("ultra_source_processing") as cp:
            final_sources = self._ultra_fast_source_processing(sources)
        
        logger.info(f"🚀 Ultra-fast source search: {len(final_sources)} sources")
        return final_sources, cache_hits
    
    async def _search_ultra_priority_domains(
        self, 
        query: str, 
        claim_type: ClaimType
    ) -> List[Source]:
        """Search ultra-priority domains first"""
        sources = []
        
        for domain in self.ultra_priority_domains[:3]:  # Top 3 only
            try:
                site_query = f"site:{domain} {query[:40]}"
                domain_sources = await self._google_search_ultra_fast(site_query)
                sources.extend(domain_sources)
                
                if len(sources) >= 3:  # Enough from priority domains
                    break
                    
            except Exception as e:
                logger.debug(f"Ultra-priority search failed for {domain}: {str(e)}")
                continue
        
        return sources
    
    async def _ultra_fast_web_search(self, optimized_query, claim_type: ClaimType) -> List[Source]:
        """Ultra-fast web search with optimized queries"""
        return await self._google_search_ultra_fast(optimized_query.query[:80])
    
    async def _google_search_ultra_fast(self, query: str) -> List[Source]:
        """Ultra-fast Google search with minimal processing"""
        if not config.serp_api_key:
            return []
        
        try:
            search = GoogleSearch({
                "q": query,
                "api_key": config.serp_api_key,
                "num": 6,  # Further reduced for speed
                "safe": "active"
            })
            
            results = search.get_dict()
            sources = []
            
            if "organic_results" in results:
                # Process only top results
                for result in results["organic_results"][:4]:  # Top 4 only
                    source = await self._ultra_fast_source_creation(result)
                    if source:
                        sources.append(source)
            
            return sources
            
        except Exception as e:
            logger.debug(f"Ultra-fast Google search failed: {str(e)}")
            return []
    
    async def _ultra_fast_source_creation(self, result: Dict) -> Optional[Source]:
        """Ultra-fast source creation with custom scrapers"""
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
            
            credibility_score = self.source_credibility.get(domain, 0.5)
            
            # Skip very low-credibility sources
            if credibility_score < 0.4:
                return None
            
            # Use custom scraper if available
            content = ""
            extraction_method = "snippet"
            
            if domain in custom_scraper.get_supported_domains():
                try:
                    scrape_result = await custom_scraper.scrape_with_custom_logic(url)
                    if scrape_result.success:
                        content = scrape_result.content
                        extraction_method = scrape_result.method
                        self.optimization_metrics['custom_scraper_uses'] += 1
                except Exception as e:
                    logger.debug(f"Custom scraper failed for {domain}: {str(e)}")
            
            # Fallback to snippet if no content
            if not content:
                content = snippet
            
            return Source(
                url=url,
                title=title,
                content=content,
                relevance_score=0.8,  # Higher default for optimized sources
                credibility_score=credibility_score,
                publication_date=None,
                domain=domain,
                extraction_method=extraction_method
            )
            
        except Exception as e:
            logger.debug(f"Ultra-fast source creation failed: {str(e)}")
            return None
    
    def _ultra_fast_source_processing(self, sources: List[Source]) -> List[Source]:
        """Ultra-fast source deduplication and prioritization"""
        if not sources:
            return []
        
        # Ultra-fast deduplication
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            if source.url not in seen_urls:
                seen_urls.add(source.url)
                unique_sources.append(source)
        
        # Ultra-fast prioritization: sort by credibility only
        unique_sources.sort(key=lambda s: s.credibility_score, reverse=True)
        
        return unique_sources[:self.max_urls]
    
    async def _advanced_evidence_analysis(
        self, 
        claim: Claim, 
        sources: List[Source], 
        optimization_stats: Dict[str, int]
    ) -> Tuple[List[Dict], List[Dict]]:
        """Advanced evidence analysis using semantic understanding"""
        
        # Convert sources to format expected by advanced analyzer
        source_dicts = []
        for source in sources:
            source_dict = {
                'url': source.url,
                'title': source.title,
                'content': source.content,
                'domain': source.domain,
                'credibility_score': source.credibility_score
            }
            source_dicts.append(source_dict)
        
        # Use advanced evidence analyzer
        evidence, contradictions = await advanced_evidence_analyzer.analyze_evidence_ultra_fast(
            claim, source_dicts
        )
        
        optimization_stats['advanced_evidence_matches'] += len(evidence) + len(contradictions)
        
        return evidence, contradictions
    
    def _enhanced_authenticity_calculation(
        self, 
        claim: Claim, 
        sources: List[Source], 
        evidence: List[Dict], 
        contradictions: List[Dict]
    ) -> float:
        """Enhanced authenticity calculation with advanced metrics"""
        if not sources:
            return 0.0
        
        # Base score from source credibility (weighted by extraction method)
        credibility_scores = []
        for source in sources:
            score = source.credibility_score
            
            # Boost for successful custom extraction
            if source.extraction_method.endswith('_custom'):
                score *= 1.1
            
            credibility_scores.append(score)
        
        avg_credibility = sum(credibility_scores) / len(credibility_scores)
        base_score = avg_credibility * 0.4
        
        # Evidence scoring with semantic similarity
        evidence_score = 0.0
        if evidence:
            evidence_weights = []
            for e in evidence:
                weight = e.get('relevance_score', 0.5) * e.get('source_credibility', 0.5)
                
                # Boost for semantic similarity
                semantic_sim = e.get('semantic_similarity', 0.0)
                if semantic_sim > 0.6:
                    weight *= 1.2
                
                evidence_weights.append(weight)
            
            evidence_score = min(0.4, sum(evidence_weights) / len(evidence_weights) * 0.4)
        
        # Contradiction penalty with semantic consideration
        contradiction_penalty = 0.0
        if contradictions:
            contradiction_weights = []
            for c in contradictions:
                weight = c.get('relevance_score', 0.5) * c.get('source_credibility', 0.5)
                
                # Higher penalty for high semantic similarity contradictions
                semantic_sim = c.get('semantic_similarity', 0.0)
                if semantic_sim > 0.6:
                    weight *= 1.3
                
                contradiction_weights.append(weight)
            
            contradiction_penalty = min(0.5, sum(contradiction_weights) / len(contradiction_weights) * 0.5)
        
        # Cross-reference bonus (enhanced for custom scrapers)
        cross_reference_bonus = 0.0
        if len(sources) >= 3:
            cross_reference_bonus = min(0.2, len(sources) * 0.04)
            
            # Bonus for diverse extraction methods
            methods = set(s.extraction_method for s in sources)
            if len(methods) > 1:
                cross_reference_bonus *= 1.1
        
        # Calculate final score
        authenticity_score = base_score + evidence_score + cross_reference_bonus - contradiction_penalty
        
        return max(0.0, min(1.0, authenticity_score))
    
    def _determine_verification_status(
        self, 
        authenticity_score: float, 
        evidence: List[Dict], 
        contradictions: List[Dict]
    ) -> str:
        """Enhanced verification status determination"""
        if authenticity_score >= 0.85 and evidence and not contradictions:
            return 'verified'
        elif authenticity_score >= 0.75 and evidence and len(contradictions) <= 1:
            return 'highly_likely'
        elif authenticity_score >= 0.6 and evidence:
            return 'partially_verified'
        elif contradictions and authenticity_score < 0.4:
            return 'disputed'
        elif authenticity_score < 0.25:
            return 'likely_false'
        else:
            return 'unverified'
    
    def _create_unverified_result(
        self, 
        claim: Claim, 
        start_time: datetime, 
        cache_hits: int,
        optimization_stats: Dict[str, int]
    ) -> FactCheckResult:
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
            optimization_stats=optimization_stats,
            error_message="No reliable sources found with ultra-optimization"
        )
    
    def _extract_domain(self, url: str) -> str:
        """Fast domain extraction"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().replace('www.', '')
        except:
            return ''
    
    def _source_to_dict(self, source: Source) -> Dict[str, Any]:
        """Convert Source to enhanced dict"""
        return {
            'url': source.url,
            'title': source.title,
            'domain': source.domain,
            'credibility_score': source.credibility_score,
            'relevance_score': source.relevance_score,
            'extraction_method': source.extraction_method
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
    
    def get_ultra_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive ultra-optimization statistics"""
        return {
            'ultra_configuration': {
                'max_urls': self.max_urls,
                'priority_sources_limit': self.priority_sources_limit,
                'concurrent_limit': self.concurrent_limit,
                'timeout': self.timeout,
                'max_search_queries': self.max_search_queries,
                'blocked_domains_count': len(self.blocked_domains),
                'ultra_priority_domains': len(self.ultra_priority_domains)
            },
            'optimization_modules': {
                'predictive_caching': predictive_cache.get_prediction_stats(),
                'advanced_evidence': advanced_evidence_analyzer.get_performance_stats(),
                'custom_scrapers': custom_scraper.get_scraper_stats(),
                'intelligent_queries': query_optimizer.get_query_optimization_stats()
            },
            'runtime_metrics': self.optimization_metrics
        }

# Global ultra-optimized fact checker
ultra_fact_checker = UltraOptimizedFactChecker()