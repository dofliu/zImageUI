// 進階功能：標籤系統和種子控制

// 全局變數
let allTags = [];
let currentFilterTags = [];

// 載入所有標籤
async function loadAllTags() {
    try {
        const response = await fetch('/tags');
        const data = await response.json();

        if (data.success) {
            allTags = data.tags;
            updateTagCloud();
        }
    } catch (error) {
        console.error('載入標籤失敗:', error);
    }
}

// 更新標籤雲
function updateTagCloud() {
    const tagCloud = document.getElementById('tagCloud');
    if (!tagCloud) return;

    tagCloud.innerHTML = '';

    if (allTags.length === 0) {
        tagCloud.innerHTML = '<p class="no-tags">尚無標籤</p>';
        return;
    }

    allTags.forEach(tagInfo => {
        const tagBtn = document.createElement('button');
        tagBtn.className = 'tag-btn';
        tagBtn.textContent = `${tagInfo.name} (${tagInfo.count})`;
        tagBtn.dataset.tag = tagInfo.name;

        // 點擊標籤進行過濾
        tagBtn.addEventListener('click', () => {
            toggleFilterTag(tagInfo.name);
        });

        tagCloud.appendChild(tagBtn);
    });
}

// 切換過濾標籤
function toggleFilterTag(tag) {
    const index = currentFilterTags.indexOf(tag);

    if (index > -1) {
        currentFilterTags.splice(index, 1);
    } else {
        currentFilterTags.push(tag);
    }

    updateTagCloudUI();
    filterHistoryByTags();
}

// 更新標籤雲UI狀態
function updateTagCloudUI() {
    const tagButtons = document.querySelectorAll('.tag-btn');
    tagButtons.forEach(btn => {
        const tag = btn.dataset.tag;
        if (currentFilterTags.includes(tag)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// 根據標籤過濾歷史記錄
async function filterHistoryByTags() {
    try {
        const response = await fetch('/history/filter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tags: currentFilterTags
            }),
        });

        const data = await response.json();

        if (data.success) {
            displayFilteredHistory(data.history);
        }
    } catch (error) {
        console.error('過濾歷史記錄失敗:', error);
    }
}

// 顯示過濾後的歷史記錄
function displayFilteredHistory(history) {
    const historyList = document.getElementById('historyList');
    if (!historyList) return;

    historyList.innerHTML = '';

    if (history.length === 0) {
        historyList.innerHTML = '<p class="history-empty">沒有符合條件的記錄</p>';
        return;
    }

    history.forEach(item => {
        const historyItem = createHistoryItem(item);
        historyList.appendChild(historyItem);
    });
}

// 為歷史記錄項目添加標籤編輯功能
function addTagEditor(itemElement, itemData) {
    const tagEditor = document.createElement('div');
    tagEditor.className = 'tag-editor';
    tagEditor.innerHTML = `
        <input type="text" class="tag-input" placeholder="添加標籤..." />
        <button class="add-tag-btn">+</button>
        <div class="item-tags"></div>
    `;

    const tagInput = tagEditor.querySelector('.tag-input');
    const addTagBtn = tagEditor.querySelector('.add-tag-btn');
    const itemTags = tagEditor.querySelector('.item-tags');

    // 顯示現有標籤
    function displayTags() {
        itemTags.innerHTML = '';
        if (itemData.tags && itemData.tags.length > 0) {
            itemData.tags.forEach(tag => {
                const tagSpan = document.createElement('span');
                tagSpan.className = 'item-tag';
                tagSpan.innerHTML = `${tag} <button class="remove-tag" data-tag="${tag}">×</button>`;

                tagSpan.querySelector('.remove-tag').addEventListener('click', async () => {
                    await removeTag(itemData.id, tag);
                });

                itemTags.appendChild(tagSpan);
            });
        }
    }

    // 添加標籤
    async function addTag() {
        const newTag = tagInput.value.trim();
        if (!newTag) return;

        if (!itemData.tags) {
            itemData.tags = [];
        }

        if (!itemData.tags.includes(newTag)) {
            itemData.tags.push(newTag);
            await updateItemTags(itemData.id, itemData.tags);
            tagInput.value = '';
            displayTags();
            loadAllTags(); // 重新載入標籤雲
        }
    }

    // 移除標籤
    async function removeTag(itemId, tag) {
        const index = itemData.tags.indexOf(tag);
        if (index > -1) {
            itemData.tags.splice(index, 1);
            await updateItemTags(itemId, itemData.tags);
            displayTags();
            loadAllTags();
        }
    }

    addTagBtn.addEventListener('click', addTag);
    tagInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addTag();
        }
    });

    displayTags();
    itemElement.appendChild(tagEditor);
}

// 更新項目標籤
async function updateItemTags(itemId, tags) {
    try {
        const response = await fetch(`/history/${itemId}/tags`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tags: tags
            }),
        });

        const data = await response.json();
        return data.success;
    } catch (error) {
        console.error('更新標籤失敗:', error);
        return false;
    }
}

// Seed 控制功能
function initSeedControl() {
    const seedCheckbox = document.getElementById('useSeed');
    const seedInput = document.getElementById('seedInput');
    const randomSeedBtn = document.getElementById('randomSeedBtn');

    if (!seedCheckbox || !seedInput) return;

    seedCheckbox.addEventListener('change', () => {
        seedInput.disabled = !seedCheckbox.checked;
        if (seedCheckbox.checked && !seedInput.value) {
            seedInput.value = Math.floor(Math.random() * (2**32 - 1));
        }
    });

    if (randomSeedBtn) {
        randomSeedBtn.addEventListener('click', () => {
            seedInput.value = Math.floor(Math.random() * (2**32 - 1));
        });
    }
}

// 獲取 Seed 設定
function getSeedSetting() {
    const seedCheckbox = document.getElementById('useSeed');
    const seedInput = document.getElementById('seedInput');

    if (seedCheckbox && seedCheckbox.checked && seedInput.value) {
        return parseInt(seedInput.value);
    }

    return null;
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadAllTags();
    initSeedControl();

    // 清除過濾按鈕
    const clearFilterBtn = document.getElementById('clearFilterBtn');
    if (clearFilterBtn) {
        clearFilterBtn.addEventListener('click', () => {
            currentFilterTags = [];
            updateTagCloudUI();
            if (typeof loadHistory === 'function') {
                loadHistory(); // 重新載入完整歷史
            }
        });
    }
});
