"""
Gallery Routes - 作品集 / 展示廊路由
提供可分享的公開作品展示頁面和精選集功能
"""
import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
import config
from services.history_service import get_history_service

gallery_bp = Blueprint('gallery', __name__)

# 作品集資料檔案
GALLERY_FILE = os.path.join(config.OUTPUT_PATH, "galleries.json")


def _load_galleries():
    """載入所有作品集"""
    if os.path.exists(GALLERY_FILE):
        try:
            with open(GALLERY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_galleries(galleries):
    """儲存作品集"""
    try:
        os.makedirs(os.path.dirname(GALLERY_FILE), exist_ok=True)
        with open(GALLERY_FILE, 'w', encoding='utf-8') as f:
            json.dump(galleries, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"儲存作品集失敗: {e}")


@gallery_bp.route('/gallery', methods=['GET'])
def gallery_page():
    """作品集展示頁面"""
    return render_template('gallery.html')


@gallery_bp.route('/gallery/<gallery_id>', methods=['GET'])
def view_gallery(gallery_id):
    """查看特定作品集"""
    return render_template('gallery.html', gallery_id=gallery_id)


@gallery_bp.route('/api/galleries', methods=['GET'])
def list_galleries():
    """列出所有作品集"""
    galleries = _load_galleries()
    # 不回傳完整圖片列表，只回傳摘要
    summaries = []
    for g in galleries:
        summaries.append({
            'id': g['id'],
            'title': g['title'],
            'description': g.get('description', ''),
            'cover_image': g['images'][0]['image_url'] if g.get('images') else None,
            'image_count': len(g.get('images', [])),
            'created_at': g['created_at'],
            'updated_at': g.get('updated_at', g['created_at']),
            'is_public': g.get('is_public', True),
            'views': g.get('views', 0),
            'tags': g.get('tags', [])
        })
    return jsonify({'success': True, 'galleries': summaries})


@gallery_bp.route('/api/galleries', methods=['POST'])
def create_gallery():
    """建立新作品集"""
    data = request.get_json()
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': '請輸入作品集標題'}), 400

    gallery = {
        'id': str(uuid.uuid4())[:8],
        'title': title,
        'description': data.get('description', ''),
        'images': [],
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'is_public': data.get('is_public', True),
        'views': 0,
        'tags': data.get('tags', []),
        'layout': data.get('layout', 'masonry'),  # masonry, grid, slideshow
        'theme': data.get('theme', 'default')  # default, dark, minimal, elegant
    }

    galleries = _load_galleries()
    galleries.insert(0, gallery)
    _save_galleries(galleries)

    return jsonify({'success': True, 'gallery': gallery})


@gallery_bp.route('/api/galleries/<gallery_id>', methods=['GET'])
def get_gallery(gallery_id):
    """取得特定作品集完整內容"""
    galleries = _load_galleries()
    for g in galleries:
        if g['id'] == gallery_id:
            # 增加瀏覽計數
            g['views'] = g.get('views', 0) + 1
            _save_galleries(galleries)
            return jsonify({'success': True, 'gallery': g})
    return jsonify({'error': '作品集不存在'}), 404


@gallery_bp.route('/api/galleries/<gallery_id>', methods=['PUT'])
def update_gallery(gallery_id):
    """更新作品集資訊"""
    data = request.get_json()
    galleries = _load_galleries()

    for g in galleries:
        if g['id'] == gallery_id:
            if 'title' in data:
                g['title'] = data['title']
            if 'description' in data:
                g['description'] = data['description']
            if 'is_public' in data:
                g['is_public'] = data['is_public']
            if 'tags' in data:
                g['tags'] = data['tags']
            if 'layout' in data:
                g['layout'] = data['layout']
            if 'theme' in data:
                g['theme'] = data['theme']
            g['updated_at'] = datetime.now().isoformat()
            _save_galleries(galleries)
            return jsonify({'success': True, 'gallery': g})

    return jsonify({'error': '作品集不存在'}), 404


@gallery_bp.route('/api/galleries/<gallery_id>', methods=['DELETE'])
def delete_gallery(gallery_id):
    """刪除作品集"""
    galleries = _load_galleries()
    galleries = [g for g in galleries if g['id'] != gallery_id]
    _save_galleries(galleries)
    return jsonify({'success': True, 'message': '已刪除作品集'})


@gallery_bp.route('/api/galleries/<gallery_id>/images', methods=['POST'])
def add_images_to_gallery(gallery_id):
    """將圖片加入作品集"""
    data = request.get_json()
    filenames = data.get('filenames', [])

    if not filenames:
        return jsonify({'error': '請選擇要加入的圖片'}), 400

    galleries = _load_galleries()
    history = get_history_service().load_history()

    # 建立 filename -> history item 的映射
    history_map = {item['filename']: item for item in history}

    for g in galleries:
        if g['id'] == gallery_id:
            existing_filenames = {img['filename'] for img in g.get('images', [])}

            added = 0
            for fn in filenames:
                if fn in existing_filenames:
                    continue

                image_entry = {
                    'filename': fn,
                    'image_url': f'/images/{fn}',
                    'added_at': datetime.now().isoformat(),
                    'caption': '',
                    'order': len(g['images'])
                }

                # 從歷史記錄補充 prompt 資訊
                if fn in history_map:
                    image_entry['prompt'] = history_map[fn].get('prompt', '')

                g['images'].append(image_entry)
                added += 1

            g['updated_at'] = datetime.now().isoformat()
            _save_galleries(galleries)
            return jsonify({
                'success': True,
                'added': added,
                'total': len(g['images']),
                'message': f'已加入 {added} 張圖片'
            })

    return jsonify({'error': '作品集不存在'}), 404


@gallery_bp.route('/api/galleries/<gallery_id>/images/<filename>', methods=['DELETE'])
def remove_image_from_gallery(gallery_id, filename):
    """從作品集移除圖片"""
    galleries = _load_galleries()

    for g in galleries:
        if g['id'] == gallery_id:
            g['images'] = [img for img in g['images'] if img['filename'] != filename]
            g['updated_at'] = datetime.now().isoformat()
            _save_galleries(galleries)
            return jsonify({'success': True, 'message': '已從作品集移除'})

    return jsonify({'error': '作品集不存在'}), 404


@gallery_bp.route('/api/galleries/<gallery_id>/images/<filename>/caption', methods=['PUT'])
def update_image_caption(gallery_id, filename):
    """更新圖片說明文字"""
    data = request.get_json()
    caption = data.get('caption', '')

    galleries = _load_galleries()
    for g in galleries:
        if g['id'] == gallery_id:
            for img in g['images']:
                if img['filename'] == filename:
                    img['caption'] = caption
                    g['updated_at'] = datetime.now().isoformat()
                    _save_galleries(galleries)
                    return jsonify({'success': True, 'message': '已更新說明'})
            return jsonify({'error': '圖片不存在'}), 404

    return jsonify({'error': '作品集不存在'}), 404


@gallery_bp.route('/api/galleries/<gallery_id>/reorder', methods=['PUT'])
def reorder_images(gallery_id):
    """重新排序作品集圖片"""
    data = request.get_json()
    ordered_filenames = data.get('filenames', [])

    galleries = _load_galleries()
    for g in galleries:
        if g['id'] == gallery_id:
            # 建立 filename -> image 映射
            img_map = {img['filename']: img for img in g['images']}
            new_images = []
            for idx, fn in enumerate(ordered_filenames):
                if fn in img_map:
                    img = img_map[fn]
                    img['order'] = idx
                    new_images.append(img)
            # 加入未在排序列表中的圖片
            for img in g['images']:
                if img['filename'] not in ordered_filenames:
                    img['order'] = len(new_images)
                    new_images.append(img)

            g['images'] = new_images
            g['updated_at'] = datetime.now().isoformat()
            _save_galleries(galleries)
            return jsonify({'success': True, 'message': '已重新排序'})

    return jsonify({'error': '作品集不存在'}), 404
