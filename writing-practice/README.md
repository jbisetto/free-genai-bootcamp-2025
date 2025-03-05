# Japanese Writing Practice App

## Difficulty: Level 200

## Business Goal
Students have asked for a learning exercise to practice writing language sentences. This application takes a word group, generates simple English sentences, and allows students to practice writing them in Japanese. The app evaluates handwritten submissions and provides feedback on writing quality.

## Overview
A Streamlit-based application designed to help users practice Japanese writing through interactive exercises. The app provides English sentences for translation, evaluates handwritten Japanese submissions using OCR technology, and offers feedback on writing quality.

## Features
- **Interactive Writing Practice**: Translate English sentences to Japanese with a focus on specific vocabulary
- **Image-based Submissions**: Upload images of handwritten Japanese text for evaluation
- **AI-powered Evaluation**: Utilizes Google's Gemini AI to grade translations and provide feedback
- **Japanese OCR**: Implements MangaOCR to extract text from handwritten submissions
- **Progress Tracking**: Records practice results and can sync with a learning management system

## Technical Details
- **Frontend**: Streamlit UI with support for Japanese character rendering
- **Backend Integration**: Connects to a Flask backend API (port 5001) to retrieve word lists and store session results
- **AI Components**:
  - Google Gemini 1.5 Flash for sentence generation and translation evaluation
  - MangaOCR for Japanese text recognition from images
- **Debug Tools**: Includes Japanese text rendering tests and API connection diagnostics

## Technical Requirements
- Streamlit
- MangaOCR (Japanese) or for another language use Managed LLM that has Vision (e.g., GPT-4o)
- Image upload capability
- Google Generative AI Python SDK
- Environment variable: `GEMINI_API_KEY` (required for AI functionality)

## Setup and Usage
1. Start the backend API server on port 5001
2. Launch the app with `streamlit run writing-app.py`
3. Select vocabulary groups to practice
4. Translate the provided English sentences to Japanese
5. Upload images of your handwritten Japanese
6. Receive AI-generated feedback on your writing

## Lessons Learned

### Technical Insights
1. **API Integration Challenges**: 
   - Mismatches between API response formats and client expectations can cause subtle rendering issues
   - Proper field mapping between backend and frontend is critical for multilingual applications
   - Always implement robust error handling with informative logging for API interactions

2. **Unicode and Multilingual Support**:
   - Non-Latin character rendering requires special attention in web applications
   - Testing specific character rendering (like Japanese) should be part of the development workflow
   - Include debug tools to verify proper character encoding throughout the application stack

3. **Port Configuration**:
   - System services can conflict with development ports (macOS AirPlay using port 5000)
   - Standardizing on non-default ports across all application components prevents conflicts
   - Document port configurations to ensure consistency across development environments

### Development Practices
1. **Debugging Approach**:
   - Adding dedicated debug panels helps identify issues without modifying core code
   - Implementing fallback mechanisms ensures application usability even when components fail
   - Detailed logging with proper formatting prevents duplicate entries and provides clear context

2. **Code Organization**:
   - Extracting repeated code into dedicated functions improves maintainability
   - Consistent error handling patterns make troubleshooting more efficient
   - Clear separation between API interaction, business logic, and UI rendering

3. **User Experience Considerations**:
   - Providing visual references (showing Japanese characters alongside English) enhances learning
   - Graceful degradation with mock data ensures the app remains functional during API issues
   - Informative error messages guide users when technical problems occur
