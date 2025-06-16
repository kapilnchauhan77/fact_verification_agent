"""
Fact-checking module that verifies claims against multiple sources
"""
import asyncio
import aiohttp
import logging
import re
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urljoin, urlparse
import hashlib

import requests
from bs4 import BeautifulSoup
from newspaper import Article
from serpapi import GoogleSearch
from tqdm.asyncio import tqdm
import random

from src.fact_check_agent.config from src.fact_check_agent import config, FACT_CHECK_SOURCES
from src.fact_check_agent.claim_extractor import Claim, ClaimType
from src.fact_check_agent.checkpoint_monitor import TimedCheckpoint, start_checkpoint, end_checkpoint, add_claim_report

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
    """Main fact-checking engine"""
    
    def __init__(self):
        """Initialize fact checker with API clients"""
        self.session = requests.Session()
        
        # Rotate user agents to avoid blocking
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Performance optimizations
        self.max_urls = 15  # Reduced from 50 for speed
        self.priority_sources_limit = 8  # Prioritize top sources
        self.delay_between_requests = 0.3  # Reduced from 1.0s
        self.timeout = 5  # Reduced from 10s for faster fails
        self.max_retries = 1  # Reduced retries
        self.concurrent_limit = 8  # Increased concurrency
        
        # Source credibility ratings with priority tiers (0.0 to 1.0)
        self.source_credibility = {
            # Tier 1: Premium sources (0.95+)
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
            
            # Tier 2: High-quality sources (0.85-0.94)
            'bbc.com': 0.92,
            'npr.org': 0.91,
            'pbs.org': 0.90,
            'factcheck.org': 0.90,
            'ieee.org': 0.88,
            'politifact.com': 0.87,
            'snopes.com': 0.85,
            
            # Tier 3: Reliable sources (0.70-0.84)
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
            'washingtonpost.com': 0.82,
        }
        
        # Priority source domains (accessed first)
        self.priority_domains = [
            'reuters.com', 'apnews.com', 'who.int', 'cdc.gov', 'nih.gov',
            'nature.com', 'science.org', 'bbc.com', 'npr.org', 'factcheck.org'
        ]
        
        # Expanded blocked domains (known for 403 errors or paywalls)
        self.blocked_domains = [
            'bloomberg.com', 'wsj.com', 'ft.com', 'nytimes.com',
            'economist.com', 'newyorker.com', 'atlanticmedia.com',
            'wired.com', 'forbes.com', 'businessinsider.com',
            'techcrunch.com', 'arstechnica.com', 'theverge.com',
            'sec.gov/Archives',  # SEC filings often blocked
            'patents.google.com', 'scholar.google.com/citations'
        ]
        
        # Cache for search results
        self.search_cache = {}
        
    async def fact_check_claims(self, claims: List[Claim]) -> List[FactCheckResult]:
        """
        Fact-check multiple claims concurrently
        
        Args:
            claims: List of claims to fact-check
            
        Returns:
            List of fact-check results
        """
        logger.info(f"Starting optimized fact-check process for {len(claims)} claims")
        
        # Create semaphore for higher concurrency
        semaphore = asyncio.Semaphore(self.concurrent_limit)
        
        async def fact_check_with_semaphore(claim):
            async with semaphore:
                return await self.fact_check_claim(claim)
        
        # Process claims concurrently
        tasks = [fact_check_with_semaphore(claim) for claim in claims]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        fact_check_results = []
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
        
        logger.info(f"Completed fact-checking {len(fact_check_results)} claims")
        return fact_check_results
    
    async def fact_check_claim(self, claim: Claim) -> FactCheckResult:
        """
        Fact-check a single claim with comprehensive checkpoint monitoring
        
        Args:
            claim: Claim to fact-check
            
        Returns:
            FactCheckResult with verification details
        """
        start_time = datetime.now()
        claim_id = f"claim_{int(time.time() * 1000)}"
        checkpoints = []
        
        logger.info(f"🔍 Fact-checking claim: {claim.text[:100]}...")
        
        try:
            # Checkpoint 1: Search for relevant sources
            with TimedCheckpoint("source_search", {"claim_type": claim.claim_type.value}) as cp:
                sources = await self._search_sources(claim)
            checkpoints.append(self._get_checkpoint_from_context(cp))
            
            # Checkpoint 2: Analyze sources for evidence
            with TimedCheckpoint("evidence_analysis", {"source_count": len(sources)}) as cp:
                evidence, contradictions = await self._analyze_sources(claim, sources)
            checkpoints.append(self._get_checkpoint_from_context(cp))
            
            # Checkpoint 3: Calculate authenticity score
            with TimedCheckpoint("authenticity_calculation", {
                "evidence_count": len(evidence), 
                "contradiction_count": len(contradictions)
            }) as cp:
                authenticity_score = self._calculate_authenticity_score(
                    claim, sources, evidence, contradictions
                )
            checkpoints.append(self._get_checkpoint_from_context(cp))
            
            # Checkpoint 4: Determine verification status
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
                    processing_time=processing_time
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
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error fact-checking claim: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Add failed report
            add_claim_report(
                claim_id=claim_id,
                claim_text=claim.text,
                claim_type=claim.claim_type.value,
                checkpoints=checkpoints,
                success=False
            )
            
            return FactCheckResult(
                claim=claim,
                verification_status='error',
                authenticity_score=0.0,
                sources_checked=[],
                evidence=[],
                contradictions=[],
                processing_time=processing_time,
                error_message=str(e)
            )
    
    def _get_checkpoint_from_context(self, context) -> 'CheckpointTiming':
        """Extract checkpoint timing from context manager"""
        from src.fact_check_agent.checkpoint_monitor import CheckpointTiming
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
    
    async def _search_sources(self, claim: Claim) -> List[Source]:
        """Search for relevant sources with detailed checkpoint monitoring"""
        sources = []
        
        # Checkpoint: Generate search queries
        with TimedCheckpoint("search_query_generation") as cp:
            search_queries = self._generate_search_queries(claim)
        
        logger.info(f"🔍 Searching for sources using {len(search_queries[:3])} queries")
        
        # Checkpoint: Execute web searches
        with TimedCheckpoint("web_search_execution", {"query_count": len(search_queries[:3])}) as cp:
            for query in search_queries[:3]:  # Limit to top 3 queries
                try:
                    # Search specific sources first
                    specific_sources = await self._search_specific_sources(claim, query)
                    sources.extend(specific_sources)
                    
                    # Fall back to general web search
                    if len(sources) < 10:
                        web_sources = await self._search_web(query, claim.claim_type)
                        sources.extend(web_sources)
                    
                except Exception as e:
                    logger.warning(f"Search failed for query '{query}': {str(e)}")
        
        # Checkpoint: Process and prioritize results
        with TimedCheckpoint("source_prioritization", {"raw_source_count": len(sources)}) as cp:
            # Remove duplicates and prioritize sources
            sources = self._deduplicate_sources(sources)
            prioritized_sources = self._prioritize_sources(sources)
            final_sources = prioritized_sources[:self.max_urls]
        
        logger.info(f"📊 Final source count: {len(final_sources)}")
        return final_sources
    
    def _generate_search_queries(self, claim: Claim) -> List[str]:
        """Generate search queries for a claim"""
        queries = []
        
        # Original claim text
        queries.append(claim.text)
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(claim.text)
        for phrase in key_phrases[:2]:
            queries.append(phrase)
        
        # Add entity-based queries
        for entity in claim.entities[:2]:
            entity_query = f"{entity['text']} {claim.claim_type.value}"
            queries.append(entity_query)
        
        # Add fact-check specific query
        fact_check_query = f"fact check {claim.text[:50]}"
        queries.append(fact_check_query)
        
        return queries[:5]  # Limit to 5 queries
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from claim text"""
        # Simple key phrase extraction
        # Remove common words and extract meaningful phrases
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        words = text.lower().split()
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        phrases = []
        # Extract bi-grams and tri-grams
        for i in range(len(filtered_words) - 1):
            phrases.append(' '.join(filtered_words[i:i+2]))
            if i < len(filtered_words) - 2:
                phrases.append(' '.join(filtered_words[i:i+3]))
        
        return phrases[:5]
    
    async def _search_specific_sources(self, claim: Claim, query: str) -> List[Source]:
        """Search specific fact-checking sources"""
        sources = []
        
        for source_domain in claim.sources_to_check[:3]:  # Limit to top 3 sources
            try:
                source_results = await self._search_domain(query, source_domain)
                sources.extend(source_results)
            except Exception as e:
                logger.warning(f"Failed to search {source_domain}: {str(e)}")
        
        return sources
    
    async def _search_domain(self, query: str, domain: str) -> List[Source]:
        """Search within a specific domain"""
        sources = []
        
        # Use site-specific search
        site_query = f"site:{domain} {query}"
        
        try:
            # Use Google search with domain restriction
            if config.serp_api_key:
                search_results = await self._google_search(site_query)
                sources.extend(search_results)
            
        except Exception as e:
            logger.warning(f"Domain search failed for {domain}: {str(e)}")
        
        return sources
    
    async def _search_web(self, query: str, claim_type: ClaimType) -> List[Source]:
        """General web search with reliability filtering"""
        sources = []
        
        try:
            if config.serp_api_key:
                # Use SerpAPI for Google search
                search_results = await self._google_search(query)
                sources.extend(search_results)
            
        except Exception as e:
            logger.warning(f"Web search failed: {str(e)}")
        
        return sources
    
    async def _google_search(self, query: str) -> List[Source]:
        """Perform Google search using SerpAPI"""
        if not config.serp_api_key:
            return []
        
        # Check cache first
        cache_key = hashlib.md5(query.encode()).hexdigest()
        if cache_key in self.search_cache:
            cached_result = self.search_cache[cache_key]
            if datetime.now() - cached_result['timestamp'] < timedelta(hours=1):
                return cached_result['sources']
        
        try:
            search = GoogleSearch({
                "q": query,
                "api_key": config.serp_api_key,
                "num": 10,
                "safe": "active"
            })
            
            results = search.get_dict()
            sources = []
            
            if "organic_results" in results:
                for result in results["organic_results"][:10]:
                    try:
                        source = await self._create_source_from_search_result(result)
                        if source:
                            sources.append(source)
                    except Exception as e:
                        logger.warning(f"Failed to process search result: {str(e)}")
            
            # Cache results
            self.search_cache[cache_key] = {
                'sources': sources,
                'timestamp': datetime.now()
            }
            
            return sources
            
        except Exception as e:
            logger.error(f"Google search failed: {str(e)}")
            return []
    
    async def _create_source_from_search_result(self, result: Dict) -> Optional[Source]:
        """Create a Source object from search result with progress tracking"""
        try:
            url = result.get('link', '')
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            if not url or not title:
                return None
            
            # Extract domain
            domain = self._extract_domain(url)
            
            # Get credibility score
            credibility_score = self.source_credibility.get(domain, 0.5)
            
            # Skip low-credibility sources
            if credibility_score < 0.3:
                logger.debug(f"Skipping low-credibility source: {domain} (score: {credibility_score})")
                return None
            
            # Skip blocked domains (paywall sites and 403-prone sources)
            if any(blocked_domain in url.lower() for blocked_domain in self.blocked_domains):
                logger.debug(f"Skipping blocked domain: {domain}")
                return None
            
            logger.debug(f"Extracting content from: {domain}")
            
            # Try to get full article content with retry mechanism
            content = await self._extract_article_content_with_retry(url)
            if not content:
                content = snippet
                logger.debug(f"Using snippet for {url} (content extraction failed)")
            
            # Calculate relevance score (simplified)
            relevance_score = 0.7  # Default relevance
            
            return Source(
                url=url,
                title=title,
                content=content,
                relevance_score=relevance_score,
                credibility_score=credibility_score,
                publication_date=None,  # Would need to extract from article
                domain=domain
            )
            
        except Exception as e:
            logger.warning(f"Failed to create source from search result: {str(e)}")
            return None
    
    async def _extract_article_content_with_retry(self, url: str, max_retries: int = 1) -> str:
        """Extract article content with fast retry mechanism"""
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    # Shorter backoff for speed
                    await asyncio.sleep(0.5)
                    logger.debug(f"Retry attempt {attempt} for {url}")
                
                return await self._extract_article_content(url)
                
            except Exception as e:
                if attempt == max_retries:
                    logger.debug(f"Final attempt failed for {url}: {str(e)}")
                    return ""
                logger.debug(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
        
        return ""
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower().replace('www.', '')
        except:
            return ''
    
    async def _extract_article_content(self, url: str) -> str:
        """Enhanced article content extraction with checkpoint monitoring"""
        
        # Checkpoint: newspaper3k extraction
        with TimedCheckpoint("newspaper3k_extraction", {"url": url}) as cp:
            try:
                content = await self._extract_with_newspaper(url)
                if content:
                    return content
            except Exception as e:
                logger.debug(f"Newspaper3k failed for {url}: {str(e)}")
        
        # Checkpoint: requests + BeautifulSoup extraction
        with TimedCheckpoint("requests_extraction", {"url": url}) as cp:
            try:
                content = await self._extract_with_requests(url)
                if content:
                    return content
            except Exception as e:
                logger.debug(f"Requests method failed for {url}: {str(e)}")
        
        # Checkpoint: aiohttp extraction
        with TimedCheckpoint("aiohttp_extraction", {"url": url}) as cp:
            try:
                content = await self._extract_with_aiohttp(url)
                if content:
                    return content
            except Exception as e:
                logger.debug(f"Aiohttp method failed for {url}: {str(e)}")
        
        logger.debug(f"All extraction methods failed for {url}")
        return ""
    
    async def _extract_with_newspaper(self, url: str) -> str:
        """Extract content using newspaper3k with enhanced configuration"""
        article = Article(url)
        
        # Set custom headers to avoid blocking
        article.config.request_timeout = self.timeout
        article.config.browser_user_agent = random.choice(self.user_agents)
        
        # Minimal delay for speed
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        article.download()
        article.parse()
        
        if not article.text or len(article.text) < 100:
            raise Exception("Article content too short or empty")
            
        return article.text[:5000]
    
    async def _extract_with_requests(self, url: str) -> str:
        """Extract content using requests + BeautifulSoup"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        response = self.session.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try common article selectors
        content = ""
        selectors = [
            'article', '[class*="article"]', '[class*="content"]', 
            '[class*="story"]', '[class*="post"]', 'main', 
            '.entry-content', '.post-content', '.article-content'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                content = ' '.join([elem.get_text(strip=True) for elem in elements])
                if len(content) > 200:
                    break
        
        # Fallback to body text
        if not content or len(content) < 200:
            content = soup.get_text(strip=True)
        
        if len(content) < 100:
            raise Exception("Content too short")
            
        return content[:5000]
    
    async def _extract_with_aiohttp(self, url: str) -> str:
        """Extract content using aiohttp as final fallback"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Basic text extraction
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text(strip=True)
                
                if len(text) < 100:
                    raise Exception("Content too short")
                
                return text[:5000]
    
    def _prioritize_sources(self, sources: List[Source]) -> List[Source]:
        """Prioritize sources by credibility and domain priority"""
        priority_sources = []
        regular_sources = []
        
        for source in sources:
            is_priority = any(domain in source.domain for domain in self.priority_domains)
            if is_priority:
                priority_sources.append(source)
            else:
                regular_sources.append(source)
        
        # Sort each group by credibility * relevance
        priority_sources.sort(key=lambda s: s.credibility_score * s.relevance_score, reverse=True)
        regular_sources.sort(key=lambda s: s.credibility_score * s.relevance_score, reverse=True)
        
        # Combine: priority sources first, then regular sources
        return priority_sources[:self.priority_sources_limit] + regular_sources
    
    def _deduplicate_sources(self, sources: List[Source]) -> List[Source]:
        """Remove duplicate sources"""
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            if source.url not in seen_urls:
                seen_urls.add(source.url)
                unique_sources.append(source)
        
        return unique_sources
    
    async def _analyze_sources(self, claim: Claim, sources: List[Source]) -> Tuple[List[Dict], List[Dict]]:
        """Analyze sources to find evidence and contradictions with progress tracking"""
        evidence = []
        contradictions = []
        
        logger.info(f"Analyzing {len(sources)} sources for evidence")
        
        # Process sources concurrently for speed
        async def analyze_source(source):
            try:
                # Add minimal delay to avoid overwhelming servers
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
                evidence = self._extract_evidence(claim, source)
                contradictions = self._find_contradictions(claim, source)
                return evidence, contradictions
                
            except Exception as e:
                logger.warning(f"Failed to analyze source {source.url}: {str(e)}")
                return [], []
        
        # Process all sources concurrently
        semaphore = asyncio.Semaphore(self.concurrent_limit)
        
        async def analyze_with_semaphore(source):
            async with semaphore:
                return await analyze_source(source)
        
        tasks = [analyze_with_semaphore(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        for result in results:
            if isinstance(result, tuple):
                source_evidence, source_contradictions = result
                evidence.extend(source_evidence)
                contradictions.extend(source_contradictions)
        
        logger.info(f"Found {len(evidence)} evidence items and {len(contradictions)} contradictions")
        return evidence, contradictions
    
    def _extract_evidence(self, claim: Claim, source: Source) -> List[Dict[str, Any]]:
        """Extract supporting evidence sentences from source"""
        evidence = []
        
        if not source.content or len(source.content) < 50:
            return evidence
        
        # Enhanced keyword matching
        claim_keywords = set()
        
        # Add claim keywords
        if claim.keywords:
            claim_keywords.update([kw.lower() for kw in claim.keywords])
        
        # Add entity text
        for entity in claim.entities:
            if entity.get('text'):
                claim_keywords.add(entity['text'].lower())
        
        # Extract key terms from claim text
        claim_words = set(word.lower().strip('.,!?') for word in claim.text.split() 
                         if len(word) > 3 and word.isalpha())
        claim_keywords.update(claim_words)
        
        # Split source content into sentences
        sentences = re.split(r'[.!?]+', source.content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 30:  # Longer minimum for quality
                continue
            
            # Enhanced matching criteria
            sentence_lower = sentence.lower()
            
            # Count keyword matches
            keyword_matches = sum(1 for keyword in claim_keywords 
                                if keyword in sentence_lower and len(keyword) > 2)
            
            # Look for supporting indicators
            supporting_indicators = [
                'according to', 'research shows', 'study found', 'data indicates',
                'evidence suggests', 'confirmed', 'verified', 'proven', 'demonstrated',
                'statistics show', 'reports indicate', 'found that', 'concluded'
            ]
            
            has_supporting_language = any(indicator in sentence_lower 
                                        for indicator in supporting_indicators)
            
            # Calculate relevance score
            relevance = keyword_matches / max(len(claim_keywords), 1) if claim_keywords else 0
            
            # Include if has good keyword overlap or supporting language
            if (keyword_matches >= 2 and relevance > 0.2) or (keyword_matches >= 1 and has_supporting_language):
                evidence_item = {
                    'sentence': sentence,
                    'source_url': source.url,
                    'source_title': source.title,
                    'source_domain': source.domain,
                    'source_credibility': source.credibility_score,
                    'relevance_score': relevance,
                    'keyword_matches': keyword_matches,
                    'has_supporting_language': has_supporting_language,
                    'type': 'supporting'
                }
                evidence.append(evidence_item)
        
        # Sort by relevance and return top evidence
        evidence.sort(key=lambda x: x['relevance_score'] * x['source_credibility'], reverse=True)
        return evidence[:3]  # Return top 3 pieces of evidence per source
    
    def _find_contradictions(self, claim: Claim, source: Source) -> List[Dict[str, Any]]:
        """Find contradictory sentences in source"""
        contradictions = []
        
        if not source.content or len(source.content) < 50:
            return contradictions
        
        # Enhanced keyword matching (same as evidence extraction)
        claim_keywords = set()
        
        if claim.keywords:
            claim_keywords.update([kw.lower() for kw in claim.keywords])
        
        for entity in claim.entities:
            if entity.get('text'):
                claim_keywords.add(entity['text'].lower())
        
        claim_words = set(word.lower().strip('.,!?') for word in claim.text.split() 
                         if len(word) > 3 and word.isalpha())
        claim_keywords.update(claim_words)
        
        # Split source content into sentences
        sentences = re.split(r'[.!?]+', source.content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 30:
                continue
            
            sentence_lower = sentence.lower()
            
            # Count keyword matches
            keyword_matches = sum(1 for keyword in claim_keywords 
                                if keyword in sentence_lower and len(keyword) > 2)
            
            # Look for contradictory indicators
            contradictory_indicators = [
                'however', 'but', 'although', 'despite', 'contrary to',
                'not', 'no evidence', 'disproven', 'false', 'incorrect',
                'disputed', 'refuted', 'contradicts', 'debunked',
                'actually', 'in fact', 'rather than', 'instead of'
            ]
            
            has_contradictory_language = any(indicator in sentence_lower 
                                           for indicator in contradictory_indicators)
            
            # Calculate relevance score
            relevance = keyword_matches / max(len(claim_keywords), 1) if claim_keywords else 0
            
            # Include if has keyword overlap AND contradictory language
            if keyword_matches >= 1 and has_contradictory_language and relevance > 0.1:
                contradiction_item = {
                    'sentence': sentence,
                    'source_url': source.url,
                    'source_title': source.title,
                    'source_domain': source.domain,
                    'source_credibility': source.credibility_score,
                    'relevance_score': relevance,
                    'keyword_matches': keyword_matches,
                    'contradictory_indicators': [ind for ind in contradictory_indicators 
                                               if ind in sentence_lower],
                    'type': 'contradictory'
                }
                contradictions.append(contradiction_item)
        
        # Sort by relevance and return top contradictions
        contradictions.sort(key=lambda x: x['relevance_score'] * x['source_credibility'], reverse=True)
        return contradictions[:2]  # Return top 2 contradictions per source
    
    def _calculate_authenticity_score(
        self, 
        claim: Claim, 
        sources: List[Source], 
        evidence: List[Dict], 
        contradictions: List[Dict]
    ) -> float:
        """Calculate authenticity score for a claim"""
        if not sources:
            return 0.0
        
        # Base score from source credibility
        avg_source_credibility = sum(s.credibility_score for s in sources) / len(sources)
        base_score = avg_source_credibility * 0.4
        
        # Evidence score
        evidence_score = 0.0
        if evidence:
            weighted_evidence = sum(
                e['relevance_score'] * e['source_credibility'] for e in evidence
            ) / len(evidence)
            evidence_score = min(0.4, weighted_evidence * 0.4)
        
        # Contradiction penalty
        contradiction_penalty = 0.0
        if contradictions:
            weighted_contradictions = sum(
                c['relevance_score'] * c['source_credibility'] for c in contradictions
            ) / len(contradictions)
            contradiction_penalty = min(0.3, weighted_contradictions * 0.3)
        
        # Cross-reference bonus
        cross_reference_bonus = 0.0
        if len(sources) >= 3:
            cross_reference_bonus = min(0.2, len(sources) * 0.05)
        
        # Calculate final score
        authenticity_score = base_score + evidence_score + cross_reference_bonus - contradiction_penalty
        
        return max(0.0, min(1.0, authenticity_score))
    
    def _determine_verification_status(
        self, 
        authenticity_score: float, 
        evidence: List[Dict], 
        contradictions: List[Dict]
    ) -> str:
        """Determine verification status based on score and evidence"""
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
    
    def _source_to_dict(self, source: Source) -> Dict[str, Any]:
        """Convert Source object to dictionary"""
        return {
            'url': source.url,
            'title': source.title,
            'domain': source.domain,
            'credibility_score': source.credibility_score,
            'relevance_score': source.relevance_score,
            'publication_date': source.publication_date.isoformat() if source.publication_date else None
        }