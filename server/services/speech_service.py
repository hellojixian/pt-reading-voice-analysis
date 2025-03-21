"""
语音服务
提供语音转文本、文本转语音等功能
"""
import os
import tempfile
from typing import Optional, Dict, Tuple, BinaryIO, Any

from flask import current_app
from werkzeug.utils import secure_filename

from services.openai_service import OpenAIService
from utils.file_utils import create_temp_file, save_temp_file_reference
from utils.audio_utils import is_valid_audio_format, prepare_audio_file_for_api
import config

class SpeechService:
    """
    语音服务类

    处理语音转文本、文本转语音相关功能，包括音频文件处理、转换和存储。

    属性:
        openai_service (OpenAIService): OpenAI服务实例
        allowed_formats (list): 允许的音频格式列表
        voice (str): 默认TTS语音类型
    """

    def __init__(self, openai_service: Optional[OpenAIService] = None,
                 allowed_formats: Optional[list] = None,
                 voice: Optional[str] = None):
        """
        初始化语音服务

        参数:
            openai_service (Optional[OpenAIService]): OpenAI服务实例，如不提供则创建新实例
            allowed_formats (Optional[list]): 允许的音频格式列表，默认为配置中的值
            voice (Optional[str]): 默认的语音类型，默认为配置中的值

        示例:
            >>> service = SpeechService()  # 使用默认配置
            >>> service = SpeechService(voice="nova")  # 指定语音类型
        """
        self.openai_service = openai_service or OpenAIService()
        self.allowed_formats = allowed_formats or config.ALLOWED_AUDIO_FORMATS
        self.voice = voice or os.getenv("OPENAI_VOICE", "alloy")

    def transcribe_audio(self, audio_file: BinaryIO) -> Dict[str, str]:
        """
        将音频文件转换为文本

        参数:
            audio_file (BinaryIO): 音频文件对象

        返回:
            Dict[str, str]: 包含转录文本的字典

        异常:
            ValueError: 如果文件格式无效
            Exception: 如果转录过程中出错

        示例:
            >>> from flask import request
            >>> audio_file = request.files['audio']
            >>> result = speech_service.transcribe_audio(audio_file)
            >>> print(f"转录结果: {result['text']}")
        """
        # 检查文件类型
        filename = secure_filename(audio_file.filename or "")
        if not is_valid_audio_format(filename, self.allowed_formats):
            raise ValueError(f"不支持的音频格式，请使用以下格式之一: {', '.join(self.allowed_formats)}")

        # 使用OpenAI的Whisper API进行转录
        text = self.openai_service.transcribe_audio(audio_file)

        return {"text": text}

    def text_to_speech(self, text: str, voice: Optional[str] = None) -> Dict[str, str]:
        """
        将文本转换为语音

        参数:
            text (str): 要转换的文本
            voice (Optional[str]): 语音类型，默认使用实例的voice属性

        返回:
            Dict[str, str]: 包含音频URL的字典

        异常:
            Exception: 如果转换过程中出错

        示例:
            >>> result = speech_service.text_to_speech("你好，世界！", voice="nova")
            >>> print(f"音频URL: {result['audio_url']}")
        """
        # 使用指定的语音或默认语音
        voice_to_use = voice or self.voice

        # 生成语音
        audio_data = self.openai_service.text_to_speech(text, voice_to_use)

        # 创建临时文件保存音频
        audio_path, filename = create_temp_file(audio_data, suffix='.mp3')

        # 保存文件路径以便后续请求
        save_temp_file_reference(filename, audio_path)

        return {"audio_url": f"/api/audio/{filename}"}

    def moderate_and_respond(self, text: str, language: str = 'en') -> Dict[str, Any]:
        """
        审核内容并生成响应，如果内容不适当则生成警告

        参数:
            text (str): 要审核的文本内容
            language (str): 语言代码，'en'或'zh'

        返回:
            Dict[str, Any]: 包含响应信息的字典

        示例:
            >>> result = speech_service.moderate_and_respond("一些内容", language="zh")
            >>> if result.get("is_warning"):
            >>>     print("内容被标记为不适当")
            >>> else:
            >>>     print(f"回复: {result['text']}")
        """
        # 内容审核
        is_flagged, categories = self.openai_service.moderate_content(text)

        if is_flagged:
            # 生成警告信息
            warning_message = self.openai_service.generate_friendly_warning(categories, language)

            # 生成语音
            audio_data = self.openai_service.text_to_speech(warning_message)

            # 创建临时文件保存音频
            audio_path, filename = create_temp_file(audio_data, suffix='.mp3')

            # 保存文件引用
            save_temp_file_reference(filename, audio_path)

            # 构建警告响应
            return {
                "text": warning_message,
                "is_warning": True,
                "audio_url": f"/api/audio/{filename}"
            }

        return {"is_flagged": False}
