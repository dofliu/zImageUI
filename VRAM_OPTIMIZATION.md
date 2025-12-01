# VRAM 優化完全指南 - 消除共用記憶體溢出

## 🔍 問題分析

您的 GPU 狀態:
```
專屬 GPU 記憶體: 11.7/12.0 GB (98% 使用)
共用 GPU 記憶體: 1.8/15.8 GB (溢出到系統 RAM)
總使用: 13.5 GB
```

**問題**: 即使使用 CPU Offload,仍有約 1.8GB 溢出到系統記憶體,導致速度變慢。

## ✅ 已實施的優化 (Level 1)

### 1. Sequential CPU Offload (最激進)
```python
pipe.enable_sequential_cpu_offload()
```

**比較**:
- `enable_model_cpu_offload()`: 模型層級的卸載
- `enable_sequential_cpu_offload()`: **更激進**,序列化卸載,只保留當前步驟在 GPU

**預期效果**: 降低 2-3GB VRAM 使用

### 2. GPU 快取清理
```python
torch.cuda.empty_cache()  # 每次生成前清理
```

### 3. CPU Generator
```python
generator=torch.Generator("cpu")  # 避免 GPU 分配
```

## 🚀 進階優化方案

如果上述優化後仍有溢出,請依序嘗試:

### Level 2: 降低圖片解析度

編輯 `app.py` 第 105-106 行:

```python
# 從 1024x1024 降到 768x768 (減少 ~30% VRAM)
height=768,
width=768,
```

或者更激進:
```python
# 降到 512x512 (減少 ~60% VRAM)
height=512,
width=512,
```

**VRAM 使用比較**:
- 1024x1024: ~12-14 GB
- 768x768: ~8-10 GB ✅
- 512x512: ~5-7 GB ✅✅

### Level 3: 使用 float16 代替 bfloat16

編輯 `app.py` 第 37 行:

```python
# 原本
torch_dtype=torch.bfloat16,

# 改為 (可減少約 10-15% VRAM)
torch_dtype=torch.float16,
```

**注意**: float16 在某些顯卡上可能數值不穩定,如果出現黑圖或異常請改回 bfloat16。

### Level 4: 啟用注意力切片 (Attention Slicing)

在 `initialize_model()` 中添加:

```python
# 在 enable_sequential_cpu_offload() 之後添加
if hasattr(pipe, 'enable_attention_slicing'):
    pipe.enable_attention_slicing(1)  # 或 "auto"
    print("✓ 已啟用 Attention Slicing")
```

這會將注意力計算分片,減少峰值 VRAM 使用。

### Level 5: VAE Slicing (如果支援)

```python
# 在 initialize_model() 中添加
if hasattr(pipe, 'enable_vae_slicing'):
    pipe.enable_vae_slicing()
    print("✓ 已啟用 VAE Slicing")
```

## 📝 完整優化配置

### 方案 A: 保持 1024 解析度 (激進優化)

在 `initialize_model()` 函數中的 `enable_sequential_cpu_offload()` 之後添加:

```python
# 啟用所有可用的優化
optimizations = []

# 1. Attention Slicing
if hasattr(pipe, 'enable_attention_slicing'):
    pipe.enable_attention_slicing("auto")
    optimizations.append("Attention Slicing")

# 2. VAE Slicing
if hasattr(pipe, 'enable_vae_slicing'):
    pipe.enable_vae_slicing()
    optimizations.append("VAE Slicing")

# 3. Memory Efficient Attention
if hasattr(pipe, 'enable_xformers_memory_efficient_attention'):
    try:
        pipe.enable_xformers_memory_efficient_attention()
        optimizations.append("xFormers Attention")
    except:
        pass

if optimizations:
    print(f"✓ 已啟用額外優化: {', '.join(optimizations)}")
```

### 方案 B: 降低解析度 (穩定方案) ✅ 推薦

修改生成參數:

```python
image = pipe(
    prompt=prompt,
    height=768,   # 從 1024 降到 768
    width=768,    # 從 1024 降到 768
    num_inference_steps=9,
    guidance_scale=0.0,
    generator=torch.Generator("cpu").manual_seed(seed),
).images[0]
```

**優點**:
- ✅ VRAM 使用降至 8-10 GB
- ✅ 完全避免溢出
- ✅ 生成速度更快 (約 5-8 秒)
- ✅ 品質仍然很好

## 🔧 實用工具腳本

創建一個測試腳本來找出最佳配置:

```python
# test_vram_usage.py
import torch
import gc

def check_vram():
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0) / (1024**3)
        reserved = torch.cuda.memory_reserved(0) / (1024**3)
        total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"VRAM: 已分配 {allocated:.2f}GB | 已保留 {reserved:.2f}GB | 總計 {total:.2f}GB")
        return reserved
    return 0

# 測試不同解析度的 VRAM 使用
resolutions = [512, 768, 1024]
for res in resolutions:
    torch.cuda.empty_cache()
    gc.collect()
    print(f"\n測試解析度: {res}x{res}")
    # 在這裡執行生成並檢查 VRAM
    check_vram()
```

## 🎯 推薦配置 (12GB VRAM)

根據您的 RTX 4080 Laptop (12GB),推薦配置:

### 選項 1: 768x768 (平衡) ✅✅✅
```python
height=768, width=768
+ Sequential CPU Offload
+ GPU Cache Cleaning
```
- VRAM: ~8-10 GB (完全在專屬記憶體內)
- 速度: 5-8 秒/張
- 品質: 優秀

### 選項 2: 1024x1024 (高品質)
```python
height=1024, width=1024
+ Sequential CPU Offload
+ Attention Slicing
+ VAE Slicing (如果支援)
```
- VRAM: ~10-12 GB (可能輕微溢出)
- 速度: 10-15 秒/張
- 品質: 最佳

### 選項 3: 512x512 (極速)
```python
height=512, width=512
+ Sequential CPU Offload
```
- VRAM: ~5-7 GB
- 速度: 3-5 秒/張
- 品質: 良好 (適合草圖或快速預覽)

## 📊 優化效果對比

| 配置 | VRAM 使用 | 溢出 | 速度 | 推薦度 |
|------|-----------|------|------|--------|
| **原始 (pipe.to cuda)** | 21GB | ❌❌❌ 嚴重 | 30-60s | ❌ |
| **Model CPU Offload** | 13.5GB | ❌ 輕微 (1.8GB) | 15-20s | ⚠️ |
| **Sequential CPU Offload** | 11-12GB | ⚠️ 邊緣 | 10-15s | ⚠️ |
| **Sequential + 768** | 8-10GB | ✅ 無 | 5-8s | ✅✅✅ |
| **Sequential + 512** | 5-7GB | ✅ 無 | 3-5s | ✅✅ |

## 💡 終極建議

### 立即可行的最佳方案:

1. **修改 app.py 兩處**:

```python
# 第 48 行 - 改用 Sequential
pipe.enable_sequential_cpu_offload()

# 第 105-106 行 - 降低解析度
height=768,
width=768,
```

2. **重新啟動伺服器**:
```bash
python app.py
```

3. **生成一張圖片並檢查**:
   - 打開工作管理員 → 效能 → GPU
   - 查看「共用 GPU 記憶體」是否還有溢出
   - 如果仍有溢出,再降到 512x512

### 如果需要 1024 解析度

只在必要時生成 1024,平時用 768:
- 可以在網頁添加解析度選擇器
- 或者準備兩個啟動配置

## 🔍 監控命令

```bash
# 持續監控 GPU 使用
nvidia-smi -l 1

# 或使用 Python
watch -n 1 python check_model_cache.py
```

## ✅ 總結

**消除溢出的最有效方法**: 降低解析度到 768x768

這樣可以:
- ✅ 完全消除共用記憶體溢出
- ✅ 提升生成速度 (5-8 秒)
- ✅ 保持優秀的圖片品質
- ✅ GPU 使用率更穩定

試試看吧! 🚀
