# Tech Specs

## Goal
We want to create an AI agent using tool use and expose that as an API endpoint. For now the endpoint exists outside of our backend-flask application. It will be moved inside the application later.

## Tech Stack
- Python FastAPI
- Ollama via the Ollama Python SDK, using Mistral 7B (running locally)
- Instructor (for structured JSON output)
- duckduckgo-search to get lyrics
- JSON file storage for vocabulary caching

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
├── data/                     # Directory for cached data
│   └── vocab_cache/          # Directory for cached vocabulary files
├── tests/                    # Unit and integration tests
│   ├── __init__.py
│   ├── test_agent.py         # Tests for the ReAct agent
│   ├── test_extract_vocab.py # Tests for vocabulary extraction
│   ├── test_get_lyrics.py    # Tests for lyrics retrieval
│   ├── test_return_vocab.py  # Tests for vocabulary formatting
│   ├── test_vocab_cache.py   # Tests for vocabulary caching
│   └── test_integration.py   # Integration tests between tools
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
   - Makes web requests to find and extract lyrics for songs
   - Normalizes song and artist names for consistent search results
   - Automatically detects language (Japanese/English) for lyrics
   - Handles various search result formats to extract clean lyrics
   - Provides error handling for failed searches
2. `extract_vocabulary` - Extract vocabulary words from the lyrics with the following features:
   - Handles both Japanese and English songs:
     - For Japanese songs: Extracts vocabulary directly from the lyrics
     - For English songs: Identifies nouns, verbs, and adjectives, then translates them to Japanese
   - Limits lyrics to at most 400 words for efficient processing
   - Ensures exactly 5 vocabulary items are returned for all songs
   - Uses detailed prompts with examples to guide the model
   - Implements fallback mechanisms when insufficient items are found
   - Maintains consistent JSON output format regardless of input language
3. `return_vocabulary` - Return the list of vocabulary words
4. `vocab_cache` - Manage vocabulary caching
   - Stores processed vocabulary results as JSON files
   - Provides functions for saving, retrieving, and listing cached vocabulary
   - Implements cache management to limit size and remove old entries
   - Includes metadata with each cached entry for tracking and management

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
          "kanji": "<kanji>",
          "romaji": ["<romaji_part1>", "<romaji_part2>", "..."]
        }
      ]
    }
    // Can return up to 400 vocabulary items
  ]
}
```

### Error Response Format
```json
{
  "error": "<error_message>"
}
```

## Caching Strategy

The application implements an efficient vocabulary caching system to optimize performance and reduce external dependencies:

1. **Storage Mechanism**:
   - Uses JSON files in a dedicated directory
   - One file per vocabulary entry for easy management
   - Includes metadata in each cached file

2. **Cache Key Generation**:
   - Creates deterministic filenames based on song and artist
   - Handles special characters and encoding issues
   - Ensures unique cache keys for each vocabulary set

3. **Cache Management**:
   - Implements time-based expiration (default: 90 days)
   - Implements size-based limiting (default: 1000 entries)
   - Provides functions for listing and cleaning the cache
   - Implements proper file locking for concurrent access

4. **Integration with Agent**:
   - Agent checks vocabulary cache before processing
   - Short-circuits processing when cached results are available
   - Automatically saves new results to cache

### Caching Benefits

1. **Reduced External Dependencies**:
   - Eliminates need for repeated lyrics retrieval
   - Enables offline operation for previously processed songs
   - Minimizes external API calls for repeat requests

2. **Improved Performance**:
   - Significantly reduces response time for cached entries
   - Eliminates LLM processing overhead for repeat requests
   - Provides near-instantaneous responses for popular songs

3. **Resource Optimization**:
   - Reduces bandwidth usage
   - Minimizes LLM token consumption
   - Improves overall application efficiency

## Testing Strategy

The application follows a technology-agnostic testing strategy based on industry best practices:

### Core Testing Principles

1. **No External Service Dependencies**
   - All tests must run without internet connectivity
   - External services must be properly mocked
   - Tests should never make real API or web requests
   - Cache systems should be isolated during testing

2. **Component Isolation**
   - Each component should be testable in isolation
   - Dependencies should be injected to facilitate mocking
   - Tests should not depend on implementation details
   - Clear boundaries between components should be maintained

3. **Multi-level Testing Approach**
   - Unit tests for individual functions and methods
   - Integration tests for component interactions
   - End-to-end tests for complete workflows
   - Performance tests for critical paths

4. **Test Data Management**
   - Test data should be isolated from production data
   - Tests should clean up after themselves
   - Each test should start with a known state
   - Test data should be representative of real-world scenarios

### Mocking Best Practices

1. **External API Mocking**
   - Web search APIs should be mocked at the request level
   - Mock responses should mirror real API responses
   - Error conditions should be simulated
   - Network failures should be testable

2. **LLM Response Mocking**
   - LLM responses should be deterministic during tests
   - Various response formats should be tested
   - Error handling for malformed responses should be verified
   - Edge cases in response parsing should be covered

3. **Component Interaction Mocking**
   - Mock interactions between components
   - Verify correct parameters are passed between components
   - Test error propagation between components
   - Ensure components are loosely coupled

4. **Caching System Mocking**
   - Isolate tests from actual cache storage
   - Test both cache hits and misses
   - Verify cache key generation logic
   - Test cache management functions

### Testing Implementation

1. **Test Setup and Teardown**
   - Properly initialize test environment
   - Clean up all test artifacts after tests
   - Use try/finally blocks to ensure cleanup
   - Isolate tests from each other

2. **Assertion Strategies**
   - Use specific, targeted assertions
   - Test both positive and negative cases
   - Verify side effects when appropriate
   - Include helpful error messages

3. **Test Organization**
   - Group related tests together
   - Use descriptive test names
   - Follow consistent naming conventions
   - Separate unit and integration tests

4. **Test Coverage Goals**
   - Aim for high coverage of core functionality
   - Prioritize critical paths and error handling
   - Test edge cases and boundary conditions
   - Verify performance characteristics

### Quality Assurance Process

Beyond automated testing, the QA process includes:

1. Code reviews with attention to testability
2. Regular test coverage analysis
3. Continuous integration to run tests automatically
4. Documentation of testing approach and results
3. Periodic test suite maintenance
4. Documentation of testing approach and coverage

Refer to the project's QA documentation for specific implementation details and current test coverage metrics.

