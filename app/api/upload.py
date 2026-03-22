import os
import logging
from flask import Blueprint, request, jsonify
from app.services.csv_processor import process_csv_stream

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload_bp', __name__)

def validate_upload_file(file_object):
    if not file_object:
        return None, (jsonify({"error": "No file provided"}), 400)

    if file_object.filename == "":
        return None, (jsonify({"error": "No file selected"}), 400)

    _, ext = os.path.splitext(file_object.filename)
    if ext.lower() not in [".csv"]:
        return None, (jsonify({"error": "Only CSV files accepted"}), 415)

    valid_content_types = ["text/csv", "application/csv", "application/octet-stream"]
    if file_object.mimetype not in valid_content_types:
        return None, (jsonify({"error": "Invalid content type"}), 415)

    return file_object, None

@upload_bp.route('/upload', methods=['POST'])
def upload_movies():
    """
    Thin route handler for processing movie CSV uploads.
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part in request"}), 400
            
        uploaded_file = request.files['file']
        
        valid_file, error_response = validate_upload_file(uploaded_file)
        if error_response:
            return error_response  
            
        summary = process_csv_stream(valid_file.stream)
        
        return jsonify(summary), 200
        
    except Exception:
        logger.exception("Unexpected error during file upload processing")
        return jsonify({"error": "Upload processing failed"}), 500