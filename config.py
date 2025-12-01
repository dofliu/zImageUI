# 配置檔案 - 可以輕鬆調整解析度和優化設定

# ===========================
# 解析度配置 (選擇一個)
# ===========================

# 選項 1: 高品質 1024x1024 (需要 12-14GB VRAM,可能有溢出)
# IMAGE_HEIGHT = 1024
# IMAGE_WIDTH = 1024

# 選項 2: 平衡 768x768 (8-10GB VRAM,推薦!) ✅✅✅
IMAGE_HEIGHT = 768
IMAGE_WIDTH = 768

# 選項 3: 快速 512x512 (5-7GB VRAM,速度最快)
# IMAGE_HEIGHT = 512
# IMAGE_WIDTH = 512

# ===========================
# 模型優化設定
# ===========================

# CPU Offload 模式 (選擇一個)
# "sequential" - 最激進,VRAM 使用最少 (推薦)
# "model" - 較溫和,速度稍快但 VRAM 使用較多
CPU_OFFLOAD_MODE = "sequential"

# 是否啟用額外優化
ENABLE_ATTENTION_SLICING = True  # 減少注意力計算的 VRAM 使用
ENABLE_VAE_SLICING = True        # 減少 VAE 的 VRAM 使用
ENABLE_XFORMERS = False          # 需要安裝 xformers,速度更快

# ===========================
# 生成參數
# ===========================

# 生成步數 (Turbo 模型建議 9 步)
NUM_INFERENCE_STEPS = 9

# 引導比例 (Turbo 模型建議 0.0)
GUIDANCE_SCALE = 0.0

# ===========================
# 路徑設定
# ===========================

# 模型快取路徑
CACHE_PATH = r"D:\AI_Cache\HuggingFace"

# 生成圖片儲存路徑
OUTPUT_PATH = r"d:\Dropbox\Project_CodingSimulation\aiAgent\zImage\generated_images"

# ===========================
# 伺服器設定
# ===========================

HOST = "0.0.0.0"
PORT = 5000
DEBUG = True
USE_RELOADER = False  # 避免生成過程中重新載入

# ===========================
# 提示訊息
# ===========================

def print_config_info():
    """顯示當前配置資訊"""
    print("\n" + "="*60)
    print("當前配置")
    print("="*60)
    print(f"圖片解析度: {IMAGE_WIDTH}x{IMAGE_HEIGHT}")
    print(f"CPU Offload 模式: {CPU_OFFLOAD_MODE}")
    print(f"生成步數: {NUM_INFERENCE_STEPS}")
    print(f"注意力切片: {'啟用' if ENABLE_ATTENTION_SLICING else '停用'}")
    print(f"VAE 切片: {'啟用' if ENABLE_VAE_SLICING else '停用'}")
    print(f"xFormers: {'啟用' if ENABLE_XFORMERS else '停用'}")

    # 預估 VRAM 使用
    if IMAGE_HEIGHT >= 1024:
        vram_estimate = "12-14 GB (可能溢出)"
    elif IMAGE_HEIGHT >= 768:
        vram_estimate = "8-10 GB (推薦)"
    else:
        vram_estimate = "5-7 GB (最省)"

    print(f"預估 VRAM: {vram_estimate}")
    print("="*60 + "\n")
