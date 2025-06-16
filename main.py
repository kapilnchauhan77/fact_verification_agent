"""
Main entry point for the Fact Check Agent
"""
import asyncio
import argparse
import json
import logging
from pathlib import Path

from src.fact_check_agent.fact_check_agent import FactCheckAgent, get_fact_check_agent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Fact Check Agent')
    parser.add_argument('--mode', choices=['document', 'text', 'interactive'], 
                       default='interactive', help='Operation mode')
    parser.add_argument('--input', help='Input file path or text')
    parser.add_argument('--output', help='Output file path for results')
    parser.add_argument('--user-id', default='default_user', help='User identifier')
    
    args = parser.parse_args()
    
    try:
        agent = get_fact_check_agent()
        
        if args.mode == 'document':
            if not args.input:
                print("Error: --input required for document mode")
                return
            
            if not Path(args.input).exists():
                print(f"Error: File not found: {args.input}")
                return
            
            print(f"Analyzing document: {args.input}")
            result = await agent.analyze_document(args.input, args.user_id)
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"Results saved to: {args.output}")
            else:
                print(json.dumps(result, indent=2))
        
        elif args.mode == 'text':
            if not args.input:
                print("Error: --input required for text mode")
                return
            
            print(f"Fact-checking text: {args.input[:100]}...")
            result = await agent.fact_check_text(args.input, args.user_id)
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"Results saved to: {args.output}")
            else:
                print(json.dumps(result, indent=2))
        
        elif args.mode == 'interactive':
            await interactive_mode(agent, args.user_id)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"Error: {str(e)}")

async def interactive_mode(agent: FactCheckAgent, user_id: str):
    """Interactive mode for testing the agent"""
    print("=== Fact Check Agent - Interactive Mode ===")
    print("Commands:")
    print("  doc <file_path>     - Analyze a document")
    print("  text <text>         - Fact-check text")
    print("  chat <message>      - Chat with the agent")
    print("  help                - Show this help")
    print("  quit                - Exit")
    print()
    
    session_id = None
    
    while True:
        try:
            command = input("> ").strip()
            
            if not command:
                continue
            
            if command.lower() in ['quit', 'exit', 'q']:
                break
            
            elif command.lower() == 'help':
                print("Commands:")
                print("  doc <file_path>     - Analyze a document")
                print("  text <text>         - Fact-check text")
                print("  chat <message>      - Chat with the agent")
                print("  help                - Show this help")
                print("  quit                - Exit")
            
            elif command.startswith('doc '):
                file_path = command[4:].strip()
                if not Path(file_path).exists():
                    print(f"File not found: {file_path}")
                    continue
                
                print("Analyzing document...")
                result = await agent.analyze_document(file_path, user_id)
                
                if result['success']:
                    print("\n=== ANALYSIS RESULTS ===")
                    print(f"Document: {result['document_info']['file_name']}")
                    print(f"Total Claims: {result['summary']['total_claims']}")
                    print(f"Verified: {result['summary']['verified_claims']}")
                    print(f"Disputed: {result['summary']['disputed_claims']}")
                    print(f"Overall Score: {result['summary']['overall_authenticity_score']:.2f}")
                    print(f"Recommendation: {result['summary']['recommendation']}")
                    
                    if result['claims']:
                        print("\n=== TOP CLAIMS ===")
                        for i, claim in enumerate(result['claims'][:3], 1):
                            print(f"\n{i}. {claim['claim']['text'][:100]}...")
                            print(f"   Score: {claim['verification']['authenticity_score']:.2f}")
                            print(f"   Level: {claim['verification']['authenticity_level']}")
                            print(f"   Sources: {len(claim['sources'])}")
                else:
                    print(f"Error: {result['error']}")
            
            elif command.startswith('text '):
                text = command[5:].strip()
                print("Fact-checking text...")
                result = await agent.fact_check_text(text, user_id)
                
                if result['success']:
                    if result.get('results'):
                        print("\n=== FACT-CHECK RESULTS ===")
                        for i, claim_result in enumerate(result['results'], 1):
                            print(f"\n{i}. {claim_result['claim'][:80]}...")
                            print(f"   Score: {claim_result['authenticity_score']:.2f}")
                            print(f"   Level: {claim_result['authenticity_level']}")
                            print(f"   Sources: {claim_result['sources_count']}")
                            print(f"   Evidence: {claim_result['evidence_count']}")
                    else:
                        print("No factual claims found in the text.")
                else:
                    print(f"Error: {result['error']}")
            
            elif command.startswith('chat '):
                message = command[5:].strip()
                
                if not session_id:
                    session_id = agent.create_session(user_id)
                    print(f"Created chat session: {session_id}")
                
                print("Sending message to agent...")
                response = await agent.chat_query(user_id, session_id, message)
                print(f"\nAgent: {response}")
            
            else:
                print("Unknown command. Type 'help' for available commands.")
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())