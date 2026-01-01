"""
History Service - 歷史記錄管理服務
"""
import os
import json
from datetime import datetime
import random
import config


class HistoryService:
    """歷史記錄管理類"""
    
    def __init__(self):
        self.output_path = config.OUTPUT_PATH
        self.history_file = os.path.join(self.output_path, "history.json")
        os.makedirs(self.output_path, exist_ok=True)
    
    def load_history(self):
        """載入歷史記錄"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_history(self, history):
        """儲存歷史記錄"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存歷史記錄失敗: {e}")
    
    def add_to_history(self, prompt, filename, tags=None):
        """新增歷史記錄"""
        history = self.load_history()
        history_item = {
            'id': f"{int(datetime.now().timestamp() * 1000)}_{random.randint(1000, 9999)}",
            'prompt': prompt,
            'filename': filename,
            'timestamp': datetime.now().isoformat(),
            'image_url': f'/images/{filename}',
            'tags': tags if tags else []
        }
        history.insert(0, history_item)  # 最新的在前面
        # 限制歷史記錄數量 (最多50筆)
        if len(history) > 50:
            history = history[:50]
        self.save_history(history)
        return history_item


# 全域歷史記錄服務實例
_history_service = None


def get_history_service():
    """獲取歷史記錄服務單例"""
    global _history_service
    if _history_service is None:
        _history_service = HistoryService()
    return _history_service
