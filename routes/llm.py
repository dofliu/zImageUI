"""
LLM Routes - 大語言模型 API 路由
"""
from flask import Blueprint, request, jsonify
from services.llm_service import get_llm_service

llm_bp = Blueprint('llm', __name__, url_prefix='/llm')


@llm_bp.route('/status', methods=['GET'])
def get_status():
    """取得 LLM 服務狀態"""
    llm_service = get_llm_service()
    
    return jsonify({
        'available': llm_service.is_available(),
        'model_loaded': llm_service.model is not None,
        'current_model': llm_service.current_model_path.split('\\')[-1] if llm_service.current_model_path else None
    })


@llm_bp.route('/models', methods=['GET'])
def get_models():
    """取得可用的 LLM 模型清單"""
    llm_service = get_llm_service()
    
    if not llm_service.is_available():
        return jsonify({
            'success': False,
            'error': 'llama-cpp-python 未安裝。請執行: pip install llama-cpp-python',
            'models': []
        })
    
    models = llm_service.get_available_models()
    return jsonify({
        'success': True,
        'models': models
    })


@llm_bp.route('/load', methods=['POST'])
def load_model():
    """載入指定的 LLM 模型"""
    llm_service = get_llm_service()
    
    data = request.get_json()
    model_id = data.get('model_id')
    
    if not model_id:
        return jsonify({
            'success': False,
            'error': '請指定 model_id'
        }), 400
    
    success = llm_service.load_model(model_id)
    
    return jsonify({
        'success': success,
        'message': '模型載入成功' if success else '模型載入失敗'
    })


@llm_bp.route('/unload', methods=['POST'])
def unload_model():
    """卸載當前 LLM 模型"""
    llm_service = get_llm_service()
    llm_service.unload_model()
    
    return jsonify({
        'success': True,
        'message': 'LLM 模型已卸載'
    })


@llm_bp.route('/generate-prompt', methods=['POST'])
def generate_prompt():
    """使用 LLM 擴展提示詞"""
    llm_service = get_llm_service()
    
    data = request.get_json()
    idea = data.get('idea', '')
    style = data.get('style', '通用')
    
    if not idea:
        return jsonify({
            'success': False,
            'error': '請輸入想法內容'
        }), 400
    
    if llm_service.model is None:
        return jsonify({
            'success': False,
            'error': '尚未載入 LLM 模型。請先選擇並載入一個模型。'
        }), 400
    
    result = llm_service.generate_prompt(idea, style)
    
    # 檢查是否為錯誤訊息
    if result.startswith('❌'):
        return jsonify({
            'success': False,
            'error': result
        }), 500
    
    return jsonify({
        'success': True,
        'prompt': result
    })


@llm_bp.route('/chat', methods=['POST'])
def chat():
    """通用聊天 API"""
    llm_service = get_llm_service()
    
    data = request.get_json()
    message = data.get('message', '')
    system_prompt = data.get('system_prompt')
    
    if not message:
        return jsonify({
            'success': False,
            'error': '請輸入訊息內容'
        }), 400
    
    if llm_service.model is None:
        return jsonify({
            'success': False,
            'error': '尚未載入 LLM 模型。請先選擇並載入一個模型。'
        }), 400
    
    result = llm_service.chat(message, system_prompt)
    
    # 檢查是否為錯誤訊息
    if result.startswith('❌'):
        return jsonify({
            'success': False,
            'error': result
        }), 500
    
    return jsonify({
        'success': True,
        'response': result
    })
