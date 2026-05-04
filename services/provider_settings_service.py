"""
Provider Settings Service - 雲端 API Key 與 Provider 設定管理

將 API Key 儲存在本地 JSON 檔案中（不上傳任何地方）。
UI 可透過設定頁面讀寫這些 Key。
"""
import os
import json
from typing import Optional
import config

# 設定檔存放路徑
PROVIDER_SETTINGS_FILE = os.path.join(
    os.path.dirname(config.OUTPUT_PATH),
    "provider_settings.json"
)


class ProviderSettingsService:
    """雲端 Provider API Key 管理服務（單例）"""

    def __init__(self):
        self._settings = self._load()

    def _load(self) -> dict:
        if os.path.exists(PROVIDER_SETTINGS_FILE):
            try:
                with open(PROVIDER_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            'gemini': {'api_key': '', 'active_model': 'gemini-2.5-flash-image'},
            'openai': {'api_key': '', 'active_model': 'gpt-image-1'},
        }

    def _save(self):
        try:
            os.makedirs(os.path.dirname(PROVIDER_SETTINGS_FILE), exist_ok=True)
            with open(PROVIDER_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[!] 儲存 Provider 設定失敗: {e}")

    # ── 讀取 ──────────────────────────────────────────────────
    def get_api_key(self, provider_id: str) -> Optional[str]:
        return self._settings.get(provider_id, {}).get('api_key') or None

    def get_active_model(self, provider_id: str) -> Optional[str]:
        return self._settings.get(provider_id, {}).get('active_model') or None

    def get_all(self) -> dict:
        """回傳給前端顯示（遮蔽 Key 的中間部分）"""
        result = {}
        for pid, cfg in self._settings.items():
            key = cfg.get('api_key', '')
            masked = self._mask_key(key) if key else ''
            result[pid] = {
                'has_key': bool(key),
                'masked_key': masked,
                'active_model': cfg.get('active_model', ''),
            }
        return result

    def _mask_key(self, key: str) -> str:
        if len(key) <= 8:
            return '****'
        return key[:4] + '****' + key[-4:]

    # ── 寫入 ──────────────────────────────────────────────────
    def set_api_key(self, provider_id: str, api_key: str) -> dict:
        if provider_id not in ('gemini', 'openai'):
            return {'success': False, 'error': f'未知 Provider: {provider_id}'}
        if provider_id not in self._settings:
            self._settings[provider_id] = {}
        self._settings[provider_id]['api_key'] = api_key.strip()
        self._save()
        return {'success': True, 'message': f'{provider_id} API Key 已儲存'}

    def set_active_model(self, provider_id: str, model_id: str) -> dict:
        if provider_id not in self._settings:
            self._settings[provider_id] = {}
        self._settings[provider_id]['active_model'] = model_id
        self._save()
        return {'success': True, 'message': f'{provider_id} 模型已切換為 {model_id}'}

    def clear_api_key(self, provider_id: str) -> dict:
        if provider_id in self._settings:
            self._settings[provider_id]['api_key'] = ''
            self._save()
        return {'success': True, 'message': f'{provider_id} API Key 已清除'}


# ── 單例 ───────────────────────────────────────────────────────
_instance: Optional[ProviderSettingsService] = None


def get_provider_settings() -> ProviderSettingsService:
    global _instance
    if _instance is None:
        _instance = ProviderSettingsService()
    return _instance
