"""
Unit tests for the vocabulary caching system.
"""
import unittest
import os
import time
import json
import shutil
import logging
from unittest.mock import patch, MagicMock

from app.tools.vocab_cache import (
    get_vocab_cache_dir, 
    generate_cache_key, 
    get_vocab_cache_path, 
    save_vocab_to_cache, 
    get_cached_vocab, 
    list_cached_vocab, 
    clean_vocab_cache
)

# Set up logging
logger = logging.getLogger(__name__)


class TestVocabCache(unittest.TestCase):
    """Test cases for the vocabulary caching system."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a test directory path
        self.test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'test_vocab_cache')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Set up test environment variable
        self.original_vocab_cache_dir = os.environ.get('VOCAB_CACHE_DIR')
        os.environ['VOCAB_CACHE_DIR'] = self.test_dir
        
        # Sample vocabulary data for testing
        self.sample_vocab = {
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
                },
                {
                    "kanji": "空",
                    "romaji": "sora",
                    "english": "sky",
                    "parts": [
                        {
                            "kanji": "空",
                            "romaji": ["so", "ra"]
                        }
                    ]
                }
            ]
        }
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        
        # Restore original environment variable
        if self.original_vocab_cache_dir:
            os.environ['VOCAB_CACHE_DIR'] = self.original_vocab_cache_dir
        else:
            if 'VOCAB_CACHE_DIR' in os.environ:
                del os.environ['VOCAB_CACHE_DIR']

    def test_generate_cache_key(self):
        """Test generating a cache key from song and artist."""
        # Test with song and artist
        key1 = generate_cache_key("Test Song", "Test Artist")
        self.assertTrue(isinstance(key1, str))
        self.assertIn("test_song", key1)
        self.assertIn("test_artist", key1)
        
        # Test with song only
        key2 = generate_cache_key("Test Song")
        self.assertTrue(isinstance(key2, str))
        self.assertIn("test_song", key2)
        
        # Test with special characters
        key3 = generate_cache_key("Test Song!", "Test Artist!")
        self.assertTrue(isinstance(key3, str))
        self.assertIn("test_song_", key3)
        self.assertIn("test_artist_", key3)
        
        # Test uniqueness
        key4 = generate_cache_key("Test Song", "Test Artist")
        self.assertEqual(key1, key4)  # Same inputs should give same key
        
        key5 = generate_cache_key("Different Song", "Test Artist")
        self.assertNotEqual(key1, key5)  # Different inputs should give different keys

    def test_get_vocab_cache_path(self):
        """Test getting the cache file path."""
        # Test with song and artist
        path1 = get_vocab_cache_path("Test Song", "Test Artist")
        self.assertTrue(isinstance(path1, str))
        self.assertTrue(path1.endswith(".json"))
        self.assertIn(generate_cache_key("Test Song", "Test Artist"), path1)
        
        # Test with song only
        path2 = get_vocab_cache_path("Test Song")
        self.assertTrue(isinstance(path2, str))
        self.assertTrue(path2.endswith(".json"))
        self.assertIn(generate_cache_key("Test Song"), path2)

    def test_save_and_get_cached_vocab(self):
        """Test saving and retrieving vocabulary from cache."""
        test_song = "Test Cache Song"
        test_artist = "Test Cache Artist"
        
        # Save vocabulary to cache
        save_result = save_vocab_to_cache(test_song, test_artist, self.sample_vocab)
        self.assertTrue(save_result['success'])
        self.assertTrue('cache_path' in save_result)
        self.assertTrue(os.path.exists(save_result['cache_path']))
        
        # Get vocabulary from cache
        get_result = get_cached_vocab(test_song, test_artist)
        self.assertIsNotNone(get_result)
        self.assertTrue(get_result['success'])
        self.assertEqual(len(get_result['vocabulary']), len(self.sample_vocab['vocabulary']))
        self.assertEqual(get_result['vocabulary'][0]['kanji'], self.sample_vocab['vocabulary'][0]['kanji'])
        self.assertTrue('cache_info' in get_result)
        self.assertTrue(get_result['cache_info']['from_cache'])
        
        # Try getting non-existent vocabulary
        get_result_none = get_cached_vocab("Non-existent Song", "Non-existent Artist")
        self.assertIsNone(get_result_none)

    def test_list_cached_vocab(self):
        """Test listing all cached vocabulary."""
        # Clear any existing cache files
        clean_vocab_cache(max_entries=0, max_age_days=0)
        
        # Save multiple vocabulary entries
        save_vocab_to_cache("Song 1", "Artist 1", self.sample_vocab)
        save_vocab_to_cache("Song 2", "Artist 2", self.sample_vocab)
        
        # List cached vocabulary
        list_result = list_cached_vocab()
        self.assertTrue(list_result['success'])
        self.assertEqual(list_result['count'], 2)
        self.assertEqual(len(list_result['cached_vocab']), 2)
        
        # Check that each entry has the expected fields
        for entry in list_result['cached_vocab']:
            self.assertTrue('song' in entry)
            self.assertTrue('artist' in entry)
            self.assertTrue('cached_at' in entry)
            self.assertTrue('last_accessed' in entry)
            self.assertTrue('file_path' in entry)
            self.assertTrue('file_size' in entry)

    def test_clean_vocab_cache(self):
        """Test cleaning up the vocabulary cache."""
        # Clear any existing cache files
        clean_vocab_cache(max_entries=0, max_age_days=0)
        
        # Save multiple vocabulary entries
        save_vocab_to_cache("Song 1", "Artist 1", self.sample_vocab)
        save_vocab_to_cache("Song 2", "Artist 2", self.sample_vocab)
        save_vocab_to_cache("Song 3", "Artist 3", self.sample_vocab)
        
        # Get the current count before cleaning
        list_before = list_cached_vocab()
        initial_count = list_before['count']
        
        # Clean up cache with max_entries=2
        clean_result = clean_vocab_cache(max_entries=2, max_age_days=90)
        self.assertTrue(clean_result['success'])
        self.assertEqual(clean_result['initial_count'], initial_count)
        self.assertEqual(clean_result['final_count'], 2)
        self.assertEqual(clean_result['deleted_excess'], initial_count - 2)
        
        # List cached vocabulary to verify
        list_result = list_cached_vocab()
        self.assertTrue(list_result['success'])
        self.assertEqual(list_result['count'], 2)

    def test_cache_metadata(self):
        """Test that cache metadata is properly stored and retrieved."""
        test_song = "Metadata Test Song"
        test_artist = "Metadata Test Artist"
        
        # Save vocabulary to cache
        save_result = save_vocab_to_cache(test_song, test_artist, self.sample_vocab)
        
        # Get the cache file path
        cache_path = get_vocab_cache_path(test_song, test_artist)
        
        # Read the cache file directly to check metadata
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Verify metadata
        self.assertTrue('_cache_metadata' in cache_data)
        metadata = cache_data['_cache_metadata']
        self.assertEqual(metadata['song'], test_song)
        self.assertEqual(metadata['artist'], test_artist)
        self.assertTrue('cached_at' in metadata)
        self.assertEqual(metadata['cache_version'], "1.0")


if __name__ == '__main__':
    unittest.main()
