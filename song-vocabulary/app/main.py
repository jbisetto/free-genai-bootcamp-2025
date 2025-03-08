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
            "/api/v1/cache": "List all songs and artists in the cache"
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

@app.get("/api/v1/cache", response_class=PlainTextResponse)
async def cache_list():
    """
    List all songs and artists in the lyrics cache as a text-based table.
    
    Returns:
        A plain text table with all cached songs and their metadata for easy viewing in browser and console
    """
    try:
        logger.info("Received request to list cached songs")
        
        # Get the list of cached songs
        result = list_cached_songs()
        
        # Log the result
        logger.info(f"Found {result.get('count', 0)} cached songs")
        
        # Format as a text-based table
        if not result.get("success", False) or result.get("count", 0) == 0:
            return "No songs found in cache."
        
        # Create table header
        table = "┌─────────────────────────────┬─────────────────────────────┬─────────────────────────────┬─────────────────────────────┐\n"
        table += "│ Song                        │ Artist                      │ Cached At                   │ Last Accessed               │\n"
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
        table += f"\nTotal cached songs: {result.get('count', 0)}\n"
        
        return table
    except Exception as e:
        logger.error(f"Error listing cached songs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing cached songs: {str(e)}")

# Run the application
if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 8000))
    
    # Run the application
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
