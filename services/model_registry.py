"""
Model Registry Service - 多模型管理與切換系統
支援動態註冊、切換和管理多個 AI 圖片生成模型
"""
import os
import json
import time
import config


# 預設模型清單 - 只載入本地已安裝的模型
DEFAULT_MODELS = [
    {
        "id": "z-image-turbo",
        "name": "Z-Image-Turbo",
        "description": "高速生成，5-8秒出圖，適合快速迭代",
        "model_id": "Tongyi-MAI/Z-Image-Turbo",
        "pipeline_class": "ZImagePipeline",
        "default_steps": 9,
        "default_guidance_scale": 0.0,
        "supports_negative_prompt": True,
        "supports_img2img": False,
        "min_resolution": 512,
        "max_resolution": 2048,
        "recommended_resolution": 768,
        "vram_requirement": "8-12GB",
        "tags": ["turbo", "fast", "general"],
        "status": "available"
    }
]


class ModelRegistry:
    """模型註冊表 - 管理所有可用的圖片生成模型"""

    def __init__(self):
        self.models = {}
        self.active_model_id = None
        self.active_pipeline = None
        self.is_loading = False  # 模型載入中狀態
        self.loading_model_name = None
        self.custom_models_file = os.path.join(config.OUTPUT_PATH, "custom_models.json")
        self._load_default_models()
        self._load_custom_models()

    def _load_default_models(self):
        """載入預設模型清單"""
        for model_config in DEFAULT_MODELS:
            self.models[model_config["id"]] = {
                **model_config,
                "is_cached": self._check_model_cached(model_config["model_id"]),
                "is_custom": False
            }

    def _load_custom_models(self):
        """載入使用者自訂模型（跳過與內建模型重複的項目）"""
        if os.path.exists(self.custom_models_file):
            try:
                with open(self.custom_models_file, 'r', encoding='utf-8') as f:
                    custom_models = json.load(f)
                default_ids = {m["id"] for m in DEFAULT_MODELS}
                for model_config in custom_models:
                    # 跳過與內建模型 ID 衝突的自訂模型
                    if model_config["id"] in default_ids:
                        continue
                    model_config["is_custom"] = True
                    model_config["is_cached"] = self._check_model_cached(model_config["model_id"])
                    self.models[model_config["id"]] = model_config
            except Exception as e:
                print(f"載入自訂模型失敗: {e}")

    def _check_model_cached(self, model_id):
        """檢查模型是否已在本地快取"""
        model_folder_name = "models--" + model_id.replace("/", "--")
        expected_path = os.path.join(config.CACHE_PATH, model_folder_name)
        return os.path.exists(expected_path)

    def list_models(self):
        """列出所有可用模型"""
        result = []
        for model_id, model_info in self.models.items():
            # 每次查詢時更新快取狀態
            model_info["is_cached"] = self._check_model_cached(model_info["model_id"])
            model_info["is_active"] = (model_id == self.active_model_id)
            result.append(model_info)
        return result

    def get_model_info(self, model_id):
        """取得特定模型資訊"""
        return self.models.get(model_id)

    def get_active_model(self):
        """取得目前啟用的模型資訊"""
        if self.active_model_id:
            return self.models.get(self.active_model_id)
        return None

    def switch_model(self, model_id):
        """切換到指定模型

        Returns:
            dict: 切換結果
        """
        if model_id not in self.models:
            return {"success": False, "error": f"未知的模型: {model_id}"}

        model_info = self.models[model_id]

        # 如果是同一個模型，不需要重新載入
        if model_id == self.active_model_id and self.active_pipeline is not None:
            return {
                "success": True,
                "message": f"模型 {model_info['name']} 已在使用中",
                "model": model_info
            }

        # 如果正在載入中，拒絕切換
        if self.is_loading:
            return {"success": False, "error": f"模型 {self.loading_model_name} 正在載入中，請稍候"}

        # 載入新模型（先載入，成功後才卸載舊模型）
        self.is_loading = True
        self.loading_model_name = model_info['name']
        try:
            start_time = time.time()
            pipeline = self._load_model(model_info)
            elapsed = time.time() - start_time

            # 新模型載入成功，安全卸載舊模型
            old_pipeline = self.active_pipeline
            self.active_pipeline = pipeline
            self.active_model_id = model_id

            if old_pipeline is not None:
                import torch
                del old_pipeline
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                print(f"[OK] 已卸載舊模型")

            return {
                "success": True,
                "message": f"模型 {model_info['name']} 已載入 (耗時 {elapsed:.1f}秒)",
                "model": model_info,
                "load_time": elapsed
            }
        except Exception as e:
            # 載入失敗，舊模型保持不動
            print(f"[!] 載入模型 {model_info['name']} 失敗: {e}")
            return {"success": False, "error": f"載入模型失敗: {str(e)}"}
        finally:
            self.is_loading = False
            self.loading_model_name = None

    def _load_model(self, model_info):
        """載入指定模型"""
        import torch

        model_id = model_info["model_id"]
        pipeline_class_name = model_info["pipeline_class"]

        # 動態載入 pipeline 類別
        pipeline_class = self._get_pipeline_class(pipeline_class_name)

        # 檢查是否有本地快取
        model_folder_name = "models--" + model_id.replace("/", "--")
        expected_path = os.path.join(config.CACHE_PATH, model_folder_name)
        use_offline = os.path.exists(expected_path)

        if use_offline:
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["DIFFUSERS_OFFLINE"] = "1"
            print(f"[OK] 發現本地快取，使用離線模式載入 {model_info['name']}")
        else:
            # 清除離線模式環境變數
            for key in ["HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "DIFFUSERS_OFFLINE"]:
                os.environ.pop(key, None)
            print(f"[*] 從 Hugging Face 下載模型 {model_info['name']}...")

        pipe = pipeline_class.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            cache_dir=config.CACHE_PATH,
            use_safetensors=True,
            local_files_only=use_offline,
        )

        # 套用 VRAM 優化
        self._apply_optimizations(pipe)

        return pipe

    def _get_pipeline_class(self, class_name):
        """動態取得 pipeline 類別"""
        import diffusers
        pipeline_cls = getattr(diffusers, class_name, None)
        if pipeline_cls is None:
            raise ValueError(f"不支援的 pipeline 類別: {class_name}")
        return pipeline_cls

    def _apply_optimizations(self, pipe):
        """套用 VRAM 優化設定"""
        # Sequential CPU Offload
        if config.CPU_OFFLOAD_MODE == "sequential":
            pipe.enable_sequential_cpu_offload()
            print("[OK] 已啟用 Sequential CPU Offload")
        elif config.CPU_OFFLOAD_MODE == "model":
            pipe.enable_model_cpu_offload()
            print("[OK] 已啟用 Model CPU Offload")

        # Attention Slicing
        if config.ENABLE_ATTENTION_SLICING and hasattr(pipe, 'enable_attention_slicing'):
            try:
                pipe.enable_attention_slicing("auto")
            except Exception:
                pass

        # VAE Slicing
        if config.ENABLE_VAE_SLICING and hasattr(pipe, 'enable_vae_slicing'):
            try:
                pipe.enable_vae_slicing()
            except Exception:
                pass

        # VAE Tiling
        if hasattr(pipe, 'enable_vae_tiling'):
            try:
                pipe.enable_vae_tiling()
            except Exception:
                pass

    def _unload_current_model(self):
        """卸載目前載入的模型"""
        import torch
        if self.active_pipeline is not None:
            del self.active_pipeline
            self.active_pipeline = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print(f"[OK] 已卸載模型: {self.active_model_id}")

    def generate(self, prompt, width, height, seed=None, negative_prompt=None):
        """使用目前啟用的模型生成圖片"""
        import torch
        import random

        if self.active_pipeline is None:
            raise RuntimeError("尚未載入任何模型，請先選擇並載入一個模型")

        model_info = self.models[self.active_model_id]

        # 清理 GPU 快取
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # 隨機種子
        if seed is None:
            seed = random.randint(0, 2**32 - 1)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        generator = torch.Generator(device=device).manual_seed(seed)

        generate_kwargs = {
            'prompt': prompt,
            'height': height,
            'width': width,
            'num_inference_steps': model_info.get('default_steps', config.NUM_INFERENCE_STEPS),
            'guidance_scale': model_info.get('default_guidance_scale', config.GUIDANCE_SCALE),
            'generator': generator,
        }

        # 僅在模型支援時添加負面提示詞
        if negative_prompt and model_info.get('supports_negative_prompt', True):
            generate_kwargs['negative_prompt'] = negative_prompt

        print(f"[{model_info['name']}] 生成: {prompt}")
        print(f"  解析度: {width}x{height}, 種子: {seed}, 步數: {generate_kwargs['num_inference_steps']}")

        image = self.active_pipeline(**generate_kwargs).images[0]
        return image, seed

    def register_custom_model(self, model_config):
        """註冊自訂模型"""
        required_fields = ["id", "name", "model_id", "pipeline_class"]
        for field in required_fields:
            if field not in model_config:
                return {"success": False, "error": f"缺少必要欄位: {field}"}

        model_config.setdefault("description", "自訂模型")
        model_config.setdefault("default_steps", 20)
        model_config.setdefault("default_guidance_scale", 7.5)
        model_config.setdefault("supports_negative_prompt", True)
        model_config.setdefault("supports_img2img", False)
        model_config.setdefault("min_resolution", 512)
        model_config.setdefault("max_resolution", 2048)
        model_config.setdefault("recommended_resolution", 768)
        model_config.setdefault("vram_requirement", "未知")
        model_config.setdefault("tags", ["custom"])
        model_config.setdefault("status", "available")
        model_config["is_custom"] = True
        model_config["is_cached"] = self._check_model_cached(model_config["model_id"])

        self.models[model_config["id"]] = model_config
        self._save_custom_models()
        return {"success": True, "message": f"已註冊自訂模型: {model_config['name']}"}

    def remove_custom_model(self, model_id):
        """移除自訂模型"""
        if model_id not in self.models:
            return {"success": False, "error": "模型不存在"}
        if not self.models[model_id].get("is_custom", False):
            return {"success": False, "error": "不能移除內建模型"}
        if model_id == self.active_model_id:
            self._unload_current_model()
            self.active_model_id = None

        del self.models[model_id]
        self._save_custom_models()
        return {"success": True, "message": "已移除自訂模型"}

    def _save_custom_models(self):
        """儲存自訂模型到檔案"""
        custom_models = [
            {k: v for k, v in m.items() if k not in ("is_cached", "is_active")}
            for m in self.models.values()
            if m.get("is_custom", False)
        ]
        try:
            os.makedirs(os.path.dirname(self.custom_models_file), exist_ok=True)
            with open(self.custom_models_file, 'w', encoding='utf-8') as f:
                json.dump(custom_models, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存自訂模型失敗: {e}")


# 全域單例
_model_registry = None


def get_model_registry():
    """取得模型註冊表單例"""
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry
