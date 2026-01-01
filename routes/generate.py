"""
Generate Routes - 圖片生成相關路由
"""
import os
import base64
from io import BytesIO
from datetime import datetime
from flask import Blueprint, request, jsonify
import config
from services.model_service import get_model_service
from services.history_service import get_history_service


generate_bp = Blueprint('generate', __name__)


@generate_bp.route('/generate', methods=['POST'])
def generate_image():
    """生成圖片 API"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        negative_prompt = data.get('negative_prompt', '')  # 負面提示詞
        style_keywords = data.get('style_keywords', '')  # 風格關鍵字
        custom_width = data.get('width')  # 自定義寬度
        custom_height = data.get('height')  # 自定義高度

        if not prompt:
            return jsonify({'error': '請輸入提示詞'}), 400

        # 組合風格關鍵字到提示詞
        if style_keywords:
            full_prompt = f"{prompt}, {style_keywords}"
        else:
            full_prompt = prompt

        # 確定使用的尺寸
        width = custom_width if custom_width else config.IMAGE_WIDTH
        height = custom_height if custom_height else config.IMAGE_HEIGHT

        # 使用模型服務生成圖片
        model_service = get_model_service()
        if style_keywords:
            print(f"風格: {style_keywords}")
        
        image, seed = model_service.generate_image(
            full_prompt, width, height, 
            negative_prompt=negative_prompt if negative_prompt else None
        )

        # 生成帶有日期時間的檔案名稱
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_{timestamp}.png"
        save_path = os.path.join(config.OUTPUT_PATH, filename)

        # 儲存圖片
        image.save(save_path)
        print(f"圖片已儲存至：{save_path}")

        # 添加到歷史記錄
        history_service = get_history_service()
        history_service.add_to_history(prompt, filename)

        # 將圖片轉換為 base64 以便在網頁上顯示
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({
            'success': True,
            'image': f"data:image/png;base64,{img_str}",
            'filename': filename,
            'prompt': prompt,
            'message': f'圖片已成功生成並儲存為 {filename}'
        })

    except Exception as e:
        print(f"錯誤：{str(e)}")
        return jsonify({'error': str(e)}), 500


@generate_bp.route('/batch-generate', methods=['POST'])
def batch_generate():
    """批量生成圖片 API"""
    try:
        data = request.get_json()
        prompts = data.get('prompts', [])
        negative_prompt = data.get('negative_prompt', '')  # 批量共用負面提示詞

        if not prompts or len(prompts) == 0:
            return jsonify({'error': '請輸入至少一個提示詞'}), 400

        # 限制批量數量 (避免 VRAM 問題)
        max_batch = 20
        if len(prompts) > max_batch:
            return jsonify({'error': f'批量生成最多支援 {max_batch} 張圖片'}), 400

        model_service = get_model_service()
        history_service = get_history_service()

        results = []
        failed_prompts = []

        print(f"\n開始批量生成 {len(prompts)} 張圖片...")

        for idx, prompt in enumerate(prompts, 1):
            prompt = prompt.strip()
            if not prompt:
                continue

            try:
                print(f"\n[{idx}/{len(prompts)}] 生成：{prompt}")

                # 生成圖片
                image, seed = model_service.generate_image(
                    prompt, config.IMAGE_WIDTH, config.IMAGE_HEIGHT,
                    negative_prompt=negative_prompt if negative_prompt else None
                )

                # 生成檔案名稱
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"batch_{timestamp}_{idx:03d}.png"
                save_path = os.path.join(config.OUTPUT_PATH, filename)

                # 儲存圖片
                image.save(save_path)
                print(f"✓ 圖片已儲存: {filename}")

                # 添加到歷史記錄
                history_service.add_to_history(prompt, filename)

                # 轉換為 base64
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

                results.append({
                    'success': True,
                    'prompt': prompt,
                    'filename': filename,
                    'image': f"data:image/png;base64,{img_str}",
                    'index': idx
                })

            except Exception as e:
                print(f"✗ 生成失敗 [{idx}/{len(prompts)}]: {str(e)}")
                failed_prompts.append({
                    'prompt': prompt,
                    'index': idx,
                    'error': str(e)
                })
                results.append({
                    'success': False,
                    'prompt': prompt,
                    'error': str(e),
                    'index': idx
                })

        print(f"\n批量生成完成! 成功: {len(results) - len(failed_prompts)}/{len(prompts)}")

        return jsonify({
            'success': True,
            'total': len(prompts),
            'succeeded': len(results) - len(failed_prompts),
            'failed': len(failed_prompts),
            'results': results,
            'message': f'批量生成完成，成功 {len(results) - len(failed_prompts)} 張，失敗 {len(failed_prompts)} 張'
        })

    except Exception as e:
        print(f"批量生成錯誤：{str(e)}")
        return jsonify({'error': str(e)}), 500


@generate_bp.route('/seed-control', methods=['POST'])
def generate_with_seed():
    """使用指定種子生成圖片（用於重現結果）"""
    try:
        import random
        
        data = request.get_json()
        prompt = data.get('prompt', '')
        negative_prompt = data.get('negative_prompt', '')  # 負面提示詞
        seed = data.get('seed')
        style_keywords = data.get('style_keywords', '')
        custom_width = data.get('width')
        custom_height = data.get('height')

        if not prompt:
            return jsonify({'error': '請輸入提示詞'}), 400

        if seed is None:
            seed = random.randint(0, 2**32 - 1)

        # 組合風格關鍵字
        if style_keywords:
            full_prompt = f"{prompt}, {style_keywords}"
        else:
            full_prompt = prompt

        # 確定尺寸
        width = custom_width if custom_width else config.IMAGE_WIDTH
        height = custom_height if custom_height else config.IMAGE_HEIGHT

        # 使用模型服務生成圖片
        model_service = get_model_service()
        history_service = get_history_service()
        
        print(f"開始生成（固定種子）：{full_prompt}")
        print(f"種子: {seed}")
        print(f"解析度: {width}x{height}")

        image, _ = model_service.generate_image(
            full_prompt, width, height, seed,
            negative_prompt=negative_prompt if negative_prompt else None
        )

        # 儲存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"seed_{seed}_{timestamp}.png"
        save_path = os.path.join(config.OUTPUT_PATH, filename)
        image.save(save_path)

        # 添加到歷史
        history_service.add_to_history(prompt, filename)

        # 轉base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({
            'success': True,
            'image': f"data:image/png;base64,{img_str}",
            'filename': filename,
            'prompt': prompt,
            'seed': seed,
            'message': f'圖片已生成（種子: {seed}）'
        })
    except Exception as e:
        print(f"錯誤：{str(e)}")
        return jsonify({'error': str(e)}), 500
