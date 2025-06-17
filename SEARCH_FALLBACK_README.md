# Search Provider Fallback System

This document describes the robust search provider fallback system implemented in the Fact Check Agent to ensure continuous operation even when primary search services fail.

## Overview

The Fact Check Agent now includes a unified search service that automatically falls back between multiple search providers:

1. **SERP API** (Primary) - High-quality commercial search API
2. **Google Custom Search** (Fallback) - Google's official search API
3. **DuckDuckGo** (Final Fallback) - Free search service, always available

## Architecture

### Unified Search Service (`search_services.py`)

The `UnifiedSearchService` class provides:
- **Automatic Failover**: Seamlessly switches between providers when one fails
- **Health Monitoring**: Tracks provider performance and consecutive failures
- **Intelligent Caching**: Caches results to reduce API calls and improve performance
- **Rate Limiting**: Respects provider limits and implements backoff strategies
- **Quality Scoring**: Assigns relevance scores based on provider capabilities

### Search Provider Priority

The system uses a smart priority system:

```
1. SERP API (if configured and healthy)
   ├─ Highest quality results
   ├─ Commercial grade reliability
   └─ Best for fact-checking accuracy

2. Google Custom Search (if configured and healthy)
   ├─ Google's search index
   ├─ Good quality results
   └─ More affordable than SERP API

3. DuckDuckGo (always available)
   ├─ Free tier search
   ├─ No API key required
   └─ Final safety net
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure your API keys:

```bash
# Primary Search Provider
SERP_API_KEY=your-serp-api-key-here

# Fallback Search Provider
GOOGLE_SEARCH_API_KEY=your-google-search-api-key
GOOGLE_SEARCH_ENGINE_ID=your-custom-search-engine-id

# DuckDuckGo - No configuration needed (always available)
```

### API Key Setup

#### 1. SERP API (Recommended Primary)
```bash
# Sign up at https://serpapi.com/
# Free tier: 100 searches/month
# Paid plans: Start at $50/month for 5,000 searches

# Add to .env:
SERP_API_KEY=your_serp_api_key_here
```

#### 2. Google Custom Search (Recommended Fallback)
```bash
# 1. Go to Google Cloud Console
# 2. Enable "Custom Search JSON API"
# 3. Create API credentials (API key)
# 4. Create Custom Search Engine at https://cse.google.com/
# Free tier: 100 searches/day
# Paid: $5 per 1,000 queries

# Add to .env:
GOOGLE_SEARCH_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
```

#### 3. DuckDuckGo (Automatic Fallback)
```bash
# No setup required!
# Automatically available as final fallback
# No API key needed
# Rate limited but free
```

## Usage

### Basic Search

```python
from src.fact_check_agent.search_services import unified_search_service

# Automatic fallback search
response = await unified_search_service.search("climate change facts", max_results=10)

print(f"Provider used: {response.provider_used}")
print(f"Results found: {len(response.results)}")
print(f"Cache hit: {response.cache_hit}")
```

### Integration with Fact Checker

The fact checker automatically uses the unified search service:

```python
from src.fact_check_agent.fact_check_agent import get_fact_check_agent

agent = get_fact_check_agent()

# Fact checking automatically uses fallback search
result = await agent.fact_check_text("COVID-19 vaccines are 95% effective")

# Check which search provider was used
search_stats = agent.get_search_provider_stats()
print(search_stats)
```

### Monitoring Provider Health

```python
from src.fact_check_agent.search_services import unified_search_service

# Get provider statistics
stats = unified_search_service.get_provider_stats()

print("Provider Health:")
for provider, health in stats['provider_health'].items():
    failures = health['consecutive_failures']
    status = "Healthy" if failures == 0 else f"{failures} consecutive failures"
    print(f"  {provider}: {status}")

print(f"Available providers: {stats['available_providers']}")
```

## Error Handling

### Provider Failure Scenarios

1. **SERP API Rate Limit Exceeded**
   ```
   INFO: SERP API rate limit reached, falling back to Google Custom Search
   INFO: Search via google_custom_search: 8 sources
   ```

2. **Google Custom Search Quota Exceeded**
   ```
   INFO: Google Custom Search quota exceeded, falling back to DuckDuckGo
   INFO: Search via duckduckgo: 5 sources
   ```

3. **All Providers Fail**
   ```
   ERROR: All search providers failed. Last error: DuckDuckGo failed: Rate limited
   ```

### Health Recovery

The system automatically recovers when providers become healthy again:

```python
# Provider health is tracked automatically
# After 5+ consecutive failures, provider is marked unhealthy
# Successful requests reset the failure count
# Unhealthy providers are deprioritized but not completely skipped
```

## Performance Features

### Intelligent Caching

- **Search Results**: Cached for 30 minutes to reduce API calls
- **Content Extraction**: Cached based on URL and domain
- **Cache Statistics**: Available through provider stats

### Concurrent Processing

- **Parallel Searches**: Multiple queries processed simultaneously
- **Async Operations**: Non-blocking search operations
- **Connection Pooling**: Reuses HTTP connections for efficiency

### Quality Scoring

Different providers receive different relevance scores:
- **SERP API**: 0.8 (highest quality)
- **Google Custom Search**: 0.75 (good quality)
- **DuckDuckGo**: 0.6 (decent quality)

## Testing

### Run Fallback Tests

```bash
# Run comprehensive test suite
python -m pytest tests/test_search_fallback.py -v

# Run demo script
python examples/demo_search_fallback.py
```

### Test Scenarios

The test suite covers:
- ✅ Primary provider success
- ✅ Fallback to secondary provider
- ✅ Final fallback to DuckDuckGo
- ✅ Provider health tracking
- ✅ Cache functionality
- ✅ All providers failure handling

## Monitoring and Logging

### Log Messages

The system provides detailed logging:

```bash
INFO: 🔍 Unified search: climate change facts...
INFO: ✅ Search success with serp_api: 8 results in 1.23s
INFO: 🎯 Cache HIT for unified search: climate change facts...
WARNING: Provider serp_api failed: Rate limit exceeded
INFO: 🔍 Search via google_custom_search: 6 sources
```

### Performance Metrics

Access detailed metrics through the agent:

```python
agent = get_fact_check_agent()

# Performance metrics
perf_metrics = agent.get_performance_metrics()

# Search provider statistics
search_stats = agent.get_search_provider_stats()

# Combined report
print("System Status:")
print(f"Cache hit rate: {search_stats.get('cache_hit_rate', 'N/A')}")
print(f"Primary provider health: {search_stats['provider_health']['serp_api']}")
```

## Cost Optimization

### API Usage Strategy

1. **Use Caching Aggressively**
   - 30-minute cache for search results
   - Reduces API calls by 60-80% typically

2. **Smart Provider Selection**
   - Use cheaper providers when possible
   - Fall back to free DuckDuckGo for less critical queries

3. **Rate Limit Awareness**
   - Automatic backoff when limits approached
   - Switch to alternative providers before exhaustion

### Cost Comparison

| Provider | Free Tier | Paid Pricing | Quality |
|----------|-----------|--------------|---------|
| SERP API | 100/month | $50/5K queries | Highest |
| Google Custom Search | 100/day | $5/1K queries | High |
| DuckDuckGo | Unlimited* | Free | Good |

*Rate limited, but sufficient for most use cases

## Troubleshooting

### Common Issues

1. **No Search Results**
   ```bash
   # Check API key configuration
   python -c "from src.fact_check_agent.config import config; print(f'SERP: {bool(config.serp_api_key)}, Google: {bool(config.google_search_api_key)}')"
   ```

2. **High API Costs**
   ```bash
   # Monitor cache hit rates
   # Consider using only free DuckDuckGo for testing
   SERP_API_KEY="" GOOGLE_SEARCH_API_KEY="" python main.py
   ```

3. **Rate Limiting**
   ```bash
   # Check provider health
   python examples/demo_search_fallback.py
   ```

### Debug Mode

Enable debug logging to see detailed provider selection:

```python
import logging
logging.getLogger('src.fact_check_agent.search_services').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features

- **Additional Providers**: Bing Search API, Brave Search API
- **Smart Load Balancing**: Distribute queries across providers
- **Cost Optimization**: Automatic provider selection based on query importance
- **Analytics Dashboard**: Web interface for monitoring provider usage

### Contributing

To add a new search provider:

1. Extend `UnifiedSearchService` class
2. Add provider-specific search method
3. Update priority logic in `_get_provider_priority()`
4. Add configuration variables
5. Create tests for the new provider

## Support

For issues with the search fallback system:

1. Check API key configuration in `.env`
2. Run the demo script to test connectivity
3. Review logs for specific error messages
4. Check provider health stats
5. Verify network connectivity and firewall settings

The search fallback system ensures your fact-checking operations continue uninterrupted, providing a robust foundation for reliable information verification.