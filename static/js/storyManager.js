/**
 * Story Manager - 漫畫工作室前端
 * 管理故事列表、角色、面板編輯、生成和預覽
 */
(function () {
    'use strict';

    let presets = {};
    let currentStory = null;
    let editingCharId = null;

    document.addEventListener('DOMContentLoaded', init);

    async function init() {
        await loadPresets();
        loadStoryList();
        bindEvents();
    }

    function bindEvents() {
        document.getElementById('createStoryBtn')?.addEventListener('click', openCreateDialog);
        document.getElementById('confirmCreateBtn')?.addEventListener('click', confirmCreate);
        document.getElementById('backToListBtn')?.addEventListener('click', backToList);
        document.getElementById('addCharacterBtn')?.addEventListener('click', () => openCharDialog());
        document.getElementById('confirmCharBtn')?.addEventListener('click', confirmCharacter);
        document.getElementById('addPanelBtn')?.addEventListener('click', addPanel);
        document.getElementById('generateAllBtn')?.addEventListener('click', generateAll);
        document.getElementById('previewPromptsBtn')?.addEventListener('click', previewPrompts);
        document.getElementById('saveStyleBtn')?.addEventListener('click', saveStyle);
        document.getElementById('saveSeedBtn')?.addEventListener('click', saveSeedSettings);
        document.getElementById('randomSeedBaseBtn')?.addEventListener('click', () => {
            document.getElementById('seedBase').value = Math.floor(Math.random() * 4294967295);
        });

        document.getElementById('stylePresetSelect')?.addEventListener('change', (e) => {
            const preset = presets.styles?.[e.target.value];
            if (preset) {
                document.getElementById('customStylePrefix').value = preset.style_prefix;
                document.getElementById('customStyleSuffix').value = preset.style_suffix;
                document.getElementById('customNegative').value = preset.negative;
            }
        });
    }

    // ==================== 預設資料 ====================

    async function loadPresets() {
        try {
            const res = await fetch('/api/story/presets');
            presets = await res.json();
        } catch (e) {
            console.error('載入預設失敗', e);
            presets = { styles: {}, layouts: {}, camera_angles: [], moods: [] };
        }
    }

    // ==================== 故事列表 ====================

    async function loadStoryList() {
        try {
            const res = await fetch('/api/stories');
            const data = await res.json();
            renderStoryList(data.stories || []);
        } catch (e) {
            console.error('載入故事列表失敗', e);
        }
    }

    function renderStoryList(stories) {
        const grid = document.getElementById('storyGrid');
        if (!stories.length) {
            grid.innerHTML = `
                <div class="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" width="64" height="64">
                        <rect x="3" y="3" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                        <rect x="14" y="3" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                        <rect x="3" y="14" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                        <rect x="14" y="14" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <h3>開始你的漫畫創作</h3>
                    <p>建立角色、設定風格、規劃劇情，一鍵生成風格一致的連環漫畫</p>
                </div>`;
            return;
        }

        grid.innerHTML = stories.map(s => {
            const layoutName = presets.layouts?.[s.layout]?.name || s.layout;
            const styleName = presets.styles?.[s.style_preset]?.name || s.style_preset;
            const panelCount = s.panels?.length || 0;
            const doneCount = (s.panels || []).filter(p => p.status === 'done').length;
            const charCount = s.characters?.length || 0;
            return `
                <div class="story-card" data-id="${s.id}">
                    <div class="story-card-top">
                        <div class="story-card-preview">
                            ${renderCardPreviews(s)}
                        </div>
                    </div>
                    <div class="story-card-body">
                        <h3 class="story-card-title">${esc(s.title)}</h3>
                        ${s.description ? `<p class="story-card-desc">${esc(s.description)}</p>` : ''}
                        <div class="story-card-meta">
                            <span class="meta-tag">${layoutName}</span>
                            <span class="meta-tag">${styleName}</span>
                            <span class="meta-tag">${charCount} 角色</span>
                            <span class="meta-tag">${doneCount}/${panelCount} 格</span>
                        </div>
                    </div>
                    <div class="story-card-actions">
                        <button class="card-edit-btn" onclick="event.stopPropagation();" data-id="${s.id}">編輯</button>
                        <button class="card-delete-btn" onclick="event.stopPropagation();" data-id="${s.id}">刪除</button>
                    </div>
                </div>`;
        }).join('');

        grid.querySelectorAll('.story-card').forEach(card => {
            card.addEventListener('click', () => openStory(card.dataset.id));
        });
        grid.querySelectorAll('.card-edit-btn').forEach(btn => {
            btn.addEventListener('click', () => openStory(btn.dataset.id));
        });
        grid.querySelectorAll('.card-delete-btn').forEach(btn => {
            btn.addEventListener('click', () => deleteStory(btn.dataset.id));
        });
    }

    function renderCardPreviews(story) {
        const panels = story.panels || [];
        const done = panels.filter(p => p.status === 'done');
        if (!done.length) {
            return '<div class="preview-placeholder">尚未生成</div>';
        }
        return done.slice(0, 4).map((p, i) =>
            `<img src="/api/stories/${story.id}/panels/${p.index}/image" alt="面板 ${i}" class="preview-thumb">`
        ).join('');
    }

    // ==================== 建立故事 ====================

    function openCreateDialog() {
        const dialog = document.getElementById('createStoryDialog');

        // 填充佈局選項
        const layoutDiv = document.getElementById('layoutOptions');
        layoutDiv.innerHTML = Object.entries(presets.layouts || {}).map(([key, info]) =>
            `<label class="option-card ${key === '4koma' ? 'selected' : ''}">
                <input type="radio" name="layout" value="${key}" ${key === '4koma' ? 'checked' : ''}>
                <span class="option-name">${info.name}</span>
                <span class="option-desc">${info.panels} 格 - ${info.description}</span>
            </label>`
        ).join('');

        // 填充風格選項
        const styleDiv = document.getElementById('styleOptions');
        styleDiv.innerHTML = Object.entries(presets.styles || {}).map(([key, info]) =>
            `<label class="option-card ${key === 'anime' ? 'selected' : ''}">
                <input type="radio" name="style" value="${key}" ${key === 'anime' ? 'checked' : ''}>
                <span class="option-name">${info.name}</span>
            </label>`
        ).join('');

        // radio 選中效果
        dialog.querySelectorAll('.option-card').forEach(card => {
            card.querySelector('input')?.addEventListener('change', (e) => {
                const group = card.closest('.layout-options, .style-options');
                group.querySelectorAll('.option-card').forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
            });
        });

        dialog.style.display = 'flex';
    }

    async function confirmCreate() {
        const title = document.getElementById('newStoryTitle')?.value?.trim();
        if (!title) { alert('請輸入標題'); return; }

        const layout = document.querySelector('input[name="layout"]:checked')?.value || '4koma';
        const style = document.querySelector('input[name="style"]:checked')?.value || 'anime';
        const desc = document.getElementById('newStoryDesc')?.value?.trim() || '';

        try {
            const res = await fetch('/api/stories', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, layout, style_preset: style, description: desc })
            });
            const data = await res.json();
            if (data.success) {
                document.getElementById('createStoryDialog').style.display = 'none';
                document.getElementById('newStoryTitle').value = '';
                document.getElementById('newStoryDesc').value = '';
                openStory(data.story.id);
            }
        } catch (e) { alert('建立失敗'); }
    }

    async function deleteStory(id) {
        if (!confirm('確定刪除這個故事？')) return;
        try {
            await fetch(`/api/stories/${id}`, { method: 'DELETE' });
            loadStoryList();
        } catch (e) { alert('刪除失敗'); }
    }

    // ==================== 故事編輯 ====================

    async function openStory(storyId) {
        try {
            const res = await fetch(`/api/stories/${storyId}`);
            const data = await res.json();
            if (!data.success) return;

            currentStory = data.story;

            document.getElementById('storyListView').style.display = 'none';
            document.getElementById('storyEditView').style.display = 'block';
            document.getElementById('editStoryTitle').textContent = currentStory.title;

            // 填充側邊欄
            fillSidebar();
            renderCharacters();
            renderPanels();
            renderPreview();
        } catch (e) {
            console.error('載入故事失敗', e);
        }
    }

    function backToList() {
        currentStory = null;
        document.getElementById('storyEditView').style.display = 'none';
        document.getElementById('storyListView').style.display = 'block';
        loadStoryList();
    }

    function fillSidebar() {
        // 風格選單
        const styleSelect = document.getElementById('stylePresetSelect');
        styleSelect.innerHTML = Object.entries(presets.styles || {}).map(([key, info]) =>
            `<option value="${key}" ${key === currentStory.style_preset ? 'selected' : ''}>${info.name}</option>`
        ).join('');

        const style = currentStory.style_custom || {};
        document.getElementById('customStylePrefix').value = style.prefix || '';
        document.getElementById('customStyleSuffix').value = style.suffix || '';
        document.getElementById('customNegative').value = style.negative || '';

        // Seed
        document.getElementById('seedBase').value = currentStory.seed_base || 42;

        // 模型選單
        const modelSelect = document.getElementById('modelSelect');
        fetch('/models').then(r => r.json()).then(data => {
            const currentModelId = currentStory.model_id;
            const opts = '<option value=""' + (!currentModelId ? ' selected' : '') + '>使用目前已啟用的模型</option>' +
                (data.models || []).map(m =>
                    `<option value="${m.id}" ${m.id === currentModelId ? 'selected' : ''}>${m.name}${m.is_active ? ' (啟用中)' : ''}</option>`
                ).join('');
            modelSelect.innerHTML = opts;
        }).catch(() => {
            modelSelect.innerHTML = '<option value="">使用目前已啟用的模型</option>';
        });

        // 佈局標籤
        const layoutName = presets.layouts?.[currentStory.layout]?.name || currentStory.layout;
        document.getElementById('layoutLabel').textContent = layoutName;
    }

    async function saveStyle() {
        if (!currentStory) return;
        const stylePreset = document.getElementById('stylePresetSelect').value;
        const style_custom = {
            prefix: document.getElementById('customStylePrefix').value,
            suffix: document.getElementById('customStyleSuffix').value,
            negative: document.getElementById('customNegative').value
        };
        await updateStory({ style_preset: stylePreset, style_custom });
        showToast('風格設定已儲存');
    }

    async function saveSeedSettings() {
        if (!currentStory) return;
        const seed_base = parseInt(document.getElementById('seedBase').value) || 42;
        const model_id = document.getElementById('modelSelect').value || null;
        await updateStory({ seed_base, model_id });
        showToast('一致性設定已儲存');
    }

    async function updateStory(updates) {
        try {
            const res = await fetch(`/api/stories/${currentStory.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });
            const data = await res.json();
            if (data.success) currentStory = data.story;
        } catch (e) { console.error(e); }
    }

    // ==================== 角色管理 ====================

    function renderCharacters() {
        const list = document.getElementById('characterList');
        const chars = currentStory?.characters || [];
        if (!chars.length) {
            list.innerHTML = '<p class="empty-hint">尚未建立角色。角色描述會嵌入每格提示詞以確保一致性。</p>';
            return;
        }

        list.innerHTML = chars.map(c => `
            <div class="char-card" data-id="${c.id}">
                <div class="char-card-header">
                    <span class="char-name">${esc(c.name)}</span>
                    ${c.color_palette ? `<span class="char-palette">${esc(c.color_palette)}</span>` : ''}
                </div>
                <p class="char-appearance">${esc(c.appearance)}</p>
                <div class="char-actions">
                    <button class="char-edit-btn" data-id="${c.id}">編輯</button>
                    <button class="char-del-btn" data-id="${c.id}">刪除</button>
                </div>
            </div>
        `).join('');

        list.querySelectorAll('.char-edit-btn').forEach(btn => {
            btn.addEventListener('click', () => openCharDialog(btn.dataset.id));
        });
        list.querySelectorAll('.char-del-btn').forEach(btn => {
            btn.addEventListener('click', () => removeCharacter(btn.dataset.id));
        });
    }

    function openCharDialog(charId) {
        editingCharId = charId || null;
        const dialog = document.getElementById('addCharDialog');
        const titleEl = document.getElementById('charDialogTitle');

        if (charId) {
            const char = currentStory.characters.find(c => c.id === charId);
            if (!char) return;
            titleEl.textContent = '編輯角色';
            document.getElementById('charName').value = char.name;
            document.getElementById('charAppearance').value = char.appearance;
            document.getElementById('charColorPalette').value = char.color_palette || '';
        } else {
            titleEl.textContent = '新增角色';
            document.getElementById('charName').value = '';
            document.getElementById('charAppearance').value = '';
            document.getElementById('charColorPalette').value = '';
        }
        dialog.style.display = 'flex';
    }

    async function confirmCharacter() {
        const name = document.getElementById('charName').value.trim();
        const appearance = document.getElementById('charAppearance').value.trim();
        const color_palette = document.getElementById('charColorPalette').value.trim();

        if (!name || !appearance) { alert('名稱和外貌描述為必填'); return; }

        try {
            if (editingCharId) {
                await fetch(`/api/stories/${currentStory.id}/characters/${editingCharId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, appearance, color_palette })
                });
            } else {
                await fetch(`/api/stories/${currentStory.id}/characters`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, appearance, color_palette })
                });
            }
            document.getElementById('addCharDialog').style.display = 'none';
            await refreshStory();
            renderCharacters();
            renderPanels();
        } catch (e) { alert('儲存失敗'); }
    }

    async function removeCharacter(charId) {
        if (!confirm('確定刪除此角色？')) return;
        try {
            await fetch(`/api/stories/${currentStory.id}/characters/${charId}`, { method: 'DELETE' });
            await refreshStory();
            renderCharacters();
            renderPanels();
        } catch (e) { alert('刪除失敗'); }
    }

    // ==================== 面板編輯 ====================

    function renderPanels() {
        const editor = document.getElementById('panelEditor');
        const panels = currentStory?.panels || [];
        const chars = currentStory?.characters || [];
        const cameraAngles = presets.camera_angles || [];
        const moods = presets.moods || [];

        editor.innerHTML = panels.map((p, i) => `
            <div class="panel-card ${p.status === 'done' ? 'done' : ''} ${p.status === 'generating' ? 'generating' : ''}" data-index="${i}">
                <div class="panel-card-header">
                    <span class="panel-num">第 ${i + 1} 格</span>
                    <span class="panel-hint">${esc(p.structure_hint || '')}</span>
                    <span class="panel-status status-${p.status}">${statusLabel(p.status)}</span>
                    ${panels.length > 1 ? `<button class="panel-remove-btn" data-index="${i}" title="刪除面板">&#x2715;</button>` : ''}
                </div>

                <div class="panel-card-body">
                    <div class="panel-field">
                        <label>場景描述 (英文)</label>
                        <textarea class="panel-scene-input" data-index="${i}" rows="3"
                            placeholder="例如：${i === 0 ? 'a girl standing at the edge of a cliff, looking at a distant castle, sunrise' : 'close-up of the girl showing surprise, a dragon appears in the sky behind her'}">${p.scene_description || ''}</textarea>
                    </div>

                    <div class="panel-row">
                        <div class="panel-field half">
                            <label>角色</label>
                            <div class="char-checkboxes">
                                ${chars.map(c => `
                                    <label class="char-check-label">
                                        <input type="checkbox" class="panel-char-check" data-index="${i}" data-char="${c.id}"
                                            ${(p.character_ids || []).includes(c.id) ? 'checked' : ''}>
                                        ${esc(c.name)}
                                    </label>
                                `).join('') || '<span class="empty-hint-sm">先建立角色</span>'}
                            </div>
                        </div>
                        <div class="panel-field quarter">
                            <label>鏡頭</label>
                            <select class="panel-camera-select" data-index="${i}">
                                ${cameraAngles.map(a => `<option value="${a}" ${a === p.camera_angle ? 'selected' : ''}>${a}</option>`).join('')}
                            </select>
                        </div>
                        <div class="panel-field quarter">
                            <label>氛圍</label>
                            <select class="panel-mood-select" data-index="${i}">
                                <option value="">無</option>
                                ${moods.map(m => `<option value="${m}" ${m === p.mood ? 'selected' : ''}>${m}</option>`).join('')}
                            </select>
                        </div>
                    </div>

                    <div class="panel-card-actions">
                        <button class="panel-save-btn" data-index="${i}">儲存面板</button>
                        <button class="panel-gen-btn" data-index="${i}">生成此格</button>
                    </div>
                </div>

                ${p.status === 'done' && p.generated_image ? `
                    <div class="panel-result">
                        <img src="/api/stories/${currentStory.id}/panels/${i}/image" alt="面板 ${i + 1}">
                    </div>
                ` : ''}
                ${p.status === 'generating' ? `
                    <div class="panel-result generating">
                        <div class="panel-spinner"></div>
                        <span>生成中...</span>
                    </div>
                ` : ''}
            </div>
        `).join('');

        // 綁定事件
        editor.querySelectorAll('.panel-save-btn').forEach(btn => {
            btn.addEventListener('click', () => savePanel(parseInt(btn.dataset.index)));
        });
        editor.querySelectorAll('.panel-gen-btn').forEach(btn => {
            btn.addEventListener('click', () => generatePanel(parseInt(btn.dataset.index)));
        });
        editor.querySelectorAll('.panel-remove-btn').forEach(btn => {
            btn.addEventListener('click', () => removePanel(parseInt(btn.dataset.index)));
        });
    }

    async function savePanel(index) {
        const scene = document.querySelector(`.panel-scene-input[data-index="${index}"]`)?.value || '';
        const camera = document.querySelector(`.panel-camera-select[data-index="${index}"]`)?.value || 'medium shot';
        const mood = document.querySelector(`.panel-mood-select[data-index="${index}"]`)?.value || '';

        const charChecks = document.querySelectorAll(`.panel-char-check[data-index="${index}"]:checked`);
        const character_ids = Array.from(charChecks).map(c => c.dataset.char);

        try {
            await fetch(`/api/stories/${currentStory.id}/panels/${index}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scene_description: scene, character_ids, camera_angle: camera, mood })
            });
            await refreshStory();
            renderPanels();
            showToast(`面板 ${index + 1} 已儲存`);
        } catch (e) { alert('儲存失敗'); }
    }

    async function addPanel() {
        try {
            await fetch(`/api/stories/${currentStory.id}/panels`, { method: 'POST' });
            await refreshStory();
            renderPanels();
        } catch (e) { alert('新增失敗'); }
    }

    async function removePanel(index) {
        if (!confirm(`確定刪除第 ${index + 1} 格？`)) return;
        try {
            await fetch(`/api/stories/${currentStory.id}/panels/${index}`, { method: 'DELETE' });
            await refreshStory();
            renderPanels();
            renderPreview();
        } catch (e) { alert('刪除失敗'); }
    }

    // ==================== 生成 ====================

    async function checkModelReady() {
        /**
         * 檢查模型是否已就緒
         * 返回 true 表示可以生成，false 表示不行（已顯示提示）
         */
        try {
            const res = await fetch('/models/active');
            const data = await res.json();

            if (data.is_loading) {
                alert(`模型「${data.loading_model_name}」正在載入中，請稍候再試。\n\n模型載入通常需要 30-60 秒。`);
                return false;
            }

            if (!data.model) {
                alert('尚未載入任何 AI 模型。\n\n請回到「生成器」頁面，系統會自動載入預設模型。\n或在模型選擇器中手動載入。');
                return false;
            }

            return true;
        } catch (e) {
            alert('無法連線到伺服器，請確認服務是否正在運行。');
            return false;
        }
    }

    async function generatePanel(index) {
        // 檢查模型狀態
        if (!await checkModelReady()) return;

        // 先儲存面板
        await savePanel(index);

        const card = document.querySelector(`.panel-card[data-index="${index}"]`);
        if (card) card.classList.add('generating');

        try {
            const res = await fetch(`/api/stories/${currentStory.id}/generate/${index}`, { method: 'POST' });
            const data = await res.json();

            if (data.success) {
                showToast(`面板 ${index + 1} 生成成功`);
            } else {
                alert(`生成失敗: ${data.error}`);
            }
        } catch (e) {
            alert('生成請求失敗');
        }

        await refreshStory();
        renderPanels();
        renderPreview();
    }

    async function generateAll() {
        // 檢查模型狀態
        if (!await checkModelReady()) return;

        // 先儲存所有面板
        const panels = currentStory?.panels || [];
        for (let i = 0; i < panels.length; i++) {
            await savePanel(i);
        }

        document.getElementById('generateAllBtn').disabled = true;
        document.getElementById('generateAllBtn').textContent = '生成中...';

        try {
            const res = await fetch(`/api/stories/${currentStory.id}/generate-all`, { method: 'POST' });
            const data = await res.json();

            if (data.success) {
                showToast(`完成！成功 ${data.succeeded}/${data.total} 格`);
            } else {
                alert(`生成失敗: ${data.error}`);
            }
        } catch (e) {
            alert('生成請求失敗');
        }

        document.getElementById('generateAllBtn').disabled = false;
        document.getElementById('generateAllBtn').textContent = '生成全部面板';

        await refreshStory();
        renderPanels();
        renderPreview();
    }

    // ==================== 預覽 ====================

    function renderPreview() {
        const container = document.getElementById('comicPreview');
        const panels = currentStory?.panels || [];
        const donePanels = panels.filter(p => p.status === 'done');

        if (!donePanels.length) {
            container.innerHTML = '<div class="preview-empty"><p>設定場景後生成面板</p><p>預覽將在此顯示</p></div>';
            return;
        }

        const layout = currentStory.layout || '4koma';
        container.className = `comic-preview layout-${layout}`;

        container.innerHTML = panels.map((p, i) => {
            if (p.status === 'done' && p.generated_image) {
                return `<div class="preview-panel">
                    <img src="/api/stories/${currentStory.id}/panels/${i}/image" alt="面板 ${i + 1}">
                    <span class="preview-panel-num">${i + 1}</span>
                </div>`;
            }
            return `<div class="preview-panel empty-panel">
                <span>${i + 1}</span>
            </div>`;
        }).join('');
    }

    async function previewPrompts() {
        try {
            const res = await fetch(`/api/stories/${currentStory.id}/preview-prompts`);
            const data = await res.json();
            if (!data.success) return;

            const content = document.getElementById('promptPreviewContent');
            content.innerHTML = (data.prompts || []).map((p, i) => `
                <div class="prompt-preview-card">
                    <div class="prompt-preview-header">
                        <span>面板 ${i + 1}</span>
                        <span class="prompt-seed">Seed: ${p.seed}</span>
                        <span class="prompt-size">${p.width}x${p.height}</span>
                    </div>
                    <div class="prompt-preview-body">
                        <p class="prompt-text">${esc(p.prompt)}</p>
                        ${p.negative_prompt ? `<p class="prompt-neg">Negative: ${esc(p.negative_prompt)}</p>` : ''}
                    </div>
                </div>
            `).join('');

            document.getElementById('promptPreviewDialog').style.display = 'flex';
        } catch (e) { alert('預覽失敗'); }
    }

    // ==================== 工具 ====================

    async function refreshStory() {
        if (!currentStory) return;
        try {
            const res = await fetch(`/api/stories/${currentStory.id}`);
            const data = await res.json();
            if (data.success) currentStory = data.story;
        } catch (e) { /* ignore */ }
    }

    function statusLabel(status) {
        const map = { empty: '未設定', ready: '待生成', generating: '生成中', done: '已完成', error: '錯誤' };
        return map[status] || status;
    }

    function esc(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function showToast(msg) {
        let t = document.getElementById('storyToast');
        if (!t) {
            t = document.createElement('div');
            t.id = 'storyToast';
            t.className = 'action-toast';
            document.body.appendChild(t);
        }
        t.textContent = msg;
        t.classList.add('show');
        setTimeout(() => t.classList.remove('show'), 2500);
    }

})();
