# OPEA Mega-Services

## Overview

This is an implementation of the microservice that was demoed in the bootcamp livestream for week 3.

## How It Works

The service provides a chat completion API that mimics the OpenAI chat completion format. When a request is sent to the `/v1/chat/bootcamp` endpoint, the service processes it and returns a response with a predefined message.

### Components

- **chat.py**: The main service file that handles requests and responses
- **Dockerfile**: Defines how to build the container image
- **docker-compose.yaml**: Orchestrates the container deployment
- **bin/request**: A utility script to test the API endpoint

## How to Run

### Using Docker Compose

```bash
# Build and start the service
docker-compose up

# Or for a clean build
docker-compose up --build
```

### Using Docker Directly

```bash
# Build the image
docker build -t mega-services:bootcamp-endpoint .

# Run the container
docker run -p 8888:8888 mega-services:bootcamp-endpoint
```

### Running Locally

```bash
# Navigate to the app directory
cd app

# Run the service
python chat.py
```

## Testing the API

You can test the API using the provided request script:

```bash
# Make the script executable if needed
chmod +x bin/request

# Run the request
./bin/request
```

Or using curl directly:

```bash
curl -X POST "http://localhost:8888/v1/chat/bootcamp?request=true" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "Hello, how are you?"
      }
    ]
  }'
```

## Notes

- The service runs on port 8888
- The API requires a query parameter `request=true`
- The response format follows the OpenAI chat completion format
