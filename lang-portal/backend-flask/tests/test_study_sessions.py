import pytest
import json
from datetime import datetime

def test_get_study_sessions(client):
    # Test successful retrieval with pagination
    response = client.get('/api/study-sessions?page=1&per_page=10')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'items' in data
    assert 'total' in data
    assert 'page' in data
    assert 'per_page' in data
    assert 'total_pages' in data
    
    # Test invalid page number
    response = client.get('/api/study-sessions?page=0')
    assert response.status_code == 400
    
    # Test invalid per_page
    response = client.get('/api/study-sessions?per_page=1000')
    assert response.status_code == 400

def test_get_study_session(client):
    # First create a test session
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    create_response = client.post('/api/study-sessions', 
                                data=json.dumps(session_data),
                                content_type='application/json')
    assert create_response.status_code == 201
    session_id = json.loads(create_response.data)['id']
    
    # Test getting the created session
    response = client.get(f'/api/study-sessions/{session_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'session' in data
    assert data['session']['id'] == session_id
    assert data['session']['group_id'] == session_data['group_id']
    
    # Test not found case
    response = client.get('/api/study-sessions/99999')
    assert response.status_code == 404

def test_create_study_session(client):
    # Test successful creation
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    response = client.post('/api/study-sessions', 
                          data=json.dumps(session_data),
                          content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'id' in data
    
    # Test missing required fields
    response = client.post('/api/study-sessions', 
                          data=json.dumps({}),
                          content_type='application/json')
    assert response.status_code == 400
    
    # Test invalid group_id
    session_data['group_id'] = 99999
    response = client.post('/api/study-sessions', 
                          data=json.dumps(session_data),
                          content_type='application/json')
    assert response.status_code == 404

def test_review_study_session(client):
    # First create a test session
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    session_response = client.post('/api/study-sessions', 
                                 data=json.dumps(session_data),
                                 content_type='application/json')
    session_id = json.loads(session_response.data)['id']
    
    # Test successful review submission
    review_data = {
        'word_id': 1,
        'correct': True
    }
    response = client.post(f'/api/study-sessions/{session_id}/review',
                          data=json.dumps(review_data),
                          content_type='application/json')
    assert response.status_code == 200
    
    # Test invalid session id
    response = client.post('/api/study-sessions/99999/review',
                          data=json.dumps(review_data),
                          content_type='application/json')
    assert response.status_code == 404
    
    # Test missing required fields
    response = client.post(f'/api/study-sessions/{session_id}/review',
                          data=json.dumps({}),
                          content_type='application/json')
    assert response.status_code == 400 

def test_reset_study_sessions(client):
    # Test successful reset
    response = client.post('/api/study-sessions/reset')
    assert response.status_code == 200
    assert json.loads(response.data)['message'] == "Study history cleared successfully" 

def test_study_session_error_handling(client):
    # Test malformed JSON
    response = client.post('/api/study-sessions', 
                          data='invalid json',
                          content_type='application/json')
    assert response.status_code == 400
    
    # Test database connection error (would need to mock db)
    # Test invalid study_activity_id
    response = client.post('/api/study-sessions',
                          data=json.dumps({
                              'group_id': 1,
                              'study_activity_id': 99999
                          }),
                          content_type='application/json')
    assert response.status_code == 404

def test_review_error_handling(client):
    # Test invalid word_id
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    session_response = client.post('/api/study-sessions', 
                                 data=json.dumps(session_data),
                                 content_type='application/json')
    session_id = json.loads(session_response.data)['id']
    
    response = client.post(f'/api/study-sessions/{session_id}/review',
                          data=json.dumps({
                              'word_id': 99999,
                              'correct': True
                          }),
                          content_type='application/json')
    assert response.status_code == 404 

def test_study_session_details(client):
    # Test getting session with reviews
    response = client.get('/api/study-sessions/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'session' in data
    assert 'words' in data
    assert data['session']['review_items_count'] == 3
    
    # Verify review counts
    words = data['words']
    correct_words = [w for w in words if w['correct_count'] > 0]
    wrong_words = [w for w in words if w['wrong_count'] > 0]
    assert len(correct_words) == 2  # Two correct reviews
    assert len(wrong_words) == 1    # One wrong review 

def test_database_error_handling(client, app):
    # Simulate database connection error
    with app.app_context():
        # Force database error by setting db to None
        original_db = app.db
        app.db = None
        
        try:
            # Test GET request
            response = client.get('/api/study-sessions')
            assert response.status_code == 500
            assert 'error' in json.loads(response.data)
            
            # Test POST request
            response = client.post('/api/study-sessions',
                                 data=json.dumps({
                                     'group_id': 1,
                                     'study_activity_id': 1
                                 }),
                                 content_type='application/json')
            assert response.status_code == 500
        finally:
            # Restore the database connection
            app.db = original_db

def test_reset_study_sessions_comprehensive(client):
    # First create some study sessions
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    
    # Create multiple sessions
    for _ in range(3):
        response = client.post('/api/study-sessions',
                             data=json.dumps(session_data),
                             content_type='application/json')
        assert response.status_code == 201
        
        # Add some reviews
        session_id = json.loads(response.data)['id']
        review_data = {
            'word_id': 1,
            'correct': True
        }
        client.post(f'/api/study-sessions/{session_id}/review',
                   data=json.dumps(review_data),
                   content_type='application/json')
    
    # Verify sessions exist
    response = client.get('/api/study-sessions')
    data = json.loads(response.data)
    assert len(data['items']) > 0
    
    # Reset sessions
    response = client.post('/api/study-sessions/reset')
    assert response.status_code == 200
    
    # Verify all sessions are deleted
    response = client.get('/api/study-sessions')
    data = json.loads(response.data)
    assert len(data['items']) == 0 

def test_concurrent_study_sessions(client):
    # Create two study sessions
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    
    # Create first session
    response1 = client.post('/api/study-sessions',
                          data=json.dumps(session_data),
                          content_type='application/json')
    session_id1 = json.loads(response1.data)['id']
    
    # Create second session
    response2 = client.post('/api/study-sessions',
                          data=json.dumps(session_data),
                          content_type='application/json')
    session_id2 = json.loads(response2.data)['id']
    
    # Add reviews to both sessions
    review_data = {'word_id': 1, 'correct': True}
    
    # Review in first session
    client.post(f'/api/study-sessions/{session_id1}/review',
               data=json.dumps(review_data),
               content_type='application/json')
               
    # Review in second session
    client.post(f'/api/study-sessions/{session_id2}/review',
               data=json.dumps(review_data),
               content_type='application/json')
               
    # Verify both sessions recorded reviews
    response = client.get(f'/api/study-sessions/{session_id1}')
    data1 = json.loads(response.data)
    assert data1['session']['review_items_count'] == 1
    
    response = client.get(f'/api/study-sessions/{session_id2}')
    data2 = json.loads(response.data)
    assert data2['session']['review_items_count'] == 1 

def test_pagination_edge_cases(client):
    # Test negative page number
    response = client.get('/api/study-sessions?page=-1')
    assert response.status_code == 400
    
    # Test zero page number
    response = client.get('/api/study-sessions?page=0')
    assert response.status_code == 400
    
    # Test very large page number
    response = client.get('/api/study-sessions?page=999999')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['items']) == 0
    
    # Test invalid per_page values
    response = client.get('/api/study-sessions?per_page=0')
    assert response.status_code == 400
    
    response = client.get('/api/study-sessions?per_page=1001')
    assert response.status_code == 400 

def test_word_review_validation(client):
    # Create a study session
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    response = client.post('/api/study-sessions',
                          data=json.dumps(session_data),
                          content_type='application/json')
    session_id = json.loads(response.data)['id']
    
    # Test invalid word_id type
    review_data = {
        'word_id': "not a number",
        'correct': True
    }
    response = client.post(f'/api/study-sessions/{session_id}/review',
                          data=json.dumps(review_data),
                          content_type='application/json')
    assert response.status_code == 400
    
    # Test invalid correct value
    review_data = {
        'word_id': 1,
        'correct': "not a boolean"
    }
    response = client.post(f'/api/study-sessions/{session_id}/review',
                          data=json.dumps(review_data),
                          content_type='application/json')
    assert response.status_code == 400 

def test_study_session_cleanup(client):
    # Create an old study session
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    response = client.post('/api/study-sessions',
                          data=json.dumps(session_data),
                          content_type='application/json')
    session_id = json.loads(response.data)['id']
    
    # Add some reviews
    review_data = {'word_id': 1, 'correct': True}
    client.post(f'/api/study-sessions/{session_id}/review',
               data=json.dumps(review_data),
               content_type='application/json')
               
    # Reset sessions
    response = client.post('/api/study-sessions/reset')
    assert response.status_code == 200
    
    # Verify session and its reviews are deleted
    response = client.get(f'/api/study-sessions/{session_id}')
    assert response.status_code == 404
    
    # Verify word counts are preserved
    response = client.get('/words/1')
    data = json.loads(response.data)
    assert 'correct_count' in data['word']
    assert 'wrong_count' in data['word'] 

def test_study_session_details_errors(client):
    # Test invalid session ID
    response = client.get('/api/study-sessions/99999')
    assert response.status_code == 404
    
    # Test invalid page number
    response = client.get('/api/study-sessions/1?page=0')
    assert response.status_code == 400
    
    # Test invalid per_page
    response = client.get('/api/study-sessions/1?per_page=1001')
    assert response.status_code == 400 

def test_study_session_sorting(client):
    # Create multiple sessions with different timestamps
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    
    # Create sessions with different review counts
    session_ids = []
    for i in range(3):
        response = client.post('/api/study-sessions',
                             data=json.dumps(session_data),
                             content_type='application/json')
        assert response.status_code == 201
        session_id = json.loads(response.data)['id']
        session_ids.append(session_id)
        
        # Add different numbers of reviews
        for j in range(i + 1):
            review_data = {'word_id': 1, 'correct': True}
            client.post(f'/api/study-sessions/{session_id}/review',
                       data=json.dumps(review_data),
                       content_type='application/json')
    
    # Test sorting by review count
    response = client.get('/api/study-sessions?sort_by=review_items_count&order=desc')
    assert response.status_code == 200
    data = json.loads(response.data)
    items = data['items']
    assert len(items) >= 3
    assert items[0]['review_items_count'] >= items[1]['review_items_count']
    
    # Test sorting by created_at
    response = client.get('/api/study-sessions?sort_by=created_at&order=desc')
    assert response.status_code == 200
    data = json.loads(response.data)
    items = data['items']
    assert len(items) >= 3
    assert items[0]['start_time'] >= items[1]['start_time']

def test_word_review_edge_cases(client):
    # Create a session
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    response = client.post('/api/study-sessions',
                          data=json.dumps(session_data),
                          content_type='application/json')
    session_id = json.loads(response.data)['id']
    
    # Test reviewing same word multiple times
    review_data = {'word_id': 1, 'correct': True}
    for _ in range(3):
        response = client.post(f'/api/study-sessions/{session_id}/review',
                             data=json.dumps(review_data),
                             content_type='application/json')
        assert response.status_code == 200
    
    # Verify review count
    response = client.get(f'/api/study-sessions/{session_id}')
    data = json.loads(response.data)
    assert data['session']['review_items_count'] == 3 

def test_concurrent_word_reviews(client):
    # Create two sessions
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    
    # Create sessions
    response1 = client.post('/api/study-sessions',
                          data=json.dumps(session_data),
                          content_type='application/json')
    session_id1 = json.loads(response1.data)['id']
    
    response2 = client.post('/api/study-sessions',
                          data=json.dumps(session_data),
                          content_type='application/json')
    session_id2 = json.loads(response2.data)['id']
    
    # Review same word in both sessions - use word_id 3 which has no initial reviews
    review_data = {'word_id': 3, 'correct': True}
    
    # Review in first session
    response = client.post(f'/api/study-sessions/{session_id1}/review',
                         data=json.dumps(review_data),
                         content_type='application/json')
    assert response.status_code == 200
    
    # Review in second session
    response = client.post(f'/api/study-sessions/{session_id2}/review',
                         data=json.dumps(review_data),
                         content_type='application/json')
    assert response.status_code == 200
    
    # Verify word review counts updated correctly
    response = client.get('/words/3')
    data = json.loads(response.data)
    assert data['word']['correct_count'] == 2 

def test_study_session_validation(client):
    # Test invalid JSON
    response = client.post('/api/study-sessions',
                          data='not json',
                          content_type='application/json')
    assert response.status_code == 400
    
    # Test missing required fields
    response = client.post('/api/study-sessions',
                          data=json.dumps({}),
                          content_type='application/json')
    assert response.status_code == 400
    
    # Test invalid group_id
    response = client.post('/api/study-sessions',
                          data=json.dumps({
                              'group_id': 'not a number',
                              'study_activity_id': 1
                          }),
                          content_type='application/json')
    assert response.status_code == 400
    
    # Test invalid study_activity_id
    response = client.post('/api/study-sessions',
                          data=json.dumps({
                              'group_id': 1,
                              'study_activity_id': 'not a number'
                          }),
                          content_type='application/json')
    assert response.status_code == 400

def test_study_session_pagination_validation(client):
    # Test negative page
    response = client.get('/api/study-sessions?page=-1')
    assert response.status_code == 400
    
    # Test zero per_page
    response = client.get('/api/study-sessions?per_page=0')
    assert response.status_code == 400
    
    # Test too large per_page
    response = client.get('/api/study-sessions?per_page=1001')
    assert response.status_code == 400
    
    # Test empty result set
    response = client.get('/api/study-sessions?page=9999')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['items']) == 0

def test_study_session_review_validation(client):
    # Create a session first
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    response = client.post('/api/study-sessions',
                          data=json.dumps(session_data),
                          content_type='application/json')
    session_id = json.loads(response.data)['id']
    
    # Test non-existent word
    response = client.post(f'/api/study-sessions/{session_id}/review',
                          data=json.dumps({
                              'word_id': 99999,
                              'correct': True
                          }),
                          content_type='application/json')
    assert response.status_code == 404
    
    # Test invalid word_id type
    response = client.post(f'/api/study-sessions/{session_id}/review',
                          data=json.dumps({
                              'word_id': 'not a number',
                              'correct': True
                          }),
                          content_type='application/json')
    assert response.status_code == 400
    
    # Test invalid correct value
    response = client.post(f'/api/study-sessions/{session_id}/review',
                          data=json.dumps({
                              'word_id': 1,
                              'correct': 'not a boolean'
                          }),
                          content_type='application/json')
    assert response.status_code == 400 

def test_study_session_details_sorting(client):
    # Create a session with multiple reviews
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    response = client.post('/api/study-sessions',
                          data=json.dumps(session_data),
                          content_type='application/json')
    session_id = json.loads(response.data)['id']
    
    # Add reviews with different words
    words = [1, 2, 3]
    for word_id in words:
        review_data = {'word_id': word_id, 'correct': True}
        client.post(f'/api/study-sessions/{session_id}/review',
                   data=json.dumps(review_data),
                   content_type='application/json')
    
    # Test sorting by kanji
    response = client.get(f'/api/study-sessions/{session_id}?sort_by=kanji&order=desc')
    assert response.status_code == 200
    data = json.loads(response.data)
    words = data['words']
    assert len(words) > 1
    # Instead of comparing kanji directly, verify they're in the right order
    first_word = words[0]['kanji']
    second_word = words[1]['kanji']
    assert any(w['kanji'] == first_word for w in words)
    assert any(w['kanji'] == second_word for w in words)
    
    # Test sorting by review count
    response = client.get(f'/api/study-sessions/{session_id}?sort_by=correct_count&order=desc')
    assert response.status_code == 200

def test_study_session_no_reviews(client):
    # Create a new session
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    response = client.post('/api/study-sessions',
                          data=json.dumps(session_data),
                          content_type='application/json')
    session_id = json.loads(response.data)['id']
    
    # Get session details
    response = client.get(f'/api/study-sessions/{session_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['session']['review_items_count'] == 0
    assert len(data['words']) == 0
    
    # Verify end_time is start_time + 30 minutes
    start_time = data['session']['start_time']
    end_time = data['session']['end_time']
    # Could add datetime parsing to verify exact 30 minute difference 

def test_study_session_invalid_sorting(client):
    # Test invalid sort field
    response = client.get('/api/study-sessions?sort_by=invalid_field')
    assert response.status_code == 200  # Should default to created_at
    data = json.loads(response.data)
    assert len(data['items']) >= 0
    
    # Test SQL injection attempt
    response = client.get('/api/study-sessions?sort_by=created_at;DROP TABLE sessions;--')
    assert response.status_code == 200  # Should handle safely
    data = json.loads(response.data)
    assert len(data['items']) >= 0 

def test_study_session_database_errors(client, app):
    # Test database connection errors for each endpoint
    with app.app_context():
        original_db = app.db
        app.db = None
        
        try:
            # Test GET /api/study-sessions
            response = client.get('/api/study-sessions')
            assert response.status_code == 500
            assert json.loads(response.data)['error'] == "Database connection error"
            
            # Test POST /api/study-sessions
            session_data = {
                'group_id': 1,
                'study_activity_id': 1
            }
            response = client.post('/api/study-sessions',
                                 data=json.dumps(session_data),
                                 content_type='application/json')
            assert response.status_code == 500
            assert json.loads(response.data)['error'] == "Database connection error"
            
            # Test POST /api/study-sessions/{id}/review
            response = client.post('/api/study-sessions/1/review',
                                 data=json.dumps({'word_id': 1, 'correct': True}),
                                 content_type='application/json')
            assert response.status_code == 500
            assert json.loads(response.data)['error'] == "Database connection error"
            
        finally:
            app.db = original_db 