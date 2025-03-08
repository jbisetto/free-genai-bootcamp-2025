# Example API Requests

This document contains example requests to the Japanese Song Vocabulary Generator API.

## Using curl

### Basic Request for "Idol" by YOASOBI

```bash
curl -X GET "http://localhost:8000/api/v1/vocab-generator?song=Idol&artist=YOASOBI" \
  -H "Accept: application/json"
```

### Other Popular Japanese Songs

#### "Lemon" by Kenshi Yonezu

```bash
curl -X GET "http://localhost:8000/api/v1/vocab-generator?song=Lemon&artist=Kenshi%20Yonezu" \
  -H "Accept: application/json"
```

#### "Gurenge" by LiSA (Demon Slayer Theme)

```bash
curl -X GET "http://localhost:8000/api/v1/vocab-generator?song=Gurenge&artist=LiSA" \
  -H "Accept: application/json"
```

#### "Shinzou wo Sasageyo" by Linked Horizon (Attack on Titan Theme)

```bash
curl -X GET "http://localhost:8000/api/v1/vocab-generator?song=Shinzou%20wo%20Sasageyo&artist=Linked%20Horizon" \
  -H "Accept: application/json"
```

## Using Python Requests

### Example Python Code

```python
import requests
import json

# API endpoint
url = "http://localhost:8000/api/v1/vocab-generator"

# Parameters
params = {
    "song": "Idol",
    "artist": "YOASOBI"
}

# Make the request
response = requests.get(url, params=params)

# Print the response
if response.status_code == 200:
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

## Expected Response Format

A successful response will have this structure:

```json
{
  "vocabulary": [
    {
      "kanji": "アイドル",
      "romaji": "aidoru",
      "english": "idol"
    },
    {
      "kanji": "夢",
      "romaji": "yume",
      "english": "dream"
    },
    ...
  ]
}
```

If there's an error, the response will look like:

```json
{
  "error": "Error message here"
}
```
