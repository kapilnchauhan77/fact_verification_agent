"""
Enhanced content extraction system with multiple fallback methods
Fixes the content extraction bottleneck (24.7% of total time)
"""
import asyncio
import aiohttp
import logging
import random
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import hashlib
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from newspaper import Article
import feedparser
from readability.readability import Document

from .performance_cache import content_cache
from .checkpoint_monitor import TimedCheckpoint

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Result of content extraction attempt"""
    content: str
    method: str
    success: bool
    duration: float
    error: Optional[str] = None

class EnhancedContentExtractor:
    """Ultra-fast content extraction with multiple fallback methods"""
    
    def __init__(self):
        """Initialize enhanced content extractor"""
        
        # Optimized user agents for different extraction methods
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]
        
        # Optimized extraction settings
        self.timeout = 2  # Aggressive timeout
        self.max_content_length = 10000  # Limit content size
        self.min_content_length = 100  # Minimum useful content
        self.concurrent_limit = 6  # Concurrent extraction attempts
        
        # Thread pool for CPU-bound operations
        self.thread_pool = ThreadPoolExecutor(max_workers=3)
        
        # Session pool for connection reuse
        self.session_pool = []
        for _ in range(3):
            session = requests.Session()
            session.headers.update({
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'DNT': '1',
                'Cache-Control': 'max-age=0'
            })
            self.session_pool.append(session)
        
        # Enhanced selectors for different content types
        self.content_selectors = {
            'news': [
                'article', '.article-content', '.entry-content', '.post-content',
                '.story-body', '.article-body', '.content-body', '[class*="article"]',
                '.main-content', 'main', '.primary-content', '.story-content'
            ],
            'academic': [
                '.abstract', '.article-content', '.full-text', '.paper-content',
                '.document-content', '.publication-content', 'article', 'main'
            ],
            'medical': [
                '.medical-content', '.health-content', '.article-content', 'article',
                '.content-area', '.main-content', 'main', '.primary-content'
            ],
            'government': [
                '.content', '.main-content', '.page-content', '.document-content',
                'article', 'main', '.body-content', '.text-content'
            ],
            'general': [
                'article', '.content', '.main-content', '.post-content',
                '.entry-content', 'main', '.primary-content', '.body-content'
            ]
        }
        
        # Domain-specific extraction strategies
        self.domain_strategies = {
            'reuters.com': 'news',
            'apnews.com': 'news',
            'bbc.com': 'news',
            'npr.org': 'news',
            'cnn.com': 'news',
            'who.int': 'medical',
            'cdc.gov': 'medical',
            'nih.gov': 'medical',
            'nature.com': 'academic',
            'science.org': 'academic',
            'ncbi.nlm.nih.gov': 'academic',
            'gov': 'government',
            'edu': 'academic'
        }
    
    async def extract_content_optimized(self, url: str, domain: str = "") -> ExtractionResult:
        """Ultra-optimized content extraction with multiple concurrent methods"""
        
        # Check cache first
        cache_key = f"enhanced_{hashlib.md5(url.encode()).hexdigest()}"
        cached_result = content_cache.get(cache_key)
        if cached_result:
            logger.debug(f"🎯 Enhanced cache HIT for: {domain}")
            return ExtractionResult(
                content=cached_result,
                method="cache",
                success=True,
                duration=0.001
            )
        
        start_time = time.time()
        
        # Determine extraction strategy based on domain
        strategy = self._get_extraction_strategy(domain)
        
        # Create concurrent extraction tasks
        extraction_tasks = [
            self._extract_with_aiohttp_enhanced(url, strategy),
            self._extract_with_requests_optimized(url, strategy),
            self._extract_with_newspaper_fast(url)
        ]
        
        # Add readability extraction for complex sites
        if strategy in ['news', 'academic']:
            extraction_tasks.append(self._extract_with_readability(url))
        
        try:
            # Run extractions concurrently with timeout
            results = await asyncio.wait_for(
                asyncio.gather(*extraction_tasks, return_exceptions=True),
                timeout=self.timeout * 2  # Total timeout for all methods
            )
            
            # Find best result
            best_result = self._select_best_result(results)
            
            if best_result and best_result.success:
                # Cache successful extraction for 2 hours
                content_cache.set(cache_key, best_result.content, ttl=7200)
                
                duration = time.time() - start_time
                logger.debug(f"✅ Enhanced extraction success: {domain} ({best_result.method}, {duration:.3f}s)")
                
                return ExtractionResult(
                    content=best_result.content,
                    method=best_result.method,
                    success=True,
                    duration=duration
                )
            
        except asyncio.TimeoutError:
            logger.debug(f"⏱️ Enhanced extraction timeout for: {domain}")
        except Exception as e:
            logger.debug(f"❌ Enhanced extraction error for {domain}: {str(e)}")
        
        duration = time.time() - start_time
        logger.debug(f"🚫 Enhanced extraction failed: {domain} ({duration:.3f}s)")
        
        return ExtractionResult(
            content="",
            method="failed",
            success=False,
            duration=duration,
            error="All extraction methods failed"
        )
    
    def _get_extraction_strategy(self, domain: str) -> str:
        """Determine optimal extraction strategy for domain"""
        domain_lower = domain.lower()
        
        # Check specific domains
        for pattern, strategy in self.domain_strategies.items():
            if pattern in domain_lower:
                return strategy
        
        # Default strategy
        return 'general'
    
    async def _extract_with_aiohttp_enhanced(self, url: str, strategy: str) -> ExtractionResult:
        """Enhanced aiohttp extraction with smart selectors"""
        start_time = time.time()
        
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.google.com/',
                'DNT': '1',
                'Cache-Control': 'max-age=0'
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    async with session.get(url, headers=headers, ssl=True) as response:
                        if response.status != 200:
                            raise Exception(f"HTTP {response.status}")
                        
                        html = await response.text()
                except aiohttp.ClientSSLError:
                    # Fallback: Try without SSL verification as last resort
                    logger.warning(f"SSL verification failed for {url}, attempting without verification")
                    async with session.get(url, headers=headers, ssl=False) as response:
                        if response.status != 200:
                            raise Exception(f"HTTP {response.status}")
                        
                        html = await response.text()
                    
                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove unwanted elements
                    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                        element.decompose()
                    
                    # Try strategy-specific selectors
                    content = self._extract_with_selectors(soup, strategy)
                    
                    if not content or len(content) < self.min_content_length:
                        # Fallback to body text
                        content = soup.get_text(strip=True, separator=' ')
                    
                    if len(content) < self.min_content_length:
                        raise Exception("Content too short")
                    
                    # Truncate for performance
                    content = content[:self.max_content_length]
                    
                    duration = time.time() - start_time
                    return ExtractionResult(
                        content=content,
                        method="aiohttp_enhanced",
                        success=True,
                        duration=duration
                    )
                    
        except Exception as e:
            duration = time.time() - start_time
            return ExtractionResult(
                content="",
                method="aiohttp_enhanced",
                success=False,
                duration=duration,
                error=str(e)
            )
    
    async def _extract_with_requests_optimized(self, url: str, strategy: str) -> ExtractionResult:
        """Optimized requests extraction with smart headers"""
        start_time = time.time()
        
        try:
            # Run in thread pool to avoid blocking
            def _sync_extract():
                session = random.choice(self.session_pool)
                
                # Randomize headers
                headers = session.headers.copy()
                headers['User-Agent'] = random.choice(self.user_agents)
                headers['Referer'] = 'https://www.google.com/'
                
                try:
                    response = session.get(
                        url, 
                        headers=headers, 
                        timeout=self.timeout,
                        allow_redirects=True,
                        verify=True  # Enable SSL certificate verification
                    )
                    response.raise_for_status()
                except requests.exceptions.SSLError:
                    # Fallback: Try without SSL verification as last resort
                    logger.warning(f"SSL verification failed for {url}, attempting without verification")
                    response = session.get(
                        url, 
                        headers=headers, 
                        timeout=self.timeout,
                        allow_redirects=True,
                        verify=False
                    )
                    response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    element.decompose()
                
                # Extract with strategy-specific selectors
                content = self._extract_with_selectors(soup, strategy)
                
                if not content or len(content) < self.min_content_length:
                    content = soup.get_text(strip=True, separator=' ')
                
                if len(content) < self.min_content_length:
                    raise Exception("Content too short")
                
                return content[:self.max_content_length]
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(self.thread_pool, _sync_extract)
            
            duration = time.time() - start_time
            return ExtractionResult(
                content=content,
                method="requests_optimized",
                success=True,
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return ExtractionResult(
                content="",
                method="requests_optimized",
                success=False,
                duration=duration,
                error=str(e)
            )
    
    async def _extract_with_newspaper_fast(self, url: str) -> ExtractionResult:
        """Fast newspaper3k extraction with optimized settings"""
        start_time = time.time()
        
        try:
            def _sync_newspaper_extract():
                article = Article(url)
                
                # Optimized configuration
                article.config.request_timeout = self.timeout
                article.config.browser_user_agent = random.choice(self.user_agents)
                article.config.fetch_images = False  # Skip images for speed
                article.config.memoize_articles = False  # Disable caching
                
                article.download()
                article.parse()
                
                if not article.text or len(article.text) < self.min_content_length:
                    raise Exception("Article text too short")
                
                return article.text[:self.max_content_length]
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(self.thread_pool, _sync_newspaper_extract)
            
            duration = time.time() - start_time
            return ExtractionResult(
                content=content,
                method="newspaper_fast",
                success=True,
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return ExtractionResult(
                content="",
                method="newspaper_fast",
                success=False,
                duration=duration,
                error=str(e)
            )
    
    async def _extract_with_readability(self, url: str) -> ExtractionResult:
        """Readability-based extraction for complex layouts"""
        start_time = time.time()
        
        try:
            def _sync_readability_extract():
                session = random.choice(self.session_pool)
                response = session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # Use readability to extract main content
                doc = Document(response.content)
                content = doc.summary()
                
                # Parse the HTML content
                soup = BeautifulSoup(content, 'html.parser')
                text_content = soup.get_text(strip=True, separator=' ')
                
                if len(text_content) < self.min_content_length:
                    raise Exception("Readability content too short")
                
                return text_content[:self.max_content_length]
            
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(self.thread_pool, _sync_readability_extract)
            
            duration = time.time() - start_time
            return ExtractionResult(
                content=content,
                method="readability",
                success=True,
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return ExtractionResult(
                content="",
                method="readability",
                success=False,
                duration=duration,
                error=str(e)
            )
    
    def _extract_with_selectors(self, soup: BeautifulSoup, strategy: str) -> str:
        """Extract content using strategy-specific selectors"""
        selectors = self.content_selectors.get(strategy, self.content_selectors['general'])
        
        content = ""
        for selector in selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join([elem.get_text(strip=True, separator=' ') for elem in elements])
                    if len(content) > self.min_content_length:
                        break
            except Exception:
                continue
        
        return content
    
    def _select_best_result(self, results: List[Any]) -> Optional[ExtractionResult]:
        """Select the best extraction result from multiple attempts"""
        valid_results = []
        
        for result in results:
            if isinstance(result, ExtractionResult) and result.success:
                valid_results.append(result)
        
        if not valid_results:
            return None
        
        # Sort by content length (longer is generally better for news articles)
        valid_results.sort(key=lambda x: len(x.content), reverse=True)
        
        # Prefer certain methods if content length is similar
        method_priorities = {
            'newspaper_fast': 3,
            'readability': 2,
            'aiohttp_enhanced': 1,
            'requests_optimized': 0
        }
        
        best_result = valid_results[0]
        for result in valid_results:
            # If content length is within 20% and method is preferred
            if (len(result.content) >= len(best_result.content) * 0.8 and
                method_priorities.get(result.method, 0) > method_priorities.get(best_result.method, 0)):
                best_result = result
        
        return best_result
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction performance statistics"""
        cache_stats = content_cache.stats()
        
        return {
            'cache_stats': cache_stats,
            'configuration': {
                'timeout': self.timeout,
                'max_content_length': self.max_content_length,
                'min_content_length': self.min_content_length,
                'concurrent_limit': self.concurrent_limit,
                'user_agents_count': len(self.user_agents),
                'session_pool_size': len(self.session_pool)
            },
            'extraction_methods': [
                'aiohttp_enhanced',
                'requests_optimized', 
                'newspaper_fast',
                'readability'
            ]
        }

# Global enhanced content extractor instance
enhanced_extractor = EnhancedContentExtractor()

async def extract_content_ultra_fast(url: str, domain: str = "") -> str:
    """Ultra-fast content extraction function"""
    result = await enhanced_extractor.extract_content_optimized(url, domain)
    return result.content if result.success else ""