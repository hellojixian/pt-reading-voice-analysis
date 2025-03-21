import { useState } from 'react';
import { useTranslation } from 'react-i18next';

/**
 * Custom hook for managing book-related state in the chat interface
 *
 * @returns {Object} Book state and related functions
 */
const useBookState = () => {
  const { t } = useTranslation();
  const [activeBook, setActiveBook] = useState(null);
  const [status, setStatus] = useState('');

  /**
   * Set active book based on function result
   *
   * @param {Array} functionResults - Function call results from API
   */
  const processBookFunctionResults = (functionResults) => {
    if (!functionResults || functionResults.length === 0) {
      return;
    }

    for (const func of functionResults) {
      // Handle get_book_content function call
      if (func.name === 'get_book_content' && func.result && func.result.status === 'success') {
        // Set current active book
        setActiveBook({
          book_id: func.result.book_id,
          book_title: func.result.book_title
        });
      }
      // If user requests to exit book discussion mode
      else if ((func.name === 'search_book_by_title' || func.name === 'recommend_books')
              && activeBook !== null) {
        // This means user might want to discuss a new book, reset activeBook
        setActiveBook(null);
      }
    }
  };

  /**
   * Exit book discussion mode
   */
  const exitBookMode = () => {
    setActiveBook(null);
    setStatus(t('book.exitedBookMode'));
  };

  return {
    activeBook,
    setActiveBook,
    processBookFunctionResults,
    exitBookMode,
    bookStatus: status,
    setBookStatus: setStatus
  };
};

export default useBookState;
