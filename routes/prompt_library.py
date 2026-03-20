"""
Prompt Library Routes - 提示詞庫 API
"""
from flask import Blueprint, request, jsonify
from services.prompt_library_service import get_prompt_library_service

prompt_library_bp = Blueprint('prompt_library', __name__)


@prompt_library_bp.route('/api/prompt-library', methods=['GET'])
def list_prompts():
    """列出提示詞庫"""
    service = get_prompt_library_service()
    category = request.args.get('category', 'all')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'rating')

    prompts = service.list_prompts(category=category, search=search, sort_by=sort_by)
    categories = service.get_categories()

    return jsonify({
        'success': True,
        'prompts': prompts,
        'categories': categories,
        'total': len(prompts)
    })


@prompt_library_bp.route('/api/prompt-library', methods=['POST'])
def add_prompt():
    """新增提示詞"""
    service = get_prompt_library_service()
    data = request.get_json()

    title = data.get('title', '').strip()
    prompt = data.get('prompt', '').strip()
    if not title or not prompt:
        return jsonify({'success': False, 'error': '標題和提示詞為必填'}), 400

    entry = service.add_prompt(
        title=title,
        prompt=prompt,
        negative_prompt=data.get('negative_prompt', ''),
        category=data.get('category', 'custom'),
        tags=data.get('tags', []),
        author=data.get('author', '使用者')
    )
    return jsonify({'success': True, 'prompt': entry})


@prompt_library_bp.route('/api/prompt-library/<prompt_id>/use', methods=['POST'])
def use_prompt(prompt_id):
    """使用提示詞（增加使用計數）"""
    service = get_prompt_library_service()
    result = service.use_prompt(prompt_id)
    if result:
        return jsonify({'success': True, 'prompt': result})
    return jsonify({'success': False, 'error': '找不到該提示詞'}), 404


@prompt_library_bp.route('/api/prompt-library/<prompt_id>/rate', methods=['POST'])
def rate_prompt(prompt_id):
    """評分"""
    service = get_prompt_library_service()
    data = request.get_json()
    rating = data.get('rating', 0)

    result = service.rate_prompt(prompt_id, rating)
    if result:
        return jsonify({'success': True, 'prompt': result})
    return jsonify({'success': False, 'error': '找不到該提示詞'}), 404


@prompt_library_bp.route('/api/prompt-library/<prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """刪除提示詞"""
    service = get_prompt_library_service()
    result = service.delete_prompt(prompt_id)
    if result:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '無法刪除（可能是預設提示詞）'}), 400
