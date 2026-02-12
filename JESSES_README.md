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
- `POST /trains` - Add or update a train schedule
- `GET /trains/{train_id}` - Get schedule for a train
- `GET /trains/next` - Find next simultaneous arrival

## Design Decisions

- **Dual indexing**: The service maintains both `train:ID -> schedule` and `time:minutes -> [train_ids]` indexes. This trades slower writes for faster overlap queries.
- **Service layer**: Business logic is separated from the API layer in `service.py`.
- **Validation**: Train IDs must be 1-6 alphabetic characters. Schedule times must be 0-1439 (minutes from midnight).
