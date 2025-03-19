import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import RecordButton from './RecordButton';
import { sendTextMessage, sendAudioForTranscription } from '../services/api';

// 用于音频URL构建
const API_BASE_URL = 'http://localhost:8000/api';

/**
 * 聊天界面组件
 * 处理用户输入和显示对话历史
 */
const ChatInterface = () => {
  const { t } = useTranslation();
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState('');
  const chatContainerRef = useRef(null);
  const audioRef = useRef(new Audio());

  // 组件挂载时添加欢迎消息
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

  // 当消息列表更新时，滚动到底部
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // 设置音频播放相关处理
  useEffect(() => {
    const audio = audioRef.current;

    // 添加音频错误处理
    const handleAudioError = (e) => {
      console.error('音频播放错误:', e);
      setStatus(t('errors.audioPlaybackError'));
      setTimeout(() => setStatus(''), 3000);
    };

    audio.addEventListener('error', handleAudioError);

    // 清理函数
    return () => {
      audio.removeEventListener('error', handleAudioError);
    };
  }, [t]);

  // 处理文本提交
  const handleSubmit = async (e) => {
    e?.preventDefault();

    // 验证输入不为空
    if (!inputText.trim()) {
      return;
    }

    await processUserInput(inputText);
    setInputText('');
  };

  // 处理语音录制完成
  const handleAudioRecorded = async (audioBlob) => {
    setStatus(t('chat.speechToText'));
    setIsProcessing(true);

    try {
      // 添加用户"正在转录中"的消息
      const tempId = Date.now().toString();
      setMessages(prev => [...prev, {
        id: tempId,
        text: t('chat.speechToText'),
        sender: 'user',
        timestamp: new Date().toISOString(),
        isTemporary: true
      }]);

      // 发送音频到服务器进行转录
      const result = await sendAudioForTranscription(audioBlob);
      const transcribedText = result.text;

      // 更新临时消息为转录的文本
      setMessages(prev => prev.map(msg =>
        msg.id === tempId
          ? { ...msg, text: transcribedText, isTemporary: false }
          : msg
      ));

      // 处理转录后的文本，传递false表示不要重复添加用户消息
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
      setStatus('');
      setIsProcessing(false);
    }
  };

  // 处理用户输入（文本或语音转录）
  const processUserInput = async (text, addUserMessage = true) => {
    // 将用户输入添加到消息列表（仅当addUserMessage为true时）
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
    setStatus(t('chat.thinking'));

    try {
      // 添加AI"正在思考"的临时消息
      const aiTempId = `ai-${Date.now()}`;
      setMessages(prev => [...prev, {
        id: aiTempId,
        text: t('chat.thinking'),
        sender: 'assistant',
        timestamp: new Date().toISOString(),
        isTemporary: true
      }]);

      // 发送用户消息到服务器
      const response = await sendTextMessage(text);

      // 移除临时消息并添加实际回复
      setMessages(prev => prev.filter(msg => msg.id !== aiTempId));
      setMessages(prev => [...prev, {
        id: `ai-${Date.now()}`,
        text: response.text,
        sender: 'assistant',
        timestamp: new Date().toISOString(),
        audioUrl: response.audio_url
      }]);

      // 播放音频回复
      if (response.audio_url) {
        try {
          // 确保URL是绝对路径
          const audioUrl = response.audio_url.startsWith('http')
            ? response.audio_url
            : `${API_BASE_URL.replace('/api', '')}${response.audio_url}`;

          audioRef.current.src = audioUrl;

          // 尝试预加载音频
          audioRef.current.load();

          // 播放音频，并处理可能的播放失败
          const playPromise = audioRef.current.play();

          if (playPromise !== undefined) {
            playPromise.catch(e => {
              console.error('音频播放失败:', e);
              // 显示音频播放错误状态
              setStatus(t('errors.audioPlaybackError'));
              setTimeout(() => setStatus(''), 3000);
            });
          }
        } catch (audioError) {
          console.error('设置音频源错误:', audioError);
        }
      }
    } catch (error) {
      console.error('发送消息错误:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        text: t('errors.apiError'),
        sender: 'system',
        timestamp: new Date().toISOString(),
        isError: true
      }]);
    } finally {
      setStatus('');
      setIsProcessing(false);
    }
  };

  // 格式化时间戳为友好的显示格式
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <>
      <div className="chat-container" ref={chatContainerRef}>
        {messages.map((message) => (
          <div
            key={message.id}
            className={`chat-message ${message.sender === 'user' ? 'user-message' : 'bot-message'} ${message.isError ? 'error-message' : ''} ${message.isTemporary ? 'temporary-message' : ''}`}
          >
            <div className="message-sender">
              {message.sender === 'user' ? t('chat.you') : t('chat.ai')}
            </div>
            <div className="message-content">{message.text}</div>
            <div className="message-time">{formatTimestamp(message.timestamp)}</div>
            {message.audioUrl && (
              <div className="message-audio-controls">
                <button
                  className="replay-audio"
                  onClick={() => {
                    try {
                      // 确保URL是绝对路径
                      const audioUrl = message.audioUrl.startsWith('http')
                        ? message.audioUrl
                        : `${API_BASE_URL.replace('/api', '')}${message.audioUrl}`;

                      audioRef.current.src = audioUrl;
                      audioRef.current.load();

                      const playPromise = audioRef.current.play();
                      if (playPromise !== undefined) {
                        playPromise.catch(e => {
                          console.error('重放音频失败:', e);
                          setStatus(t('errors.audioPlaybackError'));
                          setTimeout(() => setStatus(''), 3000);
                        });
                      }
                    } catch (audioError) {
                      console.error('设置音频源错误:', audioError);
                    }
                  }}
                >
                  <i className="material-icons">volume_up</i>
                </button>
              </div>
            )}
          </div>
        ))}
        {status && <div className="status-message">{status}</div>}
      </div>

      <form className="input-container" onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={t('chat.placeholder')}
          className="text-input"
          disabled={isProcessing}
        />
        <button
          type="submit"
          className="send-button"
          disabled={isProcessing || !inputText.trim()}
        >
          {t('chat.send')}
        </button>
        <RecordButton
          onAudioRecorded={handleAudioRecorded}
          isProcessing={isProcessing}
        />
      </form>

      <div className="keyboard-hint">
        {t('messages.pressSpace')}
      </div>
    </>
  );
};

export default ChatInterface;
