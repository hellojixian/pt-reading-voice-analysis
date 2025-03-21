"""
OpenAI Assistant 控制器
处理基于 OpenAI Assistant API 的聊天功能

注意：此文件为控制器实现，已重构为使用 AssistantService。
当前应用实际使用的是 server/api/assistant_api.py，
该文件同样使用 AssistantService 实现相同功能。

两种实现路径：
1. routes.py → controllers/assistant_controller.py (此文件)
2. routes/api_routes.py → api/assistant_api.py (当前使用)
"""
import json
from flask import jsonify, request, Response, stream_with_context

# 导入服务
from services.assistant_service import AssistantService

# 初始化 Assistant 服务
assistant_service = AssistantService()

# 辅助函数 - 创建SSE格式的消息
def format_sse(event, data):
    """
    格式化用于服务器发送事件（SSE）的消息

    参数:
        event: 事件名称
        data: 事件数据（将被转换为JSON）

    返回:
        格式化的SSE消息字符串
    """
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"

def assistant_chat_stream():
    """使用服务器发送事件（SSE）处理基于 Assistant API 的流式聊天请求"""
    # 获取消息内容
    message = request.args.get('message')
    if not message:
        return jsonify({"error": "Message content missing"}), 400

    # 获取用户语言和会话ID
    language = request.args.get('language', 'en')
    session_id = request.cookies.get('session_id', 'default_user')

    # 使用流式处理聊天
    def generate():
        # 使用assistant_service.chat_stream方法处理流式聊天
        for event_data in assistant_service.chat_stream(
            message=message,
            session_id=session_id,
            language=language
        ):
            yield event_data

    return Response(stream_with_context(generate()), content_type="text/event-stream")

def assistant_chat():
    """处理基于 Assistant API 的常规聊天请求"""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "Message content missing"}), 400

        # 获取请求参数
        user_message = data['message']
        language = data.get('language', 'en')
        session_id = request.cookies.get('session_id', 'default_user')

        # 使用服务处理聊天请求
        result = assistant_service.process_chat(
            message=user_message,
            session_id=session_id,
            language=language,
            is_stream=False
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
