"""
语音API
提供语音转文字和文字转语音功能的API端点
"""
from flask import Blueprint, jsonify, request, send_file
import os

from services.speech_service import SpeechService
from utils.audio_utils import is_valid_audio_format
from utils.file_utils import get_temp_file_path
import config

# 创建蓝图
speech_api = Blueprint('speech_api', __name__)

# 初始化服务
speech_service = SpeechService()

@speech_api.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    """
    语音转文字端点

    接收音频文件并将其转换为文本

    请求:
        POST请求，表单中包含'audio'字段（文件）

    返回:
        JSON响应，包含转录文本

    示例:
        POST /api/speech-to-text
        表单数据: {'audio': <file>}
        响应: {"text": "转录的文本内容"}
    """
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "未上传音频文件"}), 400

        audio_file = request.files['audio']

        # 检查文件类型
        if not audio_file.filename or not is_valid_audio_format(audio_file.filename, config.ALLOWED_AUDIO_FORMATS):
            return jsonify({
                "error": f"不支持的音频格式，请使用以下格式之一: {', '.join(config.ALLOWED_AUDIO_FORMATS)}"
            }), 400

        # 使用服务转录音频
        result = speech_service.transcribe_audio(audio_file)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@speech_api.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    """
    文字转语音端点

    将文本转换为语音并返回音频URL

    请求:
        POST请求，JSON数据包含'text'字段和可选的'voice'字段

    返回:
        JSON响应，包含音频文件URL

    示例:
        POST /api/text-to-speech
        请求体: {"text": "你好，世界", "voice": "alloy"}
        响应: {"audio_url": "/api/audio/abc123.mp3"}
    """
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "缺少文本内容"}), 400

        text = data['text']
        voice = data.get('voice')  # 可选参数

        # 使用服务生成语音
        result = speech_service.text_to_speech(text, voice)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@speech_api.route('/api/audio/<filename>', methods=['GET'])
def get_audio(filename):
    """
    获取生成的音频文件

    通过文件名获取临时存储的音频文件

    参数:
        filename: 音频文件名

    返回:
        音频文件流

    示例:
        GET /api/audio/abc123.mp3
    """
    try:
        # 获取音频文件路径
        audio_path = get_temp_file_path(filename)

        if not audio_path:
            return jsonify({"error": "音频文件不存在"}), 404

        # 使用Flask的send_file函数，但添加必要的响应头
        response = send_file(audio_path, mimetype='audio/mpeg', as_attachment=False)

        # 添加音频播放所需的响应头
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Content-Type-Options'] = 'nosniff'

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500
