"""
Prompt Library Service - 提示詞庫管理
支援分類、搜尋、評分、分享的社群級提示詞集合
"""
import os
import json
import uuid
from datetime import datetime
import config


PROMPT_LIBRARY_FILE = os.path.join(config.OUTPUT_PATH, "prompt_library.json")

# 預設提示詞庫
DEFAULT_PROMPTS = [
    {
        "id": "default-01",
        "title": "夢幻森林",
        "prompt": "enchanted forest with glowing mushrooms, fairy lights, mystical atmosphere, volumetric fog, cinematic lighting, 8k ultra detailed",
        "negative_prompt": "blurry, low quality, text, watermark",
        "category": "fantasy",
        "tags": ["forest", "magic", "nature"],
        "author": "Z-Image Studio",
        "rating": 4.5,
        "use_count": 0,
        "is_default": True
    },
    {
        "id": "default-02",
        "title": "賽博龐克街道",
        "prompt": "cyberpunk city street at night, neon signs in Japanese, rain reflections on wet pavement, flying cars, holographic advertisements, blade runner style, ultra detailed",
        "negative_prompt": "daylight, nature, blurry",
        "category": "scifi",
        "tags": ["cyberpunk", "city", "night", "neon"],
        "author": "Z-Image Studio",
        "rating": 4.8,
        "use_count": 0,
        "is_default": True
    },
    {
        "id": "default-03",
        "title": "水墨山水",
        "prompt": "traditional Chinese ink wash painting of mountains and rivers, misty peaks, small boat on calm water, pine trees, minimalist style, elegant brushstrokes",
        "negative_prompt": "modern, colorful, cartoon",
        "category": "art",
        "tags": ["chinese", "ink", "landscape", "traditional"],
        "author": "Z-Image Studio",
        "rating": 4.6,
        "use_count": 0,
        "is_default": True
    },
    {
        "id": "default-04",
        "title": "太空站日出",
        "prompt": "sunrise viewed from International Space Station, Earth's curvature, thin blue atmosphere line, solar panels in foreground, stars visible, photorealistic, NASA quality",
        "negative_prompt": "cartoon, illustration, blurry",
        "category": "scifi",
        "tags": ["space", "earth", "sunrise", "photorealistic"],
        "author": "Z-Image Studio",
        "rating": 4.7,
        "use_count": 0,
        "is_default": True
    },
    {
        "id": "default-05",
        "title": "美食攝影",
        "prompt": "professional food photography of a gourmet sushi platter, fresh salmon and tuna, wasabi garnish, dark moody background, studio lighting, shallow depth of field, 85mm lens",
        "negative_prompt": "amateur, blurry, overexposed, messy",
        "category": "photography",
        "tags": ["food", "sushi", "professional", "studio"],
        "author": "Z-Image Studio",
        "rating": 4.4,
        "use_count": 0,
        "is_default": True
    },
    {
        "id": "default-06",
        "title": "動漫角色立繪",
        "prompt": "anime character design, full body, young female warrior with silver hair and blue eyes, fantasy armor with gold accents, dynamic pose, detailed illustration, pixiv trending",
        "negative_prompt": "realistic, photo, deformed, bad anatomy",
        "category": "anime",
        "tags": ["anime", "character", "warrior", "fantasy"],
        "author": "Z-Image Studio",
        "rating": 4.5,
        "use_count": 0,
        "is_default": True
    },
    {
        "id": "default-07",
        "title": "建築概念",
        "prompt": "futuristic sustainable architecture, vertical garden building, solar panels integrated into glass facade, rooftop park, modern eco city, architectural visualization, octane render",
        "negative_prompt": "old, dirty, abandoned, low quality",
        "category": "architecture",
        "tags": ["architecture", "future", "eco", "concept"],
        "author": "Z-Image Studio",
        "rating": 4.3,
        "use_count": 0,
        "is_default": True
    },
    {
        "id": "default-08",
        "title": "油畫靜物",
        "prompt": "classical oil painting still life, flowers in a vase with fruits on table, dramatic chiaroscuro lighting, rich colors, Rembrandt style, museum quality, visible brushstrokes",
        "negative_prompt": "modern, digital, flat, cartoon",
        "category": "art",
        "tags": ["oil painting", "still life", "classical", "flowers"],
        "author": "Z-Image Studio",
        "rating": 4.6,
        "use_count": 0,
        "is_default": True
    }
]

CATEGORIES = {
    "all": "全部",
    "fantasy": "奇幻魔法",
    "scifi": "科幻未來",
    "art": "藝術繪畫",
    "photography": "攝影寫實",
    "anime": "動漫插畫",
    "architecture": "建築概念",
    "portrait": "人物肖像",
    "landscape": "風景自然",
    "abstract": "抽象藝術",
    "custom": "自訂"
}


class PromptLibraryService:
    """提示詞庫服務"""

    def __init__(self):
        self.prompts = self._load()

    def _load(self):
        """載入提示詞庫"""
        if os.path.exists(PROMPT_LIBRARY_FILE):
            try:
                with open(PROMPT_LIBRARY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 合併預設提示詞（如果不存在）
                existing_ids = {p['id'] for p in data}
                for dp in DEFAULT_PROMPTS:
                    if dp['id'] not in existing_ids:
                        data.append(dp)
                return data
            except Exception:
                pass
        return list(DEFAULT_PROMPTS)

    def _save(self):
        """儲存"""
        try:
            os.makedirs(os.path.dirname(PROMPT_LIBRARY_FILE), exist_ok=True)
            with open(PROMPT_LIBRARY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存提示詞庫失敗: {e}")

    def list_prompts(self, category=None, search=None, sort_by='rating'):
        """列出提示詞"""
        results = list(self.prompts)

        if category and category != 'all':
            results = [p for p in results if p.get('category') == category]

        if search:
            search_lower = search.lower()
            results = [p for p in results if
                       search_lower in p.get('title', '').lower() or
                       search_lower in p.get('prompt', '').lower() or
                       any(search_lower in t for t in p.get('tags', []))]

        if sort_by == 'rating':
            results.sort(key=lambda p: p.get('rating', 0), reverse=True)
        elif sort_by == 'use_count':
            results.sort(key=lambda p: p.get('use_count', 0), reverse=True)
        elif sort_by == 'newest':
            results.sort(key=lambda p: p.get('created_at', ''), reverse=True)

        return results

    def get_prompt(self, prompt_id):
        """取得單一提示詞"""
        for p in self.prompts:
            if p['id'] == prompt_id:
                return p
        return None

    def add_prompt(self, title, prompt, negative_prompt='', category='custom',
                   tags=None, author='使用者'):
        """新增提示詞到庫"""
        entry = {
            'id': str(uuid.uuid4())[:8],
            'title': title.strip(),
            'prompt': prompt.strip(),
            'negative_prompt': negative_prompt.strip(),
            'category': category,
            'tags': tags or [],
            'author': author,
            'rating': 0,
            'ratings_count': 0,
            'use_count': 0,
            'created_at': datetime.now().isoformat(),
            'is_default': False
        }
        self.prompts.insert(0, entry)
        self._save()
        return entry

    def use_prompt(self, prompt_id):
        """記錄使用次數"""
        for p in self.prompts:
            if p['id'] == prompt_id:
                p['use_count'] = p.get('use_count', 0) + 1
                self._save()
                return p
        return None

    def rate_prompt(self, prompt_id, rating):
        """為提示詞評分"""
        rating = max(1, min(5, float(rating)))
        for p in self.prompts:
            if p['id'] == prompt_id:
                count = p.get('ratings_count', 0)
                current = p.get('rating', 0)
                # 加權平均
                new_rating = (current * count + rating) / (count + 1)
                p['rating'] = round(new_rating, 1)
                p['ratings_count'] = count + 1
                self._save()
                return p
        return None

    def delete_prompt(self, prompt_id):
        """刪除提示詞（不能刪除預設）"""
        for p in self.prompts:
            if p['id'] == prompt_id:
                if p.get('is_default'):
                    return False
                self.prompts.remove(p)
                self._save()
                return True
        return False

    def get_categories(self):
        """取得所有分類"""
        return CATEGORIES


_prompt_library_service = None


def get_prompt_library_service():
    global _prompt_library_service
    if _prompt_library_service is None:
        _prompt_library_service = PromptLibraryService()
    return _prompt_library_service
