from flask import request, jsonify, g
from flask_cors import cross_origin
from datetime import datetime
import math

def load(app):
  # todo /study_sessions POST

  def validate_pagination(page, per_page):
    if page < 1:
      return jsonify({"error": "Page number must be greater than 0"}), 400
    if per_page < 1:
      return jsonify({"error": "Per page must be greater than 0"}), 400
    if per_page > 100:
      return jsonify({"error": "Per page must be less than or equal to 100"}), 400
    return None

  def handle_db_error(e):
    if not hasattr(app, 'db') or app.db is None:
        return jsonify({"error": "Database connection error"}), 500
    if 'closed database' in str(e) or 'no such table' in str(e):
        return jsonify({"error": "Database connection error"}), 500
    return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions', methods=['GET'])
  @cross_origin()
  def get_study_sessions():
    try:
      if not hasattr(app, 'db') or app.db is None:
        return jsonify({"error": "Database connection error"}), 500
            
      cursor = app.db.cursor()
      
      # Get pagination parameters
      page = request.args.get('page', 1, type=int)
      per_page = request.args.get('per_page', 10, type=int)
      
      # Validate pagination parameters
      error_response = validate_pagination(page, per_page)
      if error_response:
        return error_response
      
      offset = (page - 1) * per_page

      # Get sorting parameters
      sort_by = request.args.get('sort_by', 'created_at')
      order = request.args.get('order', 'desc')

      # Map frontend sort keys to database columns
      sort_mapping = {
          'review_items_count': 'review_items_count',
          'created_at': 'ss.created_at',
          'group_name': 'g.name',
          'activity_name': 'sa.name'
      }

      # Use mapped sort column or default to created_at
      sort_column = sort_mapping.get(sort_by, 'ss.created_at')
      
      # Get total count
      cursor.execute('''
        SELECT COUNT(*) as count 
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
      ''')
      total_count = cursor.fetchone()['count']

      # Get paginated sessions
      cursor.execute(f'''
        SELECT 
          ss.id,
          ss.group_id,
          g.name as group_name,
          sa.id as activity_id,
          sa.name as activity_name,
          ss.created_at,
          COUNT(wri.id) as review_items_count
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
        LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
        GROUP BY ss.id
        ORDER BY {sort_column} {order}
        LIMIT ? OFFSET ?
      ''', (per_page, offset))
      sessions = cursor.fetchall()

      return jsonify({
        'items': [{
          'id': session['id'],
          'group_id': session['group_id'],
          'group_name': session['group_name'],
          'activity_id': session['activity_id'],
          'activity_name': session['activity_name'],
          'start_time': session['created_at'],
          'end_time': session['created_at'],
          'review_items_count': session['review_items_count']
        } for session in sessions],
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': math.ceil(total_count / per_page)
      })
    except Exception as e:
      return handle_db_error(e)

  @app.route('/api/study-sessions/<id>', methods=['GET'])
  @cross_origin()
  def get_study_session(id):
    try:
      cursor = app.db.cursor()
      
      # Get pagination parameters
      page = request.args.get('page', 1, type=int)
      per_page = request.args.get('per_page', 10, type=int)
      
      # Validate pagination parameters
      error_response = validate_pagination(page, per_page)
      if error_response:
        return error_response
            
      offset = (page - 1) * per_page
      
      # Get session details
      cursor.execute('''
        SELECT 
          ss.id,
          ss.group_id,
          g.name as group_name,
          sa.id as activity_id,
          sa.name as activity_name,
          ss.created_at,
          COUNT(wri.id) as review_items_count
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
        LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
        WHERE ss.id = ?
        GROUP BY ss.id
      ''', (id,))
      
      session = cursor.fetchone()
      if not session:
        return jsonify({"error": "Study session not found"}), 404

      # Get the words reviewed in this session
      cursor.execute('''
        SELECT 
          w.*,
          COUNT(CASE WHEN wri.correct = 1 THEN 1 END) as correct_count,
          COUNT(CASE WHEN wri.correct = 0 THEN 1 END) as wrong_count
        FROM words w
        JOIN word_review_items wri ON wri.word_id = w.id
        WHERE wri.study_session_id = ?
        GROUP BY w.id
        ORDER BY w.kanji
        LIMIT ? OFFSET ?
      ''', (id, per_page, offset))
      
      words = cursor.fetchall()

      return jsonify({
        'session': {
          'id': session['id'],
          'group_id': session['group_id'],
          'group_name': session['group_name'],
          'activity_id': session['activity_id'],
          'activity_name': session['activity_name'],
          'start_time': session['created_at'],
          'end_time': session['created_at'],
          'review_items_count': session['review_items_count']
        },
        'words': [{
          'id': word['id'],
          'kanji': word['kanji'],
          'romaji': word['romaji'],
          'english': word['english'],
          'correct_count': word['correct_count'],
          'wrong_count': word['wrong_count']
        } for word in words]
      })
    except Exception as e:
      return handle_db_error(e)

  # todo POST /study_sessions/:id/review

  @app.route('/api/study-sessions/reset', methods=['POST'])
  @cross_origin()
  def reset_study_sessions():
    try:
      cursor = app.db.cursor()
      
      # First delete all word review items since they have foreign key constraints
      cursor.execute('DELETE FROM word_review_items')
      
      # Then delete all study sessions
      cursor.execute('DELETE FROM study_sessions')
      
      app.db.commit()
      
      return jsonify({"message": "Study history cleared successfully"}), 200
    except Exception as e:
      return handle_db_error(e)

  @app.route('/api/study-sessions', methods=['POST'])
  @cross_origin()
  def create_study_session():
    try:
        # First check if request is JSON
        if not request.is_json:
            return jsonify({"error": "Invalid JSON"}), 400
            
        # Then try to parse JSON
        try:
            data = request.get_json()
        except:
            return jsonify({"error": "Invalid JSON format"}), 400
        
        # Validate required fields
        if not data or 'group_id' not in data or 'study_activity_id' not in data:
            return jsonify({"error": "Missing required fields"}), 400
            
        # Validate types
        try:
            group_id = int(data['group_id'])
            study_activity_id = int(data['study_activity_id'])
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid data types"}), 400
            
        # Now check if db is available
        if not hasattr(app, 'db') or app.db is None:
            return jsonify({"error": "Database connection error"}), 500
            
        cursor = app.db.cursor()
        
        # Verify group exists
        cursor.execute('SELECT id FROM groups WHERE id = ?', (group_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Group not found"}), 404
            
        # Verify study activity exists
        cursor.execute('SELECT id FROM study_activities WHERE id = ?', (study_activity_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Study activity not found"}), 404
            
        # Create study session
        cursor.execute('''
            INSERT INTO study_sessions (group_id, study_activity_id, created_at)
            VALUES (?, ?, datetime('now'))
        ''', (group_id, study_activity_id))
        
        session_id = cursor.lastrowid
        app.db.commit()
        
        return jsonify({"id": session_id}), 201
        
    except Exception as e:
        # Only return 500 for unexpected errors
        if isinstance(e, (ValueError, TypeError)):
            return jsonify({"error": str(e)}), 400
        return handle_db_error(e)

  @app.route('/api/study-sessions/<id>/review', methods=['POST'])
  @cross_origin()
  def review_study_session(id):
    try:
        if not request.is_json:
            return jsonify({"error": "Invalid JSON"}), 400
            
        data = request.get_json()
        
        # Validate required fields
        if not data or 'word_id' not in data or 'correct' not in data:
            return jsonify({"error": "Missing required fields"}), 400
            
        # Validate types
        try:
            word_id = int(data['word_id'])
        except (ValueError, TypeError):
            return jsonify({"error": "word_id must be a number"}), 400
            
        if not isinstance(data['correct'], bool):
            return jsonify({"error": "correct must be a boolean"}), 400
            
        correct = data['correct']

        cursor = app.db.cursor()
        
        # Verify session exists
        cursor.execute('SELECT id FROM study_sessions WHERE id = ?', (id,))
        if not cursor.fetchone():
            return jsonify({"error": "Study session not found"}), 404
        
        # Verify word exists
        cursor.execute('SELECT id FROM words WHERE id = ?', (word_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Word not found"}), 404
        
        try:
            # Insert new word review item
            cursor.execute('''
                INSERT INTO word_review_items (word_id, study_session_id, correct, created_at)
                VALUES (?, ?, ?, datetime('now'))
            ''', (word_id, id, correct))
            
            # Get current review counts
            cursor.execute('''
                SELECT correct_count, wrong_count 
                FROM word_reviews 
                WHERE word_id = ?
            ''', (word_id,))
            
            result = cursor.fetchone()
            if result:
                # Update existing counts
                current_correct = result['correct_count']
                current_wrong = result['wrong_count']
                cursor.execute('''
                    UPDATE word_reviews 
                    SET correct_count = ?,
                        wrong_count = ?
                    WHERE word_id = ?
                ''', (current_correct + (1 if correct else 0), 
                     current_wrong + (0 if correct else 1), 
                     word_id))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO word_reviews (word_id, correct_count, wrong_count)
                    VALUES (?, ?, ?)
                ''', (word_id, 1 if correct else 0, 0 if correct else 1))
            
            app.db.commit()
            
            return jsonify({"message": "Word review recorded successfully"}), 200
            
        except Exception as e:
            app.db.rollback()
            raise e
            
    except Exception as e:
        return handle_db_error(e)