import os
import boto3
import json
from typing import List, Dict, Any, Optional
from pprint import pprint  # Import pprint for pretty printing
from jsonschema import validate, ValidationError
from datetime import datetime

# Model ID
MODEL_ID = "amazon.nova-micro-v1:0"

class BedrockChat:
    def __init__(self, model_id: str = MODEL_ID):
        """Initialize Bedrock chat client"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id

    def generate_response(self, messages: List[Dict[str, str]], inference_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate a response using Amazon Bedrock"""
        if inference_config is None:
            inference_config = {"temperature": 0.7}

        # Ensure the content is a list of dictionaries
        for message in messages:
            message['content'] = [{"text": message['content']}]

        try:
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig=inference_config
            )
            return response['output']['message']['content'][0]['text']
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return None

class TranscriptExtractor:
    def __init__(self, transcript: List[Dict[str, str]], prompt_file: str = 'backend/data/prompts/claude_json_prompt.md'):
        """Initialize the TranscriptExtractor with a transcript."""
        self.transcript = transcript
        self.bedrock_chat = BedrockChat()
        self.prompt = self.load_prompt(prompt_file)

    def load_prompt(self, prompt_file: str) -> str:
        """Load the prompt from a file."""
        try:
            with open(prompt_file, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error loading prompt: {str(e)}")
            return ""

    def extract_structured_data(self) -> Any:
        """Extract structured json data from the transcript using Amazon Bedrock."""

        # Prepare the full prompt for Bedrock
        full_prompt = self.prompt + "\n" + "Transcript:\n"

        # Append the transcript to the prompt
        for entry in self.transcript:
            full_prompt += entry['text'] + "\n"

        # Generate a response using the prompt
        response = self.bedrock_chat.generate_response([{"role": "user", "content": full_prompt}])
        
        # Load the JSON schema
        schema_path = 'backend/data/json/schema/json_response_schema.json'
        with open(schema_path, 'r', encoding='utf-8') as schema_file:
            schema = json.load(schema_file)

        # Validate the response against the schema
        try:
            # Assuming response is a JSON string, parse it
            response_data = json.loads(response)
            validate(instance=response_data, schema=schema)
            return response_data  # Return the validated response

        except json.JSONDecodeError:
            raise ValueError("Response is not valid JSON.")
        except ValidationError as e:
            raise ValueError(f"Response does not conform to schema: {e.message}")


    
def main():
    # Path to the transcript file
    transcript_file_path = 'backend/data/transcripts/sY7L5cfCWno.txt'
    
    # Read the transcript from the file
    if os.path.exists(transcript_file_path):
        with open(transcript_file_path, 'r', encoding='utf-8') as file:
            transcript = [{"text": line.strip()} for line in file.readlines() if line.strip()]
        
        # Create an instance of TranscriptExtractor
        extractor = TranscriptExtractor(transcript)
        
        # Extract structured data
        json_response = extractor.extract_structured_data()
        
        # Ensure the output directory exists
        output_dir = 'backend/data/questions'
        os.makedirs(output_dir, exist_ok=True)  # Create the directory if it doesn't exist
        
        # Create a unique filename with a timestamp in the format YYYYMMDD_HHMM
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_path = f"{output_dir}/{os.path.basename(transcript_file_path).replace('.txt', f'_{timestamp}_data.json')}"
        
        # Save the structured data to a JSON file
        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_response, json_file, ensure_ascii=False, indent=4)
        
        # Print the structured data using pprint for better readability
        print(json_response)  # Use pprint to pretty print the structured data

    else:
        print(f"Transcript file not found: {transcript_file_path}")

if __name__ == "__main__":
    main()
