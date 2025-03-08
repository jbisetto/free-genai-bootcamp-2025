# Integration with Backend-Flask Application

This document outlines the steps required to integrate the Japanese Song Vocabulary Generator API with the backend-flask application.

## Overview

Currently, the vocabulary generator is implemented as a standalone FastAPI application. To integrate it with the existing backend-flask application, we need to:

1. Import the agent functionality into the Flask application
2. Create a new Flask route that uses the agent
3. Ensure all dependencies are available in the Flask environment

## Integration Steps

### 1. Copy Required Files

Copy the following directories and files to the backend-flask application:

```
song-vocabulary/app/agent/ -> backend-flask/app/agent/
song-vocabulary/app/tools/ -> backend-flask/app/tools/
```

### 2. Install Dependencies

Add the following dependencies to the Flask application's requirements file:

```
ollama==0.1.5
instructor==0.4.5
duckduckgo-search==3.9.6
```

### 3. Create a Flask Route

Add a new route to the Flask application:

```python
from flask import Blueprint, request, jsonify
from app.agent.agent import run_agent

# Create a blueprint for vocabulary routes
vocab_bp = Blueprint('vocabulary', __name__, url_prefix='/api/v1')

@vocab_bp.route('/vocab-generator', methods=['GET'])
def vocab_generator():
    """
    Generate vocabulary from song lyrics.
    """
    # Get query parameters
    song = request.args.get('song')
    artist = request.args.get('artist')
    
    # Validate input
    if not song:
        return jsonify({"error": "Song parameter is required"}), 400
    
    try:
        # Run the agent to generate vocabulary
        result = run_agent(song, artist)
        
        # Check if there's an error
        if "error" in result:
            return jsonify({"error": result["error"]}), 400
        
        return jsonify(result)
    
    except Exception as e:
        # Return a proper error response
        return jsonify({"error": str(e)}), 500
```

### 4. Register the Blueprint

In the Flask application's `__init__.py` or main file, register the blueprint:

```python
from app.routes.vocabulary import vocab_bp

# Register blueprints
app.register_blueprint(vocab_bp)
```

### 5. Environment Configuration

Ensure the Flask application has access to the required environment variables:

```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:7b
```

### 6. Testing the Integration

After integrating the code, test the endpoint to ensure it works correctly:

1. Make sure Ollama is running with the Mistral 7B model
2. Start the Flask application
3. Send a test request to the endpoint:
   ```
   GET /api/v1/vocab-generator?song=Lemon&artist=Kenshi%20Yonezu
   ```
4. Verify that the response contains the expected vocabulary items

## Potential Issues and Solutions

### 1. Dependency Conflicts

If there are conflicts between the dependencies of the Flask application and the vocabulary generator, you may need to:
- Use virtual environments
- Update dependency versions to be compatible
- Refactor code to remove conflicting dependencies

### 2. Performance Considerations

The vocabulary generation process can be resource-intensive. Consider:
- Adding caching for frequently requested songs
- Implementing a job queue for asynchronous processing
- Monitoring server resources during peak usage

### 3. Error Handling

Ensure consistent error handling between the Flask application and the vocabulary generator:
- Use the same error response format
- Add appropriate logging
- Implement retry logic for transient errors

## Conclusion

By following these steps, you can successfully integrate the Japanese Song Vocabulary Generator into the backend-flask application, providing a seamless experience for users while maintaining the existing application structure.
