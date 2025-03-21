"""
文件处理工具函数
提供文件操作、临时文件管理等功能
"""
import os
import tempfile
import shutil
from typing import Optional, Dict, List, Tuple, BinaryIO
from flask import current_app

def create_temp_file(data: bytes, suffix: str = '.mp3') -> Tuple[str, str]:
    """
    创建临时文件并存储二进制数据

    参数:
        data (bytes): 要存储的二进制数据
        suffix (str): 文件后缀，默认为'.mp3'

    返回:
        Tuple[str, str]: (临时文件路径, 文件名)

    示例:
        >>> audio_data = b'some binary audio data'
        >>> path, filename = create_temp_file(audio_data, '.mp3')
        >>> print(f"文件创建在: {path}, 文件名: {filename}")
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(data)
        audio_path = temp_file.name

    # 返回文件路径和文件名
    return audio_path, os.path.basename(audio_path)

def save_temp_file_reference(filename: str, file_path: str, app=None) -> None:
    """
    在Flask应用配置中保存临时文件引用

    参数:
        filename (str): 文件名
        file_path (str): 完整的文件路径
        app: Flask应用实例，默认使用current_app

    示例:
        >>> path, filename = create_temp_file(audio_data)
        >>> save_temp_file_reference(filename, path)
    """
    # 如果没有传入app参数，则尝试使用current_app
    config = app.config if app else current_app.config

    # 保存文件引用到应用配置
    config[f"TEMP_AUDIO_{filename}"] = file_path

def get_temp_file_path(filename: str, app=None) -> Optional[str]:
    """
    从Flask应用配置中获取临时文件路径

    参数:
        filename (str): 文件名
        app: Flask应用实例，默认使用current_app

    返回:
        Optional[str]: 文件路径，如果文件不存在则返回None

    示例:
        >>> file_path = get_temp_file_path('example.mp3')
        >>> if file_path:
        >>>     print(f"找到文件: {file_path}")
        >>> else:
        >>>     print("文件不存在")
    """
    # 如果没有传入app参数，则尝试使用current_app
    config = app.config if app else current_app.config

    # 从应用配置中获取文件路径
    file_path = config.get(f"TEMP_AUDIO_{filename}")

    # 验证文件是否存在
    if file_path and os.path.exists(file_path):
        return file_path

    return None

def cleanup_temp_files(app=None) -> List[str]:
    """
    清理所有临时文件

    参数:
        app: Flask应用实例，默认使用current_app

    返回:
        List[str]: 已删除的文件列表

    示例:
        >>> deleted_files = cleanup_temp_files()
        >>> print(f"已删除 {len(deleted_files)} 个临时文件")
    """
    # 如果没有传入app参数，则尝试使用current_app
    config = app.config if app else current_app.config
    deleted_files = []

    # 查找并删除所有临时音频文件
    for key in list(config.keys()):
        if key.startswith("TEMP_AUDIO_"):
            file_path = config[key]
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    deleted_files.append(file_path)
                except Exception as e:
                    print(f"清理临时文件错误: {str(e)}")

            # 从配置中移除引用
            del config[key]

    return deleted_files

def ensure_directory_exists(directory_path: str) -> bool:
    """
    确保目录存在，如果不存在则创建

    参数:
        directory_path (str): 目录路径

    返回:
        bool: 如果目录已存在或成功创建则返回True，否则返回False

    示例:
        >>> if ensure_directory_exists('/path/to/directory'):
        >>>     print("目录已就绪")
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        return True
    except Exception as e:
        print(f"创建目录错误: {str(e)}")
        return False

def is_valid_audio_file(file_obj: BinaryIO, allowed_formats: List[str]) -> bool:
    """
    检查文件是否为有效的音频文件

    参数:
        file_obj (BinaryIO): 文件对象
        allowed_formats (List[str]): 允许的文件格式列表

    返回:
        bool: 如果文件格式有效则返回True，否则返回False

    示例:
        >>> from flask import request
        >>> audio_file = request.files['audio']
        >>> if is_valid_audio_file(audio_file, ['mp3', 'wav']):
        >>>     print("有效的音频文件")
    """
    filename = file_obj.filename
    if not filename:
        return False

    # 获取文件扩展名
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    # 检查是否为允许的格式
    return file_ext in allowed_formats
