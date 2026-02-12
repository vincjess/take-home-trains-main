# Train Schedule API

A FastAPI service for managing train schedules and finding simultaneous arrivals.

## Setup

```bash
# Install dependencies
pip install -e ".[dev]"
```

## Running the Server

```bash
# Run the server
uvicorn app:app --host 127.0.0.1 --port 5000

# Or directly
python app.py
```

## Testing

```bash
# Run tests
pytest -v

# Run tests with coverage
pytest --cov=. --cov-report=term-missing
```

## Linting

```bash
# Format code
black .
isort .

# Type check
mypy .
```

## API Endpoints

- `GET /` - Health check
- `POST /trains` - Add or update a train schedule. Accepts `{ "id": "ABC", "schedule": [0, 60, ...] }` and normalizes IDs to uppercase.
- `GET /trains/{train_id}` - Get schedule for a train. Returns `list[int]` (minutes from midnight). `train_id` must be 1-6 alphabetic characters.
- `GET /trains/next` - Find next simultaneous arrival

## Design Decisions

- **Simple scan approach**: The `/next` endpoint scans all schedules and groups by time on each request. I initially considered maintaining a secondary time index (`time:minutes -> [train_ids]`) to precompute overlaps, but this adds complexity and is harder to extend for real-world requirements like weekend/holiday schedules, multiple stations, or schedule versioning.

- **Service layer**: Business logic is separated from the API layer in `service.py`.

- **Validation**: Train IDs must be 1-6 alphabetic characters. Schedule times must be 0-1439 (minutes from midnight).
