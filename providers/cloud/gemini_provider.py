"""
Gemini Provider - Google Gemini API 圖片生成 Provider

支援模型：
  - gemini-2.5-flash-image           (Nano Banana)
  - gemini-3.1-flash-image-preview   (Nano Banana 2)
  - gemini-3-pro-image-preview       (Nano Banana Pro)
  - imagen-4.0-generate-001          (Imagen 4.0, Logo 高品質)

新增更新的 Gemini 模型只需在 GEMINI_MODELS 加入設定即可，
不需要修改任何其他程式碼。
"""
import base64
import random
from typing import Optional

from providers.base import BaseProvider

# ── Gemini 可用模型設定（未來直接加這裡即可）────────────────────
GEMINI_MODELS = {
    'gemini-2.5-flash-image': {
        'display_name': 'Gemini 2.5 Flash Image',
        'supports_image_input': True,
        'supports_image_output': True,
        'use_generate_images': False,
    },
    'gemini-3.1-flash-image-preview': {
        'display_name': 'Gemini 3.1 Flash Image Preview',
        'supports_image_input': True,
        'supports_image_output': True,
        'use_generate_images': False,
    },
    'gemini-3-pro-image-preview': {
        'display_name': 'Gemini 3 Pro Image Preview',
        'supports_image_input': True,
        'supports_image_output': True,
        'use_generate_images': False,
    },
    'gemini-2.0-flash-exp': {
        'display_name': 'Gemini 2.0 Flash (實驗)',
        'supports_image_input': True,
        'supports_image_output': True,
        'use_generate_images': False,
    },
    'imagen-4.0-generate-001': {
        'display_name': 'Imagen 4.0',
        'supports_image_input': False,
        'supports_image_output': True,
        'use_generate_images': True,  # 使用 generateImages API
    },
}


class GeminiProvider(BaseProvider):
    """Google Gemini API Provider"""

    def __init__(self, model_id: str = 'gemini-2.5-flash-image'):
        self._model_id = model_id
        self._api_key: Optional[str] = None
        self._model_meta = GEMINI_MODELS.get(model_id, GEMINI_MODELS['gemini-2.5-flash-image'])

    # ── 識別 ──────────────────────────────────────────────────
    @property
    def provider_type(self) -> str:
        return 'cloud'

    @property
    def provider_id(self) -> str:
        return 'gemini'

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
            'message': '請在設定中填入 Gemini API Key',
            'requires': 'api_key',
        }

    # ── 能力 ──────────────────────────────────────────────────
    def supports_img2img(self) -> bool:
        return self._model_meta.get('supports_image_input', False)

    def supports_inpainting(self) -> bool:
        return self._model_meta.get('supports_image_input', False)

    def supports_photo_editing(self) -> bool:
        return self._model_meta.get('supports_image_input', False)

    # ── 內部：取得 AI client ───────────────────────────────────
    def _get_client(self):
        if not self._api_key:
            raise RuntimeError("Gemini API Key 未設定，請至設定頁面填入")
        from google import genai
        return genai.Client(api_key=self._api_key)

    def _process_response(self, response) -> dict:
        """解析 Gemini generateContent 回應"""
        try:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    return {
                        'success': True,
                        'base64': part.inline_data.data,
                        'mime_type': part.inline_data.mime_type or 'image/png',
                        'seed': random.randint(0, 2 ** 32 - 1),
                    }
            # 模型只回傳文字（通常是拒絕或說明）
            reason = getattr(response.candidates[0], 'finish_reason', 'UNKNOWN')
            text = getattr(response, 'text', '') or ''
            if reason == 'SAFETY':
                return {'success': False, 'error': '圖片內容可能違反安全政策，請修改提示詞'}
            return {'success': False, 'error': f'模型未回傳圖片 (reason: {reason})。{text[:100]}'}
        except Exception as e:
            return {'success': False, 'error': f'解析回應失敗: {str(e)}'}

    # ── 文字生圖 ───────────────────────────────────────────────
    def generate(self, prompt: str, width: int, height: int,
                 negative_prompt: Optional[str] = None,
                 seed: Optional[int] = None,
                 steps: Optional[int] = None,
                 guidance_scale: Optional[float] = None,
                 **kwargs) -> dict:
        try:
            client = self._get_client()

            # Imagen 使用不同 API
            if self._model_meta.get('use_generate_images'):
                return self._generate_with_imagen(client, prompt)

            full_prompt = prompt
            if negative_prompt:
                full_prompt += f"\n\nAvoid: {negative_prompt}"

            from google.genai import types
            response = client.models.generate_content(
                model=self._model_id,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE', 'TEXT']
                ),
            )
            return self._process_response(response)
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _generate_with_imagen(self, client, prompt: str) -> dict:
        """使用 Imagen generateImages API"""
        try:
            response = client.models.generate_images(
                model=self._model_id,
                prompt=prompt,
            )
            if response.generated_images:
                img = response.generated_images[0]
                return {
                    'success': True,
                    'base64': img.image.image_bytes if hasattr(img.image, 'image_bytes') else img.image.imageBytes,
                    'mime_type': 'image/jpeg',
                    'seed': random.randint(0, 2 ** 32 - 1),
                }
            return {'success': False, 'error': 'Imagen 未回傳圖片'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ── 圖生圖 ─────────────────────────────────────────────────
    def img2img(self, image_base64: str, prompt: str,
                strength: float = 0.7,
                width: Optional[int] = None,
                height: Optional[int] = None,
                negative_prompt: Optional[str] = None,
                seed: Optional[int] = None,
                mime_type: str = 'image/jpeg',
                **kwargs) -> dict:
        try:
            client = self._get_client()
            from google.genai import types

            parts = [
                types.Part.from_bytes(data=base64.b64decode(image_base64), mime_type=mime_type),
                types.Part.from_text(text=prompt),
            ]
            response = client.models.generate_content(
                model=self._model_id,
                contents=types.Content(parts=parts),
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE', 'TEXT']
                ),
            )
            return self._process_response(response)
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ── Avatar Studio 照片編輯 ─────────────────────────────────
    def edit_photo(self, feature: str, image_base64: str,
                   image2_base64: Optional[str] = None,
                   mask_base64: Optional[str] = None,
                   image_mime: str = 'image/jpeg',
                   image2_mime: str = 'image/jpeg',
                   params: Optional[dict] = None) -> dict:
        """
        Avatar Studio 功能入口

        feature 可以是：
          professional, anime, figure, sticker, passport,
          colorize, scene, inpaint, outpaint, tryon,
          exploded, doodle, logo, gif, fusion
        """
        try:
            client = self._get_client()
            params = params or {}
            handler = self._get_feature_handler(feature)
            return handler(client, image_base64, image2_base64, mask_base64,
                           image_mime, image2_mime, params)
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_feature_handler(self, feature: str):
        handlers = {
            'professional': self._handle_professional,
            'anime': self._handle_anime,
            'figure': self._handle_figure,
            'sticker': self._handle_sticker,
            'passport': self._handle_passport,
            'colorize': self._handle_colorize,
            'scene': self._handle_scene,
            'inpaint': self._handle_inpaint,
            'outpaint': self._handle_outpaint,
            'tryon': self._handle_tryon,
            'exploded': self._handle_exploded,
            'doodle': self._handle_doodle,
            'logo': self._handle_logo,
            'gif': self._handle_gif,
            'fusion': self._handle_fusion,
        }
        handler = handlers.get(feature)
        if not handler:
            raise ValueError(f"不支援的功能: {feature}")
        return handler

    def _call_gemini(self, client, parts_list: list, model_id: str = None) -> dict:
        """統一呼叫 Gemini API 的內部方法"""
        from google.genai import types
        response = client.models.generate_content(
            model=model_id or self._model_id,
            contents=types.Content(parts=parts_list),
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT']
            ),
        )
        return self._process_response(response)

    def _img_part(self, b64: str, mime: str):
        from google.genai import types
        return types.Part.from_bytes(data=base64.b64decode(b64), mime_type=mime)

    def _txt_part(self, text: str):
        from google.genai import types
        return types.Part.from_text(text=text)

    # ── 各功能處理器 ───────────────────────────────────────────

    def _handle_professional(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        bg = params.get('background', 'a clean, professional office background')
        attire = params.get('attire', 'a professional business suit')
        hairstyle = params.get('hairstyle', '')
        expression = params.get('expression', '')
        accessory = params.get('accessory', '')
        preserve = params.get('preserve_features', False)

        if preserve:
            prompt = f"""Your task is a high-fidelity photorealistic composite professional headshot.
1. Analyze the original head: proportions, skin tone, lighting direction, neck angle.
2. Generate a compatible body wearing {attire} against background: {bg}.
3. Seamlessly integrate head and body with matching skin tone and lighting.
4. Apply professional photo retouching without altering facial features.
{f'Accessory: {accessory}.' if accessory else ''}
The output must look indistinguishable from a real professional photograph."""
        else:
            prompt = f"A professional, high-resolution headshot. Background: {bg}. Wearing: {attire}."
            if hairstyle:
                prompt += f" Hairstyle: {hairstyle}."
            if expression:
                prompt += f" Expression: {expression}."
            if accessory:
                prompt += f" Accessory: {accessory}."
            prompt += " Soft, flattering lighting suitable for a corporate profile."

        return self._call_gemini(client, [self._img_part(img_b64, img_mime), self._txt_part(prompt)])

    def _handle_anime(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        style = params.get('style', 'Modern Anime')
        strength = params.get('strength', 3)
        negative = params.get('negative_prompt', '')

        strength_desc = {
            1: "very subtle, mostly photorealistic with light anime hints",
            2: "moderate, photo features dominant with anime influence",
            3: "balanced blend of photo likeness and anime style",
            4: "strong anime transformation, original features adapted",
            5: "highly stylized anime, original photo as loose reference",
        }.get(strength, "balanced blend of photo likeness and anime style")

        # Step 1: Generate prompt via text-only call
        try:
            from google.genai import types
            prompt_resp = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"""Based on a photo, generate an English prompt for an anime avatar in the style of "{style}".
Achieve {strength_desc} transformation. Preserve the person's recognizable facial features.
Output ONLY the English prompt, no markdown.""",
                config=types.GenerateContentConfig(
                    system_instruction="You are an expert AI art prompt engineer for anime-style avatars."
                ),
            )
            img_prompt = (prompt_resp.text or '').strip()
            if not img_prompt:
                img_prompt = f"Transform this photo into {style} anime style avatar, preserving facial features."
        except Exception:
            img_prompt = f"Transform this photo into {style} anime style avatar, preserving facial features."

        if negative:
            img_prompt += f"\n\nNegative Prompt: Do not include: {negative}"

        return self._call_gemini(client, [self._img_part(img_b64, img_mime), self._txt_part(img_prompt)])

    def _handle_figure(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        base = params.get('figure_base', 'on a simple display stand')
        mode = params.get('team_mode', 'single')

        base_prompt = f"""Generate a high-quality 1/7 scale collectible figure product shot.
CRITICAL: Preserve 100% likeness of the person(s) from the photo.
Display: {base}. Professional figure photography lighting."""

        parts = [self._img_part(img_b64, img_mime)]
        if mode in ('duo_new', 'duo_same') and img2_b64:
            parts.append(self._img_part(img2_b64, img2_mime))
            base_prompt += "\nCreate two figures based on the two provided photos side by side."

        parts.append(self._txt_part(base_prompt))
        return self._call_gemini(client, parts)

    def _handle_sticker(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        style_id = params.get('sticker_style', 'cute_chibi')
        theme = params.get('theme', '')
        add_text = params.get('add_text', False)

        style_prompts = {
            'cute_chibi': "cute chibi cartoon sticker with rounded features, big eyes, pastel colors",
            'pixel_art': "pixel art sticker, 16-bit retro game style",
            'watercolor': "soft watercolor illustration sticker",
            'bold_line': "bold black outline sticker, flat bold colors, comic style",
            'holographic': "holographic iridescent sticker with shiny metallic effect",
        }
        style_desc = style_prompts.get(style_id, style_prompts['cute_chibi'])

        prompt = f"""Convert the person in the photo into a {style_desc}.
The sticker must have a clean white or transparent background, suitable for printing.
Preserve recognizable features from the original photo.
{f'Theme/context: {theme}.' if theme else ''}
{'Add a short fun text label related to the character.' if add_text else ''}"""

        return self._call_gemini(client, [self._img_part(img_b64, img_mime), self._txt_part(prompt)])

    def _handle_passport(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        photo_type = params.get('photo_type', 'id')  # 'id' or 'resume'
        prompt = """Create a professional passport/ID photo:
- White background, even lighting, no shadows on face
- Subject facing forward, neutral expression
- Proper framing: head centered, showing full face and top of shoulders
- High quality, sharp focus, no filters
- Suitable for official government ID or resume use"""
        if photo_type == 'resume':
            prompt += "\n- Slight professional smile acceptable for resume use"

        return self._call_gemini(client, [self._img_part(img_b64, img_mime), self._txt_part(prompt)])

    def _handle_colorize(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        prompt = """Colorize this black and white photograph with photorealistic, natural colors.
Analyze the context (era, environment, subjects) to apply historically accurate and realistic colors.
Preserve all original details, textures, and composition. Output a vibrant, full-color photograph."""
        return self._call_gemini(client, [self._txt_part(prompt), self._img_part(img_b64, img_mime)])

    def _handle_scene(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        scene_prompt = params.get('scene_prompt', 'a beautiful outdoor scene')
        keep_hair = params.get('keep_hairstyle', False)

        prompt = f"""Expert background replacement with photorealistic results:
1. Precisely isolate the main subject, preserving hair strands and edge details.
2. Generate a new photorealistic background: "{scene_prompt}"
3. Match lighting, shadows, and color grading between subject and new background.
4. Final result must look like a seamless, natural photograph.
{chr(10) + 'CRITICAL: Preserve the subject original hairstyle exactly.' if keep_hair else ''}"""

        return self._call_gemini(client, [self._img_part(img_b64, img_mime), self._txt_part(prompt)])

    def _handle_inpaint(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        inpaint_prompt = params.get('inpaint_prompt', 'fill naturally')
        if not mask_b64:
            return {'success': False, 'error': '請先在圖片上繪製遮罩區域'}

        prompt = f"""Inpainting task: Replace the masked area (shown in the second image as white region) with: "{inpaint_prompt}".
The replacement must blend seamlessly with the surrounding area, matching lighting, texture, and perspective.
The rest of the image must remain completely unchanged."""

        return self._call_gemini(client, [
            self._txt_part(prompt),
            self._img_part(img_b64, img_mime),
            self._img_part(mask_b64, 'image/png'),
        ])

    def _handle_outpaint(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        outpaint_prompt = params.get('outpaint_prompt', 'extend the scene naturally')
        ratio = params.get('aspect_ratio', '16:9')

        prompt = f"""Outpainting task: Extend this image to {ratio} aspect ratio.
Fill the new areas with: "{outpaint_prompt}"
The extension must be seamless, matching the style, lighting, and environment of the original image."""

        parts = [self._txt_part(prompt), self._img_part(img_b64, img_mime)]
        if mask_b64:
            parts.append(self._img_part(mask_b64, 'image/png'))

        return self._call_gemini(client, parts)

    def _handle_tryon(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        if not img2_b64:
            return {'success': False, 'error': '請上傳服裝圖片'}

        prompt = """Virtual try-on: Dress the person in the first image with the clothing shown in the second image.
Maintain the person's exact pose, body proportions, and facial features.
The clothing must fit naturally, with realistic wrinkles, shadows, and fabric texture.
Final result should look like a natural photograph of the person wearing that outfit."""

        return self._call_gemini(client, [
            self._txt_part(prompt),
            self._img_part(img_b64, img_mime),
            self._img_part(img2_b64, img2_mime),
        ])

    def _handle_exploded(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        prompt = """Create an exploded view technical illustration of the object in this image.
Show all components separated and floating in space with dotted lines indicating assembly relationships.
Use a clean white background, professional technical drawing style with labels if applicable.
The illustration should be detailed and educational."""
        return self._call_gemini(client, [self._txt_part(prompt), self._img_part(img_b64, img_mime)])

    def _handle_doodle(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        doodle_style = params.get('doodle_style', 'realistic')
        doodle_prompt = params.get('doodle_prompt', 'Convert this sketch into a detailed image')

        prompt = f"""{doodle_prompt}
Style: {doodle_style}. Use the sketch/doodle as a guide for composition and subject matter.
Create a complete, polished image that brings the sketch to life."""

        parts = [self._txt_part(prompt), self._img_part(img_b64, img_mime)]
        if img2_b64:
            parts.append(self._img_part(img2_b64, img2_mime))

        return self._call_gemini(client, parts)

    def _handle_logo(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        """Logo 設計使用 Imagen（不需要輸入圖片）"""
        brand = params.get('brand', '')
        concept = params.get('concept', '')
        logo_type = params.get('logo_type', 'modern')
        color = params.get('color', '')
        elements = params.get('elements', '')

        prompt = f"""Professional logo design for brand "{brand}".
Style: {logo_type}. Concept: {concept}.
{f'Colors: {color}.' if color else ''}
{f'Include elements: {elements}.' if elements else ''}
Clean, scalable vector-style design on white background. Suitable for business use."""

        # Logo 優先使用 Imagen
        try:
            response = client.models.generate_images(
                model='imagen-4.0-generate-001',
                prompt=prompt,
            )
            if response.generated_images:
                img = response.generated_images[0]
                raw = img.image.image_bytes if hasattr(img.image, 'image_bytes') else img.image.imageBytes
                # 若已經是 base64 字串
                if isinstance(raw, bytes):
                    b64 = base64.b64encode(raw).decode()
                else:
                    b64 = raw
                return {'success': True, 'base64': b64, 'mime_type': 'image/jpeg', 'seed': 0}
        except Exception:
            pass

        # fallback: Flash Image
        return self._call_gemini(client, [self._txt_part(prompt)])

    def _handle_gif(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        gif_prompt = params.get('gif_prompt', 'Create an animated version')
        parts = []
        if img_b64:
            parts.append(self._img_part(img_b64, img_mime))
        parts.append(self._txt_part(f"""{gif_prompt}
Create a single frame that captures the essence of an animated sequence.
Show motion blur or key frame composition that implies animation."""))
        return self._call_gemini(client, parts)

    def _handle_fusion(self, client, img_b64, img2_b64, mask_b64, img_mime, img2_mime, params):
        if not img2_b64:
            return {'success': False, 'error': '請上傳第二張人物圖片'}
        scene = params.get('scene_prompt', 'a beautiful outdoor scene')

        prompt = f"""High-fidelity photorealistic composite: combine two people from the two provided photos into a single group photo.
Scene: "{scene}"
NON-NEGOTIABLE: Both people's faces must be 100% identical and instantly recognizable as in the input photos.
Unify lighting, shadows, and color grading to create a seamless composite.
Final output must look like a real group photograph."""

        return self._call_gemini(client, [
            self._txt_part(prompt),
            self._img_part(img_b64, img_mime),
            self._img_part(img2_b64, img2_mime),
        ])

    def get_model_info(self) -> dict:
        info = super().get_model_info()
        info.update({
            'name': self._model_meta.get('display_name', self._model_id),
            'description': f'Google Gemini 雲端模型 ({self._model_id})',
            'model_id': self._model_id,
            'available_models': list(GEMINI_MODELS.keys()),
        })
        return info
