import os
import json
import boto3
from typing import List, Dict, Any, Optional
from datetime import datetime
from jsonschema import validate, ValidationError
import chromadb
from chromadb.config import Settings
import logging
from structured_data import BedrockChat
from vector_store import BedrockEmbeddings

__all__ = ['QuestionGenerator']

class QuestionGenerator:
    """
    A class for generating questions in the specified JSON format using Amazon Bedrock
    and leveraging a vector store for RAG.
    """

    def __init__(self, bedrock_model_id: str = "amazon.nova-micro-v1:0", vector_store_dir: str = None):
        """
        Initializes the QuestionGenerator with a Bedrock model and a vector store.
        """
        if vector_store_dir is None:
            # Use absolute path based on the current file's location
            vector_store_dir = os.path.join(os.path.dirname(__file__), "data", "vectorstore")
        self.bedrock_chat = BedrockChat(model_id=bedrock_model_id)
        # Load the schema
        schema_path = os.path.join(os.path.dirname(__file__), "data", "json", "schema", "generated_question_schema.json")
        with open(schema_path, "r") as f:
            self.json_schema = json.load(f)

        # Load the vector store with minimal logging
        self.client = chromadb.PersistentClient(
            path=vector_store_dir,
            settings=Settings(
                anonymized_telemetry=False,
                is_persistent=True,
                allow_reset=True
            )
        )
        # Suppress ChromaDB logs
        logging.getLogger('chromadb').setLevel(logging.ERROR)

    def generate_question_json(self, question_type: int, context: str) -> Optional[Dict]:
        """
        Generates a question in JSON format based on the given question type and context,
        and validates it against the schema. It uses RAG with the vector store.

        Args:
            question_type: The type of question to generate (1, 2, 3, or 4).
            context: The contextual theme for the question.

        Returns:
            A dictionary containing the generated question in JSON format,
            or None if an error occurs.
        """

        if question_type not in [1, 2, 3, 4]:
            print(f"Invalid question type: {question_type}. Must be 1, 2, 3, or 4.")
            return None
        
        collection_name = "JLPT_N5_question"
        # Search the vector store for similar questions
        similar_questions = self._get_similar_questions(context, question_type, collection_name)

        prompt = self._build_prompt(question_type, context, similar_questions)
        json_response_string = self.bedrock_chat.generate_response(prompt)

        if json_response_string:
            try:
                response_json = json.loads(json_response_string)
                # Validate the JSON against the schema
                validate(instance=response_json, schema=self.json_schema)
                return response_json
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                print(f"Failed JSON string: {json_response_string}")
                return None
            except ValidationError as e:
                print(f"JSON validation error: {e}")
                print(f"Failed JSON string: {json_response_string}")
                return None
        else:
            return None

    def _get_similar_questions(self, context: str, question_type:int, collection_name: str, k: int = 3) -> List[str]:
        """
        Retrieves similar questions from the vector store based on the given context.

        Args:
            context: The context to search for similar questions.
            k: The number of similar questions to retrieve.

        Returns:
            A list of strings containing similar questions.
        """
        # Get the collection
        collection = self.client.get_collection(name=collection_name)
        # Perform a similarity search using the context
        bedrock_embeddings = BedrockEmbeddings()
        query_embedding = bedrock_embeddings.generate_embedding(context)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include =['documents', 'metadatas']
        )
        # Extract questions of the correct type
        similar_questions = []
        for i in range(len(results['ids'][0])):
            result_metadata = results['metadatas'][0][i]
            question_type_metadata = 0 #default to 0
            if 'question_type' in result_metadata:
                question_type_metadata = int(result_metadata['question_type'])
            if question_type_metadata == question_type:
                similar_questions.append(results['documents'][0][i])
        
        return similar_questions

    def _build_prompt(self, question_type: int, context: str, similar_questions: List[str]) -> List[Dict[str, str]]:
        """
        Builds a prompt for the Bedrock model based on the question type, context,
        and similar questions from the vector store.

        Args:
            question_type: The type of question to generate.
            context: The contextual theme for the question.
            similar_questions: A list of similar questions from the vector store.

        Returns:
            A string containing the formatted prompt.
        """
        prompt = f"You are a helpful assistant for generating JLPT N5 level listening comprehension questions in Japanese. Generate ONE question following these strict rules:\n\n1. Use only JLPT N5 vocabulary and grammar patterns\n2. The conversation MUST contain the context needed to answer the question\n3. Questions should be simple and have ONE clear, specific correct answer\n4. The conversation should be a natural, short dialogue between 2-3 people\n5. Keep sentences short and use basic sentence structures\n6. IMPORTANT: Do NOT ask questions about numbers, amounts, times, or clock times\n7. Choose ONE of these question types: locations, objects, actions, preferences, descriptions, or reasons\n8. IMPORTANT: Always use speaker indicators in the conversation (e.g., 男の人:, 女の人:, 学生:)\n9. IMPORTANT: The conversation field must be a single line with speakers separated by spaces\n10. IMPORTANT: Generate 4 multiple choice options in Japanese, where:\n    - One option is the correct answer\n    - Three options are plausible but incorrect\n    - All options are grammatically correct and use N5 level vocabulary\n    - Options should be clearly different from each other\n\nContext: {context}\nQuestion Type: {question_type}\n\nHere are example question types (these are just examples, generate only ONE new question in Japanese):\n1. Location:\nConversation: 男の人: 田中さんはどこですか？ 女の人: 図書館で勉強しています。\nQuestion: 田中さんは今どこにいますか？\nOptions:\n1. 図書館\n2. 教室\n3. 公園\n4. レストラン\nAnswer: 図書館\n\n2. Preference:\nConversation: 学生: 山田先生、休みの日は何をしますか？ 先生: そうですね。公園で散歩するのが好きです。\nQuestion: 山田先生は休みの日に何をするのが好きですか？\nOptions:\n1. 公園で散歩する\n2. テレビを見る\n3. 本を読む\n4. 料理をする\nAnswer: 公園で散歩する\n\nHere are some similar questions for reference:\n" + '\n'.join(similar_questions) + "\n\nGenerate ONE question in this JSON format, with ALL text in Japanese:\n{\n    \"generated_question\": [\n        {\n            \"introduction\": string (simple JLPT N5 setup),\n            \"conversation\": string (natural dialogue with clear context, using speaker indicators, ALL ON ONE LINE),\n            \"question\": string (specific question with one clear answer, NO time/number questions),\n            \"options\": array (exactly 4 options in Japanese, first option must be the correct answer),\n            \"answer\": string (short, specific answer, must match the first option)\n        }\n    ]\n}\n"

        return [{
            "role": "user",
            "content": prompt
        }]
        
# Example usage:
# def main():
#     question_generator = QuestionGenerator()
#     question_type = 2
#     context = "daily conversation"
#     generator_response = question_generator.generate_question_json(question_type, context)
#     print(json.dumps(generator_response, indent=2, ensure_ascii=False, separators=(',', ': ')))

# if __name__ == "__main__":
#     main()