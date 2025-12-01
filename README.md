# Z-Image-Turbo Web UI

一個基於 Flask 的美觀 Web 介面,用於 Z-Image-Turbo 文字轉圖片 AI 模型,專為 12GB VRAM 顯卡優化。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-red.svg)

## ✨ 特色功能

- 🎨 **美觀的 Web 介面** - 現代化漸層設計,響應式布局
- ⚡ **快速生成** - Sequential CPU Offload 優化,5-8 秒生成圖片
- 💾 **記憶體優化** - 專為 12GB VRAM 設計,僅使用 ~0.7GB GPU 記憶體
- 📜 **歷史記錄** - 自動保存生成歷史,可查看過去的提示詞和圖片
- 📥 **一鍵下載** - 直接下載生成的圖片
- 🔄 **即時預覽** - 側邊欄布局,提示詞和圖片同時可見
- ⏰ **時間戳命名** - 自動以日期時間命名檔案

## 🖼️ 介面預覽

### 主介面
- **左側欄**: 提示詞輸入區 + 歷史記錄
- **右側區**: 圖片生成結果顯示

### 功能區塊
- 即時字數統計 (最多 500 字)
- 生成按鈕與狀態顯示
- 縮圖歷史記錄列表
- 下載與重新生成功能

## 🚀 快速開始

### 系統需求

- Python 3.8 或更高版本
- NVIDIA GPU (建議 12GB VRAM)
- CUDA 支援
- 約 21GB 硬碟空間 (用於模型快取)

### 安裝步驟

1. **克隆專案**
```bash
git clone https://github.com/dofliu/zImageUI.git
cd zImageUI
```

2. **安裝依賴套件**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install diffusers transformers accelerate flask pillow
```

3. **首次運行 (下載模型)**
```bash
python app.py
```

首次運行會自動從 Hugging Face 下載模型 (約 21GB),請耐心等待。模型會快取在 `cache/` 目錄中,之後啟動會非常快速。

4. **開啟瀏覽器**
```
http://localhost:5000
```

## ⚙️ 配置說明

編輯 `config.py` 來調整設定:

```python
# 圖片設定
IMAGE_WIDTH = 768          # 圖片寬度
IMAGE_HEIGHT = 768         # 圖片高度
NUM_INFERENCE_STEPS = 9    # 推理步數 (更多步數 = 更高品質但更慢)
GUIDANCE_SCALE = 0.0       # 引導比例

# 記憶體優化
CPU_OFFLOAD_MODE = "sequential"  # CPU 卸載模式
ENABLE_ATTENTION_SLICING = True  # 注意力切片
ENABLE_VAE_SLICING = True        # VAE 切片

# 伺服器設定
HOST = "0.0.0.0"          # 監聽地址
PORT = 5000               # 連接埠
DEBUG = False             # 除錯模式
```

## 💡 使用技巧

### VRAM 優化選項

本專案針對 12GB VRAM 進行了優化,使用以下技術:

1. **Sequential CPU Offload** - 將模型保存在 RAM 中,僅在需要時載入到 GPU
2. **Attention Slicing** - 分批處理注意力計算,降低記憶體峰值
3. **VAE Slicing** - 分批處理 VAE 解碼,進一步降低記憶體使用

**記憶體使用情況:**
- GPU 記憶體: ~0.7GB
- 系統 RAM: ~20GB (模型快取)
- 生成速度: 5-8 秒/張 (768×768, 9 steps)

### 提示詞建議

- 使用中文或英文描述
- 可以指定藝術風格 (如:水彩、油畫、賽博龐克等)
- 詳細描述會得到更好的結果
- 最多 500 個字元

**範例提示詞:**
```
以水彩風格,畫出一副淡水夕陽照
賽博龐克風格的未來城市,霓虹燈閃爍
油畫風格的貓咪肖像,溫暖的光線
```

## 📁 專案結構

```
zImageUI/
├── app.py                      # Flask 主程式
├── config.py                   # 配置文件
├── imageGEN_Z.py              # 原始命令列版本
├── check_model_cache.py       # 模型快取檢查工具
├── templates/
│   └── index.html             # 網頁介面
├── static/
│   ├── css/
│   │   └── style.css          # 樣式表
│   └── js/
│       └── script.js          # JavaScript 程式
├── cache/                      # 模型快取目錄 (自動生成)
├── generated_images/           # 生成圖片儲存目錄 (自動生成)
└── README.md                   # 本文件
```

## 🔧 進階功能

### 檢查模型快取

```bash
python check_model_cache.py
```

這個工具會顯示模型快取的詳細資訊,包括檔案大小和載入時間。

### 命令列版本

如果您想使用原始的命令列版本:

```bash
python imageGEN_Z.py
```

## 📚 相關文件

- [12GB_VRAM_GUIDE.md](12GB_VRAM_GUIDE.md) - 12GB VRAM 優化指南
- [VRAM_OPTIMIZATION.md](VRAM_OPTIMIZATION.md) - VRAM 優化詳細說明
- [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) - 一般優化建議
- [QUICK_START.md](QUICK_START.md) - 快速開始指南

## ⚠️ 常見問題

### Q: 首次啟動很慢?
A: 首次啟動會從 Hugging Face 下載約 21GB 的模型,這是正常的。下載完成後會快取在本地,之後啟動只需幾秒鐘。

### Q: GPU 記憶體使用率很低?
A: 這是正常的!使用 Sequential CPU Offload 時,大部分模型保存在 RAM 中,GPU 僅在計算時使用。這樣可以避免記憶體溢出。

### Q: 如何提高生成速度?
A: 可以減少 `NUM_INFERENCE_STEPS` (但會降低品質) 或降低解析度。9 steps 是速度和品質的最佳平衡點。

### Q: 支援批量生成嗎?
A: 目前版本不支援批量生成,但可以透過歷史記錄功能快速重複生成。

### Q: 如何更改輸出目錄?
A: 編輯 `config.py` 中的 `OUTPUT_PATH` 設定。

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request!

## 📄 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 文件

## 🙏 致謝

- [Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo) - Tongyi-MAI 提供的優秀文字轉圖片模型
- [Diffusers](https://github.com/huggingface/diffusers) - Hugging Face 的擴散模型函式庫
- [Flask](https://flask.palletsprojects.com/) - 輕量級 Web 框架

## 📧 聯絡方式

如有問題或建議,請透過 GitHub Issues 聯繫。

---

**享受 AI 圖片生成的樂趣! 🎨✨**
