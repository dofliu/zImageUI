"""
Story Service - 連貫漫畫/故事生成系統

核心設計理念：
1. 角色錨定 - 每個角色有固定的外貌描述 prompt block，嵌入每個面板
2. 風格錨定 - 統一的風格前綴/後綴包裹每個場景描述
3. Seed 基底 - 同一 seed 基底 + 面板偏移量維持風格一致
4. 場景推進 - 每個面板有獨立的場景描述但共享角色和風格
"""
import os
import json
import uuid
import random
from datetime import datetime
import config


STORIES_FILE = os.path.join(config.OUTPUT_PATH, "stories.json")

# 預設風格範本
STYLE_PRESETS = {
    "manga_bw": {
        "name": "黑白漫畫",
        "style_prefix": "manga panel, black and white, ink drawing, screentone shading",
        "style_suffix": "manga style, clean lineart, high contrast, professional manga",
        "negative": "color, photograph, 3d render, blurry, low quality"
    },
    "manga_color": {
        "name": "彩色漫畫",
        "style_prefix": "colored manga panel, cel shading, vibrant colors, anime coloring",
        "style_suffix": "manga style, clean lineart, vivid colors, professional manga illustration",
        "negative": "photograph, 3d render, blurry, low quality, realistic"
    },
    "anime": {
        "name": "動漫風格",
        "style_prefix": "anime illustration, detailed anime art, studio quality",
        "style_suffix": "anime style, pixiv quality, detailed illustration, beautiful color palette",
        "negative": "realistic, photograph, 3d, blurry, low quality, bad anatomy"
    },
    "comic_western": {
        "name": "美式漫畫",
        "style_prefix": "western comic book panel, bold outlines, dynamic shading",
        "style_suffix": "comic book style, Marvel DC style, dramatic lighting, professional comic art",
        "negative": "manga, anime, photograph, blurry, low quality"
    },
    "watercolor": {
        "name": "水彩繪本",
        "style_prefix": "watercolor illustration, soft colors, gentle brushstrokes, storybook art",
        "style_suffix": "watercolor style, children's book illustration, whimsical, dreamy atmosphere",
        "negative": "photograph, 3d, harsh lighting, dark, horror"
    },
    "pixel_art": {
        "name": "像素藝術",
        "style_prefix": "pixel art, 16-bit style, retro game aesthetic",
        "style_suffix": "pixel art style, clean pixels, retro gaming, sprite art quality",
        "negative": "realistic, photograph, blurry, 3d render, smooth"
    },
    "cinematic": {
        "name": "電影分鏡",
        "style_prefix": "cinematic film still, movie scene, dramatic cinematography",
        "style_suffix": "cinematic lighting, film grain, anamorphic lens, movie quality, 35mm film",
        "negative": "cartoon, anime, illustration, drawing, blurry"
    },
    "ink_wash": {
        "name": "水墨風格",
        "style_prefix": "Chinese ink wash painting, traditional brush painting, sumi-e style",
        "style_suffix": "ink painting style, elegant brushwork, minimalist, traditional Asian art",
        "negative": "colorful, modern, 3d, photograph, western art"
    }
}

# 預設佈局模板
LAYOUT_PRESETS = {
    "4koma": {
        "name": "四格漫畫",
        "description": "經典日式四格，由上而下或由左至右",
        "panels": 4,
        "structure": ["起 (Setup)", "承 (Development)", "轉 (Twist)", "結 (Conclusion)"],
        "aspect_ratio": "3:4"
    },
    "6panel": {
        "name": "六格漫畫",
        "description": "2x3 或 3x2 格式，適合較長故事",
        "panels": 6,
        "structure": ["開場", "鋪陳", "發展", "衝突", "高潮", "結局"],
        "aspect_ratio": "1:1"
    },
    "3panel": {
        "name": "三格漫畫",
        "description": "簡潔的三幕結構",
        "panels": 3,
        "structure": ["開頭", "過程", "結尾"],
        "aspect_ratio": "16:9"
    },
    "storyboard": {
        "name": "故事板",
        "description": "電影分鏡式寬螢幕",
        "panels": 4,
        "structure": ["場景建立", "角色登場", "關鍵動作", "結果"],
        "aspect_ratio": "21:9"
    },
    "single": {
        "name": "單幅插畫",
        "description": "單張高品質場景圖",
        "panels": 1,
        "structure": ["完整場景"],
        "aspect_ratio": "1:1"
    }
}

# 面板尺寸對照
ASPECT_SIZES = {
    "1:1": (768, 768),
    "3:4": (576, 768),
    "4:3": (768, 576),
    "16:9": (896, 512),
    "9:16": (512, 896),
    "21:9": (1024, 448),
}


class StoryService:
    """連貫漫畫/故事生成服務"""

    def __init__(self):
        self.stories = self._load()

    def _load(self):
        if os.path.exists(STORIES_FILE):
            try:
                with open(STORIES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save(self):
        try:
            os.makedirs(os.path.dirname(STORIES_FILE), exist_ok=True)
            with open(STORIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.stories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存故事失敗: {e}")

    # ========== 故事 CRUD ==========

    def create_story(self, title, style_preset='anime', layout='4koma', description=''):
        """建立新故事"""
        layout_info = LAYOUT_PRESETS.get(layout, LAYOUT_PRESETS['4koma'])
        style_info = STYLE_PRESETS.get(style_preset, STYLE_PRESETS['anime'])

        story = {
            'id': str(uuid.uuid4())[:8],
            'title': title,
            'description': description,
            'style_preset': style_preset,
            'style_custom': {
                'prefix': style_info['style_prefix'],
                'suffix': style_info['style_suffix'],
                'negative': style_info['negative']
            },
            'layout': layout,
            'characters': [],
            'panels': [],
            'seed_base': random.randint(0, 2**32 - 1),
            'model_id': None,  # None = 使用目前已啟用的模型
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'status': 'draft'  # draft, generating, completed
        }

        # 根據佈局預建空面板
        for i, structure_hint in enumerate(layout_info['structure']):
            story['panels'].append({
                'index': i,
                'scene_description': '',
                'structure_hint': structure_hint,
                'character_ids': [],
                'camera_angle': 'medium shot',
                'mood': '',
                'generated_image': None,
                'seed_offset': i,
                'status': 'empty'  # empty, ready, generating, done, error
            })

        self.stories.insert(0, story)
        self._save()
        return story

    def get_story(self, story_id):
        for s in self.stories:
            if s['id'] == story_id:
                return s
        return None

    def list_stories(self):
        return self.stories

    def update_story(self, story_id, updates):
        story = self.get_story(story_id)
        if not story:
            return None
        for k, v in updates.items():
            if k in ('title', 'description', 'style_preset', 'style_custom',
                      'layout', 'seed_base', 'model_id'):
                story[k] = v
        story['updated_at'] = datetime.now().isoformat()
        self._save()
        return story

    def delete_story(self, story_id):
        story = self.get_story(story_id)
        if not story:
            return False
        self.stories.remove(story)
        self._save()
        return True

    # ========== 角色管理 ==========

    def add_character(self, story_id, name, appearance, traits=None, color_palette=None):
        """新增角色到故事

        Args:
            name: 角色名稱
            appearance: 外貌描述（英文，會直接嵌入 prompt）
                例如: "a young woman with long silver hair, bright blue eyes,
                       wearing a dark blue cloak with silver star patterns"
            traits: 角色特徵標籤
            color_palette: 角色代表色
        """
        story = self.get_story(story_id)
        if not story:
            return None

        character = {
            'id': str(uuid.uuid4())[:6],
            'name': name,
            'appearance': appearance,
            'traits': traits or [],
            'color_palette': color_palette or '',
            'created_at': datetime.now().isoformat()
        }
        story['characters'].append(character)
        story['updated_at'] = datetime.now().isoformat()
        self._save()
        return character

    def update_character(self, story_id, char_id, updates):
        story = self.get_story(story_id)
        if not story:
            return None
        for c in story['characters']:
            if c['id'] == char_id:
                for k, v in updates.items():
                    if k in ('name', 'appearance', 'traits', 'color_palette'):
                        c[k] = v
                story['updated_at'] = datetime.now().isoformat()
                self._save()
                return c
        return None

    def remove_character(self, story_id, char_id):
        story = self.get_story(story_id)
        if not story:
            return False
        story['characters'] = [c for c in story['characters'] if c['id'] != char_id]
        # 從面板中移除
        for panel in story['panels']:
            if char_id in panel.get('character_ids', []):
                panel['character_ids'].remove(char_id)
        story['updated_at'] = datetime.now().isoformat()
        self._save()
        return True

    # ========== 面板管理 ==========

    def update_panel(self, story_id, panel_index, updates):
        """更新面板設定"""
        story = self.get_story(story_id)
        if not story or panel_index >= len(story['panels']):
            return None

        panel = story['panels'][panel_index]
        for k, v in updates.items():
            if k in ('scene_description', 'character_ids', 'camera_angle',
                      'mood', 'seed_offset'):
                panel[k] = v
        if panel.get('scene_description'):
            panel['status'] = 'ready'

        story['updated_at'] = datetime.now().isoformat()
        self._save()
        return panel

    def add_panel(self, story_id):
        """追加一個面板"""
        story = self.get_story(story_id)
        if not story:
            return None
        idx = len(story['panels'])
        panel = {
            'index': idx,
            'scene_description': '',
            'structure_hint': f'第 {idx + 1} 格',
            'character_ids': [],
            'camera_angle': 'medium shot',
            'mood': '',
            'generated_image': None,
            'seed_offset': idx,
            'status': 'empty'
        }
        story['panels'].append(panel)
        story['updated_at'] = datetime.now().isoformat()
        self._save()
        return panel

    def remove_panel(self, story_id, panel_index):
        """移除面板"""
        story = self.get_story(story_id)
        if not story or panel_index >= len(story['panels']):
            return False
        story['panels'].pop(panel_index)
        # 重建索引
        for i, p in enumerate(story['panels']):
            p['index'] = i
        story['updated_at'] = datetime.now().isoformat()
        self._save()
        return True

    # ========== 提示詞組裝引擎 ==========

    def assemble_prompt(self, story, panel_index):
        """組裝單一面板的完整提示詞

        組裝邏輯：
        [style_prefix], [camera_angle] of [scene_description],
        featuring [character_A_appearance] and [character_B_appearance],
        [mood], [style_suffix]

        Returns:
            dict: {prompt, negative_prompt, seed, width, height}
        """
        if panel_index >= len(story['panels']):
            return None

        panel = story['panels'][panel_index]
        style = story.get('style_custom', {})
        layout_info = LAYOUT_PRESETS.get(story.get('layout', '4koma'), LAYOUT_PRESETS['4koma'])

        # 1. 風格前綴
        prefix = style.get('prefix', '')

        # 2. 構圖/鏡頭角度
        camera = panel.get('camera_angle', 'medium shot')

        # 3. 場景描述
        scene = panel.get('scene_description', '')

        # 4. 角色描述區塊
        char_blocks = []
        char_ids = panel.get('character_ids', [])
        for char_id in char_ids:
            char = self._find_character(story, char_id)
            if char:
                char_blocks.append(char['appearance'])

        # 5. 情緒/氛圍
        mood = panel.get('mood', '')

        # 6. 風格後綴
        suffix = style.get('suffix', '')

        # 組裝
        parts = []
        if prefix:
            parts.append(prefix)
        if camera:
            parts.append(camera)

        if scene and char_blocks:
            parts.append(f"{scene}, featuring {', and '.join(char_blocks)}")
        elif scene:
            parts.append(scene)
        elif char_blocks:
            parts.append(f"featuring {', and '.join(char_blocks)}")

        if mood:
            parts.append(mood)
        if suffix:
            parts.append(suffix)

        prompt = ', '.join(parts)

        # 負面提示詞
        negative = style.get('negative', '')

        # Seed 計算（基底 + 偏移）
        seed_base = story.get('seed_base', 42)
        seed_offset = panel.get('seed_offset', panel_index)
        seed = seed_base + seed_offset

        # 面板尺寸
        aspect = layout_info.get('aspect_ratio', '1:1')
        width, height = ASPECT_SIZES.get(aspect, (768, 768))

        return {
            'prompt': prompt,
            'negative_prompt': negative,
            'seed': seed,
            'width': width,
            'height': height,
            'panel_index': panel_index
        }

    def assemble_all_prompts(self, story_id):
        """組裝故事的所有面板提示詞"""
        story = self.get_story(story_id)
        if not story:
            return None

        prompts = []
        for i in range(len(story['panels'])):
            p = self.assemble_prompt(story, i)
            if p:
                prompts.append(p)
        return prompts

    def _find_character(self, story, char_id):
        for c in story.get('characters', []):
            if c['id'] == char_id:
                return c
        return None

    # ========== 面板生成 ==========

    def generate_panel(self, story_id, panel_index):
        """生成單一面板圖片"""
        from services.model_registry import get_model_registry
        import base64
        from io import BytesIO

        story = self.get_story(story_id)
        if not story:
            return {'success': False, 'error': '找不到故事'}

        prompt_data = self.assemble_prompt(story, panel_index)
        if not prompt_data:
            return {'success': False, 'error': '面板不存在'}

        if not prompt_data['prompt'].strip():
            return {'success': False, 'error': '面板尚未設定場景描述'}

        registry = get_model_registry()

        # 檢查模型是否正在載入中
        if registry.is_loading:
            return {'success': False, 'error': f'模型「{registry.loading_model_name}」正在載入中，請稍候再試'}

        # 確保有模型可用 — 若未載入則自動載入預設模型
        if registry.active_pipeline is None:
            models = registry.list_models()
            if models:
                default_id = models[0]['id']
                print(f"[*] 自動載入預設模型: {default_id}")
                switch_result = registry.switch_model(default_id)
                if not switch_result.get('success'):
                    return {'success': False, 'error': f"自動載入模型失敗: {switch_result.get('error', '未知錯誤')}"}
            else:
                return {'success': False, 'error': '沒有可用的模型'}

        # 如果故事指定了不同模型，先檢查該模型是否存在
        desired_model = story.get('model_id')
        if desired_model:
            # 模型不在註冊表中（舊資料殘留），直接忽略
            if not registry.get_model_info(desired_model):
                print(f"[!] 故事指定的模型 {desired_model} 不存在，忽略並使用目前模型")
                desired_model = None

        if desired_model and desired_model != registry.active_model_id:
            switch_result = registry.switch_model(desired_model)
            if not switch_result.get('success'):
                print(f"[!] 切換模型 {desired_model} 失敗，使用目前模型 {registry.active_model_id}")

        # 更新面板狀態
        story['panels'][panel_index]['status'] = 'generating'
        self._save()

        try:
            image, actual_seed = registry.generate(
                prompt=prompt_data['prompt'],
                width=prompt_data['width'],
                height=prompt_data['height'],
                seed=prompt_data['seed'],
                negative_prompt=prompt_data['negative_prompt'] or None
            )

            # 儲存圖片
            story_dir = os.path.join(config.OUTPUT_PATH, 'stories', story_id)
            os.makedirs(story_dir, exist_ok=True)
            filename = f"panel_{panel_index}_{actual_seed}.png"
            filepath = os.path.join(story_dir, filename)
            image.save(filepath)

            # 轉 base64 給前端預覽
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            # 更新面板
            story['panels'][panel_index]['generated_image'] = filename
            story['panels'][panel_index]['actual_seed'] = actual_seed
            story['panels'][panel_index]['status'] = 'done'
            story['panels'][panel_index]['generated_prompt'] = prompt_data['prompt']
            story['updated_at'] = datetime.now().isoformat()
            self._save()

            return {
                'success': True,
                'panel_index': panel_index,
                'image_base64': img_b64,
                'filename': filename,
                'prompt_used': prompt_data['prompt'],
                'seed': actual_seed
            }

        except Exception as e:
            story['panels'][panel_index]['status'] = 'error'
            story['panels'][panel_index]['error'] = str(e)
            self._save()
            return {'success': False, 'error': str(e)}

    def generate_all_panels(self, story_id):
        """依序生成所有面板"""
        story = self.get_story(story_id)
        if not story:
            return {'success': False, 'error': '找不到故事'}

        results = []
        story['status'] = 'generating'
        self._save()

        for i in range(len(story['panels'])):
            panel = story['panels'][i]
            if panel.get('scene_description'):
                result = self.generate_panel(story_id, i)
                results.append(result)
            else:
                results.append({
                    'success': False,
                    'panel_index': i,
                    'error': '未設定場景描述，跳過'
                })

        story['status'] = 'completed'
        self._save()

        success_count = sum(1 for r in results if r.get('success'))
        return {
            'success': True,
            'total': len(results),
            'succeeded': success_count,
            'failed': len(results) - success_count,
            'results': results
        }

    def get_panel_image_path(self, story_id, panel_index):
        """取得面板圖片路徑"""
        story = self.get_story(story_id)
        if not story or panel_index >= len(story['panels']):
            return None
        filename = story['panels'][panel_index].get('generated_image')
        if not filename:
            return None
        return os.path.join(config.OUTPUT_PATH, 'stories', story_id, filename)

    # ========== AI 腳本生成 ==========

    def generate_script(self, story_id, auto_create_characters=True):
        """用 LLM 自動生成故事腳本（角色 + 面板描述）

        Args:
            story_id: 故事 ID
            auto_create_characters: 若故事尚無角色，是否自動生成
        """
        from services.llm_service import get_llm_service

        story = self.get_story(story_id)
        if not story:
            return {'success': False, 'error': '找不到故事'}

        llm = get_llm_service()
        if llm.model is None:
            return {'success': False, 'error': '尚未載入 LLM 模型，請先在設定中載入語言模型'}

        layout_key = story.get('layout', '4koma')
        layout = LAYOUT_PRESETS.get(layout_key, LAYOUT_PRESETS['4koma'])
        panel_count = layout['panels']
        structure = layout.get('structure', [])

        style_key = story.get('style_preset', 'anime')
        style = STYLE_PRESETS.get(style_key, STYLE_PRESETS['anime'])

        # 若尚無角色且允許自動生成，先讓 AI 構想角色
        characters_created = []
        if auto_create_characters and not story.get('characters'):
            char_result = self._generate_characters_via_llm(llm, story, style)
            if char_result.get('success'):
                for c in char_result['characters']:
                    created = self.add_character(
                        story_id=story_id,
                        name=c['name'],
                        appearance=c['appearance'],
                        traits=c.get('traits', []),
                        color_palette=c.get('color_palette', '')
                    )
                    if created:
                        characters_created.append(created)
                # 重新載入故事以取得最新角色
                story = self.get_story(story_id)
            else:
                print(f"[!] 角色生成失敗: {char_result.get('error')}，將繼續生成腳本")

        # 組裝角色資訊
        char_info = ""
        if story.get('characters'):
            char_lines = []
            for c in story['characters']:
                char_lines.append(f"- {c['name']}: {c.get('appearance', '')}")
            char_info = "\n".join(char_lines)

        # 組裝結構提示
        structure_hints = ""
        if structure:
            hints = [f"Panel {i+1}: {s}" for i, s in enumerate(structure)]
            structure_hints = "\n".join(hints)

        camera_angles = ", ".join(self.get_camera_angles()[:8])
        mood_options = ", ".join(self.get_mood_options()[:8])

        system_prompt = """You are a professional comic/manga script writer.
Your job is to generate panel-by-panel scene descriptions for image generation AI.
ALL scene descriptions MUST be written in English.
Output ONLY valid JSON, no explanations or markdown."""

        user_prompt = f"""Create a {panel_count}-panel comic script.

Title: {story.get('title', '')}
Story concept: {story.get('description', '(no description provided)')}
Visual style: {style['name']}

Characters:
{char_info if char_info else '(no characters defined yet)'}

Story structure:
{structure_hints if structure_hints else f'{panel_count} panels'}

Available camera angles: {camera_angles}
Available moods: {mood_options}

Output this exact JSON format:
{{
  "panels": [
    {{
      "scene_description": "English description of what happens in this panel, focusing on actions, poses, expressions, and environment",
      "camera_angle": "one of the available camera angles",
      "mood": "one of the available moods",
      "characters": ["character names that appear in this panel"]
    }}
  ]
}}

Rules:
- scene_description must be in English, detailed enough for image AI (30-60 words each)
- Each panel should advance the story
- Vary camera angles across panels for visual interest
- Match mood to the story moment
- Reference character names so we know who appears in each panel"""

        try:
            response = llm.chat(user_prompt, system_prompt)

            # 嘗試解析 JSON
            panels_data = self._parse_script_response(response)
            if not panels_data:
                return {
                    'success': False,
                    'error': 'AI 回覆格式無法解析，請重試',
                    'raw_response': response
                }

            # 將 AI 生成的腳本填入面板
            char_name_to_id = {}
            for c in story.get('characters', []):
                char_name_to_id[c['name'].lower()] = c['id']

            # 確保面板數量匹配
            while len(story['panels']) < len(panels_data):
                story['panels'].append({
                    'index': len(story['panels']),
                    'scene_description': '',
                    'structure_hint': '',
                    'character_ids': [],
                    'camera_angle': 'medium shot',
                    'mood': '',
                    'generated_image': None,
                    'seed_offset': len(story['panels']),
                    'status': 'empty',
                    'generated_prompt': None,
                    'actual_seed': None
                })

            for i, panel_data in enumerate(panels_data):
                if i >= len(story['panels']):
                    break
                panel = story['panels'][i]
                panel['scene_description'] = panel_data.get('scene_description', '')
                panel['camera_angle'] = panel_data.get('camera_angle', 'medium shot')
                panel['mood'] = panel_data.get('mood', '')
                panel['status'] = 'ready'

                # 根據角色名稱匹配 ID
                char_names = panel_data.get('characters', [])
                matched_ids = []
                for name in char_names:
                    name_lower = name.lower()
                    for cname, cid in char_name_to_id.items():
                        if cname in name_lower or name_lower in cname:
                            matched_ids.append(cid)
                            break
                panel['character_ids'] = matched_ids

            story['updated_at'] = datetime.now().isoformat()
            self._save()

            return {
                'success': True,
                'message': f'已自動生成 {len(characters_created)} 個角色和 {len(panels_data)} 個面板',
                'panels': story['panels'],
                'characters_created': len(characters_created)
            }
        except Exception as e:
            return {'success': False, 'error': f'腳本生成失敗: {str(e)}'}

    def _generate_characters_via_llm(self, llm, story, style):
        """讓 LLM 根據故事概念自動構想角色"""
        system_prompt = """You are a professional character designer for comics and manga.
Your job is to design memorable characters with distinct visual appearances.
ALL appearance descriptions MUST be written in English, detailed enough for image generation AI.
Output ONLY valid JSON, no explanations or markdown."""

        user_prompt = f"""Design 1 to 3 main characters for this story.

Title: {story.get('title', '')}
Story concept: {story.get('description', '(no description provided)')}
Visual style: {style['name']}

For each character, provide:
- A short memorable name (can be Chinese or English)
- A detailed English appearance description (hair, eyes, clothing, distinctive features, 25-50 words)
  This will be embedded verbatim into every image prompt, so be specific and visual.
- 2-4 personality traits (short English words)
- A signature color (e.g., "crimson red", "ocean blue")

Output this exact JSON format:
{{
  "characters": [
    {{
      "name": "character name",
      "appearance": "detailed English visual description",
      "traits": ["trait1", "trait2", "trait3"],
      "color_palette": "signature color"
    }}
  ]
}}

Rules:
- Design 1-3 characters (not more) that fit the story
- Each appearance must be distinctive enough that the character can be recognized across panels
- Include specific details: hair color/length, eye color, clothing style, age range, distinctive features
- Avoid generic descriptions - be specific and visual"""

        try:
            response = llm.chat(user_prompt, system_prompt)
            characters = self._parse_characters_response(response)
            if not characters:
                return {'success': False, 'error': '無法解析角色資料', 'raw_response': response}
            return {'success': True, 'characters': characters}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _parse_characters_response(self, response):
        """解析 LLM 回傳的角色 JSON"""
        import re
        try:
            data = json.loads(response)
            if 'characters' in data:
                return data['characters']
        except json.JSONDecodeError:
            pass

        json_match = re.search(r'\{[\s\S]*"characters"[\s\S]*\}', response)
        if json_match:
            try:
                data = json.loads(json_match.group())
                if 'characters' in data:
                    return data['characters']
            except json.JSONDecodeError:
                pass
        return None

    def _parse_script_response(self, response):
        """解析 LLM 回傳的 JSON 腳本"""
        import re
        # 嘗試直接解析
        try:
            data = json.loads(response)
            if 'panels' in data:
                return data['panels']
            return None
        except json.JSONDecodeError:
            pass

        # 嘗試提取 JSON 區塊
        json_match = re.search(r'\{[\s\S]*"panels"[\s\S]*\}', response)
        if json_match:
            try:
                data = json.loads(json_match.group())
                if 'panels' in data:
                    return data['panels']
            except json.JSONDecodeError:
                pass

        return None

    # ========== 靜態資料 ==========

    @staticmethod
    def get_style_presets():
        return STYLE_PRESETS

    @staticmethod
    def get_layout_presets():
        return LAYOUT_PRESETS

    @staticmethod
    def get_camera_angles():
        return [
            "extreme close-up", "close-up", "medium close-up",
            "medium shot", "medium long shot", "long shot",
            "extreme long shot", "bird's eye view", "worm's eye view",
            "over the shoulder", "dutch angle", "profile shot"
        ]

    @staticmethod
    def get_mood_options():
        return [
            "warm and cozy", "cold and eerie", "dramatic and intense",
            "peaceful and serene", "mysterious and dark", "cheerful and bright",
            "melancholic and somber", "energetic and dynamic", "romantic and dreamy",
            "tense and suspenseful", "humorous and lighthearted", "epic and grand"
        ]


# 全域單例
_story_service = None


def get_story_service():
    global _story_service
    if _story_service is None:
        _story_service = StoryService()
    return _story_service
