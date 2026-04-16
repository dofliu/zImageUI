"""
Story Routes - 連貫漫畫/故事生成 API
"""
from flask import Blueprint, request, jsonify, render_template, send_file
from services.story_service import get_story_service

story_bp = Blueprint('story', __name__)


# ========== 頁面路由 ==========

@story_bp.route('/story')
def story_page():
    return render_template('story.html')


# ========== 靜態資料 ==========

@story_bp.route('/api/story/presets', methods=['GET'])
def get_presets():
    """取得風格/佈局/鏡頭/氛圍預設值"""
    service = get_story_service()
    return jsonify({
        'success': True,
        'styles': service.get_style_presets(),
        'layouts': service.get_layout_presets(),
        'camera_angles': service.get_camera_angles(),
        'moods': service.get_mood_options()
    })


# ========== 故事 CRUD ==========

@story_bp.route('/api/stories', methods=['GET'])
def list_stories():
    service = get_story_service()
    return jsonify({'success': True, 'stories': service.list_stories()})


@story_bp.route('/api/stories', methods=['POST'])
def create_story():
    service = get_story_service()
    data = request.get_json()
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'success': False, 'error': '標題為必填'}), 400

    story = service.create_story(
        title=title,
        style_preset=data.get('style_preset', 'anime'),
        layout=data.get('layout', '4koma'),
        description=data.get('description', '')
    )
    return jsonify({'success': True, 'story': story})


@story_bp.route('/api/stories/<story_id>', methods=['GET'])
def get_story(story_id):
    service = get_story_service()
    story = service.get_story(story_id)
    if not story:
        return jsonify({'success': False, 'error': '找不到故事'}), 404
    return jsonify({'success': True, 'story': story})


@story_bp.route('/api/stories/<story_id>', methods=['PUT'])
def update_story(story_id):
    service = get_story_service()
    data = request.get_json()
    story = service.update_story(story_id, data)
    if not story:
        return jsonify({'success': False, 'error': '找不到故事'}), 404
    return jsonify({'success': True, 'story': story})


@story_bp.route('/api/stories/<story_id>', methods=['DELETE'])
def delete_story(story_id):
    service = get_story_service()
    if service.delete_story(story_id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '找不到故事'}), 404


# ========== 角色管理 ==========

@story_bp.route('/api/stories/<story_id>/characters', methods=['POST'])
def add_character(story_id):
    service = get_story_service()
    data = request.get_json()
    name = data.get('name', '').strip()
    appearance = data.get('appearance', '').strip()
    if not name or not appearance:
        return jsonify({'success': False, 'error': '名稱和外貌描述為必填'}), 400

    char = service.add_character(
        story_id, name, appearance,
        traits=data.get('traits', []),
        color_palette=data.get('color_palette', '')
    )
    if not char:
        return jsonify({'success': False, 'error': '找不到故事'}), 404
    return jsonify({'success': True, 'character': char})


@story_bp.route('/api/stories/<story_id>/characters/<char_id>', methods=['PUT'])
def update_character(story_id, char_id):
    service = get_story_service()
    data = request.get_json()
    char = service.update_character(story_id, char_id, data)
    if not char:
        return jsonify({'success': False, 'error': '找不到角色'}), 404
    return jsonify({'success': True, 'character': char})


@story_bp.route('/api/stories/<story_id>/characters/<char_id>', methods=['DELETE'])
def remove_character(story_id, char_id):
    service = get_story_service()
    if service.remove_character(story_id, char_id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '找不到角色'}), 404


# ========== 面板管理 ==========

@story_bp.route('/api/stories/<story_id>/panels/<int:panel_index>', methods=['PUT'])
def update_panel(story_id, panel_index):
    service = get_story_service()
    data = request.get_json()
    panel = service.update_panel(story_id, panel_index, data)
    if not panel:
        return jsonify({'success': False, 'error': '找不到面板'}), 404
    return jsonify({'success': True, 'panel': panel})


@story_bp.route('/api/stories/<story_id>/panels', methods=['POST'])
def add_panel(story_id):
    service = get_story_service()
    panel = service.add_panel(story_id)
    if not panel:
        return jsonify({'success': False, 'error': '找不到故事'}), 404
    return jsonify({'success': True, 'panel': panel})


@story_bp.route('/api/stories/<story_id>/panels/<int:panel_index>', methods=['DELETE'])
def remove_panel(story_id, panel_index):
    service = get_story_service()
    if service.remove_panel(story_id, panel_index):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '找不到面板'}), 404


# ========== 提示詞預覽 ==========

@story_bp.route('/api/stories/<story_id>/preview-prompts', methods=['GET'])
def preview_prompts(story_id):
    """預覽所有面板的組裝後提示詞"""
    service = get_story_service()
    prompts = service.assemble_all_prompts(story_id)
    if prompts is None:
        return jsonify({'success': False, 'error': '找不到故事'}), 404
    return jsonify({'success': True, 'prompts': prompts})


# ========== AI 腳本生成 ==========

@story_bp.route('/api/stories/<story_id>/generate-script', methods=['POST'])
def generate_script(story_id):
    """用 AI 自動生成故事腳本"""
    service = get_story_service()
    result = service.generate_script(story_id)
    if result.get('success'):
        return jsonify(result)
    return jsonify(result), 400


# ========== 生成 ==========

@story_bp.route('/api/stories/<story_id>/generate/<int:panel_index>', methods=['POST'])
def generate_panel(story_id, panel_index):
    """生成單一面板"""
    service = get_story_service()
    result = service.generate_panel(story_id, panel_index)
    status_code = 200 if result.get('success') else 500
    return jsonify(result), status_code


@story_bp.route('/api/stories/<story_id>/generate-all', methods=['POST'])
def generate_all(story_id):
    """生成所有面板"""
    service = get_story_service()
    result = service.generate_all_panels(story_id)
    return jsonify(result)


# ========== 圖片存取 ==========

@story_bp.route('/api/stories/<story_id>/panels/<int:panel_index>/image')
def get_panel_image(story_id, panel_index):
    """取得面板圖片"""
    service = get_story_service()
    path = service.get_panel_image_path(story_id, panel_index)
    if not path:
        return jsonify({'success': False, 'error': '找不到圖片'}), 404
    return send_file(path, mimetype='image/png')
