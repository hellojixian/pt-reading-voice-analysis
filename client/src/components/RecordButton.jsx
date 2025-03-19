import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';

/**
 * 录音按钮组件
 *
 * @param {Object} props
 * @param {Function} props.onAudioRecorded - 录音完成后的回调函数
 * @param {boolean} props.isProcessing - 是否正在处理请求
 * @param {Function} props.stopAudio - 停止正在播放的音频
 * @param {string|null} props.playingAudioId - 正在播放的音频ID，如果没有则为null
 * @param {boolean} props.inputHasFocus - 文本输入框是否有焦点
 */
const RecordButton = ({ onAudioRecorded, isProcessing, stopAudio, playingAudioId, inputHasFocus }) => {
  const { t } = useTranslation();
  const [isRecording, setIsRecording] = useState(false);
  const [recorder, setRecorder] = useState(null);
  const [error, setError] = useState(null);
  const audioChunks = useRef([]);

  // 初始化录音功能
  useEffect(() => {
    const initializeRecorder = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunks.current.push(event.data);
          }
        };

        mediaRecorder.onstop = () => {
          const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
          audioChunks.current = [];
          onAudioRecorded(audioBlob);
        };

        setRecorder(mediaRecorder);
        setError(null);
      } catch (err) {
        console.error('麦克风访问错误:', err);
        setError(t('errors.recordingFailed'));
      }
    };

    initializeRecorder();

    // 清理函数
    return () => {
      if (recorder && recorder.state === 'recording') {
        recorder.stop();
      }
    };
  }, [onAudioRecorded, t]);

  // 监听空格键
  useEffect(() => {
    const handleKeyDown = (e) => {
      // 只有在文本输入框没有焦点时才应用空格键快捷方式
      if (inputHasFocus) {
        return; // 如果输入框有焦点，不处理空格键事件
      }

      // 只有空格键被按下且未处于处理状态时才开始录音
      if (e.code === 'Space' && !isProcessing && !isRecording && recorder) {
        // 防止空格键滚动页面
        e.preventDefault();

        // 如果有音频正在播放，先停止
        if (playingAudioId && stopAudio) {
          stopAudio();
        }

        startRecording();
      }
    };

    const handleKeyUp = (e) => {
      if (e.code === 'Space' && isRecording && recorder) {
        stopRecording();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isRecording, recorder, isProcessing, playingAudioId, stopAudio, inputHasFocus]);

  const startRecording = () => {
    if (recorder && recorder.state !== 'recording' && !isProcessing) {
      audioChunks.current = [];
      recorder.start();
      setIsRecording(true);
    }
  };

  const stopRecording = () => {
    if (recorder && recorder.state === 'recording') {
      recorder.stop();
      setIsRecording(false);
    }
  };

  return (
    <div>
      <button
        className={`record-button ${isRecording ? 'recording' : ''}`}
        onMouseDown={startRecording}
        onMouseUp={stopRecording}
        onMouseLeave={isRecording ? stopRecording : undefined}
        onTouchStart={startRecording}
        onTouchEnd={stopRecording}
        disabled={isProcessing || !recorder}
        aria-label={isRecording ? t('chat.recording') : t('chat.record')}
        title={isRecording ? t('chat.recording') : t('chat.record')}
      >
        <i className="material-icons">{isRecording ? 'mic' : 'mic_none'}</i>
      </button>
      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

export default RecordButton;
