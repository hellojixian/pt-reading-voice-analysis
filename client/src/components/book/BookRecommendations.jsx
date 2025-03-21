import React from 'react';
import { useTranslation } from 'react-i18next';

/**
 * BookRecommendations component - Displays a list of recommended books
 *
 * @param {Object} props
 * @param {Object} props.functionResult - The function result containing book recommendations
 * @returns {JSX.Element|null} - The rendered component
 */
const BookRecommendations = ({ functionResult }) => {
  const { t } = useTranslation();

  if (!functionResult) return null;

  // Handle different data structures (support all formats)
  const renderRecommendations = () => {
    // For new data structure (direct array in result)
    if (Array.isArray(functionResult.result)) {
      return (
        <div className="book-recommendations">
          <h3>{t('book.recommendedBooks')}</h3>
          <div className="recommended-books-list">
            {functionResult.result.map((book, bookIndex) => (
              <div key={bookIndex} className="recommended-book">
                <a
                  href={`https://app.pickatale.com/library/book/${book.book_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="book-title-link"
                >
                  📚 {book.book_title} (ID: {book.book_id})
                </a>
                <div className="book-reason">{t('book.recommendationReason')} {book.reason}</div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // For recommended_books structure in result object
    else if (functionResult.result && functionResult.result.recommended_books) {
      return (
        <div className="book-recommendations">
          <h3>{t('book.recommendedBooks')}</h3>
          <div className="recommended-books-list">
            {functionResult.result.recommended_books.map((book, bookIndex) => (
              <div key={bookIndex} className="recommended-book">
                <a
                  href={`https://app.pickatale.com/library/book/${book.book_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="book-title-link"
                >
                  📚 {book.book_title} (ID: {book.book_id})
                </a>
                <div className="book-reason">{t('book.recommendationReason')} {book.reason}</div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // For old data structure (func.arguments.recommended_books)
    else if (functionResult.arguments && functionResult.arguments.recommended_books) {
      const { recommendation_summary, recommended_books } = functionResult.arguments;
      return (
        <div className="book-recommendations">
          {recommendation_summary && <div className="recommendation-summary">{recommendation_summary}</div>}
          <div className="recommended-books-list">
            {recommended_books.map((book, bookIndex) => (
              <div key={bookIndex} className="recommended-book">
                <a
                  href={`https://app.pickatale.com/library/book/${book.book_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="book-title-link"
                >
                  📚 {book.book_title} (ID: {book.book_id})
                </a>
                <div className="book-reason">{t('book.recommendationReason')} {book.reason}</div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    return null;
  };

  return renderRecommendations();
};

export default BookRecommendations;
