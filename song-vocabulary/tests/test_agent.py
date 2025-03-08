"""
Tests for the vocabulary extraction agent.
"""
import unittest
from unittest.mock import patch, MagicMock
import json

from app.agent.agent import run_agent, parse_llm_response

class TestVocabularyAgent(unittest.TestCase):
    """Test cases for the vocabulary extraction agent."""
    
    def test_parse_llm_response(self):
        """Test parsing of LLM responses in different formats."""
        # Test parsing a response with thought and action
        response1 = """
        Thought: I need to get the lyrics for the song first.
        Action: get_lyrics
        Action Input: {"song": "Lemon", "artist": "Kenshi Yonezu"}
        """
        thought, action, action_input, final_answer = parse_llm_response(response1)
        self.assertEqual(thought, "I need to get the lyrics for the song first.")
        self.assertEqual(action, "get_lyrics")
        # Check if action_input is a dict or string and handle accordingly
        if isinstance(action_input, str):
            self.assertEqual(json.loads(action_input), {"song": "Lemon", "artist": "Kenshi Yonezu"})
        else:
            self.assertEqual(action_input, {"song": "Lemon", "artist": "Kenshi Yonezu"})
        self.assertIsNone(final_answer)
        
        # Test parsing a response with final answer
        response2 = """
        Thought: I have extracted the vocabulary from the lyrics.
        Final Answer: {"vocabulary": [{"kanji": "レモン", "romaji": "remon", "english": "lemon"}]}
        """
        thought, action, action_input, final_answer = parse_llm_response(response2)
        self.assertEqual(thought, "I have extracted the vocabulary from the lyrics.")
        self.assertIsNone(action)
        self.assertIsNone(action_input)
        self.assertEqual(final_answer, {"vocabulary": [{"kanji": "レモン", "romaji": "remon", "english": "lemon"}]})
    
    @patch('app.agent.agent.client')
    def test_agent_workflow(self, mock_client):
        """Test the complete agent workflow with mocked tools."""
        # Mock the LLM response to directly return a final answer
        mock_client.chat.return_value = {
            "message": {
                "content": """
                Thought: I have extracted the vocabulary, now I will return it.
                Final Answer: {"vocabulary": [
                    {
                        "kanji": "レモン",
                        "romaji": "remon",
                        "english": "lemon",
                        "parts": [
                            {"kanji": "レ", "romaji": ["re"]},
                            {"kanji": "モ", "romaji": ["mo"]},
                            {"kanji": "ン", "romaji": ["n"]}
                        ]
                    }
                ]}
                """
            }
        }
        
        # Run the agent
        result = run_agent("Lemon", "Kenshi Yonezu")
        
        # Verify the result
        self.assertIn("vocabulary", result)
        self.assertEqual(len(result["vocabulary"]), 1)
        self.assertEqual(result["vocabulary"][0]["kanji"], "レモン")
        self.assertNotIn("error", result)
    
    @patch('app.agent.agent.client')
    def test_agent_error_handling_no_lyrics(self, mock_client):
        """Test agent error handling when no lyrics are found."""
        # Mock the client to return a response indicating no lyrics found
        mock_client.chat.return_value = {
            "message": {
                "content": """
                Thought: I couldn't find any lyrics for this song.
                Final Answer: No lyrics found for NonExistentSong by NonExistentArtist.
                """
            }
        }
        
        # Run the agent
        result = run_agent("NonExistentSong", "NonExistentArtist")
        
        # Verify the result
        self.assertIn("error", result)
        # Check for a more general error message that would be present
        self.assertTrue("No lyrics" in result["error"] or 
                      "couldn't find any lyrics" in result["error"].lower() or
                      "no lyrics found" in result["error"].lower())
    
    @patch('app.agent.agent.client')
    def test_agent_error_handling_llm_error(self, mock_client):
        """Test agent error handling when the LLM raises an exception."""
        # Mock the client to raise an exception
        mock_client.chat.side_effect = Exception("LLM error")
        
        # Run the agent
        result = run_agent("Lemon", "Kenshi Yonezu")
        
        # Verify the result
        self.assertIn("error", result)
        self.assertIn("LLM error", result["error"])

if __name__ == '__main__':
    unittest.main()
