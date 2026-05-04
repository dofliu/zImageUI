/**
 * Model Selector v2.0 - 支援本地 + 雲端 Provider
 *
 * 功能：
 *  - 顯示目前使用的模型（本地 / 雲端）
 *  - 點擊 chip 展開模型選擇面板
 *  - 本地模型：一鍵載入
 *  - 雲端模型：需 API Key，顯示設定入口
 */
(function () {
    'use strict';

    let currentModelId = null;
    let allModels = [];
    let panelOpen = false;

    // ── 初始化 ──────────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {
        loadModels();
        // 點擊其他地方關閉面板
        document.addEventListener('click', (e) => {
            const container = document.getElementById('modelSelectorContainer');
            if (container && !container.contains(e.target)) {
                closePanel();
            }
        });
    });

    async function loadModels() {
        try {
            const res = await fetch('/models');
            const data = await res.json();
            if (data.success) {
                allModels = data.models;
                currentModelId = data.active_model;
                renderChip();
            }
        } catch (e) {
            console.error('載入模型列表失敗:', e);
            renderChipError();
        }
    }

    // ── Chip（頂欄按鈕）────────────────────────────────────────
    function renderChip() {
        const container = document.getElementById('modelSelectorContainer');
        if (!container) return;

        const active = allModels.find(m => m.id === currentModelId);

        if (active) {
            const isCloud = active.provider_type === 'cloud';
            const providerBadge = isCloud
                ? `<span class="model-provider-badge cloud">${active.provider.toUpperCase()}</span>`
                : `<span class="model-provider-badge local">LOCAL</span>`;

            container.innerHTML = `
                <div class="model-status ready" id="modelChip" style="cursor:pointer">
                    <div class="model-status-icon">✓</div>
                    <div class="model-status-info">
                        <span class="model-status-name">${active.name} ${providerBadge}</span>
                        <span class="model-status-detail">${active.status?.message || '就緒'}</span>
                    </div>
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" style="opacity:.5;flex-shrink:0"><polyline points="6 9 12 15 18 9"/></svg>
                </div>
                <div id="modelPanel" class="model-panel" style="display:none"></div>
            `;
        } else {
            container.innerHTML = `
                <div class="model-status idle" id="modelChip" style="cursor:pointer">
                    <div class="model-status-icon">○</div>
                    <div class="model-status-info">
                        <span class="model-status-name">選擇模型</span>
                        <span class="model-status-detail">點擊以選擇生圖模型</span>
                    </div>
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" style="opacity:.5;flex-shrink:0"><polyline points="6 9 12 15 18 9"/></svg>
                </div>
                <div id="modelPanel" class="model-panel" style="display:none"></div>
            `;
        }

        document.getElementById('modelChip')?.addEventListener('click', togglePanel);
    }

    function renderChipError() {
        const container = document.getElementById('modelSelectorContainer');
        if (!container) return;
        container.innerHTML = `
            <div class="model-status error" id="modelChip" style="cursor:pointer">
                <div class="model-status-icon">!</div>
                <div class="model-status-info">
                    <span class="model-status-name">無法連線</span>
                    <span class="model-status-detail">點擊重試</span>
                </div>
            </div>
        `;
        document.getElementById('modelChip')?.addEventListener('click', loadModels);
    }

    // ── 面板 ────────────────────────────────────────────────────
    function togglePanel() {
        panelOpen ? closePanel() : openPanel();
    }

    function openPanel() {
        const panel = document.getElementById('modelPanel');
        if (!panel) return;
        panelOpen = true;
        renderPanel(panel);
        panel.style.display = 'block';
    }

    function closePanel() {
        const panel = document.getElementById('modelPanel');
        if (panel) panel.style.display = 'none';
        panelOpen = false;
    }

    function renderPanel(panel) {
        const localModels = allModels.filter(m => m.provider_type === 'local');
        const cloudModels = allModels.filter(m => m.provider_type === 'cloud');

        panel.innerHTML = `
            <div class="model-panel-inner">
                <div class="model-panel-header">
                    <span>模型選擇</span>
                    <a href="#" id="openSettingsLink" style="font-size:11px;opacity:.6">⚙ API 設定</a>
                </div>

                ${localModels.length ? `
                <div class="model-group-label">本地模型</div>
                ${localModels.map(m => renderModelRow(m)).join('')}
                ` : ''}

                ${cloudModels.length ? `
                <div class="model-group-label" style="margin-top:10px">雲端模型</div>
                ${cloudModels.map(m => renderModelRow(m)).join('')}
                ` : ''}
            </div>
        `;

        // 綁定事件
        panel.querySelectorAll('.model-row-btn').forEach(btn => {
            btn.addEventListener('click', () => handleSelectModel(btn.dataset.modelId));
        });
        panel.querySelector('#openSettingsLink')?.addEventListener('click', (e) => {
            e.preventDefault();
            closePanel();
            openSettingsModal();
        });
    }

    function renderModelRow(m) {
        const isActive = m.id === currentModelId;
        const isReady = m.status?.ready;
        const requiresKey = m.requires_api_key && !isReady;

        let btnText = isActive ? '使用中' : '選擇';
        let btnClass = isActive ? 'model-row-btn active' : 'model-row-btn';
        if (requiresKey) { btnText = '設定 Key'; btnClass += ' needs-key'; }
        if (m.is_loading) { btnText = '載入中…'; btnClass += ' loading'; }

        const providerTag = m.provider_type === 'cloud'
            ? `<span style="font-size:9px;padding:1px 5px;border-radius:3px;background:var(--at-accent-alpha,rgba(99,102,241,.15));color:var(--at-accent,#6366f1)">${m.provider.toUpperCase()}</span>`
            : '';

        return `
            <div class="model-row ${isActive ? 'is-active' : ''}">
                <div class="model-row-info">
                    <div class="model-row-name">${m.name} ${providerTag}</div>
                    <div class="model-row-desc">${m.description || ''}</div>
                </div>
                <button class="${btnClass}" data-model-id="${m.id}" ${m.is_loading || isActive ? 'disabled' : ''}>${btnText}</button>
            </div>
        `;
    }

    // ── 模型選擇邏輯 ────────────────────────────────────────────
    async function handleSelectModel(modelId) {
        const model = allModels.find(m => m.id === modelId);
        if (!model) return;

        // 雲端模型需要 API Key → 先檢查
        if (model.provider_type === 'cloud' && model.requires_api_key && !model.status?.ready) {
            closePanel();
            openSettingsModal(model.provider);
            return;
        }

        // 更新 UI
        closePanel();
        showChipLoading(model.name);

        try {
            const res = await fetch('/models/switch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_id: modelId }),
            });
            const data = await res.json();

            if (data.success) {
                currentModelId = modelId;
                await loadModels();
            } else {
                if (data.requires === 'api_key') {
                    openSettingsModal(data.provider);
                } else {
                    alert('切換模型失敗：' + (data.error || '未知錯誤'));
                }
                await loadModels();
            }
        } catch (e) {
            console.error(e);
            await loadModels();
        }
    }

    function showChipLoading(name) {
        const container = document.getElementById('modelSelectorContainer');
        if (!container) return;
        container.innerHTML = `
            <div class="model-status loading">
                <div class="model-status-spinner"></div>
                <div class="model-status-info">
                    <span class="model-status-name">${name}</span>
                    <span class="model-status-detail">切換中，請稍候…</span>
                </div>
            </div>
        `;
    }

    // ── 設定 Modal ──────────────────────────────────────────────
    function openSettingsModal(focusProvider) {
        let modal = document.getElementById('providerSettingsModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'providerSettingsModal';
            modal.className = 'settings-modal-overlay';
            document.body.appendChild(modal);
        }
        modal.innerHTML = buildSettingsModalHTML();
        modal.style.display = 'flex';
        loadSettingsData(modal, focusProvider);

        modal.querySelector('.settings-modal-close')?.addEventListener('click', () => {
            modal.style.display = 'none';
        });
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.style.display = 'none';
        });
    }

    function buildSettingsModalHTML() {
        return `
        <div class="settings-modal">
            <div class="settings-modal-topbar">
                <span class="settings-modal-title">⚙ Provider 設定</span>
                <button class="settings-modal-close at-icon-btn">✕</button>
            </div>
            <div class="settings-modal-body" id="settingsModalBody">
                <div style="text-align:center;padding:24px;opacity:.5">載入中…</div>
            </div>
        </div>`;
    }

    async function loadSettingsData(modal, focusProvider) {
        try {
            const res = await fetch('/settings/providers');
            const data = await res.json();
            const body = modal.querySelector('#settingsModalBody');
            if (!body) return;

            const providers = [
                { id: 'gemini', name: 'Google Gemini', icon: '🟦', link: 'https://aistudio.google.com/apikey',
                  models: ['Nano Banana (2.5 Flash)', 'Nano Banana 2 (3.1 Flash Preview)', 'Nano Banana Pro (3 Pro Preview)', 'Imagen 4.0'],
                  placeholder: 'AIza...' },
                { id: 'openai', name: 'OpenAI GPT Image', icon: '⬛', link: 'https://platform.openai.com/api-keys',
                  models: ['gpt-image-1', 'dall-e-3', 'dall-e-2'],
                  placeholder: 'sk-...' },
            ];

            body.innerHTML = providers.map(p => {
                const info = data.providers?.[p.id] || {};
                const focused = p.id === focusProvider;
                return `
                <div class="settings-provider-card ${focused ? 'focused' : ''}">
                    <div class="settings-provider-header">
                        <span>${p.icon} ${p.name}</span>
                        ${info.has_key
                            ? `<span class="settings-key-badge ok">✓ Key 已設定</span>`
                            : `<span class="settings-key-badge missing">未設定</span>`}
                    </div>
                    <div class="settings-field">
                        <label>API Key <a href="${p.link}" target="_blank" style="font-size:10px;opacity:.6">取得 Key ↗</a></label>
                        <div style="display:flex;gap:6px">
                            <input type="password" id="key_${p.id}" class="at-seed-input" style="flex:1"
                                placeholder="${info.has_key ? info.masked_key || p.placeholder : p.placeholder}"
                                autocomplete="off"/>
                            <button class="at-mini-btn save-key-btn" data-provider="${p.id}">儲存</button>
                            ${info.has_key ? `<button class="at-mini-btn clear-key-btn" data-provider="${p.id}" style="opacity:.6">清除</button>` : ''}
                        </div>
                    </div>
                    <div id="keyMsg_${p.id}" style="font-size:11px;min-height:16px;color:var(--at-ok,#22c55e)"></div>
                </div>`;
            }).join('');

            // 綁定按鈕
            body.querySelectorAll('.save-key-btn').forEach(btn => {
                btn.addEventListener('click', () => saveApiKey(btn.dataset.provider));
            });
            body.querySelectorAll('.clear-key-btn').forEach(btn => {
                btn.addEventListener('click', () => clearApiKey(btn.dataset.provider));
            });

        } catch (e) {
            const body = modal.querySelector('#settingsModalBody');
            if (body) body.innerHTML = `<div style="color:red;padding:16px">載入設定失敗: ${e.message}</div>`;
        }
    }

    async function saveApiKey(providerId) {
        const input = document.getElementById(`key_${providerId}`);
        const msgEl = document.getElementById(`keyMsg_${providerId}`);
        const key = input?.value?.trim();
        if (!key) { if (msgEl) msgEl.textContent = '請輸入 API Key'; return; }

        try {
            const res = await fetch(`/settings/providers/${providerId}/key`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: key }),
            });
            const data = await res.json();
            if (msgEl) {
                msgEl.textContent = data.success ? '✓ 儲存成功！' : '✗ ' + data.error;
                msgEl.style.color = data.success ? 'var(--at-ok,#22c55e)' : 'var(--at-err,#ef4444)';
            }
            if (data.success) {
                if (input) input.value = '';
                await loadModels();
            }
        } catch (e) {
            if (msgEl) { msgEl.textContent = '儲存失敗: ' + e.message; msgEl.style.color = 'var(--at-err,#ef4444)'; }
        }
    }

    async function clearApiKey(providerId) {
        if (!confirm('確定要清除此 API Key？')) return;
        await fetch(`/settings/providers/${providerId}/key`, { method: 'DELETE' });
        await loadModels();
        const modal = document.getElementById('providerSettingsModal');
        if (modal && modal.style.display !== 'none') {
            loadSettingsData(modal, providerId);
        }
    }

    // ── 對外 API ─────────────────────────────────────────────────
    window.ModelSelector = {
        getCurrentModel: () => currentModelId,
        getModels: () => allModels,
        getActiveModel: () => allModels.find(m => m.id === currentModelId),
        refresh: loadModels,
        isReady: () => {
            const active = allModels.find(m => m.id === currentModelId);
            return active ? (active.status?.ready || false) : false;
        },
        openSettings: openSettingsModal,
    };

})();
