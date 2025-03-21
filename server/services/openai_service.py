import json
import openai
import config

# 配置OpenAI客户端
openai.api_key = config.OPENAI_API_KEY

class OpenAIService:
    """处理与OpenAI API的交互服务"""

    @staticmethod
    def moderate_content(text):
        """
        使用OpenAI Moderation API检查内容是否适合儿童

        参数:
            text: 需要检查的文本

        返回:
            (flagged, categories): flagged为布尔值表示是否被标记，categories为标记类别
        """
        try:
            response = openai.moderations.create(input=text)
            result = response.results[0]
            return (result.flagged, result.categories)
        except Exception as e:
            print(f"内容审核错误: {str(e)}")
            # 出错时默认通过，避免阻止正常对话
            return (False, None)

    @staticmethod
    def generate_friendly_warning(categories, language='en', conversation_context=None):
        """
        使用OpenAI生成友好的内容警告信息

        参数:
            categories: 被标记的内容类别
            language: 用户使用的语言代码 ('en' 或 'zh')
            conversation_context: 对话上下文（最近的消息列表）

        返回:
            友好的警告消息
        """
        try:
            # 构建系统提示
            system_prompt = "你是一个儿童友好的AI助手。你需要生成一条友好但坚定的警告消息，告诉儿童用户他们询问的内容不适合他们的年龄。"
            system_prompt += "不要重复或引用用户的不当内容。使用友好、善良但坚定的语气。"

            # 准备用户内容类别信息
            # 处理categories对象，适配不同版本的OpenAI API返回的格式
            # 获取被标记的类别
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
