# Japanese Listening Comprehension Assistant

## Overview
A sophisticated language learning tool that demonstrates the evolution from basic LLM responses to a fully contextual learning assistant using RAG (Retrieval Augmented Generation). This application helps students practice Japanese listening comprehension by generating contextually relevant questions based on Japanese language content.

## Key Features
- **Progressive Learning Approach**: Demonstrates clear progression from base LLM to RAG implementation
- **Multilingual Content Processing**: Handles both Japanese and English text effectively
- **YouTube Transcript Integration**: Extracts and processes Japanese content from YouTube videos
- **Question Generation**: Creates structured, contextually relevant questions in Japanese
- **Vector-based Semantic Search**: Utilizes embeddings to find similar questions and content
- **Interactive Learning Interface**: Streamlit-based UI for student engagement

## Technical Architecture
- **Frontend**: Streamlit application providing an intuitive learning interface
- **Backend**: Python-based system integrating multiple AWS services
- **Vector Store**: ChromaDB for storing and retrieving embedded Japanese language content
- **AI Components**:
  - Amazon Bedrock for text generation (Nova Micro model)
  - Titan Embeddings for semantic search capabilities
  - JSON schema validation for consistent question formatting

## Setup Requirements
- Python 3.10+
- AWS account with Bedrock access
- Proper IAM permissions for Amazon Bedrock services
- ChromaDB for vector storage
- YouTube Transcript API for content extraction

## Usage
1. Set up a conda environment: `conda create -n language-learning-assistant python=3.10`
2. Install dependencies: `pip install -r requirements.txt`
3. Configure AWS credentials with appropriate permissions
4. Run the backend: `python3 backend/main.py`
5. Launch the frontend: `streamlit run main.py`

---
**Technical Uncertainty:**
1. How effectively can we process and structure bilingual (Japanese/English) content for RAG?
2. What's the optimal way to chunk and embed Japanese language content?
3. How can we effectively demonstrate the progression from base LLM to RAG to students?
4. Can we maintain context accuracy when retrieving Japanese language examples?
5. How do we balance between giving direct answers and providing learning guidance?
6. What's the most effective way to structure multiple-choice questions from retrieved content?

**Technical Restrictions:**
* Must use Amazon Bedrock for:
   * API (converse, guardrails, embeddings, agents) (https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
     * Aamzon Nova Micro for text generation (https://aws.amazon.com/ai/generative-ai/nova)
   * Titan for embeddings
* Must implement in Streamlit, pandas (data visualization)
* Must use SQLite for vector storage
* Must handle YouTube transcripts as knowledge source (YouTubeTranscriptApi: https://pypi.org/project/youtube-transcript-api/)
* Must demonstrate clear progression through stages:
   * Base LLM
   * Raw transcript
   * Structured data
   * RAG implementation
   * Interactive features
* Must maintain clear separation between components for teaching purposes
* Must include proper error handling for Japanese text processing
* Must provide clear visualization of RAG process
* Should work within free tier limits where possible

This structure:
1. Sets clear expectations
2. Highlights key technical challenges
3. Defines specific constraints
4. Keeps focus on both learning outcomes and technical implementation

## Knowledgebase

https://github.com/chroma-core/chroma

# How to run the frontend

```shell
streamlit run main.py
```

# How to run the backend

```shell
pip install -r requirements.txt  
cd ..
python3 backend/main.py
```

# Set up conda
```shell
conda create -n language-learning-assistant python=3.10
conda activate language-learning-assistant
```
# AWS Setup Notes
## IAM User Permissions
Create a new user with the following permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "bedrock:InvokeModel",
            "Resource": "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-micro-v1:0"
        },
        {
            "Effect": "Allow",
            "Action": "bedrock:ListFoundationModels",
            "Resource": "*"
        }
    ]
}
```
Also create a key for the user to access the AWS services. Configure the key to use the region us-east-1 after installing the AWS CLI. 


# Notes vector store work
## Do we need to use Japanese text in the semantic search?

The `vector_store.py` script utilizes Amazon Bedrock's Titan Embeddings model to perform semantic searches on a collection of Japanese questions. This section addresses whether search queries can be in English or if Japanese is preferable, and why.

**Embedding Generation:**

*   The `BedrockEmbeddings.generate_embedding(self, text: str)` method converts text into a numerical vector representation (an "embedding").
*   This method does not translate the input text. It accepts the text in its original language (e.g., English, Japanese) and sends it directly to Amazon Bedrock.
*   The `amazon.titan-embed-text-v1` model, used by Bedrock, is multilingual and understands the semantics of various languages.

**Data and Search Process:**

*   **Data in ChromaDB:** The `ChromaDBEmbedder.embed_data()` method processes data from a JSON file. All the questions in this file are in Japanese, meaning that the entire ChromaDB collection consists of Japanese questions.
*   **Search in `ChromaDBEmbedder.semantic_search()`:**
    *   The search query (`query`) is taken as input from the user.
    *   The `query` is *not* translated. It is passed directly to `self.bedrock_embeddings.generate_embedding(query)` for embedding.
    *   ChromaDB compares the embedding of the search query to the embeddings of the Japanese questions in the database.
*   **No Translation:** Crucially, no translation occurs anywhere in the code. The search query is embedded in its original language.

**Why Japanese is Generally More Accurate:**

1.  **Data Language:** All questions in the database are in Japanese.
2.  **Intra-Language Accuracy:** The Titan Embeddings model is most accurate when comparing text within the same language. This means when comparing Japanese to Japanese, the model will capture more nuanced semantic similarities.
3.  **Inter-Language Considerations:** While searching in English is possible (due to the multilingual nature of Titan), there might be a minor loss of precision. The model might not perfectly capture all of the nuances when comparing across languages.
4. **Language Model**: The Claude language model is designed to create text in Japanese. The quality of the questions and answers are best when used in Japanese.
5. **Intended Use**: The entire project is intended to be used for Japanese language learning.

**In Summary:**

*   **English Searches:** The system *can* process English search queries. Because Titan is multilingual, it will provide *some* relevant results.
*   **Japanese is Preferred:** For the most accurate and precise results, search queries should be in Japanese. This aligns with the language of the data in the database and maximizes the Titan model's ability to capture semantic meaning.
* **No Translation:** No translation is being done in this file.

This system will work in any language, but it is designed for Japanese.



# Summary of Python Data Collection Programs

**1. `backend/get_transcript.py`**

*   **Purpose:** This script's primary function is to retrieve a transcript from a YouTube video, given its URL.
*   **Process:** It uses a library to connect to YouTube and extract the transcript, handling potential errors if the transcript is unavailable.
*   **Output:** It saves the extracted transcript to a text file in the `backend/data/transcripts` directory.
*   **LLM/Models Used:** None. This script only interacts with the YouTube API.
* **Use:** Used by `structured_data.py`

**2. `backend/structured_data.py`**

*   **Purpose:** This script extracts structured data (questions, answers, and conversations) from a transcript file.
*   **Process:**
    *   Loads a transcript file.
    *   Loads a prompt from `backend/data/prompts/claude_json_prompt.md` that instructs the LLM how to extract data.
    *   Uses the **`BedrockChat`** class to interact with the **amazon.nova-micro-v1:0** model via the `generate_response` method.
    *   Sends the transcript and the prompt to the `amazon.nova-micro-v1:0` model.
    *   Receives a JSON response from `BedrockChat`.
    *   Validates the JSON response against a schema (`json_response_schema.json`).
    * If there is an error, it is raised.
    *   Saves the validated JSON data to a file named `questions_YYYYMMDD_HHMMSS.json` in the `backend/data/questions` directory.
*   **LLM/Models Used:**
    * Model ID: `amazon.nova-micro-v1:0` via `BedrockChat`
* **Use:** used by `merge_bedrock_response_runs.py`

**3. `backend/merge_bedrock_response_runs.py`**

*   **Purpose:** This script combines multiple JSON output files from `structured_data.py` into a single, merged file.
*   **Process:**
    *   It reads all `questions_YYYYMMDD_HHMMSS.json` files in the `backend/data/questions` directory.
    *   It merges the data from these files into a single JSON list.
    *   It saves the merged data to a new file named `merged_runs_YYYYMMDD_HHMMSS.json` in the same directory.
    * **Time**: Uses the date and time to create the file name.
*   **LLM/Models Used:** None. This script is purely for data management.
* **Use:** Used by `vector_store.py`

**4. `backend/vector_store.py`**

*   **Purpose:** This script loads data from the latest `merged_runs_YYYYMMDD_HHMMSS.json` file, generates embeddings for the questions, and stores them in a ChromaDB vector store. It also handles semantic searches.
*   **Process:**
    *   Uses `QuestionDataLoader.load_latest_data()` to find and load the most recent `merged_runs` file.
    *   Uses the **`BedrockEmbeddings`** class to generate embeddings for each question using the **Titan Embeddings** model.
    *   The `ChromaDBEmbedder.embed_data()` method:
        *   Connects to ChromaDB (locally).
        *   Creates or gets a collection.
        *   Adds questions, embeddings, and metadata to the collection.
    * The `ChromaDBEmbedder.semantic_search()` method:
        * Connects to ChromaDB.
        * Uses the **Titan Embeddings** model to generate a query embedding.
        * Uses ChromaDB to perform a similarity search.
        * Returns the most similar questions, along with their metadata and distances.
    *   The `main()` function shows how to load the data, add it to the store, and perform a search.
*   **LLM/Models Used:**
    * Model ID: `amazon.titan-embed-text-v1` (via `BedrockEmbeddings`) for generating embeddings.
* **Use:** Used to add the data to the ChromaDB store.

---

**Key Takeaways**

*   **`structured_data.py`** is the main script that uses an LLM to generate the structured data from the transcript.
*   **`vector_store.py`** is the main script that manages the embeddings and the vector store using an LLM.
* **`get_transcript.py`** Is used to get the raw data.
* **`merge_bedrock_response_runs.py`** Is used to merge the output data.
*  **Titan Embeddings** is used for all of the embedding generation and semantic search.
* **Claude** was used separately to create the prompt and json schema used to extract the structured data from the transcript.
* **All of the data is saved to JSON files.**
* **All of the steps prior to vector store must be run, before the vector store can be run.**
