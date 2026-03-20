"""
Analytics Service - 使用量統計與分析服務
追蹤生成次數、模型使用量、熱門提示詞等關鍵指標
"""
import os
import json
from datetime import datetime, timedelta
from collections import Counter
import config


ANALYTICS_FILE = os.path.join(config.OUTPUT_PATH, "analytics.json")


class AnalyticsService:
    """使用量統計分析服務"""

    def __init__(self):
        self.data = self._load()

    def _load(self):
        """載入統計資料"""
        if os.path.exists(ANALYTICS_FILE):
            try:
                with open(ANALYTICS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            'events': [],
            'daily_stats': {},
            'total_generations': 0,
            'total_api_calls': 0,
            'created_at': datetime.now().isoformat()
        }

    def _save(self):
        """儲存統計資料"""
        try:
            os.makedirs(os.path.dirname(ANALYTICS_FILE), exist_ok=True)
            with open(ANALYTICS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存統計資料失敗: {e}")

    def track_generation(self, model_id, prompt, width, height, mode='single', duration=None):
        """追蹤一次圖片生成事件"""
        today = datetime.now().strftime('%Y-%m-%d')
        event = {
            'type': 'generation',
            'model': model_id,
            'prompt_length': len(prompt),
            'prompt_preview': prompt[:80],
            'resolution': f'{width}x{height}',
            'mode': mode,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }

        self.data['events'].append(event)
        self.data['total_generations'] = self.data.get('total_generations', 0) + 1

        # 更新每日統計
        if today not in self.data['daily_stats']:
            self.data['daily_stats'][today] = {
                'generations': 0, 'api_calls': 0, 'models': {}, 'modes': {}
            }
        day = self.data['daily_stats'][today]
        day['generations'] = day.get('generations', 0) + 1
        day['models'][model_id] = day.get('models', {}).get(model_id, 0) + 1
        day['modes'][mode] = day.get('modes', {}).get(mode, 0) + 1

        # 限制事件數量（保留最近 1000 筆）
        if len(self.data['events']) > 1000:
            self.data['events'] = self.data['events'][-1000:]

        self._save()

    def track_api_call(self, endpoint, api_key_prefix=None):
        """追蹤一次 API 呼叫"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.data['total_api_calls'] = self.data.get('total_api_calls', 0) + 1

        if today not in self.data['daily_stats']:
            self.data['daily_stats'][today] = {
                'generations': 0, 'api_calls': 0, 'models': {}, 'modes': {}
            }
        self.data['daily_stats'][today]['api_calls'] = \
            self.data['daily_stats'][today].get('api_calls', 0) + 1

        self._save()

    def get_overview(self):
        """取得總覽統計"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_stats = self.data['daily_stats'].get(today, {})

        # 計算最近 7 天和 30 天
        week_gen = 0
        month_gen = 0
        now = datetime.now()
        for date_str, stats in self.data['daily_stats'].items():
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
                delta = (now - date).days
                if delta < 7:
                    week_gen += stats.get('generations', 0)
                if delta < 30:
                    month_gen += stats.get('generations', 0)
            except ValueError:
                continue

        return {
            'total_generations': self.data.get('total_generations', 0),
            'total_api_calls': self.data.get('total_api_calls', 0),
            'today_generations': today_stats.get('generations', 0),
            'today_api_calls': today_stats.get('api_calls', 0),
            'week_generations': week_gen,
            'month_generations': month_gen,
            'since': self.data.get('created_at', 'N/A')
        }

    def get_daily_chart(self, days=30):
        """取得每日生成數量（用於圖表）"""
        now = datetime.now()
        chart_data = []

        for i in range(days - 1, -1, -1):
            date = (now - timedelta(days=i)).strftime('%Y-%m-%d')
            stats = self.data['daily_stats'].get(date, {})
            chart_data.append({
                'date': date,
                'generations': stats.get('generations', 0),
                'api_calls': stats.get('api_calls', 0)
            })

        return chart_data

    def get_model_usage(self):
        """取得模型使用量統計"""
        model_counts = Counter()
        for event in self.data['events']:
            if event.get('type') == 'generation':
                model_counts[event.get('model', 'unknown')] += 1
        return dict(model_counts.most_common(10))

    def get_popular_resolutions(self):
        """取得熱門解析度"""
        res_counts = Counter()
        for event in self.data['events']:
            if event.get('type') == 'generation':
                res_counts[event.get('resolution', 'unknown')] += 1
        return dict(res_counts.most_common(10))

    def get_mode_distribution(self):
        """取得生成模式分佈"""
        mode_counts = Counter()
        for event in self.data['events']:
            if event.get('type') == 'generation':
                mode_counts[event.get('mode', 'single')] += 1
        return dict(mode_counts)

    def get_generation_speed(self):
        """取得平均生成速度"""
        durations = [
            e['duration'] for e in self.data['events']
            if e.get('type') == 'generation' and e.get('duration') is not None
        ]
        if not durations:
            return {'avg': None, 'min': None, 'max': None, 'count': 0}

        return {
            'avg': round(sum(durations) / len(durations), 2),
            'min': round(min(durations), 2),
            'max': round(max(durations), 2),
            'count': len(durations)
        }

    def get_recent_activity(self, limit=20):
        """取得最近活動"""
        events = self.data['events'][-limit:]
        events.reverse()
        return events


# 全域單例
_analytics_service = None


def get_analytics_service():
    """取得統計分析服務單例"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
