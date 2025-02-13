from flask import request, jsonify, g
from flask_cors import cross_origin
import json

def load(app):
    def handle_db_error(e):
        if not hasattr(app, 'db') or app.db is None:
            return jsonify({"error": "Database connection error"}), 500
        if 'closed database' in str(e) or 'no such table' in str(e):
            return jsonify({"error": "Database connection error"}), 500
        return jsonify({"error": str(e)}), 500

    # Endpoint: GET /words with pagination (50 words per page)
    @app.route('/words', methods=['GET'])
    @cross_origin()
    def get_words():
        try:
            if not hasattr(app, 'db') or app.db is None:
                return jsonify({"error": "Database connection error"}), 500
            
            cursor = app.db.cursor()

            # Get pagination parameters
            try:
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 50))
            except ValueError:
                return jsonify({"error": "Invalid pagination parameters"}), 400
            
            # Validate pagination
            if page < 1:
                return jsonify({"error": "Page number must be greater than 0"}), 400
            if per_page < 1 or per_page > 100:
                return jsonify({"error": "Invalid per_page value"}), 400
            
            offset = (page - 1) * per_page

            # Get sorting parameters
            sort_by = request.args.get('sort_by', 'kanji')
            order = request.args.get('order', 'asc')

            # Validate sort parameters
            valid_columns = ['kanji', 'romaji', 'english', 'correct_count', 'wrong_count']
            if sort_by not in valid_columns:
                return jsonify({"error": "Invalid sort parameter"}), 400
            if order not in ['asc', 'desc']:
                return jsonify({"error": "Invalid order parameter"}), 400

            # Query to fetch words with sorting
            cursor.execute(f'''
                SELECT w.id, w.kanji, w.romaji, w.english, 
                    COALESCE(r.correct_count, 0) AS correct_count,
                    COALESCE(r.wrong_count, 0) AS wrong_count
                FROM words w
                LEFT JOIN word_reviews r ON w.id = r.word_id
                ORDER BY {sort_by} {order}
                LIMIT ? OFFSET ?
            ''', (per_page, offset))

            words = cursor.fetchall()

            # Query the total number of words
            cursor.execute('SELECT COUNT(*) FROM words')
            total_words = cursor.fetchone()[0]
            total_pages = (total_words + per_page - 1) // per_page

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
                "words": words_data,
                "total_pages": total_pages,
                "current_page": page,
                "total_words": total_words
            })

        except Exception as e:
            return handle_db_error(e)
        finally:
            if hasattr(app, 'db') and app.db is not None:
                app.db.close()

    # Endpoint: GET /words/:id to get a single word with its details
    @app.route('/words/<int:word_id>', methods=['GET'])
    @cross_origin()
    def get_word(word_id):
        try:
            cursor = app.db.cursor()
            
            # Query to fetch the word and its details
            cursor.execute('''
                SELECT w.id, w.kanji, w.romaji, w.english,
                       COALESCE(r.correct_count, 0) AS correct_count,
                       COALESCE(r.wrong_count, 0) AS wrong_count,
                       GROUP_CONCAT(DISTINCT g.id || '::' || g.name) as groups
                FROM words w
                LEFT JOIN word_reviews r ON w.id = r.word_id
                LEFT JOIN word_groups wg ON w.id = wg.word_id
                LEFT JOIN groups g ON wg.group_id = g.id
                WHERE w.id = ?
                GROUP BY w.id
            ''', (word_id,))
            
            word = cursor.fetchone()
            
            if not word:
                return jsonify({"error": "Word not found"}), 404
            
            # Parse the groups string into a list of group objects
            groups = []
            if word["groups"]:
                for group_str in word["groups"].split(','):
                    group_id, group_name = group_str.split('::')
                    groups.append({
                        "id": int(group_id),
                        "name": group_name
                    })
            
            return jsonify({
                "word": {
                    "id": word["id"],
                    "kanji": word["kanji"],
                    "romaji": word["romaji"],
                    "english": word["english"],
                    "correct_count": word["correct_count"],
                    "wrong_count": word["wrong_count"],
                    "groups": groups
                }
            })
            
        except Exception as e:
            return handle_db_error(e)

    @app.route('/words/search', methods=['GET'])
    @cross_origin()
    def search_words():
        try:
            # Validate search query
            q = request.args.get('q', '')
            if len(q) > 100:  # Limit search query length
                return jsonify({"error": "Search query too long"}), 400
            
            # Validate sort parameters
            sort_by = request.args.get('sort_by', 'kanji')
            if sort_by and sort_by not in ['kanji', 'romaji', 'english', 'correct_count', 'wrong_count']:
                return jsonify({"error": "Invalid sort parameter"}), 400
            
            # Validate pagination
            try:
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 10))
            except ValueError:
                return jsonify({"error": "Invalid pagination parameters"}), 400
            
            if page < 1:
                return jsonify({"error": "Page number must be greater than 0"}), 400
            if per_page < 1 or per_page > 100:
                return jsonify({"error": "Invalid per_page value"}), 400
            
            cursor = app.db.cursor()
            
            # Get total count
            cursor.execute('''
                SELECT COUNT(*) FROM words 
                WHERE kanji LIKE ? OR romaji LIKE ? OR english LIKE ?
            ''', (f'%{q}%', f'%{q}%', f'%{q}%'))
            total_count = cursor.fetchone()[0]
            
            # Even if no results, return 200 with empty list
            if total_count == 0:
                return jsonify({
                    'items': [],
                    'total': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                }), 200
            
            # Get paginated results
            cursor.execute('''
                SELECT w.*, COALESCE(wr.correct_count, 0) as correct_count,
                       COALESCE(wr.wrong_count, 0) as wrong_count
                FROM words w
                LEFT JOIN word_reviews wr ON w.id = wr.word_id
                WHERE w.kanji LIKE ? OR w.romaji LIKE ? OR w.english LIKE ?
                LIMIT ? OFFSET ?
            ''', (f'%{q}%', f'%{q}%', f'%{q}%', per_page, (page - 1) * per_page))
            
            words = cursor.fetchall()
            
            return jsonify({
                'items': [{
                    'id': word['id'],
                    'kanji': word['kanji'],
                    'romaji': word['romaji'],
                    'english': word['english'],
                    'correct_count': word['correct_count'],
                    'wrong_count': word['wrong_count']
                } for word in words],
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            }), 200
            
        except Exception as e:
            return handle_db_error(e)