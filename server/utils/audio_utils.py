"""
音频处理工具函数
提供音频文件处理、格式验证等功能
"""
import os
from typing import List, BinaryIO, Optional
from werkzeug.utils import secure_filename
import io

def is_valid_audio_format(filename: str, allowed_formats: List[str]) -> bool:
    """
    检查文件名是否为允许的音频格式

    参数:
        filename (str): 文件名
        allowed_formats (List[str]): 允许的文件格式列表

    返回:
        bool: 如果文件格式有效则返回True，否则返回False

    示例:
        >>> if is_valid_audio_format('recording.mp3', ['mp3', 'wav']):
        >>>     print("有效的音频文件格式")
    """
    # 获取文件扩展名
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    # 检查是否为允许的格式
    return file_ext in allowed_formats

def secure_audio_filename(filename: str) -> str:
    """
    安全化音频文件名，防止恶意文件名

    参数:
        filename (str): 原始文件名

    返回:
        str: 安全的文件名

    示例:
        >>> safe_name = secure_audio_filename("malicious../file.mp3")
        >>> print(safe_name)  # 输出: "malicious__file.mp3"
    """
    return secure_filename(filename)

def prepare_audio_file_for_api(file_obj: BinaryIO) -> tuple:
    """
    准备音频文件以发送给API

    参数:
        file_obj (BinaryIO): 原始文件对象

    返回:
        tuple: (文件类对象, 文件名)

    示例:
        >>> file_data, file_name = prepare_audio_file_for_api(request.files['audio'])
        >>> response = openai.audio.transcription.create(model="whisper-1", file=file_data)
    """
    # 读取文件内容
    file_content = file_obj.read()

    # 创建一个文件类对象
    file_data = io.BytesIO(file_content)
    file_data.name = file_obj.filename or "audio_file"  # 设置文件名

    return file_data, file_obj.filename

def get_audio_duration(file_path: str) -> Optional[float]:
    """
    获取音频文件的时长（秒）

    参数:
        file_path (str): 音频文件路径

    返回:
        Optional[float]: 音频时长（秒），如果无法获取则返回None

    示例:
        >>> duration = get_audio_duration("/path/to/audio.mp3")
        >>> if duration:
        >>>     print(f"音频时长: {duration}秒")

    注意:
        此函数需要安装pydub库: pip install pydub
    """
    try:
        from pydub import AudioSegment

        # 根据文件扩展名加载不同格式的音频
        file_ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''

        if file_ext == 'mp3':
            audio = AudioSegment.from_mp3(file_path)
        elif file_ext == 'wav':
            audio = AudioSegment.from_wav(file_path)
        elif file_ext == 'ogg':
            audio = AudioSegment.from_ogg(file_path)
        else:
            # 尝试自动检测格式
            audio = AudioSegment.from_file(file_path)

        # 返回时长（毫秒转秒）
        return len(audio) / 1000.0
    except Exception as e:
        print(f"获取音频时长错误: {str(e)}")
        return None
