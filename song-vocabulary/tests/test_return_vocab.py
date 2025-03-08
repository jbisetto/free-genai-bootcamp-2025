"""
Tests for the return_vocabulary tool.
"""
import unittest
from app.tools.return_vocab import return_vocabulary

class TestReturnVocabulary(unittest.TestCase):
    """Test cases for the return_vocabulary tool."""
    
    def test_successful_vocabulary_return(self):
        """Test that vocabulary data is correctly returned when successful."""
        # Sample input data
        input_data = {
            "success": True,
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
                    "kanji": "音楽",
                    "romaji": "ongaku",
                    "english": "music",
                    "parts": [
                        {
                            "kanji": "音",
                            "romaji": ["on"]
                        },
                        {
                            "kanji": "楽",
                            "romaji": ["ga", "ku"]
                        }
                    ]
                }
            ]
        }
        
        # Call the function
        result = return_vocabulary(input_data)
        
        # Assertions
        self.assertIn("vocabulary", result)
        self.assertEqual(len(result["vocabulary"]), 2)
        self.assertEqual(result["vocabulary"][0]["kanji"], "夢")
        self.assertEqual(result["vocabulary"][0]["english"], "dream")
        self.assertEqual(result["vocabulary"][1]["kanji"], "音楽")
        self.assertEqual(result["vocabulary"][1]["english"], "music")
        self.assertNotIn("error", result)
    
    def test_error_handling(self):
        """Test that errors are correctly handled and returned."""
        # Sample input data with error
        input_data = {
            "success": False,
            "error": "Failed to extract vocabulary",
            "vocabulary": []
        }
        
        # Call the function
        result = return_vocabulary(input_data)
        
        # Assertions
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Failed to extract vocabulary")
        self.assertNotIn("vocabulary", result)
    
    def test_empty_vocabulary(self):
        """Test handling of empty vocabulary list."""
        # Sample input data with empty vocabulary
        input_data = {
            "success": True,
            "vocabulary": []
        }
        
        # Call the function
        result = return_vocabulary(input_data)
        
        # Assertions
        self.assertIn("error", result)
        self.assertEqual(result["error"], "No vocabulary items found")
        self.assertNotIn("vocabulary", result)
    
    def test_missing_success_flag(self):
        """Test handling when success flag is missing."""
        # Sample input data without success flag
        input_data = {
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
        
        # Call the function
        result = return_vocabulary(input_data)
        
        # Assertions
        self.assertIn("error", result)
        self.assertNotIn("vocabulary", result)
    
    def test_unknown_error(self):
        """Test handling when error message is not provided."""
        # Sample input data with error but no error message
        input_data = {
            "success": False
        }
        
        # Call the function
        result = return_vocabulary(input_data)
        
        # Assertions
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Unknown error occurred")
        self.assertNotIn("vocabulary", result)

if __name__ == '__main__':
    unittest.main()
