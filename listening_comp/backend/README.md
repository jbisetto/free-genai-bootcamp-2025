classDiagram
    class TranscriptExtractor {
        +load_schema(schema_path: str) : dict
        +parse_response(response: str, schema_path: str) : dict
        +extract_questions(transcript: str) : dict
        -validate_schema(data: dict, schema: dict) : None
    }

    class SchemaLoader {
        +load_schema(schema_path: str) : dict
    }

    class JSONValidator {
        +validate(data: dict, schema: dict) : None
    }

    TranscriptExtractor --> SchemaLoader : uses
    TranscriptExtractor --> JSONValidator : validates
