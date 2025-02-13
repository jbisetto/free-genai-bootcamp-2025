import pytest
import json

def test_get_words(client):
    # Test successful retrieval with pagination
    response = client.get('/words?page=1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'words' in data
    assert 'total_pages' in data
    assert 'current_page' in data
    assert 'total_words' in data
    
    # Test sorting by kanji
    response = client.get('/words?sort_by=kanji&order=desc')
    assert response.status_code == 200
    data = json.loads(response.data)
    words = data['words']
    if len(words) > 1:
        assert words[0]['kanji'] >= words[1]['kanji']
    
    # Test invalid page number
    response = client.get('/words?page=0')
    assert response.status_code == 400

def test_get_word(client):
    # Test getting existing word
    response = client.get('/words/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'word' in data
    word = data['word']
    assert word['id'] == 1
    assert word['kanji'] == '始める'
    assert word['romaji'] == 'hajimeru'
    assert word['english'] == 'to begin'
    assert 'correct_count' in word
    assert 'wrong_count' in word
    assert 'groups' in word
    
    # Test not found case
    response = client.get('/words/99999')
    assert response.status_code == 404 

def test_get_words_sorting(client):
    # Test invalid sort parameter
    response = client.get('/words?sort_by=invalid')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == "Invalid sort parameter"
    
    # Test invalid order parameter
    response = client.get('/words?sort_by=kanji&order=invalid')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == "Invalid order parameter"

def test_get_words_edge_cases(client):
    # Test very large page number
    response = client.get('/words?page=999999')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['words']) == 0
    
    # Test all sorting combinations
    sort_columns = ['kanji', 'romaji', 'english', 'correct_count', 'wrong_count']
    orders = ['asc', 'desc']
    for column in sort_columns:
        for order in orders:
            response = client.get(f'/words?sort_by={column}&order={order}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'words' in data

def test_get_word_details(client):
    # Test word with no groups
    response = client.get('/words/4')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'word' in data
    assert data['word']['groups'] == []
    
    # Test word with multiple groups
    response = client.get('/words/2')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'word' in data
    assert len(data['word']['groups']) == 2
    group_names = {g['name'] for g in data['word']['groups']}
    assert 'Test Group' in group_names
    assert 'Another Group' in group_names 

def test_sorting_edge_cases(client):
    # Test SQL injection attempt in sort parameter
    response = client.get('/words?sort_by=kanji;DROP TABLE words;--')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == "Invalid sort parameter"
    
    # Test empty result set with valid sorting
    response = client.get('/words?page=999999&sort_by=kanji')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['words']) == 0
    
    # Test all valid sort combinations
    sort_fields = ['kanji', 'romaji', 'english', 'correct_count', 'wrong_count']
    orders = ['asc', 'desc']
    for field in sort_fields:
        for order in orders:
            response = client.get(f'/words?sort_by={field}&order={order}')
            assert response.status_code == 200 

def test_word_review_counts(client):
    # Create a study session
    session_data = {
        'group_id': 1,
        'study_activity_id': 1
    }
    session_response = client.post('/api/study-sessions',
                                 data=json.dumps(session_data),
                                 content_type='application/json')
    session_id = json.loads(session_response.data)['id']
    
    # Get initial word counts
    response = client.get('/words/1')
    initial_data = json.loads(response.data)
    initial_correct = initial_data['word']['correct_count']
    initial_wrong = initial_data['word']['wrong_count']
    
    # Add correct review
    review_data = {'word_id': 1, 'correct': True}
    client.post(f'/api/study-sessions/{session_id}/review',
               data=json.dumps(review_data),
               content_type='application/json')
    
    # Verify correct count increased
    response = client.get('/words/1')
    data = json.loads(response.data)
    assert data['word']['correct_count'] == initial_correct + 1
    assert data['word']['wrong_count'] == initial_wrong
    
    # Add incorrect review
    review_data['correct'] = False
    client.post(f'/api/study-sessions/{session_id}/review',
               data=json.dumps(review_data),
               content_type='application/json')
    
    # Verify wrong count increased
    response = client.get('/words/1')
    data = json.loads(response.data)
    assert data['word']['correct_count'] == initial_correct + 1
    assert data['word']['wrong_count'] == initial_wrong + 1 

def test_word_database_errors(client, app):
    with app.app_context():
        original_db = app.db
        app.db = None
        
        try:
            # Test GET /words
            response = client.get('/words')
            assert response.status_code == 500
            assert json.loads(response.data)['error'] == "Database connection error"
            
            # Test GET /words/{id}
            response = client.get('/words/1')
            assert response.status_code == 500
            assert json.loads(response.data)['error'] == "Database connection error"
            
            # Test GET /words/search
            response = client.get('/words/search?q=test')
            assert response.status_code == 500
            assert json.loads(response.data)['error'] == "Database connection error"
            
        finally:
            app.db = original_db

def test_word_validation_errors(client):
    # Test invalid search parameters
    response = client.get('/words/search?q=' + 'a'*1000)  # Very long search term
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == "Search query too long"
    
    # Test invalid pagination parameters
    response = client.get('/words?page=-1')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == "Page number must be greater than 0"
    
    response = client.get('/words?per_page=0')
    assert response.status_code == 400
    assert 'error' in json.loads(response.data)
    
    # Test invalid sort parameters
    response = client.get('/words?sort_by=invalid;DROP TABLE words;--')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == "Invalid sort parameter"

def test_word_not_found_errors(client):
    # Test non-existent word ID
    response = client.get('/words/99999')
    assert response.status_code == 404
    assert 'error' in json.loads(response.data)
    
    # Test empty search results
    response = client.get('/words/search?q=nonexistentword')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['items']) == 0 