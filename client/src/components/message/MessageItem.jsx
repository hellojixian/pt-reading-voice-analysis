import React from 'react';
import { useTranslation } from 'react-i18next';
import renderMarkdown from '../../utils/markdown';
import BookRecommendations from '../book/BookRecommendations';
import BookSearchResults from '../book/BookSearchResults';

/**
 * MessageItem component - Renders a single chat message
 *
 * @param {Object} props
 * @param {Object} props.message - The message object to display
 * @param {Function} props.formatTimestamp - Function to format the timestamp
 * @param {string|null} props.playingAudioId - ID of currently playing audio, if any
 * @param {Function} props.onPlayAudio - Callback to play message audio
 * @param {Function} props.onStopAudio - Callback to stop message audio
 * @returns {JSX.Element} - The rendered message component
 */
const MessageItem = ({
  message,
  formatTimestamp,
  playingAudioId,
  onPlayAudio,
  onStopAudio
}) => {
  const { t } = useTranslation();

  // Check if there are book recommendations
  const hasBookRecommendations = message.functionResults &&
    message.functionResults.some(func =>
      (func.name === 'recommend_books' && (func.result || (func.arguments && func.arguments.recommended_books)))
    );

  // Render function results based on type
  const renderFunctionResults = () => {
    if (!message.functionResults || message.functionResults.length === 0) {
      return null;
    }

    return (
      <div className="function-results">
        {message.functionResults.map((func, index) => {
          // Book recommendation results
          if (func.name === 'recommend_books') {
            return <BookRecommendations key={index} functionResult={func} />;
          }

          // Book search results
          else if (func.name === 'search_book_by_title') {
            return <BookSearchResults key={index} functionResult={func} />;
          }

          // Book content results
          else if (func.name === 'get_book_content' && func.result) {
            // Check if a valid book was found in search results before displaying book content
            const hasValidBookResult = message.functionResults.some(result =>
              (result.name === 'search_book_by_title' &&
               ((Array.isArray(result.result) && result.result.length > 0) ||
                (result.result && result.result.matched_books && result.result.matched_books.length > 0))
              )
            );

            // Only display book content if search found valid books or if this isn't linked to a search
            if (hasValidBookResult || !message.functionResults.some(result => result.name === 'search_book_by_title')) {
              // Get book data from either new (nested) or old (flat) structure
              const bookData = func.result.book || func.result;
              const bookId = bookData.book_id;
              const bookTitle = bookData.book_title;

              return (
                <div key={index} className="book-content-result">
                  <h3>{t('book.bookContent')}</h3>
                  <div className="book-status">
                    {func.result.status === 'success' ? (
                      <>
                        <div className="fetched-book">
                          <a
                            href={`https://app.pickatale.com/library/book/${bookId}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="book-title-link"
                          >
                            📚 {bookTitle} (ID: {bookId})
                          </a>
                          <div className="fetched-success-message">
                            {t('book.fetchSuccess', {
                              title: bookTitle,
                              bookId: bookId
                            }).replace('{title}', bookTitle).replace('{bookId}', bookId)}
                          </div>
                        </div>
                      </>
                    ) : (
                      t('book.fetchFailed', {
                        bookId: func.arguments.book_id
                      }).replace('{bookId}', func.arguments.book_id)
                    )}
                  </div>
                </div>
              );
            }

            return null;
          }

          return null;
        })}
      </div>
    );
  };

  return (
    <div
      className={`chat-message ${message.sender === 'user' ? 'user-message' : 'bot-message'} ${message.isError ? 'error-message' : ''} ${message.isTemporary ? 'temporary-message' : ''} ${message.isWarning ? 'warning-message' : ''}`}
    >
      <div className="message-sender">
        {message.sender === 'user' ? t('chat.you') : t('chat.pickataleAssistant')}
      </div>

      {/* Only show AI text reply if there are no book recommendations */}
      {!hasBookRecommendations && (
        <div className="message-content">
          {renderMarkdown(message.text)}
        </div>
      )}

      {/* Display function call results */}
      {renderFunctionResults()}

      <div className="message-time">{formatTimestamp(message.timestamp)}</div>

      {/* Audio controls if message has audio */}
      {message.audioUrl && (
        <div className="message-audio-controls">
          <button
            className={`audio-control ${playingAudioId === message.id ? 'playing' : ''}`}
            onClick={() => {
              // If currently playing this audio, stop playback
              if (playingAudioId === message.id) {
                onStopAudio();
              } else {
                // Otherwise play this audio
                onPlayAudio(message.id, message.audioUrl);
              }
            }}
          >
            {playingAudioId === message.id ? (
              <i className="material-icons">stop</i>
            ) : (
              <i className="material-icons">volume_up</i>
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export default MessageItem;
