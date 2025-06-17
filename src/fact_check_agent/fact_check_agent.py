"""
Google ADK Fact Check Agent
Main agent implementation using Google Agent Development Kit
"""

import asyncio
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import google.generativeai as genai

# Google AI imports
import vertexai
from vertexai.generative_models import GenerativeModel

from .authenticity_scorer import AuthenticityScorer
from .claim_extractor import ClaimExtractor

# Local imports
from .config import config
from .document_processor import DocumentProcessor
from .fact_checker import FactChecker
from .performance_monitor import PerformanceMonitor, monitor_performance, with_throttling
from .report_generator import ReportGenerator
from .security_manager import SecurityManager

# Setup logging
logging.basicConfig(level=getattr(logging, config.log_level))
logger = logging.getLogger(__name__)


class FactCheckAgent:
    """Main fact-checking agent using Google AI"""

    def __init__(self):
        """Initialize the fact-check agent"""
        # Initialize Vertex AI
        vertexai.init(
            project=config.google_cloud_project, location=config.vertex_ai_location
        )

        # Initialize components
        self.document_processor = DocumentProcessor()
        self.claim_extractor = ClaimExtractor()
        self.fact_checker = FactChecker()
        self.authenticity_scorer = AuthenticityScorer()
        self.report_generator = ReportGenerator()
        self.security_manager = SecurityManager()
        self.performance_monitor = PerformanceMonitor()

        # Create Google AI model
        self.model = GenerativeModel(
            model_name=config.vertex_ai_model,
            generation_config={
                "temperature": 0.1,  # Low temperature for consistent, factual responses
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            },
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
            },
        )

        # Session management
        self.sessions = {}

        logger.info("Fact Check Agent initialized successfully")

    @monitor_performance("document_analysis")
    async def analyze_document(
        self,
        document_path: Union[str, Path],
        user_id: str = "default_user",
        session_id: str = None,
    ) -> Dict[str, Any]:
        """
        Analyze a document and fact-check its claims

        Args:
            document_path: Path to the document to analyze
            user_id: User identifier for session management
            session_id: Session identifier for security validation

        Returns:
            Comprehensive fact-check report
        """
        logger.info(f"Starting document analysis: {document_path}")

        try:
            # Security validation
            if session_id and not self.security_manager.validate_session(
                session_id, user_id
            ):
                return {"success": False, "error": "Invalid or expired session"}

            # Sanitize document path
            try:
                safe_path = self.security_manager.sanitize_document_path(
                    str(document_path)
                )
                document_path = safe_path
            except Exception as e:
                return {"success": False, "error": f"Invalid document path: {str(e)}"}
            # Step 1: OCR and text extraction
            logger.info("Step 1: Processing document...")
            document_result = self.document_processor.process_document(document_path)

            if not document_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to process document",
                    "details": document_result,
                }

            extracted_text = document_result["text"]
            logger.info(
                f"Extracted {document_result['word_count']} words from document"
            )

            # Step 2: Extract claims
            logger.info("Step 2: Extracting claims...")
            claims = self.claim_extractor.extract_claims(extracted_text)
            logger.info(f"Extracted {len(claims)} claims for fact-checking")

            if not claims:
                return {
                    "success": True,
                    "message": "No factual claims found in document",
                    "document_info": document_result["metadata"],
                    "claims": [],
                    "overall_authenticity": "no_claims",
                }

            # Step 3: Fact-check claims
            logger.info("Step 3: Fact-checking claims...")
            fact_check_results = await self.fact_checker.fact_check_claims(claims)

            # Step 4: Calculate authenticity scores
            logger.info("Step 4: Calculating authenticity scores...")
            scored_results = []

            for result in fact_check_results:
                if result.verification_status != "error":
                    # Calculate detailed authenticity score
                    scoring_breakdown = (
                        self.authenticity_scorer.calculate_authenticity_score(
                            claim_text=result.claim.text,
                            claim_type=result.claim.claim_type.value,
                            sources=result.sources_checked,
                            evidence=result.evidence,
                            contradictions=result.contradictions,
                            claim_entities=[e["text"] for e in result.claim.entities],
                        )
                    )

                    # Create comprehensive result
                    scored_result = {
                        "claim": {
                            "text": result.claim.text,
                            "type": result.claim.claim_type.value,
                            "confidence": result.claim.confidence,
                            "priority": result.claim.priority,
                            "entities": result.claim.entities,
                            "keywords": result.claim.keywords,
                        },
                        "verification": {
                            "status": result.verification_status,
                            "authenticity_score": scoring_breakdown.final_score,
                            "authenticity_level": scoring_breakdown.authenticity_level.value,
                            "confidence_interval": scoring_breakdown.confidence_interval,
                            "explanation": scoring_breakdown.explanation,
                        },
                        "scoring_breakdown": {
                            "source_credibility": scoring_breakdown.source_credibility_score,
                            "cross_reference": scoring_breakdown.cross_reference_score,
                            "evidence_quality": scoring_breakdown.evidence_quality_score,
                            "publication_date": scoring_breakdown.publication_date_score,
                            "expert_consensus": scoring_breakdown.expert_consensus_score,
                        },
                        "sources": result.sources_checked,
                        "evidence": result.evidence,
                        "contradictions": result.contradictions,
                        "processing_time": result.processing_time,
                    }
                else:
                    # Handle error cases
                    scored_result = {
                        "claim": {
                            "text": result.claim.text,
                            "type": result.claim.claim_type.value,
                            "confidence": result.claim.confidence,
                            "priority": result.claim.priority,
                        },
                        "verification": {
                            "status": "error",
                            "error_message": result.error_message,
                        },
                    }

                scored_results.append(scored_result)

            # Step 5: Calculate overall document authenticity
            overall_authenticity = self._calculate_overall_authenticity(scored_results)

            # Generate final report
            report = {
                "success": True,
                "document_info": document_result["metadata"],
                "summary": {
                    "total_claims": len(claims),
                    "verified_claims": len(
                        [
                            r
                            for r in scored_results
                            if r["verification"]["status"] == "verified"
                        ]
                    ),
                    "disputed_claims": len(
                        [
                            r
                            for r in scored_results
                            if r["verification"]["status"] == "disputed"
                        ]
                    ),
                    "unverified_claims": len(
                        [
                            r
                            for r in scored_results
                            if r["verification"]["status"] == "unverified"
                        ]
                    ),
                    "overall_authenticity_score": overall_authenticity["score"],
                    "overall_authenticity_level": overall_authenticity["level"],
                    "recommendation": overall_authenticity["recommendation"],
                },
                "claims": scored_results,
                "processing_metadata": {
                    "extraction_method": document_result["metadata"].get(
                        "processing_method"
                    ),
                    "total_processing_time": sum(
                        r.processing_time for r in fact_check_results
                    ),
                    "timestamp": str(asyncio.get_event_loop().time()),
                },
            }

            logger.info("Document analysis completed successfully")

            # Security cleanup: Ensure document is securely deleted after processing
            try:
                self.security_manager.secure_document_cleanup(document_path)
            except Exception as cleanup_error:
                logger.warning(f"Document cleanup warning: {cleanup_error}")

            return report

        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}")

            # Attempt cleanup even on error
            try:
                self.security_manager.secure_document_cleanup(document_path)
            except Exception as cleanup_error:
                logger.warning(f"Document cleanup warning: {cleanup_error}")

            return {
                "success": False,
                "error": str(e),
                "timestamp": str(asyncio.get_event_loop().time()),
            }

    def _calculate_overall_authenticity(
        self, scored_results: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate overall document authenticity"""
        if not scored_results:
            return {
                "score": 0.0,
                "level": "no_claims",
                "recommendation": "No claims to verify",
            }

        # Get successful verifications only
        successful_results = [
            r
            for r in scored_results
            if r["verification"]["status"] != "error"
            and "authenticity_score" in r["verification"]
        ]

        if not successful_results:
            return {
                "score": 0.0,
                "level": "error",
                "recommendation": "Unable to verify claims due to processing errors",
            }

        # Calculate weighted average based on claim priority
        total_weighted_score = 0.0
        total_weight = 0.0

        for result in successful_results:
            score = result["verification"]["authenticity_score"]
            priority = result["claim"]["priority"]

            # Higher priority claims get more weight (priority 1 = weight 5, priority 5 = weight 1)
            weight = 6 - priority

            total_weighted_score += score * weight
            total_weight += weight

        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0

        # Determine overall level
        if overall_score >= 0.8:
            level = "highly_authentic"
            recommendation = "Document contains highly reliable information"
        elif overall_score >= 0.6:
            level = "mostly_authentic"
            recommendation = (
                "Document is generally reliable with some verification needed"
            )
        elif overall_score >= 0.4:
            level = "mixed_authenticity"
            recommendation = "Document contains mix of verified and unverified claims"
        elif overall_score >= 0.2:
            level = "low_authenticity"
            recommendation = (
                "Document contains questionable information - verify before use"
            )
        else:
            level = "unreliable"
            recommendation = "Document contains unreliable or false information"

        return {
            "score": overall_score,
            "level": level,
            "recommendation": recommendation,
        }

    @monitor_performance("text_fact_check")
    async def fact_check_text(
        self, text: str, user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Fact-check raw text without document processing

        Args:
            text: Text to fact-check
            user_id: User identifier

        Returns:
            Fact-check results
        """
        logger.info("Starting text fact-checking")

        try:
            # Extract claims
            claims = self.claim_extractor.extract_claims(text)

            if not claims:
                return {
                    "success": True,
                    "message": "No factual claims found in text",
                    "claims": [],
                }

            # Fact-check claims
            fact_check_results = await self.fact_checker.fact_check_claims(claims)

            # Calculate scores and format results
            formatted_results = []
            for result in fact_check_results:
                if result.verification_status != "error":
                    scoring_breakdown = (
                        self.authenticity_scorer.calculate_authenticity_score(
                            claim_text=result.claim.text,
                            claim_type=result.claim.claim_type.value,
                            sources=result.sources_checked,
                            evidence=result.evidence,
                            contradictions=result.contradictions,
                        )
                    )

                    formatted_result = {
                        "claim": result.claim.text,
                        "authenticity_score": scoring_breakdown.final_score,
                        "authenticity_level": scoring_breakdown.authenticity_level.value,
                        "explanation": scoring_breakdown.explanation,
                        "sources_count": len(result.sources_checked),
                        "evidence_count": len(result.evidence),
                        "contradictions_count": len(result.contradictions),
                        "evidence": [
                            {
                                "sentence": evidence.get("sentence", ""),
                                "source_url": evidence.get("source_url", ""),
                                "source_domain": evidence.get("source_domain", ""),
                                "relevance_score": evidence.get("relevance_score", 0.0),
                                "source_credibility": evidence.get("source_credibility", 0.0),
                                "logical_reasoning": evidence.get("logical_reasoning", "Supports the claim based on content analysis"),
                                "matched_keywords": evidence.get("matched_keywords", []),
                                "supporting_indicators": evidence.get("supporting_indicators", [])
                            }
                            for evidence in result.evidence
                        ],
                        "contradictions": [
                            {
                                "sentence": contradiction.get("sentence", ""),
                                "source_url": contradiction.get("source_url", ""),
                                "source_domain": contradiction.get("source_domain", ""),
                                "relevance_score": contradiction.get("relevance_score", 0.0),
                                "source_credibility": contradiction.get("source_credibility", 0.0),
                                "logical_reasoning": contradiction.get("logical_reasoning", "Contradicts the claim based on content analysis"),
                                "matched_keywords": contradiction.get("matched_keywords", []),
                                "contradictory_indicators": contradiction.get("contradictory_indicators", []),
                                "contradiction_type": contradiction.get("contradiction_type", "general")
                            }
                            for contradiction in result.contradictions
                        ],
                    }
                    formatted_results.append(formatted_result)

            return {"success": True, "results": formatted_results}

        except Exception as e:
            logger.error(f"Error fact-checking text: {str(e)}")
            return {"success": False, "error": str(e)}

    def create_session(self, user_id: str, ip_address: str = None) -> str:
        """Create a new secure session for the user"""
        session_id = self.security_manager.create_secure_session(user_id, ip_address)

        # Also maintain legacy session format for compatibility
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": asyncio.get_event_loop().time(),
            "history": [],
        }

        return session_id

    async def chat_query(self, user_id: str, session_id: str, message: str) -> str:
        """
        Handle chat queries about fact-checking

        Args:
            user_id: User identifier
            session_id: Session identifier
            message: User message

        Returns:
            Agent response
        """
        try:
            # Security validation
            if not self.security_manager.validate_session(session_id, user_id):
                return "Invalid or expired session. Please create a new session."

            # Validate legacy session
            if session_id not in self.sessions:
                return "Session not found. Please create a new session."

            session = self.sessions[session_id]
            if session["user_id"] != user_id:
                return "Invalid session for this user."

            # Anonymize potentially sensitive information in the message
            safe_message = self.security_manager.anonymize_sensitive_data(message)

            # Prepare context for fact-checking
            context_prompt = f"""
            You are a fact-checking AI assistant. Your role is to help users understand fact-checking processes, 
            provide information about document analysis, and explain authenticity scoring.
            
            User question: {safe_message}
            
            Guidelines:
            - Be helpful and informative about fact-checking
            - Explain how the system works when asked
            - Suggest document analysis when appropriate
            - Be concise but thorough
            """

            # Generate response using Vertex AI
            response = self.model.generate_content(context_prompt)
            response_text = response.text

            # Store in session history
            session["history"].append(
                {
                    "user": message,
                    "assistant": response_text,
                    "timestamp": asyncio.get_event_loop().time(),
                }
            )

            return response_text

        except Exception as e:
            logger.error(f"Error processing chat query: {str(e)}")
            return f"I apologize, but I encountered an error processing your request: {str(e)}"

    def generate_json_report(
        self, results: Dict[str, Any], output_path: str = None
    ) -> str:
        """
        Generate structured JSON report

        Args:
            results: Analysis results
            output_path: Optional output file path

        Returns:
            JSON report string
        """
        return self.report_generator.generate_json_report(results, output_path)

    def generate_html_report(
        self, results: Dict[str, Any], output_path: str = None
    ) -> str:
        """
        Generate human-readable HTML report

        Args:
            results: Analysis results
            output_path: Optional output file path

        Returns:
            HTML report string
        """
        return self.report_generator.generate_html_report(results, output_path)

    def get_privacy_report(self) -> Dict[str, Any]:
        """
        Generate privacy compliance report

        Returns:
            Privacy report dictionary
        """
        return self.security_manager.generate_privacy_report()

    def get_audit_log(self, start_time: str = None, end_time: str = None) -> List[Dict]:
        """
        Get audit log for security monitoring

        Args:
            start_time: Start timestamp (ISO format)
            end_time: End timestamp (ISO format)

        Returns:
            List of audit events
        """
        return self.security_manager.get_audit_log(start_time, end_time)

    def check_user_permission(self, session_id: str, permission: str) -> bool:
        """
        Check if user has specific permission

        Args:
            session_id: Session identifier
            permission: Permission to check

        Returns:
            True if permission granted
        """
        return self.security_manager.check_permission(session_id, permission)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get system performance metrics

        Returns:
            Performance metrics dictionary
        """
        return self.performance_monitor.get_performance_metrics()

    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """
        Get performance alerts for issues requiring attention

        Returns:
            List of performance alerts
        """
        return self.performance_monitor.get_performance_alerts()

    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """
        Get optimization recommendations based on performance data

        Returns:
            Optimization recommendations
        """
        return self.performance_monitor.optimize_settings()

    def get_search_provider_stats(self) -> Dict[str, Any]:
        """
        Get search provider health and usage statistics
        
        Returns:
            Search provider statistics including health, configuration, and usage
        """
        return self.fact_checker.get_search_provider_stats()

    async def process_batch_documents(
        self,
        document_paths: List[str],
        user_id: str = "default_user",
        session_id: str = None,
        max_concurrent: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Process multiple documents concurrently with throttling

        Args:
            document_paths: List of document paths to process
            user_id: User identifier
            session_id: Session identifier
            max_concurrent: Maximum concurrent processing

        Returns:
            List of analysis results
        """
        # Update concurrent limit
        self.performance_monitor.max_concurrent = max_concurrent

        async def process_single_doc(doc_path):
            return await with_throttling(
                self.analyze_document(doc_path, user_id, session_id)
            )

        # Process documents with concurrency control
        tasks = [process_single_doc(doc_path) for doc_path in document_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {
                        "success": False,
                        "error": str(result),
                        "document_path": document_paths[i],
                    }
                )
            else:
                processed_results.append(result)

        return processed_results


# Global agent instance
fact_check_agent = None


def get_fact_check_agent() -> FactCheckAgent:
    """Get or create the global fact check agent instance"""
    global fact_check_agent
    if fact_check_agent is None:
        fact_check_agent = FactCheckAgent()
    return fact_check_agent


# Agent functions for document analysis and fact-checking
async def analyze_document_function(
    document_path: str, user_id: str = "default_user"
) -> str:
    """
    Analyze a document and return comprehensive fact-check results

    Args:
        document_path: Path to the document file (PDF, DOCX, or image)
        user_id: User identifier for session management

    Returns:
        JSON string containing fact-check analysis results
    """
    agent = get_fact_check_agent()
    result = await agent.analyze_document(document_path, user_id)
    return json.dumps(result, indent=2)


async def fact_check_text_function(text: str, user_id: str = "default_user") -> str:
    """
    Fact-check a piece of text and return authenticity scores

    Args:
        text: Text content to fact-check
        user_id: User identifier

    Returns:
        JSON string containing fact-check results
    """
    agent = get_fact_check_agent()
    result = await agent.fact_check_text(text, user_id)
    return json.dumps(result, indent=2)


def get_supported_formats() -> str:
    """
    Get list of supported document formats

    Returns:
        JSON string with supported formats and limitations
    """
    return json.dumps(
        {
            "supported_formats": config.supported_formats,
            "max_file_size_mb": config.max_document_size_mb,
            "ocr_language": config.ocr_language,
        }
    )


def get_agent_capabilities() -> str:
    """
    Get information about agent capabilities

    Returns:
        JSON string describing agent capabilities
    """
    capabilities = {
        "document_processing": {
            "ocr": True,
            "formats": config.supported_formats,
            "max_size_mb": config.max_document_size_mb,
        },
        "claim_extraction": {
            "types": [
                "political",
                "medical",
                "scientific",
                "financial",
                "technology",
                "general",
            ],
            "entity_recognition": True,
            "keyword_extraction": True,
        },
        "fact_checking": {
            "sources": "Multiple credible sources including government, academic, and news",
            "cross_referencing": True,
            "contradiction_detection": True,
        },
        "scoring": {
            "authenticity_scale": "0.0 to 1.0",
            "confidence_intervals": True,
            "detailed_breakdown": True,
        },
    }

    return json.dumps(capabilities, indent=2)

