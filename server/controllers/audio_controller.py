"""
音频文件控制器
"""
import os
from flask import jsonify, send_file, current_app

def get_audio(filename):
    """获取生成的音频文件"""
    try:
        audio_path = current_app.config.get(f"TEMP_AUDIO_{filename}")
        if not audio_path or not os.path.exists(audio_path):
            return jsonify({"error": "Audio file not found"}), 404

        # 使用Flask的send_file函数，但添加必要的响应头
        response = send_file(audio_path, mimetype='audio/mpeg', as_attachment=False)

        # 添加音频播放所需的响应头
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Content-Type-Options'] = 'nosniff'

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cleanup_temp_files(app=None):
    """清理临时文件"""
    # 如果没有传入app参数，则尝试使用current_app
    config = app.config if app else current_app.config

    for key in list(config.keys()):
        if key.startswith("TEMP_AUDIO_"):
            file_path = config[key]
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except Exception as e:
                    print(f"清理临时文件错误: {str(e)}")
