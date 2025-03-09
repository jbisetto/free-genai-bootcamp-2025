# TTS Service - Learning Journal

## Changes for Building ARM Image

This section outlines the modifications made to enable building the ARM-compatible Docker image for the TTS services:

1. **Dockerfile Adjustments**: The Dockerfile was updated to specify the ARM architecture by using the `--platform=linux/arm64` directive in the `FROM` statement.

2. **Image Compatibility**: The images for `speecht5-service`, `gptsovits-service`, and `tts-gptsovits` were identified as not running natively on Apple Silicon. A note was added to the README to inform users about this limitation.

3. **Service Configuration**: The `docker-compose.yaml` file was modified to set the platform for the `speecht5-service` to `linux/arm64`, ensuring compatibility with the Mac Mini M2.

4. **Health Check Endpoint**: A health check endpoint was added to the `service.py` to monitor the service's status.

5. **Run Command Updates**: The run command for the `speecht5-service` was updated to reflect the correct port mapping for the service.

## What I've Learned About Text-to-Speech Services

As part of the GenAI Bootcamp 2025, I've been exploring the OPEA Text-to-Speech (TTS) service. This README documents my learning journey and the key insights I've gained about containerized TTS services.

## Understanding the TTS Architecture

The OPEA TTS service is composed of multiple components working together:

1. **SpeechT5 Service**: A Microsoft-developed model that converts text to speech. I learned that this model offers good quality for general purpose TTS tasks and runs on port 7055.

2. **GPT-SoVITS Service**: An advanced TTS model that combines GPT (for text understanding) with SoVITS (for voice synthesis). This was fascinating to learn about because it produces much more natural-sounding speech with proper intonation. It runs on port 9880 and stores audio files in a mounted volume.

3. **TTS Integration Service**: Acts as the main interface for applications to request speech synthesis. I discovered that this service coordinates between different TTS models and provides a unified API.

## Important Note on Image Compatibility

The Docker images specified in the `docker-compose.yaml` file for the `speecht5-service`, `gptsovits-service`, and `tts-gptsovits` do not run natively on Apple Silicon (ARM64) architecture. Users may encounter compatibility issues and should consider using images built for ARM architecture or build from source if necessary.

## Docker and Containerization Insights

Working with the TTS service taught me several important concepts about Docker:

- **Multi-Container Applications**: I learned how Docker Compose manages multiple interconnected services, which is much more practical than managing individual containers.

- **Health Checks**: The configuration includes health checks to ensure services are running properly before dependencies try to use them. This prevents cascading failures.

- **Environment Variables**: The Docker Compose file uses environment variables with default values (using the `${VAR:-default}` syntax), which makes the configuration flexible and adaptable to different environments.

- **Volume Mounting**: The GPT-SoVITS service mounts an audio directory, teaching me how containers can persist data even when they're rebuilt or restarted.

## Running the TTS Service

To run the TTS service, I use these commands:

```bash
# Navigate to the TTS directory
cd opea-comps/tts

# Start all services
docker-compose up

# To run in the background
docker-compose up -d

# To stop the services
docker-compose down
```

The main TTS service becomes available at http://localhost:9088 (or whatever port is specified in the TTS_PORT environment variable).

## Customization Options

I've learned that the TTS service can be customized through environment variables:

```bash
# Change the port for the TTS service
export TTS_PORT=8000

# Use a different Docker registry
export REGISTRY=my-registry

# Start with custom configuration
docker-compose up
```

## Challenges and Solutions

During my learning process, I encountered and solved several challenges:

1. **Understanding Service Dependencies**: I initially didn't understand why the order of service startup mattered. The `depends_on` configuration with health checks solved this by ensuring services only start when their dependencies are ready.

2. **Network Configuration**: I learned about bridge networks in Docker and how they allow containers to communicate with each other while remaining isolated from the host network.

3. **Proxy Settings**: The configuration includes proxy settings, which taught me how containerized applications can access external resources through corporate proxies.

## Docker Compose Best Practices I've Learned

As I've continued working with Docker Compose, I've discovered some important best practices that significantly improved our TTS service deployment:

- **Resource Management is Critical**: I was surprised to learn how easily AI models can consume all available system resources. Adding CPU and memory limits (`deploy.resources.limits`) to each service prevents one container from affecting the performance of others—something that saved us during a demo when the SpeechT5 model started consuming too much memory.

- **Named Volumes Over Bind Mounts**: Converting our local directory mounts to named volumes (`volumes: audio_data`) was a game-changer for portability. I can now run the exact same configuration on any machine without worrying about local directory structures, and Docker handles the data persistence automatically.

- **Service Discovery Through Container Names**: Replacing hardcoded IP addresses with service names (like `http://gptsovits-service:9880`) was an "aha moment" for me. Docker's built-in DNS resolution means services can find each other automatically, even if their IP addresses change when containers restart.

## Next Steps in My Learning Journey

As I continue to explore TTS technologies, I plan to:

1. Experiment with different TTS models to compare their quality and performance
2. Learn how to train custom voice models for specific use cases
3. Explore how to integrate the TTS service with other OPEA components
4. Investigate ways to optimize the performance and resource usage of TTS services

This project has given me valuable hands-on experience with both containerization technologies and state-of-the-art TTS systems.

## Summary of Changes Made to Get vLLM Working on Mac Mini M2

This document summarizes the key changes and findings from the process of setting up and running language models using vLLM on a Mac Mini M2. The aim was to successfully run the Gemma-2B model, but adjustments were necessary to accommodate the hardware limitations.

This work has been taken as far as time allows.
