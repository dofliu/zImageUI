"""
Favorites Service - 提示詞收藏管理服務
"""
import os
import json
from datetime import datetime
import config


class FavoritesService:
    """提示詞收藏管理類"""
    
    def __init__(self):
        self.favorites_file = os.path.join(config.OUTPUT_PATH, "favorites.json")
    
    def load_favorites(self):
        """載入收藏清單"""
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_favorites(self, favorites):
        """儲存收藏清單"""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存收藏失敗: {e}")
    
    def add_favorite(self, prompt, name=None):
        """新增收藏"""
        favorites = self.load_favorites()
        
        # 檢查是否已存在
        for fav in favorites:
            if fav['prompt'] == prompt:
                return None  # 已存在
        
        favorite_item = {
            'id': f"fav_{int(datetime.now().timestamp() * 1000)}",
            'prompt': prompt,
            'name': name or prompt[:30] + ('...' if len(prompt) > 30 else ''),
            'created_at': datetime.now().isoformat(),
            'use_count': 0
        }
        favorites.insert(0, favorite_item)
        self.save_favorites(favorites)
        return favorite_item
    
    def remove_favorite(self, favorite_id):
        """移除收藏"""
        favorites = self.load_favorites()
        favorites = [f for f in favorites if f['id'] != favorite_id]
        self.save_favorites(favorites)
        return True
    
    def increment_use_count(self, favorite_id):
        """增加使用次數"""
        favorites = self.load_favorites()
        for fav in favorites:
            if fav['id'] == favorite_id:
                fav['use_count'] = fav.get('use_count', 0) + 1
                break
        self.save_favorites(favorites)


# 全域收藏服務實例
_favorites_service = None


def get_favorites_service():
    """獲取收藏服務單例"""
    global _favorites_service
    if _favorites_service is None:
        _favorites_service = FavoritesService()
    return _favorites_service
