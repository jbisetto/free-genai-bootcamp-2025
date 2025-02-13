from flask import request, jsonify, g
from flask_cors import cross_origin
import json
import math

def load(app):
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

    @app.route('/api/groups', methods=['GET'])
    @cross_origin()
    def get_groups():
        try:
            if not hasattr(app, 'db') or app.db is None:
                return jsonify({"error": "Database connection error"}), 500
            
            cursor = app.db.cursor()
            
            # Get pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            # Validate pagination
            error_response = validate_pagination(page, per_page)
            if error_response:
                return error_response
                
            offset = (page - 1) * per_page

            # Get sorting parameters
            sort_by = request.args.get('sort_by', 'name')
            order = request.args.get('order', 'asc')

            # Validate sort parameters
            valid_columns = ['name', 'words_count']
            if sort_by not in valid_columns:
                sort_by = 'name'
            if order not in ['asc', 'desc']:
                order = 'asc'

            # Get total count
            cursor.execute('SELECT COUNT(*) as count FROM groups')
            total_count = cursor.fetchone()['count']

            # Get paginated groups
            cursor.execute(f'''
                SELECT id, name, words_count
                FROM groups
                ORDER BY {sort_by} {order}
                LIMIT ? OFFSET ?
            ''', (per_page, offset))
            
            groups = cursor.fetchall()

            return jsonify({
                'items': [{
                    'id': group['id'],
                    'name': group['name'],
                    'words_count': group['words_count']
                } for group in groups],
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': math.ceil(total_count / per_page)
            })
            
        except Exception as e:
            return handle_db_error(e)

    @app.route('/api/groups', methods=['POST'])
    @cross_origin()
    def create_group():
        try:
            if not request.is_json:
                return jsonify({"error": "Invalid JSON"}), 400
                
            data = request.get_json()
            
            if not data or 'name' not in data:
                return jsonify({"error": "Name is required"}), 400
                
            cursor = app.db.cursor()
            
            # Create group
            cursor.execute('''
                INSERT INTO groups (name, words_count)
                VALUES (?, 0)
            ''', (data['name'],))
            
            group_id = cursor.lastrowid
            app.db.commit()
            
            return jsonify({"id": group_id}), 201
            
        except Exception as e:
            return handle_db_error(e)

    @app.route('/api/groups/<int:id>/words', methods=['POST'])
    @cross_origin()
    def add_word_to_group(id):
        try:
            if not request.is_json:
                return jsonify({"error": "Invalid JSON"}), 400
                
            data = request.get_json()
            
            if not data or 'word_id' not in data:
                return jsonify({"error": "word_id is required"}), 400
                
            cursor = app.db.cursor()
            
            # Verify group exists
            cursor.execute('SELECT id FROM groups WHERE id = ?', (id,))
            if not cursor.fetchone():
                return jsonify({"error": "Group not found"}), 404
                
            # Verify word exists
            cursor.execute('SELECT id FROM words WHERE id = ?', (data['word_id'],))
            if not cursor.fetchone():
                return jsonify({"error": "Word not found"}), 404
                
            # Add word to group
            cursor.execute('''
                INSERT INTO word_groups (word_id, group_id)
                VALUES (?, ?)
            ''', (data['word_id'], id))
            
            # Update word count
            cursor.execute('''
                UPDATE groups
                SET words_count = words_count + 1
                WHERE id = ?
            ''', (id,))
            
            app.db.commit()
            
            return jsonify({"message": "Word added to group"}), 200
            
        except Exception as e:
            return handle_db_error(e)

    @app.route('/api/groups/<int:id>/words/<int:word_id>', methods=['DELETE'])
    @cross_origin()
    def remove_word_from_group(id, word_id):
        try:
            cursor = app.db.cursor()
            
            # Verify group exists
            cursor.execute('SELECT id FROM groups WHERE id = ?', (id,))
            if not cursor.fetchone():
                return jsonify({"error": "Group not found"}), 404
                
            # Remove word from group
            cursor.execute('''
                DELETE FROM word_groups
                WHERE group_id = ? AND word_id = ?
            ''', (id, word_id))
            
            if cursor.rowcount > 0:
                # Update word count
                cursor.execute('''
                    UPDATE groups
                    SET words_count = words_count - 1
                    WHERE id = ?
                ''', (id,))
                
            app.db.commit()
            
            return jsonify({"message": "Word removed from group"}), 200
            
        except Exception as e:
            return handle_db_error(e)

    @app.route('/api/groups/<int:id>', methods=['DELETE'])
    @cross_origin()
    def delete_group(id):
        try:
            cursor = app.db.cursor()
            
            # Verify group exists
            cursor.execute('SELECT id FROM groups WHERE id = ?', (id,))
            if not cursor.fetchone():
                return jsonify({"error": "Group not found"}), 404
                
            # Delete word associations first
            cursor.execute('DELETE FROM word_groups WHERE group_id = ?', (id,))
            
            # Delete group
            cursor.execute('DELETE FROM groups WHERE id = ?', (id,))
            
            app.db.commit()
            
            return jsonify({"message": "Group deleted"}), 200
            
        except Exception as e:
            return handle_db_error(e)

    @app.route('/api/groups/<int:id>', methods=['GET'])
    @cross_origin()
    def get_group(id):
        try:
            cursor = app.db.cursor()

            # Get group details
            cursor.execute('''
                SELECT id, name, words_count
                FROM groups
                WHERE id = ?
            ''', (id,))
            
            group = cursor.fetchone()
            if not group:
                return jsonify({"error": "Group not found"}), 404

            # Get words in group
            cursor.execute('''
                SELECT w.*, 
                       COALESCE(wr.correct_count, 0) as correct_count,
                       COALESCE(wr.wrong_count, 0) as wrong_count
                FROM words w
                JOIN word_groups wg ON w.id = wg.word_id
                LEFT JOIN word_reviews wr ON w.id = wr.word_id
                WHERE wg.group_id = ?
            ''', (id,))
            
            words = cursor.fetchall()
            words_data = [{
                "id": word["id"],
                "kanji": word["kanji"],
                "romaji": word["romaji"],
                "english": word["english"],
                "correct_count": word["correct_count"],
                "wrong_count": word["wrong_count"]
            } for word in words]

            return jsonify({
                "group": {
                    "id": group["id"],
                    "name": group["name"],
                    "words_count": group["words_count"]
                },
                "words": words_data
            })
        except Exception as e:
            return handle_db_error(e)

    @app.route('/api/groups/<int:id>/words', methods=['GET'])
    @cross_origin()
    def get_group_words(id):
        try:
            cursor = app.db.cursor()
            
            # Get pagination parameters
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
            offset = (page - 1) * per_page

            # First, check if the group exists
            cursor.execute('SELECT name FROM groups WHERE id = ?', (id,))
            group = cursor.fetchone()
            if not group:
                return jsonify({"error": "Group not found"}), 404

            # Get total count first
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM word_groups
                WHERE group_id = ?
            ''', (id,))
            total_count = cursor.fetchone()['count']
            total_pages = math.ceil(total_count / per_page)  # Use math.ceil instead of integer division

            # Get sorting parameters
            sort_by = request.args.get('sort_by', 'kanji')
            order = request.args.get('order', 'asc')

            # Validate sort parameters
            valid_columns = ['kanji', 'romaji', 'english', 'correct_count', 'wrong_count']
            if sort_by not in valid_columns:
                sort_by = 'kanji'
            if order not in ['asc', 'desc']:
                order = 'asc'

            # Query to fetch words with pagination and sorting
            cursor.execute(f'''
                SELECT w.*, 
                       COALESCE(wr.correct_count, 0) as correct_count,
                       COALESCE(wr.wrong_count, 0) as wrong_count
                FROM words w
                JOIN word_groups wg ON w.id = wg.word_id
                LEFT JOIN word_reviews wr ON w.id = wr.word_id
                WHERE wg.group_id = ?
                ORDER BY {sort_by} {order}
                LIMIT ? OFFSET ?
            ''', (id, per_page, offset))
            
            words = cursor.fetchall()

            # Format the response
            words_data = []
            for word in words:
                words_data.append({
                    "id": word["id"],
                    "kanji": word["kanji"],
                    "romaji": word["romaji"],
                    "english": word["english"],
                    "correct_count": word["correct_count"],
                    "wrong_count": word["wrong_count"]
                })

            return jsonify({
                'words': words_data,
                'total_pages': total_pages,
                'current_page': page
            })
        except Exception as e:
            return handle_db_error(e)

    @app.route('/api/groups/<int:id>/words/raw', methods=['GET'])
    @cross_origin()
    def get_group_words_raw(id):
        try:
            cursor = app.db.cursor()
            
            # Get pagination parameters
            page = int(request.args.get('page', 1))
            words_per_page = 10
            offset = (page - 1) * words_per_page

            # Get sorting parameters
            sort_by = request.args.get('sort_by', 'kanji')
            order = request.args.get('order', 'asc')

            # Validate sort parameters
            valid_columns = ['kanji', 'romaji', 'english', 'correct_count', 'wrong_count']
            if sort_by not in valid_columns:
                sort_by = 'kanji'
            if order not in ['asc', 'desc']:
                order = 'asc'

            # First, check if the group exists
            cursor.execute('SELECT name FROM groups WHERE id = ?', (id,))
            group = cursor.fetchone()
            if not group:
                return jsonify({"error": "Group not found"}), 404

            # Query to fetch words with pagination and sorting
            cursor.execute(f'''
                SELECT w.*, 
                       COALESCE(wr.correct_count, 0) as correct_count,
                       COALESCE(wr.wrong_count, 0) as wrong_count
                FROM words w
                JOIN word_groups wg ON w.id = wg.word_id
                LEFT JOIN word_reviews wr ON w.id = wr.word_id
                WHERE wg.group_id = ?
                ORDER BY {sort_by} {order}
                LIMIT ? OFFSET ?
            ''', (id, words_per_page, offset))
            
            words = cursor.fetchall()

            # Get total words count for pagination
            cursor.execute('''
                SELECT COUNT(*) 
                FROM word_groups 
                WHERE group_id = ?
            ''', (id,))
            total_words = cursor.fetchone()[0]
            total_pages = (total_words + words_per_page - 1) // words_per_page

            # Format the response
            words_data = []
            for word in words:
                words_data.append({
                    "id": word["id"],
                    "kanji": word["kanji"],
                    "romaji": word["romaji"],
                    "english": word["english"],
                    "correct_count": word["correct_count"],
                    "wrong_count": word["wrong_count"]
                })

            return jsonify({
                'words': words_data,
                'total_pages': total_pages,
                'current_page': page
            })
        except Exception as e:
            return handle_db_error(e)

    @app.route('/api/groups/<int:id>/study_sessions', methods=['GET'])
    @cross_origin()
    def get_group_study_sessions(id):
        try:
            cursor = app.db.cursor()
            
            # Verify group exists
            cursor.execute('SELECT id FROM groups WHERE id = ?', (id,))
            if not cursor.fetchone():
                return jsonify({"error": "Group not found"}), 404
            
            # Get pagination parameters
            page = int(request.args.get('page', 1))
            sessions_per_page = 10
            offset = (page - 1) * sessions_per_page

            # Get sorting parameters
            sort_by = request.args.get('sort_by', 'created_at')
            order = request.args.get('order', 'desc')  # Default to newest first

            # Map frontend sort keys to database columns
            sort_mapping = {
                'startTime': 'created_at',
                'endTime': 'last_activity_time',
                'activityName': 'a.name',
                'groupName': 'g.name',
                'reviewItemsCount': 'review_count'
            }

            # Use mapped sort column or default to created_at
            sort_column = sort_mapping.get(sort_by, 'created_at')

            # Get total count for pagination
            cursor.execute('''
                SELECT COUNT(*)
                FROM study_sessions
                WHERE group_id = ?
            ''', (id,))
            total_sessions = cursor.fetchone()[0]
            total_pages = (total_sessions + sessions_per_page - 1) // sessions_per_page

            # Get study sessions for this group with dynamic calculations
            cursor.execute(f'''
                SELECT 
                    s.id,
                    s.group_id,
                    s.study_activity_id,
                    s.created_at as start_time,
                    (
                        SELECT MAX(created_at)
                        FROM word_review_items
                        WHERE study_session_id = s.id
                    ) as last_activity_time,
                    a.name as activity_name,
                    g.name as group_name,
                    (
                        SELECT COUNT(*)
                        FROM word_review_items
                        WHERE study_session_id = s.id
                    ) as review_count
                FROM study_sessions s
                JOIN study_activities a ON s.study_activity_id = a.id
                JOIN groups g ON s.group_id = g.id
                WHERE s.group_id = ?
                ORDER BY {sort_column} {order}
                LIMIT ? OFFSET ?
            ''', (id, sessions_per_page, offset))
            
            sessions = cursor.fetchall()
            sessions_data = []
            
            for session in sessions:
                # If there's no last_activity_time, use start_time + 30 minutes
                end_time = session["last_activity_time"]
                if not end_time:
                    end_time = cursor.execute('SELECT datetime(?, "+30 minutes")', (session["start_time"],)).fetchone()[0]
                
                sessions_data.append({
                    "id": session["id"],
                    "group_id": session["group_id"],
                    "group_name": session["group_name"],
                    "study_activity_id": session["study_activity_id"],
                    "activity_name": session["activity_name"],
                    "start_time": session["start_time"],
                    "end_time": end_time,
                    "review_items_count": session["review_count"]
                })

            return jsonify({
                'study_sessions': sessions_data,
                'total_pages': total_pages,
                'current_page': page
            })
        except Exception as e:
            return handle_db_error(e)