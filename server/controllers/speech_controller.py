"""
语音转文字控制器
"""
from flask import jsonify, request
from werkzeug.utils import secure_filename

# 导入配置和服务
import config
from services.openai_service import OpenAIService

# 初始化服务
openai_service = OpenAIService()

def speech_to_text():
    """处理语音转文字请求"""
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "没有上传音频文件"}), 400

        audio_file = request.files['audio']

        # 检查文件类型
        filename = secure_filename(audio_file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        if file_ext not in config.ALLOWED_AUDIO_FORMATS:
            return jsonify({"error": f"不支持的音频格式，请使用以下格式之一: {', '.join(config.ALLOWED_AUDIO_FORMATS)}"}), 400

        # 使用OpenAI的Whisper API进行转录
        transcription = openai_service.transcribe_audio(audio_file)

        return jsonify({"text": transcription})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
