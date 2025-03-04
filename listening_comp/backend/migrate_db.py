import sqlite3
import os

def migrate_database():
    # Get the database path
    db_dir = os.path.join(os.path.dirname(__file__), "data", "sqlite")
    db_path = os.path.join(db_dir, "questions.db")
    
    try:
        # Connect to the database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if the column already exists
            cursor.execute("PRAGMA table_info(questions)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'ffmpeg_file_location' not in columns:
                # Add the new column
                cursor.execute("ALTER TABLE questions ADD COLUMN ffmpeg_file_location TEXT")
                print("Successfully added ffmpeg_file_location column")
            else:
                print("ffmpeg_file_location column already exists")
                
    except Exception as e:
        print(f"Error during migration: {str(e)}")

if __name__ == "__main__":
    migrate_database()