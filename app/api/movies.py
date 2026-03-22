import logging
from flask import Blueprint, request, jsonify
from app.services.movie_service import parse_query_params, get_movies

movies_bp = Blueprint('movies', __name__)

@movies_bp.route('/movies', methods=['GET'])
def list_movies():
    """
    Fetches a paginated, filtered, and sorted list of movies.
    """
    try:
        params_or_error = parse_query_params(request.args)

        if isinstance(params_or_error, tuple):
            error_dict, status_code = params_or_error
            return jsonify(error_dict), status_code

        clean_params = params_or_error

        result = get_movies(clean_params)

        return jsonify(result), 200

    except Exception as e:
        # Log the actual exception internally for debugging
        logging.error(f"Internal server error in list_movies: {e}")
        # Return a safe, generic error message to the client
        return jsonify({"error": "Failed to fetch movies"}), 500