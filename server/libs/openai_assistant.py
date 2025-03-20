import openai
import time
import os
import sys
import json
import re
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置 OpenAI API 密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

# 从 prompt_templates.py 合并的内容
USER_NAME = "Jixian"
OPENAI_ASSISTANT_INSTRUCTION = f"""
你是一个私人学习助手，你可以帮助用户完成以下任务:

用户的名字是：{USER_NAME}
你可以在一开始的对话中问候用户的名字，让用户感到亲切。

可以通过用户上传的语音文件和参考文本帮助用户纠正用户的英语发音。

你还可以讨论特定图书的详细内容。当用户表达想讨论某本书时，你可以通过搜索书名或者使用 book_id 来获取这本书的完整内容。
一旦开始讨论某本书，请记住这本书的内容，并能回答用户关于这本书情节、人物、主题等具体问题，
直到用户明确表示想讨论另一本书或结束当前话题。

整个对话中，AI的回复语言必须和用户保持一致，如果用户说英语，AI也要说英语。
"""

OPENAI_BOOK_RECOMMENDER_ASSISTANT_INSTRUCTION = f"""
你是一个阅读助手，你可以根据用户的喜好帮助用户从 Library Vector Store 中推荐图书。

Library Vector Store中包含了大量的图书数据，你可以根据用户的阅读偏好为用户推荐图书。
Library Vector Store中的数据格式是，每一行的JSON字符串代表一本Pickatale的图书，例如
{{"book_id": "14082-1", "book_title": "The Discovery of America LOW", "book_Description": "Christopher Columbus was a brave sailor from Italy. He wanted to find a new way to Asia and ended up discovering a new world! Follow Columbus on his exciting journey as he meets the kind Ta\\u00edno people, brings treasures back to Spain, and changes history forever. You will love this book if you enjoy stories about explorers and adventures!"}}
book_id是图书的唯一标识符，book_title是图书的标题，book_Description是图书的描述。

通过对话了解用户的阅读偏好。例如，询问用户最喜欢的书籍类型，以及他们最近读过的书籍。
可以从关联的vector_store中为用户推荐他可能感兴趣的1-3本书。

整个对话中，AI的回复语言必须和用户保持一致，如果用户说英语，AI也要说英语。
"""

OPENAI_USER_RECOOMMANDATION_PROMPT = """
用户的阅读兴趣和喜好如下：
{reading_interests}

请基于以上用户喜好，从Library Vector Store中找出3本最适合的书籍推荐给用户。
"""

OPENAI_ANALYSIS_FUNCTION_DESCRIPTION = """
如果调用了file_search功能，用于搜索并推荐书给用户就必须要通过这个函数来格式化输出。
"""

OPENAI_ANALYSIS_FUNCTION_RESULT_DESCRIPTION = """
总结本次推荐的主要原因和理由，以及分析过程
"""


# 初始化 OpenAI 客户端
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def clean_text(text: str) -> str:
    """
    过滤掉 file_search 结果中的【x:y†source】格式的引用信息
    """
    return re.sub(r"【\d+:\d+†source】", "", text).strip()

def create_vector_store_with_file(library_data_path: str) -> str:
    """
    1. 创建一个新的 vector store
    2. 上传本地书籍数据库文件
    3. 关联文件到 vector store
    4. 返回 vector store ID
    """
    # 创建 vector store
    vector_store = client.vector_stores.create(name="Library Vector Store")
    vector_store_id = vector_store.id
    print(f"📁 Created vector store with ID: {vector_store_id}")

    # 上传文件并关联到 vector store
    with open(library_data_path, "rb") as file:
        uploaded_file = client.files.create(file=file, purpose="assistants")
        file_id = uploaded_file.id
        print(f"📄 Uploaded file with ID: {file_id}")

    # 关联文件到 vector store
    client.vector_stores.files.create(vector_store_id=vector_store_id, file_id=file_id)
    print(f"✅ Linked file to vector store {vector_store_id}")

    return vector_store_id


def ensure_assistant() -> str:
    """
    确保存在一个基础的学习助手，若无则创建，并返回 assistant_id
    """
    assistant = client.beta.assistants.create(
        name="Learning Assistant",
        instructions=OPENAI_ASSISTANT_INSTRUCTION,
        model=OPENAI_MODEL,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "recommend_books",
                    "description": "根据用户的阅读喜好帮助用户推荐图书，如果用户有多个不同的喜好这个方法只调用一次，将多个喜好总结为一个短语。例如： 用户可能喜欢冒险类的数据也会对艺术有一点点兴趣。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_interests": {
                                "type": "string",
                                "description": "通过上对话的下文分析用户可能会感兴趣的图书类型，用一个短语来概括总结用户的阅读兴趣。"
                            }
                        },
                        "required": ["user_interests"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_book_by_title",
                    "description": "根据书名搜索对应的图书ID。当用户提到想讨论某本书，但只提供了书名时，使用此功能查找匹配的图书。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "用户提到的书名"
                            }
                        },
                        "required": ["title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_book_content",
                    "description": "获取指定book_id的图书完整内容。当确定用户想讨论某本特定图书时使用此功能。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "book_id": {
                                "type": "string",
                                "description": "图书的唯一标识符"
                            }
                        },
                        "required": ["book_id"]
                    }
                }
            }
        ]
    )

    print(f"✅ Assistant created with ID: {assistant.id}")
    return assistant.id


def ensure_assistant_for_recommand_books(library_data_path: str) -> str:
    """
    确保存在一个用于图书推荐的 Assistant，若无则创建，并返回 assistant_id
    同时上传本地参考文件到 Vector Store 并启用文件搜索工具。
    """
    vector_store_id = create_vector_store_with_file(library_data_path)

    assistant = client.beta.assistants.create(
        name="Book Recommendation Assistant",
        instructions=OPENAI_BOOK_RECOMMENDER_ASSISTANT_INSTRUCTION,
        model=OPENAI_MODEL,
        tools=[
            {"type": "file_search"},  # 启用文件搜索工具
            {
                "type": "function",
                "function": {
                    "name": "recommend_books_from_vector_store",
                    "description": OPENAI_ANALYSIS_FUNCTION_DESCRIPTION,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recommended_books": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "book_id": {"type": "string", "description": "book_id in the Library Vector Store"},
                                        "book_title": {"type": "string", "description": "book_title in the Library Vector Store"},
                                        "reason": {"type": "string", "description": "Reason for recommendation"}
                                    }
                                },
                                "description": "推荐的书籍，包括书籍的 book_id, book_title, 和推荐理由"
                            }
                        },
                        "required": ["recommended_books"]
                    }
                }
            }
        ],
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}  # 关联 vector store
    )

    print(f"✅ Book Recommander Assistant created with ID: {assistant.id}")
    return assistant.id

def search_book_by_title(vector_store_id: str, title: str) -> list:
    """
    根据书名在vector store中搜索匹配的图书

    参数:
        vector_store_id: 图书数据vector store的ID
        title: 要搜索的书名

    返回:
        匹配的图书列表，每本书包含book_id, book_title, book_Description
    """
    try:
        # 创建新的对话线程
        thread = client.beta.threads.create()
        print(f"📌 Thread created with ID: {thread.id} for book title search")

        # 添加用户搜索请求到线程
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"找到书名包含'{title}'的所有图书，返回它们的book_id, book_title和book_Description"
        )

        # 创建临时助手进行搜索
        temp_assistant = client.beta.assistants.create(
            name="Book Search Assistant",
            instructions="你是一个图书搜索助手，帮助用户在Library Vector Store中查找匹配书名的图书。",
            model=OPENAI_MODEL,
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}  # 关联vector store
        )

        # 运行助手
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=temp_assistant.id
        )

        matched_books = []

        # 等待运行完成并处理结果
        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            print(f"🔄 Book search status: {run_status.status}")

            if run_status.status == "completed":
                # 获取助手的回复
                messages = client.beta.threads.messages.list(thread_id=thread.id)

                # 解析回复中的图书信息
                for msg in messages.data:
                    if msg.role == "assistant":
                        for content in msg.content:
                            if content.type == "text":
                                text = clean_text(content.text.value)
                                print(f"💬 Book search response: {text}")

                                # 尝试从文本中提取JSON格式的图书信息
                                try:
                                    # 使用正则表达式找出所有JSON格式的书籍数据
                                    import re
                                    json_matches = re.findall(r'({[\s\S]*?book_id[\s\S]*?})', text)

                                    if json_matches:
                                        for json_str in json_matches:
                                            try:
                                                book = json.loads(json_str)
                                                if "book_id" in book and "book_title" in book:
                                                    matched_books.append(book)
                                            except:
                                                continue
                                    else:
                                        # 如果没有找到JSON格式，尝试从文本提取信息
                                        book_blocks = re.split(r'\n\s*\n', text)
                                        for block in book_blocks:
                                            book_info = {}

                                            id_match = re.search(r'book_id[\s:]*([^,\s\n]+)', block)
                                            if id_match:
                                                book_info["book_id"] = id_match.group(1).strip('"\'')

                                            title_match = re.search(r'book_title[\s:]*([^\n]+)', block)
                                            if title_match:
                                                book_info["book_title"] = title_match.group(1).strip('"\'')

                                            desc_match = re.search(r'book_Description[\s:]*([^\n]+(?:\n[^\n]+)*)', block)
                                            if desc_match:
                                                book_info["book_Description"] = desc_match.group(1).strip('"\'')

                                            if "book_id" in book_info and "book_title" in book_info:
                                                matched_books.append(book_info)

                                except Exception as e:
                                    print(f"⚠️ Error parsing book info: {str(e)}")
                break

            elif run_status.status in ["failed", "cancelled", "expired"]:
                print(f"❌ Book search failed with status: {run_status.status}")
                break

            # 等待后再检查状态
            time.sleep(1)

        # 清理临时助手
        client.beta.assistants.delete(temp_assistant.id)

        return matched_books

    except Exception as e:
        print(f"❌ Error in search_book_by_title: {str(e)}")
        return []

def get_book_content(book_id: str) -> dict:
    """
    根据book_id获取图书完整内容

    参数:
        book_id: 图书的唯一标识符

    返回:
        包含图书详情和内容的字典，若未找到则返回None
    """
    try:
        # 从本地数据库获取图书内容
        import sys, os
        # 确保能导入data_source模块
        sys.path.append(os.path.dirname(__file__))
        from data_source import fetch_book_content

        # 调用fetch_book_content获取图书内容
        book_data = fetch_book_content(book_id)

        if book_data:
            print(f"📚 Found book: {book_data['book_title']} (ID: {book_data['book_id']})")
            return book_data
        else:
            print(f"⚠️ Book not found with ID: {book_id}")
            return None

    except Exception as e:
        print(f"❌ Error in get_book_content: {str(e)}")
        return None

def search_books_by_interest(book_recommendation_assistant_id: str, user_interests: str) -> list:
    """
    基于用户兴趣，使用书籍推荐 Assistant 搜索并推荐图书

    参数:
        book_recommendation_assistant_id: 书籍推荐 Assistant 的 ID
        user_interests: 用户的兴趣和阅读喜好

    返回:
        推荐书籍列表，每本书包含 book_id, book_title 和推荐理由
    """
    try:
        # 创建新的对话线程
        thread = client.beta.threads.create()
        print(f"📌 Thread created with ID: {thread.id}")

        # 格式化用户查询
        user_prompt = OPENAI_USER_RECOOMMANDATION_PROMPT.format(reading_interests=user_interests)

        # 添加用户消息到线程
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_prompt
        )

        # 运行助手
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=book_recommendation_assistant_id
        )

        recommended_books = []

        # 等待运行完成并处理结果
        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            print(f"🔄 Status: {run_status.status}")

            if run_status.status == "completed":
                # 获取助手的回复
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                for msg in messages.data:
                    if msg.role == "assistant":
                        for content in msg.content:
                            if content.type == "text":
                                print(f"💬 Assistant response: {content.text.value}")
                break

            elif run_status.status == "requires_action":
                # 处理工具调用
                tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []

                for tool_call in tool_calls:
                    if tool_call.function.name == "recommend_books_from_vector_store":
                        function_args = json.loads(tool_call.function.arguments)
                        recommended_books = function_args.get("recommended_books", [])

                        # 清理推荐理由中的引用信息
                        for book in recommended_books:
                            if "reason" in book:
                                book["reason"] = clean_text(book["reason"])
                            if "book_title" in book:
                                book["book_title"] = clean_text(book["book_title"])

                        # 返回处理结果
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps({"status": "success"})
                        })

                # 提交工具输出
                if tool_outputs:
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )

            elif run_status.status in ["failed", "cancelled", "expired"]:
                print(f"❌ Assistant run failed with status: {run_status.status}")
                if hasattr(run_status, "last_error"):
                    print(f"Error: {run_status.last_error}")
                return []

            # 等待后再检查状态
            time.sleep(2)

        return recommended_books

    except Exception as e:
        print(f"❌ Error in search_books_by_interest: {str(e)}")
        return []

def delete_assistant(assistant_id: str):
    """
    删除 Assistant，同时删除 file_search 关联的 vector store 及其文件
    """
    try:
        # 1️⃣ 获取 Assistant 详细信息
        assistant = client.beta.assistants.retrieve(assistant_id)

        # 2️⃣ 获取 `file_search` 关联的 `vector_store` ID（使用正确的访问方式）
        if assistant.tool_resources.file_search:
            vector_store_ids = assistant.tool_resources.file_search.vector_store_ids if hasattr(assistant.tool_resources, 'file_search') else []
            print(f"📌 Found {len(vector_store_ids)} vector store(s) linked to Assistant {assistant_id}: {vector_store_ids}")

        # 3️⃣ 删除 Assistant
        client.beta.assistants.delete(assistant_id)
        print(f"🗑️ Assistant {assistant_id} deleted.")

        if assistant.tool_resources.file_search:
            # 4️⃣ 删除 `vector_store` 及其关联的文件
            for vector_store_id in vector_store_ids:
                try:
                    # 获取 vector store 关联的文件
                    vector_store_files = client.vector_stores.files.list(vector_store_id=vector_store_id)

                    # 删除所有文件
                    for file in vector_store_files.data:
                        client.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=file.id)
                        print(f"🗑️ Deleted file {file.id} from vector store {vector_store_id}")

                    # 删除 vector store
                    client.vector_stores.delete(vector_store_id)
                    print(f"🗑️ Deleted vector store {vector_store_id}")

                except Exception as e:
                    print(f"⚠️ Failed to delete vector store {vector_store_id}: {e}")

    except Exception as e:
        print(f"❌ Error deleting assistant {assistant_id}: {e}")


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

            response = client.audio.transcriptions.create(
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
            response = client.chat.completions.create(
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
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            return response.content
        except Exception as e:
            print(f"文字转语音错误: {str(e)}")
            raise
