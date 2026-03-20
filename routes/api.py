"""
External API Routes - 對外 API 端點
提供帶認證的 RESTful API，讓外部應用程式可以整合圖片生成功能
"""
import os
import base64
from io import BytesIO
from datetime import datetime
from flask import Blueprint, request, jsonify
import config
from services.api_key_service import get_api_key_service, require_api_key
from services.history_service import get_history_service

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


# ===== API 金鑰管理 =====

@api_bp.route('/keys', methods=['GET'])
def list_api_keys():
    """列出所有 API 金鑰"""
    service = get_api_key_service()
    keys = service.list_keys()
    return jsonify({'success': True, 'keys': keys})


@api_bp.route('/keys', methods=['POST'])
def create_api_key():
    """建立新的 API 金鑰"""
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': '請輸入金鑰名稱'}), 400

    permissions = data.get('permissions')
    service = get_api_key_service()
    result = service.create_key(name, permissions)
    return jsonify(result)


@api_bp.route('/keys/<key_id>', methods=['DELETE'])
def delete_api_key(key_id):
    """刪除 API 金鑰"""
    service = get_api_key_service()
    result = service.delete_key(key_id)
    if result['success']:
        return jsonify(result)
    return jsonify(result), 404


@api_bp.route('/keys/<key_id>/revoke', methods=['POST'])
def revoke_api_key(key_id):
    """撤銷 API 金鑰"""
    service = get_api_key_service()
    result = service.revoke_key(key_id)
    if result['success']:
        return jsonify(result)
    return jsonify(result), 404


# ===== 對外 API 端點 (需要 API Key) =====

@api_bp.route('/generate', methods=['POST'])
@require_api_key('generate')
def api_generate():
    """外部 API: 生成圖片

    Headers:
        X-API-Key: your-api-key

    Body:
        {
            "prompt": "a cat sitting on a window",
            "negative_prompt": "blurry, bad quality",
            "width": 768,
            "height": 768,
            "seed": 12345,
            "model": "z-image-turbo",
            "output_format": "base64"  // base64 | url
        }
    """
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        if not prompt:
            return jsonify({'error': '請提供 prompt 參數'}), 400

        negative_prompt = data.get('negative_prompt', '')
        width = data.get('width', config.IMAGE_WIDTH)
        height = data.get('height', config.IMAGE_HEIGHT)
        seed = data.get('seed')
        output_format = data.get('output_format', 'base64')

        # 可選：切換模型
        model_id = data.get('model')
        if model_id:
            from services.model_registry import get_model_registry
            registry = get_model_registry()
            switch_result = registry.switch_model(model_id)
            if not switch_result['success']:
                return jsonify({'error': switch_result['error']}), 400

        from services.model_registry import get_model_registry
        registry = get_model_registry()

        if registry.active_pipeline is None:
            return jsonify({'error': '尚未載入模型'}), 503

        image, used_seed = registry.generate(
            prompt, width, height, seed,
            negative_prompt=negative_prompt if negative_prompt else None
        )

        # 儲存圖片
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"api_{timestamp}.png"
        save_path = os.path.join(config.OUTPUT_PATH, filename)
        image.save(save_path)

        history_service = get_history_service()
        history_service.add_to_history(f"[API] {prompt}", filename, tags=["api"])

        result = {
            'success': True,
            'filename': filename,
            'prompt': prompt,
            'seed': used_seed,
            'width': width,
            'height': height,
            'model': registry.active_model_id
        }

        if output_format == 'base64':
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            result['image'] = f"data:image/png;base64,{img_str}"
        else:
            result['image_url'] = f"/images/{filename}"

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/history', methods=['GET'])
@require_api_key('history')
def api_history():
    """外部 API: 取得歷史記錄"""
    history_service = get_history_service()
    history = history_service.load_history()
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    return jsonify({
        'success': True,
        'total': len(history),
        'history': history[offset:offset + limit]
    })


@api_bp.route('/models', methods=['GET'])
@require_api_key('generate')
def api_list_models():
    """外部 API: 列出可用模型"""
    from services.model_registry import get_model_registry
    registry = get_model_registry()
    return jsonify({
        'success': True,
        'models': registry.list_models(),
        'active_model': registry.active_model_id
    })
