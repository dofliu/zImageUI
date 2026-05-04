"""
Base Provider - 所有圖片生成 Provider 的抽象基底類別

新增模型只需：
1. 在 providers/cloud/ 或 providers/local/ 建立新的 Provider 類別
2. 繼承 BaseProvider 並實作所有方法
3. 在 model_registry.py 的 CLOUD_MODELS 或 LOCAL_MODELS 清單加入設定
不需要動其他任何地方。
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseProvider(ABC):
    """所有圖片生成 Provider 的抽象基底類別"""

    # ── 基本識別 ──────────────────────────────────────────────
    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Provider 類型: 'local' 或 'cloud'"""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Provider 唯一識別碼，例如 'gemini', 'openai', 'local'"""

    # ── 設定狀態 ──────────────────────────────────────────────
    @abstractmethod
    def is_configured(self) -> bool:
        """是否已完成設定（local: 模型已載入；cloud: API Key 已填入）"""

    @abstractmethod
    def get_status(self) -> dict:
        """
        回傳 provider 目前狀態
        Returns:
            {
                'ready': bool,
                'message': str,   # 給 UI 顯示的說明
                'requires': str,  # 若未就緒，需要什麼（如 'api_key', 'model_load'）
            }
        """

    # ── 核心生成能力 ───────────────────────────────────────────
    def supports_text2img(self) -> bool:
        """是否支援文字生圖"""
        return True

    def supports_img2img(self) -> bool:
        """是否支援圖生圖"""
        return False

    def supports_inpainting(self) -> bool:
        """是否支援局部重繪（Inpainting）"""
        return False

    def supports_photo_editing(self) -> bool:
        """是否支援照片編輯類功能（Avatar Studio 功能需要）"""
        return False

    @abstractmethod
    def generate(self, prompt: str, width: int, height: int,
                 negative_prompt: Optional[str] = None,
                 seed: Optional[int] = None,
                 steps: Optional[int] = None,
                 guidance_scale: Optional[float] = None,
                 **kwargs) -> dict:
        """
        文字生圖

        Returns:
            {
                'success': bool,
                'base64': str,        # base64 圖片資料（不含 data:image/... 前綴）
                'mime_type': str,     # 例如 'image/png'
                'seed': int,
                'error': str,         # 失敗時才有
            }
        """

    def img2img(self, image_base64: str, prompt: str,
                strength: float = 0.7,
                width: Optional[int] = None,
                height: Optional[int] = None,
                negative_prompt: Optional[str] = None,
                seed: Optional[int] = None,
                **kwargs) -> dict:
        """
        圖生圖（預設拋出 NotImplementedError，有支援的 Provider 自行覆寫）

        Args:
            image_base64: 輸入圖片的 base64（不含 data: 前綴）
        Returns: 與 generate() 相同格式
        """
        raise NotImplementedError(f"{self.provider_id} 不支援圖生圖")

    def edit_photo(self, feature: str, image_base64: str,
                   image2_base64: Optional[str] = None,
                   mask_base64: Optional[str] = None,
                   params: Optional[dict] = None) -> dict:
        """
        Avatar Studio 照片編輯功能（雲端模型使用）

        Args:
            feature: 功能名稱，例如 'professional', 'anime', 'passport'...
            image_base64: 主圖片 base64
            image2_base64: 第二張圖片（fusion、duo 功能用）
            mask_base64: 遮罩圖（inpainting 用）
            params: 其他參數（如 background, attire, anime_style 等）
        Returns: 與 generate() 相同格式
        """
        raise NotImplementedError(f"{self.provider_id} 不支援照片編輯")

    # ── 模型資訊 ───────────────────────────────────────────────
    def get_capabilities(self) -> dict:
        """回傳此 Provider 的能力清單"""
        return {
            'text2img': self.supports_text2img(),
            'img2img': self.supports_img2img(),
            'inpainting': self.supports_inpainting(),
            'photo_editing': self.supports_photo_editing(),
        }

    def get_model_info(self) -> dict:
        """回傳給前端顯示用的模型資訊（子類別可覆寫擴充）"""
        return {
            'provider_type': self.provider_type,
            'provider_id': self.provider_id,
            'capabilities': self.get_capabilities(),
            'status': self.get_status(),
        }
