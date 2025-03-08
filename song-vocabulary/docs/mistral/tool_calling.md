# Mistral and OpenAI-Style Tool Calling

## Overview

This document explains the current limitations of Mistral models regarding OpenAI-style tool/function calling and outlines alternative approaches for implementing agent-like behavior with Mistral models.

## Mistral Models and Tool Calling Support

### Mistral 7B (Open Source)

The open-source Mistral 7B model, which we're using through Ollama in this project, **does not natively support OpenAI-style tool calling**. This means:

- It cannot automatically parse JSON schemas for tools
- It doesn't have built-in capability to output structured function calls
- It lacks the ability to validate its outputs against function schemas

### Mistral Large (API)

The commercial Mistral Large model available through Mistral's API does support function calling similar to OpenAI's implementation. However, this is not available in the open-source versions that can be run locally through Ollama.

## Alternatives to Native Tool Calling

Since we're using the open-source Mistral 7B model through Ollama, we've implemented the following approach:

### ReAct Pattern Implementation

Our current implementation uses the ReAct (Reasoning + Acting) pattern:

1. We provide a structured prompt that instructs the model to:
   - Think about the problem
   - Choose an action from a predefined set
   - Specify inputs for that action
   - Observe the results
   - Repeat until reaching a final answer

2. We parse the model's free-text responses using regex to extract:
   - Thoughts
   - Actions
   - Action inputs
   - Final answers

3. We execute the extracted actions and provide the results back to the model.

### Challenges with this Approach

- **Parsing Complexity**: Requires complex regex to extract structured information from unstructured text
- **Format Adherence**: The model may not always adhere to the expected format
- **Error Handling**: Requires robust error handling for malformed responses
- **JSON Parsing**: Particularly challenging when extracting JSON data from the model's responses

## Potential Improvements

While maintaining the use of Mistral 7B through Ollama, we could:

1. **Improve Structured Prompting**: Provide clearer instructions and examples to the model
2. **Enhance Parsing Logic**: Develop more robust parsing mechanisms
3. **Use Instructor Library**: Leverage Instructor for structured output validation
4. **Consider Upgrading**: If function calling is critical, consider using models that natively support it

## Conclusion

Our current implementation successfully extracts vocabulary from song lyrics using a custom ReAct agent with Mistral 7B, despite the lack of native tool calling support. The implementation includes robust error handling and fallback mechanisms to ensure reliable operation.

For future development, we might consider upgrading to models with native function calling support if the complexity of the current approach becomes a maintenance burden.
