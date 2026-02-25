"""
Model Service - AI 模型管理服務
"""
import torch
import os
import time
from diffusers import ZImagePipeline
import config


class ModelService:
    """AI 模型管理類"""
    
    def __init__(self):
        self.pipe = None
        self.cache_path = config.CACHE_PATH
        os.makedirs(self.cache_path, exist_ok=True)
    
    def initialize_model(self):
        """初始化模型 (只執行一次)"""
        if self.pipe is None:
            model_id = "Tongyi-MAI/Z-Image-Turbo"
            model_folder_name = "models--" + model_id.replace("/", "--")
            
            # 優先檢查給定的或預設的快取路徑
            expected_model_path = os.path.join(self.cache_path, model_folder_name)
            
            # 自動檢測是否使用離線模式
            use_offline_mode = False
            model_load_path = model_id # 預設使用 ID 下載
            
            model_cache_exists = os.path.exists(expected_model_path)
            
            if model_cache_exists:
                print(f"[OK] 發現本地快取 ({expected_model_path})，自動啟用離線模式...")
                use_offline_mode = True
            else:
                print(f"\n[!] 警告：未在 {self.cache_path} 發現模型快取。")
                print("為避免不必要的網路下載或等待，請選擇接下來的操作：")
                print("1. 允許連線下載 (將從 Hugging Face 下載多 GB 的模型，可能需要很久)")
                print("2. 輸入我已經下載好的模型完整路徑 (例如: D:\\AI_Cache\\HuggingFace\\models--Tongyi-MAI--Z-Image-Turbo)")
                print("3. 退出程式")
                
                choice = input("\n請輸入 1, 2 或 3: ").strip()
                
                if choice == '1':
                    print("[*] 選擇連線下載，將嘗試從 Hugging Face 獲取...")
                    use_offline_mode = False
                elif choice == '2':
                    custom_path = input("請輸入模型的完整資料夾路徑: ").strip()
                    if os.path.exists(custom_path):
                        print(f"[OK] 確認路徑存在，將從 {custom_path} 載入模型...")
                        model_load_path = custom_path
                        # 如果使用者提供的是絕對路徑，我們就當作 offline 處理
                        use_offline_mode = True 
                    else:
                        print(f"[!] 錯誤：路徑 {custom_path} 不存在。程式即將退出。")
                        exit(1)
                else:
                    print("程式已退出。")
                    exit(0)

            # 離線模式的環境變數設定
            if use_offline_mode:
                os.environ["HF_HUB_OFFLINE"] = "1"
                os.environ["TRANSFORMERS_OFFLINE"] = "1"
                os.environ["DIFFUSERS_OFFLINE"] = "1"

            start_time = time.time()

            # 載入模型
            self.pipe = ZImagePipeline.from_pretrained(
                model_load_path,
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
                cache_dir=self.cache_path,
                use_safetensors=True,
                local_files_only=use_offline_mode,
            )

            # 針對 12GB VRAM 的優化設定
            print("[*] 啟用 Sequential CPU Offload (更激進的顯存優化)...")
            self.pipe.enable_sequential_cpu_offload()
            
            # 啟用額外的 VRAM 優化
            optimizations = []

            if config.ENABLE_ATTENTION_SLICING:
                if hasattr(self.pipe, 'enable_attention_slicing'):
                    try:
                        self.pipe.enable_attention_slicing("auto")
                        optimizations.append("Attention Slicing")
                    except Exception as e:
                        print(f"! Attention Slicing 啟用失敗: {e}")

            if config.ENABLE_VAE_SLICING:
                if hasattr(self.pipe, 'enable_vae_slicing'):
                    try:
                        self.pipe.enable_vae_slicing()
                        optimizations.append("VAE Slicing")
                    except Exception as e:
                        print(f"! VAE Slicing 啟用失敗: {e}")

            if config.ENABLE_XFORMERS:
                if hasattr(self.pipe, 'enable_xformers_memory_efficient_attention'):
                    try:
                        self.pipe.enable_xformers_memory_efficient_attention()
                        optimizations.append("xFormers Attention")
                    except Exception as e:
                        print(f"! xFormers 啟用失敗: {e}")

            if optimizations:
                print(f"[OK] 已啟用額外優化: {', '.join(optimizations)}")

            # 嘗試啟用 VAE Tiling
            try:
                if hasattr(self.pipe, 'enable_vae_tiling'):
                    self.pipe.enable_vae_tiling()
                    print("[OK] 已啟用 VAE Tiling (優化高解析度生成)")
                else:
                    print("! ZImagePipeline 不支援 VAE Tiling，跳過此優化")
            except Exception as e:
                print(f"! VAE Tiling 啟用失敗: {e}")

            # 嘗試啟用 Flash Attention 加速
            try:
                if hasattr(self.pipe, 'transformer') and hasattr(self.pipe.transformer, 'set_attention_backend'):
                    self.pipe.transformer.set_attention_backend("flash")
                    print("[OK] 已啟用 Flash Attention 加速")
                else:
                    print("! Flash Attention 不可用，使用預設 Attention")
            except Exception as e:
                print(f"! Flash Attention 啟用失敗: {e}")

            elapsed_time = time.time() - start_time
            print(f"[OK] 模型載入完成! (耗時 {elapsed_time:.1f} 秒)")
        else:
            print("[OK] 模型已在記憶體中,跳過載入")
    
    def generate_image(self, prompt, width, height, seed=None, negative_prompt=None):
        """生成圖片
        
        Args:
            prompt: 提示詞
            width: 圖片寬度
            height: 圖片高度
            seed: 隨機種子 (可選)
            negative_prompt: 負面提示詞 (可選)
            
        Returns:
            tuple: (image, seed)
        """
        # 確保模型已載入
        self.initialize_model()
        
        # 生成前清理 GPU 快取
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("[OK] 已清理 GPU 快取")
        
        # 使用隨機種子
        import random
        if seed is None:
            seed = random.randint(0, 2**32 - 1)
        
        print(f"開始生成：{prompt}")
        if negative_prompt:
            print(f"負面提示詞：{negative_prompt}")
        print(f"使用種子: {seed}")
        print(f"生成解析度: {width}x{height}")
        
        # 生成圖片
        device = "cuda" if torch.cuda.is_available() else "cpu"
        generator = torch.Generator(device=device).manual_seed(seed)
        
        # 準備生成參數
        generate_kwargs = {
            'prompt': prompt,
            'height': height,
            'width': width,
            'num_inference_steps': config.NUM_INFERENCE_STEPS,
            'guidance_scale': config.GUIDANCE_SCALE,
            'generator': generator,
        }
        
        # 添加負面提示詞（如果有）
        if negative_prompt:
            generate_kwargs['negative_prompt'] = negative_prompt
        
        image = self.pipe(**generate_kwargs).images[0]
        
        return image, seed


# 全域模型服務實例
_model_service = None


def get_model_service():
    """獲取模型服務單例"""
    global _model_service
    if _model_service is None:
        _model_service = ModelService()
    return _model_service
