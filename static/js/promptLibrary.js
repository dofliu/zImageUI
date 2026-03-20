/**
 * Prompt Library - 提示詞庫瀏覽與使用
 * 整合到主頁側邊欄，支援分類、搜尋、評分、一鍵套用
 */
(function () {
    'use strict';

    let currentCategory = 'all';
    let currentSort = 'rating';
    let isOpen = false;

    document.addEventListener('DOMContentLoaded', () => {
        initPromptLibrary();
    });

    function initPromptLibrary() {
        const toggleBtn = document.getElementById('togglePromptLibrary');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const panel = document.getElementById('promptLibraryPanel');
                isOpen = !isOpen;
                panel.style.display = isOpen ? 'block' : 'none';
                toggleBtn.classList.toggle('expanded', isOpen);
                if (isOpen) loadPrompts();
            });
        }

        const searchInput = document.getElementById('plSearch');
        if (searchInput) {
            let timer;
            searchInput.addEventListener('input', () => {
                clearTimeout(timer);
                timer = setTimeout(() => loadPrompts(), 300);
            });
        }

        const sortSelect = document.getElementById('plSort');
        if (sortSelect) {
            sortSelect.addEventListener('change', () => {
                currentSort = sortSelect.value;
                loadPrompts();
            });
        }

        const addBtn = document.getElementById('plAddBtn');
        if (addBtn) {
            addBtn.addEventListener('click', openAddDialog);
        }
    }

    async function loadPrompts() {
        const search = document.getElementById('plSearch')?.value || '';
        const grid = document.getElementById('plGrid');
        if (!grid) return;

        grid.innerHTML = '<div class="pl-loading">載入中...</div>';

        try {
            const params = new URLSearchParams({
                category: currentCategory,
                search: search,
                sort: currentSort
            });
            const res = await fetch(`/api/prompt-library?${params}`);
            const data = await res.json();

            renderCategories(data.categories || {});
            renderPrompts(data.prompts || []);
        } catch (e) {
            grid.innerHTML = '<div class="pl-loading">載入失敗</div>';
        }
    }

    function renderCategories(categories) {
        const bar = document.getElementById('plCategories');
        if (!bar) return;

        bar.innerHTML = Object.entries(categories).map(([key, label]) =>
            `<button class="pl-cat-btn ${key === currentCategory ? 'active' : ''}" data-cat="${key}">${label}</button>`
        ).join('');

        bar.querySelectorAll('.pl-cat-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                currentCategory = btn.dataset.cat;
                bar.querySelectorAll('.pl-cat-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                loadPrompts();
            });
        });
    }

    function renderPrompts(prompts) {
        const grid = document.getElementById('plGrid');
        if (!grid) return;

        if (prompts.length === 0) {
            grid.innerHTML = '<div class="pl-empty">沒有找到提示詞</div>';
            return;
        }

        grid.innerHTML = prompts.map(p => `
            <div class="pl-card" data-id="${p.id}">
                <div class="pl-card-header">
                    <span class="pl-card-title">${escHtml(p.title)}</span>
                    <span class="pl-card-cat">${escHtml(p.category)}</span>
                </div>
                <p class="pl-card-prompt">${escHtml(p.prompt)}</p>
                ${p.negative_prompt ? `<p class="pl-card-neg">neg: ${escHtml(p.negative_prompt)}</p>` : ''}
                <div class="pl-card-tags">
                    ${(p.tags || []).map(t => `<span class="pl-tag">${escHtml(t)}</span>`).join('')}
                </div>
                <div class="pl-card-footer">
                    <div class="pl-card-rating" data-id="${p.id}">
                        ${renderStars(p.rating || 0)}
                        <span class="pl-rating-val">${(p.rating || 0).toFixed(1)}</span>
                    </div>
                    <span class="pl-use-count">${p.use_count || 0} 次使用</span>
                    <button class="pl-use-btn" data-id="${p.id}">套用</button>
                    ${!p.is_default ? `<button class="pl-del-btn" data-id="${p.id}" title="刪除">✕</button>` : ''}
                </div>
            </div>
        `).join('');

        // 綁定套用按鈕
        grid.querySelectorAll('.pl-use-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                applyPrompt(btn.dataset.id, prompts);
            });
        });

        // 綁定刪除按鈕
        grid.querySelectorAll('.pl-del-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                deletePrompt(btn.dataset.id);
            });
        });

        // 綁定星星評分
        grid.querySelectorAll('.pl-star').forEach(star => {
            star.addEventListener('click', (e) => {
                e.stopPropagation();
                const rating = parseInt(star.dataset.val);
                const id = star.closest('.pl-card-rating').dataset.id;
                ratePrompt(id, rating);
            });
        });
    }

    function renderStars(rating) {
        let html = '';
        for (let i = 1; i <= 5; i++) {
            const filled = i <= Math.round(rating);
            html += `<span class="pl-star ${filled ? 'filled' : ''}" data-val="${i}">★</span>`;
        }
        return html;
    }

    async function applyPrompt(id, prompts) {
        const p = prompts.find(x => x.id === id);
        if (!p) return;

        // 填入提示詞
        const promptEl = document.getElementById('prompt');
        if (promptEl) {
            promptEl.value = p.prompt;
            promptEl.dispatchEvent(new Event('input'));
        }

        // 填入負面提示詞
        const negEl = document.getElementById('negativePrompt');
        if (negEl && p.negative_prompt) {
            negEl.value = p.negative_prompt;
        }

        // 記錄使用
        try {
            await fetch(`/api/prompt-library/${id}/use`, { method: 'POST' });
        } catch (e) { /* ignore */ }

        showToast('已套用提示詞: ' + p.title);
    }

    async function ratePrompt(id, rating) {
        try {
            await fetch(`/api/prompt-library/${id}/rate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rating })
            });
            loadPrompts();
        } catch (e) { /* ignore */ }
    }

    async function deletePrompt(id) {
        if (!confirm('確定刪除這個提示詞？')) return;
        try {
            const res = await fetch(`/api/prompt-library/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                loadPrompts();
                showToast('已刪除');
            } else {
                alert(data.error || '刪除失敗');
            }
        } catch (e) {
            alert('刪除失敗');
        }
    }

    function openAddDialog() {
        const dialog = document.getElementById('plAddDialog');
        if (dialog) dialog.style.display = 'flex';

        const saveBtn = document.getElementById('plSaveBtn');
        const cancelBtn = document.getElementById('plCancelBtn');

        if (saveBtn) {
            saveBtn.onclick = async () => {
                const title = document.getElementById('plNewTitle')?.value?.trim();
                const prompt = document.getElementById('plNewPrompt')?.value?.trim();
                const neg = document.getElementById('plNewNeg')?.value?.trim() || '';
                const cat = document.getElementById('plNewCategory')?.value || 'custom';
                const tagsStr = document.getElementById('plNewTags')?.value?.trim() || '';
                const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];

                if (!title || !prompt) {
                    alert('請填寫標題和提示詞');
                    return;
                }

                try {
                    const res = await fetch('/api/prompt-library', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ title, prompt, negative_prompt: neg, category: cat, tags })
                    });
                    const data = await res.json();
                    if (data.success) {
                        dialog.style.display = 'none';
                        clearAddForm();
                        loadPrompts();
                        showToast('已加入提示詞庫');
                    }
                } catch (e) {
                    alert('新增失敗');
                }
            };
        }

        if (cancelBtn) {
            cancelBtn.onclick = () => {
                dialog.style.display = 'none';
                clearAddForm();
            };
        }
    }

    function clearAddForm() {
        ['plNewTitle', 'plNewPrompt', 'plNewNeg', 'plNewTags'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
    }

    function escHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

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
