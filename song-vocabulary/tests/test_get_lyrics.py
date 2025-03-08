"""
Test module for the get_lyrics tool.
"""
import unittest
from unittest.mock import patch, MagicMock
from app.tools.get_lyrics import get_lyrics

class TestGetLyrics(unittest.TestCase):
    """Test cases for the get_lyrics function."""

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

        # Call the function
        result = get_lyrics("Lemon", "Kenshi Yonezu")

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

        # Call the function
        result = get_lyrics("Lemon")

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

        # Call the function
        result = get_lyrics("Lemon", "Kenshi Yonezu")

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

if __name__ == '__main__':
    unittest.main()
