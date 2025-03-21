"""
Assistant服务
提供OpenAI Assistant API相关的功能
"""
import os
import json
import time
import tempfile
from typing import Dict, List, Optional, Any, Tuple, Union

import openai
from flask import current_app

from services.openai_service import OpenAIService
from services.speech_service import SpeechService
from utils.file_utils import create_temp_file, save_temp_file_reference
from utils.markdown_utils import render_markdown_to_html
import config

class AssistantService:
    """
    Assistant服务类

    处理基于OpenAI Assistant API的对话功能，包括线程管理、消息处理和函数调用。

    属性:
        openai_service (OpenAIService): OpenAI服务实例
        speech_service (SpeechService): 语音服务实例
        user_threads (Dict[str, str]): 用户线程ID字典
    """

    def __init__(self, openai_service: Optional[OpenAIService] = None,
                 speech_service: Optional[SpeechService] = None):
        """
        初始化Assistant服务

        参数:
            openai_service (Optional[OpenAIService]): OpenAI服务实例，如不提供则创建新实例
            speech_service (Optional[SpeechService]): 语音服务实例，如不提供则创建新实例

        示例:
            >>> service = AssistantService()  # 使用默认服务实例
            >>> service = AssistantService(openai_service=custom_openai, speech_service=custom_speech)  # 使用自定义服务实例
        """
        self.openai_service = openai_service or OpenAIService()
        self.speech_service = speech_service or SpeechService()
        self.user_threads = {}  # 用于存储用户线程ID的字典
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)

    def init_assistant_thread(self, session_id: str = 'default_user') -> str:
        """
        初始化Assistant线程，如果不存在则创建新线程

        参数:
            session_id (str): 用户会话ID，默认为'default_user'

        返回:
            str: 线程ID

        示例:
            >>> thread_id = assistant_service.init_assistant_thread("user123")
            >>> print(f"用户线程ID: {thread_id}")
        """
        try:
            # 如果线程不存在，则创建一个新线程
            if session_id not in self.user_threads:
                thread = self.client.beta.threads.create()
                self.user_threads[session_id] = thread.id
                print(f"已为用户 {session_id} 创建新线程: {thread.id}")

            return self.user_threads[session_id]

        except Exception as e:
            print(f"初始化线程错误: {str(e)}")
            raise

    def process_chat(self, message: str, session_id: str = 'default_user',
                     language: str = 'en', is_stream: bool = False) -> Dict[str, Any]:
        """
        处理用户聊天消息

        参数:
            message (str): 用户消息内容
            session_id (str): 用户会话ID，默认为'default_user'
            language (str): 用户语言代码，'en'或'zh'
            is_stream (bool): 是否使用流式响应

        返回:
            Dict[str, Any]: 包含回复文本、音频URL和其他信息的字典

        示例:
            >>> response = assistant_service.process_chat("推荐一些冒险类图书", session_id="user123", language="zh")
            >>> print(f"AI回复: {response['text']}")
            >>> print(f"音频URL: {response['audio_url']}")
        """
        # 内容审核
        is_flagged, categories = self.openai_service.moderate_content(message)

        if is_flagged:
            return self._handle_flagged_content(categories, language)

        # 初始化或获取用户的线程ID
        thread_id = self.init_assistant_thread(session_id)

        # 获取当前Assistant ID
        assistant_id = self._get_assistant_id()

        # 向线程添加用户消息
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )

        # 运行助手
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )

        # 处理运行
        function_results = []
        run_status = self._process_run(thread_id, run.id, function_results, is_stream)

        if run_status not in ['completed']:
            return {"error": f"Assistant run failed: {run_status}"}

        # 获取助手回复
        return self._get_assistant_reply(thread_id, function_results)

    def chat_stream(self, message: str, session_id: str = 'default_user', language: str = 'en'):
        """
        使用流式处理用户聊天消息（生成器函数）

        参数:
            message (str): 用户消息内容
            session_id (str): 用户会话ID，默认为'default_user'
            language (str): 用户语言代码，'en'或'zh'

        返回:
            generator: 事件流生成器

        示例:
            >>> for event in assistant_service.chat_stream("Hello", "user123"):
            >>>     print(f"事件: {event}")
        """
        # 内容审核
        is_flagged, categories = self.openai_service.moderate_content(message)

        # 格式化SSE消息的辅助函数
        def format_sse(event, data):
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        # 发送初始状态
        yield format_sse("status", {"status": "Analyzing your request..."})

        if is_flagged:
            # 处理被标记的内容
            yield format_sse("status", {"status": "Content moderation check..."})
            warning_result = self._handle_flagged_content(categories, language)
            yield format_sse("complete", warning_result)
            return

        try:
            # 初始化线程
            thread_id = self.init_assistant_thread(session_id)

            # 获取Assistant ID
            assistant_id = self._get_assistant_id()
            if not assistant_id:
                yield format_sse("error", {"error": "Assistant ID not configured"})
                return

            # 添加用户消息
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )

            yield format_sse("status", {"status": "Thinking..."})

            # 运行助手
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
            )

            # 初始化函数调用结果
            function_results = []

            # 处理运行
            while True:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )

                # 发送状态更新
                yield format_sse("status", {"status": f"Assistant status: {run_status.status}"})

                if run_status.status == 'completed':
                    yield format_sse("status", {"status": "Generating response..."})
                    break

                elif run_status.status == 'requires_action':
                    # 处理函数调用
                    yield from self._handle_function_calls_stream(
                        thread_id, run_status, run.id, function_results, format_sse
                    )

                elif run_status.status in ['failed', 'cancelled', 'expired']:
                    yield format_sse("error", {"error": f"Assistant run failed: {run_status.status}"})
                    return

                # 等待后再检查状态
                time.sleep(0.5)

            # 获取助手回复
            reply = self._get_assistant_reply(thread_id, function_results)

            # 发送完成事件
            yield format_sse("complete", reply)

        except Exception as e:
            yield format_sse("error", {"error": str(e)})

    def _get_assistant_id(self) -> Optional[str]:
        """
        获取当前Assistant ID

        返回:
            Optional[str]: Assistant ID或None
        """
        # 从环境变量获取
        assistant_id = os.getenv('OPENAI_ASSISTANT_ID')
        if not assistant_id:
            # 从应用配置获取
            assistant_id = current_app.config.get('OPENAI_ASSISTANT_ID')
        return assistant_id

    def _handle_flagged_content(self, categories: Any, language: str) -> Dict[str, Any]:
        """
        处理被标记为不适当的内容

        参数:
            categories (Any): 被标记的内容类别
            language (str): 用户语言代码

        返回:
            Dict[str, Any]: 包含警告信息的响应字典
        """
        # 生成警告信息
        warning_message = self.openai_service.generate_friendly_warning(categories, language)

        # 生成语音
        audio_data = self.openai_service.text_to_speech(warning_message)

        # 创建临时文件
        audio_path, filename = create_temp_file(audio_data, suffix='.mp3')

        # 保存文件引用
        save_temp_file_reference(filename, audio_path)

        # 构建警告响应
        return {
            "text": warning_message,
            "html": render_markdown_to_html(warning_message),
            "is_warning": True,
            "audio_url": f"/api/audio/{filename}"
        }

    def _process_run(self, thread_id: str, run_id: str, function_results: List[Dict[str, Any]],
                     is_stream: bool = False) -> str:
        """
        处理Assistant运行

        参数:
            thread_id (str): 线程ID
            run_id (str): 运行ID
            function_results (List[Dict[str, Any]]): 存储函数调用结果的列表
            is_stream (bool): 是否为流式处理

        返回:
            str: 运行状态
        """
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )

            if run_status.status == 'completed':
                return 'completed'

            elif run_status.status == 'requires_action':
                # 处理函数调用
                self._handle_function_calls(thread_id, run_status, run_id, function_results)

            elif run_status.status in ['failed', 'cancelled', 'expired']:
                return run_status.status

            # 等待后再检查状态
            time.sleep(0.5)

    def _handle_function_calls(self, thread_id: str, run_status: Any, run_id: str,
                              function_results: List[Dict[str, Any]]) -> None:
        """
        处理函数调用

        参数:
            thread_id (str): 线程ID
            run_status (Any): 运行状态对象
            run_id (str): 运行ID
            function_results (List[Dict[str, Any]]): 存储函数调用结果的列表
        """
        if run_status.required_action.type == "submit_tool_outputs":
            tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                # 记录函数调用
                function_results.append({
                    "name": function_name,
                    "arguments": function_args
                })

                # 处理不同的函数调用
                result = self._execute_function(function_name, function_args)

                # 记录函数调用结果
                function_results[-1]["result"] = result

                # 添加到工具输出
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(result)
                })

            # 提交函数执行结果
            self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs
            )

    def _handle_function_calls_stream(self, thread_id: str, run_status: Any, run_id: str,
                                     function_results: List[Dict[str, Any]], format_sse) -> Any:
        """
        处理流式函数调用

        参数:
            thread_id (str): 线程ID
            run_status (Any): 运行状态对象
            run_id (str): 运行ID
            function_results (List[Dict[str, Any]]): 存储函数调用结果的列表
            format_sse: 格式化SSE消息的函数

        返回:
            generator: 事件流生成器
        """
        if run_status.required_action.type == "submit_tool_outputs":
            tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []

            yield format_sse("status", {"status": "Executing function calls..."})

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                # 记录函数调用
                function_results.append({
                    "name": function_name,
                    "arguments": function_args
                })

                yield format_sse("status", {"status": f"Calling function: {function_name}"})

                # 提供进度更新
                function_type = self._get_function_type(function_name)
                if function_type:
                    yield format_sse("progress", {
                        "status": f"Processing {function_type}...",
                        "progress": {
                            "type": function_type,
                            "icon": self._get_function_icon(function_type)
                        }
                    })

                # 处理不同的函数调用
                result = self._execute_function(function_name, function_args,
                                              yield_status=lambda s: format_sse("status", {"status": s}))

                # 记录函数调用结果
                function_results[-1]["result"] = result

                # 添加到工具输出
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(result)
                })

            # 提交函数执行结果
            self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs
            )

    def _execute_function(self, function_name: str, function_args: Dict[str, Any],
                         yield_status=None) -> Dict[str, Any]:
        """
        执行函数调用

        参数:
            function_name (str): 函数名称
            function_args (Dict[str, Any]): 函数参数
            yield_status: 状态更新回调函数

        返回:
            Dict[str, Any]: 函数执行结果
        """
        # 根据不同的函数名执行不同的功能
        if function_name == "recommend_books":
            user_interests = function_args.get("user_interests", "")

            if yield_status:
                yield_status("Analyzing reading interests and recommending books...")

            # 获取书籍推荐助手ID
            book_recommendation_assistant_id = current_app.config.get('BOOK_RECOMMANDATION_ASSISTANT_ID')
            if not book_recommendation_assistant_id:
                if yield_status:
                    yield_status("Book recommendation assistant ID not configured")
                return {"status": "error", "recommended_books": []}

            # 调用search_books_by_interest
            from libs import openai_assistant as oa
            recommended_books = oa.search_books_by_interest(
                book_recommendation_assistant_id,
                user_interests
            )

            if yield_status:
                yield_status(f"Found {len(recommended_books)} matching book recommendations")

            return {"status": "success", "recommended_books": recommended_books}

        elif function_name == "search_book_by_title":
            title = function_args.get("title", "")

            if yield_status:
                yield_status(f"Searching for books matching title: {title}")

            # 获取书籍推荐助手ID来获取关联的vector_store_id
            book_recommendation_assistant_id = current_app.config.get('BOOK_RECOMMANDATION_ASSISTANT_ID')
            if not book_recommendation_assistant_id:
                if yield_status:
                    yield_status("Book recommendation assistant ID not configured")
                return {"status": "error", "matched_books": []}

            # 获取助手详情以获取vector_store_id
            from libs import openai_assistant as oa
            client = openai.OpenAI()
            assistant = client.beta.assistants.retrieve(book_recommendation_assistant_id)

            if assistant.tool_resources and assistant.tool_resources.file_search:
                vector_store_ids = assistant.tool_resources.file_search.vector_store_ids
                if vector_store_ids:
                    vector_store_id = vector_store_ids[0]
                    if yield_status:
                        yield_status(f"Searching using vector_store: {vector_store_id}")

                    matched_books = oa.search_book_by_title(vector_store_id, title)

                    if yield_status:
                        yield_status(f"Found {len(matched_books)} matching books")

                    return {"status": "success", "matched_books": matched_books}

            return {"status": "error", "matched_books": []}

        elif function_name == "get_book_content":
            book_id = function_args.get("book_id", "")

            if yield_status:
                yield_status(f"Retrieving content for book: {book_id}")

            # 调用data_source获取图书内容
            from libs import openai_assistant as oa
            book_data = oa.get_book_content(book_id)

            if book_data:
                if yield_status:
                    yield_status(f"Successfully retrieved content for '{book_data['book_title']}'")
                return {"status": "success", "book": book_data}
            else:
                if yield_status:
                    yield_status(f"Book with ID {book_id} not found")
                return {"status": "not_found", "book": None}

        return {"status": "function_not_found"}

    def _get_assistant_reply(self, thread_id: str, function_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取Assistant的回复

        参数:
            thread_id (str): 线程ID
            function_results (List[Dict[str, Any]]): 函数调用结果列表

        返回:
            Dict[str, Any]: 包含回复文本、音频URL和函数调用结果的字典
        """
        # 获取最新的助手回复
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)

        # 获取最新的助手回复（第一条消息是最新的）
        assistant_message = None
        for msg in messages.data:
            if msg.role == "assistant":
                assistant_message = msg
                break

        if not assistant_message:
            return {"error": "No response received from assistant"}

        # 提取文本内容
        ai_response = ""
        for content in assistant_message.content:
            if content.type == "text":
                # 使用openai_assistant模块中的clean_text函数清理文本
                from libs.openai_assistant import clean_text
                ai_response += clean_text(content.text.value)

        # 生成语音
        audio_data = self.openai_service.text_to_speech(ai_response)

        # 创建临时文件
        audio_path, filename = create_temp_file(audio_data, suffix='.mp3')

        # 保存文件引用
        save_temp_file_reference(filename, audio_path)

        # 构建响应
        return {
            "text": ai_response,
            "html": render_markdown_to_html(ai_response),
            "audio_url": f"/api/audio/{filename}",
            "function_results": function_results
        }

    def _get_function_type(self, function_name: str) -> Optional[str]:
        """
        根据函数名获取函数类型

        参数:
            function_name (str): 函数名称

        返回:
            Optional[str]: 函数类型或None
        """
        function_types = {
            "recommend_books": "book_recommendation",
            "search_book_by_title": "book_search",
            "get_book_content": "book_content"
        }
        return function_types.get(function_name)

    def _get_function_icon(self, function_type: str) -> str:
        """
        根据函数类型获取图标

        参数:
            function_type (str): 函数类型

        返回:
            str: 图标字符
        """
        icons = {
            "book_recommendation": "📚",
            "book_search": "🔍",
            "book_content": "📖"
        }
        return icons.get(function_type, "🔄")

    @staticmethod
    def ensure_assistant() -> str:
        """
        确保Assistant存在，若不存在则创建

        返回:
            str: Assistant ID

        示例:
            >>> assistant_id = AssistantService.ensure_assistant()
            >>> print(f"Assistant ID: {assistant_id}")
        """
        from libs import openai_assistant as oa
        return oa.ensure_assistant()

    @staticmethod
    def ensure_book_recommendation_assistant(library_data_file: str) -> str:
        """
        确保图书推荐Assistant存在，若不存在则创建

        参数:
            library_data_file (str): 图书数据文件路径

        返回:
            str: 图书推荐Assistant ID

        示例:
            >>> assistant_id = AssistantService.ensure_book_recommendation_assistant("/path/to/library.json")
            >>> print(f"Book Recommendation Assistant ID: {assistant_id}")
        """
        from libs import openai_assistant as oa
        return oa.ensure_assistant_for_recommand_books(library_data_file)

    @staticmethod
    def delete_assistant(assistant_id: str) -> None:
        """
        删除Assistant及其关联资源

        参数:
            assistant_id (str): Assistant ID

        示例:
            >>> AssistantService.delete_assistant("asst_abc123")
            >>> print("Assistant deleted")
        """
        from libs import openai_assistant as oa
        oa.delete_assistant(assistant_id)
