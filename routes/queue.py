"""
Queue Routes - 生成佇列管理路由
"""
from flask import Blueprint, request, jsonify
from services.queue_service import get_queue_service

queue_bp = Blueprint('queue', __name__)


@queue_bp.route('/api/queue/submit', methods=['POST'])
def submit_task():
    """提交生成任務到佇列"""
    data = request.get_json()
    task_type = data.get('type', 'generate')
    params = data.get('params', {})
    priority = data.get('priority', 0)

    if not params.get('prompt'):
        return jsonify({'error': '請提供 prompt 參數'}), 400

    service = get_queue_service()
    task = service.submit(task_type, params, priority)
    return jsonify({'success': True, 'task': task})


@queue_bp.route('/api/queue/task/<task_id>', methods=['GET'])
def get_task(task_id):
    """查詢任務狀態"""
    service = get_queue_service()
    task = service.get_task(task_id)
    if not task:
        return jsonify({'error': '任務不存在'}), 404

    # 安全回傳（移除大型 base64 結果）
    result = dict(task)
    if result.get('result') and isinstance(result['result'], dict):
        result['has_result'] = True
        result['result_summary'] = {
            k: v for k, v in result['result'].items() if k != 'image'
        }
        if 'image' in result['result']:
            result['result_summary']['has_image'] = True

    return jsonify({'success': True, 'task': result})


@queue_bp.route('/api/queue/task/<task_id>/result', methods=['GET'])
def get_task_result(task_id):
    """取得任務完整結果（含圖片）"""
    service = get_queue_service()
    task = service.get_task(task_id)
    if not task:
        return jsonify({'error': '任務不存在'}), 404
    if task['status'] != 'completed':
        return jsonify({'error': '任務尚未完成', 'status': task['status']}), 400
    return jsonify({'success': True, 'result': task.get('result')})


@queue_bp.route('/api/queue/task/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """取消任務"""
    service = get_queue_service()
    result = service.cancel_task(task_id)
    if result['success']:
        return jsonify(result)
    return jsonify(result), 400


@queue_bp.route('/api/queue/status', methods=['GET'])
def queue_status():
    """佇列狀態總覽"""
    service = get_queue_service()
    return jsonify({'success': True, 'status': service.get_queue_status()})


@queue_bp.route('/api/queue/tasks', methods=['GET'])
def list_tasks():
    """列出最近任務"""
    limit = request.args.get('limit', 20, type=int)
    service = get_queue_service()
    return jsonify({'success': True, 'tasks': service.get_recent_tasks(limit)})


@queue_bp.route('/api/queue/clear', methods=['POST'])
def clear_completed():
    """清除已完成的任務"""
    service = get_queue_service()
    result = service.clear_completed()
    return jsonify({'success': True, **result})
