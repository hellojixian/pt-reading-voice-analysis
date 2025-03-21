"""
路由模块初始化文件
管理应用的路由注册和组织
"""
from flask import Blueprint

# 创建主API蓝图
api = Blueprint('api', __name__)

# 支持预检请求的装饰器
def cors_preflight(blueprint):
    """
    为蓝图添加对预检请求的支持

    参数:
        blueprint: Flask蓝图对象
    """
    @blueprint.route('/', defaults={'path': ''}, methods=['OPTIONS'])
    @blueprint.route('/<path:path>', methods=['OPTIONS'])
    def handle_options(path):
        """处理预检请求"""
        return '', 200

    return blueprint

# 添加CORS预检支持
cors_preflight(api)
