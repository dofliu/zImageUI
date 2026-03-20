/**
 * Gallery Manager - 作品集展示管理
 */
(function () {
    'use strict';

    let currentGalleryId = null;
    let currentGalleryImages = [];
    let lightboxIndex = 0;

    // ===== 頁面初始化 =====
    document.addEventListener('DOMContentLoaded', () => {
        // 檢查 URL 是否指定了作品集
        const pathParts = window.location.pathname.split('/');
        if (pathParts.length >= 3 && pathParts[1] === 'gallery' && pathParts[2]) {
            loadGalleryView(pathParts[2]);
        } else {
            loadGalleryList();
        }

        initEventListeners();
    });

    function initEventListeners() {
        // 建立作品集
        const createBtn = document.getElementById('createGalleryBtn');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                document.getElementById('createGalleryDialog').style.display = 'flex';
            });
        }

        // 關閉建立對話框
        const closeBtn = document.getElementById('closeCreateDialog');
        const cancelBtn = document.getElementById('cancelCreateBtn');
        if (closeBtn) closeBtn.addEventListener('click', closeCreateDialog);
        if (cancelBtn) cancelBtn.addEventListener('click', closeCreateDialog);

        // 確認建立
        const confirmBtn = document.getElementById('confirmCreateBtn');
        if (confirmBtn) confirmBtn.addEventListener('click', handleCreateGallery);

        // 佈局選項
        document.querySelectorAll('.layout-option').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.layout-option').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // 主題選項
        document.querySelectorAll('.theme-option').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.theme-option').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // 返回列表
        const backBtn = document.getElementById('backToListBtn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                document.getElementById('galleryViewPage').style.display = 'none';
                document.getElementById('galleryListPage').style.display = 'block';
                history.pushState(null, '', '/gallery');
                loadGalleryList();
            });
        }

        // 分享
        const shareBtn = document.getElementById('shareGalleryBtn');
        if (shareBtn) {
            shareBtn.addEventListener('click', () => {
                const url = window.location.href;
                navigator.clipboard.writeText(url).then(() => {
                    alert('連結已複製到剪貼簿！');
                }).catch(() => {
                    prompt('分享連結：', url);
                });
            });
        }

        // Lightbox
        const lbClose = document.getElementById('lightboxClose');
        const lbPrev = document.getElementById('lightboxPrev');
        const lbNext = document.getElementById('lightboxNext');
        if (lbClose) lbClose.addEventListener('click', closeLightbox);
        if (lbPrev) lbPrev.addEventListener('click', () => navigateLightbox(-1));
        if (lbNext) lbNext.addEventListener('click', () => navigateLightbox(1));

        // 鍵盤控制 Lightbox
        document.addEventListener('keydown', (e) => {
            const lightbox = document.getElementById('lightbox');
            if (lightbox && lightbox.style.display !== 'none') {
                if (e.key === 'Escape') closeLightbox();
                if (e.key === 'ArrowLeft') navigateLightbox(-1);
                if (e.key === 'ArrowRight') navigateLightbox(1);
            }
        });
    }

    // ===== 作品集列表 =====
    async function loadGalleryList() {
        try {
            const response = await fetch('/api/galleries');
            const data = await response.json();

            const grid = document.getElementById('galleriesGrid');
            if (!data.success || !data.galleries || data.galleries.length === 0) {
                grid.innerHTML = '<p class="empty-state">尚未建立任何作品集，點擊上方按鈕開始建立</p>';
                return;
            }

            grid.innerHTML = '';
            data.galleries.forEach(gallery => {
                const card = createGalleryCard(gallery);
                grid.appendChild(card);
            });
        } catch (error) {
            console.error('載入作品集失敗:', error);
        }
    }

    function createGalleryCard(gallery) {
        const card = document.createElement('div');
        card.className = 'gallery-card';

        const coverHTML = gallery.cover_image
            ? `<img class="gallery-card-cover" src="${gallery.cover_image}" alt="${gallery.title}">`
            : `<div class="gallery-card-cover no-image">🖼</div>`;

        const date = new Date(gallery.created_at).toLocaleDateString('zh-TW');

        card.innerHTML = `
            ${coverHTML}
            <div class="gallery-card-info">
                <h3 class="gallery-card-title">${gallery.title}</h3>
                ${gallery.description ? `<p class="gallery-card-desc">${gallery.description}</p>` : ''}
                <div class="gallery-card-meta">
                    <span class="image-count">${gallery.image_count} 張圖片</span>
                    <span>${date}</span>
                </div>
            </div>
        `;

        card.addEventListener('click', () => {
            loadGalleryView(gallery.id);
            history.pushState(null, '', `/gallery/${gallery.id}`);
        });

        return card;
    }

    // ===== 作品集檢視 =====
    async function loadGalleryView(galleryId) {
        try {
            const response = await fetch(`/api/galleries/${galleryId}`);
            const data = await response.json();

            if (!data.success) {
                alert('作品集不存在');
                return;
            }

            const gallery = data.gallery;
            currentGalleryId = galleryId;
            currentGalleryImages = gallery.images || [];

            // 更新頁面
            document.getElementById('galleryListPage').style.display = 'none';
            document.getElementById('galleryViewPage').style.display = 'block';

            document.getElementById('galleryTitle').textContent = gallery.title;
            document.getElementById('galleryDescription').textContent = gallery.description || '';
            document.getElementById('galleryViews').textContent = `${gallery.views || 0} 次瀏覽`;

            // 渲染圖片
            const container = document.getElementById('galleryImages');
            container.innerHTML = '';

            if (currentGalleryImages.length === 0) {
                container.innerHTML = '<p class="empty-state">這個作品集還沒有圖片</p>';
                return;
            }

            currentGalleryImages.forEach((img, index) => {
                const item = document.createElement('div');
                item.className = 'gallery-image-item';
                item.innerHTML = `
                    <img src="${img.image_url}" alt="${img.caption || img.prompt || ''}" loading="lazy">
                    <div class="image-overlay">
                        ${img.caption ? `<p class="caption">${img.caption}</p>` : ''}
                        ${img.prompt ? `<p class="prompt-text">${img.prompt}</p>` : ''}
                    </div>
                `;
                item.addEventListener('click', () => openLightbox(index));
                container.appendChild(item);
            });

        } catch (error) {
            console.error('載入作品集失敗:', error);
        }
    }

    // ===== 建立作品集 =====
    async function handleCreateGallery() {
        const title = document.getElementById('newGalleryTitle').value.trim();
        if (!title) {
            alert('請輸入作品集名稱');
            return;
        }

        const description = document.getElementById('newGalleryDesc').value.trim();
        const layout = document.querySelector('.layout-option.active')?.dataset.layout || 'masonry';
        const theme = document.querySelector('.theme-option.active')?.dataset.theme || 'default';

        try {
            const response = await fetch('/api/galleries', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, description, layout, theme })
            });

            const data = await response.json();
            if (data.success) {
                closeCreateDialog();
                loadGalleryList();
            } else {
                alert(data.error || '建立失敗');
            }
        } catch (error) {
            alert('建立作品集失敗: ' + error.message);
        }
    }

    function closeCreateDialog() {
        document.getElementById('createGalleryDialog').style.display = 'none';
        document.getElementById('newGalleryTitle').value = '';
        document.getElementById('newGalleryDesc').value = '';
    }

    // ===== Lightbox =====
    function openLightbox(index) {
        lightboxIndex = index;
        updateLightbox();
        document.getElementById('lightbox').style.display = 'flex';
    }

    function closeLightbox() {
        document.getElementById('lightbox').style.display = 'none';
    }

    function navigateLightbox(direction) {
        lightboxIndex += direction;
        if (lightboxIndex < 0) lightboxIndex = currentGalleryImages.length - 1;
        if (lightboxIndex >= currentGalleryImages.length) lightboxIndex = 0;
        updateLightbox();
    }

    function updateLightbox() {
        const img = currentGalleryImages[lightboxIndex];
        if (!img) return;
        document.getElementById('lightboxImage').src = img.image_url;
        document.getElementById('lightboxCaption').textContent = img.caption || '';
        document.getElementById('lightboxPrompt').textContent = img.prompt || '';
    }

})();
