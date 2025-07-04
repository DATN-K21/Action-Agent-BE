# AI Service Tests

This directory contains unit tests for the AI Service API endpoints.

## Setup

1. Install test dependencies:
```bash
pip install -r requirements-test.txt
```

2. Make sure you have the main application dependencies installed:
```bash
pip install -r requirements.txt
# or if using uv:
uv sync
```

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run specific test file:
```bash
pytest tests/test_user_api.py
```

### Run tests with verbose output:
```bash
pytest tests/ -v
```

### Run tests with coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

## Test Structure

- `conftest.py` - Test configuration and fixtures
- `test_user_api.py` - Tests for user API endpoints

## Test Features

### User API Tests (`test_user_api.py`)

Tests cover all user API endpoints:

1. **Get API Keys** (`/user/key/get-all`)
   - Success with API keys
   - Success without API keys  
   - User not found
   - Database errors

2. **Set Default API Key** (`/user/key/set-default`)
   - Success with provider
   - Success with null provider (unset)
   - API key not found
   - User not found
   - Database errors

3. **Upsert API Key** (`/user/key/upsert`)
   - Update existing key
   - Create new key
   - Update not found
   - Database errors

4. **Delete API Key** (`/user/{user_id}/key/delete`)
   - Success
   - Key not found
   - Database errors

5. **Validation Tests**
   - Invalid provider
   - Missing encrypted value
   - Empty encrypted value

## Test Utilities

The tests use:
- **pytest** for the testing framework
- **pytest-asyncio** for async test support
- **FastAPI TestClient** for API testing
- **unittest.mock** for mocking database interactions
- **SQLAlchemy mocks** for database operations

## Mock Strategy

Tests mock database interactions at the SQLAlchemy level to:
- Avoid requiring a real database
- Control exact responses for different scenarios
- Test error conditions reliably
- Run tests quickly

Each test creates appropriate mock objects that simulate SQLAlchemy result objects and database session behavior.
