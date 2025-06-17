"""
Demo script showing search provider fallback functionality
Run this to test the search fallback system with different API configurations
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.fact_check_agent.search_services import unified_search_service
from src.fact_check_agent.config import config
import logging

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def demo_search_fallback():
    """Demonstrate search provider fallback functionality"""
    
    print("=== Search Provider Fallback Demo ===\n")
    
    # Show current configuration
    print("Current Search Provider Configuration:")
    stats = unified_search_service.get_provider_stats()
    config_info = stats['configuration']
    
    print(f"🔑 SERP API: {'✅ Configured' if config_info['serp_api_configured'] else '❌ Not configured'}")
    print(f"🔑 Google Custom Search: {'✅ Configured' if config_info['google_custom_search_configured'] else '❌ Not configured'}")
    print(f"🔑 DuckDuckGo: {'✅ Available' if config_info['duckduckgo_available'] else '❌ Not available'}")
    
    print(f"\nAvailable providers in priority order: {stats['available_providers']}")
    print()
    
    # Test searches with different queries
    test_queries = [
        "climate change facts",
        "COVID-19 vaccination effectiveness",
        "artificial intelligence latest research"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: Searching for '{query}' ---")
        
        try:
            response = await unified_search_service.search(query, max_results=5)
            
            if response.results:
                print(f"✅ Success via {response.provider_used}")
                print(f"📊 Found {len(response.results)} results in {response.processing_time:.2f}s")
                print(f"💾 Cache: {'HIT' if response.cache_hit else 'MISS'}")
                
                print("\nTop results:")
                for j, result in enumerate(response.results[:3], 1):
                    print(f"  {j}. {result.title[:60]}...")
                    print(f"     🌐 {result.domain} (score: {result.relevance_score:.2f})")
                    
            else:
                print(f"❌ No results found")
                if response.error_message:
                    print(f"Error: {response.error_message}")
                    
        except Exception as e:
            print(f"❌ Search failed: {str(e)}")
    
    # Show provider health after searches
    print("\n=== Provider Health After Searches ===")
    updated_stats = unified_search_service.get_provider_stats()
    health = updated_stats['provider_health']
    
    for provider, health_info in health.items():
        failures = health_info['consecutive_failures']
        last_success = health_info['last_success']
        
        if failures == 0:
            status = "✅ Healthy"
        elif failures < 3:
            status = f"⚠️  {failures} failures"
        else:
            status = f"❌ Unhealthy ({failures} failures)"
            
        print(f"{provider}: {status}")
        if last_success:
            print(f"  Last success: {last_success.strftime('%H:%M:%S')}")

async def demo_configuration_scenarios():
    """Demo different configuration scenarios"""
    
    print("\n\n=== Configuration Scenarios Demo ===\n")
    
    # Show what happens with different API key configurations
    scenarios = [
        {
            "name": "All APIs configured",
            "description": "Best case: SERP API + Google Custom Search + DuckDuckGo"
        },
        {
            "name": "Only Google Custom Search",
            "description": "SERP API down, fallback to Google Custom Search"
        },
        {
            "name": "Only DuckDuckGo",
            "description": "All paid APIs exhausted, fallback to free DuckDuckGo"
        }
    ]
    
    for scenario in scenarios:
        print(f"📋 Scenario: {scenario['name']}")
        print(f"   {scenario['description']}")
        print()

def show_setup_instructions():
    """Show setup instructions for API keys"""
    
    print("\n\n=== API Setup Instructions ===\n")
    
    instructions = [
        {
            "service": "SERP API (Primary)",
            "steps": [
                "1. Visit https://serpapi.com/",
                "2. Create an account",
                "3. Get your API key from dashboard",
                "4. Set SERP_API_KEY environment variable",
                "5. Free tier: 100 searches/month"
            ]
        },
        {
            "service": "Google Custom Search (Fallback)",
            "steps": [
                "1. Go to Google Cloud Console",
                "2. Enable Custom Search JSON API",
                "3. Create API credentials (API key)",
                "4. Set up Custom Search Engine at https://cse.google.com/",
                "5. Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID",
                "6. Free tier: 100 searches/day"
            ]
        },
        {
            "service": "DuckDuckGo (Always Available)",
            "steps": [
                "1. No setup required!",
                "2. Automatically used as final fallback",
                "3. No API key needed",
                "4. Rate limited but free"
            ]
        }
    ]
    
    for instruction in instructions:
        print(f"🔧 {instruction['service']}:")
        for step in instruction['steps']:
            print(f"   {step}")
        print()

async def main():
    """Main demo function"""
    
    print("🚀 Starting Search Provider Fallback Demo\n")
    
    # Check if we're in a proper environment
    if not any([config.serp_api_key, config.google_search_api_key]):
        print("⚠️  Warning: No search API keys configured!")
        print("This demo will only show DuckDuckGo results.")
        print("For full functionality, configure API keys as shown below.\n")
        show_setup_instructions()
        
        # Ask if user wants to continue with limited functionality
        response = input("Continue with DuckDuckGo only? (y/N): ")
        if response.lower() != 'y':
            print("Demo cancelled. Configure API keys and try again.")
            return
    
    # Run the main demo
    await demo_search_fallback()
    
    # Show configuration scenarios
    await demo_configuration_scenarios()
    
    # Show setup instructions
    show_setup_instructions()
    
    print("\n✅ Demo completed!")
    print("\nNext steps:")
    print("1. Configure API keys using .env.example as a template")
    print("2. Run fact-checking with: python main.py --mode interactive")
    print("3. Monitor search provider usage in logs")

if __name__ == "__main__":
    asyncio.run(main())