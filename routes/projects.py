"""
Projects Routes - 工作區/專案管理路由
"""
from flask import Blueprint, request, jsonify
from services.project_service import get_project_service

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('/api/projects', methods=['GET'])
def list_projects():
    """列出所有專案"""
    status = request.args.get('status')
    service = get_project_service()
    projects = service.list_all(status)
    # 回傳摘要（不含完整圖片列表）
    summaries = []
    for p in projects:
        summary = {k: v for k, v in p.items() if k != 'images'}
        summary['image_count'] = len(p.get('images', []))
        if p.get('images'):
            summary['cover_image'] = p['images'][0].get('image_url')
        summaries.append(summary)
    return jsonify({'success': True, 'projects': summaries})


@projects_bp.route('/api/projects', methods=['POST'])
def create_project():
    """建立新專案"""
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': '請輸入專案名稱'}), 400

    service = get_project_service()
    project = service.create(
        name=name,
        description=data.get('description', ''),
        default_model=data.get('default_model'),
        default_style=data.get('default_style'),
        default_size=data.get('default_size'),
        default_negative_prompt=data.get('default_negative_prompt', '')
    )
    return jsonify({'success': True, 'project': project})


@projects_bp.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """取得完整專案內容"""
    service = get_project_service()
    project = service.get(project_id)
    if not project:
        return jsonify({'error': '專案不存在'}), 404
    return jsonify({'success': True, 'project': project})


@projects_bp.route('/api/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """更新專案"""
    data = request.get_json()
    service = get_project_service()
    project = service.update(project_id, **data)
    if not project:
        return jsonify({'error': '專案不存在'}), 404
    return jsonify({'success': True, 'project': project})


@projects_bp.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """刪除專案"""
    service = get_project_service()
    service.delete(project_id)
    return jsonify({'success': True, 'message': '已刪除專案'})


@projects_bp.route('/api/projects/<project_id>/images', methods=['POST'])
def add_image(project_id):
    """將圖片加入專案"""
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': '請指定檔案名稱'}), 400

    service = get_project_service()
    image = service.add_image(
        project_id,
        filename=filename,
        prompt=data.get('prompt', ''),
        seed=data.get('seed'),
        model_id=data.get('model'),
        metadata=data.get('metadata')
    )
    if not image:
        return jsonify({'error': '專案不存在'}), 404
    return jsonify({'success': True, 'image': image})


@projects_bp.route('/api/projects/<project_id>/images/<filename>', methods=['DELETE'])
def remove_image(project_id, filename):
    """從專案移除圖片"""
    service = get_project_service()
    if service.remove_image(project_id, filename):
        return jsonify({'success': True, 'message': '已移除'})
    return jsonify({'error': '專案或圖片不存在'}), 404


@projects_bp.route('/api/projects/<project_id>/images/<filename>/rate', methods=['PUT'])
def rate_image(project_id, filename):
    """評分圖片"""
    data = request.get_json()
    rating = data.get('rating')
    if rating is None:
        return jsonify({'error': '請提供評分 (1-5)'}), 400

    service = get_project_service()
    if service.rate_image(project_id, filename, rating):
        return jsonify({'success': True})
    return jsonify({'error': '專案或圖片不存在'}), 404


@projects_bp.route('/api/projects/<project_id>/stats', methods=['GET'])
def project_stats(project_id):
    """專案統計"""
    service = get_project_service()
    stats = service.get_project_stats(project_id)
    if not stats:
        return jsonify({'error': '專案不存在'}), 404
    return jsonify({'success': True, 'stats': stats})


@projects_bp.route('/api/projects/<project_id>/duplicate', methods=['POST'])
def duplicate_project(project_id):
    """複製專案"""
    service = get_project_service()
    new_project = service.duplicate(project_id)
    if not new_project:
        return jsonify({'error': '專案不存在'}), 404
    return jsonify({'success': True, 'project': new_project})
