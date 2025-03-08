# Tech Specs

## Goal
We want to create an AI agent using tool use and expose that as an API endpoint. For now the endpoint exists outside of our backend-flask application. It will be moved inside the application later.

## Tech Stack
- Python FastAPI
- Ollama via the Ollama Python SDK, using Mistral 7B (running locally)
- Instructor (for structured JSON output)
- duckduckgo-search to get lyrics 

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
└── Integration.md            # Documentation for backend-flask integration
└── RemoteOllama.md          # Documentation for using remote Ollama instance
```

## Agent 
### Agent Details    
We want the Agent to find song lyrics on the internet for a target song and optionally artist in a specific language and produce a list of vocabulary words that can be imported into our words database.

The words database is located at `words.db`. The table is called `words` and the sql is in `backend-flask/sql/setup/create_table_words.sql`.

The agent will perform the following tasks using our tools:
1. Get song lyrics from duckduckgo-search
2. Extract vocabulary words from the lyrics
3. Return the list of vocabulary words

The agent will not need to load the output into the database.

### Agent Tools

1. `get_lyrics` - Get song lyrics from duckduckgo-search (retrieve all lyrics, not just Japanese ones)
2. `extract_vocabulary` - Extract vocabulary words from the lyrics with the following features:
   - Limits lyrics to at most 400 words for efficient processing
   - Ensures exactly 5 vocabulary items are returned for all songs
   - Uses detailed prompts with examples to guide the model
   - Implements fallback mechanisms when insufficient items are found
3. `return_vocabulary` - Return the list of vocabulary words

Each tool will be a separate function located in the app/tools directory as specified in the project structure.

### Agent LLM

The agent will use Mistral 7B from Ollama running locally on the user's machine.
We will use Instructor (for structured JSON output).

Note: This requires Ollama to be installed and running locally with the Mistral 7B model pulled. The application will connect to the local Ollama instance at the default URL (http://localhost:11434).

A separate markdown document (`RemoteOllama.md`) will be created to outline the changes needed if Ollama is not running locally. This document will include:

1. Configuration changes to connect to a remote Ollama instance
2. Security considerations for remote connections
3. Performance implications
4. Alternative LLM providers if Ollama is not available

### Agent Prompt
Use the react prompt engineer technique for creating the agent prompt.

## API Endpoint
The endpoint should be at `/api/v1/vocab-generator`.
The request should be a GET request.
There is no authentication required.

## Future Integration
A separate markdown document (`Integration.md`) will be created to outline the steps required to integrate this standalone FastAPI endpoint with the backend-flask application. This document will include:

1. Code changes needed in the backend-flask application
2. How to import and use the agent functionality
3. Any configuration or environment variables that need to be set
4. Testing procedures to ensure the integration works correctly

The request should have the following parameters:
- `song` - The name of the song
- `artist` - The name of the artist, this is optional
  
### JSON Request Format
```json
{
  "song": "<song_name>",            
  "artist": "<artist_name>"
}
``` 
### JSON Response Format
The response should be a JSON object with the following structure that can be imported into the words database.

The majority of the fields in the response should be in Japanese, except for the `english` field.

See 'backend-flask/seed/data_verbs.json' for an example of the expected output.

```json
{
  "vocabulary": [
    {
      "kanji": "<kanji>",   
      "romaji": "<romaji>",
      "english": "<english>",
      "parts": [
        {
          "character": "<kanji>",
          "romaji": "<romaji>"
        }
      ]
    }
    // Always returns exactly 5 vocabulary items
  ]
}
```

### Error Response Format
```json
{
  "error": "<error_message>"
}
```


