# GenAI Bootcamp Project: Language Learning Platform

An experimental platform showcasing various Generative AI techniques and implementations through the lens of language learning applications.

![GenAI Project](https://img.shields.io/badge/Project-Generative%20AI-brightgreen)
![AWS Bedrock](https://img.shields.io/badge/AI-AWS%20Bedrock-orange)
![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-51.1%25-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-34.9%25-blue)
![JavaScript](https://img.shields.io/badge/JavaScript-10.3%25-yellow)

I've created this repository as part of the project work for the [Free GenAI Bootcamp](https://genai.cloudprojectbootcamp.com/) course.

## Project Focus

This repository serves as a practical exploration of Generative AI concepts and AWS AI services. The language learning application is a vehicle to demonstrate various GenAI techniques in real-world scenarios.

## GenAI Techniques Demonstrated

- **Retrieval Augmented Generation (RAG)**: Implementation with ChromaDB for contextually enhanced responses
- **LLM Prompt Engineering**: Structured prompts for consistent AI outputs
- **Vector Embeddings**: Using Amazon Titan Embeddings for semantic search
- **JSON Schema Validation**: Ensuring structured outputs from generative models
- **Multi-modal AI Integration**: Combining text, speech, and interactive elements
- **AWS Bedrock Integration**: Leveraging cloud-based AI services at scale

## Experimental Modules

Each module in this project demonstrates different aspects of Generative AI:

### Listening Comprehension
- **GenAI Focus**: RAG implementation, embedding generation, and structured output validation
- **AWS Services**: Bedrock Chat (Nova Micro model), Titan Embeddings
- **Technical Highlight**: Demonstrates progression from basic LLM to full RAG implementation

### Typing Tutor
- **GenAI Focus**: Real-time feedback generation and adaptive learning
- **Technical Highlight**: Interactive AI response generation

### Sentence Constructor
- **GenAI Focus**: Grammar validation and contextual suggestions
- **Technical Highlight**: Structured output generation with constraints

### Writing Practice
- **GenAI Focus**: Content evaluation and feedback generation
- **Technical Highlight**: Multi-step reasoning for complex feedback

## Project Structure

```
free-genai-bootcamp-2025/
├── backend/               # Backend services and utilities
├── genai-architecting/    # GenAI architectural diagrams and designs
├── lang-portal/           # Central hub connecting all modules
│   ├── backend-flask/     # Flask API server
│   ├── frontend-react/    # React-based UI
│   └── prompts/           # LLM prompt templates
├── listening_comp/        # RAG implementation with ChromaDB
│   ├── backend/           # Question generation with vector store
│   └── frontend/          # Streamlit interface
├── opea-comps/            # Additional components
│   └── mega-services/     # Service integrations
├── sentence-constructor/  # Structured output with constraints
├── typing-tutor/          # Interactive feedback generation
└── writing-practice/      # Multi-step reasoning and feedback
```

## Technical Implementation

- **Frontend**: React (TypeScript) for building responsive interfaces to AI services
- **Backend**: Python-based services integrating with AWS Bedrock
- **Vector Database**: ChromaDB for embedding storage and retrieval
- **AI Models**: Amazon Bedrock (Nova Micro, Titan Embeddings)
- **Languages**: Python (51.1%), TypeScript (34.9%), JavaScript (10.3%), Ruby (1.7%), CSS (0.8%), HTML (0.7%)

## Learning Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [RAG Pattern Implementation Guide](https://aws.amazon.com/blogs/machine-learning/question-answering-using-retrieval-augmented-generation-with-foundation-models-in-amazon-sagemaker-jumpstart/)

## Development Updates

### Week 3 Updates
- **[🚧OPEA Implementation](https://github.com/jbisetto/free-genai-bootcamp-2025/issues/7)**: WIP Added Operational Pattern Extraction and Analysis

### Week 2 Updates
- **[✅Listening Comprehension](https://github.com/jbisetto/free-genai-bootcamp-2025/issues/9)**: Implemented RAG with ChromaDB for contextually relevant question generation
- **[✅Kana Writing Practice](https://github.com/jbisetto/free-genai-bootcamp-2025/issues/8)**: Added AI-powered feedback for Japanese character writing

### Week 1 Updates
- **[✅Vocabulary Generator](https://github.com/jbisetto/free-genai-bootcamp-2025/issues/6)**: Created AI-powered vocabulary generation system
- **[✅Frontend Development](https://github.com/jbisetto/free-genai-bootcamp-2025/issues/5)**: Built React-based UI for language learning portal
- **[✅Backend Flask](https://github.com/jbisetto/free-genai-bootcamp-2025/issues/4)**: Developed Flask API server with SQLite database

### Sentence Constructor Experiments
- **[✅Claude Implementation](https://github.com/jbisetto/free-genai-bootcamp-2025/issues/3)**: Tested Anthropic's Claude for sentence construction
- **[✅ChatGPT Implementation](https://github.com/jbisetto/free-genai-bootcamp-2025/issues/2)**: Tested OpenAI's ChatGPT for sentence construction
- **[✅Meta.ai Implementation](https://github.com/jbisetto/free-genai-bootcamp-2025/issues/1)**: Tested Meta's LLM for sentence construction
