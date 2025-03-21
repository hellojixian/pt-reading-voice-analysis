import React from 'react';
import { useTranslation } from 'react-i18next';
import RecordButton from '../RecordButton';

/**
 * ChatFooter component - Renders the chat input area with text input and buttons
 *
 * @param {Object} props
 * @param {string} props.inputText - Current value of the text input
 * @param {Function} props.setInputText - Callback to update input text value
 * @param {Function} props.handleSubmit - Form submission handler
 * @param {boolean} props.isProcessing - Whether a request is currently processing
 * @param {Function} props.onAudioRecorded - Callback when audio recording is completed
 * @param {boolean} props.inputHasFocus - Whether the text input has focus
 * @param {Function} props.setInputHasFocus - Callback to update input focus state
 * @param {string|null} props.playingAudioId - ID of currently playing audio, if any
 * @param {Function} props.stopAudio - Callback to stop audio playback
 * @returns {JSX.Element} - The rendered footer component
 */
const ChatFooter = ({
  inputText,
  setInputText,
  handleSubmit,
  isProcessing,
  onAudioRecorded,
  inputHasFocus,
  setInputHasFocus,
  playingAudioId,
  stopAudio
}) => {
  const { t } = useTranslation();

  return (
    <>
      <form className="input-container" onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={t('chat.askQuestion')}
          className="text-input"
          disabled={isProcessing}
          onFocus={() => setInputHasFocus(true)}
          onBlur={() => setInputHasFocus(false)}
        />
        <button
          type="submit"
          className="send-button"
          disabled={isProcessing || !inputText.trim()}
        >
          {t('chat.send')}
        </button>
        <RecordButton
          onAudioRecorded={onAudioRecorded}
          isProcessing={isProcessing}
          stopAudio={stopAudio}
          playingAudioId={playingAudioId}
          inputHasFocus={inputHasFocus}
        />
      </form>

      <div className="keyboard-hint">
        {t('messages.keyboardHint')}
      </div>
    </>
  );
};

export default ChatFooter;
