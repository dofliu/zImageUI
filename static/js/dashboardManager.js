/**
 * Dashboard Manager - 儀表板資料載入與渲染
 */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', () => {
        loadOverview();
        loadDailyChart();
        loadModelUsage();
        loadModeDistribution();
        loadQueueStatus();
        loadApiKeys();
        loadRecentActivity();

        // 每 30 秒自動刷新
        setInterval(() => {
            loadOverview();
            loadQueueStatus();
        }, 30000);
    });

    // ===== 總覽統計 =====
    async function loadOverview() {
        try {
            const res = await fetch('/api/analytics/overview');
            const { data } = await res.json();
            document.getElementById('totalGenerations').textContent = data.total_generations.toLocaleString();
            document.getElementById('todayGenerations').textContent = data.today_generations.toLocaleString();
            document.getElementById('weekGenerations').textContent = data.week_generations.toLocaleString();
            document.getElementById('totalApiCalls').textContent = data.total_api_calls.toLocaleString();
        } catch (e) {
            console.error('載入統計失敗:', e);
        }
    }

    // ===== 每日圖表 =====
    async function loadDailyChart() {
        try {
            const res = await fetch('/api/analytics/daily?days=30');
            const { data } = await res.json();

            const container = document.getElementById('chartBars');
            container.innerHTML = '';

            const maxVal = Math.max(1, ...data.map(d => d.generations));

            data.forEach(day => {
                const bar = document.createElement('div');
                bar.className = 'chart-bar';
                const height = Math.max(2, (day.generations / maxVal) * 100);
                bar.style.height = `${height}%`;
                bar.dataset.tooltip = `${day.date}: ${day.generations} 張`;
                container.appendChild(bar);
            });
        } catch (e) {
            console.error('載入圖表失敗:', e);
        }
    }

    // ===== 模型使用量 =====
    async function loadModelUsage() {
        try {
            const res = await fetch('/api/analytics/models');
            const { data } = await res.json();
            const container = document.getElementById('modelUsage');

            if (Object.keys(data).length === 0) {
                container.innerHTML = '<p class="empty-data">尚無使用資料</p>';
                return;
            }

            const maxVal = Math.max(1, ...Object.values(data));
            container.innerHTML = '';

            Object.entries(data).forEach(([model, count]) => {
                const item = document.createElement('div');
                item.className = 'usage-item';
                item.innerHTML = `
                    <span class="usage-label">${model}</span>
                    <div class="usage-bar-wrapper">
                        <div class="usage-bar" style="width: ${(count / maxVal) * 100}%"></div>
                    </div>
                    <span class="usage-count">${count}</span>
                `;
                container.appendChild(item);
            });
        } catch (e) {
            console.error('載入模型使用量失敗:', e);
        }
    }

    // ===== 模式分佈 =====
    async function loadModeDistribution() {
        try {
            const res = await fetch('/api/analytics/modes');
            const { data } = await res.json();
            const container = document.getElementById('modeDistribution');

            if (Object.keys(data).length === 0) {
                container.innerHTML = '<p class="empty-data">尚無使用資料</p>';
                return;
            }

            const modeLabels = {
                single: '單張生成', batch: '批量生成', img2img: '圖生圖',
                variation: '變體生成', queue: '佇列生成'
            };
            const maxVal = Math.max(1, ...Object.values(data));
            container.innerHTML = '';

            Object.entries(data).forEach(([mode, count]) => {
                const item = document.createElement('div');
                item.className = 'usage-item';
                item.innerHTML = `
                    <span class="usage-label">${modeLabels[mode] || mode}</span>
                    <div class="usage-bar-wrapper">
                        <div class="usage-bar" style="width: ${(count / maxVal) * 100}%"></div>
                    </div>
                    <span class="usage-count">${count}</span>
                `;
                container.appendChild(item);
            });
        } catch (e) {
            console.error('載入模式分佈失敗:', e);
        }
    }

    // ===== 佇列狀態 =====
    async function loadQueueStatus() {
        try {
            const res = await fetch('/api/queue/status');
            const { status } = await res.json();
            document.getElementById('queuePending').textContent = status.queue_length;
            document.getElementById('queueProcessing').textContent = status.processing;
            document.getElementById('queueCompleted').textContent = status.completed;
            document.getElementById('queueFailed').textContent = status.failed;
        } catch (e) {
            console.error('載入佇列狀態失敗:', e);
        }
    }

    // ===== API 金鑰 =====
    async function loadApiKeys() {
        try {
            const res = await fetch('/api/v1/keys');
            const { keys } = await res.json();
            const container = document.getElementById('apiKeysList');

            if (!keys || keys.length === 0) {
                container.innerHTML = '<p class="empty-data">尚未建立 API 金鑰</p>';
                return;
            }

            container.innerHTML = '';
            keys.forEach(key => {
                const item = document.createElement('div');
                item.className = 'api-key-item';
                item.innerHTML = `
                    <div>
                        <div class="api-key-name">${key.name}</div>
                        <div class="api-key-prefix">${key.prefix}...</div>
                    </div>
                    <div class="api-key-usage">使用 ${key.usage_count} 次</div>
                `;
                container.appendChild(item);
            });
        } catch (e) {
            console.error('載入 API 金鑰失敗:', e);
        }
    }

    // ===== 建立金鑰 =====
    const createKeyBtn = document.getElementById('createKeyBtn');
    if (createKeyBtn) {
        createKeyBtn.addEventListener('click', async () => {
            const name = prompt('請輸入金鑰名稱：');
            if (!name) return;

            try {
                const res = await fetch('/api/v1/keys', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name })
                });
                const data = await res.json();
                if (data.success) {
                    alert(`金鑰已建立！\n\n${data.api_key}\n\n請妥善保存，此金鑰不會再次顯示。`);
                    loadApiKeys();
                }
            } catch (e) {
                alert('建立失敗: ' + e.message);
            }
        });
    }

    // ===== 最近活動 =====
    async function loadRecentActivity() {
        try {
            const res = await fetch('/api/analytics/activity?limit=15');
            const { data } = await res.json();
            const container = document.getElementById('recentActivity');

            if (!data || data.length === 0) {
                container.innerHTML = '<p class="empty-data">尚無活動記錄</p>';
                return;
            }

            container.innerHTML = '';
            data.forEach(event => {
                const item = document.createElement('div');
                item.className = 'activity-item';

                const time = new Date(event.timestamp);
                const timeStr = time.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });

                item.innerHTML = `
                    <span class="activity-type">${event.type || event.mode || 'event'}</span>
                    <span class="activity-detail">${event.prompt_preview || event.model || '-'}</span>
                    <span class="activity-time">${timeStr}</span>
                `;
                container.appendChild(item);
            });
        } catch (e) {
            console.error('載入最近活動失敗:', e);
        }
    }

})();
