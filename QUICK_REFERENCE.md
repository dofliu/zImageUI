# 快速參考指南

> v2.4.0 快速上手指南

---

## ⚡ 5 分鐘快速開始

```bash
# 安裝
pip install torch diffusers transformers flask pillow reportlab python-pptx

# 啟動
python app.py

# 訪問
http://localhost:5001
```

---

## 🎯 核心功能速查

### 單張生成
1. 輸入提示詞
2. 選擇風格（可選）
3. 選擇尺寸
4. 生成

### 批量生成
1. 切換「批量模式」
2. 每行一個提示詞
3. 最多 20 個
4. 生成 → ZIP 下載

### 提示詞助手 ⭐ v2.4
1. 輸入時自動顯示建議
2. 點擊「增強提示詞」優化
3. 選擇範本快速開始

### 批量導出
1. 多選模式
2. 勾選圖片
3. 導出 → 選格式
4. PDF 或 PPT

---

## 📱 常用快捷鍵

- `↑↓` - 自動完成導航
- `Enter` - 選擇建議
- `Esc` - 關閉建議框

---

## 🎨 推薦設置

### 最佳品質
- 尺寸: 1024×1024
- Steps: 12-15
- 風格: 任意

### 最快速度
- 尺寸: 512×512 或 768×768
- Steps: 6-9
- 風格: 無

### 平衡模式（推薦）
- 尺寸: 768×768
- Steps: 9
- 風格: 按需選擇

---

## 🔧 快速配置

### 修改默認尺寸
```python
# config.py
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 768
```

### 修改生成步數
```python
# config.py
NUM_INFERENCE_STEPS = 9  # 6-15
```

### 修改端口
```python
# config.py
PORT = 5001
```

---

## 📊 API 快速測試

### 測試生成
```bash
curl -X POST http://localhost:5001/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a cat"}'
```

### 測試增強
```bash
curl -X POST http://localhost:5001/prompt/enhance \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a cat"}'
```

---

## 💡 提示詞技巧

### 基礎結構
```
主題 + 風格 + 品質
例: a cat, watercolor style, high quality
```

### 進階結構
```
主題 + 風格 + 光線 + 相機 + 品質
例: portrait of a woman, cinematic lighting, 
    shallow depth of field, 8k, masterpiece
```

### 使用範本
1. 選擇範本
2. 輸入主題
3. 自動生成完整提示詞

---

## 🐛 快速排查

### 問題: 啟動慢
**解決**: 首次下載模型，耐心等待

### 問題: OOM 錯誤
**解決**: 降低解析度或重啟應用

### 問題: 生成太慢
**解決**: 減少 steps 或降低解析度

### 問題: 結果不理想
**解決**: 使用提示詞助手優化

---

## 📚 更多資訊

- **完整文檔**: [README.md](README.md)
- **開發指南**: [DEVELOPMENT.md](DEVELOPMENT.md)
- **問題回報**: GitHub Issues

---

**提示**: 使用提示詞助手可大幅提升生成品質！
