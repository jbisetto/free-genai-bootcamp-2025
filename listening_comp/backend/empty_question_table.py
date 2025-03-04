import sqlite3
import os
import argparse

def empty_table():
    # Get the database path from QuestionStore
    db_dir = os.path.join(os.path.dirname(__file__), "data", "sqlite")
    db_path = os.path.join(db_dir, "questions.db")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM questions")
            conn.commit()
            print(f"Successfully emptied questions table in {db_path}")
    except sqlite3.Error as e:
        print(f"Error emptying table: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--empty', action='store_true', help='Empty the questions table')
    args = parser.parse_args()
    
    if args.empty:
        empty_table()
    else:
        print("Please specify an action. Use --help for usage information.")