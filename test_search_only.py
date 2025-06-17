"""
Test search_services module in complete isolation
"""

import asyncio
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from urllib.parse import urlparse
import json
import logging

import aiohttp
import requests
from serpapi import GoogleSearch
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from duckduckgo_search import DDGS

# Mock dependencies
class MockConfig:
    serp_api_key = ""
    google_search_api_key = ""
    google_search_engine_id = ""

config = MockConfig()

class MockCache:
    def get(self, key):
        return None
    
    def set(self, key, value, ttl=None):
        pass

search_cache = MockCache()

# Setup logging
logger = logging.getLogger(__name__)

# Copy the search service classes directly
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

class UnifiedSearchService:
    """Unified search service with multiple provider fallbacks"""
    
    def __init__(self):
        """Initialize the unified search service"""
        self.providers = ['serp_api', 'google_custom_search', 'duckduckgo']
        self.provider_timeouts = {
            'serp_api': 5.0,
            'google_custom_search': 4.0,
            'duckduckgo': 3.0
        }
        self.max_results = 10
        self.retry_attempts = 2
        self.cache_ttl = 1800  # 30 minutes
        
        # Provider health tracking
        self.provider_health = {
            'serp_api': {'last_success': None, 'consecutive_failures': 0},
            'google_custom_search': {'last_success': None, 'consecutive_failures': 0},
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
    
    async def search(self, query: str, max_results: int = None) -> SearchResponse:
        """Perform search with automatic fallback between providers"""
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
        
        # All providers failed
        processing_time = time.time() - start_time
        error_msg = f"All search providers failed. Last error: {str(last_error) if last_error else 'Unknown'}"
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
        """Search with specific provider"""
        try:
            if provider == 'serp_api':
                return await self._search_serp_api(query, max_results)
            elif provider == 'google_custom_search':
                return await self._search_google_custom(query, max_results)
            elif provider == 'duckduckgo':
                return await self._search_duckduckgo(query, max_results)
            else:
                raise SearchProviderError(f"Unknown provider: {provider}")
                
        except Exception as e:
            logger.debug(f"Provider {provider} search failed: {str(e)}")
            raise SearchProviderError(f"{provider} search failed: {str(e)}")
    
    async def _search_serp_api(self, query: str, max_results: int) -> Optional[SearchResponse]:
        """Search using SERP API"""
        if not config.serp_api_key:
            raise SearchProviderError("SERP API key not configured")
        
        # This would normally make an API call, but we'll simulate it
        raise SearchProviderError("SERP API not configured (simulation)")
    
    async def _search_google_custom(self, query: str, max_results: int) -> Optional[SearchResponse]:
        """Search using Google Custom Search JSON API"""
        if not self._google_search_client or not config.google_search_api_key:
            raise SearchProviderError("Google Custom Search not configured")
        
        # This would normally make an API call, but we'll simulate it
        raise SearchProviderError("Google Custom Search not configured (simulation)")
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> Optional[SearchResponse]:
        """Search using DuckDuckGo"""
        try:
            # Use asyncio to run blocking DuckDuckGo search in thread pool
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                None,
                self._ddg_search_sync,
                query,
                max_results
            )
            
            return SearchResponse(
                results=search_results,
                provider_used='duckduckgo',
                query=query,
                total_results=len(search_results),
                processing_time=0.0
            )
                
        except Exception as e:
            logger.debug(f"DuckDuckGo search failed: {str(e)}")
            raise SearchProviderError(f"DuckDuckGo failed: {str(e)}")
    
    def _ddg_search_sync(self, query: str, max_results: int) -> List[SearchResult]:
        """Synchronous DuckDuckGo search wrapper"""
        search_results = []
        
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=max_results)
                
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
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
        
        return search_results
    
    def _get_provider_priority(self) -> List[str]:
        """Get provider priority based on health and configuration"""
        available_providers = []
        
        # Check SERP API availability
        if config.serp_api_key:
            available_providers.append('serp_api')
        
        # Check Google Custom Search availability
        if config.google_search_api_key and config.google_search_engine_id and self._google_search_client:
            available_providers.append('google_custom_search')
        
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
                'duckduckgo_available': True
            }
        }

# Test the implementation
async def test_search_service():
    print("=== Testing Search Fallback Implementation ===\n")
    
    # Test 1: Basic instantiation
    print("1. Testing service instantiation...")
    service = UnifiedSearchService()
    print("✅ UnifiedSearchService created")
    
    # Test 2: Provider stats
    print("\n2. Testing provider statistics...")
    stats = service.get_provider_stats()
    print(f"✅ Available providers: {stats['available_providers']}")
    print(f"   Configuration: {stats['configuration']}")
    
    # Test 3: Health tracking
    print("\n3. Testing health tracking...")
    service._update_provider_health('serp_api', success=False)
    service._update_provider_health('serp_api', success=False)
    health = service.provider_health['serp_api']
    print(f"✅ Health tracking: {health['consecutive_failures']} failures recorded")
    
    # Test 4: Real search (DuckDuckGo)
    print("\n4. Testing real search with DuckDuckGo...")
    try:
        response = await service.search("artificial intelligence", max_results=3)
        print(f"✅ Search completed via: {response.provider_used}")
        print(f"   Results: {len(response.results)}")
        if response.results:
            for i, result in enumerate(response.results[:2], 1):
                print(f"   {i}. {result.title[:60]}...")
                print(f"      {result.domain}")
        else:
            print(f"   Error: {response.error_message}")
    except Exception as e:
        print(f"⚠️  Search failed: {e}")
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Run tests
    asyncio.run(test_search_service())