import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { sendTextMessage, sendAudioForTranscription } from '../services/api';

/**
 * Custom hook for managing chat functionality
 *
 * @param {Function} onAudioPlayRequest - Callback to request audio playback
 * @param {Function} processBookFunctionResults - Callback to process book-related function results
 * @returns {Object} Chat state and methods
 */
const useChat = (onAudioPlayRequest, processBookFunctionResults) => {
  const { t } = useTranslation();
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState('');
  const [processingSteps, setProcessingSteps] = useState([]);
  const [inputHasFocus, setInputHasFocus] = useState(false);
  const chatContainerRef = useRef(null);

  // Add welcome message on component mount
  useEffect(() => {
    setMessages([
      {
        id: 'welcome',
        text: t('messages.welcome'),
        sender: 'assistant',
        timestamp: new Date().toISOString()
      }
    ]);
  }, [t]);

  // Scroll to bottom when messages list updates
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // Handle status update
  const handleStatusUpdate = (statusMsg, progress = null) => {
    // Set status message
    setStatus(statusMsg);

    // If it's a new step, add to processing steps list
    if (progress !== null) {
      setProcessingSteps(prev => {
        // Check if there's already a step of the same type
        const existingIndex = prev.findIndex(step => step.type === progress.type);
        if (existingIndex >= 0) {
          // Update existing step
          const updatedSteps = [...prev];
          updatedSteps[existingIndex] = { ...progress, status: statusMsg };
          return updatedSteps;
        } else {
          // Add new step
          return [...prev, { ...progress, status: statusMsg }];
        }
      });
    }
  };

  // Process user input (text or transcribed speech)
  const processUserInput = async (text, addUserMessage = true) => {
    // Add user input to messages list (only when addUserMessage is true)
    if (addUserMessage) {
      const userMsgId = Date.now().toString();
      setMessages(prev => [...prev, {
        id: userMsgId,
        text: text,
        sender: 'user',
        timestamp: new Date().toISOString()
      }]);
    }

    setIsProcessing(true);
    setStatus(t('chat.thinking')); // Show status message at the bottom
    setProcessingSteps([]); // Clear processing steps

    try {
      // Send user message to server, using SSE for real-time status updates
      const response = await sendTextMessage(text, handleStatusUpdate);

      // Add actual reply
      const messageId = `ai-${Date.now()}`;
      setMessages(prev => [...prev, {
        id: messageId,
        text: response.text,
        sender: 'assistant',
        timestamp: new Date().toISOString(),
        audioUrl: response.audio_url,
        isWarning: response.is_warning || false, // Add warning flag
        functionResults: response.function_results || [] // Add function call results
      }]);

      // Process function call results, update activeBook state
      if (response.function_results && response.function_results.length > 0) {
        processBookFunctionResults(response.function_results);
      }

      // Clear status message after getting server response
      setStatus('');

      // Auto-play audio reply - only for non-warning messages
      if (response.audio_url && !response.is_warning) {
        onAudioPlayRequest(messageId, response.audio_url);
      }
    } catch (error) {
      console.error('发送消息错误:', error);
      // Clear status message when error occurs
      setStatus('');
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        text: t('errors.apiError'),
        sender: 'system',
        timestamp: new Date().toISOString(),
        isError: true
      }]);
    } finally {
      setProcessingSteps([]); // Clear processing steps
      setIsProcessing(false);
    }
  };

  // Handle text submission
  const handleSubmit = async (e) => {
    e?.preventDefault();

    // Validate input is not empty
    if (!inputText.trim()) {
      return;
    }

    await processUserInput(inputText);
    setInputText('');
  };

  // Handle audio recording completion
  const handleAudioRecorded = async (audioBlob) => {
    setStatus(t('chat.speechToText'));
    setIsProcessing(true);

    try {
      // Add user "transcribing" message
      const tempId = Date.now().toString();
      setMessages(prev => [...prev, {
        id: tempId,
        text: t('chat.speechToText'),
        sender: 'user',
        timestamp: new Date().toISOString(),
        isTemporary: true
      }]);

      // Send audio to server for transcription
      const result = await sendAudioForTranscription(audioBlob);
      const transcribedText = result.text;

      // Update temporary message with transcribed text
      setMessages(prev => prev.map(msg =>
        msg.id === tempId
          ? { ...msg, text: transcribedText, isTemporary: false }
          : msg
      ));

      // Process transcribed text, passing false means don't add user message again
      await processUserInput(transcribedText, false);
    } catch (error) {
      console.error('语音转录错误:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        text: t('errors.apiError'),
        sender: 'system',
        timestamp: new Date().toISOString(),
        isError: true
      }]);
    } finally {
      // Keep status message visible
      setIsProcessing(false);
    }
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return {
    messages,
    inputText,
    setInputText,
    isProcessing,
    status,
    processingSteps,
    inputHasFocus,
    setInputHasFocus,
    chatContainerRef,
    handleSubmit,
    handleAudioRecorded,
    formatTimestamp
  };
};

export default useChat;
