import io
import pytest

# Adjust these imports based on your exact file structure
from app.api.__init__ import create_app
from app.db.mongo import movie_collection

@pytest.fixture
def client():
    """
    Sets up a test client and ensures the database is clean 
    before and after every test runs.
    """
    app = create_app()
    app.config['TESTING'] = True
    
    # Wipe the database clean BEFORE the test
    movie_collection.delete_many({})
    
    with app.test_client() as client:
        yield client
        
    # Wipe the database clean AFTER the test
    movie_collection.delete_many({})

def create_fake_file(filename, content, mimetype="text/csv"):
    """Helper function to create in-memory files with explicit mimetypes."""
    return (io.BytesIO(content.encode('utf-8')), filename, mimetype)

# ---------------------------------------------------------
# THE 5 MENTOR TESTS
# ---------------------------------------------------------

def test_1_happy_path(client):
    """Test 1 — Happy path: Create an in-memory CSV with 5 valid rows"""
    csv_content = (
        "title,original_title,original_language,release_date\n"
        "Movie A,Movie A,en,10/30/1995\n"
        "Movie B,Movie B,en,12/15/1995\n"
        "Movie C,Movie C,en,01/01/2000\n"
        "Movie D,Movie D,en,05/05/2010\n"
        "Movie E,Movie E,en,08/20/2020\n"
    )
    data = {'file': create_fake_file('test.csv', csv_content)}
    
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 200
    summary = response.get_json()
    assert summary["successfully_inserted"] == 5
    assert summary["failed_rows"] == 0

def test_2_invalid_file_type(client):
    """Test 2 — Invalid file type: POST a .txt file"""
    txt_content = "This is just text, not a CSV format."
    
    # Pass 'text/plain' as the third argument to simulate a bad file
    data = {'file': create_fake_file('test.txt', txt_content, 'text/plain')}
    
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 415
    assert "Only CSV files accepted" in response.get_json()["error"]

def test_3_empty_csv(client):
    """Test 3 — Empty CSV: POST CSV with only the header row"""
    csv_content = "title,original_title,original_language,release_date\n"
    data = {'file': create_fake_file('empty.csv', csv_content)}
    
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 200
    summary = response.get_json()
    assert summary["total_rows_read"] == 0
    assert summary["successfully_inserted"] == 0

def test_4_invalid_rows(client):
    """Test 4 — CSV with some invalid rows: 2 of 5 rows have empty titles"""
    csv_content = (
        "title,original_title,original_language,release_date\n"
        "Movie A,Movie A,en,10/30/1995\n"
        ",Movie B,en,12/15/1995\n"               # Invalid: completely empty title
        "Movie C,Movie C,en,01/01/2000\n"
        "   ,Movie D,en,05/05/2010\n"           # Invalid: whitespace-only title
        "Movie E,Movie E,en,08/20/2020\n"
    )
    data = {'file': create_fake_file('mixed.csv', csv_content)}
    
    response = client.post('/api/upload', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 200
    summary = response.get_json()
    assert summary["successfully_inserted"] == 3
    assert summary["failed_rows"] == 2

def test_5_duplicate_upload_idempotency(client):
    """Test 5 — Duplicate upload idempotency: Upload same CSV twice"""
    csv_content = (
        "title,original_title,original_language,release_date\n"
        "Movie A,Movie A,en,10/30/1995\n"
        "Movie B,Movie B,en,12/15/1995\n"
        "Movie C,Movie C,en,01/01/2000\n"
        "Movie D,Movie D,en,05/05/2010\n"
        "Movie E,Movie E,en,08/20/2020\n"
    )
    
    # Run the First Upload
    data1 = {'file': create_fake_file('test.csv', csv_content)}
    client.post('/api/upload', data=data1, content_type='multipart/form-data')
    
    # Run the Second Upload (identical data)
    data2 = {'file': create_fake_file('test.csv', csv_content)}
    response2 = client.post('/api/upload', data=data2, content_type='multipart/form-data')
    
    assert response2.status_code == 200
    summary2 = response2.get_json()
    
    # The second upload should skip all 5 as duplicates
    assert summary2["skipped_duplicates"] == 5
    assert summary2["successfully_inserted"] == 0
    
    # Assert total documents in collection == 5 (not 10)
    total_docs = movie_collection.count_documents({})
    assert total_docs == 5