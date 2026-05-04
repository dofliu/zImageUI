"""
Model Registry Service v4.0 - 多 Provider 模型管理系統

架構說明：
  - LOCAL_MODELS  : 本地 HuggingFace diffusers 模型清單
  - CLOUD_MODELS  : 雲端 API 模型清單（Gemini / OpenAI …）
  - ModelRegistry : 統一管理所有模型，對外提供 generate() / generate_b64() / edit_photo()

新增模型：
  - 本地模型 → 在 LOCAL_MODELS 加一筆設定
  - 雲端模型 → 在 CLOUD_MODELS 加一筆設定，或直接在對應 Provider 檔案加入
  不需要動其他地方。
"""
import os
import json
import base64
from typing import Optional
import config
from providers.local.diffusers_provider import DiffusersProvider
from providers.cloud.gemini_provider import GeminiProvider
from providers.cloud.openai_provider import OpenAIProvider


# ── 本地模型清單 ─────────────────────────────────────────────────
LOCAL_MODELS = [
    {
        "id": "z-image-turbo",
        "name": "Z-Image-Turbo",
        "description": "高速生成，5-8 秒出圖，適合快速迭代",
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
        "status": "available",
    },
    # ── 未來加入本地模型只需在這裡添加一筆 ──
]

# ── 雲端模型清單 ─────────────────────────────────────────────────
CLOUD_MODELS = [
    {
        "id": "gemini-flash-image",
        "name": "Nano Banana（2.5 Flash）",
        "description": "Gemini 2.5 Flash Image，支援照片編輯、大頭照、動漫等所有 Avatar 功能",
        "provider": "gemini",
        "model_id": "gemini-2.5-flash-image",
        "tags": ["cloud", "photo-editing", "avatar", "gemini"],
        "requires_api_key": True,
    },
    {
        "id": "gemini-nano-banana2",
        "name": "Nano Banana 2（3.1 Flash）",
        "description": "Gemini 3.1 Flash Image Preview，速度與大量使用優化，支援全部 Avatar 功能",
        "provider": "gemini",
        "model_id": "gemini-3.1-flash-image-preview",
        "tags": ["cloud", "photo-editing", "avatar", "gemini"],
        "requires_api_key": True,
    },
    {
        "id": "gemini-nano-banana-pro",
        "name": "Nano Banana Pro（3 Pro）",
        "description": "Gemini 3 Pro Image Preview，進階推論、高保真文字，支援全部 Avatar 功能",
        "provider": "gemini",
        "model_id": "gemini-3-pro-image-preview",
        "tags": ["cloud", "photo-editing", "avatar", "gemini"],
        "requires_api_key": True,
    },
    {
        "id": "gemini-imagen4",
        "name": "Imagen 4.0",
        "description": "Google Imagen 高品質生圖，適合 Logo 設計與精細圖像",
        "provider": "gemini",
        "model_id": "imagen-4.0-generate-001",
        "tags": ["cloud", "logo", "gemini"],
        "requires_api_key": True,
    },
    {
        "id": "gpt-image-1",
        "name": "GPT Image 1",
        "description": "OpenAI 雲端圖片生成，支援圖片編輯與 Avatar 功能",
        "provider": "openai",
        "model_id": "gpt-image-1",
        "tags": ["cloud", "avatar", "openai"],
        "requires_api_key": True,
    },
    {
        "id": "dall-e-3",
        "name": "DALL-E 3",
        "description": "OpenAI 高品質文字生圖",
        "provider": "openai",
        "model_id": "dall-e-3",
        "tags": ["cloud", "openai"],
        "requires_api_key": True,
    },
    # ── 未來加入雲端模型只需在這裡添加一筆 ──
]


class ModelRegistry:
    """統一模型管理（本地 + 雲端 Provider）"""

    def __init__(self):
        self._local_providers: dict = {}   # model_id -> DiffusersProvider
        self._gemini_providers: dict = {}  # model_id -> GeminiProvider
        self._openai_providers: dict = {}  # model_id -> OpenAIProvider
        self._active_model_id: Optional[str] = None
        self._custom_models_file = os.path.join(config.OUTPUT_PATH, "custom_models.json")

        self._init_local_providers()
        self._init_cloud_providers()
        self._load_custom_models()
        self._sync_api_keys()

    # ── 初始化 ─────────────────────────────────────────────────
    def _init_local_providers(self):
        for cfg in LOCAL_MODELS:
            self._local_providers[cfg['id']] = DiffusersProvider(cfg)

    def _init_cloud_providers(self):
        for cfg in CLOUD_MODELS:
            pid = cfg['provider']
            mid = cfg['id']
            if pid == 'gemini':
                self._gemini_providers[mid] = GeminiProvider(cfg['model_id'])
            elif pid == 'openai':
                self._openai_providers[mid] = OpenAIProvider(cfg['model_id'])

    def _sync_api_keys(self):
        try:
            from services.provider_settings_service import get_provider_settings
            settings = get_provider_settings()
            gemini_key = settings.get_api_key('gemini')
            openai_key = settings.get_api_key('openai')
            if gemini_key:
                for p in self._gemini_providers.values():
                    p.set_api_key(gemini_key)
            if openai_key:
                for p in self._openai_providers.values():
                    p.set_api_key(openai_key)
        except Exception as e:
            print(f"[!] 同步 API Key 失敗: {e}")

    def reload_api_keys(self):
        """API Key 更新後呼叫此方法"""
        self._sync_api_keys()

    # ── 自訂本地模型 ────────────────────────────────────────────
    def _load_custom_models(self):
        if not os.path.exists(self._custom_models_file):
            return
        try:
            with open(self._custom_models_file, 'r', encoding='utf-8') as f:
                custom_models = json.load(f)
            builtin_ids = {m['id'] for m in LOCAL_MODELS}
            for cfg in custom_models:
                if cfg['id'] not in builtin_ids and cfg['id'] not in self._local_providers:
                    cfg['is_custom'] = True
                    self._local_providers[cfg['id']] = DiffusersProvider(cfg)
        except Exception as e:
            print(f"[!] 載入自訂模型失敗: {e}")

    def _save_custom_models(self):
        builtin_ids = {m['id'] for m in LOCAL_MODELS}
        custom = [p._model_config for mid, p in self._local_providers.items()
                  if mid not in builtin_ids]
        try:
            os.makedirs(os.path.dirname(self._custom_models_file), exist_ok=True)
            with open(self._custom_models_file, 'w', encoding='utf-8') as f:
                json.dump(custom, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[!] 儲存自訂模型失敗: {e}")

    # ── 查詢 ───────────────────────────────────────────────────
    def list_models(self) -> list:
        result = []
        for mid, p in self._local_providers.items():
            cfg = p._model_config
            result.append({
                'id': mid,
                'name': cfg.get('name', mid),
                'description': cfg.get('description', ''),
                'provider_type': 'local',
                'provider': 'local',
                'is_active': mid == self._active_model_id,
                'is_loaded': p.is_configured(),
                'is_loading': p.is_loading(),
                'is_cached': p.is_cached(),
                'is_custom': cfg.get('is_custom', False),
                'vram_requirement': cfg.get('vram_requirement', ''),
                'default_steps': cfg.get('default_steps', 20),
                'tags': cfg.get('tags', []),
                'status': p.get_status(),
            })

        for cfg in CLOUD_MODELS:
            mid = cfg['id']
            provider = self._get_cloud_provider(mid, cfg['provider'])
            if provider:
                s = provider.get_status()
                result.append({
                    'id': mid,
                    'name': cfg['name'],
                    'description': cfg['description'],
                    'provider_type': 'cloud',
                    'provider': cfg['provider'],
                    'is_active': mid == self._active_model_id,
                    'is_loaded': s['ready'],
                    'is_loading': False,
                    'is_cached': True,
                    'is_custom': False,
                    'requires_api_key': cfg.get('requires_api_key', True),
                    'tags': cfg.get('tags', []),
                    'status': s,
                })
        return result

    def get_model_info(self, model_id: str) -> Optional[dict]:
        return next((m for m in self.list_models() if m['id'] == model_id), None)

    def get_active_model(self) -> Optional[dict]:
        if self._active_model_id:
            return self.get_model_info(self._active_model_id)
        return None

    # ── 舊版相容屬性 ────────────────────────────────────────────
    @property
    def active_model_id(self):
        return self._active_model_id

    @property
    def active_pipeline(self):
        if self._active_model_id and self._active_model_id in self._local_providers:
            return self._local_providers[self._active_model_id]._pipeline
        return None

    @property
    def is_loading(self):
        if self._active_model_id and self._active_model_id in self._local_providers:
            return self._local_providers[self._active_model_id].is_loading()
        return False

    @property
    def loading_model_name(self):
        if self._active_model_id and self._active_model_id in self._local_providers:
            return self._local_providers[self._active_model_id].get_loading_name()
        return None

    @property
    def models(self) -> dict:
        return {m['id']: m for m in self.list_models()}

    # ── 切換模型 ────────────────────────────────────────────────
    def switch_model(self, model_id: str) -> dict:
        if model_id in self._local_providers:
            provider = self._local_providers[model_id]
            if provider.is_configured():
                self._active_model_id = model_id
                return {'success': True, 'message': f'{provider._model_config["name"]} 已在使用中',
                        'model': self.get_model_info(model_id)}
            result = provider.load()
            if result['success']:
                for oid, op in self._local_providers.items():
                    if oid != model_id and op.is_configured():
                        op.unload()
                self._active_model_id = model_id
                result['model'] = self.get_model_info(model_id)
            return result

        cloud_cfg = next((c for c in CLOUD_MODELS if c['id'] == model_id), None)
        if cloud_cfg:
            provider = self._get_cloud_provider(model_id, cloud_cfg['provider'])
            if not provider:
                return {'success': False, 'error': f'找不到 Provider: {cloud_cfg["provider"]}'}
            if not provider.is_configured():
                return {
                    'success': False,
                    'error': f'請先在設定中填入 {cloud_cfg["provider"].upper()} API Key',
                    'requires': 'api_key',
                    'provider': cloud_cfg['provider'],
                }
            self._active_model_id = model_id
            return {'success': True, 'message': f'{cloud_cfg["name"]} 已設為使用中',
                    'model': self.get_model_info(model_id)}

        return {'success': False, 'error': f'未知模型: {model_id}'}

    def _get_cloud_provider(self, model_id: str, provider_id: str):
        if provider_id == 'gemini':
            return self._gemini_providers.get(model_id)
        if provider_id == 'openai':
            return self._openai_providers.get(model_id)
        return None

    def _get_active_provider(self):
        if not self._active_model_id:
            return None
        if self._active_model_id in self._local_providers:
            return self._local_providers[self._active_model_id]
        cloud_cfg = next((c for c in CLOUD_MODELS if c['id'] == self._active_model_id), None)
        if cloud_cfg:
            return self._get_cloud_provider(self._active_model_id, cloud_cfg['provider'])
        return None

    # ── 生成（統一） ─────────────────────────────────────────────
    def generate(self, prompt: str, width: int, height: int,
                 seed=None, negative_prompt=None, **kwargs):
        """
        向後相容介面（routes/generate.py 使用）
        本地模型 → 回傳 (PIL.Image, seed)
        雲端模型 → 回傳 (base64_str, seed)
        """
        provider = self._get_active_provider()
        if provider is None:
            raise RuntimeError("尚未載入任何模型")
        result = provider.generate(prompt=prompt, width=width, height=height,
                                   seed=seed, negative_prompt=negative_prompt, **kwargs)
        if not result.get('success'):
            raise RuntimeError(result.get('error', '生成失敗'))
        if 'pil_image' in result:
            return result['pil_image'], result['seed']
        return result['base64'], result['seed']

    def generate_b64(self, prompt: str, width: int, height: int,
                     seed=None, negative_prompt=None, **kwargs) -> dict:
        """新版統一介面，總是回傳 base64"""
        provider = self._get_active_provider()
        if provider is None:
            return {'success': False, 'error': '尚未選擇模型'}
        result = provider.generate(prompt=prompt, width=width, height=height,
                                   seed=seed, negative_prompt=negative_prompt, **kwargs)
        if result.get('success') and 'pil_image' in result:
            from io import BytesIO
            buf = BytesIO()
            result['pil_image'].save(buf, format='PNG')
            result['base64'] = base64.b64encode(buf.getvalue()).decode()
            result['mime_type'] = 'image/png'
        return result

    # ── Avatar Studio ────────────────────────────────────────────
    def edit_photo(self, feature: str, image_base64: str,
                   image2_base64=None, mask_base64=None,
                   image_mime='image/jpeg', image2_mime='image/jpeg',
                   params=None) -> dict:
        provider = self._get_active_provider()
        if provider is None:
            return {'success': False, 'error': '請先選擇一個模型'}
        if not hasattr(provider, 'edit_photo'):
            return {'success': False, 'error': f'{self._active_model_id} 不支援照片編輯，請切換到雲端模型'}
        return provider.edit_photo(feature=feature, image_base64=image_base64,
                                   image2_base64=image2_base64, mask_base64=mask_base64,
                                   image_mime=image_mime, image2_mime=image2_mime,
                                   params=params)

    # ── 自訂模型管理 ────────────────────────────────────────────
    def register_custom_model(self, model_config: dict) -> dict:
        for field in ['id', 'name', 'model_id', 'pipeline_class']:
            if field not in model_config:
                return {'success': False, 'error': f'缺少必要欄位: {field}'}
        model_config.setdefault('description', '自訂模型')
        model_config.setdefault('default_steps', 20)
        model_config.setdefault('default_guidance_scale', 7.5)
        model_config.setdefault('supports_negative_prompt', True)
        model_config.setdefault('supports_img2img', False)
        model_config.setdefault('vram_requirement', '未知')
        model_config.setdefault('tags', ['custom'])
        model_config['is_custom'] = True
        self._local_providers[model_config['id']] = DiffusersProvider(model_config)
        self._save_custom_models()
        return {'success': True, 'message': f'已註冊: {model_config["name"]}'}

    def remove_custom_model(self, model_id: str) -> dict:
        builtin_ids = {m['id'] for m in LOCAL_MODELS}
        if model_id not in self._local_providers:
            return {'success': False, 'error': '模型不存在'}
        if model_id in {m['id'] for m in LOCAL_MODELS}:
            return {'success': False, 'error': '不能移除內建模型'}
        if model_id == self._active_model_id:
            self._local_providers[model_id].unload()
            self._active_model_id = None
        del self._local_providers[model_id]
        self._save_custom_models()
        return {'success': True, 'message': '已移除自訂模型'}

    @property
    def models(self) -> dict:
        """舊版相容：回傳 {model_id: model_info} 字典"""
        return {m['id']: m for m in self.list_models()}


# ── 全域單例 ─────────────────────────────────────────────────────
_model_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry
