import json
import openai
import config

# 配置OpenAI客户端
openai.api_key = config.OPENAI_API_KEY

class OpenAIService:
    """处理与OpenAI API的交互服务"""

    @staticmethod
    def transcribe_audio(audio_file):
        """
        使用OpenAI Whisper API将音频转换为文本

        参数:
            audio_file: 音频文件对象

        返回:
            转录的文本
        """
        try:
            # 读取文件内容而不是直接传递FileStorage对象
            file_content = audio_file.read()

            # 使用io.BytesIO创建一个文件类对象
            import io
            file_data = io.BytesIO(file_content)
            file_data.name = audio_file.filename  # 设置文件名

            response = openai.audio.transcriptions.create(
                model="whisper-1",
                file=file_data
            )
            return response.text
        except Exception as e:
            print(f"音频转文字错误: {str(e)}")
            raise

    @staticmethod
    def get_chat_response(messages):
        """
        使用OpenAI Chat API获取回复

        参数:
            messages: 对话历史消息列表

        返回:
            AI的回复文本
        """
        try:
            response = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"获取聊天回复错误: {str(e)}")
            raise

    @staticmethod
    def text_to_speech(text, voice="alloy"):
        """
        使用OpenAI TTS API将文本转换为语音

        参数:
            text: 要转换的文本
            voice: 语音类型 (alloy, echo, fable, onyx, nova, shimmer)

        返回:
            音频数据的二进制内容
        """
        try:
            response = openai.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            return response.content
        except Exception as e:
            print(f"文字转语音错误: {str(e)}")
            raise
