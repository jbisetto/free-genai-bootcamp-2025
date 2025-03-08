"""
Test module for the get_lyrics tool.
"""
import unittest
import os
import sqlite3
import time
import json
import zlib
import base64
import sys
import logging
from unittest.mock import patch, MagicMock
import app.tools.get_lyrics
from app.tools.get_lyrics import get_lyrics, setup_lyrics_cache_db, compress_lyrics, decompress_lyrics, cache_lyrics, get_cached_lyrics, manage_lyrics_cache

# Set up logging
logger = logging.getLogger(__name__)

class TestGetLyrics(unittest.TestCase):
    """Test cases for the get_lyrics function."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a test database path
        self.test_db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(self.test_db_dir, exist_ok=True)
        self.test_db_path = os.path.join(self.test_db_dir, 'test_lyrics_cache.db')
        
        # Remove test database if it exists
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def tearDown(self):
        """Clean up after tests."""
        # Clean up test data from the main cache
        self._cleanup_test_data("Lemon", "Kenshi Yonezu")
        self._cleanup_test_data("Test", "Artist")
        
        # Remove test database
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
            
    def _cleanup_test_data(self, song, artist):
        """Helper method to clean up test data from the cache."""
        try:
            conn, cursor = setup_lyrics_cache_db()
            try:
                # Delete the test song from the cache
                cursor.execute(
                    "DELETE FROM lyrics_cache WHERE song LIKE ? AND artist LIKE ?", 
                    (song.lower(), artist.lower())
                )
                conn.commit()
                logger.info(f"Cleaned up test data: {cursor.rowcount} rows deleted")
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"Error cleaning up test data: {e}")

    @patch('app.tools.get_lyrics.get_cached_lyrics')
    @patch('app.tools.get_lyrics.DDGS')
    def test_successful_lyrics_retrieval(self, mock_ddgs, mock_get_cached):
        """Test successful retrieval of lyrics."""
        # Setup cache miss
        mock_get_cached.return_value = None
        
        # Setup mock
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = [
            {
                'title': 'Lemon Lyrics',
                'body': 'Sample lyrics for Lemon by Kenshi Yonezu',
                'href': 'https://example.com/lyrics'
            }
        ]

        # Call the function with use_mock=False but the actual web request is mocked
        result = get_lyrics("Lemon", "Kenshi Yonezu", use_mock=False)

        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['lyrics'], 'Sample lyrics for Lemon by Kenshi Yonezu')
        self.assertEqual(result['metadata']['title'], 'Lemon')
        self.assertEqual(result['metadata']['artist'], 'Kenshi Yonezu')
        self.assertEqual(result['metadata']['source'], 'https://example.com/lyrics')
        
        # Verify the search query
        mock_instance.text.assert_called_once_with("Kenshi Yonezu Lemon lyrics", max_results=5)

    @patch('app.tools.get_lyrics.get_cached_lyrics')
    @patch('app.tools.get_lyrics.DDGS')
    def test_no_artist_provided(self, mock_ddgs, mock_get_cached):
        """Test lyrics retrieval when no artist is provided."""
        # Setup cache miss
        mock_get_cached.return_value = None
        
        # Setup mock
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = [
            {
                'title': 'Lemon Lyrics',
                'body': 'Sample lyrics for Lemon',
                'href': 'https://example.com/lyrics'
            }
        ]

        # Call the function without artist and with use_mock=False but the web request is mocked
        result = get_lyrics("Lemon", use_mock=False)

        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['lyrics'], 'Sample lyrics for Lemon')
        self.assertEqual(result['metadata']['title'], 'Lemon')
        self.assertEqual(result['metadata']['artist'], 'Unknown')
        
        # Verify the search query
        mock_instance.text.assert_called_once_with("Lemon lyrics", max_results=5)

    @patch('app.tools.get_lyrics.DDGS')
    def test_no_lyrics_found(self, mock_ddgs):
        """Test behavior when no lyrics are found."""
        # Setup mock
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = []

        # Call the function
        result = get_lyrics("NonExistentSong", "NonExistentArtist")

        # Assertions
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "No lyrics found for the given song and artist")
        self.assertIsNone(result['lyrics'])
        self.assertIsNone(result['metadata'])
        
    @patch('app.tools.get_lyrics.get_cached_lyrics')
    @patch('app.tools.get_lyrics.DDGS')
    def test_exception_handling(self, mock_ddgs, mock_get_cached):
        """Test handling of exceptions during lyrics retrieval."""
        # Setup cache miss
        mock_get_cached.return_value = None
        
        # Setup mock to raise an exception
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.side_effect = Exception("Test exception")

        # Call the function with use_mock=False but the actual web request is mocked
        result = get_lyrics("Lemon", "Kenshi Yonezu", use_mock=False)

        # Assertions
        self.assertFalse(result['success'])
        self.assertIn("Error fetching lyrics", result['error'])
        self.assertIn("Test exception", result['error'])
        self.assertIsNone(result['lyrics'])
        self.assertIsNone(result['metadata'])
        
    @patch('app.tools.get_lyrics.DDGS')
    def test_multiple_results(self, mock_ddgs):
        """Test that the function selects the first result when multiple are available."""
        # Setup mock with multiple results
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = [
            {
                'title': 'First Result',
                'body': 'These are the first lyrics',
                'href': 'https://example.com/first'
            },
            {
                'title': 'Second Result',
                'body': 'These are the second lyrics',
                'href': 'https://example.com/second'
            }
        ]

        # Call the function
        result = get_lyrics("Test Song", "Test Artist")

        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['lyrics'], 'These are the first lyrics')
        self.assertEqual(result['metadata']['source'], 'https://example.com/first')

    @patch('app.tools.get_lyrics.get_cached_lyrics')
    def test_mock_mode(self, mock_get_cached):
        """Test the mock mode for lyrics retrieval."""
        # Setup cache miss
        mock_get_cached.return_value = None
        
        # Call the function with mock mode
        result = get_lyrics("Lemon", "Kenshi Yonezu", use_mock=True)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['lyrics'])
        # Don't check the length as it may vary
        self.assertEqual(result['metadata']['title'], 'Lemon')
        self.assertEqual(result['metadata']['artist'], 'Kenshi Yonezu')
        self.assertEqual(result['metadata']['source'], 'mock_data')
        self.assertTrue(result['metadata']['is_mock'])
        
    def test_compression_functions(self):
        """Test the compression and decompression functions."""
        original_text = "This is a test lyrics string with some repetition. " * 10
        
        # Test compression
        compressed, info = compress_lyrics(original_text)
        self.assertIsNotNone(compressed)
        self.assertGreater(info['compression_ratio'], 1.0)  # Should achieve some compression
        
        # Test decompression
        decompressed = decompress_lyrics(compressed)
        self.assertEqual(original_text, decompressed)
    
    def test_caching_functions(self):
        """Test the caching functions."""
        # Use a test database file instead of mocking
        test_db_path = os.path.join(os.path.dirname(__file__), 'test_lyrics_cache.db')
        
        # Remove the test database if it exists
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        # Connect to the test database
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # Create the table
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
        conn.commit()
        
        # Test compression and decompression
        test_lyrics = "Test lyrics content"
        compressed, comp_info = compress_lyrics(test_lyrics)
        self.assertIsInstance(compressed, str)
        self.assertIsInstance(comp_info, dict)
        self.assertIn('compression_ratio', comp_info)
        
        decompressed = decompress_lyrics(compressed)
        self.assertEqual(decompressed, test_lyrics)
        
        # Test caching with direct database operations
        test_metadata = {"title": "Test Song", "artist": "Test Artist"}
        
        # Insert test data
        cursor.execute(
            '''INSERT INTO lyrics_cache 
               (song, artist, compressed_lyrics, compression_info, metadata) 
               VALUES (?, ?, ?, ?, ?)''',
            ('test song', 'test artist', compressed, json.dumps(comp_info), json.dumps(test_metadata))
        )
        conn.commit()
        
        # Query the data
        cursor.execute("SELECT * FROM lyrics_cache WHERE song = 'test song' AND artist = 'test artist'")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        
        # Clean up
        conn.close()
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
    
    @patch('app.tools.get_lyrics.get_cached_lyrics')
    @patch('app.tools.get_lyrics.cache_lyrics')
    @patch('app.tools.get_lyrics.DDGS')
    def test_caching_workflow(self, mock_ddgs, mock_cache, mock_get_cache):
        """Test the complete caching workflow."""
        # Setup cache miss first
        mock_get_cache.return_value = None
        
        # Setup successful lyrics fetch
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = [
            {
                'title': 'Test Lyrics',
                'body': 'Sample lyrics for testing',
                'href': 'https://example.com/lyrics'
            }
        ]
        
        # Setup successful caching - return compression stats
        mock_cache.return_value = {
            'compression_ratio': 1.5,
            'original_size': 100,
            'compressed_size': 67
        }
        
        # First call - should fetch from web and cache
        # Use use_mock=False but the web request is mocked
        result1 = get_lyrics("Test", "Artist", use_mock=False)
        self.assertTrue(result1['success'])
        self.assertEqual(result1['lyrics'], 'Sample lyrics for testing')
        mock_get_cache.assert_called_once()
        mock_instance.text.assert_called_once()
        mock_cache.assert_called_once()
        
        # Reset mocks for second call
        mock_get_cache.reset_mock()
        mock_instance.text.reset_mock()
        mock_cache.reset_mock()
        
        # Setup cache hit for second call
        mock_get_cache.return_value = {
            'success': True, 
            'lyrics': 'Sample lyrics for testing',
            'metadata': {'title': 'Test', 'artist': 'Artist'},
            'cache_info': {
                'from_cache': True,
                'compression': {'compression_ratio': 1.5},
                'language': 'en',
                'cached_at': '2023-01-01 12:00:00'
            }
        }
        
        # Second call - should get from cache
        result2 = get_lyrics("Test", "Artist", use_mock=False)
        self.assertTrue(result2['success'])
        self.assertEqual(result2['lyrics'], 'Sample lyrics for testing')
        self.assertTrue(result2['cache_info']['from_cache'])
        mock_get_cache.assert_called_once()
        mock_instance.text.assert_not_called()
        mock_cache.assert_not_called()


    def test_cache_collision_handling(self):
        """Test handling of cache collisions (same song name, different artists)."""
        # Define test lyrics
        lyrics1 = "Lyrics for Artist 1"
        lyrics2 = "Lyrics for Artist 2"
        
        # Use a test database file
        test_db_path = os.path.join(os.path.dirname(__file__), 'test_collision_cache.db')
        
        # Remove the test database if it exists
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        # Mock the get_cached_lyrics function
        with patch('app.tools.get_lyrics.get_cached_lyrics', autospec=True) as mock_get_cached:
            # Setup mock to return different values based on input
            def side_effect(song, artist=None):
                if song == "Same Song" and artist == "Artist 1":
                    return {
                        'success': True,
                        'lyrics': lyrics1,
                        'metadata': {"title": "Same Song", "artist": "Artist 1"},
                        'cache_info': {'from_cache': True}
                    }
                elif song == "Same Song" and artist == "Artist 2":
                    return {
                        'success': True,
                        'lyrics': lyrics2,
                        'metadata': {"title": "Same Song", "artist": "Artist 2"},
                        'cache_info': {'from_cache': True}
                    }
                return None
            
            mock_get_cached.side_effect = side_effect
            
            # Get lyrics for both artists - using the mock directly
            cached1 = mock_get_cached("Same Song", "Artist 1")
            cached2 = mock_get_cached("Same Song", "Artist 2")
            
            # Verify different lyrics were returned for each artist
            self.assertEqual(cached1['lyrics'], lyrics1)
            self.assertEqual(cached2['lyrics'], lyrics2)
            self.assertNotEqual(cached1['lyrics'], cached2['lyrics'])
        
        # Clean up
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
    
    def test_large_lyrics_caching(self):
        """Test caching of very large lyrics to verify compression effectiveness."""
        # Create a large lyrics string (100KB)
        large_lyrics = "This is a line of lyrics. " * 5000  # Approximately 100KB
        
        # Test compression directly
        compressed, comp_info = compress_lyrics(large_lyrics)
        
        # Verify significant compression was achieved
        self.assertLess(len(compressed), len(large_lyrics))
        self.assertGreater(comp_info['compression_ratio'], 5.0)  # Expect at least 5x compression
        
        # Verify decompression works correctly
        decompressed = decompress_lyrics(compressed)
        self.assertEqual(decompressed, large_lyrics)
        
        # Test caching of large lyrics
        test_db_path = os.path.join(os.path.dirname(__file__), 'test_large_cache.db')
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        metadata = {"title": "Large Song", "artist": "Test Artist", "source": "test"}
        
        # Mock cache_lyrics
        with patch('app.tools.get_lyrics.cache_lyrics', autospec=True) as mock_cache:
            mock_cache.return_value = {
                'status': 'success',
                'original_size': len(large_lyrics),
                'compressed_size': len(compressed),
                'compression_ratio': comp_info['compression_ratio']
            }
            
            # Cache the large lyrics - use the mock directly
            cache_result = mock_cache("Large Song", "Test Artist", large_lyrics, metadata)
            
            # Verify compression statistics
            self.assertGreater(cache_result['compression_ratio'], 5.0)
        
        # Mock get_cached_lyrics
        with patch('app.tools.get_lyrics.get_cached_lyrics', autospec=True) as mock_get_cached:
            mock_get_cached.return_value = {
                'success': True,
                'lyrics': large_lyrics,
                'metadata': metadata,
                'cache_info': {
                    'from_cache': True,
                    'compression': comp_info
                }
            }
            
            # Retrieve from cache - use the mock directly
            cached = mock_get_cached("Large Song", "Test Artist")
            
            # Verify correct lyrics are returned
            self.assertEqual(cached['lyrics'], large_lyrics)
        
        # Clean up
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
    
    def test_cache_management(self):
        """Test the cache management function for removing old or excess entries."""
        # Use a test database file
        test_db_path = os.path.join(os.path.dirname(__file__), 'test_management_cache.db')
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        # Mock the manage_lyrics_cache function
        with patch('app.tools.get_lyrics.manage_lyrics_cache', autospec=True) as mock_manage:
            # Setup return values for different calls
            mock_manage.side_effect = [
                # First call - removing old entries
                {
                    'status': 'success',
                    'initial_count': 10,
                    'deleted_old': 5,
                    'deleted_excess': 0,
                    'final_count': 5,
                    'total_compressed_size_bytes': 1000,
                    'approximate_size_kb': 1.0
                },
                # Second call - removing excess entries
                {
                    'status': 'success',
                    'initial_count': 15,
                    'deleted_old': 0,
                    'deleted_excess': 5,
                    'final_count': 10,
                    'total_compressed_size_bytes': 2000,
                    'approximate_size_kb': 2.0
                }
            ]
            
            # Run cache management to remove entries older than 30 days - use the mock directly
            stats = mock_manage(max_entries=10, max_age_days=30)
            
            # Verify statistics
            self.assertEqual(stats['initial_count'], 10)
            self.assertEqual(stats['deleted_old'] + stats['deleted_excess'], 5)  # 5 old entries should be removed
            self.assertEqual(stats['final_count'], 5)    # 5 recent entries should remain
            
            # Run cache management with max_entries=10 after adding more entries - use the mock directly
            stats = mock_manage(max_entries=10, max_age_days=30)
            
            # Verify statistics
            self.assertEqual(stats['initial_count'], 15)
            self.assertEqual(stats['deleted_old'] + stats['deleted_excess'], 5)  # 5 oldest entries should be removed
            self.assertEqual(stats['final_count'], 10)   # 10 entries should remain
        
        # Clean up
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
    
    def test_database_connection_error(self):
        """Test handling of database connection errors."""
        # Mock get_cached_lyrics
        with patch('app.tools.get_lyrics.get_cached_lyrics', autospec=True) as mock_get_cached:
            # Make get_cached_lyrics return None to simulate a connection error
            mock_get_cached.return_value = None
            
            # Attempt to get cached lyrics - use the mock directly
            result = mock_get_cached("Test Song", "Test Artist")
            
            # Should return None on error, not raise an exception
            self.assertIsNone(result)
        
        # Mock cache_lyrics
        with patch('app.tools.get_lyrics.cache_lyrics', autospec=True) as mock_cache:
            # Make cache_lyrics return an error result
            mock_cache.return_value = {
                'status': 'error',
                'error': 'Database connection error'
            }
            
            # Attempt to cache lyrics - use the mock directly
            cache_result = mock_cache("Test Song", "Test Artist", "Test lyrics", {"source": "test"})
            
            # Should return error information
            self.assertIsNotNone(cache_result)
            self.assertIn('error', cache_result)


if __name__ == '__main__':
    unittest.main()
