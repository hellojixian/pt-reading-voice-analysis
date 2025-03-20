const API_BASE_URL = 'http://localhost:8000/api';

/**
 * 发送文本消息到服务器（使用Assistant API）
 * 支持两种模式：常规模式和SSE实时状态更新模式
 *
 * @param {string} message - 用户输入的文本消息
 * @param {function} onStatusUpdate - 状态更新回调函数 (SSE模式使用)
 * @returns {Promise<Object>} - 包含AI回复文本和音频URL的对象
 */
export const sendTextMessage = async (message, onStatusUpdate = null) => {
  // 如果提供了状态更新回调，使用SSE模式
  if (onStatusUpdate) {
    return sendTextMessageWithSSE(message, onStatusUpdate);
  }

  // 否则使用常规模式
  try {
    // 使用Assistant API端点
    const response = await fetch(`${API_BASE_URL}/assistant-chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      mode: 'cors', // 明确指定CORS模式
      credentials: 'same-origin',
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error(`API错误: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('发送文本消息错误:', error);
    // 作为临时解决方案，返回一个模拟回复
    return {
      text: "I'm sorry, I'm having trouble connecting to the server. This is a simulated response. In a real application, I would process your message and provide a relevant answer.",
      audio_url: null
    };
  }
};

/**
 * 使用SSE（Server-Sent Events）发送文本消息，接收实时状态更新
 *
 * @param {string} message - 用户输入的文本消息
 * @param {function} onStatusUpdate - 状态更新回调函数
 * @returns {Promise<Object>} - 包含AI回复文本和音频URL的对象
 */
const sendTextMessageWithSSE = (message, onStatusUpdate) => {
  return new Promise((resolve, reject) => {
    try {
      // 创建一个带查询参数的URL
      const encodedMessage = encodeURIComponent(message);
      const url = `${API_BASE_URL}/assistant-chat-stream?message=${encodedMessage}`;

      // 创建SSE连接
      const eventSource = new EventSource(url);
      let finalResponse = null;

      // 监听状态更新事件
      eventSource.addEventListener('status', (event) => {
        const statusData = JSON.parse(event.data);
        onStatusUpdate(statusData.status);
      });

      // 监听进度更新事件
      eventSource.addEventListener('progress', (event) => {
        const progressData = JSON.parse(event.data);
        onStatusUpdate(progressData.status, progressData.progress);
      });

      // 监听完成事件
      eventSource.addEventListener('complete', (event) => {
        finalResponse = JSON.parse(event.data);
        eventSource.close();
        resolve(finalResponse);
      });

      // 监听错误
      eventSource.addEventListener('error', (event) => {
        console.error('SSE错误:', event);
        eventSource.close();

        // 如果已经收到了最终响应，则使用它
        if (finalResponse) {
          resolve(finalResponse);
        } else {
          // 否则返回错误
          reject(new Error('服务器连接中断'));
        }
      });

    } catch (error) {
      console.error('SSE连接错误:', error);
      reject(error);
    }
  });
};

/**
 * 获取书籍推荐
 * @param {string} userInterests - 用户的阅读兴趣
 * @returns {Promise<Object>} - 包含推荐书籍的对象
 */
export const getBookRecommendations = async (userInterests) => {
  try {
    const response = await fetch(`${API_BASE_URL}/recommend-books`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_interests: userInterests }),
    });

    if (!response.ok) {
      throw new Error(`API错误: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('获取书籍推荐错误:', error);
    throw error;
  }
};

/**
 * 将音频数据发送到服务器进行语音转文字
 * @param {Blob} audioBlob - 录制的音频数据
 * @returns {Promise<Object>} - 包含转录文本的对象
 */
export const sendAudioForTranscription = async (audioBlob) => {
  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');

    const response = await fetch(`${API_BASE_URL}/speech-to-text`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API错误: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('发送音频转录错误:', error);
    throw error;
  }
};

/**
 * 请求将文本转换为语音
 * @param {string} text - 要转换为语音的文本
 * @param {string} voice - 语音类型 (可选)
 * @returns {Promise<Object>} - 包含音频URL的对象
 */
export const textToSpeech = async (text, voice = 'alloy') => {
  try {
    const response = await fetch(`${API_BASE_URL}/text-to-speech`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text, voice }),
    });

    if (!response.ok) {
      throw new Error(`API错误: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('文字转语音错误:', error);
    throw error;
  }
};

/**
 * 检查服务器健康状态
 * @returns {Promise<Object>} - 包含服务器状态信息的对象
 */
export const checkHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`API错误: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('健康检查错误:', error);
    throw error;
  }
};
