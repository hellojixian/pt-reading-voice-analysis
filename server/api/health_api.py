"""
健康检查API
提供系统健康状态检查端点
"""
from flask import jsonify, Blueprint

# 创建蓝图
health_api = Blueprint('health_api', __name__)

@health_api.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查端点

    返回系统健康状态和版本信息

    返回:
        JSON响应，包含状态和版本信息

    示例:
        GET /api/health
        响应: {"status": "healthy", "version": "1.0.0"}
    """
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "message": "服务正常运行"
    })
