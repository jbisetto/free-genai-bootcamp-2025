"""
Test module for the get_lyrics tool.
"""
import unittest
import logging
from unittest.mock import patch, MagicMock
from app.tools.get_lyrics import get_lyrics

# Set up logging
logger = logging.getLogger(__name__)

class TestGetLyrics(unittest.TestCase):
    """Test cases for the get_lyrics function."""
    
    def test_mock_lyrics(self):
        """Test that mock lyrics are returned when use_mock is True."""
        song = "Test Song"
        artist = "Test Artist"
        
        # Get mock lyrics
        result = get_lyrics(song, artist, use_mock=True)
        
        # Verify the result
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['lyrics'])
        self.assertIn(song, result['lyrics'])
        self.assertIn(artist, result['lyrics'])
        
        # Verify metadata
        self.assertEqual(result['metadata']['title'], song)
        self.assertEqual(result['metadata']['artist'], artist)
        self.assertEqual(result['metadata']['source'], 'mock_data')
        self.assertTrue(result['metadata']['is_mock'])
        self.assertIn('language', result['metadata'])
        self.assertIn('fetched_at', result['metadata'])
    
    def test_mock_lyrics_no_artist(self):
        """Test that mock lyrics are returned when artist is None."""
        song = "Test Song"
        
        # Get mock lyrics without artist
        result = get_lyrics(song, use_mock=True)
        
        # Verify the result
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['lyrics'])
        self.assertIn(song, result['lyrics'])
        self.assertIn('Unknown', result['lyrics'])
        
        # Verify metadata
        self.assertEqual(result['metadata']['title'], song)
        self.assertEqual(result['metadata']['artist'], 'Unknown')
        self.assertEqual(result['metadata']['source'], 'mock_data')
        self.assertTrue(result['metadata']['is_mock'])
    
    @patch('app.tools.get_lyrics.DDGS')
    def test_web_lyrics_success(self, mock_ddgs):
        """Test fetching lyrics from web with successful results."""
        # Setup mock
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = [
            {
                'title': 'Test Lyrics',
                'body': 'Sample lyrics for testing',
                'href': 'https://example.com/lyrics'
            }
        ]
        
        # Get lyrics from web
        result = get_lyrics("Test Song", "Test Artist", use_mock=False)
        
        # Verify the result
        self.assertTrue(result['success'])
        self.assertEqual(result['lyrics'], 'Sample lyrics for testing')
        
        # Verify metadata
        self.assertEqual(result['metadata']['title'], 'Test Song')
        self.assertEqual(result['metadata']['artist'], 'Test Artist')
        self.assertEqual(result['metadata']['source'], 'https://example.com/lyrics')
        self.assertIn('language', result['metadata'])
        self.assertIn('fetched_at', result['metadata'])
        
        # Verify the search query
        mock_instance.text.assert_called_once_with('Test Artist Test Song lyrics', max_results=5)
    
    @patch('app.tools.get_lyrics.DDGS')
    def test_web_lyrics_no_results(self, mock_ddgs):
        """Test fetching lyrics from web with no results."""
        # Setup mock to return empty results
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = []
        
        # Get lyrics from web
        result = get_lyrics("Test Song", "Test Artist", use_mock=False)
        
        # Verify the result
        self.assertFalse(result['success'])
        self.assertIsNone(result['lyrics'])
        self.assertIsNone(result['metadata'])
        self.assertIn('error', result)
        self.assertIn('No lyrics found', result['error'])
    
    @patch('app.tools.get_lyrics.DDGS')
    def test_web_lyrics_exception(self, mock_ddgs):
        """Test handling of exceptions when fetching lyrics from web."""
        # Setup mock to raise an exception
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.side_effect = Exception("Test exception")
        
        # Get lyrics from web
        result = get_lyrics("Test Song", "Test Artist", use_mock=False)
        
        # Verify the result
        self.assertFalse(result['success'])
        self.assertIsNone(result['lyrics'])
        self.assertIsNone(result['metadata'])
        self.assertIn('error', result)
        self.assertIn('Test exception', result['error'])
    
    def test_language_detection_english(self):
        """Test language detection for English lyrics."""
        # Get mock lyrics
        result = get_lyrics("English Song", "Test Artist", use_mock=True)
        
        # Verify language detection
        self.assertEqual(result['metadata']['language'], 'english')
    
    @patch('app.tools.get_lyrics.DDGS')
    def test_language_detection_japanese(self, mock_ddgs):
        """Test language detection for Japanese lyrics."""
        # Setup mock with Japanese lyrics
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = [
            {
                'title': 'Japanese Lyrics',
                'body': '日本語の歌詞です。テストのために。',
                'href': 'https://example.com/lyrics'
            }
        ]
        
        # Get lyrics from web
        result = get_lyrics("Japanese Song", "Japanese Artist", use_mock=False)
        
        # Verify language detection
        self.assertEqual(result['metadata']['language'], 'japanese')
    


    @patch('app.tools.get_lyrics.DDGS')
    def test_successful_lyrics_retrieval(self, mock_ddgs):
        """Test successful retrieval of lyrics."""
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

    @patch('app.tools.get_lyrics.DDGS')
    def test_no_artist_provided(self, mock_ddgs):
        """Test lyrics retrieval when no artist is provided."""
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
        
    @patch('app.tools.get_lyrics.DDGS')
    def test_exception_handling(self, mock_ddgs):
        """Test handling of exceptions during lyrics retrieval."""
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

    def test_mock_mode(self):
        """Test the mock mode for lyrics retrieval."""
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
    
    @patch('app.tools.get_lyrics.DDGS')
    def test_web_lyrics_retrieval_success(self, mock_ddgs):
        """Test successful retrieval of lyrics from the web."""
        # Setup mock response
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = [
            {
                'title': 'Song Lyrics - Artist',
                'body': 'These are the lyrics for the song',
                'href': 'https://example.com/lyrics'
            }
        ]
        
        # Call the function
        result = get_lyrics("Song", "Artist")
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['lyrics'], 'These are the lyrics for the song')
        self.assertEqual(result['metadata']['title'], 'Song')
        self.assertEqual(result['metadata']['artist'], 'Artist')
        self.assertEqual(result['metadata']['source'], 'https://example.com/lyrics')
    
    @patch('app.tools.get_lyrics.DDGS')
    def test_web_lyrics_retrieval_no_results(self, mock_ddgs):
        """Test when no lyrics are found for a song."""
        # Setup mock response with empty results
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = []
        
        # Call the function
        result = get_lyrics("Nonexistent Song", "Unknown Artist")
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIsNone(result['lyrics'])
        self.assertIn('No lyrics found', result['error'])
    
    @patch('app.tools.get_lyrics.DDGS')
    def test_web_lyrics_retrieval_exception(self, mock_ddgs):
        """Test handling of exceptions during lyrics retrieval."""
        # Setup mock to raise an exception
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.side_effect = Exception("Test exception")
        
        # Call the function
        result = get_lyrics("Song", "Artist")
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIsNone(result['lyrics'])
        self.assertIn('error', result)
        self.assertIn('Test exception', result['error'])
    
    def test_language_detection(self):
        """Test language detection functionality."""
        # Test English detection
        english_lyrics = "These are English lyrics for testing purposes."
        result = get_lyrics("Test Song", "Test Artist", use_mock=True)
        self.assertEqual(result['metadata']['language'], 'english')
        
        # Test Japanese detection (simulated)
        # Create a mock result with Japanese characters
        with patch('app.tools.get_lyrics.DDGS') as mock_ddgs:
            mock_instance = MagicMock()
            mock_ddgs.return_value = mock_instance
            mock_instance.text.return_value = [
                {
                    'title': 'Japanese Lyrics',
                    'body': 'これは日本語の歌詞です。テスト用です。',
                    'href': 'https://example.com/japanese'
                }
            ]
            
            # Call the function
            result = get_lyrics("Japanese Song", "Japanese Artist")
            
            # Verify language detection
            self.assertEqual(result['metadata']['language'], 'japanese')
    
    @patch('app.tools.get_lyrics.DDGS')
    def test_lyrics_with_special_characters(self, mock_ddgs):
        """Test handling of lyrics with special characters."""
        # Setup mock response with special characters
        mock_instance = MagicMock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = [
            {
                'title': 'Special Lyrics',
                'body': 'Lyrics with special characters: é, ñ, ü, ç, ß',
                'href': 'https://example.com/special'
            }
        ]
        
        # Call the function
        result = get_lyrics("Special Song", "Artist")
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['lyrics'], 'Lyrics with special characters: é, ñ, ü, ç, ß')
        self.assertIn('language', result['metadata'])

if __name__ == '__main__':
    unittest.main()
