from flask import Flask, g, request, jsonify
from flask_cors import CORS
import logging
import sys  # Add this import
from werkzeug.serving import WSGIRequestHandler

from lib.db import Db

import routes.words
import routes.groups
import routes.study_sessions
import routes.dashboard
import routes.study_activities

def get_allowed_origins(app):
    try:
        cursor = app.db.cursor()
        cursor.execute('SELECT url FROM study_activities')
        urls = cursor.fetchall()
        # Convert URLs to origins (e.g., https://example.com/app -> https://example.com)
        origins = set()
        for url in urls:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url['url'])
                origin = f"{parsed.scheme}://{parsed.netloc}"
                origins.add(origin)
            except:
                continue
        return list(origins) if origins else ["*"]
    except:
        return ["*"]  # Fallback to allow all origins if there's an error

def create_app(test_config=None):
    app = Flask(__name__)
    
    if test_config is None:
        app.config.from_mapping(
            DATABASE='words.db'
        )
    else:
        app.config.update(test_config)
    
    # Initialize database
    app.db = Db(database=app.config['DATABASE'])
    
    # Simple CORS configuration for development
    CORS(app, 
         origins="*",
         allow_headers=["Content-Type", "Authorization"],
         expose_headers=["Content-Type", "Authorization"],
         supports_credentials=True)

    # Close database connection
    @app.teardown_appcontext
    def close_db(exception):
        app.db.close()

    # load routes
    routes.words.load(app)
    routes.groups.load(app)
    routes.study_sessions.load(app)
    routes.dashboard.load(app)
    routes.study_activities.load(app)
    
    return app

app = create_app()

# Set up more verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Force output to stdout
    ]
)
logger = logging.getLogger(__name__)

# Add a test route to verify logging
@app.route('/api/test')
def test_logging():
    logger.debug("This is a test debug message")
    logger.info("This is a test info message")
    logger.warning("This is a test warning message")
    print("Direct print statement")  # Add a direct print for testing
    return jsonify({"message": "Test successful"})

WSGIRequestHandler.protocol_version = "HTTP/1.1"  # Add this line at the top

@app.before_request
def log_request():
    # Use werkzeug's logger which we know is working
    app.logger.info("=== Incoming Request ===")
    app.logger.info(f"Path: {request.path}")
    app.logger.info(f"Method: {request.method}")
    app.logger.info(f"Origin: {request.headers.get('Origin')}")
    app.logger.info(f"Headers: {dict(request.headers)}")
    app.logger.info(f"Data: {request.get_data()}")
    app.logger.info("=====================")

@app.after_request
def log_response(response):
    app.logger.info("=== Response ===")
    app.logger.info(f"Status: {response.status}")
    app.logger.info(f"Headers: {dict(response.headers)}")
    app.logger.info("================")
    return response

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)