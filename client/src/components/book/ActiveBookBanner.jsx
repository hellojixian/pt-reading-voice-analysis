import React from 'react';
import { useTranslation } from 'react-i18next';

/**
 * ActiveBookBanner component - Displays information about the book currently being discussed
 *
 * @param {Object} props
 * @param {Object} props.book - The book object with title and id
 * @param {Function} props.onExitBookMode - Callback to exit book discussion mode
 * @returns {JSX.Element|null} - The rendered component or null if no book
 */
const ActiveBookBanner = ({ book, onExitBookMode }) => {
  const { t } = useTranslation();

  if (!book) return null;

  return (
    <div className="active-book-banner">
      <div className="book-info">
        <span className="book-icon">📚</span>
        <div className="book-details">
          <h3>
            <a
              href={`https://app.pickatale.com/library/book/${book.book_id}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              {book.book_title}
            </a>
          </h3>
          <span className="book-id">ID: {book.book_id}</span>
        </div>
      </div>
      <button className="exit-book-mode" onClick={onExitBookMode}>
        {t('book.endDiscussion')}
      </button>
    </div>
  );
};

export default ActiveBookBanner;
