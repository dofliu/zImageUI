"""
OpenAI Provider - GPT Image 生成 Provider

支援模型：
  - gpt-image-1  (文字生圖 / 圖片編輯)
  - dall-e-3     (高品質文字生圖)

新增更新的 OpenAI 模型只需在 OPENAI_MODELS 加入設定即可。
"""
import base64
import random
from typing import Optional
from io import BytesIO

from providers.base import BaseProvider

# ── OpenAI 可用模型設定 ──────────────────────────────────────────
OPENAI_MODELS = {
    'gpt-image-1': {
        'display_name': 'GPT Image 1',
        'supports_image_input': True,
        'supports_edit': True,
        'default_size': '1024x1024',
        'available_sizes': ['1024x1024', '1536x1024', '1024x1536'],
    },
    'dall-e-3': {
        'display_name': 'DALL-E 3',
        'supports_image_input': False,
        'supports_edit': False,
        'default_size': '1024x1024',
        'available_sizes': ['1024x1024', '1792x1024', '1024x1792'],
    },
    'dall-e-2': {
        'display_name': 'DALL-E 2',
        'supports_image_input': True,
        'supports_edit': True,
        'default_size': '1024x1024',
        'available_sizes': ['256x256', '512x512', '1024x1024'],
    },
}


class OpenAIProvider(BaseProvider):
    """OpenAI GPT Image Provider"""

    def __init__(self, model_id: str = 'gpt-image-1'):
        self._model_id = model_id
        self._api_key: Optional[str] = None
        self._model_meta = OPENAI_MODELS.get(model_id, OPENAI_MODELS['gpt-image-1'])

    # ── 識別 ──────────────────────────────────────────────────
    @property
    def provider_type(self) -> str:
        return 'cloud'

    @property
    def provider_id(self) -> str:
        return 'openai'

    # ── API Key ────────────────────────────────────────────────
    def set_api_key(self, api_key: str):
        self._api_key = api_key.strip() if api_key else None

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def get_status(self) -> dict:
        if self.is_configured():
            return {
                'ready': True,
                'message': f'{self._model_meta["display_name"]} · 雲端就緒',
                'requires': None,
            }
        return {
            'ready': False,
            'message': '請在設定中填入 OpenAI API Key',
            'requires': 'api_key',
        }

    # ── 能力 ──────────────────────────────────────────────────
    def supports_img2img(self) -> bool:
        return self._model_meta.get('supports_image_input', False)

    def supports_inpainting(self) -> bool:
        return self._model_meta.get('supports_edit', False)

    def supports_photo_editing(self) -> bool:
        return self._model_meta.get('supports_image_input', False)

    # ── 內部：取得 client ──────────────────────────────────────
    def _get_client(self):
        if not self._api_key:
            raise RuntimeError("OpenAI API Key 未設定，請至設定頁面填入")
        from openai import OpenAI
        return OpenAI(api_key=self._api_key)

    def _best_size(self, width: int, height: int) -> str:
        """選擇最接近的支援尺寸"""
        available = self._model_meta.get('available_sizes', ['1024x1024'])
        default = self._model_meta.get('default_size', '1024x1024')
        # 根據長寬比選擇最接近的
        ratio = width / max(height, 1)
        if ratio > 1.3:
            for s in available:
                w, h = map(int, s.split('x'))
                if w > h:
                    return s
        elif ratio < 0.77:
            for s in available:
                w, h = map(int, s.split('x'))
                if h > w:
                    return s
        return default

    def _response_to_b64(self, response_data) -> str:
        """從 OpenAI 回應提取 base64"""
        image_obj = response_data.data[0]
        if hasattr(image_obj, 'b64_json') and image_obj.b64_json:
            return image_obj.b64_json
        if hasattr(image_obj, 'url') and image_obj.url:
            import urllib.request
            with urllib.request.urlopen(image_obj.url) as resp:
                return base64.b64encode(resp.read()).decode()
        raise ValueError("OpenAI 回應中找不到圖片資料")

    # ── 文字生圖 ───────────────────────────────────────────────
    def generate(self, prompt: str, width: int, height: int,
                 negative_prompt: Optional[str] = None,
                 seed: Optional[int] = None,
                 steps: Optional[int] = None,
                 guidance_scale: Optional[float] = None,
                 **kwargs) -> dict:
        try:
            client = self._get_client()
            size = self._best_size(width, height)

            full_prompt = prompt
            if negative_prompt:
                full_prompt += f". Avoid: {negative_prompt}"

            gen_kwargs = dict(
                model=self._model_id,
                prompt=full_prompt,
                size=size,
                response_format='b64_json',
                n=1,
            )
            # DALL-E 3 支援品質設定
            if self._model_id == 'dall-e-3':
                gen_kwargs['quality'] = 'hd'

            response = client.images.generate(**gen_kwargs)
            b64 = self._response_to_b64(response)
            return {
                'success': True,
                'base64': b64,
                'mime_type': 'image/png',
                'seed': random.randint(0, 2 ** 32 - 1),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ── 圖生圖 ─────────────────────────────────────────────────
    def img2img(self, image_base64: str, prompt: str,
                strength: float = 0.7,
                width: Optional[int] = None,
                height: Optional[int] = None,
                negative_prompt: Optional[str] = None,
                seed: Optional[int] = None,
                mime_type: str = 'image/png',
                **kwargs) -> dict:
        try:
            client = self._get_client()
            size = self._best_size(width or 1024, height or 1024)

            # 轉成 PNG bytes
            img_bytes = base64.b64decode(image_base64)
            img_file = BytesIO(img_bytes)
            img_file.name = 'input.png'

            full_prompt = prompt
            if negative_prompt:
                full_prompt += f". Avoid: {negative_prompt}"

            response = client.images.edit(
                model=self._model_id,
                image=img_file,
                prompt=full_prompt,
                size=size,
                response_format='b64_json',
                n=1,
            )
            b64 = self._response_to_b64(response)
            return {
                'success': True,
                'base64': b64,
                'mime_type': 'image/png',
                'seed': random.randint(0, 2 ** 32 - 1),
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ── Avatar Studio 照片編輯 ─────────────────────────────────
    def edit_photo(self, feature: str, image_base64: str,
                   image2_base64: Optional[str] = None,
                   mask_base64: Optional[str] = None,
                   image_mime: str = 'image/jpeg',
                   image2_mime: str = 'image/jpeg',
                   params: Optional[dict] = None) -> dict:
        """使用 images.edit 實現照片編輯功能"""
        try:
            client = self._get_client()
            params = params or {}
            prompt = self._build_edit_prompt(feature, params)

            img_bytes = base64.b64decode(image_base64)
            img_file = BytesIO(img_bytes)
            img_file.name = 'input.png'

            edit_kwargs = dict(
                model=self._model_id,
                image=img_file,
                prompt=prompt,
                size='1024x1024',
                response_format='b64_json',
                n=1,
            )

            if mask_base64 and self._model_meta.get('supports_edit'):
                mask_bytes = base64.b64decode(mask_base64)
                mask_file = BytesIO(mask_bytes)
                mask_file.name = 'mask.png'
                edit_kwargs['mask'] = mask_file

            response = client.images.edit(**edit_kwargs)
            b64 = self._response_to_b64(response)
            return {'success': True, 'base64': b64, 'mime_type': 'image/png', 'seed': 0}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _build_edit_prompt(self, feature: str, params: dict) -> str:
        """為每個 Avatar Studio 功能建立提示詞"""
        prompts = {
            'professional': lambda p: f"Professional headshot. Background: {p.get('background', 'office')}. Attire: {p.get('attire', 'business suit')}. Soft flattering lighting.",
            'anime': lambda p: f"Transform into {p.get('style', 'Modern Anime')} style avatar while preserving facial likeness.",
            'figure': lambda p: f"Transform into a high-quality 1/7 scale collectible figure product shot. Display: {p.get('figure_base', 'display stand')}.",
            'sticker': lambda p: f"Convert into a cute {p.get('sticker_style', 'chibi')} sticker with white background.",
            'passport': lambda p: "Professional passport/ID photo: white background, even lighting, facing forward, neutral expression.",
            'colorize': lambda p: "Colorize this black and white photograph with natural, realistic colors.",
            'scene': lambda p: f"Replace background with: {p.get('scene_prompt', 'beautiful outdoor scene')}. Keep subject unchanged.",
            'inpaint': lambda p: f"Replace the masked area with: {p.get('inpaint_prompt', 'fill naturally')}.",
            'tryon': lambda p: "Virtual try-on: dress the person with the clothing from the reference, maintaining pose and features.",
            'exploded': lambda p: "Create an exploded view technical illustration showing all components separated.",
            'doodle': lambda p: f"Convert this sketch into a {p.get('doodle_style', 'realistic')} image.",
            'logo': lambda p: f"Professional logo design for '{p.get('brand', '')}'. Style: {p.get('logo_type', 'modern')}. Clean white background.",
            'gif': lambda p: f"Create an animated-style frame: {p.get('gif_prompt', 'dynamic scene')}.",
            'fusion': lambda p: f"Composite photo of two people in scene: {p.get('scene_prompt', 'outdoor')}.",
        }
        builder = prompts.get(feature)
        if builder:
            return builder(params)
        return f"Apply {feature} transformation to this image."

    def get_model_info(self) -> dict:
        info = super().get_model_info()
        info.update({
            'name': self._model_meta.get('display_name', self._model_id),
            'description': f'OpenAI 雲端模型 ({self._model_id})',
            'model_id': self._model_id,
            'available_models': list(OPENAI_MODELS.keys()),
        })
        return info
