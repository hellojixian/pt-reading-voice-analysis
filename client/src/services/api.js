const API_BASE_URL = 'http://localhost:8000/api';

/**
 * 发送文本消息到服务器
 * @param {string} message - 用户输入的文本消息
 * @returns {Promise<Object>} - 包含AI回复文本和音频URL的对象
 */
export const sendTextMessage = async (message) => {
  try {
    // 使用mode: 'no-cors'避免触发预检请求
    const response = await fetch(`${API_BASE_URL}/chat`, {
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
