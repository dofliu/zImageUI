"""
Queue Service - 生成佇列管理服務
管理非同步圖片生成任務，支援優先順序、狀態追蹤和取消
"""
import os
import json
import uuid
import threading
import time
from datetime import datetime
from collections import deque
import config


class TaskStatus:
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class QueueService:
    """生成佇列服務"""

    def __init__(self, max_concurrent=1):
        self.tasks = {}  # task_id -> task_info
        self.queue = deque()  # 待處理佇列
        self.max_concurrent = max_concurrent
        self.active_count = 0
        self.lock = threading.Lock()
        self.worker_thread = None
        self._running = False

    def start(self):
        """啟動佇列處理器"""
        if self._running:
            return
        self._running = True
        self.worker_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.worker_thread.start()
        print("[Queue] 佇列處理器已啟動")

    def stop(self):
        """停止佇列處理器"""
        self._running = False

    def submit(self, task_type, params, priority=0):
        """提交新任務到佇列

        Args:
            task_type: 任務類型 (generate, batch, img2img, variation)
            params: 任務參數
            priority: 優先順序 (數字越大越優先)

        Returns:
            dict: 任務資訊
        """
        task_id = str(uuid.uuid4())[:12]
        task = {
            'id': task_id,
            'type': task_type,
            'params': params,
            'priority': priority,
            'status': TaskStatus.PENDING,
            'created_at': datetime.now().isoformat(),
            'started_at': None,
            'completed_at': None,
            'progress': 0,
            'result': None,
            'error': None
        }

        with self.lock:
            self.tasks[task_id] = task
            self.queue.append(task_id)
            # 依優先順序排序
            sorted_queue = sorted(self.queue,
                                  key=lambda tid: self.tasks[tid].get('priority', 0),
                                  reverse=True)
            self.queue = deque(sorted_queue)

        print(f"[Queue] 任務已加入佇列: {task_id} ({task_type})")
        return task

    def get_task(self, task_id):
        """取得任務狀態"""
        return self.tasks.get(task_id)

    def cancel_task(self, task_id):
        """取消任務"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return {'success': False, 'error': '任務不存在'}

            if task['status'] == TaskStatus.PENDING:
                task['status'] = TaskStatus.CANCELLED
                if task_id in self.queue:
                    self.queue.remove(task_id)
                return {'success': True, 'message': '任務已取消'}
            elif task['status'] == TaskStatus.PROCESSING:
                task['status'] = TaskStatus.CANCELLED
                return {'success': True, 'message': '任務將在目前步驟完成後取消'}
            else:
                return {'success': False, 'error': '任務已完成或已取消'}

    def get_queue_status(self):
        """取得佇列狀態"""
        with self.lock:
            pending = sum(1 for t in self.tasks.values() if t['status'] == TaskStatus.PENDING)
            processing = sum(1 for t in self.tasks.values() if t['status'] == TaskStatus.PROCESSING)
            completed = sum(1 for t in self.tasks.values() if t['status'] == TaskStatus.COMPLETED)
            failed = sum(1 for t in self.tasks.values() if t['status'] == TaskStatus.FAILED)

        return {
            'queue_length': pending,
            'processing': processing,
            'completed': completed,
            'failed': failed,
            'total': len(self.tasks)
        }

    def get_recent_tasks(self, limit=20):
        """取得最近的任務列表"""
        tasks_list = sorted(
            self.tasks.values(),
            key=lambda t: t['created_at'],
            reverse=True
        )[:limit]

        # 移除大型結果資料，只回傳摘要
        result = []
        for t in tasks_list:
            summary = {k: v for k, v in t.items() if k != 'result'}
            if t.get('result') and isinstance(t['result'], dict):
                summary['has_result'] = True
                summary['result_filename'] = t['result'].get('filename')
            result.append(summary)
        return result

    def clear_completed(self):
        """清除已完成的任務記錄"""
        with self.lock:
            to_remove = [
                tid for tid, t in self.tasks.items()
                if t['status'] in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
            ]
            for tid in to_remove:
                del self.tasks[tid]
        return {'cleared': len(to_remove)}

    def _process_loop(self):
        """佇列處理主迴圈"""
        while self._running:
            task_id = None

            with self.lock:
                if self.active_count < self.max_concurrent and self.queue:
                    task_id = self.queue.popleft()
                    self.active_count += 1

            if task_id:
                self._execute_task(task_id)
                with self.lock:
                    self.active_count -= 1
            else:
                time.sleep(0.5)  # 沒有任務時短暫休眠

    def _execute_task(self, task_id):
        """執行單一任務"""
        task = self.tasks.get(task_id)
        if not task or task['status'] == TaskStatus.CANCELLED:
            return

        task['status'] = TaskStatus.PROCESSING
        task['started_at'] = datetime.now().isoformat()

        try:
            start_time = time.time()
            result = self._run_generation(task)
            duration = time.time() - start_time

            if task['status'] == TaskStatus.CANCELLED:
                return

            task['status'] = TaskStatus.COMPLETED
            task['completed_at'] = datetime.now().isoformat()
            task['progress'] = 100
            task['result'] = result
            task['result']['duration'] = round(duration, 2)

            # 追蹤統計
            try:
                from services.analytics_service import get_analytics_service
                analytics = get_analytics_service()
                analytics.track_generation(
                    model_id=task['params'].get('model', 'unknown'),
                    prompt=task['params'].get('prompt', ''),
                    width=task['params'].get('width', config.IMAGE_WIDTH),
                    height=task['params'].get('height', config.IMAGE_HEIGHT),
                    mode=task['type'],
                    duration=round(duration, 2)
                )
            except Exception:
                pass

            print(f"[Queue] 任務完成: {task_id} ({duration:.1f}s)")

        except Exception as e:
            task['status'] = TaskStatus.FAILED
            task['completed_at'] = datetime.now().isoformat()
            task['error'] = str(e)
            print(f"[Queue] 任務失敗: {task_id} - {e}")

    def _run_generation(self, task):
        """執行圖片生成"""
        import base64
        from io import BytesIO
        from services.model_registry import get_model_registry
        from services.history_service import get_history_service

        params = task['params']
        registry = get_model_registry()

        if registry.active_pipeline is None:
            raise RuntimeError("尚未載入模型")

        prompt = params.get('prompt', '')
        width = params.get('width', config.IMAGE_WIDTH)
        height = params.get('height', config.IMAGE_HEIGHT)
        seed = params.get('seed')
        negative_prompt = params.get('negative_prompt')

        image, used_seed = registry.generate(
            prompt, width, height, seed,
            negative_prompt=negative_prompt
        )

        # 儲存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"queue_{timestamp}_{task['id']}.png"
        save_path = os.path.join(config.OUTPUT_PATH, filename)
        image.save(save_path)

        # 歷史記錄
        history_service = get_history_service()
        history_service.add_to_history(f"[queue] {prompt}", filename)

        # 加入專案（如果指定）
        project_id = params.get('project_id')
        if project_id:
            try:
                from services.project_service import get_project_service
                project_service = get_project_service()
                project_service.add_image(
                    project_id, filename, prompt,
                    seed=used_seed,
                    model_id=registry.active_model_id
                )
            except Exception:
                pass

        # base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return {
            'filename': filename,
            'image': f"data:image/png;base64,{img_str}",
            'prompt': prompt,
            'seed': used_seed,
            'width': width,
            'height': height
        }


# 全域單例
_queue_service = None


def get_queue_service():
    """取得佇列服務單例"""
    global _queue_service
    if _queue_service is None:
        _queue_service = QueueService(max_concurrent=1)
        _queue_service.start()
    return _queue_service
