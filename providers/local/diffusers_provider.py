"""
Diffusers Provider - 本地端 HuggingFace / diffusers 模型 Provider

支援任何可透過 diffusers Pipeline 載入的模型，
包括 Z-Image-Turbo、SDXL、Flux 等。
"""
import os
import time
import random
from typing import Optional
from io import BytesIO
import base64

from providers.base import BaseProvider
import config


class DiffusersProvider(BaseProvider):
    """本地端 HuggingFace diffusers 模型 Provider"""

    def __init__(self, model_config: dict):
        """
        Args:
            model_config: 模型設定字典，包含 model_id, pipeline_class 等
        """
        self._model_config = model_config
        self._pipeline = None
        self._is_loading = False
        self._loading_name = None

    # ── 識別 ──────────────────────────────────────────────────
    @property
    def provider_type(self) -> str:
        return 'local'

    @property
    def provider_id(self) -> str:
        return 'local'

    # ── 狀態 ──────────────────────────────────────────────────
    def is_configured(self) -> bool:
        return self._pipeline is not None

    def is_loading(self) -> bool:
        return self._is_loading

    def get_loading_name(self) -> Optional[str]:
        return self._loading_name

    def is_cached(self) -> bool:
        """檢查模型是否在本地已快取"""
        model_id = self._model_config.get('model_id', '')
        model_folder_name = "models--" + model_id.replace("/", "--")
        expected_path = os.path.join(config.CACHE_PATH, model_folder_name)
        return os.path.exists(expected_path)

    def get_status(self) -> dict:
        if self._is_loading:
            return {
                'ready': False,
                'message': f'模型 {self._loading_name} 載入中，請稍候…',
                'requires': 'wait',
            }
        if self._pipeline is not None:
            return {
                'ready': True,
                'message': f'模型就緒 · {self._model_config.get("default_steps", "?")} 步 · {self._model_config.get("vram_requirement", "?")}',
                'requires': None,
            }
        cached = self.is_cached()
        return {
            'ready': False,
            'message': '尚未載入' if cached else '需要下載模型',
            'requires': 'model_load',
        }

    # ── 能力 ──────────────────────────────────────────────────
    def supports_img2img(self) -> bool:
        return self._model_config.get('supports_img2img', False)

    # ── 模型載入 / 卸載 ───────────────────────────────────────
    def load(self) -> dict:
        """載入模型到記憶體"""
        if self._pipeline is not None:
            return {'success': True, 'message': f'{self._model_config["name"]} 已在使用中'}
        if self._is_loading:
            return {'success': False, 'error': f'{self._loading_name} 正在載入中，請稍候'}

        self._is_loading = True
        self._loading_name = self._model_config.get('name', '未知模型')
        try:
            start_time = time.time()
            self._pipeline = self._load_pipeline()
            elapsed = time.time() - start_time
            return {
                'success': True,
                'message': f'{self._model_config["name"]} 已載入 (耗時 {elapsed:.1f}秒)',
                'load_time': elapsed,
            }
        except Exception as e:
            print(f"[!] 載入模型失敗: {e}")
            return {'success': False, 'error': f'載入模型失敗: {str(e)}'}
        finally:
            self._is_loading = False
            self._loading_name = None

    def unload(self):
        """卸載模型釋放 VRAM"""
        if self._pipeline is not None:
            try:
                import torch
                del self._pipeline
                self._pipeline = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                print(f"[OK] 已卸載模型: {self._model_config.get('name')}")
            except Exception as e:
                print(f"[!] 卸載模型時發生錯誤: {e}")

    def _load_pipeline(self):
        """內部：載入 diffusers pipeline"""
        import torch
        model_id = self._model_config['model_id']
        pipeline_class_name = self._model_config['pipeline_class']

        # 動態載入 pipeline 類別
        import diffusers
        pipeline_cls = getattr(diffusers, pipeline_class_name, None)
        if pipeline_cls is None:
            raise ValueError(f"不支援的 pipeline 類別: {pipeline_class_name}")

        # 離線 / 線上模式
        model_folder_name = "models--" + model_id.replace("/", "--")
        expected_path = os.path.join(config.CACHE_PATH, model_folder_name)
        use_offline = os.path.exists(expected_path)

        if use_offline:
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["DIFFUSERS_OFFLINE"] = "1"
            print(f"[OK] 使用本地快取離線載入: {self._model_config['name']}")
        else:
            for key in ["HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "DIFFUSERS_OFFLINE"]:
                os.environ.pop(key, None)
            print(f"[*] 從 HuggingFace 下載模型: {self._model_config['name']}…")

        pipe = pipeline_cls.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            cache_dir=config.CACHE_PATH,
            use_safetensors=True,
            local_files_only=use_offline,
        )
        self._apply_optimizations(pipe)
        return pipe

    def _apply_optimizations(self, pipe):
        """套用 VRAM 優化"""
        if config.CPU_OFFLOAD_MODE == "sequential":
            pipe.enable_sequential_cpu_offload()
        elif config.CPU_OFFLOAD_MODE == "model":
            pipe.enable_model_cpu_offload()
        if config.ENABLE_ATTENTION_SLICING and hasattr(pipe, 'enable_attention_slicing'):
            try:
                pipe.enable_attention_slicing("auto")
            except Exception:
                pass
        if config.ENABLE_VAE_SLICING and hasattr(pipe, 'enable_vae_slicing'):
            try:
                pipe.enable_vae_slicing()
            except Exception:
                pass
        if hasattr(pipe, 'enable_vae_tiling'):
            try:
                pipe.enable_vae_tiling()
            except Exception:
                pass

    # ── 生成 ──────────────────────────────────────────────────
    def generate(self, prompt: str, width: int, height: int,
                 negative_prompt: Optional[str] = None,
                 seed: Optional[int] = None,
                 steps: Optional[int] = None,
                 guidance_scale: Optional[float] = None,
                 **kwargs) -> dict:
        if self._pipeline is None:
            return {'success': False, 'error': '尚未載入模型，請先點擊「載入模型」'}

        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            if seed is None:
                seed = random.randint(0, 2 ** 32 - 1)

            device = "cuda" if torch.cuda.is_available() else "cpu"
            generator = torch.Generator(device=device).manual_seed(seed)

            _steps = steps or self._model_config.get('default_steps', config.NUM_INFERENCE_STEPS)
            _guidance = guidance_scale or self._model_config.get('default_guidance_scale', config.GUIDANCE_SCALE)

            gen_kwargs = {
                'prompt': prompt,
                'height': height,
                'width': width,
                'num_inference_steps': _steps,
                'guidance_scale': _guidance,
                'generator': generator,
            }
            if negative_prompt and self._model_config.get('supports_negative_prompt', True):
                gen_kwargs['negative_prompt'] = negative_prompt

            image = self._pipeline(**gen_kwargs).images[0]

            # 轉 base64
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()

            return {
                'success': True,
                'base64': img_b64,
                'mime_type': 'image/png',
                'seed': seed,
                'pil_image': image,  # 留給 route 儲存檔案用
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_model_info(self) -> dict:
        info = super().get_model_info()
        info.update({
            'name': self._model_config.get('name', ''),
            'description': self._model_config.get('description', ''),
            'is_cached': self.is_cached(),
            'is_loaded': self._pipeline is not None,
            'is_loading': self._is_loading,
            'vram_requirement': self._model_config.get('vram_requirement', ''),
            'default_steps': self._model_config.get('default_steps', 20),
        })
        return info
