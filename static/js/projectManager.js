/**
 * Project Manager - 專案管理前端
 */
(function () {
    'use strict';

    let currentProjectId = null;
    let projectsCache = [];

    document.addEventListener('DOMContentLoaded', () => {
        loadProjects();
        initEventListeners();
    });

    function initEventListeners() {
        const createBtn = document.getElementById('createProjectBtn');
        if (createBtn) createBtn.addEventListener('click', () => {
            document.getElementById('createProjectDialog').style.display = 'flex';
        });

        const closeBtn = document.getElementById('closeProjectDialog');
        const cancelBtn = document.getElementById('cancelProjectBtn');
        if (closeBtn) closeBtn.addEventListener('click', closeDialog);
        if (cancelBtn) cancelBtn.addEventListener('click', closeDialog);

        const confirmBtn = document.getElementById('confirmProjectBtn');
        if (confirmBtn) confirmBtn.addEventListener('click', handleCreateProject);

        const backBtn = document.getElementById('backToProjectsBtn');
        if (backBtn) backBtn.addEventListener('click', () => {
            document.getElementById('projectDetailPage').style.display = 'none';
            document.getElementById('projectListPage').style.display = 'block';
            loadProjects();
        });

        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) statusFilter.addEventListener('change', loadProjects);

        const deleteBtn = document.getElementById('deleteProjectBtn');
        if (deleteBtn) deleteBtn.addEventListener('click', handleDeleteProject);

        const statusSelect = document.getElementById('detailStatusSelect');
        if (statusSelect) statusSelect.addEventListener('change', async () => {
            if (!currentProjectId) return;
            await fetch(`/api/projects/${currentProjectId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: statusSelect.value })
            });
        });

        const notesField = document.getElementById('detailNotes');
        if (notesField) {
            let saveTimeout;
            notesField.addEventListener('input', () => {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(async () => {
                    if (!currentProjectId) return;
                    await fetch(`/api/projects/${currentProjectId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ notes: notesField.value })
                    });
                }, 800);
            });
        }
    }

    // ===== 列表 =====
    async function loadProjects() {
        try {
            const status = document.getElementById('statusFilter')?.value || '';
            const url = status ? `/api/projects?status=${status}` : '/api/projects';
            const res = await fetch(url);
            const data = await res.json();

            projectsCache = data.projects || [];
            renderProjectList(projectsCache);
        } catch (e) {
            console.error('載入專案失敗:', e);
        }
    }

    function renderProjectList(projects) {
        const grid = document.getElementById('projectsGrid');
        if (!projects.length) {
            grid.innerHTML = '<p class="empty-state">尚未建立任何專案，點擊右上方按鈕開始</p>';
            return;
        }

        grid.innerHTML = '';
        projects.forEach(p => {
            const card = document.createElement('div');
            card.className = 'project-card';

            const statusClass = p.status || 'active';
            const statusLabel = { active: '進行中', completed: '已完成', archived: '已歸檔' }[statusClass] || statusClass;
            const date = new Date(p.created_at).toLocaleDateString('zh-TW');

            card.innerHTML = `
                <div class="project-card-top">
                    <h3 class="project-card-name">${p.name}</h3>
                    <span class="project-status-badge ${statusClass}">${statusLabel}</span>
                </div>
                ${p.description ? `<p class="project-card-desc">${p.description}</p>` : ''}
                <div class="project-card-meta">
                    <span class="project-image-count">${p.image_count || 0} 張圖片</span>
                    <span>${date}</span>
                </div>
            `;

            card.addEventListener('click', () => openProjectDetail(p.id));
            grid.appendChild(card);
        });
    }

    // ===== 詳情 =====
    async function openProjectDetail(projectId) {
        try {
            const res = await fetch(`/api/projects/${projectId}`);
            const data = await res.json();
            if (!data.success) return;

            const project = data.project;
            currentProjectId = projectId;

            document.getElementById('projectListPage').style.display = 'none';
            document.getElementById('projectDetailPage').style.display = 'block';

            document.getElementById('detailProjectName').textContent = project.name;
            document.getElementById('detailProjectDesc').textContent = project.description || '';
            document.getElementById('detailStatusSelect').value = project.status || 'active';
            document.getElementById('detailNotes').value = project.notes || '';

            // 統計
            const statsRes = await fetch(`/api/projects/${projectId}/stats`);
            const statsData = await statsRes.json();
            if (statsData.success) {
                const s = statsData.stats;
                document.getElementById('detailImageCount').textContent = s.total_images;
                document.getElementById('detailAvgRating').textContent = s.avg_rating || '-';
                document.getElementById('detailModelsUsed').textContent = s.models_used.length;
            }

            // 設定
            const settings = project.settings || {};
            const settingsDiv = document.getElementById('detailSettings');
            let hasSettings = false;
            if (settings.default_model) {
                document.getElementById('settingModel').textContent = `模型: ${settings.default_model}`;
                hasSettings = true;
            }
            if (settings.default_style) {
                document.getElementById('settingStyle').textContent = `風格: ${settings.default_style}`;
                hasSettings = true;
            }
            settingsDiv.style.display = hasSettings ? 'flex' : 'none';

            // 圖片
            renderProjectImages(project.images || []);

        } catch (e) {
            console.error('載入專案詳情失敗:', e);
        }
    }

    function renderProjectImages(images) {
        const grid = document.getElementById('detailImagesGrid');
        if (!images.length) {
            grid.innerHTML = '<p class="empty-state">這個專案還沒有圖片。在生成器中選擇「加入專案」即可添加。</p>';
            return;
        }

        grid.innerHTML = '';
        images.forEach(img => {
            const card = document.createElement('div');
            card.className = 'detail-image-card';

            const rating = img.rating || 0;
            const stars = [1, 2, 3, 4, 5].map(i =>
                `<button class="star-btn ${i <= rating ? 'active' : ''}" data-rating="${i}" data-filename="${img.filename}">★</button>`
            ).join('');

            card.innerHTML = `
                <img src="${img.image_url}" alt="${img.prompt || ''}" loading="lazy">
                <div class="detail-image-info">
                    <div class="detail-image-prompt">${img.prompt || ''}</div>
                    <div class="detail-image-actions">
                        <div class="star-rating">${stars}</div>
                        <button class="remove-image-btn" data-filename="${img.filename}" title="移除">✕</button>
                    </div>
                </div>
            `;

            // 星星評分
            card.querySelectorAll('.star-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const r = parseInt(btn.dataset.rating);
                    const fn = btn.dataset.filename;
                    await fetch(`/api/projects/${currentProjectId}/images/${fn}/rate`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ rating: r })
                    });
                    openProjectDetail(currentProjectId);
                });
            });

            // 移除
            card.querySelector('.remove-image-btn')?.addEventListener('click', async (e) => {
                e.stopPropagation();
                const fn = e.currentTarget.dataset.filename;
                if (!confirm('確定要從專案中移除這張圖片？')) return;
                await fetch(`/api/projects/${currentProjectId}/images/${fn}`, { method: 'DELETE' });
                openProjectDetail(currentProjectId);
            });

            grid.appendChild(card);
        });
    }

    // ===== 建立 =====
    async function handleCreateProject() {
        const name = document.getElementById('newProjectName').value.trim();
        if (!name) { alert('請輸入專案名稱'); return; }

        const description = document.getElementById('newProjectDesc').value.trim();
        const negPrompt = document.getElementById('defaultNegPrompt').value.trim();

        try {
            const res = await fetch('/api/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, description, default_negative_prompt: negPrompt })
            });
            const data = await res.json();
            if (data.success) { closeDialog(); loadProjects(); }
            else { alert(data.error || '建立失敗'); }
        } catch (e) { alert('建立專案失敗: ' + e.message); }
    }

    async function handleDeleteProject() {
        if (!currentProjectId) return;
        if (!confirm('確定要刪除此專案？圖片檔案不會被刪除。')) return;

        await fetch(`/api/projects/${currentProjectId}`, { method: 'DELETE' });
        currentProjectId = null;
        document.getElementById('projectDetailPage').style.display = 'none';
        document.getElementById('projectListPage').style.display = 'block';
        loadProjects();
    }

    function closeDialog() {
        document.getElementById('createProjectDialog').style.display = 'none';
        document.getElementById('newProjectName').value = '';
        document.getElementById('newProjectDesc').value = '';
        document.getElementById('defaultNegPrompt').value = '';
    }

})();
