"""
Sample usage examples for the Fact Check Agent
"""
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import asyncio
import json
from pathlib import Path

from fact_check_agent.fact_check_agent import FactCheckAgent

async def example_1_text_fact_checking():
    """Example 1: Basic text fact-checking"""
    print("=== Example 1: Text Fact-Checking ===\n")
    
    agent = FactCheckAgent()
    
    sample_claims = [
        "The COVID-19 vaccine is 95% effective according to clinical trials.",
        "Climate change has increased global temperatures by 1.1°C since 1880.",
        "Artificial intelligence will replace 50% of jobs by 2025.",
        "The Federal Reserve raised interest rates to 5.25% in 2023."
    ]
    
    for i, claim in enumerate(sample_claims, 1):
        print(f"Claim {i}: {claim}")
        result = await agent.fact_check_text(claim)
        
        if result['success'] and result.get('results'):
            for claim_result in result['results']:
                print(f"  ✓ Authenticity Score: {claim_result['authenticity_score']:.2f}")
                print(f"  ✓ Level: {claim_result['authenticity_level']}")
                print(f"  ✓ Sources Checked: {claim_result['sources_count']}")
                print(f"  ✓ Evidence Found: {claim_result['evidence_count']}")
        print()

async def example_2_comprehensive_analysis():
    """Example 2: Comprehensive document analysis"""
    print("=== Example 2: Comprehensive Analysis ===\n")
    
    agent = FactCheckAgent()
    
    # Sample text that would typically come from a document
    document_text = """
    Medical Research Summary Report
    
    Recent studies from Johns Hopkins University demonstrate that regular 
    exercise reduces the risk of cardiovascular disease by 35%. This finding 
    is supported by a meta-analysis of 25 studies involving over 100,000 participants.
    
    The World Health Organization reports that cardiovascular diseases are 
    the leading cause of death globally, accounting for 17.9 million deaths 
    per year, which represents 31% of all global deaths.
    
    A breakthrough study published in Nature Medicine shows that a new 
    gene therapy treatment has achieved 90% success rates in treating 
    rare genetic disorders in preliminary trials.
    
    According to the CDC, vaccination rates for measles have declined 
    to 89% nationally, falling below the 95% threshold needed for 
    herd immunity protection.
    """
    
    result = await agent.fact_check_text(document_text)
    
    if result['success']:
        print(f"Analysis completed successfully!")
        print(f"Total claims analyzed: {len(result.get('results', []))}")
        
        for i, claim_result in enumerate(result['results'], 1):
            print(f"\n--- Claim {i} ---")
            print(f"Text: {claim_result['claim'][:100]}...")
            print(f"Score: {claim_result['authenticity_score']:.2f}")
            print(f"Level: {claim_result['authenticity_level']}")
            print(f"Explanation: {claim_result.get('explanation', 'N/A')}")
            print(f"Sources: {claim_result['sources_count']}")
            
            # Show interpretation
            if claim_result['authenticity_score'] >= 0.8:
                print("✅ HIGH CONFIDENCE - Safe to cite")
            elif claim_result['authenticity_score'] >= 0.6:
                print("⚠️  MODERATE CONFIDENCE - Consider verification")
            else:
                print("❌ LOW CONFIDENCE - Requires additional verification")

async def example_3_agent_capabilities():
    """Example 3: Demonstrate agent capabilities"""
    print("=== Example 3: Agent Capabilities ===\n")
    
    from fact_check_agent.fact_check_agent import get_agent_capabilities, get_supported_formats
    
    # Show capabilities
    capabilities = json.loads(get_agent_capabilities())
    print("Agent Capabilities:")
    print(f"  • Document Processing: {capabilities['document_processing']['formats']}")
    print(f"  • Max File Size: {capabilities['document_processing']['max_size_mb']} MB")
    print(f"  • Claim Types: {capabilities['claim_extraction']['types']}")
    print(f"  • Scoring Range: {capabilities['scoring']['authenticity_scale']}")
    
    # Show supported formats
    formats = json.loads(get_supported_formats())
    print(f"\nSupported Formats: {formats['supported_formats']}")
    print(f"OCR Language: {formats['ocr_language']}")

async def example_4_session_management():
    """Example 4: Session management and chat"""
    print("=== Example 4: Session Management ===\n")
    
    agent = FactCheckAgent()
    
    # Create session
    user_id = "demo_user_123"
    session_id = agent.create_session(user_id)
    print(f"Created session: {session_id}")
    
    # Sample chat interactions
    chat_queries = [
        "How do you calculate authenticity scores?",
        "What sources do you consider most credible for medical claims?",
        "Can you explain your fact-checking process?"
    ]
    
    for query in chat_queries:
        print(f"\nUser: {query}")
        response = await agent.chat_query(user_id, session_id, query)
        print(f"Agent: {response[:200]}...")  # Truncate for demo

def example_5_scoring_interpretation():
    """Example 5: Understanding authenticity scores"""
    print("=== Example 5: Scoring Interpretation ===\n")
    
    from fact_check_agent.authenticity_scorer import AuthenticityScorer
    
    scorer = AuthenticityScorer()
    
    # Example score interpretations
    test_scores = [0.95, 0.75, 0.55, 0.35, 0.15]
    
    print("Authenticity Score Interpretations:")
    for score in test_scores:
        interpretation = scorer.get_score_interpretation(score)
        print(f"\nScore: {score:.2f} ({interpretation['percentage']})")
        print(f"Level: {interpretation['level']}")
        print(f"Recommendation: {interpretation['recommendation']}")
        print(f"Color Code: {interpretation['color_code']}")

async def example_6_error_handling():
    """Example 6: Error handling and edge cases"""
    print("=== Example 6: Error Handling ===\n")
    
    agent = FactCheckAgent()
    
    # Test with empty text
    result = await agent.fact_check_text("")
    print(f"Empty text result: {result}")
    
    # Test with non-factual text
    opinion_text = "I think pizza is the best food ever and everyone should eat it daily."
    result = await agent.fact_check_text(opinion_text)
    print(f"Opinion text result: {result['success']}")
    if result.get('results'):
        print(f"Claims found: {len(result['results'])}")
    else:
        print("No factual claims detected in opinion text")

async def main():
    """Run all examples"""
    print("🔍 Fact Check Agent - Sample Usage Examples\n")
    print("=" * 60)
    
    try:
        await example_1_text_fact_checking()
        await example_2_comprehensive_analysis()
        await example_3_agent_capabilities()
        await example_4_session_management()
        example_5_scoring_interpretation()
        await example_6_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("\nNext steps:")
        print("1. Try the interactive mode: python main.py --mode interactive")
        print("2. Test with your own documents: python main.py --mode document --input your_file.pdf")
        print("3. Integrate into your application using the Python API")
        
    except Exception as e:
        print(f"❌ Error running examples: {str(e)}")
        print("Make sure you have:")
        print("1. Set up Google Cloud credentials")
        print("2. Installed all dependencies")
        print("3. Configured your .env file")

if __name__ == "__main__":
    asyncio.run(main())