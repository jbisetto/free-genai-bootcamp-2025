# Japanese Song Vocabulary Generator

This application uses AI to find song lyrics and extract Japanese vocabulary words for language learning. It supports both Japanese and English songs.

## Features

- Search for song lyrics using DuckDuckGo
- Efficient vocabulary caching system:
  - JSON file-based storage to reduce LLM processing overhead
  - Significantly improves response times for previously processed songs
- Extract Japanese vocabulary from lyrics using Mistral 7B
- Support for both Japanese and English songs:
  - Japanese songs: Extract vocabulary directly from lyrics
  - English songs: Identify nouns, verbs, and adjectives and translate them to Japanese
- Format vocabulary with kanji, romaji, English translation, and character breakdown
- Expose functionality through a FastAPI endpoint
- Cache management utilities for both lyrics and vocabulary caches

## Requirements

- Python 3.8+
- Ollama installed locally with Mistral 7B model
- Internet connection for lyrics search (first-time only for each song)
- SQLite (included in Python standard library)

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd song-vocabulary
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Make sure Ollama is installed and the Mistral 7B model is pulled:
   ```
   ollama pull mistral:7b
   ```

4. Create a `.env` file based on `.env.example`:
   ```
   cp .env.example .env
   ```

## Usage

1. Start the API server:
   ```
   python -m app.main
   ```

2. Access the API at http://localhost:8000

3. Use the API endpoints:
   - Vocabulary Generator: `/api/v1/vocab-generator?song=SONG_NAME&artist=ARTIST_NAME`
   - Cache Listing: `/api/v1/cache` (view all cached songs and artists)

4. Access API documentation:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
   ```
   # Japanese song example
   GET /api/v1/vocab-generator?song=Lemon&artist=Kenshi%20Yonezu
   
   # English song example
   GET /api/v1/vocab-generator?song=Hello&artist=Adele
   ```

4. The API will return a JSON response with vocabulary items:
   ```json
   {
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
       ...
     ]
   }
   ```

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Additional Endpoints

- **Cache Management**: `/api/v1/cache/clean` - Clean up old cache entries
- **Vocabulary Cache Listing**: `/api/v1/vocab-cache` - List all cached vocabulary entries

## Performance Optimization

The application implements several performance optimizations:

1. **Lyrics Caching**: Lyrics are cached in a SQLite database to reduce external API calls
   - Subsequent requests for the same song use cached data
   - Cached lyrics are compressed using zlib to reduce storage requirements
   - Typical compression ratios range from 1.4x to 2.5x depending on lyrics content

2. **Vocabulary Caching**: Processed vocabulary is cached as JSON files to reduce LLM processing overhead
   - Vocabulary is stored with metadata including song, artist, and timestamp
   - Cached vocabulary is retrieved based on song and artist name
   - Significant reduction in response time by eliminating LLM processing for repeat requests

3. **Cache Management**:
   - Automatic cleanup of old cache entries (configurable, default: 90 days)
   - Size-based cache limiting (configurable, default: 1000 entries)
   - LRU (Least Recently Used) eviction policy for excess entries
   - Separate management for both lyrics and vocabulary caches

## Testing

The application includes comprehensive test coverage for all components:

```
python -m unittest discover -s tests
```

The test suite includes:
- Unit tests for all tools (lyrics retrieval, vocabulary extraction, vocabulary formatting)
- Integration tests between tools
- Agent tests for the ReAct agent workflow
- Mock mode for testing caching without external API dependencies

For a detailed analysis of test coverage and quality assurance assessment, see the [QA Testing Summary](tests/QA_TESTING_SUMMARY.md).

## Project Structure

```
song-vocabulary/
├── app/
│   ├── __init__.py           # Makes app a proper package
│   ├── main.py               # FastAPI application and endpoint definition
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent.py          # ReAct agent implementation
│   │   └── prompt.py         # ReAct prompt template
│   └── tools/
│       ├── __init__.py
│       ├── get_lyrics.py     # Tool to fetch lyrics
│       ├── extract_vocab.py  # Tool to extract vocabulary
│       ├── return_vocab.py   # Tool to format vocabulary
│       └── vocab_cache.py    # Tool for vocabulary caching
├── tests/                    # Unit and integration tests
│   ├── __init__.py
│   ├── test_agent.py         # Tests for the ReAct agent
│   ├── test_extract_vocab.py # Tests for vocabulary extraction
│   ├── test_get_lyrics.py    # Tests for lyrics retrieval
│   ├── test_integration.py   # Integration tests between tools
│   ├── test_return_vocab.py  # Tests for vocabulary formatting
│   ├── test_vocab_cache.py   # Tests for vocabulary caching
│   ├── test_vocab_cache_integration.py # Integration tests for vocabulary caching
│   ├── test_caching_integration.py # Integration tests for both caching systems
│   └── QA_TESTING_SUMMARY.md # QA assessment and test coverage report
├── requirements.txt          # Project dependencies
├── .env.example              # Example environment variables
├── README.md                 # Project documentation
└── Tech-Specs.md             # Technical specifications
```

## Future Integration

See `Integration.md` for details on how to integrate this API with the backend-flask application.

## Using Remote Ollama

See `RemoteOllama.md` for details on how to use a remote Ollama instance instead of a local one.
