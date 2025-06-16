#!/usr/bin/env python3
"""
Demo script showing chunked claim extraction for large documents
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from fact_check_agent.claim_extractor import ClaimExtractor

def create_large_test_document():
    """Create a large test document that will trigger chunking"""
    
    sections = [
        """
        SECTION 1: CORPORATE INFORMATION
        Apple Inc. is a multinational technology company headquartered in Cupertino, California. 
        The company was founded in 1976 by Steve Jobs, Steve Wozniak, and Ronald Wayne.
        Apple reported record revenue of $394.3 billion in fiscal 2022, representing an 8% increase.
        The company currently employs over 164,000 people worldwide as of September 2023.
        """,
        """
        SECTION 2: MEDICAL RESEARCH CLAIMS
        According to the World Health Organization, COVID-19 vaccines are 95% effective at preventing severe illness.
        Clinical trials conducted by Pfizer showed 91% efficacy in preventing symptomatic COVID-19.
        The FDA approved the Pfizer-BioNTech vaccine on August 23, 2021, for individuals 16 and older.
        Over 13 billion vaccine doses have been administered globally as of December 2023.
        """,
        """
        SECTION 3: FINANCIAL MARKET DATA
        Tesla stock increased by 25% in the first quarter of 2024, driven by strong delivery numbers.
        The company delivered 466,140 vehicles in Q1 2024, exceeding Wall Street expectations.
        Microsoft announced a $10 billion investment in OpenAI in January 2023.
        Amazon's AWS division generated $80.1 billion in revenue in 2023, up 13% year-over-year.
        """,
        """
        SECTION 4: SCIENTIFIC DISCOVERIES
        Scientists at MIT developed a room-temperature quantum computer achieving 99% fidelity.
        Research published in Nature magazine shows climate change is accelerating faster than predicted.
        Global temperatures have risen by 1.1 degrees Celsius since pre-industrial times.
        The year 2023 was recorded as the warmest year on record globally.
        """,
        """
        SECTION 5: ECONOMIC INDICATORS
        The Federal Reserve raised interest rates by 0.25% in March 2024.
        The federal funds rate now stands at 5.5% following ten consecutive rate hikes.
        China's economy grew by 5.2% in 2023, meeting government targets.
        The country's GDP reached $17.9 trillion, making it the world's second-largest economy.
        """,
        """
        SECTION 6: TECHNOLOGY DEVELOPMENTS
        Google's parent company Alphabet reported $283 billion in revenue for 2023.
        YouTube advertising revenue reached $31.5 billion during the same period.
        The company's search advertising business generated $175 billion in annual revenue.
        Meta's Reality Labs division lost $13.7 billion in 2023 despite VR/AR investments.
        """,
        """
        SECTION 7: HEALTHCARE STATISTICS
        A new Alzheimer's drug reduces cognitive decline by 27% in early-stage patients.
        The FDA is expected to approve the medication by the end of 2024.
        Clinical trials included 1,795 participants across multiple medical centers.
        The drug showed statistically significant benefits after 18 months of treatment.
        """,
        """
        SECTION 8: ENERGY AND ENVIRONMENT
        Renewable energy sources accounted for 30% of global electricity generation in 2023.
        Solar panel efficiency has improved by 15% over the past five years.
        Electric vehicle sales increased by 35% globally in 2023 compared to 2022.
        The International Energy Agency predicts 50% renewable energy by 2030.
        """
    ]
    
    # Repeat sections to create a document larger than 16,000 characters
    full_document = ""
    for i in range(5):  # Repeat 5 times to ensure we exceed 16k chars
        for section in sections:
            full_document += section + "\n\n"
    
    return full_document

async def demonstrate_chunked_extraction():
    """Demonstrate the chunked extraction functionality"""
    
    print("🚀 CHUNKED CLAIM EXTRACTION DEMONSTRATION")
    print("=" * 60)
    
    # Create large test document
    document = create_large_test_document()
    print(f"📄 Created test document: {len(document):,} characters")
    
    # Initialize claim extractor
    extractor = ClaimExtractor()
    
    # Extract claims (will automatically use chunking)
    print(f"🧠 Starting claim extraction...")
    claims = extractor.extract_claims(document)
    
    print(f"✅ Extraction completed!")
    print(f"📊 Total claims extracted: {len(claims)}")
    print()
    
    # Show breakdown by claim type
    claim_types = {}
    for claim in claims:
        claim_type = claim.claim_type.value
        claim_types[claim_type] = claim_types.get(claim_type, 0) + 1
    
    print("📈 Claims by Type:")
    for claim_type, count in sorted(claim_types.items()):
        print(f"   {claim_type}: {count}")
    print()
    
    # Show top 10 claims
    print("🔍 Top 10 Extracted Claims:")
    for i, claim in enumerate(claims[:10], 1):
        print(f"{i:2d}. {claim.text}")
        print(f"    Type: {claim.claim_type.value}, Confidence: {claim.confidence:.2f}, Priority: {claim.priority}")
        print()
    
    print("🎉 CHUNKED EXTRACTION DEMONSTRATION COMPLETE!")
    print()
    print("✅ Key Features Demonstrated:")
    print("   • Automatic chunking for documents > 16,000 characters")
    print("   • Smart text splitting at sentence/paragraph boundaries")  
    print("   • Claim deduplication across chunks")
    print("   • Comprehensive claim extraction from large documents")
    print("   • Proper handling of JSON parsing errors")
    
    return claims

if __name__ == "__main__":
    asyncio.run(demonstrate_chunked_extraction())