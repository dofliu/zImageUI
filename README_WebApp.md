# AI 圖片生成器 - 網頁版

這是一個基於 Z-Image-Turbo 模型的 AI 圖片生成網頁應用程式，提供優美的使用者介面。

## 功能特點

✨ **優美的網頁介面** - 深色主題，現代化設計
📝 **中英文支援** - 提示詞支援中英文混合輸入
🖼️ **即時顯示** - 生成的圖片立即顯示在網頁上
💾 **自動命名** - 檔案名稱自動加上日期時間 (格式: `generated_YYYYMMDD_HHMMSS.png`)
⬇️ **一鍵下載** - 可直接下載生成的圖片

## 專案結構

```
zImage/
├── app.py                      # Flask 主程式
├── imageGEN_Z.py              # 原始指令列版本
├── templates/
│   └── index.html             # 網頁模板
├── static/
│   ├── css/
│   │   └── style.css          # 樣式檔案
│   └── js/
│       └── script.js          # JavaScript 互動邏輯
└── generated_images/          # 生成的圖片儲存位置 (自動建立)
```

## 安裝需求

```bash
pip install flask torch diffusers
```

## 使用方法

### 1. 啟動伺服器

```bash
python app.py
```

### 2. 開啟瀏覽器

程式啟動後，在瀏覽器中開啟:

```
http://localhost:5000
```

或從其他裝置訪問 (需在同一網路):

```
http://[您的電腦IP]:5000
```

### 3. 生成圖片

1. 在輸入框中輸入您的圖片描述提示詞
2. 點擊「開始生成圖片」按鈕
3. 等待幾秒鐘
4. 圖片生成後會自動顯示在頁面上
5. 可以點擊「下載圖片」按鈕儲存圖片

## 提示詞範例

```
用圖文圖卡圖片來說明存在主義，日式漫畫風格，請知名動漫角色來協助說明加強效果
```

```
未來科技城市，賽博龐克風格，霓虹燈，夜景，高品質
```

```
可愛的貓咪，水彩畫風格，溫暖的色調
```

## 技術規格

- **模型**: Z-Image-Turbo (Tongyi-MAI)
- **圖片解析度**: 1024x1024
- **生成步數**: 9 步 (Turbo 優化)
- **硬體需求**: NVIDIA GPU (建議 8GB+ VRAM)
- **框架**: Flask + PyTorch + Diffusers

## 檔案儲存

所有生成的圖片會儲存在 `generated_images/` 資料夾中，檔案命名格式為:

```
generated_20251201_143052.png
```

年月日_時分秒 的格式，確保每個檔案名稱唯一。

## 快捷鍵

- **Enter** - 快速生成圖片
- **Shift + Enter** - 在輸入框換行

## 注意事項

1. 第一次執行時會自動下載模型 (約 5-10 GB)
2. 模型會快取在 `D:\AI_Cache\HuggingFace`
3. 確保顯卡驅動程式和 CUDA 已正確安裝
4. 如果顯存不足，可在 `app.py` 中啟用 `enable_model_cpu_offload()`

## 故障排除

### 顯存不足

在 `app.py` 的 `initialize_model()` 函數中，找到這行並取消註解:

```python
pipe.enable_model_cpu_offload()
```

### 模型載入失敗

確認網路連線正常，模型會從 Hugging Face 下載。

### 網頁無法訪問

檢查防火牆設定，確保 5000 埠沒有被封鎖。

## 授權

本專案使用 Z-Image-Turbo 模型，請遵守相關使用條款。
