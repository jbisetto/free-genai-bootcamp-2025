# vLLM with Gemma-2B on Apple Silicon - Implementation Notes

## Overview

This directory contains work on implementing vLLM (a high-performance inference engine) to run Google's Gemma-2B model on Apple Silicon hardware. This README documents the implementation attempts and success.

There are more details on the process in the `vllm-tutorial.md` file. 

## What Was Done

1. **Created a Docker Compose Configuration**
   - Created `docker-compose.yaml` to define a containerized environment for running vLLM with Gemma-2B
   - Configured volume mapping for model caching
   - Set up appropriate environment variables and resource limits
   - Added health checks and security configurations

2. **Attempted to Use Pre-built Images**
   - Tried to use the `ghcr.io/vllm-project/vllm-mps:latest` image with ARM64 platform specification
   - Encountered "manifest unknown" error indicating the image doesn't exist for the ARM64 architecture

## Current Blockers

The main blocker encountered is that there isn't a pre-built vLLM Docker image available for Apple Silicon (ARM64) architecture in the GitHub Container Registry. The error message "manifest unknown" confirms this.

```
Error response from daemon: manifest unknown
```

## Next Steps

Based on findings and the vLLM tutorial, the correct approach is to **build the Docker image from source** rather than trying to pull a pre-built image. The tutorial specifically mentions:

> #### Apple Silicon
> have to build from source
> use python3.10

And provides these commands for building:

```bash
docker build -f Dockerfile.arm -t vllm-cpu-env --shm-size=4g .
docker run -it \
            --rm \
            --network=host \
            --cpuset-cpus=<cpu-id-list, optional> \
            --cpuset-mems=<memory-node, optional> \
            vllm-cpu-env
```

## Implementation Plan

To successfully run vLLM with Gemma-2B on Apple Silicon:

1. **Obtain the Dockerfile and Source Code**
   - Clone the vLLM repository: `git clone https://github.com/vllm-project/vllm.git`
   - Navigate to the repository directory

2. **Build the Docker Image**
   - Follow the build instructions in the tutorial
   - Use Python 3.10 as specified

3. **Update Docker Compose Configuration**
   - Modify `docker-compose.yaml` to use the locally built image instead of trying to pull from a registry

4. **Set Up Hugging Face Authentication**
   - Create a Hugging Face account if not already done
   - Accept the Gemma model license
   - Generate and configure an access token

## Resources

- [vLLM GitHub Repository](https://github.com/vllm-project/vllm)
- [Gemma Model on Hugging Face](https://huggingface.co/google/gemma-2b)
- See the `vllm-tutorial.md` file in this directory for detailed setup instructions, originally created using Claude but was updated while attempting to get vLLM working on Mac Mini M2.

## Summary of Changes Made to Get vLLM Working on Mac Mini M2

This document summarizes the key changes and findings from the process of setting up and running language models using vLLM on a Mac Mini M2. The aim was to successfully run the Gemma-2B model, but adjustments were necessary to accommodate the hardware limitations.

## Key Changes:

1. **Model Selection**: Initially targeted the Gemma-2B model (2 billion parameters), but it was found that smaller models like TinyLlama (1.1B parameters) and OPT (125M parameters) performed better on the available hardware.

2. **Hardware Limitations**: The Mac Mini M2 has 8GB of unified memory, which led to memory exhaustion and engine process failures when attempting to load larger models. This necessitated a shift to smaller models that could run efficiently within the memory constraints.

3. **Docker Configuration**: Adjustments were made to Docker settings to allocate more memory, but even with these changes, the larger models proved unmanageable. The focus shifted to optimizing the environment for smaller models.

4. **Removed Health Check**: The health check endpoint was found to be non-functional and was removed from the documentation to avoid misleading users.

5. **Documentation Updates**: Throughout the process, the tutorial and README were updated to reflect the findings, ensuring clarity and accuracy for future users.

