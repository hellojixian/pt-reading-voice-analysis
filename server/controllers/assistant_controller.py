"""
OpenAI Assistant 控制器
处理基于 OpenAI Assistant API 的聊天功能
"""
import os
import tempfile
import time
import json
from flask import jsonify, request, current_app

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

def assistant_chat():
    """处理基于 Assistant API 的聊天请求"""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "缺少消息内容"}), 400

        user_message = data['message']

        # 初始化或获取用户的线程ID
        thread_id = init_assistant_thread()

        client = openai.OpenAI()

        # 获取当前 Assistant ID
        assistant_id = os.getenv('OPENAI_ASSISTANT_ID', None)
        if not assistant_id:
            # 如果环境变量中没有设置，尝试从应用配置中获取
            assistant_id = current_app.config.get('OPENAI_ASSISTANT_ID')
            if not assistant_id:
                return jsonify({"error": "未配置 Assistant ID"}), 500

        # 向线程添加用户消息
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        # 运行助手
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
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

                        # 如果是推荐图书函数，直接返回参数
                        if function_name == "recommend_books":
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": json.dumps(function_args)
                            })

                    # 提交函数执行结果给 OpenAI
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                return jsonify({"error": f"Assistant 运行失败: {run_status.status}"}), 500

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
            return jsonify({"error": "未收到助手回复"}), 500

        # 提取文本内容
        ai_response = ""
        for content in assistant_message.content:
            if content.type == "text":
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
