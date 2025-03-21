"""
API路由注册模块
注册所有API蓝图到主API路由
"""
from flask import Flask

from routes import api
from api.health_api import health_api
from api.speech_api import speech_api
from api.assistant_api import assistant_api
from api.chat_api import chat_api

def register_routes(app: Flask):
    """
    注册所有API路由到Flask应用

    参数:
        app: Flask应用实例

    示例:
        >>> app = Flask(__name__)
        >>> register_routes(app)
    """
    # 注册各API蓝图到主API蓝图
    api.register_blueprint(health_api)
    api.register_blueprint(speech_api)
    api.register_blueprint(assistant_api)
    api.register_blueprint(chat_api)

    # 注册主API蓝图到Flask应用
    app.register_blueprint(api)
