"""
文字转语音控制器
"""
import os
import tempfile
from flask import jsonify, request, current_app

# 导入服务
from services.openai_service import OpenAIService

# 初始化服务
openai_service = OpenAIService()

def text_to_speech():
    """处理文字转语音请求"""
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "缺少文本内容"}), 400

        text = data['text']
        voice = data.get('voice', 'alloy')  # 默认使用alloy声音

        # 生成语音
        audio_data = openai_service.text_to_speech(text, voice)

        # 创建临时文件保存音频
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_data)
            audio_path = temp_file.name

        # 保存文件路径以便后续请求
        current_app.config[f"TEMP_AUDIO_{os.path.basename(audio_path)}"] = audio_path

        return jsonify({"audio_url": f"/api/audio/{os.path.basename(audio_path)}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
