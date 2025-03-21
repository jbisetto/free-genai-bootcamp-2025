# Song Vocabulary App: Developer Onboarding Guide

## Overview

The Song Vocabulary App is an AI-powered application that extracts Japanese vocabulary from song lyrics. It uses a ReAct (Reasoning + Acting) agent pattern with Mistral 7B to create a tool-using AI system that can:

1. Search for and retrieve song lyrics
2. Extract relevant Japanese vocabulary from those lyrics
3. Format the vocabulary into a structured JSON response

This document will help you understand the architecture, components, and workflow of the application.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────────┐
│                 │     │                 │     │                         │
│  FastAPI        │────▶│  ReAct Agent    │────▶│  External Services      │
│  Endpoints      │     │  (Mistral 7B)   │     │  - DuckDuckGo Search   │
│                 │     │                 │     │  - Ollama API           │
└─────────────────┘     └─────────────────┘     └─────────────────────────┘
                              │
                              │
                              ▼
                        ┌─────────────────┐
                        │                 │
                        │  Agent Tools    │
                        │                 │
                        └─────────────────┘
                              │
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
    ┌─────────────────┐┌─────────────────┐┌─────────────────┐
    │                 ││                 ││                 │
    │  get_lyrics     ││ extract_vocab   ││ return_vocab    │
    │  Tool           ││ Tool            ││ Tool            │
    │                 ││                 ││                 │
    └─────────────────┘└─────────────────┘└─────────────────┘
             │
             ▼
    ┌─────────────────┐
    │                 │
    │  JSON           │
    │  Vocabulary     │
    │  Cache          │
    │                 │
    └─────────────────┘
```

## Key Components

### 1. FastAPI Application (`app/main.py`)

The FastAPI application provides the HTTP interface for the vocabulary generator with multiple endpoints:

#### API Endpoints

1. **Vocabulary Generator Endpoint**

```python
@app.get("/api/v1/vocab-generator")
async def vocab_generator(
    song: str = Query(..., description="The name of the song"),
    artist: Optional[str] = Query(None, description="The name of the artist (optional)")
):
    # Run the agent to generate vocabulary
    result = run_agent(song, artist)
    
    # Return the result
    return result
```

2. **Cache Listing Endpoint**

```python
@app.get("/api/v1/cache", response_class=PlainTextResponse)
async def cache_list():
    # Get the list of cached songs
    result = list_cached_songs()
    
    # Format as a text-based table
    # ... (table formatting code)
    
    return table
```

This endpoint returns a formatted text-based table of all songs and artists currently in the vocabulary cache, along with their cache timestamps and last accessed times. It's designed for easy viewing directly in a browser or console, making it ideal for quick debugging and monitoring of the vocabulary caching system.

**Example Output:**

```
┌─────────────────────────────┬─────────────────────────────┬─────────────────────────────┬─────────────────────────────┐
│ Song                        │ Artist                      │ Cached At                   │ Last Accessed               │
├─────────────────────────────┼─────────────────────────────┼─────────────────────────────┼─────────────────────────────┤
│ lemon                       │ kenshi yonezu               │ 2025-03-07 20:45:12         │ 2025-03-08 00:51:23         │
│ gurenge                     │ lisa                        │ 2025-03-06 15:30:45         │ 2025-03-07 10:22:18         │
└─────────────────────────────┴─────────────────────────────┴─────────────────────────────┴─────────────────────────────┘

Total cached songs: 2
```

#### API Documentation

The API is fully documented using OpenAPI and can be accessed through:

- **Swagger UI**: Available at `/docs` endpoint
- **ReDoc**: Available at `/redoc` endpoint

Both interfaces provide interactive documentation where you can explore the API endpoints, see request/response schemas, and even test the API directly from the browser.

### 2. ReAct Agent (`app/agent/agent.py`)

The agent implements the ReAct pattern (Reasoning + Acting) to:
- Parse user requests
- Decide which tools to use
- Execute tools
- Process observations
- Generate a final answer

```python
def run_agent(song: str, artist: Optional[str] = None) -> Dict[str, Any]:
    # Generate the initial prompt
    prompt = get_prompt(song, artist)
    
    # Initialize conversation history
    conversation = [{"role": "user", "content": prompt}]
    
    # Initialize state
    max_iterations = 10
    iterations = 0
    
    # Run the agent loop
    while iterations < max_iterations:
        # Get response from LLM
        response = client.chat(model=MODEL_NAME, messages=conversation)
        llm_response = response["message"]["content"]
        
        # Parse the response
        thought, action, action_input, final_answer = parse_llm_response(llm_response)
        
        # If we have a final answer, return it
        if final_answer:
            return final_answer
            
        # If we have an action, execute it
        if action and action in TOOLS:
            # Execute the tool
            tool_result = TOOLS[action](**json.loads(action_input))
            
            # Add the observation to the conversation
            conversation.append({"role": "assistant", "content": llm_response})
            conversation.append({"role": "user", "content": f"Observation: {json.dumps(tool_result)}"})
        
        iterations += 1
    
    # If we reach max iterations, return an error
    return {"error": "Max iterations reached without finding an answer"}
```

### 3. Tools

The agent uses three specialized tools:

#### a. Get Lyrics Tool (`app/tools/get_lyrics.py`)

Searches for and retrieves lyrics for a given song and artist using DuckDuckGo search:

```python
def get_lyrics(song: str, artist: Optional[str] = None, use_mock: bool = False) -> Dict[str, Any]:
    # First check if lyrics are in the cache
    cached_result = get_cached_lyrics(song, artist)
    if cached_result:
        logger.info(f"Cache hit for '{song}' by '{artist}'")
        return cached_result
    
    logger.info(f"Cache miss for '{song}' by '{artist}', fetching from web")
    
    # If mock mode is enabled, return mock lyrics
    if use_mock:
        logger.info(f"Cache miss for '{song}' by '{artist}', using mock data")
        lyrics = f"Sample lyrics for {song} by {artist}"
        metadata = {"source": "mock", "is_mock": True}
        
        # Cache the mock lyrics
        cache_stats = cache_lyrics(song, artist, lyrics, metadata)
        logger.info(f"Updated cache entry for '{song}' by '{artist}'")
        
        return {
            "success": True,
            "lyrics": lyrics,
            "source": "mock",
            "is_mock": True,
            "cache_stats": cache_stats
        }
    
    # Construct the search query
    query = f"{song} lyrics"
    if artist:
        query = f"{artist} {query}"
    
    # Search for lyrics using DuckDuckGo
    try:
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=5))
        
        # Process results and extract lyrics
        # ...
        
        # Cache the lyrics
        cache_stats = cache_lyrics(song, artist, lyrics, metadata)
        logger.info(f"Updated cache entry for '{song}' by '{artist}'")
        
        return {
            "success": True,
            "lyrics": lyrics,
            "source": source,
            "cache_stats": cache_stats
        }
    except Exception as e:
        logger.error(f"Error fetching lyrics: {e}")
        return {"success": False, "error": str(e)}
```

#### b. Extract Vocabulary Tool (`app/tools/extract_vocab.py`)

Uses the Mistral 7B model with Instructor to extract Japanese vocabulary from lyrics. The tool handles both Japanese and English songs:

```python
def extract_vocabulary(lyrics: str) -> Dict[str, Any]:
    # Limit lyrics to 400 words
    words = lyrics.split()
    if len(words) > 400:
        lyrics = " ".join(words[:400])
    
    # Use instructor to create structured output
    instructor_client = instructor.patch(client)
    
    # Define the schema for vocabulary items
    class VocabularyItem(instructor.dsl.InstructorDSLModel):
        kanji: str
        romaji: str
        english: str
        parts: List[Part]
    
    # Extract vocabulary using the LLM with language-specific instructions
    # For Japanese lyrics: Extract vocabulary directly
    # For English lyrics: Translate nouns, verbs, and adjectives to Japanese
    # ...
```

**Language Handling**:
- **Japanese Songs**: Vocabulary is extracted directly from the lyrics
- **English Songs**: Nouns, verbs, and adjectives are identified and translated to Japanese

#### c. Return Vocabulary Tool (`app/tools/return_vocab.py`)

Formats the vocabulary data into the required JSON structure:

```python
def return_vocabulary(vocabulary_data: Dict[str, Any]) -> Dict[str, Any]:
    if not vocabulary_data.get("success", False):
        return {
            "error": vocabulary_data.get("error", "Unknown error occurred")
        }
    
    vocabulary = vocabulary_data.get("vocabulary", [])
    
    return {
        "vocabulary": vocabulary
    }
```

## Vocabulary Caching System and Mock Mode

The application includes a vocabulary caching system using JSON file storage to improve performance and reduce LLM processing overhead.

### JSON-based Vocabulary Caching

The vocabulary caching system stores processed vocabulary in JSON files with the following features:

1. **Automatic Cache Creation**: The cache directory is created automatically if it doesn't exist
2. **Structured Storage**: Vocabulary data is stored in JSON format for easy retrieval
3. **Metadata Storage**: Additional metadata like song, artist, and timestamp are stored alongside vocabulary
4. **Cache Management**: A function to clean up old or excess entries is provided

```python
def get_cached_vocab(song: str, artist: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve vocabulary from the cache if available."""
    # Ensure cache directory exists
    os.makedirs(VOCAB_CACHE_DIR, exist_ok=True)
    
    # Generate cache key based on song and artist
    cache_key = f"{song}_{artist if artist else 'unknown'}".lower()
    cache_key = re.sub(r'[^a-z0-9_]', '_', cache_key)
    cache_file = os.path.join(VOCAB_CACHE_DIR, f"{cache_key}.json")
    
    # Check if cache file exists
    if not os.path.exists(cache_file):
        return None
    
    # Read and parse the cache file
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            
        # Extract cache metadata
        metadata = cache_data.get("_cache_metadata", {})
        
        # Update the last accessed timestamp
        # This is done in a separate function in the actual implementation
        
        # Remove metadata from the returned result
        result = cache_data.copy()
        if "_cache_metadata" in result:
            del result["_cache_metadata"]
        
        # Return the vocabulary data with cache information
        return result
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        logger.error(f"Error reading vocabulary cache: {e}")
        return None
```

### Mock Mode

The application includes a mock mode for testing and development purposes. This allows you to retrieve lyrics without making actual API calls.

#### Using Mock Mode

```python
# Example 1: Using mock mode in the get_lyrics function
result = get_lyrics("Lemon", "Kenshi Yonezu", use_mock=True)
# Returns mock lyrics with is_mock=True in the metadata

# Example 2: Testing with mock mode
def test_get_lyrics_with_mock():
    result = get_lyrics("Test Song", "Test Artist", use_mock=True)
    assert result["success"] == True
    assert result["is_mock"] == True
    assert "Sample lyrics" in result["lyrics"]
```

#### Benefits of Mock Mode

1. **Testing Without External Dependencies**: Run tests without internet access
2. **Consistent Test Results**: Tests are not affected by external API changes
3. **Faster Test Execution**: No need to wait for network requests
4. **Offline Development**: Develop and test without internet connectivity

## The ReAct Pattern

The application uses the ReAct (Reasoning + Acting) pattern, which follows this cycle:

```
┌─────────────┐
│             │
│  Thought    │◄───────────────┐
│             │                │
└──────┬──────┘                │
       │                       │
       ▼                       │
┌─────────────┐         ┌─────────────┐
│             │         │             │
│  Action     │────────▶│ Observation │
│             │         │             │
└─────────────┘         └─────────────┘
```

1. **Thought**: The agent reasons about what to do next
2. **Action**: The agent selects and executes a tool
3. **Observation**: The agent processes the result of the tool
4. **Repeat**: The cycle continues until a final answer is reached

### Example ReAct Trace

```
Thought: I need to find lyrics for the song "Lemon" by Kenshi Yonezu.
Action: get_lyrics
Action Input: {"song": "Lemon", "artist": "Kenshi Yonezu"}
Observation: {"success": true, "lyrics": "夢ならばどれほどよかったでしょう...", "metadata": {...}}

Thought: Now I have the lyrics, I need to extract vocabulary from them.
Action: extract_vocabulary
Action Input: {"lyrics": "夢ならばどれほどよかったでしょう..."}
Observation: {"success": true, "vocabulary": [{...}, {...}, ...]}

Thought: I have the vocabulary items. I need to format them for the final response.
Action: return_vocabulary
Action Input: {"vocabulary_data": {"success": true, "vocabulary": [{...}, ...]}}
Observation: {"vocabulary": [{...}, {...}, ...]}

Thought: I now have the formatted vocabulary. I can provide the final answer.
Final Answer: {"vocabulary": [{...}, {...}, ...]}
```

## JSON Response Format

The application returns vocabulary in the same consistent format regardless of whether the input is a Japanese or English song:

### Example: Japanese Song Response

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
    {
      "kanji": "レモン",
      "romaji": "remon",
      "english": "lemon",
      "parts": [
        {
          "kanji": "レ",
          "romaji": ["re"]
        },
        {
          "kanji": "モ",
          "romaji": ["mo"]
        },
        {
          "kanji": "ン",
          "romaji": ["n"]
        }
      ]
    }
    // More vocabulary items...
  ]
}
```

### Example: English Song Response

```json
{
  "vocabulary": [
    {
      "kanji": "こんにちは",
      "romaji": "konnichiwa",
      "english": "hello",
      "parts": [
        {
          "kanji": "こん",
          "romaji": ["kon"]
        },
        {
          "kanji": "にち",
          "romaji": ["nichi"]
        },
        {
          "kanji": "は",
          "romaji": ["wa"]
        }
      ]
    },
    {
      "kanji": "愛",
      "romaji": "ai",
      "english": "love",
      "parts": [
        {
          "kanji": "愛",
          "romaji": ["ai"]
        }
      ]
    }
    // More vocabulary items...
  ]
}
```

## Error Handling

The application implements comprehensive error handling:

1. **Tool-level errors**: Each tool returns a success/error status
2. **Agent-level errors**: The agent handles LLM failures and tool errors
3. **API-level errors**: FastAPI exception handlers provide clean error responses

Example error response:

```json
{
  "error": "No lyrics found for the given song and artist"
}
```

## Running the Application

1. **Environment Setup**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start the Server**:
   ```bash
   python -m app.main
   ```

3. **Access the API**:
   - Swagger UI: http://localhost:8000/docs
   - API Endpoint: http://localhost:8000/api/v1/vocab-generator?song=Lemon&artist=Kenshi%20Yonezu

## Testing

Run the test suite:

```bash
python -m unittest discover -s tests
```

## Testing Framework

The Song Vocabulary App uses a comprehensive testing approach that includes unit tests, integration tests, and performance tests. This section will help you understand how to run tests, how our mocking strategy works, and how to add new tests.

### Test Structure

Tests are organized into the following categories:

1. **Unit Tests**: Located in `tests/` directory with filenames matching `test_*.py`
   - `test_get_lyrics.py`: Tests for the lyrics retrieval and caching functionality
   - `test_extract_vocab.py`: Tests for the vocabulary extraction functionality
   - `test_agent.py`: Tests for the ReAct agent functionality

2. **Integration Tests**: Located in `tests/` directory
   - `test_caching_integration.py`: Tests for the interaction between caching and other components

### Running Tests

To run all tests:

```bash
python -m unittest discover
```

To run a specific test file:

```bash
python -m unittest tests/test_caching_integration.py
```

To run a specific test with verbose output:

```bash
python -m unittest tests/test_caching_integration.py -v
```

### Mocking Strategy

We use Python's `unittest.mock` library extensively to isolate components during testing. Here's how our mocking strategy works:

#### 1. External API Mocking

We mock external APIs to avoid making real network requests during testing:

```python
# Example: Mocking DuckDuckGo search
with patch('app.tools.get_lyrics.DDGS') as mock_ddgs:
    mock_instance = MagicMock()
    mock_ddgs.return_value = mock_instance
    mock_instance.text.return_value = [{'body': 'Mock lyrics', 'href': 'https://example.com'}]
    
    # Test code that uses DDGS
    result = get_lyrics("Test Song", "Test Artist")
```

#### 2. Component Interaction Mocking

We mock interactions between components to test them in isolation:

```python
# Example: Mocking extract_vocabulary when testing the workflow
with patch('app.tools.extract_vocab.extract_vocabulary') as mock_extract:
    mock_extract.return_value = {
        'success': True,
        'vocabulary': [
            {'word': 'テスト', 'reading': 'tesuto', 'meaning': 'test'}
        ]
    }
    
    # Test code that uses extract_vocabulary
    result = process_lyrics("Some lyrics")
```

#### 3. LLM Response Mocking

We mock LLM responses when testing the agent:

```python
# Example: Mocking LLM responses
with patch('app.agent.agent.client') as mock_client:
    mock_response = MagicMock()
    mock_response.response = "Thought: I need to get lyrics\nAction: get_lyrics\nAction Input: {\"song\": \"Test\"}\n..."
    mock_client.completions.create.return_value = mock_response
    
    # Test code that uses the LLM
    result = run_agent("What are the lyrics to Test?")
```

#### 4. Caching System Testing

For testing the vocabulary caching system, we use a combination of real and mock components:

1. **Real JSON Files**: We use real JSON files but with a temporary directory path for testing
2. **Mock Network Failures**: We simulate network failures by raising exceptions from mocked components
3. **Performance Testing**: We compare the performance of cached vs. non-cached vocabulary retrieval

```python
# Example: Setting up a test directory for vocabulary caching
def setUp(self):
    # Create a temporary directory for the vocabulary cache
    self.test_cache_dir = tempfile.mkdtemp()
    
    # Set the environment variable to use the test cache directory
    os.environ["VOCAB_CACHE_DIR"] = self.test_cache_dir
```

### Test Coverage

Our tests cover the following key areas:

1. **Lyrics Retrieval**:
   - Successful retrieval of lyrics
   - Error handling for network failures
   - Metadata handling

2. **Vocabulary Extraction**:
   - Extraction of vocabulary from Japanese lyrics
   - Handling of different input formats
   - Error handling for invalid inputs

3. **Agent Functionality**:
   - Correct parsing of LLM responses
   - Proper tool selection and execution
   - Error handling and recovery

4. **Integration Testing**:
   - End-to-end workflow from lyrics retrieval to vocabulary extraction
   - Offline mode operation
   - Performance comparison

### Adding New Tests

When adding new tests, follow these guidelines:

1. **Use Descriptive Test Names**: Test method names should clearly describe what they're testing
2. **Isolate Dependencies**: Use mocking to isolate the component being tested
3. **Test Edge Cases**: Include tests for error conditions and edge cases
4. **Document Test Purpose**: Include docstrings explaining what each test is verifying
5. **Keep Tests Independent**: Each test should be able to run independently

### Recent Test Improvements

As of March 2025, we've made several improvements to the testing framework:

1. **Eliminated Real Web Requests in All Tests**:
   - Updated all tests to properly mock web requests instead of making real API calls
   - Added cleanup methods to ensure test data is removed from the cache before and after tests
   - Implemented try/finally blocks to ensure cleanup happens even if tests fail
   - Added proper error handling in cleanup methods to prevent test failures due to cleanup issues

2. **Enhanced Integration Tests**:
   - Fixed `test_lyrics_to_vocabulary_workflow` to correctly verify the extract_vocabulary mock is called as expected
   - Enhanced `test_offline_mode_fallback` to use unique song names with timestamps
   - Improved simulation of network unavailability in offline tests
   - Added proper cleanup of test data to ensure test isolation

3. **Better Test Documentation and Clarity**:
   - Added detailed comments explaining test purposes and mocking strategies
   - Documented why certain tests are skipped and the challenges involved
   - Added explicit comments in tests to clarify that `use_mock=False` is still using mocked web requests via unittest.mock
   - Improved logging to show when test data is being cleaned up

## Common Development Tasks

### Adding a New Tool

1. Create a new tool file in `app/tools/`
2. Implement the tool function
3. Add the tool to the `TOOLS` dictionary in `app/agent/agent.py`
4. Update the prompt in `app/agent/prompt.py` to include the new tool
5. Add tests for the new tool

### Modifying the Agent Behavior

1. Update the prompt template in `app/agent/prompt.py`
2. Modify the `run_agent` function in `app/agent/agent.py`
3. Test the changes with different inputs

### Adding a New API Endpoint

1. Define the new endpoint in `app/main.py`
2. Implement the necessary logic
3. Add documentation using FastAPI's built-in docstrings
4. Add tests for the new endpoint

### Modifying Language Handling

1. Update the prompt in `app/tools/extract_vocab.py` to adjust language-specific instructions
2. Ensure the Pydantic models match the expected output structure
3. Test with both Japanese and English songs to verify consistent behavior
4. Update tests to cover the language-specific functionality

## Debugging Tips

1. **Enable Verbose Logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Inspect LLM Responses**:
   - Add print statements in `parse_llm_response` to see raw responses
   - Check the conversation history in `run_agent`

3. **Test Tools Independently**:
   - Each tool has a `__main__` block for standalone testing
   - Example: `python -m app.tools.get_lyrics`

## Next Steps and Improvements

1. Add support for additional languages
2. Implement caching for lyrics and LLM responses
3. Add more sophisticated error recovery mechanisms
4. Implement user feedback and correction mechanisms
5. Expand the vocabulary extraction with more detailed information

---

This onboarding document should help you get started with the Song Vocabulary App. If you have any questions, refer to the source code or reach out to the team.
