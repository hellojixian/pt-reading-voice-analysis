# PT Reading Voice Analysis - Client API Documentation

## Table of Contents
- [PT Reading Voice Analysis - Client API Documentation](#pt-reading-voice-analysis---client-api-documentation)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [API Service](#api-service)
    - [Base Configuration](#base-configuration)
    - [Text Message Functions](#text-message-functions)
      - [Send Text Message](#send-text-message)
    - [Audio Processing Functions](#audio-processing-functions)
      - [Send Audio for Transcription](#send-audio-for-transcription)
      - [Text to Speech](#text-to-speech)
    - [Book Related Functions](#book-related-functions)
      - [Get Book Recommendations](#get-book-recommendations)
    - [System Functions](#system-functions)
      - [Check Health](#check-health)
  - [React Hooks](#react-hooks)
    - [useChat](#usechat)
    - [useAudio](#useaudio)
    - [useBookState](#usebookstate)
  - [Event Handling](#event-handling)
    - [Server-Sent Events (SSE)](#server-sent-events-sse)
    - [Audio Events](#audio-events)

## Overview

The client API provides a set of functions and React hooks for interacting with the PT Reading Voice Analysis backend. This API handles text messaging, speech-to-text, text-to-speech, audio playback, and book-related functionality.

## API Service

The main API service is defined in `client/src/services/api.js` and provides the following functions:

### Base Configuration

```javascript
const API_BASE_URL = 'http://localhost:8000/api';
```

This constant defines the base URL for all API endpoints. If the server location changes, only this constant needs to be updated.

### Text Message Functions

#### Send Text Message

```javascript
export const sendTextMessage = async (message, onStatusUpdate = null) => { ... }
```

Sends a text message to the server and receives an AI response.

**Parameters:**
- `message` (string): The text message to send to the server
- `onStatusUpdate` (function, optional): Callback for status updates during processing

**Returns:**
- Promise resolving to an object with the following properties:
  - `text`: The text response from the AI
  - `html`: HTML-formatted response (if available)
  - `audio_url`: URL to the audio file of the spoken response
  - `function_results`: Results from any functions called during processing
  - `is_warning`: Boolean indicating if the response is a warning

**Example:**
```javascript
// Basic usage
const response = await sendTextMessage("Tell me about science fiction books");
console.log(response.text); // AI's text response

// With status updates
const response = await sendTextMessage("Tell me about science fiction books",
  (status, progress) => {
    console.log(`Current status: ${status}`);
    if (progress) {
      console.log(`Progress: ${progress.type}`);
    }
  }
);
```

### Audio Processing Functions

#### Send Audio for Transcription

```javascript
export const sendAudioForTranscription = async (audioBlob) => { ... }
```

Sends recorded audio to the server for speech-to-text conversion.

**Parameters:**
- `audioBlob` (Blob): Audio data recorded from the user

**Returns:**
- Promise resolving to an object with the following property:
  - `text`: The transcribed text from the audio

**Example:**
```javascript
// After recording audio with the browser's MediaRecorder API
const transcription = await sendAudioForTranscription(audioBlob);
console.log(`Transcribed text: ${transcription.text}`);
```

#### Text to Speech

```javascript
export const textToSpeech = async (text, voice = 'alloy') => { ... }
```

Converts text to speech and returns an audio URL.

**Parameters:**
- `text` (string): Text to convert to speech
- `voice` (string, optional): Voice type to use, default is 'alloy'

**Returns:**
- Promise resolving to an object with the following property:
  - `audio_url`: URL to the generated audio file

**Example:**
```javascript
const audioResponse = await textToSpeech("Hello world", "nova");
const audioElement = new Audio(audioResponse.audio_url);
audioElement.play();
```

### Book Related Functions

#### Get Book Recommendations

```javascript
export const getBookRecommendations = async (userInterests) => { ... }
```

Gets book recommendations based on user interests.

**Parameters:**
- `userInterests` (string): Description of user's reading interests

**Returns:**
- Promise resolving to an object with the following property:
  - `recommended_books`: Array of recommended book objects

**Example:**
```javascript
const recommendations = await getBookRecommendations("science fiction with robots");
recommendations.recommended_books.forEach(book => {
  console.log(`Book: ${book.book_title}`);
});
```

### System Functions

#### Check Health

```javascript
export const checkHealth = async () => { ... }
```

Checks the server's health status.

**Returns:**
- Promise resolving to an object with the following properties:
  - `status`: Health status of the server
  - `version`: Server version
  - `message`: Additional status message

**Example:**
```javascript
const healthStatus = await checkHealth();
if (healthStatus.status === "healthy") {
  console.log("Server is running normally");
}
```

## React Hooks

The client provides custom React hooks for managing application state and behavior.

### useChat

```javascript
const useChat = (onAudioPlayRequest, processBookFunctionResults) => { ... }
```

Manages chat functionality including message history, user input, and API interactions.

**Parameters:**
- `onAudioPlayRequest` (function): Callback to request audio playback
- `processBookFunctionResults` (function): Callback to process book-related function results

**Returns:**
- Object containing:
  - `messages`: Array of message objects
  - `inputText`: Current input text value
  - `setInputText`: Function to update input text
  - `isProcessing`: Boolean indicating if a message is being processed
  - `status`: Current status message
  - `processingSteps`: Array of processing step objects
  - `inputHasFocus`: Boolean indicating if the input field has focus
  - `setInputHasFocus`: Function to update input focus state
  - `chatContainerRef`: Ref object for the chat container
  - `handleSubmit`: Function to handle message submission
  - `handleAudioRecorded`: Function to handle recorded audio
  - `formatTimestamp`: Function to format message timestamps

**Example:**
```javascript
const {
  messages,
  inputText,
  setInputText,
  isProcessing,
  handleSubmit,
  handleAudioRecorded
} = useChat(
  (messageId, audioUrl) => playAudio(messageId, audioUrl),
  (results) => processBookResults(results)
);
```

### useAudio

```javascript
const useAudio = (apiBaseUrl = 'http://localhost:8000/api') => { ... }
```

Manages audio playback for chat responses.

**Parameters:**
- `apiBaseUrl` (string, optional): Base URL for the API

**Returns:**
- Object containing:
  - `playingAudioId`: ID of the currently playing audio message
  - `status`: Current audio playback status
  - `setStatus`: Function to update audio status
  - `playAudio`: Function to play audio for a message
  - `stopAudio`: Function to stop audio playback

**Example:**
```javascript
const { playingAudioId, playAudio, stopAudio } = useAudio();

// Play audio for a message
playAudio('message-123', '/api/audio/response.mp3');

// Stop audio playback
stopAudio();
```

### useBookState

```javascript
const useBookState = () => { ... }
```

Manages book-related state in the chat interface.

**Returns:**
- Object containing:
  - `activeBook`: Current active book object or null
  - `setActiveBook`: Function to update active book
  - `processBookFunctionResults`: Function to process book function results
  - `exitBookMode`: Function to exit book discussion mode
  - `bookStatus`: Current book-related status
  - `setBookStatus`: Function to update book status

**Example:**
```javascript
const {
  activeBook,
  processBookFunctionResults,
  exitBookMode
} = useBookState();

// Process function results from chat response
processBookFunctionResults(response.function_results);

// Exit book discussion mode
exitBookMode();
```

## Event Handling

### Server-Sent Events (SSE)

The client API supports real-time updates through Server-Sent Events when sending messages:

```javascript
const sendTextMessageWithSSE = (message, onStatusUpdate) => { ... }
```

When using this mode, the client establishes an SSE connection to the server and receives events in real-time.

**Event Types:**
- `status`: General status updates
- `progress`: Processing progress updates
- `complete`: Final response
- `error`: Error information

### Audio Events

Audio playback is managed with event listeners for error handling and playback completion:

- `error`: Triggered when audio playback fails
- `ended`: Triggered when audio playback completes
- `Escape` key: Pressing the Escape key stops audio playback
