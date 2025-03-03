import os
import json
import boto3 #import boto3
from typing import List, Dict, Any, Optional
from datetime import datetime
import chromadb  # Import ChromaDB
from chromadb.config import Settings
from structured_data import BedrockChat #Removed BedrockEmbeddings import


# Model ID for Amazon Bedrock
MODEL_ID = "amazon.nova-micro-v1:0"
# Model ID for Amazon Bedrock Titan Embeddings Model
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v1"

class BedrockEmbeddings:
    def __init__(self, model_id: str = EMBEDDING_MODEL_ID):
        """Initialize Bedrock embeddings client"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate an embedding using Amazon Bedrock"""
        try:
            body = json.dumps({"inputText": text})
            response = self.bedrock_client.invoke_model(
                body=body,
                modelId=self.model_id,
                accept="application/json",
                contentType="application/json"
            )
            response_body = json.loads(response.get('body').read())
            return response_body.get('embedding')
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            return None

class ChromaDBEmbedder:
    def __init__(self, model_id: str = MODEL_ID, db_directory: str = "backend/data/vectorstore"):
        """Initialize ChromaDB embedder with Bedrock model and local persistence."""
        self.bedrock_chat = BedrockChat(model_id)
        self.bedrock_embeddings = BedrockEmbeddings()
        self.db_directory = db_directory
        self.client = chromadb.PersistentClient(path=self.db_directory, settings=Settings(allow_reset=True))

    def embed_data(self, collection_name: str, data: List[Dict[str, Any]]) -> None:
        """Embed structured data into ChromaDB."""
        #Get or create the collection
        collection = self.client.get_or_create_collection(name=collection_name)

        ids = []
        embeddings = []
        metadatas = []

        for entry in data:
            # Generate embedding using Bedrock
            embedding = self.bedrock_embeddings.generate_embedding(entry['question']) #<--- Changed this line
            ids.append(str(entry['id']))
            embeddings.append(embedding) #<--- Changed this line
            metadatas.append({"introduction": entry['introduction']})
            
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def semantic_search(self, collection_name:str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search in ChromaDB."""
        #Get the collection
        collection = self.client.get_collection(name=collection_name)
        query_embedding = self.bedrock_embeddings.generate_embedding(query) #<--- Changed this line

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return results

class QuestionDataLoader:
    @staticmethod
    def load_latest_data(directory: str) -> List[Dict[str, Any]]:
        """Load the latest merged_runs JSON file from the specified directory."""
        latest_file = None
        latest_timestamp = datetime.min

        for filename in os.listdir(directory):
            if 'merged_runs' in filename and filename.endswith('.json'):
                # Extract timestamp from filename
                parts = filename.split('_')
                if len(parts) >= 5:
                    date_str = parts[3]
                    time_str = parts[4].replace(".json", "")
                    timestamp_str = f"{date_str}_{time_str}"
                    timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')

                    if timestamp > latest_timestamp:
                        latest_timestamp = timestamp
                        latest_file = filename
                else:
                    print(f"Unexpected filename format: {filename}. Skipping file.")
                    continue

        if latest_file:
            with open(os.path.join(directory, latest_file), 'r', encoding='utf-8') as json_file:
                json_data = json.load(json_file)

                #Check if the file is formated correctly
                if not isinstance(json_data, list):
                    raise ValueError(f"The data in '{latest_file}' is not a list of records.")
                
                return json_data
        else:
            raise FileNotFoundError("No merged_runs JSON file found in the specified directory.")

def main():
    # Load the latest data file
    data_directory = 'backend/data/questions/'
    data_loader = QuestionDataLoader()
    questions_data = data_loader.load_latest_data(data_directory)

    # Create an instance of ChromaDBEmbedder with a specified local directory
    chroma_db_directory = "backend/data/vectorstore"  # Choose your preferred directory
    embedder = ChromaDBEmbedder(db_directory=chroma_db_directory)

    # Embed the structured data into ChromaDB
    collection_name = "JLPT_N5_question"  # Choose a name for your collection
    embedder.embed_data(collection_name, questions_data)
    print(f"Questions embedded successfully into ChromaDB in directory: {chroma_db_directory}.")

    # Perform a semantic search
    user_query = input("Enter a question to search for similar questions: ")
    search_results = embedder.semantic_search(collection_name, user_query)

    # Display the search results
    print("Search Results:")
    for i in range(len(search_results['ids'][0])):
        result_id = search_results['ids'][0][i]
        result_distance = search_results['distances'][0][i]
        result_metadata = search_results['metadatas'][0][i]

        print(f"ID: {result_id}, Distance: {result_distance}")
        # Print all metadata key-value pairs
        print("Metadata:")
        for key, value in result_metadata.items():
            print(f"  {key}: {value}")
        print("-" * 20)  # Separator between results


if __name__ == "__main__":
    main()
