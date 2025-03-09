import requests
import json
import os

# Get the model name from environment or use default
MODEL_NAME = os.environ.get("MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")

def chat_with_llm(prompt, max_tokens=150):
    response = requests.post(
        "http://localhost:8000/v1/completions",
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
    )
    
    result = response.json()
    return result['choices'][0]['text']

if __name__ == "__main__":
    print(f"Chat with {MODEL_NAME} (type 'exit' to quit)")
    print("-----------------------------------")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
            
        response = chat_with_llm(user_input)
        print(f"\nAI: {response}")