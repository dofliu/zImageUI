import torch
import os
from diffusers import ZImagePipeline
from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
import base64
from io import BytesIO
import random
import config  # 導入配置檔案
import json

app = Flask(__name__)

# 從配置檔案讀取路徑設定
cache_path = config.CACHE_PATH
output_path = config.OUTPUT_PATH
history_file = os.path.join(output_path, "history.json")
os.makedirs(cache_path, exist_ok=True)
os.makedirs(output_path, exist_ok=True)

# 全域變數存放模型
pipe = None

# 歷史記錄管理
def load_history():
    """載入歷史記錄"""
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    """儲存歷史記錄"""
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"儲存歷史記錄失敗: {e}")

def add_to_history(prompt, filename):
    """新增歷史記錄"""
    history = load_history()
    history_item = {
        'prompt': prompt,
        'filename': filename,
        'timestamp': datetime.now().isoformat(),
        'image_url': f'/images/{filename}'
    }
    history.insert(0, history_item)  # 最新的在前面
    # 限制歷史記錄數量 (最多50筆)
    if len(history) > 50:
        history = history[:50]
    save_history(history)
    return history_item

def initialize_model():
    """初始化模型 (只執行一次)"""
    global pipe
    if pipe is None:
        # 檢查本地快取是否存在
        model_cache_exists = os.path.exists(os.path.join(cache_path, "models--Tongyi-MAI--Z-Image-Turbo"))
        if model_cache_exists:
            print("✓ 發現本地快取,從硬碟載入模型...")
        else:
            print("✗ 未發現本地快取,將從 Hugging Face 下載模型 (這需要較長時間)...")

        import time
        start_time = time.time()

        pipe = ZImagePipeline.from_pretrained(
            "Tongyi-MAI/Z-Image-Turbo",
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            cache_dir=cache_path,
            use_safetensors=True,
            local_files_only=False,  # 允許從網路下載,但會優先使用本地快取
        )

        # 針對 12GB VRAM 的優化設定
        print("⟳ 啟用 Sequential CPU Offload (更激進的顯存優化)...")
        pipe.enable_sequential_cpu_offload()
        # 啟用額外的 VRAM 優化
        optimizations = []

        if config.ENABLE_ATTENTION_SLICING:
            if hasattr(pipe, 'enable_attention_slicing'):
                try:
                    pipe.enable_attention_slicing("auto")
                    optimizations.append("Attention Slicing")
                except Exception as e:
                    print(f"! Attention Slicing 啟用失敗: {e}")

        if config.ENABLE_VAE_SLICING:
            if hasattr(pipe, 'enable_vae_slicing'):
                try:
                    pipe.enable_vae_slicing()
                    optimizations.append("VAE Slicing")
                except Exception as e:
                    print(f"! VAE Slicing 啟用失敗: {e}")

        if config.ENABLE_XFORMERS:
            if hasattr(pipe, 'enable_xformers_memory_efficient_attention'):
                try:
                    pipe.enable_xformers_memory_efficient_attention()
                    optimizations.append("xFormers Attention")
                except Exception as e:
                    print(f"! xFormers 啟用失敗: {e}")

        if optimizations:
            print(f"✓ 已啟用額外優化: {', '.join(optimizations)}")

        # 嘗試啟用 VAE Tiling (如果 pipeline 支援)
        try:
            if hasattr(pipe, 'enable_vae_tiling'):
                pipe.enable_vae_tiling()
                print("✓ 已啟用 VAE Tiling (優化高解析度生成)")
            else:
                print("! ZImagePipeline 不支援 VAE Tiling，跳過此優化")
        except Exception as e:
            print(f"! VAE Tiling 啟用失敗: {e}")

        # 嘗試啟用 Flash Attention 加速 (如果環境支援)
        try:
            if hasattr(pipe, 'transformer') and hasattr(pipe.transformer, 'set_attention_backend'):
                pipe.transformer.set_attention_backend("flash")
                print("✓ 已啟用 Flash Attention 加速")
            else:
                print("! Flash Attention 不可用，使用預設 Attention")
        except Exception as e:
            print(f"! Flash Attention 啟用失敗: {e}")

        # 注意: 已使用 enable_model_cpu_offload()，不再需要 pipe.to("cuda")

        elapsed_time = time.time() - start_time
        print(f"✓ 模型載入完成! (耗時 {elapsed_time:.1f} 秒)")
    else:
        print("✓ 模型已在記憶體中,跳過載入")

@app.route('/')
def index():
    """首頁"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_image():
    """生成圖片 API"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')

        if not prompt:
            return jsonify({'error': '請輸入提示詞'}), 400

        # 確保模型已載入
        initialize_model()

        # 生成前清理 GPU 快取
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("✓ 已清理 GPU 快取")

        # 生成圖像
        print(f"開始生成：{prompt}")
        # 使用隨機種子,讓每次生成的圖片都不同
        seed = random.randint(0, 2**32 - 1)
        print(f"使用種子: {seed}")

        # 使用配置檔案中的參數生成圖片
        print(f"生成解析度: {config.IMAGE_WIDTH}x{config.IMAGE_HEIGHT}")

        # 生成圖片
        # 使用 CUDA generator 以確保與模型在同一設備
        device = "cuda" if torch.cuda.is_available() else "cpu"
        generator = torch.Generator(device=device).manual_seed(seed)

        image = pipe(
            prompt=prompt,
            height=config.IMAGE_HEIGHT,
            width=config.IMAGE_WIDTH,
            num_inference_steps=config.NUM_INFERENCE_STEPS,
            guidance_scale=config.GUIDANCE_SCALE,
            generator=generator,
        ).images[0]

        # 生成帶有日期時間的檔案名稱
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_{timestamp}.png"
        save_path = os.path.join(output_path, filename)

        # 儲存圖片
        image.save(save_path)
        print(f"圖片已儲存至：{save_path}")

        # 添加到歷史記錄
        add_to_history(prompt, filename)

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

@app.route('/images/<filename>')
def get_image(filename):
    """提供圖片下載"""
    return send_from_directory(output_path, filename)

@app.route('/history', methods=['GET'])
def get_history():
    """獲取歷史記錄"""
    try:
        history = load_history()
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['DELETE'])
def clear_history():
    """清除所有歷史記錄"""
    try:
        save_history([])
        return jsonify({
            'success': True,
            'message': '歷史記錄已清除'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 顯示配置資訊
    config.print_config_info()

    print(f"模型緩存路徑：{cache_path}")
    print(f"生成圖片儲存路徑：{output_path}")

    # 🚀 優化：在伺服器啟動時就預載入模型
    print("\n===================================")
    print("正在預載入模型...")
    print("===================================")
    initialize_model()
    print("✅ 模型已就緒！可以開始生成圖片了\n")

    print("正在啟動 Flask 伺服器...")
    print(f"請在瀏覽器開啟: http://localhost:{config.PORT}")
    print("===================================\n")

    # 關閉 reloader 避免生成過程中重新載入
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT,
        use_reloader=config.USE_RELOADER
    )
