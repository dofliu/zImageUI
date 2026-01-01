"""
Z-Image-Turbo Web UI - v2.5.0
AI 圖片生成 Web 應用

重構版本 - 模組化架構
"""
from flask import Flask, render_template
import config
from routes import register_blueprints
from services.model_service import get_model_service


# 建立 Flask 應用
app = Flask(__name__)


# 註冊所有路由藍圖
register_blueprints(app)


@app.route('/')
def index():
    """首頁"""
    return render_template('index.html')


if __name__ == '__main__':
    # 顯示配置資訊
    config.print_config_info()

    print(f"模型緩存路徑：{config.CACHE_PATH}")
    print(f"生成圖片儲存路徑：{config.OUTPUT_PATH}")

    # 🚀 優化：在伺服器啟動時就預載入模型
    print("\n===================================")
    print("正在預載入模型...")
    print("===================================")
    model_service = get_model_service()
    model_service.initialize_model()
    print("✅ 模型已就緒！可以開始生成圖片了\n")

    print("正在啟動 Flask 伺服器...")
    print(f"請在瀏覽器開啟: http://localhost:{config.PORT}")
    print("===================================\n")

    # 關閉 reloader 避免生成過程中重新載入
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT,
        use_reloader=config.USE_RELOADER
    )
