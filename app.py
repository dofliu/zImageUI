"""
Z-Image Studio - v3.0.0
AI 圖片生成平台

產品化版本 - 多模型 / 圖生圖 / 作品集 / API
"""
from flask import Flask, render_template
import config
from flask_cors import CORS

from routes import register_blueprints
from services.model_registry import get_model_registry


# 建立 Flask 應用
app = Flask(__name__)
CORS(app)


# 註冊所有路由藍圖
register_blueprints(app)


@app.route('/')
def index():
    """首頁 - 圖片生成器"""
    return render_template('index.html')


if __name__ == '__main__':
    # 顯示配置資訊
    config.print_config_info()

    print(f"模型緩存路徑：{config.CACHE_PATH}")
    print(f"生成圖片儲存路徑：{config.OUTPUT_PATH}")

    # 初始化模型註冊表
    print("\n===================================")
    print("Z-Image Studio v3.0.0")
    print("===================================")
    registry = get_model_registry()

    # 自動載入預設模型 (Z-Image-Turbo)
    print("正在預載入預設模型 (Z-Image-Turbo)...")
    result = registry.switch_model("z-image-turbo")
    if result['success']:
        print(f"  {result['message']}")
    else:
        print(f"  預設模型載入失敗: {result.get('error', '未知錯誤')}")
        print("  您可以在 UI 中手動選擇並載入其他模型")

    print(f"\n已註冊 {len(registry.models)} 個模型:")
    for mid, minfo in registry.models.items():
        cached = "已快取" if minfo.get('is_cached') else "需下載"
        print(f"  - {minfo['name']} ({cached})")

    print(f"\n正在啟動 Flask 伺服器...")
    print(f"  生成器: http://localhost:{config.PORT}")
    print(f"  作品集: http://localhost:{config.PORT}/gallery")
    print(f"  API 文件: http://localhost:{config.PORT}/api/v1/")
    print("===================================\n")

    # 關閉 reloader 避免生成過程中重新載入
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT,
        use_reloader=config.USE_RELOADER
    )
