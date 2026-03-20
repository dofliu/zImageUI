"""
Models Routes - 多模型管理路由
"""
from flask import Blueprint, request, jsonify
from services.model_registry import get_model_registry

models_bp = Blueprint('models', __name__)


@models_bp.route('/models', methods=['GET'])
def list_models():
    """列出所有可用模型"""
    registry = get_model_registry()
    models = registry.list_models()
    active = registry.get_active_model()
    return jsonify({
        'success': True,
        'models': models,
        'active_model': active['id'] if active else None
    })


@models_bp.route('/models/active', methods=['GET'])
def get_active_model():
    """取得目前啟用的模型"""
    registry = get_model_registry()
    active = registry.get_active_model()
    if active:
        return jsonify({'success': True, 'model': active})
    return jsonify({'success': True, 'model': None, 'message': '尚未載入任何模型'})


@models_bp.route('/models/switch', methods=['POST'])
def switch_model():
    """切換模型"""
    data = request.get_json()
    model_id = data.get('model_id')
    if not model_id:
        return jsonify({'error': '請指定模型 ID'}), 400

    registry = get_model_registry()
    result = registry.switch_model(model_id)

    if result['success']:
        return jsonify(result)
    return jsonify(result), 400


@models_bp.route('/models/<model_id>', methods=['GET'])
def get_model_info(model_id):
    """取得特定模型資訊"""
    registry = get_model_registry()
    info = registry.get_model_info(model_id)
    if info:
        return jsonify({'success': True, 'model': info})
    return jsonify({'error': '模型不存在'}), 404


@models_bp.route('/models/register', methods=['POST'])
def register_custom_model():
    """註冊自訂模型"""
    data = request.get_json()
    registry = get_model_registry()
    result = registry.register_custom_model(data)

    if result['success']:
        return jsonify(result)
    return jsonify(result), 400


@models_bp.route('/models/<model_id>', methods=['DELETE'])
def remove_model(model_id):
    """移除自訂模型"""
    registry = get_model_registry()
    result = registry.remove_custom_model(model_id)

    if result['success']:
        return jsonify(result)
    return jsonify(result), 400
