import pytest
from run import app  # <-- Importing app directly from your run.py file!
from app.db.mongo import movie_collection # <-- Using your exact collection name

@pytest.fixture(scope="module")
def test_client():
    """
    Creates a test client for the Flask app.
    Runs once per test module.
    """
    app.config['TESTING'] = True
    
    with app.test_client() as testing_client:
        yield testing_client

@pytest.fixture(scope="module", autouse=True)
def seed_database():
    """
    Seeds the database with 20 test documents before tests run.
    Cleans up (drops) the collection after the tests finish.
    """
    # Grab the database object directly from your existing collection
    db = movie_collection.database
    test_collection = db["test_movies"]
    
    # Temporarily override the real collection exactly where the API uses it 
    import app.services.movie_service as movie_service
    original_collection = movie_service.movie_collection
    movie_service.movie_collection = test_collection

    # 1. Clear any old test data
    test_collection.delete_many({})

    # 2. Insert 20 known test documents
    test_docs = []
    for i in range(1, 21):
        # 5 movies from 1995, 15 from 2024
        year = 1995 if i <= 5 else 2024
        # Even numbers are English ('en'), odd are French ('fr')
        lang = "en" if i % 2 == 0 else "fr"
        # Ratings cycle from 1.0 to 10.0
        rating = float(i % 10) + 1.0 

        test_docs.append({
            "title": f"Test Movie {i}",
            "year": year,
            "original_language": lang,
            "vote_average": rating,
            "release_date": f"{year}-01-01T00:00:00"
        })
    
    test_collection.insert_many(test_docs)

    # Yield hands control over to the tests
    yield

    # 3. Teardown: Drop the test collection after all tests are done
    test_collection.drop()
    
    # Restore the original collection
    movie_service.movie_collection = original_collection


# --- 🧪 TEST CASES ---

def test_1_default_pagination(test_client):
    """Test 1 — Default pagination (no filters)"""
    response = test_client.get('/api/movies')
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Assert default limit
    assert len(data['data']) == 10
    
    # Assert pagination metadata exists
    pagination = data['pagination']
    
    # FIXED: Changed 'current_page' to 'page'
    expected_keys = ['page', 'limit', 'total_documents', 'total_pages', 'has_next', 'has_prev']
    for key in expected_keys:
        assert key in pagination

def test_2_custom_limit(test_client):
    """Test 2 — Custom limit returns exact amount"""
    response = test_client.get('/api/movies?limit=5')
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['data']) == 5
    assert data['pagination']['limit'] == 5

def test_3_year_filter(test_client):
    """Test 3 — Filter by year returns only matching movies"""
    response = test_client.get('/api/movies?year=1995')
    
    assert response.status_code == 200
    data = response.get_json()
    
    # We seeded exactly 5 movies from 1995
    assert len(data['data']) == 5
    for movie in data['data']:
        assert movie['year'] == 1995

def test_4_language_filter(test_client):
    """Test 4 — Filter by language returns only matching movies"""
    # Note: 'english' gets parsed to 'en' in your backend logic!
    response = test_client.get('/api/movies?language=english')
    
    assert response.status_code == 200
    data = response.get_json()
    
    # We seeded 10 'en' movies (the even numbers)
    assert len(data['data']) == 10
    for movie in data['data']:
        assert movie['original_language'] == 'en'

def test_5_sort_descending_vote_average(test_client):
    """Test 5 — Sort by vote_average descending"""
    # Changed to 'ratings' to match your ALLOWED_SORT_FIELDS dictionary!
    response = test_client.get('/api/movies?sort_by=ratings&order=desc')
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Extract the ratings into a list
    ratings = [movie['vote_average'] for movie in data['data']]
    
    # Create a copy of the list and sort it descending manually
    expected_ratings = sorted(ratings, reverse=True)
    
    # Assert the API returned them in the perfectly sorted order
    assert ratings == expected_ratings

def test_6_invalid_sort_field(test_client):
    """Test 6 — Invalid sort field returns 400 Bad Request"""
    response = test_client.get('/api/movies?sort_by=invalid_field')
    
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    # Updated to match the error message we wrote in your parser
    assert "sort_by must be" in data['error']

def test_7_page_beyond_range(test_client):
    """Test 7 — Page beyond range returns empty data array"""
    response = test_client.get('/api/movies?page=9999')
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['data'] == []
    assert data['pagination']['has_next'] is False