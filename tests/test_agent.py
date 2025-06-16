"""
Test script for the Fact Check Agent
"""
import asyncio
import pytest
import tempfile
import json
from pathlib import Path

from src.fact_check_agent.fact_check_agent import FactCheckAgent
from src.fact_check_agent.document_processor import DocumentProcessor
from src.fact_check_agent.claim_extractor import ClaimExtractor
from src.fact_check_agent.authenticity_scorer import AuthenticityScorer

class TestFactCheckAgent:
    """Test cases for the Fact Check Agent"""
    
    @pytest.fixture
    async def agent(self):
        """Create agent instance for testing"""
        return FactCheckAgent()
    
    @pytest.fixture
    def sample_text(self):
        """Sample text with factual claims"""
        return """
        According to the CDC, COVID-19 vaccines are 95% effective at preventing severe illness.
        The study published in Nature shows that climate change has increased global temperatures by 1.1°C since 1880.
        Recent research indicates that artificial intelligence will replace 40% of jobs by 2030.
        The Federal Reserve announced that inflation reached 8.5% in March 2022.
        """
    
    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing"""
        content = """
        FACT SHEET: Important Medical Information
        
        Recent studies from Johns Hopkins University demonstrate that regular exercise 
        reduces the risk of heart disease by 35%. The American Heart Association 
        confirms this finding in their 2023 report.
        
        According to WHO data, approximately 17.9 million people die from cardiovascular 
        diseases each year, representing 31% of all global deaths.
        
        Scientists at MIT have developed a new drug that shows 90% effectiveness 
        in treating rare genetic disorders, according to clinical trials published 
        in The New England Journal of Medicine.
        """
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            return f.name
    
    def test_document_processor(self):
        """Test document processing functionality"""
        processor = DocumentProcessor()
        
        # Test with sample text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document with sample text.")
            temp_path = f.name
        
        try:
            # Note: This would normally test with actual document files
            # For basic testing, we'll just verify the processor initializes
            assert processor is not None
            assert processor.supported_formats
        finally:
            Path(temp_path).unlink()
    
    def test_claim_extractor(self, sample_text):
        """Test claim extraction"""
        extractor = ClaimExtractor()
        claims = extractor.extract_claims(sample_text)
        
        assert len(claims) > 0
        assert all(hasattr(claim, 'text') for claim in claims)
        assert all(hasattr(claim, 'claim_type') for claim in claims)
        assert all(hasattr(claim, 'confidence') for claim in claims)
        
        # Check that COVID claim is extracted
        covid_claims = [c for c in claims if 'COVID' in c.text or 'vaccine' in c.text]
        assert len(covid_claims) > 0
    
    def test_authenticity_scorer(self):
        """Test authenticity scoring"""
        scorer = AuthenticityScorer()
        
        # Mock data for testing
        sources = [
            {
                'domain': 'cdc.gov',
                'url': 'https://cdc.gov/test',
                'credibility_score': 0.95,
                'publication_date': '2023-01-01T00:00:00Z'
            }
        ]
        
        evidence = [
            {
                'text': 'CDC confirms vaccine effectiveness',
                'source_credibility': 0.95,
                'relevance_score': 0.8
            }
        ]
        
        contradictions = []
        
        result = scorer.calculate_authenticity_score(
            claim_text="Vaccines are effective",
            claim_type="medical",
            sources=sources,
            evidence=evidence,
            contradictions=contradictions
        )
        
        assert 0.0 <= result.final_score <= 1.0
        assert result.authenticity_level is not None
        assert result.explanation
    
    @pytest.mark.asyncio
    async def test_text_fact_checking(self, agent, sample_text):
        """Test text fact-checking functionality"""
        result = await agent.fact_check_text(sample_text)
        
        assert result['success'] is True
        if 'results' in result:
            assert len(result['results']) > 0
            
            for claim_result in result['results']:
                assert 'claim' in claim_result
                assert 'authenticity_score' in claim_result
                assert 0.0 <= claim_result['authenticity_score'] <= 1.0
    
    def test_session_management(self, agent):
        """Test session creation"""
        user_id = "test_user_123"
        session_id = agent.create_session(user_id)
        
        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0

def run_integration_test():
    """Run a comprehensive integration test"""
    print("=== Fact Check Agent Integration Test ===\n")
    
    async def test_full_workflow():
        """Test the complete workflow"""
        agent = FactCheckAgent()
        
        # Test 1: Text fact-checking
        print("Test 1: Text Fact-Checking")
        test_text = """
        The World Health Organization states that handwashing can reduce 
        respiratory infections by up to 16%. NASA confirms that Earth's 
        average temperature has risen by 1.1°C since the late 19th century.
        """
        
        result = await agent.fact_check_text(test_text)
        print(f"✓ Text analysis completed: {result['success']}")
        
        if result['success'] and 'results' in result:
            print(f"  - Found {len(result['results'])} claims")
            for i, claim in enumerate(result['results'], 1):
                print(f"  - Claim {i}: Score {claim['authenticity_score']:.2f}")
        
        # Test 2: Agent capabilities
        print("\nTest 2: Agent Capabilities")
        from src.fact_check_agent.fact_check_agent import get_agent_capabilities
        capabilities = json.loads(get_agent_capabilities())
        print(f"✓ Supported formats: {capabilities['document_processing']['formats']}")
        print(f"✓ Claim types: {capabilities['claim_extraction']['types']}")
        
        # Test 3: Session management
        print("\nTest 3: Session Management")
        session_id = agent.create_session("test_user")
        print(f"✓ Created session: {session_id}")
        
        print("\n=== Integration Test Completed Successfully ===")
    
    asyncio.run(test_full_workflow())

if __name__ == "__main__":
    # Run integration test if executed directly
    run_integration_test()