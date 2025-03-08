"""
Tool for formatting vocabulary data into the required JSON structure.
"""
from typing import Dict, Any, List

def return_vocabulary(vocabulary_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats vocabulary data into the required JSON structure.
    
    Args:
        vocabulary_data: The vocabulary data to format
    
    Returns:
        A dictionary containing the formatted vocabulary
    """
    if not vocabulary_data.get("success", False):
        return {
            "error": vocabulary_data.get("error", "Unknown error occurred")
        }
    
    vocabulary = vocabulary_data.get("vocabulary", [])
    
    if not vocabulary:
        return {
            "error": "No vocabulary items found"
        }
    
    # The vocabulary is already in the correct format from extract_vocabulary
    # Just return it in the expected response structure
    return {
        "vocabulary": vocabulary
    }

if __name__ == "__main__":
    # Example usage
    sample_data = {
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
            }
        ]
    }
    
    result = return_vocabulary(sample_data)
    print(result)
