# Z-Image-Turbo Web UI

> **v2.1.0** - 功能強大的 AI 圖片生成 Web 應用

一個基於 Flask 的專業 Web 介面,用於 Z-Image-Turbo 文字轉圖片 AI 模型。
專為 12GB VRAM 顯卡優化,支援批量生成、風格模板、標籤管理等進階功能。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-red.svg)
![Version](https://img.shields.io/badge/version-2.0.0-green.svg)

## ✨ 核心特色

### 🚀 基礎功能
- 🎨 **美觀的 Web 介面** - 現代化漸層設計,響應式布局
- ⚡ **快速生成** - Sequential CPU Offload 優化,5-8 秒生成圖片
- 💾 **記憶體優化** - 專為 12GB VRAM 設計,僅使用 ~0.7GB GPU 記憶體
- 📜 **歷史記錄** - 自動保存生成歷史,可查看過去的提示詞和圖片
- 📥 **一鍵下載** - 直接下載生成的圖片
- 🔄 **即時預覽** - 側邊欄布局,提示詞和圖片同時可見

### 🎯 進階功能 (v2.0-v2.1 新增)
- 🔢 **批量生成** - 一次生成最多 20 張圖片,ZIP 批量下載
- 🎭 **風格模板** - 50+ 專業風格,7 大分類快速選擇
- 📐 **尺寸預設** - 15+ 社群/列印尺寸,一鍵切換
- 🏷️ **標籤系統** - 為圖片添加標籤,智能分類與過濾
- 🎲 **Seed 控制** - 固定種子重現結果,便於調試優化
- 📝 **文字疊加** - 在圖片上添加標題與說明,支援中文字體

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

## 💡 功能使用指南

### 🔢 批量生成模式
1. 點擊「批量生成」切換模式
2. 每行輸入一個提示詞（最多 20 個）
3. 點擊「開始批量生成」
4. 查看網格結果
5. 點擊「下載全部 (ZIP)」批量下載

### 🎭 使用風格模板
1. 在「風格模板」下拉選單中選擇風格
2. 系統自動將風格關鍵字組合到提示詞
3. 50+ 風格可選：
   - **藝術風格**: 水彩、油畫、素描、水墨、浮世繪、印象派
   - **現代風格**: 賽博龐克、極簡、復古、蒸汽龐克、波普
   - **動漫風格**: 吉卜力、日式、迪士尼、像素、漫畫
   - **教學模板**: 科學圖解、歷史場景、文學插圖等

### 📐 選擇圖片尺寸
1. 在「圖片尺寸」選單中選擇預設尺寸
2. 社群媒體: Instagram、Facebook、YouTube 等
3. 列印尺寸: A4、A5、明信片
4. 標準尺寸: 512²、768²、1024²

### 🏷️ 標籤管理
1. 在側邊欄查看標籤雲（顯示所有標籤和使用次數）
2. 點擊標籤進行過濾（可多選）
3. 點擊「清除篩選」按鈕恢復顯示全部
4. 為生成的圖片添加自定義標籤

### 🎲 Seed 控制
1. 在提示詞輸入區域勾選「使用固定種子」
2. 輸入 Seed 值或點擊 🎲 按鈕生成隨機 Seed
3. 使用相同 Seed 和提示詞可重現完全相同的結果
4. Seed 值會顯示在檔案名稱中 (seed_{seed}_{timestamp}.png)

### 📝 文字疊加
1. 生成圖片後，會自動顯示「添加文字」編輯器
2. 輸入要疊加的文字（最多 100 字）
3. 選擇文字位置（頂部/中間/底部）
4. 選擇文字顏色（白色/黑色）
5. 勾選「背景遮罩」增加文字可讀性
6. 點擊「套用文字」生成帶文字的新圖片
7. 可重複疊加多次文字

**使用場景**：
- 教學教材標題
- 社群媒體圖文
- 簡報封面製作
- 圖片說明文字

### VRAM 優化

本專案針對 12GB VRAM 進行了優化:

1. **Sequential CPU Offload** - 模型保存在 RAM，按需載入 GPU
2. **Attention Slicing** - 分批處理注意力計算
3. **VAE Slicing** - 分批處理 VAE 解碼

**性能指標:**
- GPU 記憶體: ~0.7GB
- 系統 RAM: ~20GB (模型快取)
- 生成速度: 5-8 秒/張 (768×768, 9 steps)
- 批量生成: 支援最多 20 張

### 提示詞建議

**基礎提示詞:**
```
一隻貓咪坐在窗邊,溫暖的陽光
未來城市的夜景,霓虹燈閃爍
森林中的小木屋,秋天的氛圍
```

**配合風格模板:**
```
基礎提示詞: 一隻貓咪坐在窗邊
選擇風格: 水彩畫
→ 系統自動組合: 一隻貓咪坐在窗邊, watercolor style, soft colors, flowing
```

## 📁 專案結構

```
zImageUI/
├── app.py                      # Flask 主程式 (已升級 v2.1)
├── config.py                   # 配置文件
├── templates.json              # 風格模板資料庫 (50+ 風格)
├── claude.md                   # 開發計劃文檔
├── todo.md                     # 任務清單
├── FEATURES.md                 # 功能詳細說明
├── imageGEN_Z.py              # 原始命令列版本
├── check_model_cache.py       # 模型快取檢查工具
├── templates/
│   └── index.html             # 網頁介面 (已升級 v2.1)
├── static/
│   ├── css/
│   │   └── style.css          # 樣式表 (1500+ 行)
│   └── js/
│       ├── script.js          # 主 JavaScript (已升級)
│       ├── templates.js       # 風格/尺寸選擇器
│       ├── advanced.js        # 標籤/Seed 功能
│       └── textOverlay.js     # 文字疊加功能 (新增)
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

## 📡 API 端點

### 基礎功能
- `POST /generate` - 單張圖片生成
- `GET /history` - 獲取歷史記錄
- `DELETE /history` - 清除歷史記錄
- `GET /images/<filename>` - 圖片訪問

### 批量功能
- `POST /batch-generate` - 批量生成 (最多 20 張)
- `POST /batch-download` - ZIP 批量下載

### 模板與預設
- `GET /templates` - 風格模板列表
- `GET /size-presets` - 尺寸預設列表

### 進階功能
- `GET /tags` - 獲取所有標籤與使用統計
- `POST /history/<id>/tags` - 更新歷史記錄標籤
- `POST /history/filter` - 根據標籤過濾歷史
- `POST /seed-control` - 使用固定 Seed 生成
- `POST /add-text-overlay` - 在圖片上添加文字疊加

**共 13 個 API 端點**

詳細 API 說明請參考 [FEATURES.md](FEATURES.md)

## 📚 相關文件

- [FEATURES.md](FEATURES.md) - 完整功能說明與使用指南
- [claude.md](claude.md) - 開發計劃與技術架構
- [todo.md](todo.md) - 任務追蹤清單

## ⚠️ 常見問題

### Q: 首次啟動很慢?
A: 首次啟動會從 Hugging Face 下載約 21GB 的模型,這是正常的。下載完成後會快取在本地,之後啟動只需幾秒鐘。

### Q: GPU 記憶體使用率很低?
A: 這是正常的!使用 Sequential CPU Offload 時,大部分模型保存在 RAM 中,GPU 僅在計算時使用。這樣可以避免記憶體溢出。

### Q: 如何提高生成速度?
A: 可以減少 `NUM_INFERENCE_STEPS` (但會降低品質) 或降低解析度。9 steps 是速度和品質的最佳平衡點。

### Q: 支援批量生成嗎?
A: v2.0 已支援批量生成!點擊「批量生成」模式,每行輸入一個提示詞,最多可一次生成 20 張圖片,並支援 ZIP 批量下載。

### Q: 如何使用風格模板?
A: 在介面上方選擇「風格模板」下拉選單,選擇您想要的風格,系統會自動將風格關鍵字組合到您的提示詞中。

### Q: 如何重現相同的圖片?
A: 使用 Seed 控制功能!勾選「使用固定種子」並輸入相同的 Seed 值和提示詞,就能重現完全相同的結果。

### Q: 如何更改輸出目錄?
A: 編輯 `config.py` 中的 `OUTPUT_PATH` 設定。

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request!

## 📄 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 文件

## 📝 更新日誌

### v2.1.0 (2025-12-02)
- ✅ **新增文字疊加功能**
  - 在圖片上添加標題與說明文字
  - 支援中文字體 (微軟雅黑/微軟正黑體)
  - 3 種位置選擇 (頂部/中間/底部)
  - 2 種顏色選擇 (白色/黑色)
  - 半透明背景遮罩選項
  - 折疊式編輯器 UI
  - 可重複疊加文字
- ✅ 新增 textOverlay.js 模組
- ✅ 新增 `/add-text-overlay` API 端點
- ✅ 新增 200+ 行 CSS 樣式
- ✅ 總共 13 個 API 端點

### v2.0.0 (2025-12-01)
- ✅ 新增批量生成模式 (最多 20 張)
- ✅ 新增 50+ 風格模板系統 (7 大分類)
- ✅ 新增 15+ 尺寸預設 (社群/列印/標準)
- ✅ 新增標籤管理系統 (完整功能)
- ✅ 新增 Seed 固定控制 (完整功能)
- ✅ 優化模組化代碼結構
- ✅ 完善 API 端點 (12 個端點)
- ✅ 前端 UI 完全整合

### v1.0.0 (2025-11-30)
- ✅ 基礎 Web 介面
- ✅ 單張圖片生成
- ✅ 歷史記錄功能
- ✅ VRAM 優化 (Sequential CPU Offload)
- ✅ 側邊欄布局設計

## 🙏 致謝

- [Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo) - Tongyi-MAI 提供的優秀文字轉圖片模型
- [Diffusers](https://github.com/huggingface/diffusers) - Hugging Face 的擴散模型函式庫
- [Flask](https://flask.palletsprojects.com/) - 輕量級 Web 框架

## 📧 聯絡方式

如有問題或建議,請透過 GitHub Issues 聯繫。

---

**享受 AI 圖片生成的樂趣! 🎨✨**
