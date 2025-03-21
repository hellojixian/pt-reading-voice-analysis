import React from 'react';
import { useTranslation } from 'react-i18next';

/**
 * BookSearchResults component - Displays search results for books
 *
 * @param {Object} props
 * @param {Object} props.functionResult - The function result containing book search results
 * @returns {JSX.Element|null} - The rendered component or null if no results
 */
const BookSearchResults = ({ functionResult }) => {
  const { t } = useTranslation();

  if (!functionResult) return null;

  // Direct array in result (old format)
  if (Array.isArray(functionResult.result)) {
    return (
      <div className="book-search-results">
        <h3>{t('book.searchResults')}</h3>
        <div className="matched-books-list">
          {functionResult.result.map((book, bookIndex) => (
            <div key={bookIndex} className="matched-book">
              <a
                href={`https://app.pickatale.com/library/book/${book.book_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="book-title-link"
              >
                📚 {book.book_title} (ID: {book.book_id})
              </a>
              {book.book_Description && (
                <div className="book-description">{book.book_Description}</div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // New format with matched_books field
  if (functionResult.result && functionResult.result.matched_books) {
    return (
      <div className="book-search-results">
        <h3>{t('book.searchResults')}</h3>
        <div className="matched-books-list">
          {functionResult.result.matched_books.map((book, bookIndex) => (
            <div key={bookIndex} className="matched-book">
              <a
                href={`https://app.pickatale.com/library/book/${book.book_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="book-title-link"
              >
                📚 {book.book_title} (ID: {book.book_id})
              </a>
              {book.book_Description && (
                <div className="book-description">{book.book_Description}</div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return null;
};

export default BookSearchResults;
