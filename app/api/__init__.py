import os
from flask import Flask, jsonify, current_app
from dotenv import load_dotenv
from flask_cors import CORS
from app.config import Config
from app.db.mongo import mongo_client
from app.api.upload import upload_bp
from app.api.movies import movies_bp

def create_app():
    load_dotenv()

    app = Flask(__name__)
    CORS(app)

    # Access secrets
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/movie_db')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 *1024))
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'key-placeholder')

    app.config.from_object(Config)

    # Registered blueprints
    app.register_blueprint(upload_bp, url_prefix = '/api')
    app.register_blueprint(movies_bp, url_prefix = '/api')

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Global error handler that makes sure each response is always in JSON."""
        code = getattr(e, 'code', 500)
        
        if code >= 500:
            current_app.logger.exception(e)
            return jsonify({
                "success": False, 
                "error": "Unexpected error occurred.",
                "status_code": code
            }), code

        error_message = str(e)
        
        if code == 413:
            max_bytes = current_app.config.get('MAX_CONTENT_LENGTH', 0)
            max_mb = max_bytes // (1024 * 1024)
            error_message = f"File too large. Maximum allowed size is {max_mb} MB"
            
        elif code == 415:
            error_message = "Unsupported file type. Only CSV files are accepted."
            
        elif code == 400:
            error_message = "Bad request. Please check your input."

        return jsonify({
            "success": False,
            "error": error_message,
            "status_code": code
        }), code
    
    @app.errorhandler(404)
    def resource_not_found(e):
        return jsonify({"error": "Resource not found"}), 404
    
    return app

