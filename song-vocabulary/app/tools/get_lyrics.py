"""
Tool for fetching song lyrics using duckduckgo-search.
"""
from typing import Optional, Dict, Any
from duckduckgo_search import DDGS

def get_lyrics(song: str, artist: Optional[str] = None) -> Dict[str, Any]:
    """
    Searches for and retrieves lyrics for a given song and artist.
    
    Args:
        song: The name of the song to search for
        artist: Optional artist name to narrow down the search
    
    Returns:
        A dictionary containing the lyrics and metadata
    """
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
        # In a real-world scenario, we might want to implement more sophisticated
        # logic to identify the most relevant lyrics
        best_result = results[0]
        
        # Extract the lyrics from the search result
        # This is a simplified approach - in practice, we might need to parse HTML
        # or use more sophisticated techniques to extract clean lyrics
        lyrics = best_result.get('body', '')
        
        # Create metadata
        metadata = {
            "title": song,
            "artist": artist if artist else "Unknown",
            "source": best_result.get('href', '')
        }
        
        return {
            "success": True,
            "lyrics": lyrics,
            "metadata": metadata
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching lyrics: {str(e)}",
            "lyrics": None,
            "metadata": None
        }

if __name__ == "__main__":
    # Example usage
    result = get_lyrics("Lemon", "Kenshi Yonezu")
    print(result)
