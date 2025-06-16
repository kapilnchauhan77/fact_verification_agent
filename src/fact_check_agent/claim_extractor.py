"""
Claim extraction and classification module using Gemini
"""
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import vertexai
from vertexai.generative_models import GenerativeModel, Part
import google.auth

from .config import FACT_CHECK_SOURCES, config
from .checkpoint_monitor import TimedCheckpoint

logger = logging.getLogger(__name__)

class ClaimType(Enum):
    """Types of claims that can be fact-checked"""
    POLITICAL = "political"
    MEDICAL = "medical"
    SCIENTIFIC = "scientific"
    FINANCIAL = "financial"
    TECHNOLOGY = "technology"
    GENERAL = "general"
    STATISTICAL = "statistical"
    HISTORICAL = "historical"

@dataclass
class Claim:
    """Represents a factual claim extracted from text"""
    text: str
    claim_type: ClaimType
    confidence: float
    context: str
    sentence_index: int
    entities: List[Dict[str, Any]]
    keywords: List[str]
    sources_to_check: List[str]
    priority: int  # 1 (highest) to 5 (lowest)

class ClaimExtractor:
    """Extracts and classifies factual claims from text using Gemini"""
    
    def __init__(self):
        """Initialize the claim extractor with Gemini model"""
        try:
            # Initialize Vertex AI
            vertexai.init(
                project=config.google_cloud_project,
                location=config.vertex_ai_location
            )
            
            # Initialize Gemini model
            self.model = GenerativeModel(config.vertex_ai_model)
            logger.info(f"Initialized Gemini model: {config.vertex_ai_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            self.model = None
    
    def extract_claims(self, text: str) -> List[Claim]:
        """
        Extract factual claims from text using Gemini with chunking for large texts
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of extracted claims
        """
        if not text or not text.strip():
            return []
        
        if not self.model:
            logger.error("Gemini model not initialized")
            return []
        
        logger.info(f"🧠 Extracting claims from text ({len(text)} characters)")
        
        # Check if text is too long and needs chunking
        max_chunk_size = 16000
        if len(text) <= max_chunk_size:
            # Process normally for smaller texts
            return self._extract_claims_from_chunk(text)
        else:
            # Process in chunks for larger texts
            logger.info(f"📄 Text too long ({len(text)} chars), processing in chunks of {max_chunk_size}")
            return self._extract_claims_with_chunking(text, max_chunk_size)
    
    def _extract_claims_with_chunking(self, text: str, max_chunk_size: int) -> List[Claim]:
        """
        Extract claims from large text by processing in chunks
        
        Args:
            text: Input text to analyze
            max_chunk_size: Maximum size of each chunk
            
        Returns:
            Combined list of extracted claims from all chunks
        """
        all_claims = []
        
        try:
            # Split text into smart chunks (try to break at sentence boundaries)
            chunks = self._split_text_into_chunks(text, max_chunk_size)
            
            logger.info(f"📊 Processing {len(chunks)} chunks")
            
            # Process each chunk
            for i, chunk in enumerate(chunks):
                logger.info(f"🔍 Processing chunk {i+1}/{len(chunks)} ({len(chunk)} characters)")
                
                try:
                    # Extract claims from this chunk
                    with TimedCheckpoint("chunk_processing", {"chunk_index": i, "chunk_size": len(chunk)}) as cp:
                        chunk_claims = self._extract_claims_from_chunk(chunk)
                    
                    # Adjust sentence indices to account for previous chunks
                    for claim in chunk_claims:
                        claim.sentence_index += i * 100  # Offset by chunk number
                    
                    all_claims.extend(chunk_claims)
                    logger.info(f"✅ Chunk {i+1}: Extracted {len(chunk_claims)} claims")
                    
                except Exception as e:
                    logger.warning(f"❌ Failed to process chunk {i+1}: {str(e)}")
                    # Continue with next chunk
                    continue
            
            # Deduplicate and merge similar claims
            with TimedCheckpoint("claim_deduplication", {"total_claims": len(all_claims)}) as cp:
                final_claims = self._deduplicate_claims(all_claims)
            
            # Sort by priority and confidence
            final_claims.sort(key=lambda x: (x.priority, -x.confidence))
            
            logger.info(f"✅ Completed chunked extraction: {len(final_claims)} claims from {len(chunks)} chunks")
            return final_claims
            
        except Exception as e:
            logger.error(f"❌ Failed chunked extraction: {str(e)}")
            # Fallback to simple extraction on first chunk
            first_chunk = text[:max_chunk_size]
            return self._fallback_extraction(first_chunk)
    
    def _extract_claims_from_chunk(self, text: str) -> List[Claim]:
        """
        Extract claims from a single chunk of text
        
        Args:
            text: Text chunk to analyze
            
        Returns:
            List of extracted claims
        """
        try:
            # Checkpoint: Create prompt for Gemini
            with TimedCheckpoint("prompt_creation", {"text_length": len(text)}) as cp:
                prompt = self._create_extraction_prompt(text)
            
            # Checkpoint: Generate response from Gemini
            with TimedCheckpoint("gemini_api_call", {"prompt_length": len(prompt)}) as cp:
                response = self.model.generate_content(prompt)
            
            # Checkpoint: Parse the response
            with TimedCheckpoint("response_parsing", {"response_length": len(response.text)}) as cp:
                claims = self._parse_gemini_response(response.text, text)
            
            return claims
            
        except Exception as e:
            logger.error(f"❌ Failed to extract claims from chunk: {str(e)}")
            # Fallback extraction for this chunk
            return self._fallback_extraction(text)
    
    def _split_text_into_chunks(self, text: str, max_chunk_size: int) -> List[str]:
        """
        Split text into chunks, preferring sentence boundaries
        
        Args:
            text: Text to split
            max_chunk_size: Maximum size of each chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        
        # Try to split at paragraph boundaries first
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # If paragraph itself is too long, split at sentence boundaries
                if len(paragraph) > max_chunk_size:
                    sentences = re.split(r'[.!?]+', paragraph)
                    temp_chunk = ""
                    
                    for sentence in sentences:
                        if len(temp_chunk) + len(sentence) > max_chunk_size:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                                temp_chunk = sentence
                            else:
                                # Single sentence too long, force split
                                chunks.append(sentence[:max_chunk_size])
                                temp_chunk = sentence[max_chunk_size:]
                        else:
                            temp_chunk += sentence + "."
                    
                    if temp_chunk:
                        current_chunk = temp_chunk
                else:
                    current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _deduplicate_claims(self, claims: List[Claim]) -> List[Claim]:
        """
        Remove duplicate or very similar claims
        
        Args:
            claims: List of claims to deduplicate
            
        Returns:
            Deduplicated list of claims
        """
        if not claims:
            return []
        
        unique_claims = []
        seen_texts = set()
        
        for claim in claims:
            # Simple deduplication based on claim text similarity
            claim_text_normalized = claim.text.lower().strip()
            
            # Check for exact matches
            if claim_text_normalized in seen_texts:
                continue
            
            # Check for very similar claims (>80% similarity)
            is_duplicate = False
            for seen_text in seen_texts:
                similarity = self._calculate_text_similarity(claim_text_normalized, seen_text)
                if similarity > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_claims.append(claim)
                seen_texts.add(claim_text_normalized)
        
        return unique_claims
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity based on word overlap
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _create_extraction_prompt(self, text: str) -> str:
        """Create a prompt for Gemini to extract claims"""
        claim_types = [ct.value for ct in ClaimType]
        
        prompt = f"""
You are an expert fact-checker. Analyze the following text and extract factual claims that can be verified.

CLAIM TYPES:
{', '.join(claim_types)}

INSTRUCTIONS:
1. Identify sentences that contain verifiable factual claims
2. Break down compound claims into separate individual claims when possible
3. Extract key entities (people, places, organizations, dates, numbers)
4. Classify each claim by type
5. Assign confidence score (0.0-1.0) based on how factual/specific the claim is
6. Assign priority (1=highest, 5=lowest) based on importance/controversy
7. Extract relevant keywords
8. Provide context from surrounding text

COMPOUND CLAIM BREAKDOWN:
- If a sentence contains multiple distinct factual assertions, extract them as separate claims
- Example: "Company X is regulated and has license number 12345" should become:
  1. "Company X is regulated"
  2. "Company X has license number 12345"
- Example: "Product Y costs $100 and was launched in 2023" should become:
  1. "Product Y costs $100"
  2. "Product Y was launched in 2023"

IMPORTANT: You MUST respond with valid JSON only. No additional text before or after the JSON.

OUTPUT FORMAT (JSON):
{{
  "claims": [
    {{
      "text": "The exact claim sentence",
      "claim_type": "one of: {', '.join(claim_types)}",
      "confidence": 0.85,
      "priority": 2,
      "entities": [
        {{"text": "Entity Name", "label": "PERSON|ORG|GPE|DATE|MONEY|PERCENT", "start": 0, "end": 10}}
      ],
      "keywords": ["keyword1", "keyword2"],
      "context": "Surrounding sentences for context"
    }}
  ]
}}

If no claims are found, return: {{"claims": []}}

FILTER CRITERIA:
- Only include claims that are factual, specific, and verifiable
- Skip opinions, speculation, or vague statements
- Focus on claims with numbers, dates, specific entities, or definitive statements
- Minimum 5 words per claim
- Break compound claims into individual verifiable statements

TEXT TO ANALYZE:
{text}
"""
        return prompt
    
    def _parse_gemini_response(self, response_text: str, original_text: str) -> List[Claim]:
        """Parse Gemini's JSON response into Claim objects"""
        claims = []
        
        try:
            # Handle empty or invalid responses
            if not response_text or not response_text.strip():
                logger.warning("Empty response from Gemini")
                return claims
            
            # Clean and extract JSON from response
            json_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if '```json' in json_text:
                start = json_text.find('```json') + 7
                end = json_text.find('```', start)
                if end != -1:
                    json_text = json_text[start:end].strip()
            elif '```' in json_text:
                # Handle generic code blocks
                start = json_text.find('```') + 3
                end = json_text.rfind('```')
                if end != -1 and end > start:
                    json_text = json_text[start:end].strip()
            
            # Try to find JSON object within the text
            if not json_text.startswith('{'):
                # Look for JSON object in the response
                start_brace = json_text.find('{')
                if start_brace != -1:
                    # Find matching closing brace
                    brace_count = 0
                    end_brace = -1
                    for i in range(start_brace, len(json_text)):
                        if json_text[i] == '{':
                            brace_count += 1
                        elif json_text[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_brace = i + 1
                                break
                    
                    if end_brace != -1:
                        json_text = json_text[start_brace:end_brace]
            
            # Parse JSON
            if json_text.strip():
                data = json.loads(json_text)
                
                # Handle different response structures
                claims_data = []
                if isinstance(data, dict):
                    if 'claims' in data:
                        claims_data = data['claims']
                    elif isinstance(data.get('claims'), list):
                        claims_data = data['claims']
                    else:
                        # Single claim object
                        claims_data = [data]
                elif isinstance(data, list):
                    claims_data = data
                
                for i, claim_data in enumerate(claims_data):
                    try:
                        # Validate required fields
                        if not claim_data.get('text'):
                            continue
                        
                        # Parse claim type
                        claim_type_str = claim_data.get('claim_type', 'general').lower()
                        claim_type = ClaimType.GENERAL  # Default
                        for ct in ClaimType:
                            if ct.value == claim_type_str:
                                claim_type = ct
                                break
                        
                        # Get sources for this claim type
                        sources_to_check = self._get_sources_for_claim_type(claim_type)
                        
                        # Create claim object
                        claim = Claim(
                            text=claim_data['text'],
                            claim_type=claim_type,
                            confidence=float(claim_data.get('confidence', 0.5)),
                            context=claim_data.get('context', ''),
                            sentence_index=i,
                            entities=claim_data.get('entities', []),
                            keywords=claim_data.get('keywords', []),
                            sources_to_check=sources_to_check,
                            priority=int(claim_data.get('priority', 3))
                        )
                        
                        claims.append(claim)
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse individual claim: {str(e)}")
                        continue
            else:
                logger.warning("No valid JSON found in Gemini response")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {str(e)}")
            logger.debug(f"Cleaned JSON text: {json_text[:200]}...")
            logger.debug(f"Original response: {response_text[:200]}...")
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            
        return claims
    
    def _fallback_extraction(self, text: str) -> List[Claim]:
        """Fallback method for basic claim extraction when Gemini fails"""
        claims = []
        
        try:
            # Simple sentence-based extraction
            import re
            
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if len(sentence) < 10:  # Skip very short sentences
                    continue
                
                # Check for factual indicators
                factual_indicators = [
                    'according to', 'research shows', 'studies indicate', 
                    'data suggests', 'statistics show', 'reports indicate',
                    'scientists found', 'experts say'
                ]
                
                sentence_lower = sentence.lower()
                has_factual_indicator = any(indicator in sentence_lower for indicator in factual_indicators)
                has_numbers = bool(re.search(r'\d+(?:\.\d+)?%|\$\d+|\d{4}', sentence))
                
                if has_factual_indicator or has_numbers:
                    # Basic entity extraction (simple regex)
                    entities = []
                    # Find numbers/percentages
                    numbers = re.findall(r'\d+(?:\.\d+)?%|\$\d+(?:,\d{3})*(?:\.\d+)?|\d{4}', sentence)
                    for num in numbers:
                        entities.append({
                            'text': num,
                            'label': 'NUMBER',
                            'start': 0,
                            'end': 0
                        })
                    
                    # Simple keywords (words > 4 chars)
                    keywords = [word.lower() for word in sentence.split() 
                              if len(word) > 4 and word.isalpha()][:5]
                    
                    claim = Claim(
                        text=sentence,
                        claim_type=ClaimType.GENERAL,
                        confidence=0.6 if has_factual_indicator else 0.4,
                        context=text[:200] + "..." if len(text) > 200 else text,
                        sentence_index=i,
                        entities=entities,
                        keywords=keywords,
                        sources_to_check=FACT_CHECK_SOURCES['general'],
                        priority=3
                    )
                    
                    claims.append(claim)
            
            logger.info(f"Fallback extraction found {len(claims)} claims")
            
        except Exception as e:
            logger.error(f"Fallback extraction failed: {str(e)}")
        
        return claims
    
    def _get_sources_for_claim_type(self, claim_type: ClaimType) -> List[str]:
        """Get appropriate sources for fact-checking based on claim type"""
        return FACT_CHECK_SOURCES.get(claim_type.value, FACT_CHECK_SOURCES['general'])