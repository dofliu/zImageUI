"""
Image-to-Image Routes - 圖生圖功能路由
支援上傳參考圖片，基於參考圖進行風格轉換或修改
"""
import os
import base64
from io import BytesIO
from datetime import datetime
from flask import Blueprint, request, jsonify
from PIL import Image
import config
from services.history_service import get_history_service

img2img_bp = Blueprint('img2img', __name__)


def _load_reference_image(image_data, target_width, target_height):
    """載入並預處理參考圖片"""
    if image_data.startswith('data:'):
        # Base64 encoded image
        header, data = image_data.split(',', 1)
        image_bytes = base64.b64decode(data)
    else:
        image_bytes = base64.b64decode(image_data)

    image = Image.open(BytesIO(image_bytes)).convert('RGB')
    image = image.resize((target_width, target_height), Image.LANCZOS)
    return image


@img2img_bp.route('/img2img', methods=['POST'])
def image_to_image():
    """圖生圖 API

    接受參考圖片和提示詞，生成基於參考圖的新圖片。
    支援 multipart/form-data (檔案上傳) 和 JSON (base64) 兩種方式。
    """
    try:
        # 處理不同的上傳方式
        if request.content_type and 'multipart/form-data' in request.content_type:
            # 檔案上傳方式
            if 'image' not in request.files:
                return jsonify({'error': '請上傳參考圖片'}), 400

            file = request.files['image']
            prompt = request.form.get('prompt', '')
            negative_prompt = request.form.get('negative_prompt', '')
            strength = float(request.form.get('strength', 0.75))
            custom_width = request.form.get('width', type=int)
            custom_height = request.form.get('height', type=int)
            style_keywords = request.form.get('style_keywords', '')

            ref_image = Image.open(file.stream).convert('RGB')
        else:
            # JSON + base64 方式
            data = request.get_json()
            if not data or not data.get('image'):
                return jsonify({'error': '請提供參考圖片'}), 400

            prompt = data.get('prompt', '')
            negative_prompt = data.get('negative_prompt', '')
            strength = float(data.get('strength', 0.75))
            custom_width = data.get('width')
            custom_height = data.get('height')
            style_keywords = data.get('style_keywords', '')

            ref_image = _load_reference_image(
                data['image'],
                custom_width or config.IMAGE_WIDTH,
                custom_height or config.IMAGE_HEIGHT
            )

        if not prompt:
            return jsonify({'error': '請輸入提示詞'}), 400

        # 確保 strength 在合理範圍
        strength = max(0.1, min(1.0, strength))

        # 組合提示詞
        full_prompt = f"{prompt}, {style_keywords}" if style_keywords else prompt

        # 確定尺寸
        width = custom_width or config.IMAGE_WIDTH
        height = custom_height or config.IMAGE_HEIGHT

        # 調整參考圖尺寸
        ref_image = ref_image.resize((width, height), Image.LANCZOS)

        # 使用模型進行 img2img 生成
        from services.model_registry import get_model_registry
        import torch
        import random

        registry = get_model_registry()
        if registry.active_pipeline is None:
            return jsonify({'error': '尚未載入模型，請先在模型選擇器中載入一個模型'}), 400

        model_info = registry.get_active_model()

        # 清理 GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        seed = random.randint(0, 2**32 - 1)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        generator = torch.Generator(device=device).manual_seed(seed)

        # 準備生成參數 - img2img 模式
        generate_kwargs = {
            'prompt': full_prompt,
            'image': ref_image,
            'strength': strength,
            'num_inference_steps': model_info.get('default_steps', config.NUM_INFERENCE_STEPS),
            'guidance_scale': model_info.get('default_guidance_scale', config.GUIDANCE_SCALE),
            'generator': generator,
        }

        if negative_prompt and model_info.get('supports_negative_prompt', True):
            generate_kwargs['negative_prompt'] = negative_prompt

        print(f"[img2img] 生成: {full_prompt}")
        print(f"  強度: {strength}, 解析度: {width}x{height}")

        result_image = registry.active_pipeline(**generate_kwargs).images[0]

        # 儲存圖片
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"img2img_{timestamp}.png"
        save_path = os.path.join(config.OUTPUT_PATH, filename)
        result_image.save(save_path)

        # 同時保存參考圖（用於比較）
        ref_filename = f"ref_{timestamp}.png"
        ref_save_path = os.path.join(config.OUTPUT_PATH, ref_filename)
        ref_image.save(ref_save_path)

        # 添加歷史
        history_service = get_history_service()
        history_service.add_to_history(f"[img2img] {prompt}", filename, tags=["img2img"])

        # 回傳 base64
        buffered = BytesIO()
        result_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({
            'success': True,
            'image': f"data:image/png;base64,{img_str}",
            'filename': filename,
            'ref_filename': ref_filename,
            'prompt': prompt,
            'seed': seed,
            'strength': strength,
            'message': f'圖生圖完成 (強度: {strength})'
        })

    except Exception as e:
        print(f"img2img 錯誤: {str(e)}")
        return jsonify({'error': str(e)}), 500


@img2img_bp.route('/img2img/variations', methods=['POST'])
def generate_variations():
    """基於一張圖片生成多個變體

    使用不同的 strength 和 seed 產生多種變化
    """
    try:
        data = request.get_json()
        if not data or not data.get('image'):
            return jsonify({'error': '請提供參考圖片'}), 400

        prompt = data.get('prompt', '')
        count = min(data.get('count', 4), 8)  # 最多 8 個變體
        strength_range = data.get('strength_range', [0.3, 0.5, 0.7, 0.9])

        if not prompt:
            return jsonify({'error': '請輸入提示詞'}), 400

        width = data.get('width') or config.IMAGE_WIDTH
        height = data.get('height') or config.IMAGE_HEIGHT

        ref_image = _load_reference_image(data['image'], width, height)

        from services.model_registry import get_model_registry
        import torch
        import random

        registry = get_model_registry()
        if registry.active_pipeline is None:
            return jsonify({'error': '尚未載入模型'}), 400

        model_info = registry.get_active_model()
        history_service = get_history_service()

        results = []
        # 確保有足夠的 strength 值
        while len(strength_range) < count:
            strength_range.append(random.uniform(0.3, 0.9))
        strength_range = strength_range[:count]

        for idx, strength in enumerate(strength_range):
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                seed = random.randint(0, 2**32 - 1)
                device = "cuda" if torch.cuda.is_available() else "cpu"
                generator = torch.Generator(device=device).manual_seed(seed)

                generate_kwargs = {
                    'prompt': prompt,
                    'image': ref_image,
                    'strength': strength,
                    'num_inference_steps': model_info.get('default_steps', config.NUM_INFERENCE_STEPS),
                    'guidance_scale': model_info.get('default_guidance_scale', config.GUIDANCE_SCALE),
                    'generator': generator,
                }

                result_image = registry.active_pipeline(**generate_kwargs).images[0]

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"variation_{timestamp}_{idx+1:02d}.png"
                save_path = os.path.join(config.OUTPUT_PATH, filename)
                result_image.save(save_path)

                history_service.add_to_history(
                    f"[variation] {prompt} (strength={strength:.2f})",
                    filename, tags=["variation", "img2img"]
                )

                buffered = BytesIO()
                result_image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

                results.append({
                    'success': True,
                    'image': f"data:image/png;base64,{img_str}",
                    'filename': filename,
                    'strength': strength,
                    'seed': seed,
                    'index': idx + 1
                })

                print(f"  [variation {idx+1}/{count}] strength={strength:.2f}, seed={seed}")

            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e),
                    'strength': strength,
                    'index': idx + 1
                })

        succeeded = sum(1 for r in results if r['success'])
        return jsonify({
            'success': True,
            'total': count,
            'succeeded': succeeded,
            'failed': count - succeeded,
            'results': results,
            'message': f'已生成 {succeeded}/{count} 個變體'
        })

    except Exception as e:
        print(f"variation 錯誤: {str(e)}")
        return jsonify({'error': str(e)}), 500
