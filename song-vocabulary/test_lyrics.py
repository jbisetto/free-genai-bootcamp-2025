#!/usr/bin/env python3
"""
Test script to verify the get_lyrics functionality without making web calls.
"""
import json
from app.tools.get_lyrics import get_lyrics

def test_mock_lyrics():
    """Test the mock lyrics functionality"""
    print("\n=== Testing Mock Lyrics Functionality ===")
    
    # Test with mock data
    result = get_lyrics("Lemon", "Kenshi Yonezu", use_mock=True)
    
    # Print the results
    print(f"Success: {result['success']}")
    print(f"Lyrics length: {len(result['lyrics'])} characters")
    print(f"Language: {result['metadata']['language']}")
    print(f"Fetched at: {result['metadata']['fetched_at']}")
    print(f"Is mock: {result['metadata'].get('is_mock', False)}")
    
    # Verify no cache-related fields are present
    print("\nVerifying no cache fields are present:")
    print(f"'cache_info' in result: {'cache_info' in result}")
    
    # Pretty print the full result
    print("\nFull result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result['success']

if __name__ == "__main__":
    test_mock_lyrics()
