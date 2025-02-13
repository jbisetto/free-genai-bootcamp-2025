import pytest
import json

def test_get_groups(client):
    # Test successful retrieval with pagination
    response = client.get('/groups?page=1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'items' in data
    assert 'total' in data
    assert 'page' in data
    assert 'per_page' in data
    assert 'total_pages' in data
    assert len(data['items']) > 0
    
    # Test sorting
    response = client.get('/groups?sort_by=name&order=desc')
    assert response.status_code == 200
    data = json.loads(response.data)
    groups = data['items']
    # Verify descending order
    if len(groups) > 1:
        assert groups[0]['name'] >= groups[1]['name']
    
    # Test invalid sort parameter
    response = client.get('/groups?sort_by=invalid')
    assert response.status_code == 200  # Should default to name
    
def test_get_group(client):
    # Test getting existing group
    response = client.get('/groups/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'group' in data
    group = data['group']
    assert 'id' in group
    assert 'name' in group
    assert 'words_count' in group
    
    # Test not found case
    response = client.get('/groups/99999')
    assert response.status_code == 404

def test_get_group_words(client):
    # Test successful retrieval with pagination
    response = client.get('/groups/1/words?page=1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'words' in data
    assert 'total_pages' in data
    assert 'current_page' in data
    
    # Test sorting
    response = client.get('/groups/1/words?sort_by=kanji&order=desc')
    assert response.status_code == 200
    data = json.loads(response.data)
    words = data['words']
    # Verify descending order
    if len(words) > 1:
        assert words[0]['kanji'] >= words[1]['kanji']
    
    # Test invalid group id
    response = client.get('/groups/99999/words')
    assert response.status_code == 404

def test_get_group_words_raw(client):
    # Test successful retrieval
    response = client.get('/groups/1/words/raw')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'words' in data
    
    # Test invalid group id
    response = client.get('/groups/99999/words/raw')
    assert response.status_code == 404
    
    # Verify all words are returned (no pagination)
    response1 = client.get('/groups/1/words/raw')
    response2 = client.get('/groups/1/words')
    data1 = json.loads(response1.data)
    data2 = json.loads(response2.data)
    assert len(data1['words']) >= len(data2['words'])

def test_get_group_study_sessions(client):
    # Test successful retrieval
    response = client.get('/groups/1/study_sessions')
    assert response.status_code == 200
    
    # Test invalid group id
    response = client.get('/groups/99999/study_sessions')
    assert response.status_code == 404 

def test_group_pagination(client):
    # Test zero per_page
    response = client.get('/groups?per_page=0')
    assert response.status_code == 400
    
    # Test negative page
    response = client.get('/groups?page=-1')
    assert response.status_code == 400
    
    # Test very large per_page
    response = client.get('/groups?per_page=1000')
    assert response.status_code == 400

def test_group_words_sorting(client):
    # Test all valid sort combinations
    sort_columns = ['kanji', 'romaji', 'english', 'correct_count', 'wrong_count']
    orders = ['asc', 'desc']
    for column in sort_columns:
        for order in orders:
            response = client.get(f'/groups/1/words?sort_by={column}&order={order}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'words' in data 

def test_group_word_counts(client):
    # Test group with multiple words
    response = client.get('/groups/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['group']['words_count'] == 3
    
    # Test group with one word
    response = client.get('/groups/2')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['group']['words_count'] == 1

def test_group_words_pagination(client):
    # Test first page
    response = client.get('/groups/1/words?page=1&per_page=2')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['words']) == 2
    assert data['total_pages'] == 2
    
    # Test second page
    response = client.get('/groups/1/words?page=2&per_page=2')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['words']) == 1  # Last word on second page 

def test_group_error_handling(client):
    # Test database error
    response = client.get('/groups?sort_by=invalid;DROP TABLE groups;--')
    assert response.status_code == 200  # Should default to name sorting
    
    # Test invalid page number
    response = client.get('/groups?page=-1')
    assert response.status_code == 400
    assert json.loads(response.data)['error'] == "Page number must be greater than 0"
    
    # Test invalid per_page
    response = client.get('/groups?per_page=0')
    assert response.status_code == 400
    assert json.loads(response.data)['error'] == "Per page must be greater than 0"

def test_group_sorting_validation(client):
    # Test invalid sort field
    response = client.get('/groups?sort_by=invalid_field')
    assert response.status_code == 200  # Should default to name
    data = json.loads(response.data)
    assert len(data['items']) > 0
    
    # Test invalid order
    response = client.get('/groups?sort_by=name&order=invalid')
    assert response.status_code == 200  # Should default to asc
    data = json.loads(response.data)
    assert len(data['items']) > 0

def test_empty_group_handling(client):
    # Create an empty group
    response = client.post('/groups', 
                          data=json.dumps({'name': 'Empty Group'}),
                          content_type='application/json')
    assert response.status_code == 201
    group_id = json.loads(response.data)['id']
    
    # Get group details
    response = client.get(f'/groups/{group_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['group']['words_count'] == 0
    assert len(data['words']) == 0

def test_group_word_count_updates(client):
    # Create a new group
    response = client.post('/groups', 
                          data=json.dumps({'name': 'Test Group'}),
                          content_type='application/json')
    assert response.status_code == 201
    group_id = json.loads(response.data)['id']
    
    # Add a word to the group
    response = client.post(f'/groups/{group_id}/words',
                          data=json.dumps({'word_id': 1}),
                          content_type='application/json')
    assert response.status_code == 200
    
    # Verify word count updated
    response = client.get(f'/groups/{group_id}')
    data = json.loads(response.data)
    assert data['group']['words_count'] == 1
    
    # Remove word from group
    response = client.delete(f'/groups/{group_id}/words/1')
    assert response.status_code == 200
    
    # Verify word count updated
    response = client.get(f'/groups/{group_id}')
    data = json.loads(response.data)
    assert data['group']['words_count'] == 0

def test_group_deletion(client):
    # Create a group
    response = client.post('/groups', 
                          data=json.dumps({'name': 'Group to Delete'}),
                          content_type='application/json')
    assert response.status_code == 201
    group_id = json.loads(response.data)['id']
    
    # Add a word to the group
    response = client.post(f'/groups/{group_id}/words',
                          data=json.dumps({'word_id': 1}),
                          content_type='application/json')
    assert response.status_code == 200
    
    # Delete the group
    response = client.delete(f'/groups/{group_id}')
    assert response.status_code == 200
    
    # Verify group is deleted
    response = client.get(f'/groups/{group_id}')
    assert response.status_code == 404
    
    # Verify word still exists
    response = client.get('/words/1')
    assert response.status_code == 200 

def test_group_database_error_handling(client, app):
    # Simulate database error
    with app.app_context():
        # Force database error by setting db to None
        original_db = app.db
        app.db = None
        
        try:
            # Test GET request
            response = client.get('/groups')
            assert response.status_code == 500
            assert 'error' in json.loads(response.data)
            
            # Test POST request
            response = client.post('/groups',
                                 data=json.dumps({'name': 'Test Group'}),
                                 content_type='application/json')
            assert response.status_code == 500
            assert 'error' in json.loads(response.data)
        finally:
            # Restore the database connection
            app.db = original_db 