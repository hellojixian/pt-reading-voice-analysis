"""
主应用入口文件
初始化和配置Flask应用
"""
import os
from flask import Flask

# 配置
import config

# 中间件
from middleware.cors_middleware import setup_cors

# 路由
from routes.api_routes import register_routes

# 服务
from services.assistant_service import AssistantService
from services.data_service import DataService
from utils.file_utils import cleanup_temp_files

def create_app():
    """
    创建并配置Flask应用

    返回:
        Flask应用实例
    """
    # 初始化Flask应用
    app = Flask(__name__)

    # 配置CORS
    setup_cors(app)

    # 注册路由
    register_routes(app)

    # 初始化应用配置
    app.config['OPENAI_ASSISTANT_ID'] = None
    app.config['BOOK_RECOMMANDATION_ASSISTANT_ID'] = None

    return app

def init_assistants(app):
    """
    初始化OpenAI Assistant

    参数:
        app: Flask应用实例

    返回:
        tuple: (assistant_id, book_recommendation_assistant_id)
    """
    assistant_id = None
    book_recommendation_assistant_id = None

    try:
        # 初始化数据服务
        data_service = DataService()
        # 获取书籍数据
        library_data_file = data_service.fetch_all_production_books()
        print(f"Library data file created at: {library_data_file}")

        # 初始化Assistant服务
        assistant_service = AssistantService()

        # 创建Assistant
        assistant_id = assistant_service.ensure_assistant()
        book_recommendation_assistant_id = assistant_service.ensure_book_recommendation_assistant(library_data_file)

        # 保存Assistant ID到应用配置
        app.config['OPENAI_ASSISTANT_ID'] = assistant_id
        app.config['BOOK_RECOMMANDATION_ASSISTANT_ID'] = book_recommendation_assistant_id

        print(f"Assistant ID {assistant_id} saved to app config")
        print(f"Book Recommendation Assistant ID {book_recommendation_assistant_id} saved to app config")

        return assistant_id, book_recommendation_assistant_id

    except Exception as e:
        print(f"初始化Assistant错误: {str(e)}")
        return None, None

def cleanup(app, assistant_id=None, book_recommendation_assistant_id=None):
    """
    清理资源，包括临时文件和Assistant

    参数:
        app: Flask应用实例
        assistant_id: 要删除的Assistant ID
        book_recommendation_assistant_id: 要删除的图书推荐Assistant ID
    """
    print("\n🧹 正在清理...")

    # 清理临时文件
    cleanup_temp_files(app)

    # 删除Assistant
    if assistant_id:
        AssistantService.delete_assistant(assistant_id)

    if book_recommendation_assistant_id:
        AssistantService.delete_assistant(book_recommendation_assistant_id)

# 应用入口点
if __name__ == '__main__':
    # 创建Flask应用
    app = create_app()

    # 初始化Assistant
    assistant_id, book_recommendation_assistant_id = init_assistants(app)

    try:
        # 运行应用
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG
        )
    finally:
        # 清理资源
        cleanup(app, assistant_id, book_recommendation_assistant_id)
