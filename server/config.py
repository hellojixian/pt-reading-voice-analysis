import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# OpenAI API设置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("必须设置OPENAI_API_KEY环境变量")

# 服务器设置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "True").lower() in ["true", "1", "t"]

# 跨域设置
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

# 应用设置
MAX_AUDIO_LENGTH_SECONDS = 60  # 最大录音长度（秒）
ALLOWED_AUDIO_FORMATS = ["mp3", "wav", "ogg", "webm"]
