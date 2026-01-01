"""
Templates Routes - 模板與標籤相關路由
"""
import os
import json
from flask import Blueprint, request, jsonify
import config
from services.history_service import get_history_service


templates_bp = Blueprint('templates', __name__)

# 模板檔案路徑
TEMPLATES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates.json")


@templates_bp.route('/templates', methods=['GET'])
def get_templates():
    """獲取風格模板列表"""
    try:
        if os.path.exists(TEMPLATES_FILE):
            with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            return jsonify({
                'success': True,
                'templates': templates
            })
        else:
            return jsonify({
                'success': False,
                'error': '模板檔案不存在'
            }), 404
    except Exception as e:
        print(f"讀取模板錯誤：{str(e)}")
        return jsonify({'error': str(e)}), 500


@templates_bp.route('/size-presets', methods=['GET'])
def get_size_presets():
    """獲取尺寸預設列表"""
    presets = {
        "社群媒體": [
            {"name": "Instagram 正方形", "width": 1080, "height": 1080, "ratio": "1:1"},
            {"name": "Instagram 直式", "width": 1080, "height": 1350, "ratio": "4:5"},
            {"name": "Facebook 封面", "width": 1200, "height": 630, "ratio": "1.91:1"},
            {"name": "Twitter 卡片", "width": 1200, "height": 675, "ratio": "16:9"},
            {"name": "YouTube 縮圖", "width": 1280, "height": 720, "ratio": "16:9"}
        ],
        "列印尺寸": [
            {"name": "A4 直式", "width": 2480, "height": 3508, "ratio": "A4"},
            {"name": "A4 橫式", "width": 3508, "height": 2480, "ratio": "A4"},
            {"name": "A5 直式", "width": 1748, "height": 2480, "ratio": "A5"},
            {"name": "明信片", "width": 1600, "height": 1200, "ratio": "4:3"}
        ],
        "標準尺寸": [
            {"name": "正方形 512", "width": 512, "height": 512, "ratio": "1:1", "vram": "低"},
            {"name": "正方形 768", "width": 768, "height": 768, "ratio": "1:1", "vram": "中"},
            {"name": "正方形 1024", "width": 1024, "height": 1024, "ratio": "1:1", "vram": "高"},
            {"name": "寬屏 16:9", "width": 1024, "height": 576, "ratio": "16:9", "vram": "中"},
            {"name": "直式 9:16", "width": 576, "height": 1024, "ratio": "9:16", "vram": "中"}
        ]
    }

    return jsonify({
        'success': True,
        'presets': presets,
        'current': {
            'width': config.IMAGE_WIDTH,
            'height': config.IMAGE_HEIGHT
        }
    })


@templates_bp.route('/tags', methods=['GET'])
def get_all_tags():
    """獲取所有使用過的標籤"""
    try:
        history_service = get_history_service()
        history = history_service.load_history()
        all_tags = set()
        tag_counts = {}

        for item in history:
            if 'tags' in item:
                for tag in item['tags']:
                    all_tags.add(tag)
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # 按使用頻率排序
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

        return jsonify({
            'success': True,
            'tags': [{'name': tag, 'count': count} for tag, count in sorted_tags]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@templates_bp.route('/history/<item_id>/tags', methods=['POST'])
def update_tags(item_id):
    """更新歷史記錄的標籤"""
    try:
        data = request.get_json()
        tags = data.get('tags', [])

        history_service = get_history_service()
        history = history_service.load_history()
        updated = False

        for item in history:
            if item.get('id') == item_id:
                item['tags'] = tags
                updated = True
                break

        if updated:
            history_service.save_history(history)
            return jsonify({
                'success': True,
                'message': '標籤已更新'
            })
        else:
            return jsonify({
                'success': False,
                'error': '找不到該記錄'
            }), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@templates_bp.route('/history/filter', methods=['POST'])
def filter_history():
    """根據標籤過濾歷史記錄"""
    try:
        data = request.get_json()
        filter_tags = data.get('tags', [])

        history_service = get_history_service()
        
        if not filter_tags:
            # 沒有過濾條件，返回全部
            history = history_service.load_history()
        else:
            history = history_service.load_history()
            # 過濾包含任一標籤的記錄
            filtered = [
                item for item in history
                if 'tags' in item and any(tag in item['tags'] for tag in filter_tags)
            ]
            history = filtered

        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
