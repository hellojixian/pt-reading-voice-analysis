"""
聊天API
提供基于OpenAI Chat API的聊天功能端点
"""
from flask import Blueprint, jsonify, request
import os

from services.openai_service import OpenAIService
from services.speech_service import SpeechService

# 创建蓝图
chat_api = Blueprint('chat_api', __name__)

# 初始化服务
openai_service = OpenAIService()
speech_service = SpeechService()

# 会话历史记录（真实项目中应使用数据库存储）
conversation_history = []

@chat_api.route('/api/chat', methods=['POST'])
def chat():
    """
    处理基本聊天请求

    使用OpenAI Chat API处理文本聊天请求，并生成语音响应

    请求:
        POST请求，JSON数据包含'message'字段和可选的'language'字段

    返回:
        JSON响应，包含回复文本和音频URL

    示例:
        POST /api/chat
        请求体: {"message": "你好，我是谁？", "language": "zh"}
        响应: {
            "text": "你好！你是一个用户，我是AI助手。",
            "audio_url": "/api/audio/abc123.mp3"
        }
    """
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "缺少消息内容"}), 400

        user_message = data['message']
        language = data.get('language', 'en')

        # 内容审核
        moderation_result = speech_service.moderate_and_respond(user_message, language)
        if moderation_result.get("is_warning"):
            # 如果被标记为不适当，直接返回警告
            return jsonify(moderation_result)

        # 更新对话历史
        conversation_history.append({"role": "user", "content": user_message})

        # 获取AI回复
        ai_response = openai_service.get_chat_response(conversation_history)

        # 更新对话历史
        conversation_history.append({"role": "assistant", "content": ai_response})

        # 生成语音
        tts_result = speech_service.text_to_speech(ai_response)

        # 构建响应
        response = {
            "text": ai_response,
            "audio_url": tts_result["audio_url"]
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_api.route('/api/chat/reset', methods=['POST'])
def reset_chat():
    """
    重置聊天历史

    清除当前的对话历史记录

    返回:
        JSON响应，确认历史已重置

    示例:
        POST /api/chat/reset
        响应: {"status": "success", "message": "聊天历史已重置"}
    """
    global conversation_history
    conversation_history = []

    return jsonify({
        "status": "success",
        "message": "聊天历史已重置"
    })
