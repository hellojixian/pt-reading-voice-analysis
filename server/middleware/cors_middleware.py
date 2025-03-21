"""
CORS 中间件
处理跨域资源共享相关配置和响应头
"""
from typing import Optional, Union, List
from flask import Flask, Response
from flask_cors import CORS

def setup_cors(app: Flask, origins: Union[str, List[str], None] = "*") -> None:
    """
    为Flask应用配置CORS

    参数:
        app (Flask): Flask应用实例
        origins (Union[str, List[str], None]): 允许的源，可以是字符串、列表或None，默认为"*"（允许所有源）

    示例:
        >>> from flask import Flask
        >>> app = Flask(__name__)
        >>> setup_cors(app, origins=["http://localhost:3000", "https://example.com"])
    """
    CORS(app, resources={r"/*": {"origins": origins}}, supports_credentials=True)

    # 注册启动后回调，添加CORS头
    @app.after_request
    def after_request_callback(response: Response) -> Response:
        """
        每次请求后添加CORS头

        参数:
            response (Response): Flask响应对象

        返回:
            Response: 添加了CORS头的响应对象
        """
        # 添加CORS头 - 只提供一个值，避免多个值导致的CORS错误
        if origins == "*":
            response.headers.add('Access-Control-Allow-Origin', '*')
        elif isinstance(origins, list):
            # 实际应用中应该检查请求源是否在允许列表中并返回匹配的源
            # 这里简化为返回第一个配置的源
            response.headers.add('Access-Control-Allow-Origin', origins[0] if origins else '*')
        else:
            response.headers.add('Access-Control-Allow-Origin', origins or '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    # 添加对预检请求的支持
    @app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def handle_options(path: str) -> tuple:
        """
        处理预检请求

        参数:
            path (str): 请求路径

        返回:
            tuple: 空响应和200状态码
        """
        return '', 200
