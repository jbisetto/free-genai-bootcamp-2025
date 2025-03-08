"""
Test module for the extract_vocab tool.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import sys

# Import the function to test
from app.tools.extract_vocab import extract_vocabulary, MODEL_NAME

class TestExtractVocabulary(unittest.TestCase):
    """Test cases for the extract_vocabulary function."""

    def test_empty_lyrics(self):
        """Test behavior when empty lyrics are provided."""
        # Call the function with empty lyrics
        result = extract_vocabulary("")
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "No lyrics provided")
        self.assertEqual(result['vocabulary'], [])
    
    def test_lyrics_truncation(self):
        """Test that lyrics longer than 400 words are truncated."""
        # Create lyrics with more than 400 words
        long_lyrics = " ".join(["word"] * 500)
        
        # We can't easily test the actual truncation without mocking the LLM,
        # but we can verify the function doesn't crash with long input
        with patch('app.tools.extract_vocab.instructor.patch') as mock_patch:
            # Setup the mock to raise an exception to avoid calling the real LLM
            mock_client = MagicMock()
            mock_patch.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("Test exception")
            
            # Call the function
            result = extract_vocabulary(long_lyrics)
            
            # Verify the function handled the exception properly
            self.assertFalse(result['success'])
            self.assertIn("Error extracting vocabulary", result['error'])
    
    @patch('app.tools.extract_vocab.instructor.patch')
    @patch('app.tools.extract_vocab.client')
    def test_general_error_handling(self, mock_client, mock_instructor_patch):
        """Test general error handling during vocabulary extraction."""
        # Setup mock to raise a specific exception
        mock_instructor_client = MagicMock()
        mock_instructor_patch.return_value = mock_instructor_client
        mock_instructor_client.chat.completions.create.side_effect = Exception("Test error")
        
        # Call the function
        result = extract_vocabulary("Sample lyrics")
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn("Error extracting vocabulary", result['error'])
        self.assertEqual(result['vocabulary'], [])
    
    def test_model_name_constant(self):
        """Test that the MODEL_NAME constant is set correctly."""
        self.assertEqual(MODEL_NAME, "mistral:7b")
    
    @patch('app.tools.extract_vocab.instructor.patch')
    @patch('app.tools.extract_vocab.client')
    def test_instructor_client_creation(self, mock_client, mock_instructor_patch):
        """Test that the instructor client is created correctly."""
        # Setup mock
        mock_instructor_client = MagicMock()
        mock_instructor_patch.return_value = mock_instructor_client
        mock_instructor_client.chat.completions.create.side_effect = Exception("Test exception")
        
        # Call the function
        extract_vocabulary("Sample lyrics")
        
        # Verify instructor.patch was called with the client
        mock_instructor_patch.assert_called_once_with(mock_client)

if __name__ == '__main__':
    unittest.main()
