"""Tool for fetching song lyrics using duckduckgo-search.

This module provides functionality to search for and retrieve lyrics for songs:

1. Search Capabilities:
   - Uses DuckDuckGo search API to find lyrics for songs
   - Supports searching by song name and optional artist name
   - Extracts lyrics from search results

2. Language Detection:
   - Automatically detects if lyrics are in Japanese or English
   - Provides language information in the returned metadata

3. Testing Support:
   - Includes a mock mode for testing without external API dependencies
   - Returns consistent test data when mock mode is enabled

Usage:
    lyrics_result = get_lyrics("Song Name", "Artist Name")
    
    # With mock data for testing
    test_result = get_lyrics("Song Name", "Artist Name", use_mock=True)
"""
import os
import json
import logging
import time
from typing import Optional, Dict, Any
from duckduckgo_search import DDGS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_lyrics(song: str, artist: Optional[str] = None, use_mock: bool = False) -> Dict[str, Any]:
    """
    Searches for and retrieves lyrics for a given song and artist.
    
    Args:
        song: The name of the song to search for
        artist: Optional artist name to narrow down the search
        use_mock: If True, returns mock data instead of making a web request
    
    Returns:
        A dictionary containing the lyrics and metadata
    """
    logger.info(f"Fetching lyrics for '{song}' by '{artist or 'Unknown'}', {'using mock data' if use_mock else 'from web'}")
    
    # If using mock mode, return mock lyrics
    if use_mock:
        # Generate mock lyrics based on song name
        mock_lyrics = f"""This is a mock lyrics for {song} by {artist or 'Unknown'}
        
Verse 1:
Imagine the first verse of the song here
With multiple lines of text to simulate real lyrics
This helps us test the functionality
Without relying on external APIs that might have rate limits

Chorus:
This is the {song} chorus
Repeated a few times
This is the {song} chorus
To make it more realistic

Verse 2:
Second verse continues the song
With more lines to increase the text size
So we can properly test our processing
And see how well the system works

Bridge:
A bridge section with different lyrics
To add variety to our mock song

Chorus:
This is the {song} chorus
Repeated a few times
This is the {song} chorus
One last time for the end

(End)
"""
        
        # Create metadata
        metadata = {
            "title": song,
            "artist": artist if artist else "Unknown",
            "source": "mock_data",
            "is_mock": True,
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Detect language (simple check for Japanese characters)
        is_japanese = any(ord(c) > 0x3000 for c in mock_lyrics)
        metadata["language"] = "japanese" if is_japanese else "english"
        
        return {
            "success": True,
            "lyrics": mock_lyrics,
            "metadata": metadata
        }
    else:
        # Construct the search query
        query = f"{song} lyrics"
        if artist:
            query = f"{artist} {query}"
        
        try:
            # Initialize the DuckDuckGo search
            ddgs = DDGS()
            
            # Search for lyrics
            results = list(ddgs.text(query, max_results=5))
            
            if not results:
                return {
                    "success": False,
                    "error": "No lyrics found for the given song and artist",
                    "lyrics": None,
                    "metadata": None
                }
            
            # Extract the most relevant result
            best_result = results[0]
            
            # Extract the lyrics from the search result
            lyrics = best_result.get('body', '')
            
            # Create metadata
            metadata = {
                "title": song,
                "artist": artist if artist else "Unknown",
                "source": best_result.get('href', ''),
                "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Detect language (simple check for Japanese characters)
            is_japanese = any(ord(c) > 0x3000 for c in lyrics)
            metadata["language"] = "japanese" if is_japanese else "english"
            
            return {
                "success": True,
                "lyrics": lyrics,
                "metadata": metadata
            }
        except Exception as e:
            error_msg = f"Error fetching lyrics: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "lyrics": None,
                "metadata": None
            }

if __name__ == "__main__":
    # Example usage with mock data
    print("\nFetching lyrics (using mock data):")
    result = get_lyrics("Lemon", "Kenshi Yonezu", use_mock=True)
    print(f"Success: {result['success']}")
    print(f"Lyrics length: {len(result['lyrics'])}")
    print(f"Language: {result['metadata']['language']}")
    print(f"Fetched at: {result['metadata']['fetched_at']}")
    
    # Example of real fetch (commented out to avoid actual web requests during testing)
    # print("\nFetching lyrics from web:")
    # result2 = get_lyrics("Lemon", "Kenshi Yonezu")
    # print(f"Success: {result2['success']}")
    # print(f"Lyrics length: {len(result2['lyrics'])}")
    # print(f"Language: {result2['metadata']['language']}")
    # print(f"Fetched at: {result2['metadata']['fetched_at']}")
