"""
OpenAI Assistant 控制器
处理基于 OpenAI Assistant API 的聊天功能
"""
import os
import tempfile
import time
import json
import threading
from functools import wraps
from flask import jsonify, request, current_app, Response, stream_with_context

# 导入 OpenAI Assistant 相关库
import openai
from libs import openai_assistant
from services.openai_service import OpenAIService

# 初始化服务
openai_service = OpenAIService()

# 用于存储用户线程ID的字典
# 在实际应用中，这应该存储在数据库中
user_threads = {}

def init_assistant_thread():
    """初始化 Assistant 线程，如果不存在则创建"""
    try:
        # 获取当前会话 ID（在实际应用中，这应该是用户特定的）
        session_id = request.cookies.get('session_id', 'default_user')

        # 如果线程不存在，则创建一个新线程
        if session_id not in user_threads:
            client = openai.OpenAI()
            thread = client.beta.threads.create()
            user_threads[session_id] = thread.id
            print(f"已为用户 {session_id} 创建新线程: {thread.id}")

        return user_threads[session_id]

    except Exception as e:
        print(f"初始化线程错误: {str(e)}")
        raise

# 辅助函数 - 创建SSE格式的消息
def format_sse(event, data):
    """
    格式化用于服务器发送事件（SSE）的消息

    参数:
        event: 事件名称
        data: 事件数据（将被转换为JSON）

    返回:
        格式化的SSE消息字符串
    """
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def assistant_chat_stream():
    """使用服务器发送事件（SSE）处理基于 Assistant API 的流式聊天请求"""
    # 获取消息内容
    message = request.args.get('message')
    if not message:
        return jsonify({"error": "Message content missing"}), 400

    # 获取用户语言（如果传入）
    lang = request.args.get('language', 'en')

    # 内容审核
    is_flagged, categories = openai_service.moderate_content(message)
    print(f"是否被标记: {is_flagged}, 类别: {categories}")

    # 初始化或获取用户的线程ID
    try:
        thread_id = init_assistant_thread()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    def generate():
        # 发送初始状态
        yield format_sse("status", {"status": "Analyzing your request..."})

        try:
            # 检查内容是否被标记为不适当
            if is_flagged:
                yield format_sse("status", {"status": "Content moderation check..."})

                # 动态生成友好的警告信息
                context = []  # 流式模式下不需要对话上下文
                warning_message = openai_service.generate_friendly_warning(categories, lang, context)

                # 构建警告响应
                response = {
                    "text": warning_message,
                    "is_warning": True
                }

                # 直接返回警告，不继续处理请求
                yield format_sse("complete", response)
                return

            # 内容审核通过，继续正常处理
            client = openai.OpenAI()

            # 获取当前 Assistant ID
            assistant_id = os.getenv('OPENAI_ASSISTANT_ID', None)
            if not assistant_id:
                assistant_id = current_app.config.get('OPENAI_ASSISTANT_ID')
                if not assistant_id:
                    yield format_sse("error", {"error": "Assistant ID not configured"})
                    return

            # 向线程添加用户消息
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )

            yield format_sse("status", {"status": "Thinking..."})

            # 运行助手
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
            )

            # 初始化函数调用结果
            function_results = []

            # 等待运行完成
            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )

                # 发送当前状态更新
                yield format_sse("status", {"status": f"Assistant status: {run_status.status}"})

                if run_status.status == 'completed':
                    yield format_sse("status", {"status": "Generating response..."})
                    break

                elif run_status.status == 'requires_action':
                    yield format_sse("status", {"status": "Executing function call..."})

                    # 处理函数调用请求
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

                            yield format_sse("status", {"status": f"Calling function: {function_name}"})

                            # 根据函数名称处理不同的函数调用
                            if function_name == "recommend_books":
                                yield format_sse("progress", {
                                    "status": "Analyzing reading interests and recommending books...",
                                    "progress": {
                                        "type": "book_recommendation",
                                        "icon": "📚"
                                    }
                                })

                                # 处理图书推荐函数调用
                                user_interests = function_args.get("user_interests", "")

                                # 获取书籍推荐助手 ID
                                book_recommandation_assistant_id = current_app.config.get('BOOK_RECOMMANDATION_ASSISTANT_ID')
                                if not book_recommandation_assistant_id:
                                    yield format_sse("status", {"status": "Book recommendation assistant ID not configured, cannot provide book recommendations"})
                                    recommended_books = []
                                else:
                                    # 调用 search_books_by_interest 获取推荐书籍
                                    from libs import openai_assistant as oa
                                    recommended_books = oa.search_books_by_interest(
                                        book_recommandation_assistant_id,
                                        user_interests
                                    )

                                    yield format_sse("status", {"status": "Found matching book recommendations"})

                                # 记录函数调用结果
                                function_results[-1]["result"] = recommended_books

                                # 返回推荐书籍给对话助手
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": json.dumps({
                                        "status": "success",
                                        "recommended_books": recommended_books
                                    })
                                })

                            elif function_name == "search_book_by_title":
                                yield format_sse("progress", {
                                    "status": "Searching for books matching the title...",
                                    "progress": {
                                        "type": "book_search",
                                        "icon": "🔍"
                                    }
                                })

                                # 处理根据书名搜索图书函数调用
                                title = function_args.get("title", "")

                                # 获取书籍推荐助手 ID来获取关联的vector_store_id
                                book_recommandation_assistant_id = current_app.config.get('BOOK_RECOMMANDATION_ASSISTANT_ID')
                                if not book_recommandation_assistant_id:
                                    yield format_sse("status", {"status": "Book recommendation assistant ID not configured, cannot search for books"})
                                    matched_books = []
                                else:
                                    # 获取助手详情以获取vector_store_id
                                    from libs import openai_assistant as oa
                                    client = openai.OpenAI()
                                    assistant = client.beta.assistants.retrieve(book_recommandation_assistant_id)

                                    if assistant.tool_resources and assistant.tool_resources.file_search:
                                        vector_store_ids = assistant.tool_resources.file_search.vector_store_ids
                                        if vector_store_ids:
                                            vector_store_id = vector_store_ids[0]
                                            yield format_sse("status", {"status": f"Searching for title using vector_store: {title}"})
                                            matched_books = oa.search_book_by_title(vector_store_id, title)

                                            if matched_books:
                                                yield format_sse("status", {"status": f"Found {len(matched_books)} matching books"})
                                            else:
                                                yield format_sse("status", {"status": "No matching books found"})
                                        else:
                                            yield format_sse("status", {"status": "No associated vector_store found"})
                                            matched_books = []
                                    else:
                                        yield format_sse("status", {"status": "Assistant not configured with file_search tool"})
                                        matched_books = []

                                # 记录函数调用结果
                                function_results[-1]["result"] = matched_books

                                # 返回匹配的图书给对话助手
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": json.dumps({
                                        "status": "success",
                                        "matched_books": matched_books
                                    })
                                })

                            elif function_name == "get_book_content":
                                yield format_sse("progress", {
                                    "status": "Retrieving book content...",
                                    "progress": {
                                        "type": "book_content",
                                        "icon": "📖"
                                    }
                                })

                                # 处理获取图书内容函数调用
                                book_id = function_args.get("book_id", "")

                                # 调用data_source获取图书内容
                                from libs import openai_assistant as oa
                                book_data = oa.get_book_content(book_id)

                                # 记录函数调用结果
                                if book_data:
                                    yield format_sse("status", {"status": f"Successfully retrieved content for '{book_data['book_title']}'"})
                                    function_results[-1]["result"] = {
                                        "book_id": book_data["book_id"],
                                        "book_title": book_data["book_title"],
                                        "status": "success"
                                    }
                                else:
                                    yield format_sse("status", {"status": f"Book with ID {book_id} not found"})
                                    function_results[-1]["result"] = {
                                        "book_id": book_id,
                                        "status": "not_found"
                                    }

                                # 返回图书内容给对话助手
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": json.dumps({
                                        "status": "success" if book_data else "not_found",
                                        "book": book_data
                                    })
                                })

                        # 提交函数执行结果给 OpenAI
                        client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread_id,
                            run_id=run.id,
                            tool_outputs=tool_outputs
                        )

                elif run_status.status in ['failed', 'cancelled', 'expired']:
                    yield format_sse("error", {"error": f"Assistant run failed: {run_status.status}"})
                    return

                # 短暂等待后再检查状态
                time.sleep(0.5)

            # 获取最新的助手回复
            messages = client.beta.threads.messages.list(thread_id=thread_id)

            # 获取最新的助手回复（第一条消息是最新的）
            assistant_message = None
            for msg in messages.data:
                if msg.role == "assistant":
                    assistant_message = msg
                    break

            if not assistant_message:
                yield format_sse("error", {"error": "No response received from assistant"})
                return

            # 提取文本内容
            ai_response = ""
            for content in assistant_message.content:
                if content.type == "text":
                    if content.text.annotations:
                        print(content.text.annotations)
                    # 使用 openai_assistant 模块中的 clean_text 函数清理文本
                    ai_response += openai_assistant.clean_text(content.text.value)

            # 生成语音
            yield format_sse("status", {"status": "Generating voice response..."})
            audio_data = openai_service.text_to_speech(ai_response)

            # 创建临时文件保存音频
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(audio_data)
                audio_path = temp_file.name

            # 构建响应
            response = {
                "text": ai_response,
                "audio_url": f"/api/audio/{os.path.basename(audio_path)}",
                "function_results": function_results
            }

            # 保存文件路径以便后续请求
            current_app.config[f"TEMP_AUDIO_{os.path.basename(audio_path)}"] = audio_path

            # 发送完成事件
            yield format_sse("complete", response)

        except Exception as e:
            yield format_sse("error", {"error": str(e)})

    return Response(stream_with_context(generate()), content_type="text/event-stream")


def assistant_chat():
    """处理基于 Assistant API 的常规聊天请求"""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "Message content missing"}), 400

        user_message = data['message']

        # 获取用户语言（如果传入）
        lang = data.get('language', 'en')

        # 内容审核
        is_flagged, categories = openai_service.moderate_content(user_message)
        print(f"是否被标记: {is_flagged}, 类别: {categories}")

        # 检查内容是否被标记为不适当
        if is_flagged:
            # 动态生成友好的警告信息
            context = []  # 非流式模式下暂不使用对话上下文
            warning_message = openai_service.generate_friendly_warning(categories, lang, context)

            # 构建警告响应并直接返回
            return jsonify({
                "text": warning_message,
                "is_warning": True
            })

        # 内容审核通过，继续正常处理
        # 初始化或获取用户的线程ID
        thread_id = init_assistant_thread()

        client = openai.OpenAI()

        # 获取当前 Assistant ID
        assistant_id = os.getenv('OPENAI_ASSISTANT_ID', None)
        if not assistant_id:
            # 如果环境变量中没有设置，尝试从应用配置中获取
            assistant_id = current_app.config.get('OPENAI_ASSISTANT_ID')
            if not assistant_id:
                return jsonify({"error": "Assistant ID not configured"}), 500

        # 向线程添加用户消息
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        # 运行助手
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )

        # 初始化函数调用结果
        function_results = []

        # 等待运行完成
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            print(f"Assistant 运行状态: {run_status.status}")

            if run_status.status == 'completed':
                break
            elif run_status.status == 'requires_action':
                print("Assistant 需要执行函数")
                # 处理函数调用请求
                if run_status.required_action.type == "submit_tool_outputs":
                    tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = []

                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        print(f"函数名称: {function_name}")
                        print(f"函数参数: {function_args}")

                        # 记录函数调用
                        function_results.append({
                            "name": function_name,
                            "arguments": function_args
                        })

                        # 根据函数名称处理不同的函数调用
                        if function_name == "recommend_books":
                            # 处理图书推荐函数调用
                            user_interests = function_args.get("user_interests", "")
                            print(f"用户兴趣: {user_interests}")

                            # 获取书籍推荐助手 ID
                            book_recommandation_assistant_id = current_app.config.get('BOOK_RECOMMANDATION_ASSISTANT_ID')
                            if not book_recommandation_assistant_id:
                                print("未配置书籍推荐助手 ID，无法提供图书推荐")
                                recommended_books = []
                            else:
                                # 调用 search_books_by_interest 获取推荐书籍
                                print(f"调用书籍推荐助手 ID: {book_recommandation_assistant_id}")
                                from libs import openai_assistant as oa
                                recommended_books = oa.search_books_by_interest(
                                    book_recommandation_assistant_id,
                                    user_interests
                                )

                            # 记录函数调用结果
                            function_results[-1]["result"] = recommended_books

                            # 返回推荐书籍给对话助手
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": json.dumps({
                                    "status": "success",
                                    "recommended_books": recommended_books
                                })
                            })

                        elif function_name == "search_book_by_title":
                            # 处理根据书名搜索图书函数调用
                            title = function_args.get("title", "")
                            print(f"搜索书名: {title}")

                            # 获取书籍推荐助手 ID来获取关联的vector_store_id
                            book_recommandation_assistant_id = current_app.config.get('BOOK_RECOMMANDATION_ASSISTANT_ID')
                            if not book_recommandation_assistant_id:
                                print("未配置书籍推荐助手 ID，无法搜索图书")
                                matched_books = []
                            else:
                                # 获取助手详情以获取vector_store_id
                                from libs import openai_assistant as oa
                                client = openai.OpenAI()
                                assistant = client.beta.assistants.retrieve(book_recommandation_assistant_id)

                                if assistant.tool_resources and assistant.tool_resources.file_search:
                                    vector_store_ids = assistant.tool_resources.file_search.vector_store_ids
                                    if vector_store_ids:
                                        vector_store_id = vector_store_ids[0]
                                        print(f"使用vector_store_id: {vector_store_id}搜索书籍")
                                        matched_books = oa.search_book_by_title(vector_store_id, title)
                                    else:
                                        print("未找到关联的vector_store")
                                        matched_books = []
                                else:
                                    print("助手未配置file_search工具")
                                    matched_books = []

                            # 记录函数调用结果
                            function_results[-1]["result"] = matched_books

                            # 返回匹配的图书给对话助手
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": json.dumps({
                                    "status": "success",
                                    "matched_books": matched_books
                                })
                            })

                        elif function_name == "get_book_content":
                            # 处理获取图书内容函数调用
                            book_id = function_args.get("book_id", "")
                            print(f"获取图书内容，book_id: {book_id}")

                            # 调用data_source获取图书内容
                            from libs import openai_assistant as oa
                            book_data = oa.get_book_content(book_id)

                            # 记录函数调用结果
                            if book_data:
                                function_results[-1]["result"] = {
                                    "book_id": book_data["book_id"],
                                    "book_title": book_data["book_title"],
                                    "status": "success"
                                }
                            else:
                                function_results[-1]["result"] = {
                                    "book_id": book_id,
                                    "status": "not_found"
                                }

                            # 返回图书内容给对话助手
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": json.dumps({
                                    "status": "success" if book_data else "not_found",
                                    "book": book_data
                                })
                            })

                    # 提交函数执行结果给 OpenAI
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                return jsonify({"error": f"Assistant run failed: {run_status.status}"}), 500

            # 短暂等待后再检查状态
            time.sleep(0.5)

        # 获取最新的助手回复
        messages = client.beta.threads.messages.list(thread_id=thread_id)

        # 获取最新的助手回复（第一条消息是最新的）
        assistant_message = None
        for msg in messages.data:
            if msg.role == "assistant":
                assistant_message = msg
                break

        if not assistant_message:
            return jsonify({"error": "No response received from assistant"}), 500

        # 提取文本内容
        ai_response = ""
        for content in assistant_message.content:
            if content.type == "text":
                if content.text.annotations:
                    print(content.text.annotations)
                print('-------')
                print(assistant_message)
                # 使用 openai_assistant 模块中的 clean_text 函数清理文本
                ai_response += openai_assistant.clean_text(content.text.value)

        # 生成语音
        audio_data = openai_service.text_to_speech(ai_response)

        # 创建临时文件保存音频
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_data)
            audio_path = temp_file.name

        # 构建响应
        response = {
            "text": ai_response,
            "audio_url": f"/api/audio/{os.path.basename(audio_path)}",
            "function_results": function_results  # 添加函数调用结果
        }

        # 保存文件路径以便后续请求
        current_app.config[f"TEMP_AUDIO_{os.path.basename(audio_path)}"] = audio_path

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
