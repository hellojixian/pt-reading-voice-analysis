"""
OpenAI服务 - 基础服务
提供与OpenAI API交互的核心功能
"""
import json
import openai
from typing import Any, Dict, List, Optional, Tuple, Union
import config

# 配置OpenAI客户端
openai.api_key = config.OPENAI_API_KEY

class OpenAIService:
    """
    处理与OpenAI API的交互服务

    此类提供了与OpenAI API交互的基础功能，包括内容审核、对话生成、语音转文本和文本转语音功能。

    属性:
        api_key (str): OpenAI API密钥
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化OpenAIService实例

        参数:
            api_key (Optional[str]): OpenAI API密钥，如果不提供则使用config中的密钥

        示例:
            >>> service = OpenAIService()  # 使用配置文件中的API密钥
            >>> service = OpenAIService(api_key="your-api-key")  # 使用自定义API密钥
        """
        self.api_key = api_key or config.OPENAI_API_KEY
        openai.api_key = self.api_key

    def moderate_content(self, text: str) -> Tuple[bool, Any]:
        """
        使用OpenAI Moderation API检查内容是否适合儿童

        参数:
            text (str): 需要检查的文本

        返回:
            Tuple[bool, Any]:
                - 第一个元素是布尔值，表示内容是否被标记为不适当
                - 第二个元素是标记类别对象

        示例:
            >>> is_flagged, categories = service.moderate_content("这是一段正常文本")
            >>> if is_flagged:
            >>>     print(f"内容被标记为不适当，类别: {categories}")
            >>> else:
            >>>     print("内容适合儿童")
        """
        try:
            response = openai.moderations.create(input=text)
            result = response.results[0]
            return (result.flagged, result.categories)
        except Exception as e:
            print(f"内容审核错误: {str(e)}")
            # 出错时默认通过，避免阻止正常对话
            return (False, None)

    def generate_friendly_warning(self, categories: Any, language: str = 'en',
                                 conversation_context: Optional[List[Dict[str, str]]] = None) -> str:
        """
        使用OpenAI生成友好的内容警告信息

        参数:
            categories (Any): 被标记的内容类别
            language (str): 用户使用的语言代码 ('en' 或 'zh')
            conversation_context (Optional[List[Dict[str, str]]]): 对话上下文（最近的消息列表）

        返回:
            str: 友好的警告消息

        示例:
            >>> categories = {'sexual': True, 'hate': False, 'violence': False}
            >>> warning = service.generate_friendly_warning(categories, language='zh')
            >>> print(warning)
        """
        try:
            # 构建系统提示
            system_prompt = "你是一个儿童友好的AI助手。你需要生成一条友好但坚定的警告消息，告诉儿童用户他们询问的内容不适合他们的年龄。"
            system_prompt += "不要重复或引用用户的不当内容。使用友好、善良但坚定的语气。"

            # 获取被标记的类别
            flagged_categories = self._extract_flagged_categories(categories)

            # 生成类别信息
            category_info = f"用户询问了关于以下内容的问题: {', '.join(flagged_categories) if flagged_categories else '不适当内容'}"

            # 添加对话上下文概括（如果有）
            context_summary = ""
            if conversation_context and len(conversation_context) > 1:
                recent_messages = conversation_context[-3:-1] if len(conversation_context) > 2 else conversation_context[:-1]
                context_summary = "对话的主题是关于: " + ", ".join([msg.get("content", "")[:50] for msg in recent_messages])

            # 语言指示
            lang_instruction = "请用中文回复" if language == 'zh' else "Please respond in English"

            # 构建用户提示
            user_prompt = f"{category_info}\n{context_summary}\n{lang_instruction}\n请生成一个友好但明确的警告，让孩子明白这个话题不适合他们，并鼓励他们询问适合年龄的内容。"

            # 调用OpenAI API
            response = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )

            warning_message = response.choices[0].message.content
            return warning_message

        except Exception as e:
            print(f"生成警告信息错误: {str(e)}")
            # 出错时返回默认警告
            if language == 'zh':
                return "不要淘气，这不是你这个年龄该知道的内容哦！让我们聊一些有趣又健康的话题吧。"
            else:
                return "Don't be naughty! This isn't something for someone your age. Let's talk about fun and healthy topics instead!"

    def transcribe_audio(self, audio_file: Any) -> str:
        """
        使用OpenAI Whisper API将音频转换为文本

        参数:
            audio_file (Any): 音频文件对象

        返回:
            str: 转录的文本

        示例:
            >>> from flask import request
            >>> audio_file = request.files['audio']
            >>> transcription = service.transcribe_audio(audio_file)
            >>> print(f"转录文本: {transcription}")
        """
        try:
            # 处理文件
            from utils.audio_utils import prepare_audio_file_for_api
            file_data, _ = prepare_audio_file_for_api(audio_file)

            response = openai.audio.transcriptions.create(
                model="whisper-1",
                file=file_data
            )
            return response.text
        except Exception as e:
            print(f"音频转文字错误: {str(e)}")
            raise

    def get_chat_response(self, messages: List[Dict[str, str]]) -> str:
        """
        使用OpenAI Chat API获取回复

        参数:
            messages (List[Dict[str, str]]): 对话历史消息列表

        返回:
            str: AI的回复文本

        示例:
            >>> messages = [
            >>>     {"role": "system", "content": "你是一个有帮助的助手。"},
            >>>     {"role": "user", "content": "你好，请问今天天气如何？"}
            >>> ]
            >>> response = service.get_chat_response(messages)
            >>> print(f"AI回复: {response}")
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

    def text_to_speech(self, text: str, voice: str = "alloy") -> bytes:
        """
        使用OpenAI TTS API将文本转换为语音

        参数:
            text (str): 要转换的文本
            voice (str): 语音类型 (alloy, echo, fable, onyx, nova, shimmer)

        返回:
            bytes: 音频数据的二进制内容

        示例:
            >>> text = "你好，我是AI助手。"
            >>> audio_data = service.text_to_speech(text, voice="alloy")
            >>> # 保存为MP3文件
            >>> with open("output.mp3", "wb") as f:
            >>>     f.write(audio_data)
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

    def _extract_flagged_categories(self, categories: Any) -> List[str]:
        """
        从分类对象中提取被标记的类别

        参数:
            categories (Any): 类别对象，可能是dict或OpenAI模型对象

        返回:
            List[str]: 被标记的类别列表
        """
        flagged_categories = []
        if hasattr(categories, 'items'):
            # Dict-like object
            for cat, cat_obj in categories.items():
                if isinstance(cat_obj, bool) and cat_obj:
                    flagged_categories.append(cat)
                elif hasattr(cat_obj, 'flagged') and cat_obj.flagged:
                    flagged_categories.append(cat)
        elif hasattr(categories, '__dict__'):
            # 对象格式，有属性
            for cat, value in categories.__dict__.items():
                if isinstance(value, bool) and value:
                    flagged_categories.append(cat)
        else:
            # 简单尝试直接遍历所有可能被标记的类别
            possible_categories = [
                'sexual', 'hate', 'harassment', 'self-harm',
                'sexual/minors', 'hate/threatening', 'violence/graphic',
                'self-harm/intent', 'self-harm/instructions', 'harassment/threatening',
                'violence'
            ]
            for cat in possible_categories:
                if hasattr(categories, cat) and getattr(categories, cat):
                    flagged_categories.append(cat)

        return flagged_categories
