# Testing the Fetch Book Content Function

This directory contains tests for the `fetch_book_content()` function in the data_source.py module.

## Test Structure

- `__init__.py`: Marks the directory as a Python package
- `conftest.py`: Configuration for pytest
- `test_data_source.py`: Tests for the data_source.py module

## Running the Tests

To run the tests, make sure you have pytest installed:

```bash
pip install pytest pytest-mock
```

Then run the tests using:

```bash
# From the server directory
python -m pytest tests/

# Or for more verbose output
python -m pytest tests/ -v
```

## Test Cases

The test suite for `fetch_book_content()` includes:

1. **Valid Book IDs**: Tests retrieving data for each of the valid book IDs (12550-1, 2590-3, 2940-5)
2. **Invalid Book ID**: Tests the function's behavior when an invalid ID is provided
3. **Database Errors**: Tests error handling when database connection fails
4. **Data Structure**: Validates the structure of the returned data

## Mock Strategy

The tests use the `unittest.mock` library to mock the Snowflake database connection and cursor. This approach:

- Avoids actual database calls during testing
- Makes tests faster and more reliable
- Allows testing of edge cases and error conditions
- Removes external dependencies for testing

## Adding More Tests

To add more tests:

1. Add new test functions to test_data_source.py
2. Follow the naming convention `test_*`
3. Use pytest fixtures as needed
4. Run the tests to ensure they pass
