import csv
import io
import csv
import logging
from app.models.movie import Movie
from app.db.mongo import movie_collection
from datetime import datetime
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

logger = logging.getLogger(__name__)

def flush_chunk(buffer: list) -> dict:
    if not buffer:
        return {"inserted": 0, "duplicates": 0}

    operations = []
    for doc in buffer:
        filter_key = {
            "title": doc.get("title"),
            "release_date": doc.get("release_date"),
            "original_language": doc.get("original_language")
        }
        
        created_at_val = doc.pop("created_at", datetime.utcnow())
        
        update = {
            "$set": doc,
            "$setOnInsert": {"created_at": created_at_val}
        }
        
        operations.append(UpdateOne(filter_key, update, upsert=True))

    try:
        result = movie_collection.bulk_write(
            operations,
            ordered=False
        )
        return {
            "inserted": result.upserted_count,
            "duplicates": result.modified_count
        }
        
    except BulkWriteError as e:
        logger.error(f"BulkWriteError encountered during chunk flush: {e.details}")
        return {
            "inserted": e.details.get("nUpserted", 0), 
            "duplicates": 0
        }

def process_csv_stream(file_stream) -> dict:
    """
    Streams a CSV file, validates rows, and batches valid documents to the DB.
    """

    total_rows = 0
    inserted = 0
    duplicates = 0
    failed = 0
    error_log = []
    
    ERROR_CAP = 100
    CHUNK_SIZE = 500

    wrapped_stream = io.TextIOWrapper(file_stream, encoding="utf-8-sig", errors="replace")
    reader = csv.DictReader(wrapped_stream)

    buffer = []
    
    for row_number, row in enumerate(reader, start=1):
        total_rows += 1
        
        movie = Movie.validate_and_transform(row)
        
        if movie is None:
            failed += 1
            if len(error_log) < ERROR_CAP:
                error_log.append({
                    "row_number": row_number,
                    "reason": "validation failed: missing title or critical field"
                })
            continue
            
        buffer.append(movie.to_dict())
        
        # Batch processing
        if len(buffer) >= CHUNK_SIZE:
            result = flush_chunk(buffer)
            inserted += result["inserted"]
            duplicates += result["duplicates"]
            buffer.clear()

    if buffer:
        result = flush_chunk(buffer)
        inserted += result["inserted"]
        duplicates += result["duplicates"]
        buffer.clear()

    return {
        "total_rows_read": total_rows,
        "successfully_inserted": inserted,
        "skipped_duplicates": duplicates,
        "failed_rows": failed,
        "errors": error_log,
        "error_log_truncated": len(error_log) >= ERROR_CAP
    }
