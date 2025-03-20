import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import RecordButton from './RecordButton';
import { sendTextMessage, sendAudioForTranscription } from '../services/api';

// ActiveBookBanner组件 - 显示当前正在讨论的书籍信息
const ActiveBookBanner = ({ book, onExitBookMode }) => {
  if (!book) return null;

  return (
    <div className="active-book-banner">
      <div className="book-info">
        <span className="book-icon">📚</span>
        <div className="book-details">
          <h3>{book.book_title}</h3>
          <span className="book-id">ID: {book.book_id}</span>
        </div>
      </div>
      <button className="exit-book-mode" onClick={onExitBookMode}>
        结束讨论
      </button>
    </div>
  );
};

// 用于音频URL构建
const API_BASE_URL = 'http://localhost:8000/api';

/**
 * Reading Voice Analysis Chat Interface
 * A Pickatale product for analyzing and improving reading skills
 */
const ChatInterface = () => {
  const { t } = useTranslation();
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState(''); // 用户输入文本
  const [isProcessing, setIsProcessing] = useState(false);
  const [status, setStatus] = useState('');
  const [processingSteps, setProcessingSteps] = useState([]); // 处理步骤列表
  const [activeBook, setActiveBook] = useState(null); // 当前讨论的书籍
  const [playingAudioId, setPlayingAudioId] = useState(null); // 跟踪当前播放的音频ID
  const [inputHasFocus, setInputHasFocus] = useState(false); // 跟踪输入框是否有焦点
  const chatContainerRef = useRef(null);
  const audioRef = useRef(new Audio());

  // Add welcome message on component mount
  useEffect(() => {
    setMessages([
      {
        id: 'welcome',
        text: 'Welcome to Pickatale Reading Assistant! I can analyze your reading voice and provide personalized feedback to help improve your reading skills. Try reading a passage or asking a question.',
        sender: 'assistant',
        timestamp: new Date().toISOString()
      }
    ]);
  }, []);

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
      setPlayingAudioId(null); // 重置播放状态
    };

    // 添加音频结束处理
    const handleAudioEnded = () => {
      setPlayingAudioId(null); // 重置播放状态
    };

    // 添加ESC键监听，用于停止正在播放的音频
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && playingAudioId) {
        stopAudio();
      }
    };

    audio.addEventListener('error', handleAudioError);
    audio.addEventListener('ended', handleAudioEnded);
    window.addEventListener('keydown', handleKeyDown);

    // 清理函数
    return () => {
      audio.removeEventListener('error', handleAudioError);
      audio.removeEventListener('ended', handleAudioEnded);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [t, playingAudioId]);

  // 停止音频播放
  const stopAudio = () => {
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
    }
    setPlayingAudioId(null);
  };

  // 播放音频
  const playAudio = (messageId, audioUrl) => {
    // 如果已经在播放，先停止
    if (playingAudioId) {
      stopAudio();
    }

    try {
      // 确保URL是绝对路径
      const fullAudioUrl = audioUrl.startsWith('http')
        ? audioUrl
        : `${API_BASE_URL.replace('/api', '')}${audioUrl}`;

      audioRef.current.src = fullAudioUrl;
      audioRef.current.load();

      // 播放音频，并处理可能的播放失败
      const playPromise = audioRef.current.play();

      if (playPromise !== undefined) {
        playPromise.then(() => {
          // 设置当前播放的消息ID
          setPlayingAudioId(messageId);
        }).catch(e => {
          console.error('音频播放失败:', e);
          setStatus(t('errors.audioPlaybackError'));
          setTimeout(() => setStatus(''), 3000);
        });
      }
    } catch (audioError) {
      console.error('设置音频源错误:', audioError);
    }
  };

  // 退出书籍讨论模式
  const exitBookMode = () => {
    setActiveBook(null);
    setStatus('已退出书籍讨论模式');
    setTimeout(() => setStatus(''), 2000);
  };

  // 处理文本提交
  const handleSubmit = async (e) => {
    e?.preventDefault();

    // 验证输入不为空
    if (!inputText.trim()) {
      return;
    }

    // 如果有音频正在播放，先停止
    if (playingAudioId) {
      stopAudio();
    }

    await processUserInput(inputText);
    setInputText('');
  };

  // 处理语音录制完成
  const handleAudioRecorded = async (audioBlob) => {
    setStatus(t('chat.speechToText'));
    setIsProcessing(true);

    // 如果有音频正在播放，先停止
    if (playingAudioId) {
      stopAudio();
    }

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

  // 处理状态更新
  const handleStatusUpdate = (statusMsg, progress = null) => {
    setStatus(statusMsg);

    // 如果是新步骤，添加到处理步骤列表
    if (progress !== null) {
      setProcessingSteps(prev => {
        // 检查是否已有相同类型的步骤
        const existingIndex = prev.findIndex(step => step.type === progress.type);
        if (existingIndex >= 0) {
          // 更新现有步骤
          const updatedSteps = [...prev];
          updatedSteps[existingIndex] = { ...progress, status: statusMsg };
          return updatedSteps;
        } else {
          // 添加新步骤
          return [...prev, { ...progress, status: statusMsg }];
        }
      });
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
    setProcessingSteps([]); // 清空处理步骤

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

      // 发送用户消息到服务器，使用SSE接收实时状态更新
      const response = await sendTextMessage(text, handleStatusUpdate);

      // 移除临时消息并添加实际回复
      const messageId = `ai-${Date.now()}`;
      setMessages(prev => prev.filter(msg => msg.id !== aiTempId));
      setMessages(prev => [...prev, {
        id: messageId,
        text: response.text,
        sender: 'assistant',
        timestamp: new Date().toISOString(),
        audioUrl: response.audio_url,
        functionResults: response.function_results || [] // 添加函数调用结果
      }]);

      // 处理函数调用结果，更新activeBook状态
      if (response.function_results && response.function_results.length > 0) {
        for (const func of response.function_results) {
          // 处理获取书籍内容的函数调用
          if (func.name === 'get_book_content' && func.result && func.result.status === 'success') {
            // 设置当前活跃的书籍
            setActiveBook({
              book_id: func.result.book_id,
              book_title: func.result.book_title
            });
          }
          // 如果用户要求退出书籍讨论模式
          else if ((func.name === 'search_book_by_title' || func.name === 'recommend_books')
                  && activeBook !== null) {
            // 这意味着用户可能想讨论新书，重置activeBook
            setActiveBook(null);
          }
        }
      }

      // 自动播放音频回复
      if (response.audio_url) {
        playAudio(messageId, response.audio_url);
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
      setProcessingSteps([]); // 清空处理步骤
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
      <div className="header">
        <h1>
          <div className="full-logo">
            <img
              src="./assets/logo.png"
              alt="Pickatale"
              className="pickatale-logo-image"
            />
            <span>Reading Assistant</span>
          </div>
        </h1>
        <div className="language-selector">
          <select onChange={(e) => {
            // Handle language change
            const selectedLanguage = e.target.value;
            if (window.i18n && window.i18n.changeLanguage) {
              window.i18n.changeLanguage(selectedLanguage);
            }
          }}>
            <option value="en">English</option>
            <option value="zh">中文</option>
          </select>
        </div>
      </div>

      {/* 活跃书籍横幅 */}
      <ActiveBookBanner book={activeBook} onExitBookMode={exitBookMode} />

      <div className="chat-container" ref={chatContainerRef}>
        {/* 处理步骤显示 */}
        {processingSteps.length > 0 && (
          <div className="processing-steps">
            {processingSteps.map((step, index) => (
              <div key={index} className="processing-step">
                <span className="step-icon">{step.icon || '⚙️'}</span>
                <span className="step-status">{step.status}</span>
              </div>
            ))}
          </div>
        )}
        {messages.map((message) => (
          <div
            key={message.id}
            className={`chat-message ${message.sender === 'user' ? 'user-message' : 'bot-message'} ${message.isError ? 'error-message' : ''} ${message.isTemporary ? 'temporary-message' : ''}`}
          >
            <div className="message-sender">
              {message.sender === 'user' ? 'You' : 'Pickatale Assistant'}
            </div>

            {/* 检查是否有图书推荐结果 */}
            {(() => {
              // 查找是否有推荐书籍的函数调用结果
              const hasBookRecommendations = message.functionResults &&
                message.functionResults.some(func =>
                  (func.name === 'recommend_books' && (func.result || (func.arguments && func.arguments.recommended_books)))
                );

              // 仅当没有书籍推荐结果时才显示AI回复的文本内容
              if (!hasBookRecommendations) {
                return <div className="message-content">{message.text}</div>;
              }
              return null;
            })()}

            {/* Display function call results, such as recommended books or search results */}
            {message.functionResults && message.functionResults.length > 0 && (
              <div className="function-results">
                {message.functionResults.map((func, index) => {
                  // 推荐书籍结果
                  if (func.name === 'recommend_books' && func.result) {
                    // 使用新数据结构 func.result 数组
                    return (
                      <div key={index} className="book-recommendations">
                        <h3>推荐书籍:</h3>
                        <div className="recommended-books-list">
                          {func.result.map((book, bookIndex) => (
                            <div key={bookIndex} className="recommended-book">
                              <a
                                href={`https://app.pickatale.com/library/book/${book.book_id}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="book-title-link"
                              >
                                📚 {book.book_title} (ID: {book.book_id})
                              </a>
                              <div className="book-reason">推荐理由: {book.reason}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  }
                  // 兼容旧数据结构 func.arguments.recommended_books
                  else if (func.name === 'recommend_books' && func.arguments && func.arguments.recommended_books) {
                    const { recommendation_summary, recommended_books } = func.arguments;
                    return (
                      <div key={index} className="book-recommendations">
                        {recommendation_summary && <div className="recommendation-summary">{recommendation_summary}</div>}
                        <div className="recommended-books-list">
                          {recommended_books.map((book, bookIndex) => (
                            <div key={bookIndex} className="recommended-book">
                              <a
                                href={`https://app.pickatale.com/library/book/${book.book_id}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="book-title-link"
                              >
                                📚 {book.book_title} (ID: {book.book_id})
                              </a>
                              <div className="book-reason">推荐理由: {book.reason}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  }
                  // 书籍搜索结果
                  else if (func.name === 'search_book_by_title' && func.result) {
                    return (
                      <div key={index} className="book-search-results">
                        <h3>搜索到的书籍:</h3>
                        <div className="matched-books-list">
                          {func.result.map((book, bookIndex) => (
                            <div key={bookIndex} className="matched-book">
                              <div className="book-title">
                                📚 {book.book_title} (ID: {book.book_id})
                              </div>
                              {book.book_Description && (
                                <div className="book-description">{book.book_Description}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  }
                  // 获取书籍内容结果
                  else if (func.name === 'get_book_content' && func.result) {
                    return (
                      <div key={index} className="book-content-result">
                        <h3>书籍内容:</h3>
                        <div className="book-status">
                          {func.result.status === 'success'
                            ? `成功获取《${func.result.book_title}》(ID: ${func.result.book_id})的内容`
                            : `未找到ID为 ${func.arguments.book_id} 的书籍`}
                        </div>
                      </div>
                    );
                  }
                  return null;
                })}
              </div>
            )}

            <div className="message-time">{formatTimestamp(message.timestamp)}</div>
            {message.audioUrl && (
              <div className="message-audio-controls">
                <button
                  className={`audio-control ${playingAudioId === message.id ? 'playing' : ''}`}
                  onClick={() => {
                    // 如果当前正在播放这个音频，则停止播放
                    if (playingAudioId === message.id) {
                      stopAudio();
                    } else {
                      // 否则播放这个音频
                      playAudio(message.id, message.audioUrl);
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
        ))}
        {status && <div className="status-message">{status}</div>}
      </div>

      <form className="input-container" onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Ask a question or read a passage..."
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
          onAudioRecorded={handleAudioRecorded}
          isProcessing={isProcessing}
          stopAudio={stopAudio}
          playingAudioId={playingAudioId}
          inputHasFocus={inputHasFocus}
        />
      </form>

      <div className="keyboard-hint">
        Press Space to record | Press Esc to stop audio
      </div>

      <div className="pickatale-footer">
        <div className="footer-bubbles">
          <span className="bubble bubble-green"></span>
          <span className="bubble bubble-yellow"></span>
          <span className="bubble bubble-blue"></span>
        </div>
        <p>© {new Date().getFullYear()} Pickatale. Helping children love reading.</p>
      </div>
    </>
  );
};

export default ChatInterface;
