import streamlit as st
import requests
import os
import logging
import json
import google.generativeai as genai
from urllib.parse import urlparse, parse_qs
import tempfile
from PIL import Image

# Create a logger
logger = logging.getLogger("Writing Practice App")
logger.setLevel(logging.DEBUG)

# Create a file handler
file_handler = logging.FileHandler("writing-practice.log")
file_handler.setLevel(logging.DEBUG)

# Create a formatter and add it to the handler
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

# Set page configuration
st.set_page_config(
    page_title="Japanese Writing Practice",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get the Google Gemini API key from the environment variable
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY environment variable not set. Please set it before running the app.")
    st.stop()

# Initialize Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# API endpoint
API_ENDPOINT = "http://localhost:5000/api"  # Base URL

# Add a debug message to show the API endpoint
logger.debug(f"Using API endpoint: {API_ENDPOINT}")

# Function to test API connection
def test_api_connection():
    try:
        logger.debug(f"Testing API connection to {API_ENDPOINT}/health")
        response = requests.get(f"{API_ENDPOINT}/health", timeout=5)  # Increased timeout
        logger.debug(f"API health check response: {response.status_code}")
        logger.debug(f"API health check headers: {response.headers}")
        
        if response.status_code == 200:
            logger.info("API health check successful")
            return True
        elif response.status_code == 403:
            logger.error(f"API health check failed with 403 Forbidden. This may indicate an authentication issue.")
            return False
        elif response.status_code == 404:
            logger.error(f"API health check failed with 404 Not Found. The health endpoint may not exist.")
            return False
        else:
            logger.error(f"API health check failed with status code: {response.status_code}, response: {response.text}")
            return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"API connection error: {str(e)}")
        return False
    except requests.exceptions.Timeout as e:
        logger.error(f"API request timed out: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"API health check failed with unexpected error: {str(e)}")
        return False

# Test the API connection
api_available = test_api_connection()
logger.debug(f"API available: {api_available}")

# Parse query parameters from URL
def get_query_params():
    query_params = st.query_params
    logger.debug(f"Query parameters: {query_params}")
    
    group_id = query_params.get("group_id", "1")
    session_id = query_params.get("session_id", "")
    
    return {
        "group_id": group_id,
        "session_id": session_id
    }

# Function to get words from the API
def get_words(group_id):
    logger.debug(f"Getting words for group {group_id}")
    try:
        # Log the full URL we're trying to access
        url = f"{API_ENDPOINT}/groups/{group_id}/words/raw"
        logger.debug(f"Requesting words from URL: {url}")
        
        # Make the request with a timeout
        response = requests.get(url, timeout=10)
        
        # Log the response status and headers
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            words_data = response.json()
            logger.debug(f"Successfully retrieved {len(words_data)} words")
            return words_data
        else:
            logger.error(f"Failed to get words: {response.status_code} - {response.text}")
            # For debugging purposes, return mock data if API fails
            return [
                {"word_jp": "本", "word_en": "book"},
                {"word_jp": "車", "word_en": "car"},
                {"word_jp": "家", "word_en": "house"},
                {"word_jp": "読む", "word_en": "read"},
                {"word_jp": "食べる", "word_en": "eat"}
            ]
    except Exception as e:
        logger.error(f"Exception while getting words: {str(e)}")
        # For debugging purposes, return mock data if API fails
        return [
            {"word_jp": "本", "word_en": "book"},
            {"word_jp": "車", "word_en": "car"},
            {"word_jp": "家", "word_en": "house"},
            {"word_jp": "読む", "word_en": "read"},
            {"word_jp": "食べる", "word_en": "eat"}
        ]

# Function to send session results back to the API
def update_session_results(session_id, results):
    if not session_id:
        logger.warning("No session_id provided, skipping results update")
        return False
    
    logger.debug(f"Updating session {session_id} with results")
    try:
        response = requests.post(
            f"{API_ENDPOINT}/study-sessions/{session_id}/results",
            json=results
        )
        if response.status_code == 200:
            logger.debug("Successfully updated session results")
            return True
        else:
            logger.error(f"Failed to update session results: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception while updating session results: {str(e)}")
        return False

# LLM functions
def generate_sentence(word):
    prompt = f"""Generate a simple sentence that contains the following word: {word}
The grammar of the sentence should be scoped to JLPTN5 grammar level.
You can use the following vocabulary to construct a simple sentence:
- simple objects eg. book, car, house
- simple verbs eg. read, drive, eat
- simple adjectives eg. red, big, tasty
- simple adverbs eg. quickly, very, always"""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating sentence: {str(e)}")
        # Fallback to a simple sentence if the API call fails
        return f"This is a {word}."

def translate_to_english(text_jp):
    prompt = f"Translate the following text from japanese to english:\n{text_jp}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error translating text: {str(e)}")
        # Fallback to a simple translation if the API call fails
        return "Translation failed. Please try again."

def grade_translation(text, reference_text):
    prompt = f"""Grade the following piece of text based on the reference text:
{text}. Provide a letter score using the japanase S Rank to score the user's translation.
Provide an evaluation of the user's translation with suggestions for improvement."""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error grading translation: {str(e)}")
        # Fallback to a simple grade if the API call fails
        return "B - Good effort! Keep practicing."

# Mock MangaOCR function (in a real app, you would integrate the actual OCR library)
def transcribe_image(image_file):
    # This is a placeholder for MangaOCR integration
    # In a real implementation, you would use the MangaOCR library to transcribe the image
    
    # For demo purposes, return a placeholder text based on the current sentence
    logger.debug(f"Transcribing image: {image_file.name}")
    
    # In a real implementation, you would process the image here
    # For now, we'll generate mock Japanese text based on the current word
    current_word = st.session_state.current_word
    
    # Map of English words to Japanese mock translations
    mock_translations = {
        "book": "これは本です。",  # This is a book.
        "car": "私は車を持っています。",  # I have a car.
        "house": "彼の家は大きいです。",  # His house is big.
        "read": "私は毎日本を読みます。",  # I read books every day.
        "eat": "私は朝ごはんを食べました。",  # I ate breakfast.
        # Add more mappings for other words
    }
    
    # Return a mock translation based on the current word, or a default if not found
    return mock_translations.get(current_word, "日本語のテキスト例です。")

# Main Streamlit app
st.title("Japanese Writing Practice")

# Get query parameters
params = get_query_params()
group_id = params["group_id"]
session_id = params["session_id"]

# Display session information in sidebar
st.sidebar.write(f"Group ID: {group_id}")
if session_id:
    st.sidebar.write(f"Session ID: {session_id}")

# Display API connection status
if api_available:
    st.sidebar.success("API Connection: Connected")
else:
    st.sidebar.error("API Connection: Disconnected (using mock data)")

# Get words data
words_data = get_words(group_id)

# Display a warning if we're using mock data
if words_data and len(words_data) == 5 and words_data[0].get("word_en") == "book":
    st.warning("Using mock data because the API connection failed. The app will still function for demonstration purposes.")

# Initialize session state variables if they don't exist
if "state" not in st.session_state:
    st.session_state.state = "initial"
if "current_word" not in st.session_state:
    st.session_state.current_word = None
if "current_sentence_en" not in st.session_state:
    st.session_state.current_sentence_en = None
if "user_translation_jp" not in st.session_state:
    st.session_state.user_translation_jp = None
if "evaluation_report" not in st.session_state:
    st.session_state.evaluation_report = None
if "word_index" not in st.session_state:
    st.session_state.word_index = 0
if "results" not in st.session_state:
    st.session_state.results = []
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# Handle different page states
if st.session_state.state == "initial":
    # Initial State
    st.write("## Welcome to the Japanese Writing Practice app!")
    st.write("This application will help you practice writing Japanese sentences.")
    st.write("You'll be given English sentences to translate and write in Japanese.")
    st.write("Upload an image of your handwritten Japanese, and we'll evaluate it!")
    
    if st.button("Let's Practice Writing!", key="start_button"):
        # Get a word from the words data
        word_data = words_data[st.session_state.word_index]
        st.session_state.current_word = word_data["word_en"]
        # Generate a sentence using the word
        st.session_state.current_sentence_en = generate_sentence(st.session_state.current_word)
        # Change state to practice
        st.session_state.state = "practice"
        st.rerun()

elif st.session_state.state == "practice":
    # Practice State
    st.write("## Translate the following sentence into Japanese:")
    st.write(f"**{st.session_state.current_sentence_en}**")
    
    # File uploader for the user's writing
    uploaded_file = st.file_uploader("Upload your writing", type=["jpg", "png", "jpeg"], key="file_uploader")
    
    # Display the uploaded image if available
    if uploaded_file is not None:
        st.session_state.uploaded_image = uploaded_file
        image = Image.open(uploaded_file)
        st.image(image, caption="Your uploaded writing")
        
        # Enable the check button
        if st.button("Check my writing", key="check_button"):
            # Transcribe the image to Japanese text
            st.session_state.user_translation_jp = transcribe_image(uploaded_file)
            
            # Translate the Japanese text to English for comparison
            translated_user_text_en = translate_to_english(st.session_state.user_translation_jp)
            
            # Grade the translation
            st.session_state.evaluation_report = grade_translation(
                translated_user_text_en, 
                st.session_state.current_sentence_en
            )
            
            # Store result
            st.session_state.results.append({
                "word": st.session_state.current_word,
                "sentence_en": st.session_state.current_sentence_en,
                "user_translation_jp": st.session_state.user_translation_jp,
                "evaluation": st.session_state.evaluation_report
            })
            
            # Change state to results
            st.session_state.state = "results"
            st.rerun()
    else:
        # Disable the check button if no image is uploaded
        st.button("Check my writing", key="check_button_disabled", disabled=True)

elif st.session_state.state == "results":
    # Results State
    st.write("## Results")
    
    # Display the original sentence and user's translation
    st.write(f"**Original English Sentence:** {st.session_state.current_sentence_en}")
    st.write(f"**Your Japanese Translation:** {st.session_state.user_translation_jp}")
    
    # Display the evaluation
    st.write("### Evaluation:")
    st.write(st.session_state.evaluation_report)
    
    # Display the uploaded image
    if st.session_state.uploaded_image:
        image = Image.open(st.session_state.uploaded_image)
        st.image(image, caption="Your uploaded writing", use_container_width=True, width=300)
    
    # Determine which buttons to show based on evaluation
    if "try again" in st.session_state.evaluation_report.lower():
        if st.button("Try again", key="try_again_button"):
            # Keep the same sentence but reset the uploaded image
            st.session_state.uploaded_image = None
            st.session_state.state = "practice"
            st.rerun()
    else:
        if st.button("Give me another sentence", key="next_sentence_button"):
            # Move to the next word
            st.session_state.word_index = (st.session_state.word_index + 1) % len(words_data)
            word_data = words_data[st.session_state.word_index]
            st.session_state.current_word = word_data["word_en"]
            # Generate a new sentence
            st.session_state.current_sentence_en = generate_sentence(st.session_state.current_word)
            # Reset the uploaded image
            st.session_state.uploaded_image = None
            # Change state back to practice
            st.session_state.state = "practice"
            st.rerun()
    
    # Always show the finish button
    if st.button("Finish", key="finish_button"):
        # Send results to API if session_id is provided
        if session_id:
            success = update_session_results(session_id, {
                "results": st.session_state.results,
                "completed": True
            })
            if success:
                st.success("Session results saved successfully!")
            else:
                st.error("Failed to save session results.")
        
        # Reset the app state
        st.session_state.state = "initial"
        st.session_state.results = []
        st.session_state.word_index = 0
        st.session_state.uploaded_image = None
        st.rerun()

# Footer
st.sidebar.markdown("---")
st.sidebar.write("Japanese Writing Practice App")
st.sidebar.write(" 2025 Language Learning Portal")
