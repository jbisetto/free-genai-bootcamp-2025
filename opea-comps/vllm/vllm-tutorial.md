# Tutorial: Running Language Models with vLLM on Mac Mini M2

This tutorial will guide you through setting up and running language models using vLLM on your Mac Mini M2. This setup allows you to run language models locally on Apple Silicon. While the original goal was to run Gemma-2B, testing revealed that smaller models work better with the available resources.

## Hardware Specifications and Limitations

This tutorial was developed and tested on a Mac Mini with the following specifications:
- Apple M2 chip
- 8GB unified memory
- macOS Sonoma

These hardware specifications present certain limitations when running large language models:

### What Didn't Work with Larger Models

When attempting to run the Gemma-2B model (which has approximately 2 billion parameters), several issues were encountered:

1. **Memory Exhaustion**: The Docker container would crash with out-of-memory errors when loading the full model into RAM
2. **Engine Process Failures**: vLLM would report "Engine process failed to start" errors
3. **Slow Loading Times**: Even when allocating maximum available resources, the model would take an extremely long time to load
4. **MPS Compatibility Issues**: While Apple's Metal Performance Shaders (MPS) backend is available, vLLM's implementation had limited compatibility with it
5. **Docker Resource Constraints**: Even with increased memory allocation in Docker Desktop settings, the 8GB system memory was insufficient for the model's requirements

These limitations necessitated exploring smaller, more efficient models that could run successfully on this hardware configuration.

## Prerequisites

- Mac Mini with M2 chip
- macOS Sonoma (14.0) or newer
- At least 8GB RAM (16GB recommended)
- 10GB+ free disk space
- Docker Desktop for Mac (Apple Silicon version)
- Hugging Face account (for model access)

## Step 1: Install Docker Desktop for Mac

1. Download Docker Desktop for Mac (Apple Silicon) from [Docker's website](https://www.docker.com/products/docker-desktop/)
2. Install and launch Docker Desktop
3. Verify Docker is running with:
   ```bash
   docker --version
   ```

## Step 2: Set Up Hugging Face Access Token

Gemma requires authentication to download:

1. Create a Hugging Face account if you don't have one: [https://huggingface.co/join](https://huggingface.co/join)
2. Visit [https://huggingface.co/google/gemma-2b](https://huggingface.co/google/gemma-2b) and accept the model license
3. Create an access token:
   - Go to [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
   - Click "New token"
   - Name it "vLLM" and set role to "read"
   - Copy the generated token

4. In your terminal, export the token as an environment variable:
   ```bash
   export HF_TOKEN=your_huggingface_token_here
   ```

## Step 3: Build the vLLM Docker Image for Apple Silicon

For Apple Silicon, we need to build the vLLM Docker image from source:

1. Clone the vLLM repository if you haven't already:
```bash
git clone https://github.com/vllm-project/vllm.git
cd vllm
```

2. Build the Docker image using Python 3.10:
```bash
docker build -f Dockerfile.arm -t vllm-cpu-env --shm-size=4g .
```

This will create a Docker image tagged as `vllm-cpu-env` that's compatible with Apple Silicon.

## Step 4: Create a Docker Volume for Model Storage

To avoid downloading the model each time you run the container, create a persistent volume:

```bash
docker volume create small-models
```

This volume will store the downloaded model files, ensuring they persist between container runs.

## Step 5: Run the Docker Container with a Smaller Model

While Gemma-2B was our initial target, we found that smaller models work better with the available resources on Mac Mini M2. Here's how to run a smaller model like TinyLlama or OPT:

1. Before running the container, make sure you've set your Hugging Face token as an environment variable:

```bash
export HF_TOKEN=your_huggingface_token_here
```

2. Run the container with TinyLlama (1.1B parameters):

```bash
docker run -it --rm -p 8000:8000 \
  -v small-models:/root/.cache/huggingface \
  -e HF_TOKEN=$HF_TOKEN \
  vllm-cpu-env \
  --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
  --max-model-len 1024 \
  --dtype float16 \
  --device cpu
```

Alternatively, you can try an even smaller model like OPT-125M:

```bash
docker run -it --rm -p 8000:8000 \
  -v small-models:/root/.cache/huggingface \
  -e HF_TOKEN=$HF_TOKEN \
  vllm-cpu-env \
  --model facebook/opt-125m \
  --max-model-len 1024 \
  --dtype float16 \
  --device cpu
```

Note: We're using `--device cpu` instead of `mps` because vLLM's current implementation doesn't support MPS as a device option.

This will:
- Map port 8000 to your local machine
- Use the Metal Performance Shaders (MPS) backend
- Set the model to run in 16-bit precision
- Use the Gemma chat template for better conversation formatting

The first run will download the model, which may take several minutes. Subsequent runs will be faster as the model will be cached.

## Step 6: Test the Model with a Simple Query

Open a new terminal window and test that the API is working. The curl command should match the model you're running:

### Testing the Model

To test that the model is working, use the following curl command:
### For TinyLlama:
```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "prompt": "Explain what a language model is in simple terms",
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

### For OPT-125M:
```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "facebook/opt-125m",
    "prompt": "Explain what a language model is in simple terms",
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

### Docker Test Requests

For convenience, you can also find pre-defined requests in the `docker-test-requests` file located in the `bin` directory. This file contains sample curl commands to test the API endpoints.

## Step 7: Create a Simple Python Client

Create a file named `chat_with_llm.py`:

```python
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
```

Run the script:

```bash
python chat_with_llm.py
```

Or specify a different model:

```bash
MODEL_NAME="facebook/opt-125m" python chat_with_llm.py
```



## Step 8: Using Chat Completions API (Optional)

For a more interactive chat experience, you can use the Chat Completions API with models that support it:

```python
import requests
import json
import os

# Get the model name from environment or use default
MODEL_NAME = os.environ.get("MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")

def chat_with_llm(messages, max_tokens=150):
    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        json={
            "model": MODEL_NAME,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
    )
    
    result = response.json()
    return result['choices'][0]['message']['content']

if __name__ == "__main__":
    print(f"Chat with {MODEL_NAME} (type 'exit' to quit)")
    print("-----------------------------------")
    
    # Store conversation history
    conversation = [
        {"role": "system", "content": "You are a helpful AI assistant."}
    ]
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
            
        # Add user message to conversation
        conversation.append({"role": "user", "content": user_input})
        
        # Get response
        response = chat_with_llm(conversation)
        
        # Add assistant response to conversation
        conversation.append({"role": "assistant", "content": response})
        
        print(f"\nAI: {response}")
```

## Troubleshooting

### Model Compatibility Issues

If you encounter errors about model compatibility with vLLM:

1. Not all models are compatible with vLLM. If you see an error like `ValueError: [ModelName] has no vLLM implementation`, try a different model from the list of compatible ones.
2. Models known to work with vLLM on Apple Silicon include:
   - TinyLlama/TinyLlama-1.1B-Chat-v1.0
   - facebook/opt-125m
   - microsoft/phi-1_5
   - EleutherAI/pythia-70m

### Memory Issues

If you encounter out-of-memory errors:

1. Increase Docker's memory allocation in Docker Desktop settings
2. Try reducing `max-model-len` to a smaller value like 512
3. Use an even smaller model (under 500M parameters)
4. Add swap space to the Docker container with `--memory-swap 16g`

### API Connection Issues

If you can't connect to the API:

1. Make sure the container is running
2. Check that port 8000 is not being used by another application
3. Try using `-p 8000:8000` instead of `--network=host` when starting the container

## Shutting Down

To stop the vLLM server, press Ctrl+C in the terminal where it's running.

To remove the container:
```bash
docker ps -a
docker rm [CONTAINER_ID]
```

## Advanced Configuration

### Trying Larger Models

If you want to attempt running larger models like Gemma-2B, you'll need to allocate more resources:

1. Increase Docker's memory allocation in Docker Desktop settings (at least 12GB recommended)
2. Use a quantized version of the model if available
3. Run with minimal context length and batch size

```bash
docker run -it --rm -p 8000:8000 \
  -v large-models:/root/.cache/huggingface \
  -e HF_TOKEN=$HF_TOKEN \
  --memory=12g --memory-swap=16g \
  vllm-cpu-env \
  --model google/gemma-2b \
  --max-model-len 1024 \
  --dtype float16 \
  --device cpu \
  --max-num-batched-tokens 1024 \
  --max-num-seqs 32
```

Note: This may still exceed the resources of a Mac Mini M2 with 8GB RAM.

### Error Messages Observed

When attempting to run Gemma-2B, the following errors appeared:

```
Engine process failed to start
```

And:

```
RuntimeError: CUDA out of memory. Tried to allocate X MiB
```

These errors indicate insufficient memory resources for the model. Even when using CPU instead of GPU/MPS, the model's memory requirements exceeded the available system resources.

### Hardware Upgrades That Would Help

If you want to run larger models like Gemma-2B on Apple Silicon, consider:

1. Using a Mac with 16GB+ unified memory (M2 Pro/Max or newer)
2. Adding external swap space or using a fast SSD for virtual memory
3. Using quantized versions of models (4-bit or 8-bit precision) when available

## Conclusion

You now have a local language model running on your Mac Mini M2 using vLLM! While the initial target was Gemma-2B, testing showed that smaller models like TinyLlama and OPT work better with the available resources on Apple Silicon.

This setup gives you a functional language model without requiring an internet connection or sending data to external APIs. As you become more comfortable with vLLM, you can experiment with different models and configurations.

For production use cases, you might want to consider:
- Running on a more powerful machine
- Using specialized quantization techniques
- Fine-tuning the model for specific tasks

Happy experimenting with your local LLM!
