"""
Tool for caching vocabulary results in JSON files.

This module provides functions for saving and retrieving vocabulary JSON files,
allowing the application to bypass the agent workflow for previously processed songs.

The vocabulary cache uses a file-based approach where each song's vocabulary is stored
as a separate JSON file in a structured directory.
"""
import os
import json
import time
import logging
import hashlib
from typing import Optional, Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the base directory for vocabulary cache
def get_vocab_cache_dir() -> str:
    """Get the directory for storing vocabulary cache files."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    vocab_cache_dir = os.path.join(base_dir, 'data', 'vocab_cache')
    os.makedirs(vocab_cache_dir, exist_ok=True)
    return vocab_cache_dir

def generate_cache_key(song: str, artist: Optional[str] = None) -> str:
    """
    Generate a unique cache key for a song and artist combination.
    
    Args:
        song: The name of the song
        artist: Optional artist name
        
    Returns:
        A unique string key suitable for use as a filename
    """
    # Create a string that combines song and artist
    if artist:
        key_string = f"{song.lower()}_{artist.lower()}"
    else:
        key_string = song.lower()
    
    # Create a hash of the string to ensure filename compatibility
    hash_obj = hashlib.md5(key_string.encode('utf-8'))
    hash_str = hash_obj.hexdigest()
    
    # Return a combination of readable name and hash
    safe_song = "".join(c if c.isalnum() else "_" for c in song.lower())
    if artist:
        safe_artist = "".join(c if c.isalnum() else "_" for c in artist.lower())
        return f"{safe_song}_{safe_artist}_{hash_str[:8]}"
    else:
        return f"{safe_song}_{hash_str[:8]}"

def get_vocab_cache_path(song: str, artist: Optional[str] = None) -> str:
    """
    Get the file path for a cached vocabulary result.
    
    Args:
        song: The name of the song
        artist: Optional artist name
        
    Returns:
        The full path to the vocabulary cache file
    """
    cache_key = generate_cache_key(song, artist)
    return os.path.join(get_vocab_cache_dir(), f"{cache_key}.json")

def save_vocab_to_cache(song: str, artist: Optional[str], vocabulary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save vocabulary results to a cache file.
    
    Args:
        song: The name of the song
        artist: Optional artist name
        vocabulary: The vocabulary data to cache
        
    Returns:
        Metadata about the cache operation
    """
    cache_path = get_vocab_cache_path(song, artist)
    
    # Add cache metadata
    cache_data = vocabulary.copy()
    cache_data["_cache_metadata"] = {
        "song": song,
        "artist": artist if artist else "Unknown",
        "cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cache_version": "1.0"
    }
    
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved vocabulary to cache: {cache_path}")
        return {
            "success": True,
            "cache_path": cache_path,
            "cached_at": cache_data["_cache_metadata"]["cached_at"]
        }
    except Exception as e:
        logger.error(f"Error saving vocabulary to cache: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def get_cached_vocab(song: str, artist: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve vocabulary results from cache if available.
    
    Args:
        song: The name of the song
        artist: Optional artist name
        
    Returns:
        The cached vocabulary data or None if not found
    """
    cache_path = get_vocab_cache_path(song, artist)
    
    if not os.path.exists(cache_path):
        return None
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Update the access time of the file to track usage
        os.utime(cache_path, None)
        
        # Extract cache metadata
        metadata = cache_data.get("_cache_metadata", {})
        
        # Remove metadata from the returned result
        result = cache_data.copy()
        if "_cache_metadata" in result:
            del result["_cache_metadata"]
        
        logger.info(f"Retrieved vocabulary from cache: {cache_path}")
        return {
            "success": True,
            "vocabulary": result.get("vocabulary", []),
            "cache_info": {
                "from_cache": True,
                "cached_at": metadata.get("cached_at"),
                "file_path": cache_path
            }
        }
    except Exception as e:
        logger.error(f"Error reading vocabulary from cache: {str(e)}")
        return None

def list_cached_vocab() -> Dict[str, Any]:
    """
    List all vocabulary files in the cache.
    
    Returns:
        A dictionary containing information about cached vocabulary files
    """
    vocab_cache_dir = get_vocab_cache_dir()
    
    if not os.path.exists(vocab_cache_dir):
        return {
            "success": True,
            "cached_vocab": [],
            "count": 0,
            "message": "Vocabulary cache directory does not exist yet"
        }
    
    try:
        cached_vocab = []
        for filename in os.listdir(vocab_cache_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(vocab_cache_dir, filename)
                
                # Get file stats
                stats = os.stat(file_path)
                created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stats.st_ctime))
                accessed_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stats.st_atime))
                
                # Try to read metadata from the file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        metadata = data.get("_cache_metadata", {})
                        song = metadata.get("song", "Unknown")
                        artist = metadata.get("artist", "Unknown")
                except Exception:
                    # If we can't read the file, use the filename as a fallback
                    parts = filename.split('_')
                    song = parts[0] if len(parts) > 0 else "Unknown"
                    artist = parts[1] if len(parts) > 1 else "Unknown"
                
                cached_vocab.append({
                    "song": song,
                    "artist": artist,
                    "cached_at": created_at,
                    "last_accessed": accessed_at,
                    "file_path": file_path,
                    "file_size": stats.st_size
                })
        
        # Sort by last accessed time (most recent first)
        cached_vocab.sort(key=lambda x: x["last_accessed"], reverse=True)
        
        return {
            "success": True,
            "cached_vocab": cached_vocab,
            "count": len(cached_vocab)
        }
    except Exception as e:
        logger.error(f"Error listing cached vocabulary: {str(e)}")
        return {
            "success": False,
            "error": f"Error listing cached vocabulary: {str(e)}",
            "cached_vocab": [],
            "count": 0
        }

def clean_vocab_cache(max_entries: int = 1000, max_age_days: int = 90) -> Dict[str, Any]:
    """
    Clean up the vocabulary cache by removing old or excess entries.
    
    Args:
        max_entries: Maximum number of entries to keep
        max_age_days: Maximum age of entries in days
        
    Returns:
        Statistics about the cleanup operation
    """
    vocab_cache_dir = get_vocab_cache_dir()
    
    if not os.path.exists(vocab_cache_dir):
        return {
            "success": True,
            "message": "Vocabulary cache directory does not exist yet",
            "deleted": 0
        }
    
    try:
        # Get initial count using list_cached_vocab
        initial_list = list_cached_vocab()
        initial_count = initial_list['count']
        
        # Get all cache files with their stats
        cache_files = []
        for filename in os.listdir(vocab_cache_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(vocab_cache_dir, filename)
                stats = os.stat(file_path)
                cache_files.append({
                    "path": file_path,
                    "accessed_at": stats.st_atime,
                    "created_at": stats.st_ctime,
                    "size": stats.st_size
                })
        
        # Sort by last accessed time (oldest first)
        cache_files.sort(key=lambda x: x["accessed_at"])
        
        # Calculate cutoff time for age-based deletion
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        
        # Delete old files
        deleted_old = 0
        for file_info in cache_files[:]:
            if file_info["created_at"] < cutoff_time:
                os.remove(file_info["path"])
                cache_files.remove(file_info)
                deleted_old += 1
        
        # Delete excess files if needed
        deleted_excess = 0
        if len(cache_files) > max_entries:
            # We've already sorted by access time, so we'll delete the oldest accessed
            for file_info in cache_files[:len(cache_files) - max_entries]:
                os.remove(file_info["path"])
                deleted_excess += 1
        
        return {
            "success": True,
            "initial_count": initial_count,
            "deleted_old": deleted_old,
            "deleted_excess": deleted_excess,
            "final_count": len(cache_files) - deleted_excess
        }
    except Exception as e:
        logger.error(f"Error cleaning vocabulary cache: {str(e)}")
        return {
            "success": False,
            "error": f"Error cleaning vocabulary cache: {str(e)}",
            "deleted": 0
        }

if __name__ == "__main__":
    # Example usage
    print("Vocabulary Cache Directory:", get_vocab_cache_dir())
    
    # Example of saving vocabulary
    example_vocab = {
        "vocabulary": [
            {
                "kanji": "夢",
                "romaji": "yume",
                "english": "dream",
                "parts": [
                    {
                        "kanji": "夢",
                        "romaji": ["yu", "me"]
                    }
                ]
            }
        ]
    }
    
    save_result = save_vocab_to_cache("Test Song", "Test Artist", example_vocab)
    print("Save Result:", save_result)
    
    # Example of retrieving vocabulary
    get_result = get_cached_vocab("Test Song", "Test Artist")
    print("Get Result:", get_result)
    
    # Example of listing vocabulary
    list_result = list_cached_vocab()
    print(f"Found {list_result['count']} cached vocabulary files")
