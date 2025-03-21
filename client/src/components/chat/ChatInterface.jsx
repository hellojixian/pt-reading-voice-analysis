import React from 'react';
import { useTranslation } from 'react-i18next';
import LanguageSelector from '../LanguageSelector';
import ActiveBookBanner from '../book/ActiveBookBanner';
import MessageList from '../message/MessageList';
import ChatFooter from './ChatFooter';
import useChat from '../../hooks/useChat';
import useAudio from '../../hooks/useAudio';
import useBookState from '../../hooks/useBookState';

/**
 * Reading Voice Analysis Chat Interface
 * A Pickatale product for analyzing and improving reading skills
 */
const ChatInterface = () => {
  const { t } = useTranslation();

  // Initialize audio hook
  const {
    playingAudioId,
    status: audioStatus,
    setStatus: setAudioStatus,
    playAudio,
    stopAudio
  } = useAudio();

  // Initialize book state hook
  const {
    activeBook,
    processBookFunctionResults,
    exitBookMode,
    bookStatus,
    setBookStatus
  } = useBookState();

  // Initialize chat hook, passing in audio play and book function callbacks
  const {
    messages,
    inputText,
    setInputText,
    isProcessing,
    status: chatStatus,
    processingSteps,
    inputHasFocus,
    setInputHasFocus,
    chatContainerRef,
    handleSubmit,
    handleAudioRecorded,
    formatTimestamp
  } = useChat(playAudio, processBookFunctionResults);

  // Combine status messages
  const status = audioStatus || bookStatus || chatStatus;

  // Handle audio playing - when starting new audio, stop any current playback
  const handleAudioPlay = (messageId, audioUrl) => {
    if (playingAudioId) {
      stopAudio();
    }
    playAudio(messageId, audioUrl);
  };

  return (
    <>
      <div className="header">
        <h1>
          <div className="full-logo">
            <img
              src="./assets/logo.png"
              alt="Pickatale"
              className="pickatale-logo-image"
            />
            <span>{t('app.readingAssistant')}</span>
          </div>
        </h1>
        <LanguageSelector />
      </div>

      {/* Active book banner */}
      <ActiveBookBanner
        book={activeBook}
        onExitBookMode={exitBookMode}
      />

      {/* Message list */}
      <MessageList
        messages={messages}
        formatTimestamp={formatTimestamp}
        playingAudioId={playingAudioId}
        onPlayAudio={handleAudioPlay}
        onStopAudio={stopAudio}
        processingSteps={processingSteps}
        status={status}
        containerRef={chatContainerRef}
      />

      {/* Chat input and controls */}
      <ChatFooter
        inputText={inputText}
        setInputText={setInputText}
        handleSubmit={handleSubmit}
        isProcessing={isProcessing}
        onAudioRecorded={handleAudioRecorded}
        inputHasFocus={inputHasFocus}
        setInputHasFocus={setInputHasFocus}
        playingAudioId={playingAudioId}
        stopAudio={stopAudio}
      />

      <div className="pickatale-footer">
        <div className="footer-bubbles">
          <span className="bubble bubble-green"></span>
          <span className="bubble bubble-yellow"></span>
          <span className="bubble bubble-blue"></span>
        </div>
        <p>{t('footer.copyright', { year: new Date().getFullYear() })}</p>
      </div>
    </>
  );
};

export default ChatInterface;
