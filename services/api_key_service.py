"""
API Key Service - API 金鑰管理服務
提供 API 金鑰的生成、驗證和管理功能，讓外部應用可以整合圖片生成功能
"""
import os
import json
import secrets
import hashlib
from datetime import datetime
from functools import wraps
from flask import request, jsonify
import config


API_KEYS_FILE = os.path.join(config.OUTPUT_PATH, "api_keys.json")


class APIKeyService:
    """API 金鑰管理服務"""

    def __init__(self):
        self.keys = self._load_keys()

    def _load_keys(self):
        """載入 API 金鑰"""
        if os.path.exists(API_KEYS_FILE):
            try:
                with open(API_KEYS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_keys(self):
        """儲存 API 金鑰"""
        try:
            os.makedirs(os.path.dirname(API_KEYS_FILE), exist_ok=True)
            with open(API_KEYS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.keys, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存 API 金鑰失敗: {e}")

    def _hash_key(self, key):
        """雜湊 API 金鑰"""
        return hashlib.sha256(key.encode()).hexdigest()

    def create_key(self, name, permissions=None):
        """建立新的 API 金鑰

        Args:
            name: 金鑰名稱/描述
            permissions: 允許的操作列表

        Returns:
            dict: 包含金鑰資訊（金鑰明文只在建立時顯示一次）
        """
        # 生成 API 金鑰: zimg_前綴 + 32字元隨機字串
        raw_key = f"zimg_{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(raw_key)
        key_prefix = raw_key[:12]  # 用於顯示識別

        default_permissions = ["generate", "history", "gallery"]
        key_info = {
            'name': name,
            'prefix': key_prefix,
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'permissions': permissions or default_permissions,
            'usage_count': 0,
            'is_active': True,
            'rate_limit': 60,  # 每分鐘請求次數上限
        }

        self.keys[key_hash] = key_info
        self._save_keys()

        return {
            'success': True,
            'api_key': raw_key,  # 只在建立時回傳明文
            'key_info': {**key_info, 'id': key_hash[:8]},
            'message': '請妥善保存此 API 金鑰，它不會再次顯示'
        }

    def validate_key(self, raw_key):
        """驗證 API 金鑰

        Returns:
            tuple: (is_valid, key_info)
        """
        if not raw_key:
            return False, None

        key_hash = self._hash_key(raw_key)
        key_info = self.keys.get(key_hash)

        if not key_info:
            return False, None

        if not key_info.get('is_active', True):
            return False, None

        # 更新使用統計
        key_info['last_used'] = datetime.now().isoformat()
        key_info['usage_count'] = key_info.get('usage_count', 0) + 1
        self._save_keys()

        return True, key_info

    def list_keys(self):
        """列出所有 API 金鑰（不包含雜湊值）"""
        result = []
        for key_hash, info in self.keys.items():
            result.append({
                'id': key_hash[:8],
                'name': info['name'],
                'prefix': info['prefix'],
                'created_at': info['created_at'],
                'last_used': info['last_used'],
                'permissions': info['permissions'],
                'usage_count': info['usage_count'],
                'is_active': info['is_active'],
                'rate_limit': info.get('rate_limit', 60)
            })
        return result

    def revoke_key(self, key_id_prefix):
        """撤銷 API 金鑰"""
        for key_hash, info in self.keys.items():
            if key_hash[:8] == key_id_prefix:
                info['is_active'] = False
                self._save_keys()
                return {'success': True, 'message': f'已撤銷金鑰: {info["name"]}'}
        return {'success': False, 'error': '金鑰不存在'}

    def delete_key(self, key_id_prefix):
        """刪除 API 金鑰"""
        for key_hash in list(self.keys.keys()):
            if key_hash[:8] == key_id_prefix:
                name = self.keys[key_hash]['name']
                del self.keys[key_hash]
                self._save_keys()
                return {'success': True, 'message': f'已刪除金鑰: {name}'}
        return {'success': False, 'error': '金鑰不存在'}

    def check_permission(self, raw_key, required_permission):
        """檢查金鑰是否有特定權限"""
        is_valid, key_info = self.validate_key(raw_key)
        if not is_valid:
            return False
        return required_permission in key_info.get('permissions', [])


# 全域單例
_api_key_service = None


def get_api_key_service():
    """取得 API 金鑰服務單例"""
    global _api_key_service
    if _api_key_service is None:
        _api_key_service = APIKeyService()
    return _api_key_service


def require_api_key(permission=None):
    """API 金鑰驗證裝飾器

    用法:
        @require_api_key('generate')
        def my_api_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 從 Header 或 Query Parameter 取得 API Key
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

            if not api_key:
                return jsonify({
                    'error': '需要 API 金鑰。請在 Header 中加入 X-API-Key 或使用 ?api_key= 參數',
                    'code': 'MISSING_API_KEY'
                }), 401

            service = get_api_key_service()
            is_valid, key_info = service.validate_key(api_key)

            if not is_valid:
                return jsonify({
                    'error': '無效的 API 金鑰',
                    'code': 'INVALID_API_KEY'
                }), 401

            if permission and permission not in key_info.get('permissions', []):
                return jsonify({
                    'error': f'此金鑰沒有 {permission} 權限',
                    'code': 'INSUFFICIENT_PERMISSIONS'
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
