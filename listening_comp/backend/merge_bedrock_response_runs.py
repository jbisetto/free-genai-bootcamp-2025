import os
import json
import glob
import time
from pprint import pprint  # Import pprint for pretty printing
from jsonschema import validate, ValidationError

class JsonMerger:
    def __init__(self, directory: str, schema_file: str):
        self.directory = directory
        self.schema_file = schema_file
        self.merged_data = {}
    
    def load_schema(self) -> None:
        with open(self.schema_file, 'r', encoding='utf-8') as schema_file:  # Ensure UTF-8 encoding
            self.schema = json.load(schema_file)

    def merge_json_files(self, prefix: str) -> None:
        """Merge JSON files with the specified prefix into a single dictionary."""
        files = glob.glob(os.path.join(self.directory, f"{prefix}*.json"))
        
        if not files:
            print(f"No files found for prefix: {prefix}")
            return

        # Initialize the merged data and the next unique ID
        next_id = 1
        merged_data = []

        # Process the first file
        first_file = files[0]
        print(f"processing first file: {first_file}")
        try:
            with open(first_file, 'r', encoding='utf-8') as json_file:  # Ensure UTF-8 encoding
                data = json.load(json_file)
                for record in data['questions']:
                    if isinstance(record, dict):
                        record['id'] = next_id  # Assign a unique ID
                        merged_data.append(record)
                        next_id += 1  # Increment the ID for the next record
                    else:
                        print(f"Unexpected record format: {record}")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {first_file}")
            return
        except Exception as e:
            print(f"An error occurred while processing file {first_file}: {str(e)}")
            return

        # Process subsequent files
        for file in files[1:]:
            print(f"processing file: {file}")
            try:
                with open(file, 'r', encoding='utf-8') as json_file:  # Ensure UTF-8 encoding
                    data = json.load(json_file)
                    for record in data['questions']:
                        introduction_text = record.get('introduction', '')  # Assuming 'introduction' is the key
                        if not any(existing_record['introduction'] == introduction_text for existing_record in merged_data):
                            if isinstance(record, dict):
                                record['id'] = next_id  # Assign a new unique ID
                                merged_data.append(record)
                                next_id += 1  # Increment the ID for the next record
                            else:
                                print(f"Unexpected record format: {record}")
                        else:
                            print(f"Introduction text already exists, skipping: {introduction_text}")
            except json.JSONDecodeError:
                print(f"Error decoding JSON from file: {file}")
            except Exception as e:
                print(f"An error occurred while processing file {file}: {str(e)}")

        # Update the merged_data in the class
        self.merged_data = {record['id']: record for record in merged_data}  # Use ID as the key

    def validate_json(self) -> bool:
        # Create a valid JSON structure from merged_data
        valid_json = {
            "questions": list(self.merged_data.values())  # Assuming merged_data contains question objects
        }

        try:
            validate(instance=valid_json, schema=self.schema)
        except ValidationError as e:
            print(f"Validation error: {e.message}")
            return False
        return True

    def save_merged_file(self, prefix: str) -> None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.directory, f"{prefix}_merged_runs_{timestamp}.json")
        with open(output_file, 'w', encoding='utf-8') as outfile:  # Ensure UTF-8 encoding
            json.dump(list(self.merged_data.values()), outfile, indent=4, ensure_ascii=False)  # Prevent ASCII encoding

    def process(self) -> None:
        self.load_schema()
        files = glob.glob(os.path.join(self.directory, '*.json'))
        print("Found JSON files:")  # Debugging: List of found JSON files
        for file in files:
            print(file)  # Print each file on a new line
        prefixes = set(file.split('/')[-1].split('_')[0] for file in files if 'merged_runs' not in file)
        print(f"Extracted prefixes (excluding merged_runs): {prefixes}")  # Debugging: List of extracted prefixes
        for prefix in prefixes:
            print(f"Processing prefix: {prefix}")  # Debugging: Current prefix being processed
            self.merge_json_files(prefix)
            if self.validate_json():
                self.save_merged_file(prefix)
            else:
                print(f"Merged data for prefix '{prefix}' is not valid.")

if __name__ == "__main__":
    directory = 'backend/data/questions'
    schema_file = 'backend/data/json/schema/json_response_schema.json'
    merger = JsonMerger(directory, schema_file)
    merger.process()