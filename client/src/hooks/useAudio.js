import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

/**
 * Custom hook for handling audio playback in the chat interface
 *
 * @param {string} apiBaseUrl - Base URL for the API
 * @returns {Object} Audio control methods and state
 */
const useAudio = (apiBaseUrl = 'http://localhost:8000/api') => {
  const { t } = useTranslation();
  const [playingAudioId, setPlayingAudioId] = useState(null);
  const [status, setStatus] = useState('');
  const audioRef = useRef(new Audio());

  // Setup audio event handlers
  useEffect(() => {
    const audio = audioRef.current;

    // Add audio error handler
    const handleAudioError = (e) => {
      console.error('音频播放错误:', e);
      setStatus(t('errors.audioPlaybackError'));
      setPlayingAudioId(null); // Reset playing state
    };

    // Add audio ended handler
    const handleAudioEnded = () => {
      setPlayingAudioId(null); // Reset playing state
    };

    // Add ESC key listener to stop playing audio
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && playingAudioId) {
        stopAudio();
      }
    };

    audio.addEventListener('error', handleAudioError);
    audio.addEventListener('ended', handleAudioEnded);
    window.addEventListener('keydown', handleKeyDown);

    // Cleanup function
    return () => {
      audio.removeEventListener('error', handleAudioError);
      audio.removeEventListener('ended', handleAudioEnded);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [t, playingAudioId]);

  /**
   * Stop audio playback
   */
  const stopAudio = () => {
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
    }
    setPlayingAudioId(null);
  };

  /**
   * Play audio from the given URL
   *
   * @param {string} messageId - ID of the message containing this audio
   * @param {string} audioUrl - URL of the audio file to play
   */
  const playAudio = (messageId, audioUrl) => {
    // If already playing, stop first
    if (playingAudioId) {
      stopAudio();
    }

    try {
      // Ensure URL is absolute path
      const fullAudioUrl = audioUrl.startsWith('http')
        ? audioUrl
        : `${apiBaseUrl.replace('/api', '')}${audioUrl}`;

      audioRef.current.src = fullAudioUrl;
      audioRef.current.load();

      // Play audio and handle possible playback failure
      const playPromise = audioRef.current.play();

      if (playPromise !== undefined) {
        playPromise.then(() => {
          // Set currently playing message ID
          setPlayingAudioId(messageId);
        }).catch(e => {
          console.error('音频播放失败:', e);
          setStatus(t('errors.audioPlaybackError'));
        });
      }
    } catch (audioError) {
      console.error('设置音频源错误:', audioError);
    }
  };

  return {
    playingAudioId,
    status,
    setStatus,
    playAudio,
    stopAudio
  };
};

export default useAudio;
