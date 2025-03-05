import sqlite3
import json
from datetime import datetime
import os

class QuestionStore:
    def __init__(self):
        # Store SQLite database in backend/data/sqlite
        db_dir = os.path.join(os.path.dirname(__file__), "data", "sqlite")
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = os.path.join(db_dir, "questions.db")
        self._init_db()

    def _init_db(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    context TEXT NOT NULL,
                    question_data TEXT NOT NULL,
                    ffmpeg_file_location TEXT
                )
            """)

    def save_question(self, context: str, question_data: dict, ffmpeg_file_location: str = None) -> int:
        """Save a new question to the database"""
        print("\n=== Save_Question ===")
        print(f"Context: {context}")
        print(f"introduction Data: {question_data.get('introduction', '')}")
        print(f"conversation Data: {question_data.get('conversation', '')}")
        print(f"question Data: {question_data.get('question', '')}")
        print(f"Audio File: {ffmpeg_file_location}")
        print("===============================\n")
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO questions (timestamp, context, question_data, ffmpeg_file_location) VALUES (?, ?, ?, ?)",
                (datetime.now().isoformat(), context, json.dumps(question_data), ffmpeg_file_location)
            )
            return cursor.lastrowid

    def get_all_questions(self):
        """Retrieve all questions ordered by timestamp"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM questions ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            return [{
                'id': row['id'],
                'timestamp': row['timestamp'],
                'context': row['context'],
                'question_data': json.loads(row['question_data']),
                'ffmpeg_file_location': row['ffmpeg_file_location']
            } for row in rows]

    def get_question(self, question_id: int):
        """Retrieve a specific question by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'context': row['context'],
                    'question_data': json.loads(row['question_data']),
                    'ffmpeg_file_location': row['ffmpeg_file_location']
                }
            return None
    def update_question_audio(self, question_id: int, audio_file: str):
        """Update a question with its audio file location"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE questions SET ffmpeg_file_location = ? WHERE id = ?",
                (audio_file, question_id)
            )
            return cursor.rowcount > 0