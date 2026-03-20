/**
 * Action Buttons - 生成結果的快捷操作
 * 加入專案、加入作品集、圖片比較
 */
(function () {
    'use strict';

    let compareSlotA = null;
    let compareSlotB = null;
    let selectingSlot = null; // 'A' or 'B'

    document.addEventListener('DOMContentLoaded', () => {
        initActionButtons();
        initCompareMode();
    });

    function initActionButtons() {
        // 加入專案按鈕
        const projectBtn = document.getElementById('addToProjectBtn');
        if (projectBtn) {
            projectBtn.addEventListener('click', async () => {
                const dropdown = document.getElementById('projectDropdown');
                if (dropdown.style.display !== 'none') {
                    dropdown.style.display = 'none';
                    return;
                }
                // 關閉其他 dropdown
                document.getElementById('galleryDropdown').style.display = 'none';
                await loadProjectDropdown();
                dropdown.style.display = 'block';
            });
        }

        // 加入作品集按鈕
        const galleryBtn = document.getElementById('addToGalleryBtn');
        if (galleryBtn) {
            galleryBtn.addEventListener('click', async () => {
                const dropdown = document.getElementById('galleryDropdown');
                if (dropdown.style.display !== 'none') {
                    dropdown.style.display = 'none';
                    return;
                }
                document.getElementById('projectDropdown').style.display = 'none';
                await loadGalleryDropdown();
                dropdown.style.display = 'block';
            });
        }

        // 點擊外部關閉 dropdown
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.action-dropdown')) {
                document.querySelectorAll('.dropdown-menu').forEach(d => d.style.display = 'none');
            }
        });
    }

    async function loadProjectDropdown() {
        const dropdown = document.getElementById('projectDropdown');
        try {
            const res = await fetch('/api/projects');
            const data = await res.json();
            const projects = data.projects || [];

            if (projects.length === 0) {
                dropdown.innerHTML = '<div class="dropdown-empty">尚無專案，<a href="/projects">建立一個</a></div>';
                return;
            }

            dropdown.innerHTML = projects.map(p => `
                <div class="dropdown-item" data-id="${p.id}">
                    <span class="dropdown-item-name">${p.name}</span>
                    <span class="dropdown-item-count">${p.image_count || 0} 張</span>
                </div>
            `).join('');

            dropdown.querySelectorAll('.dropdown-item').forEach(item => {
                item.addEventListener('click', async () => {
                    const projectId = item.dataset.id;
                    await addToProject(projectId);
                    dropdown.style.display = 'none';
                });
            });
        } catch (e) {
            dropdown.innerHTML = '<div class="dropdown-empty">載入失敗</div>';
        }
    }

    async function loadGalleryDropdown() {
        const dropdown = document.getElementById('galleryDropdown');
        try {
            const res = await fetch('/api/galleries');
            const data = await res.json();
            const galleries = data.galleries || [];

            if (galleries.length === 0) {
                dropdown.innerHTML = '<div class="dropdown-empty">尚無作品集，<a href="/gallery">建立一個</a></div>';
                return;
            }

            dropdown.innerHTML = galleries.map(g => `
                <div class="dropdown-item" data-id="${g.id}">
                    <span class="dropdown-item-name">${g.title}</span>
                    <span class="dropdown-item-count">${g.image_count || 0} 張</span>
                </div>
            `).join('');

            dropdown.querySelectorAll('.dropdown-item').forEach(item => {
                item.addEventListener('click', async () => {
                    const galleryId = item.dataset.id;
                    await addToGallery(galleryId);
                    dropdown.style.display = 'none';
                });
            });
        } catch (e) {
            dropdown.innerHTML = '<div class="dropdown-empty">載入失敗</div>';
        }
    }

    async function addToProject(projectId) {
        const fn = window.currentFilename;
        const prompt = document.getElementById('currentPrompt')?.textContent || '';
        if (!fn) { alert('沒有可加入的圖片'); return; }

        try {
            const res = await fetch(`/api/projects/${projectId}/images`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: fn, prompt: prompt })
            });
            const data = await res.json();
            if (data.success) {
                showToast('已加入專案');
            } else {
                alert(data.error || '加入失敗');
            }
        } catch (e) {
            alert('加入專案失敗: ' + e.message);
        }
    }

    async function addToGallery(galleryId) {
        const fn = window.currentFilename;
        if (!fn) { alert('沒有可加入的圖片'); return; }

        try {
            const res = await fetch(`/api/galleries/${galleryId}/images`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filenames: [fn] })
            });
            const data = await res.json();
            if (data.success) {
                showToast('已加入作品集');
            } else {
                alert(data.error || '加入失敗');
            }
        } catch (e) {
            alert('加入作品集失敗: ' + e.message);
        }
    }

    // ===== 圖片比較模式 =====
    function initCompareMode() {
        const compareBtn = document.getElementById('compareBtn');
        if (compareBtn) {
            compareBtn.addEventListener('click', openCompareMode);
        }

        const closeBtn = document.getElementById('closeCompareBtn');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeCompareMode);
        }

        // 點擊 slot 選擇圖片
        const slotA = document.getElementById('compareSlotA');
        const slotB = document.getElementById('compareSlotB');
        if (slotA) slotA.addEventListener('click', () => { selectingSlot = 'A'; highlightHistoryForSelection(); });
        if (slotB) slotB.addEventListener('click', () => { selectingSlot = 'B'; highlightHistoryForSelection(); });
    }

    function openCompareMode() {
        // 如果有目前圖片，放入 Slot A
        const currentImg = document.getElementById('generatedImage')?.src;
        const currentPromptText = document.getElementById('currentPrompt')?.textContent || '';

        if (currentImg && currentImg !== '') {
            compareSlotA = { src: currentImg, prompt: currentPromptText };
            renderCompareSlot('A', compareSlotA);
        }

        compareSlotB = null;
        renderCompareSlot('B', null);
        document.getElementById('compareOverlay').style.display = 'flex';
    }

    function closeCompareMode() {
        document.getElementById('compareOverlay').style.display = 'none';
        selectingSlot = null;
    }

    function renderCompareSlot(slot, data) {
        const el = document.getElementById(slot === 'A' ? 'compareSlotA' : 'compareSlotB');
        if (!el) return;

        if (data && data.src) {
            el.innerHTML = `
                <img src="${data.src}" alt="比較圖片 ${slot}">
                <div class="compare-slot-info">
                    <p>${data.prompt || ''}</p>
                </div>
            `;
        } else {
            el.innerHTML = '<p class="compare-hint">點擊此處，再從歷史記錄中選擇圖片</p>';
        }
    }

    function highlightHistoryForSelection() {
        // 讓歷史記錄項目可以被選擇作為比較圖片
        const historyItems = document.querySelectorAll('.history-item');
        historyItems.forEach(item => {
            // 加入一個臨時的選擇提示
            item.style.cursor = 'crosshair';
            item.style.outline = '2px solid #8b5cf6';

            const handler = function () {
                const img = item.querySelector('img');
                const promptEl = item.querySelector('.history-item-prompt');

                if (img && selectingSlot) {
                    const data = { src: img.src, prompt: promptEl?.textContent || '' };
                    if (selectingSlot === 'A') {
                        compareSlotA = data;
                        renderCompareSlot('A', data);
                    } else {
                        compareSlotB = data;
                        renderCompareSlot('B', data);
                    }
                }

                // 清除所有高亮
                historyItems.forEach(h => {
                    h.style.cursor = '';
                    h.style.outline = '';
                    h.removeEventListener('click', handler);
                });
                selectingSlot = null;
            };

            item.addEventListener('click', handler, { once: true });
        });
    }

    // ===== Toast 通知 =====
    function showToast(message) {
        let toast = document.getElementById('actionToast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'actionToast';
            toast.className = 'action-toast';
            document.body.appendChild(toast);
        }
        toast.textContent = message;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 2500);
    }

})();
