import pytest
import os
import tempfile
from app import create_app
from lib.db import Db

@pytest.fixture
def app():
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Create the app with test config
    app = create_app({
        'TESTING': True,
        'DATABASE': db_path
    })
    
    # Set up the database
    with app.app_context():
        db = Db(database=db_path)
        cursor = db.cursor()
        
        # Create tables
        db.setup_tables(cursor)
        
        # Add test groups
        cursor.execute('''
            INSERT INTO groups (id, name, words_count) 
            VALUES 
                (1, 'Test Group', 3),
                (2, 'Another Group', 1)
        ''')
        
        # Add test words
        cursor.execute('''
            INSERT INTO words (id, kanji, romaji, english, parts) 
            VALUES 
                (1, '始める', 'hajimeru', 'to begin', '[]'),
                (2, '終わる', 'owaru', 'to end', '[]'),
                (3, '食べる', 'taberu', 'to eat', '[]'),
                (4, '走る', 'hashiru', 'to run', '[]')  -- Word without group
        ''')
        
        # Link words to groups
        cursor.execute('''
            INSERT INTO word_groups (word_id, group_id)
            VALUES 
                (1, 1),  -- Word 1 in Group 1
                (2, 1),  -- Word 2 in Group 1
                (2, 2),  -- Word 2 also in Group 2 (multiple groups)
                (3, 1)   -- Word 3 in Group 1
        ''')
        
        # Add test study activities
        cursor.execute('''
            INSERT INTO study_activities (id, name, url, preview_url)
            VALUES 
                (1, 'Test Activity', 'http://test.com', 'http://test.com/preview.jpg'),
                (2, 'Another Activity', 'http://test2.com', 'http://test2.com/preview.jpg')
        ''')
        
        # Add initial word reviews
        cursor.execute('''
            INSERT INTO word_reviews (word_id, correct_count, wrong_count)
            VALUES 
                (1, 5, 2),
                (2, 3, 1)
        ''')
        
        # Add a test study session with reviews
        cursor.execute('''
            INSERT INTO study_sessions (id, group_id, study_activity_id, created_at)
            VALUES 
                (1, 1, 1, datetime('now')),
                (2, 1, 1, datetime('now', '-1 day')),
                (3, 1, 2, datetime('now', '-2 days'))
        ''')
        
        # Add word review items
        cursor.execute('''
            INSERT INTO word_review_items (word_id, study_session_id, correct, created_at)
            VALUES 
                (1, 1, 1, datetime('now')),
                (2, 1, 0, datetime('now')),
                (3, 1, 1, datetime('now')),
                (1, 2, 1, datetime('now', '-1 day')),
                (2, 2, 1, datetime('now', '-1 day')),
                (1, 3, 0, datetime('now', '-2 days'))
        ''')
        
        db.commit()
        
    yield app
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner() 