# HTTP Metadata Inventory Service

A FastAPI service that collects and stores HTTP metadata (headers, cookies, page source) for any given URL. Built with Python 3.11, MongoDB, and Docker Compose.

## Quick Start

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`.

Interactive API docs (Swagger UI) at `http://localhost:8000/docs`.

## API Endpoints

### POST /metadata

Create a metadata record by fetching a URL's headers, cookies, and page source.

```bash
curl -X POST http://localhost:8000/metadata \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

**Response (201 Created):**
```json
{
  "url": "https://example.com",
  "status_code": 200,
  "headers": {"content-type": "text/html", "server": "cloudflare", ...},
  "cookies": {},
  "page_source": "<!doctype html>...",
  "fetched_at": "2026-04-21T19:22:45Z"
}
```

### GET /metadata

Retrieve stored metadata for a URL.

```bash
curl "http://localhost:8000/metadata?url=https://example.com"
```

**If data exists (200 OK):** Returns the full metadata record.

**If data is missing (202 Accepted):** Queues a background fetch and returns immediately.
```json
{
  "message": "Metadata not found. Collection has been scheduled.",
  "url": "https://example.com"
}
```
The next GET for the same URL will return the fetched data.

## Architecture

```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Settings from environment variables
├── database.py          # MongoDB connection management
├── models.py            # Pydantic request/response models
├── routes/
│   └── metadata.py      # API endpoint handlers
└── services/
    └── metadata.py      # Core business logic (fetch, store, retrieve)
```

The codebase follows a layered architecture:
- **Routes** handle HTTP concerns (request parsing, status codes, error responses)
- **Services** contain business logic (fetching URLs, storing data)
- **Models** define data shapes and validation
- **Database** manages the MongoDB connection lifecycle

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Configuration

Settings are managed via environment variables (or a `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DB_NAME` | `metadata_inventory` | Database name |
| `REQUEST_TIMEOUT` | `30` | Timeout in seconds for outbound HTTP requests |

## Design Decisions

- **Background tasks via FastAPI's `BackgroundTasks`** instead of a separate worker queue. This keeps the architecture simple while meeting the async requirement without self-referential HTTP calls.
- **Unique index on URL** in MongoDB for O(log n) lookups and duplicate prevention at the database level.
- **`httpx` with `AsyncClient`** for non-blocking outbound requests, matching FastAPI's async architecture.
- **`upsert` on store** — if metadata for a URL already exists, it gets replaced with fresh data rather than creating duplicates.
