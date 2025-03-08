"""
Tool for extracting Japanese vocabulary from song lyrics.
"""
from typing import Dict, Any, List
import instructor
from ollama import Client
import json
import logging
from pydantic import BaseModel

# Initialize logging
logger = logging.getLogger(__name__)

# Define the model name
MODEL_NAME = "mistral:7b"

# Initialize the Ollama client
client = Client(host="http://localhost:11434")

def extract_vocabulary(lyrics: str) -> Dict[str, Any]:
    """
    Extracts Japanese vocabulary from song lyrics, handling both Japanese and English inputs.
    
    Args:
        lyrics: The song lyrics to extract vocabulary from
    
    Returns:
        A dictionary containing the extracted vocabulary
        
    Language Handling:
        - Japanese lyrics: Vocabulary is extracted directly from the lyrics
        - English lyrics: Nouns, verbs, and adjectives are identified and translated to Japanese
    """
    if not lyrics:
        return {
            "success": False,
            "error": "No lyrics provided",
            "vocabulary": []
        }
    
    # Limit lyrics to 400 words to ensure efficient processing
    words = lyrics.split()
    if len(words) > 400:
        lyrics = " ".join(words[:400])
        logger.info(f"Lyrics truncated from {len(words)} to 400 words for processing")
    
    try:
        # Use instructor to create a structured output
        instructor_client = instructor.patch(client)
        
        # Define the schema for vocabulary items
        class Part(instructor.dsl.InstructorDSLModel):
            kanji: str
            romaji: List[str]
        
        class VocabularyItem(instructor.dsl.InstructorDSLModel):
            kanji: str
            romaji: str
            english: str
            parts: List[Part]
        
        class VocabularyResponse(instructor.dsl.InstructorDSLModel):
            vocabulary: List[VocabularyItem]
        
        # JSON example for the prompt
        json_example = '''
```json
{
  "vocabulary": [
    {
      "kanji": "レモン",
      "romaji": "remon",
      "english": "lemon",
      "parts": [
        {"kanji": "レ", "romaji": ["re"]},
        {"kanji": "モ", "romaji": ["mo"]},
        {"kanji": "ン", "romaji": ["n"]}
      ]
    },
    {
      "kanji": "愛",
      "romaji": "ai",
      "english": "love",
      "parts": [
        {"kanji": "愛", "romaji": ["ai"]}
      ]
    },
    {
      "kanji": "音楽",
      "romaji": "ongaku",
      "english": "music",
      "parts": [
        {"kanji": "音", "romaji": ["on"]},
        {"kanji": "楽", "romaji": ["ga", "ku"]}
      ]
    },
    {
      "kanji": "歌",
      "romaji": "uta",
      "english": "song",
      "parts": [
        {"kanji": "歌", "romaji": ["u", "ta"]}
      ]
    },
    {
      "kanji": "心",
      "romaji": "kokoro",
      "english": "heart",
      "parts": [
        {"kanji": "心", "romaji": ["ko", "ko", "ro"]}
      ]
    }
  ]
}
```
'''
        
        # Create the prompt for extracting vocabulary
        prompt = f"""
        You are a Japanese language expert. Extract important vocabulary words from the following song lyrics.
        For each word:
        1. Provide the kanji/kana form
        2. Provide the romaji (romanized) pronunciation
        3. Provide the English translation
        4. Break down each kanji character with its romaji pronunciation
        
        ⚠️ CRITICAL REQUIREMENT: You can extract up to 400 vocabulary items. ⚠️
        
        INSTRUCTIONS FOR DIFFERENT LANGUAGES:
        
        If the lyrics are primarily in Japanese:
        - Extract vocabulary words directly from the Japanese lyrics
        - Focus on important nouns, verbs, adjectives, and expressions
        
        If the lyrics are primarily in English:
        - Identify only nouns, verbs, and adjectives from the English lyrics
        - Ignore function words (prepositions, articles, conjunctions, pronouns, etc.)
        - Translate each identified word into Japanese (kanji/kana)
        - Provide the romaji pronunciation
        - Provide the original English word
        - Break down each kanji character with its romaji pronunciation
        
        FORMAT YOUR RESPONSE EXACTLY LIKE THE EXAMPLE BELOW. DO NOT DEVIATE FROM THIS FORMAT.
        {json_example}
        
        Here are the lyrics:
        
        {lyrics}
        """
        
        # Get the structured response from the LLM
        response = instructor_client.chat.completions.create(
            model=MODEL_NAME,
            response_model=VocabularyResponse,
            messages=[
                {"role": "system", "content": "You are a helpful Japanese language teaching assistant. Your task is to extract vocabulary items from song lyrics. You MUST provide EXACTLY 5 vocabulary items. Follow the format in the example precisely."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # Lower temperature for more consistent results
            max_tokens=2000  # Ensure we have enough tokens for a complete response
        )
        
        # Convert Pydantic models to dictionaries for proper JSON serialization
        vocab_list = []
        for item in response.vocabulary:
            parts_list = []
            for part in item.parts:
                parts_list.append({
                    "kanji": part.kanji,  # Use kanji instead of character
                    "romaji": part.romaji
                })
            
            vocab_list.append({
                "kanji": item.kanji,
                "romaji": item.romaji,
                "english": item.english,
                "parts": parts_list
            })
        
        return {
            "success": True,
            "vocabulary": vocab_list
        }
    
    except Exception as e:
        error_msg = str(e)
        
        # Add a note about expected errors during testing
        if "InstructorDSLModel" in error_msg and "no attribute" in error_msg:
            logger.error(f"Error extracting vocabulary: {error_msg} (EXPECTED DURING TESTING)")
        else:
            logger.error(f"Error extracting vocabulary: {error_msg}")
        
        # Check for specific error messages
        if "model not found" in error_msg.lower():
            return {
                "success": False,
                "error": "Ollama model not found. Please make sure Ollama is running and the Mistral model is installed.\n\n"
                        "To install the model, run the following command in your terminal:\n\n"
                        "ollama pull mistral:7b\n\n"
                        "After installing the model, restart the application and try again.",
                "vocabulary": []
            }
        
        return {
            "success": False,
            "error": f"Error extracting vocabulary: {error_msg}",
            "vocabulary": []
        }

if __name__ == "__main__":
    # Example usage
    sample_lyrics = """
    夢ならばどれほどよかったでしょう
    未だにあなたのことを夢にみる
    忘れた物を取りに帰るように
    古びた思い出の埃を払う
    
    戻らない幸せがあることを
    最後にあなたが教えてくれた
    言えずに隠してた昏い過去も
    あなたがいなきゃ永遠に昏いまま
    
    きっともうこれ以上 傷つくことなど
    ありはしないとわかっている
    あの日の悲しみさえ
    あの日の苦しみさえ
    そのすべてを愛してた あなたとともに
    胸に残り離れない
    """
    result = extract_vocabulary(sample_lyrics)
    print(json.dumps(result, ensure_ascii=False, indent=2))
