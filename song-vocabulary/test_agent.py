"""
Test script for the vocabulary agent.
"""
import json
import sys
import logging
from app.agent.agent import run_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Run a test of the agent with a specific song."""
    if len(sys.argv) > 1:
        song = sys.argv[1]
        artist = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # Default to a Japanese song for better vocabulary extraction
        song = "Lemon"
        artist = "Kenshi Yonezu"
    
    print(f"Testing agent with song: {song}, artist: {artist}")
    
    try:
        print(f"\n=== Starting agent run for '{song}' by '{artist}' ===\n")
        
        # Run the agent
        result = run_agent(song, artist)
        
        # Print result type and structure
        print(f"\n=== Agent run completed ===\n")
        print(f"Result type: {type(result)}")
        if isinstance(result, dict):
            print(f"Result keys: {result.keys()}")
            
            # If we have vocabulary, print some stats
            if "vocabulary" in result and isinstance(result["vocabulary"], list):
                print(f"Vocabulary items: {len(result['vocabulary'])}")
                # For testing purposes, we expect at least 5 vocabulary items
                if len(result["vocabulary"]) < 5:
                    print("WARNING: Expected at least 5 vocabulary items for testing")
                if result["vocabulary"]:
                    print(f"First item type: {type(result['vocabulary'][0])}")
                    if isinstance(result["vocabulary"][0], dict):
                        print(f"First item keys: {result['vocabulary'][0].keys()}")
        
        # Try to serialize to JSON
        json_result = json.dumps(result, ensure_ascii=False)
        print("JSON serialization successful")
        
        # Print the result
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
