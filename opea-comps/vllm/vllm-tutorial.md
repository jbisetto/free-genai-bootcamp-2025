# Tutorial: Running Gemma 2B with vLLM on Mac Mini M2

This tutorial will guide you through setting up and running Google's Gemma 2B model using vLLM on your Mac Mini M2. This setup allows you to run a compact but powerful language model locally on Apple Silicon.

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

## Step 3: Pull the vLLM Docker Image

Pull the ARM-compatible vLLM image:

```bash
docker pull ghcr.io/vllm-project/vllm-mps:latest
```

#### Apple Silicon
have to build from source
use python3.10

```bash
docker build -f Dockerfile.cpu -t vllm-cpu-env --shm-size=4g .
docker run -it \
            --rm \
            --network=host \
            --cpuset-cpus=<cpu-id-list, optional> \
            --cpuset-mems=<memory-node, optional> \
            vllm-cpu-env
```

## Step 4: Create a Docker Volume for Model Storage

To avoid downloading the model each time you run the container:

```bash
docker volume create gemma-models
```

## Step 5: Run the Docker Container with Gemma 2B

Launch the container with the following command:

```bash
docker run --platform linux/arm64 -p 8000:8000 \
  -v gemma-models:/root/.cache/huggingface \
  -e HF_TOKEN=$HF_TOKEN \
  -e PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 \
  ghcr.io/vllm-project/vllm-mps:latest \
  --model google/gemma-2b \
  --max-model-len 2048 \
  --dtype float16 \
  --device mps \
  --chat-template gemma
```

This will:
- Map port 8000 to your local machine
- Use the Metal Performance Shaders (MPS) backend
- Set the model to run in 16-bit precision
- Use the Gemma chat template for better conversation formatting

The first run will download the model, which may take several minutes. Subsequent runs will be faster as the model will be cached.

## Step 6: Test the Model with a Simple Query

Open a new terminal window and test that the API is working:

```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-2b",
    "prompt": "Explain domain modeling in software development",
    "max_tokens": 256,
    "temperature": 0.7
  }'
```

## Step 7: Create a Simple Python Client

Create a file named `chat_with_gemma.py`:

```python
import requests
import json

def chat_with_gemma(prompt, max_tokens=256):
    response = requests.post(
        "http://localhost:8000/v1/completions",
        json={
            "model": "google/gemma-2b",
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
    )
    
    result = response.json()
    return result['choices'][0]['text']

if __name__ == "__main__":
    print("Chat with Gemma 2B (type 'exit' to quit)")
    print("-----------------------------------")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
            
        response = chat_with_gemma(user_input)
        print(f"\nGemma: {response}")
```

Run the script:

```bash
python chat_with_gemma.py
```

## Step 8: Using Chat Completions API (Optional)

For a more interactive chat experience, you can use the Chat Completions API:

```python
import requests
import json

def chat_with_gemma(messages, max_tokens=256):
    response = requests.post(
        "http://localhost:8000/v1/chat/completions",
        json={
            "model": "google/gemma-2b",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
    )
    
    result = response.json()
    return result['choices'][0]['message']['content']

if __name__ == "__main__":
    print("Chat with Gemma 2B (type 'exit' to quit)")
    print("-----------------------------------")
    
    # Store conversation history
    conversation = [
        {"role": "system", "content": "You are a helpful AI assistant based on the Gemma 2B model."}
    ]
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
            
        # Add user message to conversation
        conversation.append({"role": "user", "content": user_input})
        
        # Get response
        response = chat_with_gemma(conversation)
        
        # Add assistant response to conversation
        conversation.append({"role": "assistant", "content": response})
        
        print(f"\nGemma: {response}")
```

## Troubleshooting

1. **Out of Memory Errors**: 
   - Reduce `--max-model-len` to 1024 
   - Try a smaller batch size with `--max-batch-size 4`

2. **Slow Response Times**:
   - Use `--max-num-batched-tokens 512` to reduce latency at the cost of throughput

3. **Model Download Issues**:
   - Verify your Hugging Face token is valid
   - Check you've accepted the model license agreement

4. **Docker Errors**:
   - Ensure Docker has sufficient resources allocated in Docker Desktop preferences

## Shutting Down

To stop the vLLM server, press Ctrl+C in the terminal where it's running.

To remove the container:
```bash
docker ps -a
docker rm [CONTAINER_ID]
```

## Conclusion

You now have a local Gemma 2B model running on your Mac Mini M2 using vLLM! This setup gives you a powerful language model without requiring an internet connection or sending data to external APIs.

For production use cases, you might want to consider:
- Running on a more powerful machine
- Using specialized quantization techniques
- Fine-tuning the model for specific tasks

Happy experimenting with your local LLM!
