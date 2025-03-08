# Using a Remote Ollama Instance

This document outlines the changes needed to use a remote Ollama instance instead of a local one for the Japanese Song Vocabulary Generator.

## Overview

By default, the application is configured to use a local Ollama instance running on the default URL (`http://localhost:11434`). However, there may be scenarios where you want to use a remote Ollama instance, such as:

- Running the application on a server without enough resources for local LLM inference
- Using a shared Ollama instance across multiple applications
- Leveraging more powerful hardware for inference

## Configuration Changes

### 1. Environment Variables

Update the `.env` file to point to the remote Ollama instance:

```
OLLAMA_HOST=http://your-remote-ollama-server:11434
```

### 2. Code Changes

Modify the Ollama client initialization in the following files:

1. `app/agent/agent.py`:
```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Ollama host from environment variable
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Initialize the Ollama client
client = Client(host=ollama_host)
```

2. `app/tools/extract_vocab.py`:
```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Ollama host from environment variable
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Initialize the Ollama client
client = Client(host=ollama_host)
```

### 3. Docker Configuration (Optional)

If you're using Docker, update your `Dockerfile` and `docker-compose.yml` to include the environment variable:

```yaml
# docker-compose.yml
services:
  app:
    environment:
      - OLLAMA_HOST=http://ollama:11434
  
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
```

## Security Considerations

When using a remote Ollama instance, consider the following security measures:

1. **Network Security**:
   - Use a secure connection (HTTPS) if possible
   - Implement IP whitelisting to restrict access
   - Set up a VPN or SSH tunnel for secure communication

2. **Authentication**:
   - Implement API key authentication for the Ollama server
   - Use environment variables or a secrets manager to store credentials

3. **Data Privacy**:
   - Ensure that sensitive data is not sent to the remote server
   - Consider data encryption for sensitive information

## Performance Implications

Using a remote Ollama instance can have performance implications:

1. **Latency**:
   - Network latency can increase response times
   - Consider implementing caching for frequently used responses

2. **Bandwidth**:
   - Large requests and responses can consume significant bandwidth
   - Optimize the size of data being sent to and from the remote server

3. **Resource Sharing**:
   - A shared Ollama instance may experience contention
   - Implement queuing or rate limiting to manage load

## Alternative LLM Providers

If Ollama is not available or suitable for your needs, consider these alternatives:

### 1. OpenAI API

```python
import openai
from instructor import patch

# Initialize the OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
instructor_client = patch(client)

# Use GPT-4 or GPT-3.5-Turbo
response = instructor_client.chat.completions.create(
    model="gpt-4",
    response_model=VocabularyResponse,
    messages=[
        {"role": "system", "content": "You are a helpful Japanese language teaching assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.1
)
```

### 2. Hugging Face Inference API

```python
import requests
import os
import json

def extract_vocabulary_hf(lyrics: str) -> Dict[str, Any]:
    API_URL = f"https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {os.getenv('HF_API_TOKEN')}"}
    
    # Create the prompt
    prompt = f"""
    You are a Japanese language expert. Extract important vocabulary words from the following Japanese song lyrics.
    ...
    """
    
    # Make the API request
    response = requests.post(
        API_URL,
        headers=headers,
        json={"inputs": prompt}
    )
    
    # Process the response
    # ...
```

### 3. Self-hosted Alternatives

- **LiteLLM**: A lightweight library that provides a unified interface to various LLM providers
- **LocalAI**: A self-hosted alternative to OpenAI API that can run various models
- **vLLM**: A high-throughput and memory-efficient inference engine for LLMs

## Conclusion

By following the steps outlined in this document, you can configure the Japanese Song Vocabulary Generator to use a remote Ollama instance or alternative LLM providers, allowing for more flexibility in deployment and resource management.
