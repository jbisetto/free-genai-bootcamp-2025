# Japanese Song Vocabulary Generator

This application uses AI to find Japanese song lyrics and extract vocabulary words for language learning.

## Features

- Search for song lyrics using DuckDuckGo
- Extract Japanese vocabulary from lyrics using Mistral 7B
- Format vocabulary with kanji, romaji, English translation, and character breakdown
- Expose functionality through a FastAPI endpoint

## Requirements

- Python 3.8+
- Ollama installed locally with Mistral 7B model
- Internet connection for lyrics search

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

3. Use the `/api/v1/vocab-generator` endpoint to generate vocabulary:
   ```
   GET /api/v1/vocab-generator?song=Lemon&artist=Kenshi%20Yonezu
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
│       └── return_vocab.py   # Tool to format vocabulary
├── tests/                    # Unit tests
│   ├── __init__.py
│   ├── test_agent.py
│   └── test_tools.py
├── requirements.txt          # Project dependencies
├── .env.example              # Example environment variables
├── README.md                 # Project documentation
└── Tech-Specs.md             # Technical specifications
```

## Future Integration

See `Integration.md` for details on how to integrate this API with the backend-flask application.

## Using Remote Ollama

See `RemoteOllama.md` for details on how to use a remote Ollama instance instead of a local one.
