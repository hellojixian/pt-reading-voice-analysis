"""
健康检查控制器
"""
from flask import jsonify

def health_check():
    """健康检查端点"""
    return jsonify({"status": "healthy", "version": "1.0.0"})
