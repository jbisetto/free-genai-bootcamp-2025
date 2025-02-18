import streamlit as st
import requests
import os
import logging
from google import genai

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

# Get the Google Gemini API key from the environment variable
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY environment variable not set. Please set it before running the app.")
    st.stop()

# Initialize Gemini
client = genai.Client(api_key=api_key)

# API endpoint
API_ENDPOINT = "http://localhost:5000/api/groups/"  # Base URL

# Function to get words from the API
def get_words(group_id):
    logger.debug(f"Getting words for group {group_id}")
    try:
    
        response = requests.get(f"{API_ENDPOINT}{group_id}/words/raw")
        logger.debug(f"Response: {response.json()}")
        response.raise_for_status()
        data = response.json()
        return data  # Expecting a list of dictionaries
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return None

# LLM functions
def generate_sentence(word):
    prompt = f"""Generate a simple sentence that contains the following word: {word}
The grammar of the sentence should be scoped to JLPTN5 grammar level.
You can use the following vocabulary to construct a simple sentence:
- simple objects eg. book, car, house
- simple verbs eg. read, drive, eat
- simple adjectives eg. red, big, tasty
- simple adverbs eg. quickly, very, always"""
    response = client.generate_text(model="gemini-1.5-flash", prompt=prompt)
    return response.result

def translate_to_english(text_jp):
    prompt = f"""Translate the following text from japanese to english:
{text_jp}"""
    response = client.models.generate_content(model="gemini-2.0-flash", prompt=prompt)
    return response.result

def grade_translation(text, reference_text):
    prompt = f"""Grade the following piece of text based on the reference text:
{text}. Provide a letter score using the japanase S Rank to score the user's translation.
Provide an evaluation of the user's translation with suggestions for improvement."""
    response = text.generate_text(model="gemini-1.5-flash", prompt=prompt)
    return response.result


# Streamlit app
st.title("Japanese Writing Practice")

# Group ID input
group_id = st.number_input("Enter Group ID", min_value=1, value=1, step=1)

words_data = get_words(group_id)
if words_data is None:
    st.stop()

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

if st.session_state.state == "initial":
    st.write("Welcome to the Japanese Writing Practice app!")
    if st.button("Let's Practice Writing!"):
        st.session_state.current_word = words_data[st.session_state.word_index]["word_en"]
        st.session_state.current_sentence_en = generate_sentence(st.session_state.current_word)
        st.session_state.state = "practice"

elif st.session_state.state == "practice":
    st.write(f"Translate the following sentence into Japanese:")
    st.write(f"**{st.session_state.current_sentence_en}**")

    uploaded_file = st.file_uploader("Upload your writing", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        # Placeholder for MangaOCR integration.  You'll need to install and integrate MangaOCR here.
        # For this example, we'll just simulate the transcription.
        st.session_state.user_translation_jp = "（ここに日本語の文字起こしが入ります）"  # Replace with actual MangaOCR output

        if st.button("Check my writing"):
            # Placeholder for Translation Sub-System
            translated_user_text_en = translate_to_english(st.session_state.user_translation_jp)

            # Placeholder for Grading Sub-System
            st.session_state.evaluation_report = grade_translation(translated_user_text_en, st.session_state.current_sentence_en)

            st.session_state.state = "results"

elif st.session_state.state == "results":
    st.write(f"Original English Sentence: **{st.session_state.current_sentence_en}**")
    st.write(f"Your Japanese Translation: **{st.session_state.user_translation_jp}**")
    st.write(f"Evaluation: **{st.session_state.evaluation_report}**")

    if "Try again" in st.session_state.evaluation_report.lower():
        if st.button("Try again"):
            st.session_state.state = "practice"
    else:
        if st.button("Give me another sentence"):
            st.session_state.word_index = (st.session_state.word_index + 1) % len(words_data)
            st.session_state.current_word = words_data[st.session_state.word_index]["word_en"]
            st.session_state.current_sentence_en = generate_sentence(st.session_state.current_word)
            st.session_state.state = "practice"

    if st.button("Finish"):
        st.session_state.clear()
        st.experimental_rerun()