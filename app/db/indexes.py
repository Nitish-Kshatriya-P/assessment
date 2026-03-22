from app.db.mongo import movie_collection
from pymongo import ASCENDING, DESCENDING

def get_indexes():
    """
    Using indexes for reducing the latency for each search in the database.
    """

    movie_collection.create_index(
        [("year", ASCENDING), ("original_language", ASCENDING)]
    )

    movie_collection.create_index(
        [("vote_average", DESCENDING)]
    )

    movie_collection.create_index(
        [("release_date", ASCENDING)]
    )

    movie_collection.create_index(
        [("year", ASCENDING), ("title", ASCENDING), ("original_language", ASCENDING)], unique = True
    )
    print("Indexes created")

if __name__=="__main__":
    get_indexes()