import openai
import time
import os
import sys
import json
import re
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

sys.path.append(os.path.dirname(__file__))
import prompt_templates as pt

# 设置 OpenAI API 密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")


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


def ensure_assistant(library_data_path: str) -> str:
    """
    确保存在一个 Assistant，若无则创建，并返回 assistant_id，
    同时上传本地参考文件到 Vector Store 并启用文件搜索工具。
    """
    vector_store_id = create_vector_store_with_file(library_data_path)

    assistant = client.beta.assistants.create(
        name="Learning Assistant",
        instructions=pt.OPENAI_ASSISTANT_INSTRUCTION,
        model=OPENAI_MODEL,
        tools=[
            {"type": "file_search"},  # 启用文件搜索工具
            {
                "type": "function",
                "function": {
                    "name": "recommend_books",
                    "description": pt.OPENAI_ANALYSIS_FUNCTION_DESCRIPTION,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recommendation_summary": {
                                "type": "string",
                                "description": pt.OPENAI_ANALYSIS_FUNCTION_RESULT_DESCRIPTION
                            },
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
                        "required": ["recommendation_summary", "recommended_books"]
                    }
                }
            }
        ],
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}  # 关联 vector store
    )

    print(f"✅ Assistant created with ID: {assistant.id}")
    return assistant.id




def delete_assistant(assistant_id: str):
    """
    删除 Assistant，同时删除 file_search 关联的 vector store 及其文件
    """
    try:
        # 1️⃣ 获取 Assistant 详细信息
        assistant = client.beta.assistants.retrieve(assistant_id)

        # 2️⃣ 获取 `file_search` 关联的 `vector_store` ID（使用正确的访问方式）
        vector_store_ids = assistant.tool_resources.file_search.vector_store_ids if assistant.tool_resources.file_search else []

        print(f"📌 Found {len(vector_store_ids)} vector store(s) linked to Assistant {assistant_id}: {vector_store_ids}")

        # 3️⃣ 删除 Assistant
        client.beta.assistants.delete(assistant_id)
        print(f"🗑️ Assistant {assistant_id} deleted.")

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
