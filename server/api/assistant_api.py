"""
Assistant API
提供基于OpenAI Assistant API的聊天功能端点
"""
from flask import Blueprint, jsonify, request, Response, stream_with_context
import os
import json

from services.assistant_service import AssistantService
from utils.file_utils import get_temp_file_path

# 创建蓝图
assistant_api = Blueprint('assistant_api', __name__)

# 初始化服务
assistant_service = AssistantService()

@assistant_api.route('/api/assistant-chat', methods=['POST'])
def assistant_chat():
    """
    处理基于Assistant API的聊天请求

    接收聊天消息并返回AI回复

    请求:
        POST请求，JSON数据包含'message'字段和可选的'language'字段

    返回:
        JSON响应，包含回复文本和音频URL

    示例:
        POST /api/assistant-chat
        请求体: {"message": "你好，请推荐一些书", "language": "zh"}
        响应: {
            "text": "AI回复的文本内容",
            "audio_url": "/api/audio/abc123.mp3",
            "function_results": []
        }
    """
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "缺少消息内容"}), 400

        # 获取请求参数
        user_message = data['message']
        language = data.get('language', 'en')
        session_id = request.cookies.get('session_id', 'default_user')

        # 处理聊天请求
        result = assistant_service.process_chat(
            message=user_message,
            session_id=session_id,
            language=language,
            is_stream=False
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@assistant_api.route('/api/assistant-chat-stream', methods=['GET'])
def assistant_chat_stream():
    """
    使用服务器发送事件（SSE）处理基于Assistant API的流式聊天请求

    接收聊天消息并以流式方式返回AI回复

    请求:
        GET请求，URL参数包含'message'和可选的'language'

    返回:
        服务器发送事件（SSE）流

    示例:
        GET /api/assistant-chat-stream?message=你好，请推荐一些书&language=zh
    """
    # 获取消息内容
    message = request.args.get('message')
    if not message:
        return jsonify({"error": "缺少消息内容"}), 400

    # 获取用户语言和会话ID
    language = request.args.get('language', 'en')
    session_id = request.cookies.get('session_id', 'default_user')

    # 使用流式处理聊天
    def generate():
        try:
            # 使用assistant_service.chat_stream方法处理流式聊天
            for event_data in assistant_service.chat_stream(
                message=message,
                session_id=session_id,
                language=language
            ):
                yield event_data
        except Exception as e:
            # 格式化错误消息为SSE格式
            error_data = {"error": str(e)}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream"
    )
