"""
API路由定义
"""
from flask import Blueprint

# 导入控制器
from controllers.health_controller import health_check
from controllers.speech_controller import speech_to_text
from controllers.tts_controller import text_to_speech
from controllers.audio_controller import get_audio
from controllers.assistant_controller import assistant_chat, assistant_chat_stream

# 创建蓝图
api = Blueprint('api', __name__)

# 添加对预检请求的支持
@api.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@api.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    """处理预检请求"""
    return '', 200

# 健康检查路由
@api.route('/api/health', methods=['GET'])
def api_health_check():
    """健康检查端点"""
    return health_check()

# Assistant 聊天路由
@api.route('/api/assistant-chat', methods=['POST'])
def api_assistant_chat():
    """处理文字聊天请求（Assistant API）"""
    return assistant_chat()

# Assistant 聊天SSE流式路由
@api.route('/api/assistant-chat-stream', methods=['GET'])
def api_assistant_chat_stream():
    """处理文字聊天请求（SSE流式API）"""
    return assistant_chat_stream()

# 语音转文字路由
@api.route('/api/speech-to-text', methods=['POST'])
def api_speech_to_text():
    """处理语音转文字请求"""
    return speech_to_text()

# 文字转语音路由
@api.route('/api/text-to-speech', methods=['POST'])
def api_text_to_speech():
    """处理文字转语音请求"""
    return text_to_speech()

# 获取音频文件路由
@api.route('/api/audio/<filename>', methods=['GET'])
def api_get_audio(filename):
    """获取生成的音频文件"""
    return get_audio(filename)
