/**
 * Favorites Manager - 提示詞收藏管理
 */

// 載入收藏列表
async function loadFavorites() {
    try {
        const response = await fetch('/favorites');
        const data = await response.json();

        if (data.success) {
            renderFavoritesList(data.favorites);
        }
    } catch (error) {
        console.error('載入收藏失敗:', error);
    }
}

// 渲染收藏列表
function renderFavoritesList(favorites) {
    const container = document.getElementById('favoritesList');
    if (!container) return;

    if (favorites.length === 0) {
        container.innerHTML = '<p class="favorites-empty">尚無收藏的提示詞</p>';
        return;
    }

    container.innerHTML = '';

    favorites.forEach(fav => {
        const item = document.createElement('div');
        item.className = 'favorite-item';
        item.dataset.id = fav.id;

        const content = document.createElement('div');
        content.className = 'favorite-content';
        content.addEventListener('click', () => useFavorite(fav.id, fav.prompt));

        const nameSpan = document.createElement('span');
        nameSpan.className = 'favorite-name';
        nameSpan.textContent = fav.name;

        const countSpan = document.createElement('span');
        countSpan.className = 'favorite-count';
        countSpan.textContent = `使用 ${fav.use_count || 0} 次`;

        content.appendChild(nameSpan);
        content.appendChild(countSpan);

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'favorite-delete-btn';
        deleteBtn.title = '移除收藏';
        deleteBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M6 6L18 18M6 18L18 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
        `;
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            removeFavorite(fav.id);
        });

        item.appendChild(content);
        item.appendChild(deleteBtn);
        container.appendChild(item);
    });
}

// 新增收藏
async function addToFavorites() {
    const promptInput = document.getElementById('prompt');
    if (!promptInput) return;

    const prompt = promptInput.value.trim();
    if (!prompt) {
        alert('請先輸入提示詞');
        return;
    }

    try {
        const response = await fetch('/favorites', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });

        const data = await response.json();

        if (data.success) {
            loadFavorites();
            updateFavoriteButton(true);
        } else {
            alert(data.error || '新增收藏失敗');
        }
    } catch (error) {
        console.error('新增收藏失敗:', error);
        alert('新增收藏失敗');
    }
}

// 移除收藏
async function removeFavorite(favoriteId) {
    if (!confirm('確定要移除此收藏嗎？')) return;

    try {
        const response = await fetch(`/favorites/${favoriteId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            loadFavorites();
        }
    } catch (error) {
        console.error('移除收藏失敗:', error);
    }
}

// 使用收藏
async function useFavorite(favoriteId, prompt) {
    const promptInput = document.getElementById('prompt');
    if (promptInput) {
        promptInput.value = prompt;
        promptInput.dispatchEvent(new Event('input'));
    }

    // 更新使用次數
    try {
        await fetch(`/favorites/${favoriteId}/use`, { method: 'POST' });
        loadFavorites();
    } catch (error) {
        console.error('更新使用次數失敗:', error);
    }
}

// 更新收藏按鈕狀態
function updateFavoriteButton(isFavorited) {
    const btn = document.getElementById('addFavoriteBtn');
    if (btn) {
        btn.classList.toggle('favorited', isFavorited);
    }
}

// HTML 轉義
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/'/g, "&#39;").replace(/"/g, "&quot;");
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadFavorites();

    // 綁定收藏按鈕
    const addBtn = document.getElementById('addFavoriteBtn');
    if (addBtn) {
        addBtn.addEventListener('click', addToFavorites);
    }
});
