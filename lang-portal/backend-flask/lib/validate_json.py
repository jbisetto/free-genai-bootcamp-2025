import json
import jsonschema
from jsonschema import validate

# Sample JSON data
sample_json = {
    "kanji": "払う",
    "romaji": "harau",
    "english": "to pay",
    "parts": [
        { "kanji": "払", "romaji": ["ha","ra"] },
        { "kanji": "う", "romaji": ["u"] }
    ]
}

# Load the JSON schema
try:
    with open('schema.json', 'r') as f:
        json_schema = json.load(f)
    print("Schema loaded successfully.")
except FileNotFoundError:
    print("Error: schema.json file not found.")
    exit(1)

# Validate the sample JSON against the schema
try:
    print("Validating sample JSON...")
    validate(instance=sample_json, schema=json_schema)
    print("Sample JSON is valid.")
except jsonschema.exceptions.ValidationError as e:
    print("Sample JSON is invalid.")
    print(f"Validation error: {e.message}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")