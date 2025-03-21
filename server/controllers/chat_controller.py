"""
聊天功能控制器
"""
import os
import tempfile
from flask import jsonify, request, current_app

# 导入服务
from services.openai_service import OpenAIService

# 初始化服务
openai_service = OpenAIService()

# 会话历史记录（真实项目中应使用数据库存储）
conversation_history = []

def chat():
    """处理文字聊天请求"""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "Message content missing"}), 400

        user_message = data['message']

        # 更新对话历史
        conversation_history.append({"role": "user", "content": user_message})

        # 获取AI回复
        ai_response = openai_service.get_chat_response(conversation_history)

        # 更新对话历史
        conversation_history.append({"role": "assistant", "content": ai_response})

        # 生成语音
        audio_data = openai_service.text_to_speech(ai_response)

        # 创建临时文件保存音频
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_data)
            audio_path = temp_file.name

        # 构建响应
        response = {
            "text": ai_response,
            "audio_url": f"/api/audio/{os.path.basename(audio_path)}"
        }

        # 保存文件路径以便后续请求
        current_app.config[f"TEMP_AUDIO_{os.path.basename(audio_path)}"] = audio_path

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
