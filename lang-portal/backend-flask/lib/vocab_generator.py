import json  # For working with JSON data
import requests  # For making HTTP requests to the Ollama API
import argparse  # For parsing command-line arguments
import re  # For regular expressions (used for input validation)
import os  # For interacting with the operating system (e.g., file paths)
import gradio as gr  # For creating the Gradio interface
import jsonschema  # For JSON schema validation
from jsonschema import validate

OLLAMA_BASE_URL = "http://127.0.0.1:11434/api"  # Base URL for the Ollama API

# Load JSON Schema
try:
    with open('schema.json', 'r') as f:
        json_schema = json.load(f)
except FileNotFoundError:
    print("Error: schema.json file not found.")
    exit(1)

def generate_japanese_words(word, theme, word_type, max_words=10):
    """Generates Japanese words, handles <think> tags, partial JSON, and validates against schema."""
    prompt = f"Generate {max_words} common Japanese {word_type} related to {theme}, prioritizing common words. Return ONLY valid JSON."
    payload = {
        "model": "deepseek-r1:latest",
        "prompt": prompt
    }

    try:
        response = requests.post(f"{OLLAMA_BASE_URL}/generate", json=payload, stream=True)
        response.raise_for_status()

        generated_json = []
        all_chunks = ""
        json_buffer = ""

        for chunk in response.iter_lines():
            if chunk:
                decoded_chunk = chunk.decode('utf-8')
                all_chunks += decoded_chunk + "\n"

                cleaned_chunk = re.sub(r"<think>.*?</think>", "", decoded_chunk, flags=re.DOTALL)
                cleaned_chunk = re.sub(r"\s+", " ", cleaned_chunk).strip()  # Remove extra whitespace

                if cleaned_chunk:
                    json_buffer += cleaned_chunk

                    try:
                        json_response = json.loads(json_buffer)
                        for entry in json_response:
                            # Debugging output to see the entry before filtering
                            print(f"Entry before filtering: {entry}")

                            try:
                                # Validate the entire entry against the schema
                                validate(instance=entry, schema=json_schema)
                                generated_json.append(entry)  # Append only if valid
                            except jsonschema.exceptions.ValidationError as e:
                                print(f"Schema validation error: {e}")
                                print(f"Invalid entry: {entry}")  # Print the entry that failed validation

                        json_buffer = ""
                    except json.JSONDecodeError:
                        # Partial JSON, continue accumulating
                        pass
                    except Exception as e:
                        print(f"Unexpected error: {e}")
                        print("Full LLM Response (for debugging):")
                        print(all_chunks)
                        return None

        return generated_json

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
        return None


def save_json_to_file(data, filename):
    """Saves or appends JSON data to a file."""
    try:
        if os.path.exists(filename):  # Check if the file exists
            with open(filename, 'r', encoding='utf-8') as f:  # Open in read mode
                try:
                    existing_data = json.load(f)  # Load existing JSON data
                except json.JSONDecodeError: # Handle empty or invalid JSON file
                    existing_data = []  # Start with an empty list
                existing_data.extend(data)  # Append the new data
            with open(filename, 'w', encoding='utf-8') as f:  # Open in write mode
                json.dump(existing_data, f, ensure_ascii=False, indent=4)  # Save with pretty printing
        else:  # If the file doesn't exist
            with open(filename, 'w', encoding='utf-8') as f:  # Create and open in write mode
                json.dump(data, f, ensure_ascii=False, indent=4)  # Save with pretty printing
        print(f"JSON data saved to {filename}")
    except Exception as e:  # Catch any errors during file operations
        print(f"Error saving JSON to file: {e}")

def main():
    """Main function: parses arguments, calls LLM, saves results. Handles CLI and GUI."""
    parser = argparse.ArgumentParser(description="Generate Japanese vocabulary.",
                                     epilog="Example: python vocab_generator.py weather -d ./output -n 20 or python vocab_generator.py -g")  # Argument parser
    parser.add_argument("word", type=str, help="The English word (seed and theme).", nargs='?')  # Word argument (optional for GUI)
    parser.add_argument("-d", "--directory", type=str, default=".", help="Directory to save output files.")  # Directory argument
    parser.add_argument("-n", "--num_words", type=int, default=10, help="Maximum number of words.")  # Number of words argument
    parser.add_argument("-g", "--gui", action="store_true", help="Launch the Gradio interface.")  # GUI flag
    args = parser.parse_args()  # Parse arguments

    if args.gui:  # If GUI option is selected
        def generate_and_save(word, num_words, directory):  # Function for Gradio button
            if not re.match(r"^[a-zA-Z]+$", word):  # Validate input word
                return "Error: Input word must contain only alphabetic characters."  # Error message

            if not os.path.isdir(directory):  # Check if directory exists
                return "Error: Output directory does not exist."  # Error message

            results = ""  # Results string
            for word_type in ["adjectives", "verbs"]:  # Loop for adjectives and verbs
                generated_json = generate_japanese_words(word, word, word_type, num_words)  # Call LLM (word is theme)

                if generated_json:  # If LLM call successful
                    filename = os.path.join(directory, f"{word}_{word_type}.json")  # Create filename
                    save_json_to_file(generated_json, filename)  # Save JSON data
                    results += f"JSON data saved to {filename}\n"  # Success message
                else:
                    results += f"Error generating {word_type}.\n"  # Error message
            return results  # Return results

        with gr.Blocks() as demo:  # Create Gradio interface
            word_input = gr.Textbox(label="English Word (Seed and Theme)")  # Word input
            num_words_input = gr.Number(label="Number of Words", value=10)  # Number of words input
            directory_input = gr.Textbox(label="Output Directory", value=".")  # Directory input
            output_text = gr.Textbox(label="Output")  # Output textbox
            btn = gr.Button("Generate and Save")  # Button
            btn.click(fn=generate_and_save, inputs=[word_input, num_words_input, directory_input], outputs=output_text)  # Button action

        demo.launch()  # Launch Gradio interface
    else:  # Command-line mode
        if not args.word:  # Check if word is provided
            print("Error: Word is required in command-line mode.")  # Error message
            exit(1)

        if not re.match(r"^[a-zA-Z]+$", args.word):  # Validate input word
            print("Error: Input word must contain only alphabetic characters.")  # Error message
            exit(1)

        if not os.path.isdir(args.directory):  # Check if directory exists
            print("Error: Output directory does not exist.")  # Error message
            exit(1)

        for word_type in ["adjectives", "verbs"]:  # Loop for adjectives and verbs
            generated_json = generate_japanese_words(args.word, args.word, word_type, args.num_words)  # Call LLM (word is theme)

            if generated_json:  # If LLM call successful
                filename = os.path.join(args.directory, f"{args.word}_{word_type}.json")  # Create filename
                save_json_to_file(generated_json, filename)  # Save JSON data

if __name__ == "__main__":
    main()  # Call main function