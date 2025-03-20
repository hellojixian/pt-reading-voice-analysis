import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# Add the server directory to the Python path so we can import modules from it
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the function to test
from libs.data_source import fetch_book_content


# Mock data for different book IDs
MOCK_BOOK_DATA = {
    '12550-1': {
        'permanent_id': '12550-1',
        'title': 'Mock Book 1',
        'description': 'Description for Mock Book 1',
        'extended_info': json.dumps([
            {'rawText': 'Page 1 content for book 12550-1.'},
            {'rawText': 'Page 2 content for book 12550-1.'}
        ])
    },
    '2590-3': {
        'permanent_id': '2590-3',
        'title': 'Mock Book 2',
        'description': 'Description for Mock Book 2',
        'extended_info': json.dumps([
            {'rawText': 'Page 1 content for book 2590-3.'},
            {'rawText': 'Page 2 content for book 2590-3.'},
            {'rawText': 'Page 3 content for book 2590-3.'}
        ])
    },
    '2940-5': {
        'permanent_id': '2940-5',
        'title': 'Mock Book 3',
        'description': 'Description for Mock Book 3',
        'extended_info': json.dumps([
            {'rawText': 'Page 1 content for book 2940-5.'},
            {'rawText': 'Page 2 content for book 2940-5.'},
            {'rawText': 'Page 3 content for book 2940-5.'},
            {'rawText': 'Page 4 content for book 2940-5.'}
        ])
    }
}


# Mock function for cursor.fetchall() to return data based on book_id
def mock_fetchall(book_id):
    if book_id in MOCK_BOOK_DATA:
        book_data = MOCK_BOOK_DATA[book_id]
        return [(
            book_data['permanent_id'],
            book_data['title'],
            book_data['description'],
            book_data['extended_info']
        )]
    return []


# Fixtures
@pytest.fixture
def mock_snowflake_connection():
    """Creates a mock Snowflake connection and cursor."""
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


# Tests
@pytest.mark.parametrize('book_id', ['12550-1', '2590-3', '2940-5'])
def test_fetch_book_content_valid_ids(book_id, mock_snowflake_connection):
    """Test fetch_book_content with valid book IDs."""
    mock_conn, mock_cursor = mock_snowflake_connection

    # Configure the mock cursor to return appropriate data
    mock_cursor.fetchall.return_value = mock_fetchall(book_id)

    # Patch the database connection
    with patch('libs.data_source.get_db_connection', return_value=mock_conn):
        result = fetch_book_content(book_id)

        # Check that the function executed the SQL query
        mock_cursor.execute.assert_called_once()

        # Verify the result structure and content
        assert result is not None
        assert 'book_id' in result
        assert 'book_title' in result
        assert 'book_description' in result
        assert 'book_content' in result

        # Verify the content matches our mock data
        assert result['book_id'] == book_id
        assert result['book_title'] == MOCK_BOOK_DATA[book_id]['title']
        assert result['book_description'] == MOCK_BOOK_DATA[book_id]['description']

        # Verify that the book content includes all pages
        expected_pages = [page['rawText'] for page in
                         json.loads(MOCK_BOOK_DATA[book_id]['extended_info'])]
        for page_content in expected_pages:
            assert page_content in result['book_content']


def test_fetch_book_content_invalid_id(mock_snowflake_connection):
    """Test fetch_book_content with an invalid book ID."""
    mock_conn, mock_cursor = mock_snowflake_connection

    # Configure the mock cursor to return no data (empty list)
    mock_cursor.fetchall.return_value = []

    # Patch the database connection
    with patch('libs.data_source.get_db_connection', return_value=mock_conn):
        result = fetch_book_content('invalid-id')

        # Check that the function executed the SQL query
        mock_cursor.execute.assert_called_once()

        # Verify the result is None for an invalid ID
        assert result is None


def test_fetch_book_content_db_error(mock_snowflake_connection):
    """Test error handling when database errors occur."""
    mock_conn, mock_cursor = mock_snowflake_connection

    # Configure the mock cursor to raise an exception
    mock_cursor.execute.side_effect = Exception("Database connection error")

    # Patch the database connection
    with patch('libs.data_source.get_db_connection', return_value=mock_conn):
        with pytest.raises(Exception) as exc_info:
            fetch_book_content('12550-1')

        # Verify that the exception is propagated
        assert "Database connection error" in str(exc_info.value)


def test_fetch_book_content_data_structure(mock_snowflake_connection):
    """Test the structure of the data returned by fetch_book_content."""
    book_id = '12550-1'
    mock_conn, mock_cursor = mock_snowflake_connection

    # Configure the mock cursor to return appropriate data
    mock_cursor.fetchall.return_value = mock_fetchall(book_id)

    # Patch the database connection
    with patch('libs.data_source.get_db_connection', return_value=mock_conn):
        result = fetch_book_content(book_id)

        # Verify the structure of the returned data
        assert isinstance(result, dict)
        assert isinstance(result['book_id'], str)
        assert isinstance(result['book_title'], str)
        assert isinstance(result['book_description'], str)
        assert isinstance(result['book_content'], str)
