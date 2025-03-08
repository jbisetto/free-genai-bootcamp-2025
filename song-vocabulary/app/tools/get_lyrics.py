"""
Tool for fetching song lyrics using duckduckgo-search with SQLite caching and compression.

This module implements a robust caching system for song lyrics to address several challenges:

1. External API Limitations:
   - DuckDuckGo search API has rate limits that can cause failures during heavy usage
   - Caching reduces the number of external API calls needed for repeated song requests

2. Performance Optimization:
   - Cached lyrics are retrieved much faster than making new web requests
   - Compression reduces storage requirements while maintaining fast retrieval

3. Offline Functionality:
   - Previously fetched lyrics can be accessed even without internet connectivity
   - Mock mode allows for testing without any external API dependencies

The caching system uses SQLite for persistent storage and zlib for compression:
   - Typical compression ratios range from 1.4x to 2.5x depending on lyrics content
   - Metadata is stored alongside lyrics for language detection and source tracking
   - Cache management functions automatically clean up old or excess entries

Usage:
    lyrics_result = get_lyrics("Song Name", "Artist Name")
    
    # With mock data for testing
    test_result = get_lyrics("Song Name", "Artist Name", use_mock=True)
    
    # Cache management
    stats = manage_lyrics_cache(max_entries=500, max_age_days=60)
"""
import os
import sqlite3
import json
import zlib
import base64
import time
import logging
from typing import Optional, Dict, Any, Tuple
from duckduckgo_search import DDGS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_lyrics_cache_db() -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
    """Set up the lyrics cache database with compression support.
    
    Creates the SQLite database and necessary tables/indexes for storing compressed lyrics.
    The database is stored in the 'data' directory at the project root.
    
    Returns:
        A tuple containing (connection, cursor) for the database
    """
    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    db_path = os.path.join(data_dir, 'lyrics_cache.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table with compressed lyrics storage
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lyrics_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        song TEXT NOT NULL,
        artist TEXT,
        compressed_lyrics TEXT NOT NULL,
        compression_info TEXT NOT NULL,
        metadata TEXT,
        language TEXT,
        source_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_song_artist ON lyrics_cache(song, artist)')
    
    conn.commit()
    return conn, cursor

def compress_lyrics(lyrics: str, compression_level: int = 6) -> Tuple[str, Dict[str, Any]]:
    """Compress lyrics using zlib and encode as base64 for storage.
    
    Args:
        lyrics: The raw lyrics text to compress
        compression_level: zlib compression level (1-9, where 9 is highest compression)
        
    Returns:
        A tuple containing (compressed_text, compression_info)
        where compression_info contains metadata about the compression
    """
    original_bytes = lyrics.encode('utf-8')
    original_size = len(original_bytes)
    
    compressed = zlib.compress(original_bytes, level=compression_level)
    compressed_size = len(compressed)
    
    # Base64 encode for storage as text
    encoded = base64.b64encode(compressed).decode('ascii')
    encoded_size = len(encoded)
    
    compression_ratio = original_size / encoded_size if encoded_size > 0 else 0
    
    stats = {
        "original_size_bytes": original_size,
        "compressed_size_bytes": compressed_size,
        "encoded_size_bytes": encoded_size,
        "compression_ratio": compression_ratio,
        "compression_method": "zlib+base64",
        "compression_level": compression_level
    }
    
    return encoded, stats

def decompress_lyrics(compressed_text: str) -> str:
    """Decompress lyrics from base64-encoded zlib-compressed format."""
    try:
        compressed = base64.b64decode(compressed_text.encode('ascii'))
        return zlib.decompress(compressed).decode('utf-8')
    except Exception as e:
        logger.error(f"Error decompressing lyrics: {str(e)}")
        return f"Error decompressing lyrics: {str(e)}"

def get_cached_lyrics(song: str, artist: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve and decompress lyrics from cache."""
    try:
        # Normalize inputs
        normalized_song = song.lower().strip()
        normalized_artist = artist.lower().strip() if artist else None
        
        # Connect to database
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        db_path = os.path.join(data_dir, 'lyrics_cache.db')
        
        if not os.path.exists(db_path):
            return None
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query
        query = 'SELECT * FROM lyrics_cache WHERE song = ?'
        params = [normalized_song]
        
        if normalized_artist:
            query += ' AND artist = ?'
            params.append(normalized_artist)
        else:
            query += ' AND artist IS NULL'
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # Update access time
        cursor.execute(
            'UPDATE lyrics_cache SET accessed_at = datetime("now") WHERE id = ?',
            (row[0],)  # id is the first column
        )
        conn.commit()
        
        # Decompress lyrics
        decompressed_lyrics = decompress_lyrics(row[3])  # compressed_lyrics is the fourth column
        
        # Parse metadata and compression info
        metadata = json.loads(row[5]) if row[5] else {}  # metadata is the sixth column
        compression_info = json.loads(row[4]) if row[4] else {}  # compression_info is the fifth column
        
        # Prepare result
        result = {
            "success": True,
            "lyrics": decompressed_lyrics,
            "metadata": metadata,
            "cache_info": {
                "from_cache": True,
                "compression": compression_info,
                "language": row[6],  # language is the seventh column
                "cached_at": row[8]  # created_at is the ninth column
            }
        }
        
        conn.close()
        logger.info(f"Cache hit for '{song}' by '{artist}'")
        return result
    except Exception as e:
        logger.error(f"Error retrieving from cache: {str(e)}")
        return None

def cache_lyrics(song: str, artist: Optional[str], lyrics: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Store lyrics in compressed format in the cache."""
    try:
        # Normalize inputs
        normalized_song = song.lower().strip()
        normalized_artist = artist.lower().strip() if artist else None
        
        # Connect to database
        conn, cursor = setup_lyrics_cache_db()
        
        # Compress lyrics
        compressed_lyrics, compression_stats = compress_lyrics(lyrics)
        
        # Detect language (simplified)
        language = "japanese"
        if any(char in lyrics.lower() for char in "abcdefghijklmnopqrstuvwxyz"):
            language = "english"
        
        # Check if entry already exists
        query = 'SELECT id FROM lyrics_cache WHERE song = ?'
        params = [normalized_song]
        
        if normalized_artist:
            query += ' AND artist = ?'
            params.append(normalized_artist)
        else:
            query += ' AND artist IS NULL'
        
        cursor.execute(query, params)
        existing = cursor.fetchone()
        
        if existing:
            # Update existing entry
            cursor.execute(
                '''
                UPDATE lyrics_cache 
                SET compressed_lyrics = ?, compression_info = ?, metadata = ?, 
                    language = ?, source_url = ?, accessed_at = datetime("now")
                WHERE id = ?
                ''',
                (
                    compressed_lyrics,
                    json.dumps(compression_stats),
                    json.dumps(metadata),
                    language,
                    metadata.get("source", ""),
                    existing[0]
                )
            )
            logger.info(f"Updated cache entry for '{song}' by '{artist}'")
        else:
            # Store new entry
            cursor.execute(
                '''
                INSERT INTO lyrics_cache 
                (song, artist, compressed_lyrics, compression_info, metadata, language, source_url) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    normalized_song,
                    normalized_artist,
                    compressed_lyrics,
                    json.dumps(compression_stats),
                    json.dumps(metadata),
                    language,
                    metadata.get("source", "")
                )
            )
            logger.info(f"Added new cache entry for '{song}' by '{artist}'")
        
        conn.commit()
        conn.close()
        
        return compression_stats
    except Exception as e:
        logger.error(f"Error caching lyrics: {str(e)}")
        return {"error": str(e)}

def manage_lyrics_cache(max_entries: int = 1000, max_age_days: int = 90) -> Dict[str, Any]:
    """Manages the lyrics cache by removing old or excess entries.
    
    This function performs two types of cleanup:
    1. Age-based: Removes entries older than max_age_days
    2. Size-based: If more than max_entries remain after age-based cleanup,
       removes the least recently accessed entries until max_entries remain
    
    The function also calculates the total size of the compressed data to help
    monitor storage usage.
    
    Args:
        max_entries: Maximum number of entries to keep in cache (default: 1000)
        max_age_days: Maximum age of entries in days (default: 90)
        
    Returns:
        Statistics about the cleanup operation including:
        - initial_count: Number of entries before cleanup
        - deleted_old: Number of entries deleted due to age
        - deleted_excess: Number of entries deleted due to excess
        - final_count: Number of entries after cleanup
        - total_compressed_size_bytes: Total size of compressed lyrics in bytes
        - approximate_size_kb: Approximate size of the cache in KB
    """
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        db_path = os.path.join(data_dir, 'lyrics_cache.db')
        
        if not os.path.exists(db_path):
            return {"status": "no_cache_exists"}
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get initial count
        cursor.execute('SELECT COUNT(*) FROM lyrics_cache')
        initial_count = cursor.fetchone()[0]
        
        # Delete entries older than max_age_days
        cursor.execute(
            'DELETE FROM lyrics_cache WHERE created_at < datetime("now", ?)',
            (f'-{max_age_days} days',)
        )
        old_deleted = cursor.rowcount
        
        # Get count after age-based deletion
        cursor.execute('SELECT COUNT(*) FROM lyrics_cache')
        after_age_delete_count = cursor.fetchone()[0]
        
        # If still over max_entries, delete oldest accessed entries
        excess_deleted = 0
        if after_age_delete_count > max_entries:
            cursor.execute(
                '''
                DELETE FROM lyrics_cache 
                WHERE id IN (
                    SELECT id FROM lyrics_cache 
                    ORDER BY accessed_at ASC 
                    LIMIT ?
                )
                ''',
                (after_age_delete_count - max_entries,)
            )
            excess_deleted = cursor.rowcount
        
        conn.commit()
        
        # Get final count
        cursor.execute('SELECT COUNT(*) FROM lyrics_cache')
        final_count = cursor.fetchone()[0]
        
        # Get total size
        cursor.execute('SELECT SUM(length(compressed_lyrics)) FROM lyrics_cache')
        total_compressed_size = cursor.fetchone()[0] or 0
        
        stats = {
            "status": "success",
            "initial_count": initial_count,
            "deleted_old": old_deleted,
            "deleted_excess": excess_deleted,
            "final_count": final_count,
            "total_compressed_size_bytes": total_compressed_size,
            "approximate_size_kb": total_compressed_size / 1024
        }
        
        conn.close()
        logger.info(f"Cache cleanup: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error managing cache: {str(e)}")
        return {"status": "error", "error": str(e)}

def get_lyrics(song: str, artist: Optional[str] = None, use_mock: bool = False) -> Dict[str, Any]:
    """
    Searches for and retrieves lyrics for a given song and artist, with caching.
    
    Args:
        song: The name of the song to search for
        artist: Optional artist name to narrow down the search
    
    Returns:
        A dictionary containing the lyrics and metadata
    """
    # First check if we have cached lyrics
    cached_result = get_cached_lyrics(song, artist)
    if cached_result:
        return cached_result
    
    # If not in cache, fetch from web or use mock data
    logger.info(f"Cache miss for '{song}' by '{artist}', {'using mock data' if use_mock else 'fetching from web'}")
    
    # If using mock mode, return mock lyrics
    if use_mock:
        # Generate mock lyrics based on song name
        mock_lyrics = f"""This is a mock lyrics for {song} by {artist or 'Unknown'}
        
Verse 1:
Imagine the first verse of the song here
With multiple lines of text to simulate real lyrics
This helps us test the compression functionality
Without relying on external APIs that might have rate limits

Chorus:
This is the {song} chorus
Repeated a few times
This is the {song} chorus
To make it more realistic

Verse 2:
Second verse continues the song
With more lines to increase the text size
So we can properly test our compression
And see how well the caching system works

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
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "is_mock": True
        }
        
        lyrics = mock_lyrics
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
        except Exception as e:
            error_msg = f"Error fetching lyrics: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "lyrics": None,
                "metadata": None
            }
        
    # Cache the lyrics
    compression_stats = cache_lyrics(song, artist, lyrics, metadata)
    
    return {
        "success": True,
        "lyrics": lyrics,
        "metadata": metadata,
        "cache_info": {
            "from_cache": False,
            "compression": compression_stats
        }
    }

def list_cached_songs() -> Dict[str, Any]:
    """
    Lists all songs and artists currently in the lyrics cache.
    
    Returns:
        A dictionary containing a list of cached songs with their artists and cache timestamps
    """
    try:
        # Connect to database
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        db_path = os.path.join(data_dir, 'lyrics_cache.db')
        
        if not os.path.exists(db_path):
            return {
                "success": True,
                "cached_songs": [],
                "count": 0,
                "message": "Cache database does not exist yet"
            }
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query all songs and artists, ordered by most recently accessed
        cursor.execute(
            'SELECT song, artist, created_at, accessed_at FROM lyrics_cache ORDER BY accessed_at DESC'
        )
        rows = cursor.fetchall()
        
        # Format the results
        cached_songs = []
        for row in rows:
            song, artist, created_at, accessed_at = row
            cached_songs.append({
                "song": song,
                "artist": artist if artist else "Unknown",
                "cached_at": created_at,
                "last_accessed": accessed_at
            })
        
        conn.close()
        
        return {
            "success": True,
            "cached_songs": cached_songs,
            "count": len(cached_songs)
        }
    except Exception as e:
        logger.error(f"Error listing cached songs: {str(e)}")
        return {
            "success": False,
            "error": f"Error listing cached songs: {str(e)}",
            "cached_songs": [],
            "count": 0
        }

if __name__ == "__main__":
    # Example usage with mock data to test caching
    print("\nFetching lyrics (first time, using mock data):")
    result = get_lyrics("Lemon", "Kenshi Yonezu", use_mock=True)
    print(f"Success: {result['success']}")
    print(f"Lyrics length: {len(result['lyrics']) if result['lyrics'] else 0} characters")
    print(f"From cache: {result.get('cache_info', {}).get('from_cache', False)}")
    if 'compression' in result.get('cache_info', {}):
        print(f"Compression ratio: {result['cache_info']['compression'].get('compression_ratio', 0):.2f}x")
    
    print("\nFetching same lyrics again (should be from cache):")
    result = get_lyrics("Lemon", "Kenshi Yonezu", use_mock=True)
    print(f"Success: {result['success']}")
    print(f"Lyrics length: {len(result['lyrics']) if result['lyrics'] else 0} characters")
    print(f"From cache: {result.get('cache_info', {}).get('from_cache', True)}")
    
    # Try another song to test multiple entries
    print("\nFetching different song lyrics (using mock data):")
    result = get_lyrics("Flamingo", "Kenshi Yonezu", use_mock=True)
    print(f"Success: {result['success']}")
    print(f"Lyrics length: {len(result['lyrics']) if result['lyrics'] else 0} characters")
    print(f"From cache: {result.get('cache_info', {}).get('from_cache', False)}")
    
    print("\nCache management statistics:")
    stats = manage_lyrics_cache(max_entries=100, max_age_days=30)
    print(stats)
