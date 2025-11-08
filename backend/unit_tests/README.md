# Unit Tests

This directory contains unit tests for the Eve Trade Helper application.

## Structure

```
unittests/
├── __init__.py           # Test module
├── conftest.py           # pytest configuration and fixtures
├── test_eve_api_client.py  # Tests for EveAPIClient
├── test_cache_decorator.py # Tests for cache decorator
├── test_deals_service.py   # Tests for DealsService
├── test_market_service.py   # Tests for MarketService
├── reference/            # Reference data for comparison
│   ├── regions_list.json
│   ├── region_details_*.json
│   └── ...
└── README.md            # This file
```

## Running Tests

```bash
# Install pytest
pip install pytest

# Run all unit tests
pytest backend/unittests/ -m unit

# Run with details
pytest backend/unittests/ -m unit -v

# Run a specific test file
pytest backend/unittests/test_deals_service.py

# Run a specific test
pytest backend/unittests/test_deals_service.py::TestDealsServiceCollectTypes::test_collect_all_types_from_simple_group
```

## Cache for Unit Tests

Unit tests use an **in-memory fake cache** (`FakeCache`) that simulates Redis behavior without requiring a real connection. This allows:

- Testing cache behavior without depending on Redis
- Running tests faster
- Isolating each test (cache is cleaned after each test)

The fake cache implements the same interface as `SimpleCache`:
- `get(key)`: retrieves data from cache
- `set(key, items, metadata)`: saves data to cache
- `is_valid(key)`: checks if cache is still valid
- `clear(key)`: clears cache

## Reference Generation

On first execution, tests will:
1. Make real API calls
2. Save results in `unittests/reference/`
3. Skip tests with a message indicating references were created

On subsequent executions, tests will:
1. Compare API results with references
2. Report differences if they exist

## Updating References

To regenerate references:

```bash
# Delete old references
rm -rf backend/unittests/reference/*.json

# Re-run tests
pytest backend/unittests/ -m unit
```

## Notes

- Unit tests use mocks to isolate business logic
- Tests are marked with `@pytest.mark.unit`
- Fake cache is automatically used for all unit tests
- Cache is cleaned after each test to avoid leaks between tests
- Integration tests (in `integration_tests/`) use real Redis cache
