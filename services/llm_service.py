"""
LLM Service - 本地大語言模型管理服務
使用 llama-cpp-python 載入 GGUF 格式模型
"""
import os
import glob
from typing import Optional, List, Dict
import config

# 嘗試導入 llama-cpp-python，若未安裝則提供友善提示
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    Llama = None


class LLMService:
    """本地 LLM 管理類"""
    
    def __init__(self):
        self.model: Optional[Llama] = None
        self.current_model_path: Optional[str] = None
        self.model_cache_path = config.LLM_CACHE_PATH
        os.makedirs(self.model_cache_path, exist_ok=True)
    
    def is_available(self) -> bool:
        """檢查 llama-cpp-python 是否可用"""
        return LLAMA_CPP_AVAILABLE
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """掃描快取目錄，回傳可用的 GGUF 模型清單"""
        models = []
        pattern = os.path.join(self.model_cache_path, "*.gguf")
        for filepath in glob.glob(pattern):
            filename = os.path.basename(filepath)
            # 從檔名推斷模型名稱 (移除 .gguf 副檔名)
            model_name = filename.replace(".gguf", "").replace("-", " ").replace("_", " ")
            models.append({
                "id": filename,
                "name": model_name.title(),
                "path": filepath,
                "size_gb": round(os.path.getsize(filepath) / (1024**3), 2)
            })
        return models
    
    def load_model(self, model_filename: str) -> bool:
        """載入指定的 GGUF 模型
        
        Args:
            model_filename: 模型檔案名稱 (例如 qwen2.5-7b-instruct-q4_k_m.gguf)
            
        Returns:
            bool: 是否成功載入
        """
        if not LLAMA_CPP_AVAILABLE:
            print("❌ llama-cpp-python 未安裝，無法載入本地 LLM")
            return False
        
        model_path = os.path.join(self.model_cache_path, model_filename)
        
        if not os.path.exists(model_path):
            print(f"❌ 找不到模型檔案: {model_path}")
            return False
        
        # 如果已經載入相同模型，跳過
        if self.current_model_path == model_path and self.model is not None:
            print(f"✓ 模型已在記憶體中: {model_filename}")
            return True
        
        # 卸載舊模型
        if self.model is not None:
            print("⟳ 卸載舊模型...")
            del self.model
            self.model = None
            import gc
            gc.collect()
        
        print(f"⟳ 載入模型: {model_filename}")
        print(f"  GPU 層數: {config.LLM_GPU_LAYERS}")
        
        try:
            self.model = Llama(
                model_path=model_path,
                n_ctx=config.LLM_CONTEXT_LENGTH,
                n_gpu_layers=config.LLM_GPU_LAYERS,
                verbose=False,
            )
            self.current_model_path = model_path
            print(f"✓ 模型載入成功!")
            return True
        except Exception as e:
            print(f"❌ 模型載入失敗: {e}")
            return False
    
    def unload_model(self):
        """卸載當前模型以釋放顯存"""
        if self.model is not None:
            print("⟳ 卸載 LLM 模型...")
            del self.model
            self.model = None
            self.current_model_path = None
            import gc
            gc.collect()
            print("✓ LLM 模型已卸載")
    
    def generate_prompt(self, idea: str, style: str = "通用") -> str:
        """將簡單想法擴展為詳細的圖片生成提示詞
        
        Args:
            idea: 使用者的簡單想法 (例如「太空中的貓」)
            style: 風格偏好 (例如「寫實」、「動漫」、「油畫」)
            
        Returns:
            str: 詳細的圖片生成提示詞
        """
        if self.model is None:
            return f"❌ 尚未載入 LLM 模型。請先選擇並載入一個模型。"
        
        system_prompt = """You are an expert AI image prompt engineer. Your task is to expand a simple idea into a detailed, high-quality prompt for Stable Diffusion or similar image generation models.

Rules:
1. Output ONLY the prompt in English, no explanations
2. Include details about: subject, composition, lighting, colors, style, mood, quality tags
3. Use comma-separated descriptive phrases
4. Add quality boosters like: masterpiece, best quality, highly detailed, 8k, professional
5. Keep prompts under 200 words"""

        user_message = f"Expand this idea into a detailed image generation prompt. Style preference: {style}\n\nIdea: {idea}"
        
        try:
            response = self.model.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=config.LLM_MAX_TOKENS,
                temperature=0.7,
            )
            
            generated_text = response["choices"][0]["message"]["content"]
            return generated_text.strip()
        except Exception as e:
            return f"❌ 生成失敗: {e}"
    
    def chat(self, message: str, system_prompt: Optional[str] = None) -> str:
        """通用聊天功能
        
        Args:
            message: 使用者訊息
            system_prompt: 可選的系統提示詞
            
        Returns:
            str: 模型回覆
        """
        if self.model is None:
            return "❌ 尚未載入 LLM 模型。請先選擇並載入一個模型。"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        try:
            response = self.model.create_chat_completion(
                messages=messages,
                max_tokens=config.LLM_MAX_TOKENS,
                temperature=0.7,
            )
            
            generated_text = response["choices"][0]["message"]["content"]
            return generated_text.strip()
        except Exception as e:
            return f"❌ 生成失敗: {e}"


# 全域 LLM 服務實例
_llm_service = None


def get_llm_service() -> LLMService:
    """獲取 LLM 服務單例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
