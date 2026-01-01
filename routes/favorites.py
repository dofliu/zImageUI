"""
Favorites Routes - 提示詞收藏相關路由
"""
from flask import Blueprint, request, jsonify
from services.favorites_service import get_favorites_service


favorites_bp = Blueprint('favorites', __name__)


@favorites_bp.route('/favorites', methods=['GET'])
def get_favorites():
    """獲取所有收藏"""
    try:
        favorites_service = get_favorites_service()
        favorites = favorites_service.load_favorites()
        return jsonify({
            'success': True,
            'favorites': favorites,
            'count': len(favorites)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@favorites_bp.route('/favorites', methods=['POST'])
def add_favorite():
    """新增收藏"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        name = data.get('name', '').strip()
        
        if not prompt:
            return jsonify({'error': '請提供提示詞'}), 400
        
        favorites_service = get_favorites_service()
        result = favorites_service.add_favorite(prompt, name if name else None)
        
        if result:
            return jsonify({
                'success': True,
                'favorite': result,
                'message': '已加入收藏'
            })
        else:
            return jsonify({
                'success': False,
                'error': '此提示詞已在收藏中'
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@favorites_bp.route('/favorites/<favorite_id>', methods=['DELETE'])
def remove_favorite(favorite_id):
    """移除收藏"""
    try:
        favorites_service = get_favorites_service()
        favorites_service.remove_favorite(favorite_id)
        return jsonify({
            'success': True,
            'message': '已從收藏移除'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@favorites_bp.route('/favorites/<favorite_id>/use', methods=['POST'])
def use_favorite(favorite_id):
    """使用收藏（增加計數）"""
    try:
        favorites_service = get_favorites_service()
        favorites_service.increment_use_count(favorite_id)
        return jsonify({
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
