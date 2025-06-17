"""
Unified Search Service with Multiple Provider Fallbacks
Provides resilient search capabilities with automatic failover between SERP AI, Google Custom Search, and DuckDuckGo
"""

import asyncio
import logging
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from urllib.parse import urlparse
import json
import socket
from contextlib import asynccontextmanager

import aiohttp
import requests
from serpapi import GoogleSearch
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from duckduckgo_search import DDGS

from .config import config
from .performance_cache import search_cache

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Unified search result structure"""
    url: str
    title: str
    snippet: str
    domain: str
    source_provider: str
    relevance_score: float = 0.7
    publication_date: Optional[datetime] = None

@dataclass
class SearchResponse:
    """Search response with metadata"""
    results: List[SearchResult]
    provider_used: str
    query: str
    total_results: int
    processing_time: float
    cache_hit: bool = False
    error_message: Optional[str] = None

class SearchProviderError(Exception):
    """Custom exception for search provider errors"""
    pass

class NetworkError(SearchProviderError):
    """Network connectivity related errors"""
    pass

class TimeoutError(SearchProviderError):
    """Request timeout errors"""
    pass

class RateLimitError(SearchProviderError):
    """Rate limiting errors"""
    pass

class UnifiedSearchService:
    """Unified search service with multiple provider fallbacks"""
    
    def __init__(self):
        """Initialize the unified search service"""
        self.providers = ['serp_api', 'google_custom_search', 'gcp_search', 'duckduckgo']
        self.provider_timeouts = {
            'serp_api': 5.0,
            'google_custom_search': 4.0,
            'gcp_search': 4.0,
            'duckduckgo': 3.0
        }
        self.max_results = 10
        self.retry_attempts = 3
        self.cache_ttl = 1800  # 30 minutes
        self.network_timeout = 10  # Network request timeout
        self.retry_delay = 1.0  # Delay between retries
        
        # Provider health tracking
        self.provider_health = {
            'serp_api': {'last_success': None, 'consecutive_failures': 0},
            'google_custom_search': {'last_success': None, 'consecutive_failures': 0},
            'gcp_search': {'last_success': None, 'consecutive_failures': 0},
            'duckduckgo': {'last_success': None, 'consecutive_failures': 0}
        }
        
        # Initialize Google Custom Search client
        self._google_search_client = None
        if config.google_search_api_key and config.google_search_engine_id:
            try:
                self._google_search_client = build("customsearch", "v1", 
                                                 developerKey=config.google_search_api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Google Custom Search: {e}")
        
        # Initialize GCP Search client
        self._gcp_search_client = None
        if config.gcp_search_api_key and config.gcp_search_engine_id:
            try:
                self._gcp_search_client = build("customsearch", "v1", 
                                               developerKey=config.gcp_search_api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize GCP Search: {e}")
    
    async def search(self, query: str, max_results: int = None) -> SearchResponse:
        """
        Perform search with automatic fallback between providers
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            SearchResponse with results and metadata
        """
        start_time = time.time()
        max_results = max_results or self.max_results
        
        # Check cache first
        cache_key = f"unified_search_{hashlib.md5(query.encode()).hexdigest()[:12]}_{max_results}"
        cached_response = search_cache.get(cache_key)
        if cached_response:
            cached_response['cache_hit'] = True
            cached_response['processing_time'] = time.time() - start_time
            logger.info(f"🎯 Cache HIT for unified search: {query[:50]}...")
            return SearchResponse(**cached_response)
        
        logger.info(f"🔍 Unified search: {query[:50]}...")
        
        # Try providers in priority order
        last_error = None
        for provider in self._get_provider_priority():
            try:
                if not self._is_provider_healthy(provider):
                    logger.debug(f"Skipping unhealthy provider: {provider}")
                    continue
                
                logger.debug(f"Trying search provider: {provider}")
                response = await self._search_with_provider(provider, query, max_results)
                
                if response and response.results:
                    # Update provider health
                    self._update_provider_health(provider, success=True)
                    
                    # Cache successful response
                    response_dict = asdict(response)
                    response_dict['cache_hit'] = False
                    search_cache.set(cache_key, response_dict, ttl=self.cache_ttl)
                    
                    processing_time = time.time() - start_time
                    response.processing_time = processing_time
                    
                    logger.info(f"✅ Search success with {provider}: {len(response.results)} results in {processing_time:.2f}s")
                    return response
                else:
                    logger.warning(f"Provider {provider} returned no results")
                    
            except Exception as e:
                logger.warning(f"Provider {provider} failed: {str(e)}")
                self._update_provider_health(provider, success=False)
                last_error = e
                continue
        
        # All providers failed - try degraded mode
        processing_time = time.time() - start_time
        logger.warning(f"All search providers failed. Attempting offline/degraded mode.")
        
        # Try to provide degraded search results
        degraded_response = await self._degraded_mode_search(query, max_results)
        if degraded_response and degraded_response.results:
            degraded_response.processing_time = processing_time
            degraded_response.error_message = f"Degraded mode: All live providers failed. Last error: {str(last_error) if last_error else 'Unknown'}"
            logger.info(f"Degraded mode provided {len(degraded_response.results)} cached/fallback results")
            return degraded_response
        
        # Complete failure
        error_msg = f"All search providers failed including degraded mode. Last error: {str(last_error) if last_error else 'Unknown'}"
        logger.error(error_msg)
        
        return SearchResponse(
            results=[],
            provider_used="none",
            query=query,
            total_results=0,
            processing_time=processing_time,
            error_message=error_msg
        )
    
    async def _search_with_provider(self, provider: str, query: str, max_results: int) -> Optional[SearchResponse]:
        """Search with specific provider with retry logic"""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                if provider == 'serp_api':
                    return await self._search_serp_api(query, max_results)
                elif provider == 'google_custom_search':
                    return await self._search_google_custom(query, max_results)
                elif provider == 'gcp_search':
                    return await self._search_gcp_search(query, max_results)
                elif provider == 'duckduckgo':
                    return await self._search_duckduckgo(query, max_results)
                else:
                    raise SearchProviderError(f"Unknown provider: {provider}")
                    
            except (NetworkError, TimeoutError, socket.gaierror, aiohttp.ClientError) as e:
                last_error = e
                if attempt < self.retry_attempts - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.debug(f"Provider {provider} network error (attempt {attempt + 1}), retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.warning(f"Provider {provider} failed after {self.retry_attempts} attempts: {str(e)}")
                    raise NetworkError(f"{provider} network failed: {str(e)}")
                    
            except RateLimitError as e:
                logger.warning(f"Provider {provider} rate limited: {str(e)}")
                raise e
                
            except Exception as e:
                logger.debug(f"Provider {provider} search failed: {str(e)}")
                raise SearchProviderError(f"{provider} search failed: {str(e)}")
        
        if last_error:
            raise NetworkError(f"{provider} failed after {self.retry_attempts} attempts: {str(last_error)}")
        
        raise SearchProviderError(f"{provider} failed unexpectedly")
    
    async def _search_serp_api(self, query: str, max_results: int) -> Optional[SearchResponse]:
        """Search using SERP API"""
        if not config.serp_api_key:
            raise SearchProviderError("SERP API key not configured")
        
        try:
            search = GoogleSearch({
                "q": query,
                "api_key": config.serp_api_key,
                "num": min(max_results, 10),
                "safe": "active"
            })
            
            results_dict = search.get_dict()
            
            if "error" in results_dict:
                raise SearchProviderError(f"SERP API error: {results_dict['error']}")
            
            results = []
            organic_results = results_dict.get("organic_results", [])
            
            for result in organic_results[:max_results]:
                url = result.get('link', '')
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                
                if url and title:
                    domain = self._extract_domain(url)
                    results.append(SearchResult(
                        url=url,
                        title=title,
                        snippet=snippet,
                        domain=domain,
                        source_provider='serp_api',
                        relevance_score=0.8  # SERP API generally high quality
                    ))
            
            return SearchResponse(
                results=results,
                provider_used='serp_api',
                query=query,
                total_results=len(results),
                processing_time=0.0  # Will be set by caller
            )
            
        except Exception as e:
            logger.debug(f"SERP API search failed: {str(e)}")
            raise SearchProviderError(f"SERP API failed: {str(e)}")
    
    async def _search_google_custom(self, query: str, max_results: int) -> Optional[SearchResponse]:
        """Search using Google Custom Search JSON API"""
        if not self._google_search_client or not config.google_search_api_key:
            raise SearchProviderError("Google Custom Search not configured")
        
        try:
            # Use asyncio to run blocking Google API call in thread pool
            loop = asyncio.get_event_loop()
            search_result = await loop.run_in_executor(
                None,
                lambda: self._google_search_client.cse().list(
                    q=query,
                    cx=config.google_search_engine_id,
                    num=min(max_results, 10),
                    safe='active'
                ).execute()
            )
            
            results = []
            items = search_result.get('items', [])
            
            for item in items[:max_results]:
                url = item.get('link', '')
                title = item.get('title', '')
                snippet = item.get('snippet', '')
                
                if url and title:
                    domain = self._extract_domain(url)
                    results.append(SearchResult(
                        url=url,
                        title=title,
                        snippet=snippet,
                        domain=domain,
                        source_provider='google_custom_search',
                        relevance_score=0.75  # Google Custom Search good quality
                    ))
            
            return SearchResponse(
                results=results,
                provider_used='google_custom_search',
                query=query,
                total_results=len(results),
                processing_time=0.0
            )
            
        except HttpError as e:
            logger.debug(f"Google Custom Search HTTP error: {str(e)}")
            raise SearchProviderError(f"Google Custom Search failed: {str(e)}")
        except Exception as e:
            logger.debug(f"Google Custom Search failed: {str(e)}")
            raise SearchProviderError(f"Google Custom Search failed: {str(e)}")
    
    async def _search_gcp_search(self, query: str, max_results: int) -> Optional[SearchResponse]:
        """Search using GCP Search JSON API"""
        if not self._gcp_search_client or not config.gcp_search_api_key:
            raise SearchProviderError("GCP Search not configured")
        
        try:
            # Use asyncio to run blocking Google API call in thread pool
            loop = asyncio.get_event_loop()
            search_result = await loop.run_in_executor(
                None,
                lambda: self._gcp_search_client.cse().list(
                    q=query,
                    cx=config.gcp_search_engine_id,
                    num=min(max_results, 10),
                    safe='active'
                ).execute()
            )
            
            results = []
            items = search_result.get('items', [])
            
            for item in items[:max_results]:
                url = item.get('link', '')
                title = item.get('title', '')
                snippet = item.get('snippet', '')
                
                if url and title:
                    domain = self._extract_domain(url)
                    results.append(SearchResult(
                        url=url,
                        title=title,
                        snippet=snippet,
                        domain=domain,
                        source_provider='gcp_search',
                        relevance_score=0.75  # GCP Search good quality
                    ))
            
            return SearchResponse(
                results=results,
                provider_used='gcp_search',
                query=query,
                total_results=len(results),
                processing_time=0.0
            )
            
        except HttpError as e:
            logger.debug(f"GCP Search HTTP error: {str(e)}")
            raise SearchProviderError(f"GCP Search failed: {str(e)}")
        except Exception as e:
            logger.debug(f"GCP Search failed: {str(e)}")
            raise SearchProviderError(f"GCP Search failed: {str(e)}")
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> Optional[SearchResponse]:
        """Search using DuckDuckGo with improved error handling"""
        try:
            # First try the duckduckgo-search library with better error handling
            search_results = await self._ddg_search_with_fallback(query, max_results)
            
            return SearchResponse(
                results=search_results,
                provider_used='duckduckgo',
                query=query,
                total_results=len(search_results),
                processing_time=0.0
            )
                
        except Exception as e:
            logger.debug(f"DuckDuckGo search failed: {str(e)}")
            # Check if it's a network error
            if any(err in str(e).lower() for err in ['connect', 'dns', 'network', 'timeout', 'resolve']):
                raise NetworkError(f"DuckDuckGo network error: {str(e)}")
            else:
                raise SearchProviderError(f"DuckDuckGo failed: {str(e)}")
    
    async def _ddg_search_with_fallback(self, query: str, max_results: int) -> List[SearchResult]:
        """DuckDuckGo search with better error handling and fallback"""
        search_results = []
        
        try:
            # Use asyncio to run blocking search with timeout
            loop = asyncio.get_event_loop()
            
            # Wrap the search in a timeout
            search_task = loop.run_in_executor(
                None,
                self._ddg_search_sync_safe,
                query,
                max_results
            )
            
            search_results = await asyncio.wait_for(search_task, timeout=self.network_timeout)
            
        except asyncio.TimeoutError:
            logger.warning(f"DuckDuckGo search timed out after {self.network_timeout}s")
            raise TimeoutError(f"DuckDuckGo search timed out")
        except Exception as e:
            logger.debug(f"DuckDuckGo search error: {str(e)}")
            raise e
        
        return search_results
    
    def _ddg_search_sync_safe(self, query: str, max_results: int) -> List[SearchResult]:
        """Safe synchronous DuckDuckGo search wrapper using correct API"""
        search_results = []
        
        try:
            # Set socket timeout for network operations
            import socket
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(self.network_timeout)
            
            try:
                # Use the correct DuckDuckGo API according to documentation
                ddgs = DDGS()
                results = ddgs.text(
                    keywords=query,
                    region='wt-wt',  # Worldwide
                    safesearch='moderate',  # Moderate safe search
                    max_results=max_results
                )
                
                # Process results - note the correct field names
                for result in results:
                    url = result.get('href', '')
                    title = result.get('title', '')
                    snippet = result.get('body', '')
                    
                    if url and title:
                        domain = self._extract_domain(url)
                        search_results.append(SearchResult(
                            url=url,
                            title=title,
                            snippet=snippet,
                            domain=domain,
                            source_provider='duckduckgo',
                            relevance_score=0.6  # DuckDuckGo decent quality
                        ))
                        
            finally:
                socket.setdefaulttimeout(original_timeout)
                
        except Exception as e:
            logger.debug(f"DuckDuckGo sync search error: {str(e)}")
            raise e
        
        return search_results
    
    async def _degraded_mode_search(self, query: str, max_results: int) -> Optional[SearchResponse]:
        """Provide degraded search results when all providers fail"""
        try:
            logger.info(f"Attempting degraded mode search for: {query}")
            
            # Strategy 1: Check cache for similar queries
            similar_results = await self._search_cache_similar_queries(query, max_results)
            if similar_results:
                return SearchResponse(
                    results=similar_results,
                    provider_used="cache_fallback",
                    query=query,
                    total_results=len(similar_results),
                    processing_time=0.0,
                    cache_hit=True
                )
            
            # Strategy 2: Provide curated fallback results for common queries
            fallback_results = self._get_fallback_results(query, max_results)
            if fallback_results:
                return SearchResponse(
                    results=fallback_results,
                    provider_used="curated_fallback",
                    query=query,
                    total_results=len(fallback_results),
                    processing_time=0.0
                )
            
            logger.debug("No degraded mode results available")
            return None
            
        except Exception as e:
            logger.debug(f"Degraded mode search failed: {str(e)}")
            return None
    
    async def _search_cache_similar_queries(self, query: str, max_results: int) -> List[SearchResult]:
        """Search cache for similar queries"""
        try:
            # Simple approach: look for cached results with similar keywords
            query_words = set(query.lower().split())
            
            # This would need to be implemented with actual cache scanning
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.debug(f"Cache search failed: {str(e)}")
            return []
    
    def _get_fallback_results(self, query: str, max_results: int) -> List[SearchResult]:
        """Provide curated fallback results for common query types"""
        try:
            query_lower = query.lower()
            results = []
            
            # Fact-checking related fallbacks
            if any(term in query_lower for term in ['fact check', 'verify', 'truth', 'false', 'misinformation']):
                results.extend([
                    SearchResult(
                        url="https://www.snopes.com",
                        title="Snopes.com - Fact Checking",
                        snippet="The definitive Internet reference source for urban legends, folklore, myths, rumors, and misinformation.",
                        domain="snopes.com",
                        source_provider="curated_fallback",
                        relevance_score=0.8
                    ),
                    SearchResult(
                        url="https://www.factcheck.org",
                        title="FactCheck.org - A Project of The Annenberg Public Policy Center",
                        snippet="We are a nonpartisan, nonprofit consumer advocate for voters that aims to reduce the level of deception and confusion in U.S. politics.",
                        domain="factcheck.org",
                        source_provider="curated_fallback",
                        relevance_score=0.8
                    ),
                    SearchResult(
                        url="https://www.politifact.com",
                        title="PolitiFact | The Poynter Institute",
                        snippet="PolitiFact is a fact-checking website that rates the accuracy of claims by elected officials and others on its Truth-O-Meter.",
                        domain="politifact.com",
                        source_provider="curated_fallback",
                        relevance_score=0.7
                    )
                ])
            
            # News and current events fallbacks
            elif any(term in query_lower for term in ['news', 'current', 'today', '2024', 'latest']):
                results.extend([
                    SearchResult(
                        url="https://www.reuters.com",
                        title="Reuters - Breaking International News & Views",
                        snippet="Reuters.com brings you the latest news from around the world, covering breaking news in business, politics, and more.",
                        domain="reuters.com",
                        source_provider="curated_fallback",
                        relevance_score=0.8
                    ),
                    SearchResult(
                        url="https://apnews.com",
                        title="Associated Press News",
                        snippet="The Associated Press is an independent global news organization dedicated to factual reporting.",
                        domain="apnews.com",
                        source_provider="curated_fallback",
                        relevance_score=0.8
                    ),
                    SearchResult(
                        url="https://www.bbc.com/news",
                        title="BBC News - Home",
                        snippet="Visit BBC News for up-to-the-minute news, breaking news, video, audio and feature stories.",
                        domain="bbc.com",
                        source_provider="curated_fallback",
                        relevance_score=0.7
                    )
                ])
            
            # Scientific/research fallbacks
            elif any(term in query_lower for term in ['research', 'study', 'scientific', 'science', 'medical']):
                results.extend([
                    SearchResult(
                        url="https://www.ncbi.nlm.nih.gov/pubmed",
                        title="PubMed - NCBI",
                        snippet="PubMed comprises more than 34 million citations for biomedical literature from MEDLINE, life science journals, and online books.",
                        domain="ncbi.nlm.nih.gov",
                        source_provider="curated_fallback",
                        relevance_score=0.8
                    ),
                    SearchResult(
                        url="https://scholar.google.com",
                        title="Google Scholar",
                        snippet="Google Scholar provides a simple way to broadly search for scholarly literature across many disciplines and sources.",
                        domain="scholar.google.com",
                        source_provider="curated_fallback",
                        relevance_score=0.7
                    )
                ])
            
            return results[:max_results]
            
        except Exception as e:
            logger.debug(f"Fallback results generation failed: {str(e)}")
            return []
    
    def _get_provider_priority(self) -> List[str]:
        """Get provider priority based on health and configuration"""
        available_providers = []
        
        # Check SERP API availability
        if config.serp_api_key:
            available_providers.append('serp_api')
        
        # Check Google Custom Search availability
        if config.google_search_api_key and config.google_search_engine_id and self._google_search_client:
            available_providers.append('google_custom_search')
        
        # Check GCP Search availability
        if config.gcp_search_api_key and config.gcp_search_engine_id and self._gcp_search_client:
            available_providers.append('gcp_search')
        
        # DuckDuckGo is always available (no API key required)
        available_providers.append('duckduckgo')
        
        # Sort by health (fewer consecutive failures first)
        available_providers.sort(key=lambda p: self.provider_health[p]['consecutive_failures'])
        
        return available_providers
    
    def _is_provider_healthy(self, provider: str) -> bool:
        """Check if provider is healthy enough to use"""
        health = self.provider_health[provider]
        
        # Provider is unhealthy if it has more than 5 consecutive failures
        # and last failure was within the last 5 minutes
        if health['consecutive_failures'] > 5:
            last_success = health.get('last_success')
            if not last_success or (datetime.now() - last_success).total_seconds() > 300:
                return False
        
        return True
    
    def _update_provider_health(self, provider: str, success: bool):
        """Update provider health metrics"""
        health = self.provider_health[provider]
        
        if success:
            health['last_success'] = datetime.now()
            health['consecutive_failures'] = 0
        else:
            health['consecutive_failures'] += 1
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().replace('www.', '')
        except:
            return ''
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get provider health and usage statistics"""
        return {
            'provider_health': self.provider_health,
            'available_providers': self._get_provider_priority(),
            'configuration': {
                'serp_api_configured': bool(config.serp_api_key),
                'google_custom_search_configured': bool(config.google_search_api_key and config.google_search_engine_id),
                'gcp_search_configured': bool(config.gcp_search_api_key and config.gcp_search_engine_id),
                'duckduckgo_available': True
            }
        }

# Global search service instance
unified_search_service = UnifiedSearchService()

async def search_with_fallback(query: str, max_results: int = 10) -> SearchResponse:
    """
    Convenience function for searching with automatic fallback
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        SearchResponse with results from the best available provider
    """
    return await unified_search_service.search(query, max_results)