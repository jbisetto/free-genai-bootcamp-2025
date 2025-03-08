"""
FastAPI application for the vocabulary generator.
"""
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import os
import traceback
import logging
from dotenv import load_dotenv

from app.agent.agent import run_agent
from app.tools.get_lyrics import list_cached_songs
from app.tools.vocab_cache import list_cached_vocab, clean_vocab_cache

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Japanese Song Vocabulary Generator",
    description="API for generating Japanese vocabulary from song lyrics",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Add exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"error": f"An unexpected error occurred: {str(exc)}"},
    )

# Define request model
class SongRequest(BaseModel):
    song: str
    artist: Optional[str] = None

# Define routes
@app.get("/")
async def root():
    """Root endpoint that returns API information."""
    return {
        "message": "Welcome to the Japanese Song Vocabulary Generator API",
        "endpoints": {
            "/api/v1/vocab-generator": "Generate vocabulary from song lyrics",
            "/api/v1/cache/lyrics": "List all songs and artists in the lyrics cache",
            "/api/v1/cache/vocab": "List all songs and artists in the vocabulary cache",
            "/api/v1/cache/cleanup": "Clean up old or excess cache entries"
        }
    }

@app.get("/api/v1/vocab-generator")
async def vocab_generator(
    song: str = Query(..., description="The name of the song"),
    artist: Optional[str] = Query(None, description="The name of the artist (optional)")
):
    """
    Generate vocabulary from song lyrics.
    
    Args:
        song: The name of the song
        artist: Optional artist name
    
    Returns:
        A JSON object with either the vocabulary list or an error message
    """
    try:
        logger.info(f"Received request for song: {song}, artist: {artist}")
        
        # Run the agent to generate vocabulary
        result = run_agent(song, artist)
        logger.info(f"Agent result type: {type(result)}")
        
        # Log the result for debugging
        if isinstance(result, dict):
            logger.info(f"Result keys: {result.keys()}")
            
            # Log cache information if available
            if "cache_info" in result and isinstance(result["cache_info"], dict):
                if result["cache_info"].get("from_cache", False):
                    logger.info(f"✅ Using CACHED lyrics for '{song}' by '{artist or 'Unknown'}'")
                    if "cached_at" in result["cache_info"]:
                        logger.info(f"  - Cached at: {result['cache_info']['cached_at']}")
                    if "compression" in result["cache_info"] and isinstance(result["cache_info"]["compression"], dict):
                        ratio = result["cache_info"]["compression"].get("ratio", "unknown")
                        logger.info(f"  - Compression ratio: {ratio}x")
                else:
                    logger.info(f"🔍 Using FRESH lyrics for '{song}' by '{artist or 'Unknown'}'")
        else:
            logger.info(f"Result is not a dict: {result}")
        
        # Check if there's an error
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Error from agent: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Ensure result is a dictionary
        if not isinstance(result, dict):
            logger.error(f"Result is not a dictionary: {result}")
            return {"error": "Invalid response format", "details": str(result)}
        
        logger.info("Successfully generated vocabulary")
        return result
    
    except Exception as e:
        # Log the full exception traceback
        logger.error(f"Exception in vocab_generator: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a proper error response
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import HTMLResponse, PlainTextResponse

@app.get("/api/v1/cache/lyrics", response_class=PlainTextResponse)
async def lyrics_cache_list():
    """
    List all songs and artists in the lyrics cache as a text-based table.
    
    Returns:
        A plain text table with all cached songs and their metadata for easy viewing in browser and console
    """
    try:
        logger.info("Received request to list cached lyrics")
        
        # Get the list of cached songs
        result = list_cached_songs()
        
        # Log the result
        logger.info(f"Found {result.get('count', 0)} cached lyrics entries")
        
        # Format as a text-based table
        if not result.get("success", False) or result.get("count", 0) == 0:
            return "No songs found in cache."
        
        # Create table header
        table = "┌─────────────────────────────┬─────────────────────────────┬─────────────────────────────┬─────────────────────────────┐\n"
        table += "│ Song                        │ Artist                      │ Cached At                   │ Last Accessed               │\n"
        table += "├─────────────────────────────┼─────────────────────────────┼─────────────────────────────┼─────────────────────────────┤\n"
        table += "│ LYRICS CACHE                │                             │                             │                             │\n"
        table += "├─────────────────────────────┼─────────────────────────────┼─────────────────────────────┼─────────────────────────────┤\n"
        
        # Add table rows
        for song in result.get("cached_songs", []):
            song_name = (song.get("song", "") or "")[:25]
            artist_name = (song.get("artist", "") or "")[:25]
            cached_at = (song.get("cached_at", "") or "")[:25]
            last_accessed = (song.get("last_accessed", "") or "")[:25]
            
            table += f"│ {song_name.ljust(25)} │ {artist_name.ljust(25)} │ {cached_at.ljust(25)} │ {last_accessed.ljust(25)} │\n"
        
        # Add table footer
        table += "└─────────────────────────────┴─────────────────────────────┴─────────────────────────────┴─────────────────────────────┘\n"
        table += f"\nTotal cached lyrics entries: {result.get('count', 0)}\n"
        
        return table
    except Exception as e:
        logger.error(f"Error listing cached lyrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing cached lyrics: {str(e)}")

@app.get("/api/v1/cache/vocab", response_class=PlainTextResponse)
async def vocab_cache_list():
    """
    List all songs and artists in the vocabulary cache as a text-based table.
    
    Returns:
        A plain text table with all cached vocabulary files and their metadata for easy viewing in browser and console
    """
    try:
        logger.info("Received request to list cached vocabulary")
        
        # Get the list of cached vocabulary
        result = list_cached_vocab()
        
        # Log the result
        logger.info(f"Found {result.get('count', 0)} cached vocabulary entries")
        
        # Format as a text-based table
        if not result.get("success", False) or result.get("count", 0) == 0:
            return "No vocabulary found in cache."
        
        # Create table header
        table = "┌─────────────────────────────┬─────────────────────────────┬─────────────────────────────┬─────────────────────────────┐\n"
        table += "│ Song                        │ Artist                      │ Cached At                   │ Last Accessed               │\n"
        table += "├─────────────────────────────┼─────────────────────────────┼─────────────────────────────┼─────────────────────────────┤\n"
        table += "│ VOCABULARY CACHE            │                             │                             │                             │\n"
        table += "├─────────────────────────────┼─────────────────────────────┼─────────────────────────────┼─────────────────────────────┤\n"
        
        # Add table rows
        for vocab in result.get("cached_vocab", []):
            song_name = (vocab.get("song", "") or "")[:25]
            artist_name = (vocab.get("artist", "") or "")[:25]
            cached_at = (vocab.get("cached_at", "") or "")[:25]
            last_accessed = (vocab.get("last_accessed", "") or "")[:25]
            
            table += f"│ {song_name.ljust(25)} │ {artist_name.ljust(25)} │ {cached_at.ljust(25)} │ {last_accessed.ljust(25)} │\n"
        
        # Add table footer
        table += "└─────────────────────────────┴─────────────────────────────┴─────────────────────────────┴─────────────────────────────┘\n"
        table += f"\nTotal cached vocabulary entries: {result.get('count', 0)}\n"
        
        return table
    except Exception as e:
        logger.error(f"Error listing cached vocabulary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing cached vocabulary: {str(e)}")

@app.get("/api/v1/cache/cleanup")
async def cache_cleanup(
    max_entries: int = Query(1000, description="Maximum number of entries to keep in each cache"),
    max_age_days: int = Query(90, description="Maximum age of entries in days")
):
    """
    Clean up old or excess cache entries.
    
    Args:
        max_entries: Maximum number of entries to keep in each cache
        max_age_days: Maximum age of entries in days
    
    Returns:
        Statistics about the cleanup operation
    """
    try:
        logger.info(f"Received request to clean up cache (max_entries={max_entries}, max_age_days={max_age_days})")
        
        # Clean up vocabulary cache
        vocab_result = clean_vocab_cache(max_entries=max_entries, max_age_days=max_age_days)
        
        # Log the result
        if vocab_result.get("success", False):
            logger.info(f"Vocabulary cache cleanup: {vocab_result.get('initial_count', 0)} -> {vocab_result.get('final_count', 0)} entries")
            logger.info(f"Deleted {vocab_result.get('deleted_old', 0)} old entries and {vocab_result.get('deleted_excess', 0)} excess entries")
        else:
            logger.error(f"Error cleaning vocabulary cache: {vocab_result.get('error', 'Unknown error')}")
        
        return {
            "success": True,
            "vocabulary_cache": vocab_result
        }
    except Exception as e:
        logger.error(f"Error cleaning cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cleaning cache: {str(e)}")

# Run the application
if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 8000))
    
    # Run the application
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
