# Assessment

A production-grade REST API built with Python Flask and MongoDB that allows content teams to upload movie data via CSV files (up to 1GB) and query the ingested data with filtering, sorting, and pagination. Built as part of an SDE-1 assessment.

---

## Tech Stack

| Layer      | Technology        | Version  |
|------------|-------------------|----------|
| Framework  | Python Flask      | 3.x      |
| Database   | MongoDB           | 6.x      |
| Driver     | PyMongo           | 4.x      |
| Runtime    | Python            | 3.11+    |
| Container  | Docker            | 24.x     |

---

## Project Structure

```text
assessment/
│
├── app/
│   ├── __init__.py          # App factory: create_app()
│   ├── config.py            # Environment-based configuration
│   │
│   ├── api/
│   │   ├── upload.py        # POST /api/upload
│   │   └── movies.py        # GET /api/movies
│   │
│   ├── services/
│   │   ├── csv_processor.py # Streaming CSV ingestion logic
│   │   └── movie_service.py # Filter, sort, paginate logic
│   │
│   ├── db/
│   │   ├── mongo.py         # MongoDB singleton connection
|   |   └── indexes.py       # Indexes file
│   │   
│   └── models/
│       └── movie.py         # Document schema and validator
│
├── tests/
│   ├── test_upload.py       # Upload pipeline integration tests
│   └── test_movies.py       # Query API integration tests
│
├── .env.example             # Environment variable template
├── docker-compose.yml       # MongoDB + Flask containerised setup
├── requirements.txt         # Pinned Python dependencies
└── README.md
---

## Prerequisites
Ensure the following are installed before proceeding:

1. Python 3.11 or higher → https://www.python.org/downloads/

2. MongoDB 6.x → https://www.mongodb.com/docs/manual/installation/ OR Docker Desktop → https://www.docker.com/products/docker-desktop/

3. Git → https://git-scm.com/downloads/

Verify installations:

Bash
python --version    # Expected: Python 3.11.x
mongosh --version   # Expected: 2.x.x
docker --version    # Expected: Docker 24.x.x


Local Setup
Step 1: Clone the Repository
Bash
git clone [https://github.com/YOUR_USERNAME/imdb-content-system.git](https://github.com/YOUR_USERNAME/imdb-content-system.git)
cd imdb-content-system
Step 2: Create and Activate Virtual Environment
Bash
python -m venv venv

# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
Confirm activation: your terminal prompt shows (venv)

Step 3: Install Dependencies
Bash
pip install -r requirements.txt
Step 4: Configure Environment Variables
Bash
cp .env.example .env
Open .env and set the following values:

MONGO_URI=mongodb://localhost:27017
DB_NAME=imdb_content
MAX_CONTENT_LENGTH_MB=1024
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5000

If using Docker for MongoDB (see Section 6), use: MONGO_URI=mongodb://localhost:27017 (Docker Compose maps MongoDB to localhost:27017 by default)

Step 5: Create MongoDB Indexes
Bash
python -m app.db.create_indexes
Expected output:

Index created: year_language_compound

Index created: vote_average

Index created: release_date

Index created: unique_title_date_language

Step 6: Start the Flask Server
Bash
flask --app run:app run
Expected output:

* Running on http://127.0.0.1:5000

* Debug mode: on

Running with Docker (Recommended)
Docker Compose starts both MongoDB and Flask together with a single command — no local MongoDB installation needed.

Step 1: Ensure Docker Desktop is running
Step 2: Start all services
Bash
docker compose up --build
This will:

Pull the official MongoDB 6 image

Build the Flask application image

Start both containers on the same network

Map Flask to http://localhost:5000

Map MongoDB to localhost:27017

Step 3: Create indexes (first time only)
Bash
docker compose exec api python -m app.db.create_indexes
Step 4: Stop all services
Bash
docker compose down
To also delete the MongoDB data volume:

Bash
docker compose down -v
API Reference
Base URL: http://localhost:5000/api

─────────────────────────────────────────────────

POST /api/upload
─────────────────────────────────────────────────

Description: Upload a CSV file containing movie data. Supports files up to 1GB via streaming. Re-uploading the same file is safe (idempotent).

Request: multipart/form-data

Field name: file

Field type: File (.csv only)

Success Response (200):

JSON
{
    "status": "completed",
    "summary": {
        "total_rows_read": 9999,
        "successfully_inserted": 9847,
        "skipped_duplicates": 120,
        "failed_rows": 32,
        "error_log_truncated": false
    },
    "errors": [
        { "row_number": 47, "reason": "missing required field: title" }
    ]
}
Error Responses:

400 → No file provided / empty filename

413 → File exceeds 1GB limit

415 → File is not a CSV

500 → Internal processing error

─────────────────────────────────────────────────

GET /api/movies
─────────────────────────────────────────────────

Description: Retrieve paginated list of movies with optional filtering and sorting.

Query Parameters:

page (Integer): Page number (default: 1)

limit (Integer): Results per page (default: 10, max: 100)

year (Integer): Filter by release year (e.g. 1995)

language (String): Filter by language (e.g. english)

sort_by (String): Sort field (release_date | vote_average)

order (String): Sort direction (asc | desc, default: desc)

Success Response (200):

JSON
{
    "success": true,
    "data": [
        {
            "title": "Toy Story",
            "original_title": "Toy Story",
            "year": 1995,
            "vote_average": 7.7,
            "primary_language": "english",
            "release_date": "1995-10-30T00:00:00"
        }
    ],
    "pagination": {
        "page": 1,
        "limit": 10,
        "total_documents": 4821,
        "total_pages": 483,
        "has_next": true,
        "has_prev": false
    }
}
Error Responses:

400 → Invalid query parameter values

500 → Database error

Example Requests:

Bash
# All movies, default pagination
GET /api/movies

# Filter by year
GET /api/movies?year=1995

# Filter by language
GET /api/movies?language=english

# Combined filter with sort
GET /api/movies?year=1995&language=english&sort_by=vote_average&order=desc

# Custom pagination
GET /api/movies?page=3&limit=25
Running the Tests
⚠️ IMPORTANT — Read Before Running Tests There are two test files with different database requirements:

─────────────────────────────────────────────────

test_upload.py — Self-contained, no setup needed
─────────────────────────────────────────────────
These tests create their own in-memory CSV data and manage their own database state via fixtures. They will clean up after themselves automatically.

Run independently:

Bash
python -m pytest tests/test_upload.py -v
─────────────────────────────────────────────────

test_movies.py — Requires seeded test data
─────────────────────────────────────────────────
These tests query the database and assert against real documents. They require a test database with pre-loaded content before they will pass.

Required setup before running test_movies.py:

Step 1: Ensure your .env points to the test database: DB_NAME=imdb_content_test (Use a SEPARATE database — not your production data)

Step 2: Seed the test database with sample data:

Upload the sample CSV to the test database first:

Bash
flask --app run:app run
curl -X POST -F "file=@sample.csv" http://localhost:5000/api/upload
OR insert the provided fixture documents manually:

Bash
python -m tests.seed_test_db
(creates 20 known documents for deterministic assertions)

Step 3: Run the movie tests:

Bash
python -m pytest tests/test_movies.py -v
─────────────────────────────────────────────────

Full test suite (both files together):
─────────────────────────────────────────────────

Bash
python -m pytest tests/ -v
Expected output:

Plaintext
tests/test_upload.py::test_happy_path                PASSED
tests/test_upload.py::test_invalid_file_type         PASSED
tests/test_upload.py::test_empty_csv                 PASSED
tests/test_upload.py::test_invalid_rows              PASSED
tests/test_upload.py::test_duplicate_idempotency     PASSED
tests/test_movies.py::test_default_pagination        PASSED
tests/test_movies.py::test_custom_limit              PASSED
tests/test_movies.py::test_year_filter               PASSED
tests/test_movies.py::test_language_filter           PASSED
tests/test_movies.py::test_sort_descending           PASSED
tests/test_movies.py::test_invalid_sort              PASSED
tests/test_movies.py::test_page_beyond_range         PASSED
──────────────────────────────────────────────────────
12 passed