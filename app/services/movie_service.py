import math
from pymongo import ASCENDING, DESCENDING
from app.db.mongo import movie_collection
from datetime import datetime

ALLOWED_SORT_FIELDS = {
    "release_date": "year",
    "ratings" : "vote_average"
}

def sanitise_document(doc: dict) -> dict:
    """
    Recursively checks a document for datetime objects and converts them to ISO 8601 strings for safe JSON serialization.
    """
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
        elif isinstance(value, list):
            doc[key] = [
                item.isoformat() if isinstance(item, datetime) else item
                for item in value
            ]
    return doc

def sanitise_documents(docs: list) -> list:
    """
    Applies the datetime sanitisation to a full list of documents.
    """
    return [sanitise_document(doc) for doc in docs]

def parse_query_params(args: dict):
    """
    Validates and cleans the raw request arguments.
    """
    try:
        page = int(args.get("page", 1))
        if page < 1:
            return {"error": "page must be >= 1"}, 400

        limit = int(args.get("limit", 10))
        if limit < 1 or limit > 100:
            return {"error": "limit must be between 1 and 100"}, 400

        year = args.get("year")
        if year is not None:
            year = int(year)
            if year < 1888 or year > 2100:
                return {"error": "invalid year range (1888-2100)"}, 400

        language = args.get("language")
        if language:
            language = language.strip().lower()[:2]

        sort_by = args.get("sort_by")
        if sort_by and sort_by not in ALLOWED_SORT_FIELDS:
            return {"error": "sort_by must be release_date or vote_average"}, 400
        
        db_sort_field = ALLOWED_SORT_FIELDS.get(sort_by) if sort_by else None

        order = args.get("order", "desc").lower()
        if order not in ["asc", "desc"]:
            return {"error": "order must be asc or desc"}, 400
        
        sort_direction = ASCENDING if order == "asc" else DESCENDING

        return {
            "page": page,
            "limit": limit,
            "year": year,
            "language": language,
            "sort_by": db_sort_field,
            "sort_direction": sort_direction
        }

    except ValueError:
        return {"error": "Invalid data type provided for numeric fields"}, 400

def build_filter(year=None, language=None):
    """
    Dynamically construct a MongoDB filter object based on the provided arguments.
    """
    filter_dict = {}

    if year is not None:
        filter_dict["year"] = year

    if language is not None:
        filter_dict["original_language"] = language

    return filter_dict

def get_movies(params: dict) -> dict:
    """
    Fetches the movies and total count.
    """
    filter_dict = build_filter(params.get("year"), params.get("language"))

    if params.get("sort_by") is not None:
        sort_tuple = (params["sort_by"], params["sort_direction"])
    else:
        sort_tuple = ("_id", DESCENDING)

    skip = (params["page"] - 1) * params["limit"]

    cursor = movie_collection.find(
        filter_dict,
        {"_id": 0} 
    )

    if sort_tuple:
        cursor = cursor.sort(*sort_tuple)
        
    cursor = cursor.skip(skip).limit(params["limit"])
    documents = list(cursor)

    total = movie_collection.count_documents(filter_dict)

    total_pages = math.ceil(total / params["limit"])
    has_next = params["page"] < total_pages
    has_prev = params["page"] > 1

    return {
        "success": True,
        "data": documents,
        "pagination": {
            "page": params["page"],
            "limit": params["limit"],
            "total_documents": total,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev
        }
    }