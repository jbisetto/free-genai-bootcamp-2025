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
```

## Key Components

### 1. FastAPI Application (`app/main.py`)

The FastAPI application provides the HTTP interface for the vocabulary generator:

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
def get_lyrics(song: str, artist: Optional[str] = None) -> Dict[str, Any]:
    # Construct the search query
    query = f"{song} lyrics"
    if artist:
        query = f"{artist} {query}"
    
    # Search for lyrics using DuckDuckGo
    ddgs = DDGS()
    results = list(ddgs.text(query, max_results=5))
    
    # Extract and return the lyrics
    # ...
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

The tests include:
- Unit tests for each tool
- Integration tests for tool interactions
- Agent tests for the ReAct workflow

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
