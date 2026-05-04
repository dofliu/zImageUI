"""
Settings Routes - API Key 與 Provider 設定路由
"""
from flask import Blueprint, request, jsonify
from services.provider_settings_service import get_provider_settings
from services.model_registry import get_model_registry

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/settings/providers', methods=['GET'])
def get_provider_settings_route():
    """取得所有 Provider 設定（遮蔽 Key）"""
    settings = get_provider_settings()
    return jsonify({'success': True, 'providers': settings.get_all()})


@settings_bp.route('/settings/providers/<provider_id>/key', methods=['POST'])
def set_api_key(provider_id: str):
    """儲存 API Key"""
    data = request.get_json()
    api_key = data.get('api_key', '').strip()

    if not api_key:
        return jsonify({'success': False, 'error': '請輸入 API Key'}), 400

    settings = get_provider_settings()
    result = settings.set_api_key(provider_id, api_key)

    if result['success']:
        # 重新同步到 registry
        get_model_registry().reload_api_keys()

    return jsonify(result)


@settings_bp.route('/settings/providers/<provider_id>/key', methods=['DELETE'])
def clear_api_key(provider_id: str):
    """清除 API Key"""
    settings = get_provider_settings()
    result = settings.clear_api_key(provider_id)
    if result['success']:
        get_model_registry().reload_api_keys()
    return jsonify(result)


@settings_bp.route('/settings/providers/<provider_id>/model', methods=['POST'])
def set_provider_model(provider_id: str):
    """切換 Provider 使用的模型"""
    data = request.get_json()
    model_id = data.get('model_id', '').strip()
    if not model_id:
        return jsonify({'success': False, 'error': '請指定 model_id'}), 400

    settings = get_provider_settings()
    result = settings.set_active_model(provider_id, model_id)
    return jsonify(result)
