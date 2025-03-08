# Mock Mode and Caching System Guide

This guide provides detailed information about the mock mode and caching system in the Song Vocabulary App.

## Mock Mode

Mock mode allows you to retrieve lyrics without making actual API calls. This is useful for testing, development, and offline usage.

### Basic Usage

```python
from app.tools.get_lyrics import get_lyrics

# Using mock mode
result = get_lyrics("Lemon", "Kenshi Yonezu", use_mock=True)

# The result will contain mock lyrics
print(result["lyrics"])  # "Sample lyrics for Lemon by Kenshi Yonezu"
print(result["is_mock"])  # True
print(result["source"])  # "mock"
```

### Use Cases for Mock Mode

#### 1. Testing Without External Dependencies

```python
import unittest
from unittest.mock import patch
from app.tools.get_lyrics import get_lyrics

class TestLyricsRetrieval(unittest.TestCase):
    def test_get_lyrics_with_mock(self):
        # No internet connection needed
        result = get_lyrics("Test Song", "Test Artist", use_mock=True)
        
        self.assertTrue(result["success"])
        self.assertTrue(result["is_mock"])
        self.assertEqual(result["source"], "mock")
        self.assertIn("Sample lyrics", result["lyrics"])
```

#### 2. Development Without Internet

```python
def develop_offline():
    # Get mock lyrics
    lyrics_result = get_lyrics("Lemon", "Kenshi Yonezu", use_mock=True)
    
    # Process the lyrics as if they were real
    vocabulary = extract_vocabulary(lyrics_result["lyrics"])
    
    # Continue development without needing internet
    return vocabulary
```

#### 3. Demo and Presentation

```python
def demo_app():
    # For presentations, use mock mode to ensure consistent results
    songs = [
        ("Lemon", "Kenshi Yonezu"),
        ("Flamingo", "Kenshi Yonezu"),
        ("LOSER", "Kenshi Yonezu")
    ]
    
    results = []
    for song, artist in songs:
        # Always get consistent results, even without internet
        lyrics = get_lyrics(song, artist, use_mock=True)
        vocab = extract_vocabulary(lyrics["lyrics"])
        results.append(vocab)
    
    return results
```

## Caching System

The caching system uses SQLite and zlib compression to store lyrics locally, reducing API calls and enabling offline functionality.

### How It Works

1. When `get_lyrics()` is called, it first checks the cache
2. If lyrics are found in the cache, they are decompressed and returned
3. If not found, lyrics are fetched from the web (or mock mode)
4. New lyrics are compressed and stored in the cache for future use

### Cache Functions

#### Retrieving from Cache

```python
from app.tools.get_lyrics import get_cached_lyrics

# Check if lyrics are in the cache
cached_result = get_cached_lyrics("Lemon", "Kenshi Yonezu")

if cached_result:
    print("Cache hit!")
    print(f"Lyrics: {cached_result['lyrics']}")
    print(f"Age: {cached_result['cache_info']['age_seconds']} seconds")
else:
    print("Cache miss!")
```

#### Storing in Cache

```python
from app.tools.get_lyrics import cache_lyrics

# Store lyrics in the cache
lyrics = "These are the lyrics to my song..."
metadata = {"source": "web", "url": "https://example.com/lyrics"}

cache_stats = cache_lyrics("My Song", "My Artist", lyrics, metadata)

print(f"Original size: {cache_stats['original_size']} bytes")
print(f"Compressed size: {cache_stats['compressed_size']} bytes")
print(f"Compression ratio: {cache_stats['compression_ratio']:.2f}x")
```

#### Managing the Cache

```python
from app.tools.get_lyrics import manage_lyrics_cache

# Clean up old or excess entries
stats = manage_lyrics_cache(max_entries=500, max_age_days=30)

print(f"Entries before cleanup: {stats['entries_before']}")
print(f"Entries removed: {stats['entries_removed']}")
print(f"Entries after cleanup: {stats['entries_after']}")
```

### Advanced Usage

#### Combining Mock Mode and Caching

```python
def get_lyrics_with_fallback(song, artist):
    """Get lyrics with fallback to cache and then mock mode."""
    # Try to get from cache first
    cached_result = get_cached_lyrics(song, artist)
    if cached_result:
        return cached_result
    
    try:
        # Try to get from web
        return get_lyrics(song, artist, use_mock=False)
    except Exception:
        # If web fails, use mock mode
        return get_lyrics(song, artist, use_mock=True)
```

#### Custom Cache Path

```python
import os
from app.tools.get_lyrics import get_lyrics

# Set a custom cache path for testing
os.environ["LYRICS_CACHE_PATH"] = "/tmp/test_lyrics_cache.db"

# Now the cache will use the custom path
result = get_lyrics("Test Song", "Test Artist")
```

## Best Practices

1. **Testing**: Always use mock mode in tests to avoid external dependencies
2. **Development**: Use the cache during development to reduce API calls
3. **Production**: Implement cache management to prevent unlimited growth
4. **Offline Mode**: Combine cache and mock mode for robust offline functionality

## Troubleshooting

### Cache Issues

If you encounter issues with the cache:

1. **Database Locked**: Ensure all connections are properly closed
2. **Corrupted Cache**: Delete the cache file and let it be recreated
3. **Performance Issues**: Run cache management to clean up old entries

### Mock Mode Issues

1. **Inconsistent Results**: Mock mode always returns the same format, check your parsing
2. **Missing Metadata**: Mock mode includes basic metadata; add custom metadata if needed

## Conclusion

The combination of mock mode and caching provides a robust system for lyrics retrieval that works in various scenarios, from development to testing to production. Use these features to make your application more reliable and efficient.
