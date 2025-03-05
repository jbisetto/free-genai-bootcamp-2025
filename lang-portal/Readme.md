## Install

```sh
pip install -r requirements.txt
```

## Setup DB

```
invoke init-db
```

## Run

```sh
python app.py
```

## Week 2 Changes

### Backend Changes
- Updated the Flask server port from 5000 to 5001 to avoid conflicts with other services
- Added HTTP/1.1 protocol support via `WSGIRequestHandler.protocol_version = "HTTP/1.1"`
- Enhanced logging configuration for better debugging
- Implemented a health endpoint for system status monitoring

### API Improvements
- Improved CORS configuration for cross-origin requests
- Enhanced error handling for API endpoints
- Added better request and response logging

### Configuration
- Maintained the SQLite database configuration (words.db)
- Preserved the existing route structure for words, groups, study sessions, and dashboard