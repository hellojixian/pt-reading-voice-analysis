import os
from flask import Flask, request
from flask_cors import CORS

# 导入配置
import config
from controllers.audio_controller import cleanup_temp_files
from routes import api

# 初始化Flask应用
app = Flask(__name__)
# 正确配置CORS，允许所有源访问
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# 注册蓝图
app.register_blueprint(api)

# 配置 OpenAI Assistant ID 变量，将在 assistant_controller 中使用
app.config['OPENAI_ASSISTANT_ID'] = None

# 注册启动后回调，添加CORS头
@app.after_request
def after_request_callback(response):
    """每次请求后添加CORS头并检查临时文件"""
    # 添加CORS头
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    assistant_id = None
    import libs.data_source as ds, libs.openai_assistant as oa
    try:
        library_data_file = ds.fetch_all_production_books()
        print(f"Library data file created at: {library_data_file}")
        assistant_id = oa.ensure_assistant(library_data_file)

        # 将 assistant_id 保存到应用配置中，以便控制器使用
        app.config['OPENAI_ASSISTANT_ID'] = assistant_id
        print(f"Assistant ID {assistant_id} saved to app config")

        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
    finally:
        # 清理临时文件和删除 Assistant
        print("\n🧹 Cleaning up...")
        cleanup_temp_files(app)
        if assistant_id:
            oa.delete_assistant(assistant_id)
