import os
import tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import io

# 导入配置和服务
import config
from services.openai_service import OpenAIService

# 初始化Flask应用
app = Flask(__name__)
# 正确配置CORS，允许所有源访问
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# 初始化服务
openai_service = OpenAIService()

# 会话历史记录（真实项目中应使用数据库存储）
conversation_history = []

# 添加对预检请求的支持
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    """处理预检请求"""
    return '', 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({"status": "healthy", "version": "1.0.0"})

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理文字聊天请求"""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "缺少消息内容"}), 400

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
        app.config[f"TEMP_AUDIO_{os.path.basename(audio_path)}"] = audio_path

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/speech-to-text', methods=['POST'])
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

@app.route('/api/text-to-speech', methods=['POST'])
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
        app.config[f"TEMP_AUDIO_{os.path.basename(audio_path)}"] = audio_path

        return jsonify({"audio_url": f"/api/audio/{os.path.basename(audio_path)}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/audio/<filename>', methods=['GET'])
def get_audio(filename):
    """获取生成的音频文件"""
    try:
        audio_path = app.config.get(f"TEMP_AUDIO_{filename}")
        if not audio_path or not os.path.exists(audio_path):
            return jsonify({"error": "找不到音频文件"}), 404

        # 使用Flask的send_file函数，但添加必要的响应头
        response = send_file(audio_path, mimetype='audio/mpeg', as_attachment=False)

        # 添加音频播放所需的响应头
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Content-Type-Options'] = 'nosniff'

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 清理临时文件的函数
def cleanup_temp_files():
    """清理临时文件"""
    for key in list(app.config.keys()):
        if key.startswith("TEMP_AUDIO_"):
            file_path = app.config[key]
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except Exception as e:
                    print(f"清理临时文件错误: {str(e)}")

# 注册启动后回调，添加CORS头
@app.after_request
def after_request_callback(response):
    """每次请求后添加CORS头并检查临时文件"""
    # 添加CORS头
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
