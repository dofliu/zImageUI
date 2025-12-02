# Z-Image-Turbo Web UI - 開發文檔

> 開發者指南與技術架構文檔

---

## 📊 當前狀態 (v2.4.0)

### 完成功能
1. ✅ 基礎生成系統 (v1.0)
2. ✅ 批量生成模式 (v2.0)
3. ✅ 風格模板系統 (v2.0) - 50+ 風格
4. ✅ 尺寸預設系統 (v2.0) - 15+ 尺寸
5. ✅ 標籤管理系統 (v2.0)
6. ✅ Seed 固定控制 (v2.0)
7. ✅ 文字疊加功能 (v2.1)
8. ✅ 批量導出功能 (v2.2) - PDF + PPT
9. ✅ 批量刪除功能 (v2.3)
10. ✅ 提示詞智能助手 (v2.4) ⭐ 最新

### 技術指標
- **API 端點**: 20 個
- **JavaScript**: 6 個模組，2000+ 行
- **CSS**: 2200+ 行
- **Python**: 1200+ 行
- **關鍵字庫**: 400+ 個
- **提示詞範本**: 12 個

---

## 🏗️ 技術架構

### 後端架構 (Flask + PyTorch)

```
app.py (主程式)
├── 模型管理
│   ├── Z-Image-Turbo (Diffusers)
│   ├── Sequential CPU Offload
│   ├── Attention Slicing
│   └── VAE Slicing
├── API 路由（20 個端點）
│   ├── 基礎生成 (4 個)
│   ├── 批量操作 (2 個)
│   ├── 模板系統 (2 個)
│   ├── 標籤系統 (3 個)
│   ├── 進階功能 (5 個)
│   └── 提示詞助手 (4 個)
└── 數據管理
    ├── history.json
    ├── templates.json
    └── prompt_keywords.json
```

### 前端架構 (JavaScript 模組化)

```
static/js/
├── script.js           # 主腳本（核心邏輯）
├── templates.js        # 風格/尺寸選擇器
├── advanced.js         # 標籤/Seed 控制
├── textOverlay.js      # 文字疊加
├── exportManager.js    # 批量導出/刪除
└── promptAssistant.js  # 提示詞助手（v2.4）
```

### VRAM 優化策略

```python
# Sequential CPU Offload - 核心優化
pipe.enable_sequential_cpu_offload()

# 其他優化
pipe.enable_attention_slicing()
pipe.enable_vae_slicing()

# 結果
- GPU: ~0.7GB（12GB 僅使用 6%）
- RAM: ~20GB（模型存放）
- 速度: 5-8 秒/張（768×768, 9 steps）
```

---

## 📋 API 設計規範

### 命名規範
- **資源型**: `/resource` (GET/POST/DELETE)
- **操作型**: `/action-verb` (POST)
- **嵌套型**: `/parent/<id>/child` (GET/POST)

### 響應格式
```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "error": null
}
```

### 完整端點列表

#### 基礎生成
1. `POST /generate` - 單張生成
2. `GET /history` - 獲取歷史
3. `DELETE /history` - 清除歷史
4. `GET /images/<filename>` - 訪問圖片

#### 批量操作
5. `POST /batch-generate` - 批量生成
6. `POST /batch-download` - ZIP 下載

#### 模板系統
7. `GET /templates` - 風格模板列表
8. `GET /size-presets` - 尺寸預設列表

#### 標籤系統
9. `GET /tags` - 獲取所有標籤
10. `POST /history/<id>/tags` - 更新標籤
11. `POST /history/filter` - 標籤過濾

#### 進階功能
12. `POST /seed-control` - Seed 生成
13. `POST /add-text-overlay` - 文字疊加
14. `POST /export-pdf` - PDF 導出
15. `POST /export-ppt` - PPT 導出
16. `POST /delete-images` - 批量刪除

#### 提示詞助手 (v2.4)
17. `POST /prompt/suggestions` - 自動完成建議
18. `POST /prompt/enhance` - 增強提示詞
19. `GET /prompt/templates` - 範本列表
20. `POST /prompt/apply-template` - 應用範本

---

## 🎨 前端設計規範

### CSS 變數系統
```css
:root {
    --primary-color: #8b5cf6;
    --gradient-primary: linear-gradient(135deg, #8b5cf6, #6366f1);
    --surface: #ffffff;
    --text-primary: #1a1a1a;
    --text-secondary: #6b7280;
    --border-color: #e5e7eb;
    --hover-bg: #f3f4f6;
}
```

### 顏色方案
- 🟣 主色：紫色漸層（#8b5cf6 → #6366f1）
- 🟢 成功：綠色漸層（#10b981 → #059669）
- 🟠 警告：橙色漸層（#f59e0b → #d97706）
- 🔴 危險：紅色漸層（#e74c3c → #c0392b）

### JavaScript 模組規範
```javascript
// 模組模板
(function() {
    'use strict';

    // 初始化函數
    function initModule() {
        console.log('✓ 模組已初始化');
        // 綁定事件
    }

    // 頁面載入時初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initModule);
    } else {
        initModule();
    }
})();
```

---

## 🔮 未來開發計劃

### 短期計劃（v2.5）
- [ ] 提示詞歷史記錄
- [ ] 提示詞收藏功能
- [ ] 更多範本（擴展到 30+）
- [ ] 負面提示詞支援

### 中期計劃（v3.0）
- [ ] 圖片編輯工具（裁切、旋轉、濾鏡）
- [ ] 背景移除功能（rembg）
- [ ] 圖片放大（upscaling）
- [ ] ControlNet 整合

### 長期計劃（v4.0+）
- [ ] 使用者系統（註冊/登入）
- [ ] 多模型支援（可切換不同模型）
- [ ] 雲端同步
- [ ] API 對外開放
- [ ] 插件系統

---

## 🛠️ 開發環境設置

### 必要工具
- Python 3.8+
- Node.js（用於 JS 語法檢查）
- Git

### 開發流程
1. 創建功能分支
2. 實作新功能
3. JavaScript 語法檢查：`node --check static/js/*.js`
4. 測試功能
5. 更新文檔
6. 提交代碼

### 測試清單
- [ ] 單張生成測試
- [ ] 批量生成測試
- [ ] 所有 API 端點測試
- [ ] UI 響應性測試
- [ ] VRAM 佔用檢查
- [ ] 跨瀏覽器測試

---

## 📦 依賴管理

### 核心依賴
```
torch>=2.0.0
torchvision>=0.15.0
diffusers>=0.21.0
transformers>=4.30.0
accelerate>=0.20.0
flask>=2.3.0
pillow>=10.0.0
reportlab>=4.0.0
python-pptx>=0.6.21
```

### 開發依賴
```
pytest
black
flake8
```

---

## 🐛 已知問題

### 已修復
- ✅ JavaScript 變數重複宣告（v2.2）
- ✅ PPT 背景色類型錯誤（v2.3）
- ✅ 導出對話框按鈕不可見（v2.3）
- ✅ 風格選擇器文字壓縮（v2.3）

### 待處理
- 無

---

## 📈 性能優化建議

### 已實施
1. ✅ Sequential CPU Offload
2. ✅ Attention Slicing
3. ✅ VAE Slicing
4. ✅ 模型預載入
5. ✅ 批量序列化處理

### 可選優化
- xFormers（需額外安裝）
- Half Precision (FP16)
- Model Quantization

---

## 🔐 安全考量

### 已實施
- ✅ 輸入驗證
- ✅ 文件大小限制
- ✅ 路徑遍歷防護
- ✅ 刪除確認機制

### 待加強
- [ ] API 頻率限制
- [ ] 提示詞內容過濾
- [ ] 使用者認證系統

---

## 📚 參考資源

### 官方文檔
- [Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
- [Diffusers](https://huggingface.co/docs/diffusers)
- [Flask](https://flask.palletsprojects.com/)

### 技術文章
- Sequential CPU Offload 原理
- VRAM 優化最佳實踐
- Web UI 設計模式

---

## 💡 貢獻指南

### 提交 Issue
- 使用清晰的標題
- 提供詳細的重現步驟
- 附上錯誤截圖/日誌

### 提交 PR
- 遵循代碼風格
- 更新相關文檔
- 通過所有測試
- 清晰的 commit 訊息

---

**維護者**: Claude Code
**最後更新**: 2025-12-02
**版本**: v2.4.0
