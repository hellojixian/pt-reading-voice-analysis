import React from 'react';
import MessageItem from './MessageItem';
import ProcessingStatus from '../chat/ProcessingStatus';

/**
 * MessageList component - Renders the list of chat messages
 *
 * @param {Object} props
 * @param {Array} props.messages - List of message objects to display
 * @param {Function} props.formatTimestamp - Function to format message timestamps
 * @param {string|null} props.playingAudioId - ID of currently playing audio, if any
 * @param {Function} props.onPlayAudio - Callback to play message audio
 * @param {Function} props.onStopAudio - Callback to stop message audio
 * @param {Array} props.processingSteps - List of processing steps (e.g., thinking, searching)
 * @param {string} props.status - Current status message
 * @param {React.RefObject} props.containerRef - Reference to the container element
 * @returns {JSX.Element} - The rendered message list component
 */
const MessageList = ({
  messages,
  formatTimestamp,
  playingAudioId,
  onPlayAudio,
  onStopAudio,
  processingSteps,
  status,
  containerRef
}) => {
  return (
    <div className="chat-container" ref={containerRef}>
      {/* Messages */}
      {messages.map((message) => (
        <MessageItem
          key={message.id}
          message={message}
          formatTimestamp={formatTimestamp}
          playingAudioId={playingAudioId}
          onPlayAudio={onPlayAudio}
          onStopAudio={onStopAudio}
        />
      ))}

      {/* Display processing status at the bottom of the chat */}
      <ProcessingStatus
        processingSteps={processingSteps}
        status={status}
      />
    </div>
  );
};

export default MessageList;
