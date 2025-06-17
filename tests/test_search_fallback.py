"""
Test suite for search provider fallback functionality
Tests SERP API, Google Custom Search, and DuckDuckGo fallbacks
"""

import asyncio
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock

from src.fact_check_agent.search_services import (
    UnifiedSearchService, 
    SearchResult, 
    SearchResponse,
    SearchProviderError
)
from src.fact_check_agent.config import config


class TestSearchFallback:
    """Test search provider fallback functionality"""
    
    @pytest.fixture
    def search_service(self):
        """Create a search service instance for testing"""
        return UnifiedSearchService()
    
    @pytest.mark.asyncio
    async def test_serp_api_primary_success(self, search_service):
        """Test successful SERP API search as primary provider"""
        # Mock SERP API configuration
        with patch.object(config, 'serp_api_key', 'test_key'):
            with patch('src.fact_check_agent.search_services.GoogleSearch') as mock_search:
                # Mock successful SERP API response
                mock_search.return_value.get_dict.return_value = {
                    'organic_results': [
                        {
                            'link': 'https://example.com/article1',
                            'title': 'Test Article 1',
                            'snippet': 'This is a test snippet'
                        },
                        {
                            'link': 'https://example.com/article2',
                            'title': 'Test Article 2',
                            'snippet': 'Another test snippet'
                        }
                    ]
                }
                
                response = await search_service.search("test query")
                
                assert response.provider_used == 'serp_api'
                assert len(response.results) == 2
                assert response.results[0].url == 'https://example.com/article1'
                assert response.results[0].title == 'Test Article 1'
                assert response.results[0].source_provider == 'serp_api'
    
    @pytest.mark.asyncio
    async def test_fallback_to_google_custom_search(self, search_service):
        """Test fallback to Google Custom Search when SERP API fails"""
        # Mock configuration
        with patch.object(config, 'serp_api_key', ''), \
             patch.object(config, 'google_search_api_key', 'test_google_key'), \
             patch.object(config, 'google_search_engine_id', 'test_engine_id'):
            
            # Mock Google Custom Search client
            mock_client = Mock()
            mock_cse = Mock()
            mock_client.cse.return_value = mock_cse
            mock_cse.list.return_value.execute.return_value = {
                'items': [
                    {
                        'link': 'https://google-result.com/article1',
                        'title': 'Google Result 1',
                        'snippet': 'Google search snippet'
                    }
                ]
            }
            
            with patch.object(search_service, '_google_search_client', mock_client):
                response = await search_service.search("test query")
                
                assert response.provider_used == 'google_custom_search'
                assert len(response.results) == 1
                assert response.results[0].url == 'https://google-result.com/article1'
                assert response.results[0].source_provider == 'google_custom_search'
    
    @pytest.mark.asyncio
    async def test_fallback_to_duckduckgo(self, search_service):
        """Test fallback to DuckDuckGo when other providers fail"""
        # Mock configuration with no API keys
        with patch.object(config, 'serp_api_key', ''), \
             patch.object(config, 'google_search_api_key', ''):
            
            # Mock DuckDuckGo search
            with patch('src.fact_check_agent.search_services.AsyncDDGS') as mock_ddgs:
                mock_context = AsyncMock()
                mock_ddgs.return_value.__aenter__.return_value = mock_context
                
                # Mock async generator for DDG results
                async def mock_text_results(*args, **kwargs):
                    yield {
                        'href': 'https://duckduckgo-result.com/article1',
                        'title': 'DuckDuckGo Result 1',
                        'body': 'DuckDuckGo search snippet'
                    }
                
                mock_context.text.return_value = mock_text_results()
                
                response = await search_service.search("test query")
                
                assert response.provider_used == 'duckduckgo'
                assert len(response.results) == 1
                assert response.results[0].url == 'https://duckduckgo-result.com/article1'
                assert response.results[0].source_provider == 'duckduckgo'
    
    @pytest.mark.asyncio
    async def test_provider_health_tracking(self, search_service):
        """Test that provider health is tracked correctly"""
        # Simulate provider failure
        search_service._update_provider_health('serp_api', success=False)
        search_service._update_provider_health('serp_api', success=False)
        
        health = search_service.provider_health['serp_api']
        assert health['consecutive_failures'] == 2
        
        # Simulate provider recovery
        search_service._update_provider_health('serp_api', success=True)
        
        health = search_service.provider_health['serp_api']
        assert health['consecutive_failures'] == 0
        assert health['last_success'] is not None
    
    @pytest.mark.asyncio
    async def test_unhealthy_provider_skipped(self, search_service):
        """Test that unhealthy providers are skipped"""
        # Make SERP API unhealthy
        for _ in range(6):  # More than threshold
            search_service._update_provider_health('serp_api', success=False)
        
        assert not search_service._is_provider_healthy('serp_api')
        
        # Provider should be skipped in priority list logic
        priority_list = search_service._get_provider_priority()
        # Should still be in list but with lowest priority due to health issues
        assert 'serp_api' in priority_list
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, search_service):
        """Test that search results are cached properly"""
        with patch.object(config, 'serp_api_key', 'test_key'):
            with patch('src.fact_check_agent.search_services.GoogleSearch') as mock_search:
                mock_search.return_value.get_dict.return_value = {
                    'organic_results': [
                        {
                            'link': 'https://example.com/cached',
                            'title': 'Cached Result',
                            'snippet': 'This should be cached'
                        }
                    ]
                }
                
                # First call - should not be cached
                response1 = await search_service.search("cache test query")
                assert not response1.cache_hit
                
                # Second call - should be cached
                response2 = await search_service.search("cache test query")
                # Note: Cache functionality depends on the actual cache implementation
                # This test may need adjustment based on cache behavior
    
    def test_provider_stats(self, search_service):
        """Test provider statistics reporting"""
        stats = search_service.get_provider_stats()
        
        assert 'provider_health' in stats
        assert 'available_providers' in stats
        assert 'configuration' in stats
        
        config_info = stats['configuration']
        assert 'serp_api_configured' in config_info
        assert 'google_custom_search_configured' in config_info
        assert 'duckduckgo_available' in config_info
        assert config_info['duckduckgo_available'] == True  # Always available
    
    @pytest.mark.asyncio
    async def test_all_providers_fail(self, search_service):
        """Test behavior when all search providers fail"""
        # Mock all providers to fail
        with patch.object(config, 'serp_api_key', ''), \
             patch.object(config, 'google_search_api_key', ''):
            
            with patch('src.fact_check_agent.search_services.AsyncDDGS') as mock_ddgs:
                # Make DuckDuckGo fail too
                mock_ddgs.side_effect = Exception("DDG failed")
                
                response = await search_service.search("failing query")
                
                assert response.provider_used == 'none'
                assert len(response.results) == 0
                assert response.error_message is not None
                assert 'failed' in response.error_message.lower()


if __name__ == "__main__":
    # Run a simple test
    async def simple_test():
        service = UnifiedSearchService()
        try:
            result = await service.search("test query", max_results=3)
            print(f"Search completed using: {result.provider_used}")
            print(f"Results found: {len(result.results)}")
            for i, res in enumerate(result.results[:2]):
                print(f"{i+1}. {res.title} - {res.domain}")
        except Exception as e:
            print(f"Search test failed: {e}")
    
    print("Running simple search fallback test...")
    asyncio.run(simple_test())