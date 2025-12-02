# Z-Image-Turbo Web UI

> **v2.4.0** - AI 圖片生成 Web 應用 | 提示詞智能助手

基於 Flask 的專業 AI 圖片生成工具，使用 Z-Image-Turbo 模型，專為 12GB VRAM 優化。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Version](https://img.shields.io/badge/version-2.4.0-green.svg)

📚 **文檔導航**: [完整索引](DOCUMENTATION.md) | [快速參考](QUICK_REFERENCE.md) | [開發指南](DEVELOPMENT.md)

---

## ✨ 核心特色

### 基礎功能
- 🎨 現代化 Web 介面
- ⚡ 快速生成（5-8 秒/張）
- 💾 記憶體優化（~0.7GB GPU）
- 📜 歷史記錄自動保存
- 📥 批量下載 ZIP

### 進階功能（v2.0-v2.4）
- 🔢 批量生成（最多 20 張）
- 🎭 風格模板（50+ 種）
- 📐 尺寸預設（15+ 種）
- 🏷️ 標籤系統
- 🎲 Seed 控制
- 📝 文字疊加
- 📦 批量導出（PDF/PPT）
- 🗑️ 批量刪除
- 🤖 **提示詞智能助手**（v2.4 新增）

---

## 🚀 快速開始

### 安裝

```bash
# 1. 克隆專案
git clone <repository-url>
cd zImage

# 2. 安裝依賴
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install diffusers transformers accelerate pillow flask reportlab python-pptx

# 3. 啟動應用
python app.py

# 4. 訪問
# http://localhost:5001
```

> 首次啟動會下載約 21GB 模型文件

---

## 📖 主要功能

### 1. 提示詞智能助手 ✨ v2.4 新增

#### 自動完成建議
- 輸入時自動顯示關鍵字
- 400+ 專業關鍵字（7 大類別）
- 鍵盤導航：↑↓ 選擇，Enter 插入

#### AI 增強
- 點擊「增強提示詞」按鈕
- 自動添加品質關鍵字
- 智能優化提示詞結構

#### 快速範本（12 種）
- 人物：專業人像、動漫風格
- 風景：自然風景、城市場景
- 藝術：水彩畫、概念藝術
- 科幻：賽博龐克、太空
- 攝影：微距、美食
- 風格：極簡、復古

### 2. 批量生成
- 每行一個提示詞
- 最多 20 張
- 序列化處理（避免 OOM）
- ZIP 批量下載

### 3. 風格與尺寸
- 50+ 風格模板（7 大分類）
- 15+ 尺寸預設（社群/列印）
- 自訂尺寸（512-3508px）

### 4. Seed 控制
- 固定種子重現結果
- 隨機種子生成
- 適合參數調試

### 5. 批量操作
- 多選模式
- PDF 導出（單頁/雙欄/網格）
- PPT 導出（簡潔/專業/教學）
- 批量刪除（安全確認）

---

## 📡 API 端點（20 個）

### 基礎
- POST /generate - 單張生成
- GET /history - 歷史記錄
- DELETE /history - 清除歷史

### 批量
- POST /batch-generate - 批量生成
- POST /batch-download - ZIP 下載

### 模板
- GET /templates - 風格列表
- GET /size-presets - 尺寸列表

### 進階
- POST /seed-control - Seed 生成
- POST /add-text-overlay - 文字疊加
- POST /export-pdf - PDF 導出
- POST /export-ppt - PPT 導出
- POST /delete-images - 批量刪除

### 提示詞助手（v2.4）
- POST /prompt/suggestions - 自動完成
- POST /prompt/enhance - 增強提示詞
- GET /prompt/templates - 範本列表
- POST /prompt/apply-template - 應用範本

---

## 🔧 技術架構

### 後端
- Flask + Z-Image-Turbo + Diffusers
- Sequential CPU Offload 優化
- ~0.7GB GPU + ~20GB RAM
- 5-8 秒生成速度

### 前端
- Vanilla JavaScript（6 個模組）
- 2200+ 行 CSS
- 響應式布局

---

## ❓ 常見問題

**Q: 首次啟動很慢？**
A: 需下載 21GB 模型，下載後會緩存。

**Q: GPU 使用率低？**
A: 正常。Sequential CPU Offload 將大部分模型放在 RAM。

**Q: 如何提速？**
A: 減少步數或降低解析度。9 steps 是最佳平衡。

**Q: 批量生成會 OOM？**
A: 不會。序列化處理，一次一張。

**Q: 如何重現結果？**
A: 使用 Seed 控制，相同 Seed + 提示詞 = 相同結果。

---

## 📝 更新日誌

### v2.4.0 (2025-12-02)
- ✨ 提示詞智能助手
  - 自動完成（400+ 關鍵字）
  - AI 增強
  - 12 個範本
- ✅ +4 API 端點（總共 20 個）
- ✅ +440 行 JS
- ✅ +210 行 CSS

### v2.3.0 (2025-12-02)
- ✨ 批量刪除功能
- 🎨 UI/UX 優化
- ✅ +1 API 端點（16 個）

### v2.2.0 (2025-12-02)
- ✨ 批量導出（PDF/PPT）
- ✅ +2 API 端點（15 個）

### v2.1.0 (2025-12-02)
- ✨ 文字疊加功能
- ✅ +1 API 端點（13 個）

### v2.0.0 (2025-12-01)
- ✨ 批量生成、風格模板、尺寸預設、標籤系統、Seed 控制
- ✅ 12 API 端點

### v1.0.0 (2025-11-30)
- ✅ 基礎 Web 介面
- ✅ 單張生成
- ✅ VRAM 優化

---

## 📁 專案結構

```
zImage/
├── app.py                      # Flask 主程式
├── config.py                   # 配置
├── templates.json              # 風格模板
├── prompt_keywords.json        # 關鍵字庫
├── DEVELOPMENT.md              # 開發文檔
├── README.md                   # 本文件
├── templates/
│   └── index.html
├── static/
│   ├── css/style.css          # 2200+ 行
│   └── js/
│       ├── script.js
│       ├── templates.js
│       ├── advanced.js
│       ├── textOverlay.js
│       ├── exportManager.js
│       └── promptAssistant.js
└── generated_images/
```

---

## 🤝 貢獻與開發

- **用戶文檔**: 本文件（README.md）
- **開發文檔**: [DEVELOPMENT.md](DEVELOPMENT.md)
- **問題回報**: 歡迎提交 Issue
- **功能建議**: 歡迎 Pull Request

---

## 📄 授權

MIT License

---

**開發**: Claude Code
**版本**: v2.4.0
**日期**: 2025-12-02
