import torch
import os
from diffusers import ZImagePipeline

# 建立 D 槽的資料夾 (如果不存在的話)
cache_path = r"D:\AI_Cache\HuggingFace"  # 您可以自訂這個 D 槽路徑
os.makedirs(cache_path, exist_ok=True)

print(f"模型將下載並緩存至：{cache_path}")

# 1. 載入模型
# 建議使用 bfloat16 以獲得最佳效能 (RTX 30/40 系列顯卡支援良好)
# 如果是較舊的顯卡 (如 1080/2080)，請改用 torch.float16
print("正在載入模型...")


pipe = ZImagePipeline.from_pretrained(
    "Tongyi-MAI/Z-Image-Turbo",
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    cache_dir=cache_path,  # <--- 加入這一行指定路徑
    use_safetensors=True,
)

# 2. 硬體設定與優化
# 一般情況下移至 GPU
pipe.to("cuda")

# [顯存不足時的救星]
# 如果您的顯卡 VRAM 小於 16GB，請取消下面這一行的註解 (刪除 #)
# 這會讓模型層在 CPU 和 GPU 間切換，速度變慢但能省顯存
# pipe.enable_model_cpu_offload()

# [加速選項]
# 如果您有安裝 flash-attn 套件，可以取消註解以加速
# pipe.transformer.set_attention_backend("flash")

# 3. 設定提示詞 (Prompt)
# 這個模型支援中英文混雜，您可以試試看
prompt = "用圖文圖卡圖片 來說明存在主義，日式漫畫風格，請知名動漫角色來協助說明加強效果，也引用過去各界名人，說過的話或是範例，來詳細說明存在主義。"

print(f"開始生成：{prompt}")

# 4. 生成圖像
# Z-Image-Turbo 只需要 8-9 步 (num_inference_steps)
image = pipe(
    prompt=prompt,
    height=1024,
    width=1024,
    num_inference_steps=9,  # Turbo 版本設 9 步即可
    guidance_scale=0.0,     # Turbo 版本通常設為 0
    generator=torch.Generator("cuda").manual_seed(42), # 固定種子碼以便重現
).images[0]

# 5. 存檔
save_path = "professor_wind_turbine.png"
image.save(save_path)
print(f"圖片已儲存至：{save_path}")