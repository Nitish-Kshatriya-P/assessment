import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
# from app.db.mongo import mongo_client
# from app.api.upload import upload_bp
# from app.api.movies import movies_bp 

def create_app():
    load_dotenv()

    app = Flask(__name__)
    CORS(app)

    # Access secrets
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/movie_db')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 *1024))
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'key-placeholder')

    # mongo_client.init_app(app)

    # # Registering blueprints
    # app.register_blueprint(upload_bp, url_prefix = '/api')
    # app.register_blueprint(movies_bp, url_prefix = '/api')

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Global error handler that's making each response is always in JSON."""
        code = getattr(e, 'code', 500)
        return jsonify({
            "success": False,
            "error": str(e),
            "status_code": code
        }), code
    
    @app.errorhandler(404)
    def resource_not_found(e):
        return jsonify({"error": "Resource not found"}), 404
    
    return app

