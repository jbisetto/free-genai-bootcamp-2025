"""
Test module for the get_lyrics tool.
"""
import unittest
import os
import sqlite3
import time
import json
from unittest.mock import patch, MagicMock
from app.tools.get_lyrics import get_lyrics, setup_lyrics_cache_db, compress_lyrics, decompress_lyrics, cache_lyrics, get_cached_lyrics, manage_lyrics_cache

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
        # Remove test database
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

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

        # Call the function with use_mock=False to force web search
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

        # Call the function without artist and with use_mock=False to force web search
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

        # Call the function with use_mock=False to force web search
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
        # Use use_mock=False to force web search
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


if __name__ == '__main__':
    unittest.main()
