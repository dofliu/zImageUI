"""
History Routes - 歷史記錄相關路由
"""
import os
import zipfile
import tempfile
from datetime import datetime
from flask import Blueprint, request, jsonify, send_from_directory, send_file
import config
from services.history_service import get_history_service


history_bp = Blueprint('history', __name__)


@history_bp.route('/images/<filename>')
def get_image(filename):
    """提供圖片下載"""
    return send_from_directory(config.OUTPUT_PATH, filename)


@history_bp.route('/history', methods=['GET'])
def get_history():
    """獲取歷史記錄"""
    try:
        history_service = get_history_service()
        history = history_service.load_history()
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@history_bp.route('/history', methods=['DELETE'])
def clear_history():
    """清除所有歷史記錄"""
    try:
        history_service = get_history_service()
        history_service.save_history([])
        return jsonify({
            'success': True,
            'message': '歷史記錄已清除'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@history_bp.route('/batch-download', methods=['POST'])
def batch_download():
    """批量下載圖片為 ZIP"""
    try:
        data = request.get_json()
        filenames = data.get('filenames', [])

        if not filenames:
            return jsonify({'error': '沒有要下載的檔案'}), 400

        # 建立臨時 ZIP 檔案
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"batch_images_{timestamp}.zip"
        zip_path = os.path.join(tempfile.gettempdir(), zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename in filenames:
                file_path = os.path.join(config.OUTPUT_PATH, filename)
                if os.path.exists(file_path):
                    zipf.write(file_path, filename)

        # 發送檔案後刪除臨時檔案
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )

    except Exception as e:
        print(f"批量下載錯誤：{str(e)}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/delete-images', methods=['POST'])
def delete_images():
    """刪除選定的圖片"""
    try:
        data = request.get_json()
        filenames = data.get('filenames', [])

        if not filenames:
            return jsonify({'error': '請選擇要刪除的圖片'}), 400

        deleted_count = 0
        failed_files = []

        # 載入歷史記錄
        history_service = get_history_service()
        history = history_service.load_history()

        # 刪除圖片檔案並從歷史記錄中移除
        for filename in filenames:
            file_path = os.path.join(config.OUTPUT_PATH, filename)

            try:
                # 刪除圖片檔案
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"✓ 已刪除圖片: {filename}")

                # 從歷史記錄中移除
                history = [item for item in history if item['filename'] != filename]

            except Exception as e:
                print(f"✗ 刪除 {filename} 失敗: {e}")
                failed_files.append(filename)

        # 儲存更新後的歷史記錄
        history_service.save_history(history)

        if failed_files:
            return jsonify({
                'success': True,
                'deleted': deleted_count,
                'failed': len(failed_files),
                'failed_files': failed_files,
                'message': f'已刪除 {deleted_count} 張圖片，{len(failed_files)} 張失敗'
            })
        else:
            return jsonify({
                'success': True,
                'deleted': deleted_count,
                'message': f'成功刪除 {deleted_count} 張圖片'
            })

    except Exception as e:
        print(f"刪除圖片錯誤：{str(e)}")
        return jsonify({'error': str(e)}), 500
