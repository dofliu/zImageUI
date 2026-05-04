"""
Avatar Studio Routes - 照片編輯 / 人物生成功能路由
移植自 avatarFusion，整合進 zImage 的 Provider 架構

所有功能都透過目前選用的雲端 Provider（Gemini / OpenAI）執行。
切換模型不需改程式碼。
"""
import os
import base64
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
import config
from services.model_registry import get_model_registry
from services.history_service import get_history_service

avatar_bp = Blueprint('avatar', __name__)


# ── 頁面 ────────────────────────────────────────────────────────
@avatar_bp.route('/avatar')
def avatar_page():
    return render_template('avatar.html')


# ── 統一生成入口 ─────────────────────────────────────────────────
@avatar_bp.route('/avatar/generate', methods=['POST'])
def avatar_generate():
    """
    Avatar Studio 統一入口

    Request JSON:
    {
        "feature": "professional" | "anime" | "figure" | "sticker" |
                   "passport" | "colorize" | "scene" | "inpaint" |
                   "outpaint" | "tryon" | "exploded" | "doodle" |
                   "logo" | "gif" | "fusion",
        "image": "data:image/jpeg;base64,...",       # 主圖（部分功能必填）
        "image2": "data:image/jpeg;base64,...",      # 第二張圖（tryon/fusion/duo 用）
        "mask": "data:image/png;base64,...",         # 遮罩（inpaint 用）
        "params": { ... }                            # 各功能專屬參數
    }
    """
    try:
        data = request.get_json()
        feature = data.get('feature', '').strip()
        if not feature:
            return jsonify({'success': False, 'error': '請指定功能名稱 (feature)'}), 400

        # 解析圖片
        image_b64, image_mime = _parse_image(data.get('image'))
        image2_b64, image2_mime = _parse_image(data.get('image2'))
        mask_b64, _ = _parse_image(data.get('mask'))

        # logo 功能不需要圖片
        if feature != 'logo' and not image_b64:
            return jsonify({'success': False, 'error': '請上傳圖片'}), 400

        params = data.get('params', {})

        registry = get_model_registry()
        result = registry.edit_photo(
            feature=feature,
            image_base64=image_b64,
            image2_base64=image2_b64,
            mask_base64=mask_b64,
            image_mime=image_mime,
            image2_mime=image2_mime,
            params=params,
        )

        if not result.get('success'):
            return jsonify(result), 400

        # 儲存到 output 資料夾
        filename = _save_image(result['base64'], result.get('mime_type', 'image/png'), feature)

        # 加入歷史
        try:
            history_service = get_history_service()
            history_service.add_to_history(f'[Avatar/{feature}]', filename)
        except Exception:
            pass

        mime = result.get('mime_type', 'image/png')
        return jsonify({
            'success': True,
            'image': f"data:{mime};base64,{result['base64']}",
            'filename': filename,
            'feature': feature,
        })

    except Exception as e:
        print(f"[Avatar] 錯誤: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ── 輔助函式 ─────────────────────────────────────────────────────
def _parse_image(data_url: str):
    """解析 data URL，回傳 (base64_str, mime_type) 或 (None, None)"""
    if not data_url:
        return None, None
    try:
        if ',' in data_url:
            header, b64 = data_url.split(',', 1)
            mime = header.split(':')[1].split(';')[0] if ':' in header else 'image/jpeg'
        else:
            b64 = data_url
            mime = 'image/jpeg'
        return b64, mime
    except Exception:
        return None, None


def _save_image(b64: str, mime_type: str, feature: str) -> str:
    """儲存 base64 圖片到 output 資料夾，回傳檔名"""
    ext = mime_type.split('/')[-1].replace('jpeg', 'jpg')
    if ext not in ('png', 'jpg', 'jpeg', 'webp'):
        ext = 'png'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"avatar_{feature}_{timestamp}.{ext}"
    save_path = os.path.join(config.OUTPUT_PATH, filename)
    try:
        os.makedirs(config.OUTPUT_PATH, exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(base64.b64decode(b64))
    except Exception as e:
        print(f"[Avatar] 儲存圖片失敗: {e}")
    return filename


# ── 取得 Avatar Studio 功能清單 ──────────────────────────────────
@avatar_bp.route('/avatar/features', methods=['GET'])
def get_features():
    """回傳所有 Avatar Studio 功能的中繼資料（給前端建 UI 用）"""
    features = [
        {
            'id': 'professional',
            'name': '專業大頭照',
            'icon': '👔',
            'description': '生成適合履歷 / 公司官網的專業形象照',
            'needs_image': True,
            'needs_image2': False,
            'params': ['background', 'attire', 'hairstyle', 'expression', 'accessory', 'preserve_features'],
        },
        {
            'id': 'anime',
            'name': '動漫風格',
            'icon': '🎨',
            'description': '將照片轉換成各種動漫藝術風格',
            'needs_image': True,
            'needs_image2': False,
            'params': ['style', 'strength', 'negative_prompt'],
        },
        {
            'id': 'figure',
            'name': '公仔生成',
            'icon': '🪆',
            'description': '生成 1/7 比例高端收藏人偶產品照',
            'needs_image': True,
            'needs_image2': False,
            'params': ['figure_base', 'team_mode'],
        },
        {
            'id': 'sticker',
            'name': '貼紙創作',
            'icon': '🎭',
            'description': '生成各種風格的客製化貼紙',
            'needs_image': True,
            'needs_image2': False,
            'params': ['sticker_style', 'theme', 'add_text'],
        },
        {
            'id': 'passport',
            'name': '證件照',
            'icon': '🪪',
            'description': '生成符合規格的護照 / 履歷證件照',
            'needs_image': True,
            'needs_image2': False,
            'params': ['photo_type'],
        },
        {
            'id': 'colorize',
            'name': '老照片上色',
            'icon': '🎨',
            'description': '將黑白老照片轉為彩色',
            'needs_image': True,
            'needs_image2': False,
            'params': [],
        },
        {
            'id': 'scene',
            'name': '場景替換',
            'icon': '🌆',
            'description': '更換照片背景，保留主體',
            'needs_image': True,
            'needs_image2': False,
            'params': ['scene_prompt', 'keep_hairstyle'],
        },
        {
            'id': 'inpaint',
            'name': '局部重繪',
            'icon': '✏️',
            'description': '繪製遮罩範圍，讓 AI 重新生成該區域',
            'needs_image': True,
            'needs_mask': True,
            'needs_image2': False,
            'params': ['inpaint_prompt'],
        },
        {
            'id': 'outpaint',
            'name': '場景延伸',
            'icon': '↔️',
            'description': '向外延伸圖片畫面',
            'needs_image': True,
            'needs_image2': False,
            'params': ['aspect_ratio', 'outpaint_prompt'],
        },
        {
            'id': 'tryon',
            'name': '虛擬換裝',
            'icon': '👗',
            'description': '上傳服裝圖片，AI 幫你試穿',
            'needs_image': True,
            'needs_image2': True,
            'params': [],
        },
        {
            'id': 'exploded',
            'name': '爆炸圖',
            'icon': '💥',
            'description': '生成產品爆炸分解技術插圖',
            'needs_image': True,
            'needs_image2': False,
            'params': [],
        },
        {
            'id': 'doodle',
            'name': '塗鴉生圖',
            'icon': '🖊️',
            'description': '將草圖 / 塗鴉轉換成完整圖像',
            'needs_image': True,
            'needs_image2': False,
            'params': ['doodle_style', 'doodle_prompt'],
        },
        {
            'id': 'logo',
            'name': 'Logo 設計',
            'icon': '🎯',
            'description': '生成專業品牌 Logo（不需上傳圖片）',
            'needs_image': False,
            'needs_image2': False,
            'params': ['brand', 'concept', 'logo_type', 'color', 'elements'],
        },
        {
            'id': 'gif',
            'name': 'GIF 動畫幀',
            'icon': '🎬',
            'description': '生成動畫關鍵幀圖像',
            'needs_image': False,
            'needs_image2': False,
            'params': ['gif_prompt'],
        },
        {
            'id': 'fusion',
            'name': '照片融合',
            'icon': '🔀',
            'description': '將兩張人物照合成在新場景中',
            'needs_image': True,
            'needs_image2': True,
            'params': ['scene_prompt'],
        },
    ]
    return jsonify({'success': True, 'features': features})
