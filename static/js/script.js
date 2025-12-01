// DOM 元素
const promptInput = document.getElementById('prompt');
const charCount = document.getElementById('charCount');
const generateBtn = document.getElementById('generateBtn');
const btnText = document.getElementById('btnText');
const loadingSection = document.getElementById('loadingSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');
const welcomeSection = document.getElementById('welcomeSection');
const generatedImage = document.getElementById('generatedImage');
const currentPrompt = document.getElementById('currentPrompt');
const filename = document.getElementById('filename');
const errorMessage = document.getElementById('errorMessage');
const downloadBtn = document.getElementById('downloadBtn');
const retryBtn = document.getElementById('retryBtn');
const historyList = document.getElementById('historyList');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');

// 批量生成相關元素
const singleModeBtn = document.getElementById('singleModeBtn');
const batchModeBtn = document.getElementById('batchModeBtn');
const singleModeInput = document.getElementById('singleModeInput');
const batchModeInput = document.getElementById('batchModeInput');
const batchPrompts = document.getElementById('batchPrompts');
const batchCount = document.getElementById('batchCount');
const batchProgress = document.getElementById('batchProgress');
const currentProgress = document.getElementById('currentProgress');
const totalProgress = document.getElementById('totalProgress');
const batchProgressBar = document.getElementById('batchProgressBar');
const batchResultSection = document.getElementById('batchResultSection');
const batchResultGrid = document.getElementById('batchResultGrid');
const batchSuccessCount = document.getElementById('batchSuccessCount');
const batchFailCount = document.getElementById('batchFailCount');
const batchDownloadBtn = document.getElementById('batchDownloadBtn');

let currentImageData = null;
let currentFilename = null;
let currentMode = 'single'; // 'single' or 'batch'
let batchResults = []; // 存儲批量結果

// 設置 currentFilename 並同步到全域作用域
function setCurrentFilename(filename) {
    currentFilename = filename;
    if (typeof window !== 'undefined') {
        window.currentFilename = filename;
    }
}

// 字數計數器
if (promptInput && charCount) {
    promptInput.addEventListener('input', () => {
        const count = promptInput.value.length;
        charCount.textContent = `${count} 字`;
    });
}

// 批量提示詞計數器
if (batchPrompts && batchCount) {
    batchPrompts.addEventListener('input', () => {
        const lines = batchPrompts.value.split('\n').filter(line => line.trim() !== '');
        batchCount.textContent = `${lines.length} 個提示詞`;
    });
}

// 模式切換
if (singleModeBtn && batchModeBtn) {
    singleModeBtn.addEventListener('click', () => {
        currentMode = 'single';
        singleModeBtn.classList.add('active');
        batchModeBtn.classList.remove('active');
        if (singleModeInput) singleModeInput.style.display = 'block';
        if (batchModeInput) batchModeInput.style.display = 'none';
        if (btnText) btnText.textContent = '開始生成圖片';
    });

    batchModeBtn.addEventListener('click', () => {
        currentMode = 'batch';
        batchModeBtn.classList.add('active');
        singleModeBtn.classList.remove('active');
        if (singleModeInput) singleModeInput.style.display = 'none';
        if (batchModeInput) batchModeInput.style.display = 'block';
        if (btnText) btnText.textContent = '開始批量生成';
    });
}

// 載入歷史記錄
async function loadHistory() {
    try {
        const response = await fetch('/history');
        const data = await response.json();

        if (data.success && data.history.length > 0) {
            historyList.innerHTML = '';
            data.history.forEach(item => {
                const historyItem = createHistoryItem(item);
                historyList.appendChild(historyItem);
            });
        } else {
            historyList.innerHTML = '<p class="history-empty">尚無歷史記錄</p>';
        }
    } catch (error) {
        console.error('載入歷史記錄失敗:', error);
    }
}

// 創建歷史記錄項目
function createHistoryItem(item) {
    const div = document.createElement('div');
    div.className = 'history-item';

    // 如果在多選模式，添加 checkbox
    if (typeof selectMode !== 'undefined' && selectMode) {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'history-item-checkbox';
        checkbox.setAttribute('data-filename', item.filename);

        // 檢查是否已選中
        if (typeof selectedFiles !== 'undefined' && selectedFiles.has(item.filename)) {
            checkbox.checked = true;
        }

        // checkbox 點擊事件
        checkbox.addEventListener('click', (e) => {
            e.stopPropagation();  // 防止觸發項目點擊
            if (typeof toggleFileSelection === 'function') {
                toggleFileSelection(item.filename, checkbox);
            }
        });

        div.appendChild(checkbox);
    }

    const img = document.createElement('img');
    img.className = 'history-item-thumbnail';
    img.src = item.image_url;
    img.alt = '歷史圖片';

    const content = document.createElement('div');
    content.className = 'history-item-content';

    const promptText = document.createElement('div');
    promptText.className = 'history-item-prompt';
    promptText.textContent = item.prompt;

    const timeText = document.createElement('div');
    timeText.className = 'history-item-time';
    const date = new Date(item.timestamp);
    timeText.textContent = formatDate(date);

    content.appendChild(promptText);
    content.appendChild(timeText);

    div.appendChild(img);
    div.appendChild(content);

    // 點擊歷史記錄項目顯示該圖片（非多選模式或點擊非 checkbox 區域）
    div.addEventListener('click', (e) => {
        // 安全檢查 selectMode 是否存在
        const isSelectMode = typeof selectMode !== 'undefined' && selectMode;
        if (!isSelectMode || e.target.tagName !== 'INPUT') {
            showHistoryImage(item);
        }
    });

    return div;
}

// 顯示歷史圖片
function showHistoryImage(item) {
    hideAllSections();

    generatedImage.src = item.image_url;
    currentPrompt.textContent = item.prompt;
    filename.textContent = `檔案名稱: ${item.filename}`;

    currentImageData = item.image_url;
    setCurrentFilename(item.filename);

    resultSection.style.display = 'block';

    // 顯示文字疊加編輯器
    if (typeof showTextOverlayEditor === 'function') {
        showTextOverlayEditor(item.filename);
    }
}

// 格式化日期
function formatDate(date) {
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '剛剛';
    if (minutes < 60) return `${minutes} 分鐘前`;
    if (hours < 24) return `${hours} 小時前`;
    if (days < 7) return `${days} 天前`;

    return date.toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 生成圖片
if (generateBtn) {
    generateBtn.addEventListener('click', async () => {
        if (currentMode === 'batch') {
            await handleBatchGenerate();
        } else {
            await handleSingleGenerate();
        }
    });
} else {
    console.error('生成按鈕未找到！');
}

// 單張生成處理
async function handleSingleGenerate() {
    const prompt = promptInput.value.trim();

    if (!prompt) {
        showError('請輸入圖片描述提示詞');
        return;
    }

    // 隱藏之前的結果和錯誤
    hideAllSections();

    // 顯示載入中
    loadingSection.style.display = 'flex';
    generateBtn.disabled = true;
    btnText.textContent = '生成中...';

    try {
        // 獲取風格和尺寸設定
        const styleKeywords = typeof getSelectedStyle === 'function' ? getSelectedStyle() : '';
        const sizeSettings = typeof getSelectedSize === 'function' ? getSelectedSize() : null;

        const requestBody = {
            prompt: prompt,
            style_keywords: styleKeywords
        };

        // 如果有自定義尺寸，添加到請求
        if (sizeSettings) {
            requestBody.width = sizeSettings.width;
            requestBody.height = sizeSettings.height;
        }

        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // 顯示結果
            currentImageData = data.image;
            setCurrentFilename(data.filename);

            generatedImage.src = data.image;
            currentPrompt.textContent = data.prompt;
            filename.textContent = `檔案名稱: ${data.filename}`;

            loadingSection.style.display = 'none';
            resultSection.style.display = 'block';

            // 顯示文字疊加編輯器
            if (typeof showTextOverlayEditor === 'function') {
                showTextOverlayEditor(data.filename);
            }

            // 重新載入歷史記錄
            loadHistory();
        } else {
            throw new Error(data.error || '生成失敗');
        }
    } catch (error) {
        console.error('錯誤:', error);
        showError(error.message || '發生未知錯誤，請稍後再試');
    } finally {
        generateBtn.disabled = false;
        btnText.textContent = currentMode === 'batch' ? '開始批量生成' : '開始生成圖片';
    }
}

// 批量生成處理
async function handleBatchGenerate() {
    const lines = batchPrompts.value.split('\n').filter(line => line.trim() !== '');

    if (lines.length === 0) {
        showError('請輸入至少一個提示詞');
        return;
    }

    if (lines.length > 20) {
        showError('批量生成最多支援 20 個提示詞');
        return;
    }

    // 隱藏之前的結果
    hideAllSections();

    // 顯示載入中和進度條
    loadingSection.style.display = 'flex';
    batchProgress.style.display = 'block';
    generateBtn.disabled = true;
    btnText.textContent = '批量生成中...';

    // 初始化進度
    totalProgress.textContent = lines.length;
    currentProgress.textContent = '0';
    batchProgressBar.style.width = '0%';

    batchResults = [];

    try {
        const response = await fetch('/batch-generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompts: lines
            }),
        });

        const data = await response.json();

        if (response.ok && data.success) {
            batchResults = data.results;

            // 顯示批量結果
            loadingSection.style.display = 'none';
            batchProgress.style.display = 'none';
            displayBatchResults(data);

            // 重新載入歷史記錄
            loadHistory();
        } else {
            throw new Error(data.error || '批量生成失敗');
        }
    } catch (error) {
        console.error('批量生成錯誤:', error);
        showError(error.message || '批量生成失敗，請稍後再試');
        batchProgress.style.display = 'none';
    } finally {
        generateBtn.disabled = false;
        btnText.textContent = '開始批量生成';
    }
}

// 顯示批量結果
function displayBatchResults(data) {
    batchResultSection.style.display = 'block';
    batchSuccessCount.textContent = data.succeeded;
    batchFailCount.textContent = data.failed;

    // 清空之前的結果
    batchResultGrid.innerHTML = '';

    // 添加每個結果項目
    data.results.forEach(result => {
        const item = createBatchResultItem(result);
        batchResultGrid.appendChild(item);
    });
}

// 創建批量結果項目
function createBatchResultItem(result) {
    const div = document.createElement('div');
    div.className = `batch-result-item ${result.success ? '' : 'failed'}`;

    if (result.success) {
        div.innerHTML = `
            <img src="${result.image}" alt="${result.prompt}" class="batch-result-image">
            <div class="batch-result-info">
                <div class="batch-result-prompt">${result.prompt}</div>
                <div class="batch-result-status">
                    <span class="success-badge">✓ 成功</span>
                    <span>#${result.index}</span>
                </div>
            </div>
        `;

        // 點擊顯示大圖
        div.addEventListener('click', () => {
            showBatchImage(result);
        });
    } else {
        div.innerHTML = `
            <div class="batch-result-info">
                <div class="batch-result-prompt">${result.prompt}</div>
                <div class="batch-result-status">
                    <span class="error-badge">✗ 失敗</span>
                    <span>#${result.index}</span>
                </div>
                <div class="batch-error-message">${result.error}</div>
            </div>
        `;
    }

    return div;
}

// 顯示批量圖片大圖
function showBatchImage(result) {
    hideAllSections();

    generatedImage.src = result.image;
    currentPrompt.textContent = result.prompt;
    filename.textContent = `檔案名稱: ${result.filename}`;

    currentImageData = result.image;
    setCurrentFilename(result.filename);

    resultSection.style.display = 'block';
}

// 批量下載按鈕
batchDownloadBtn.addEventListener('click', async () => {
    const successResults = batchResults.filter(r => r.success);

    if (successResults.length === 0) {
        alert('沒有成功的圖片可以下載');
        return;
    }

    const filenames = successResults.map(r => r.filename);

    try {
        const response = await fetch('/batch-download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filenames: filenames
            }),
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `batch_images_${new Date().getTime()}.zip`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } else {
            throw new Error('下載失敗');
        }
    } catch (error) {
        console.error('下載錯誤:', error);
        alert('下載失敗: ' + error.message);
    }
});

// 下載圖片
downloadBtn.addEventListener('click', () => {
    if (currentImageData && currentFilename) {
        const link = document.createElement('a');
        link.href = currentImageData;
        link.download = currentFilename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
});

// 清除歷史記錄
clearHistoryBtn.addEventListener('click', async () => {
    if (!confirm('確定要清除所有歷史記錄嗎？此操作無法復原。')) {
        return;
    }

    try {
        const response = await fetch('/history', {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            historyList.innerHTML = '<p class="history-empty">尚無歷史記錄</p>';
            alert('歷史記錄已清除');
        } else {
            throw new Error(data.error || '清除失敗');
        }
    } catch (error) {
        console.error('清除歷史記錄失敗:', error);
        alert('清除失敗: ' + error.message);
    }
});

// 重試按鈕
retryBtn.addEventListener('click', () => {
    hideAllSections();
    welcomeSection.style.display = 'flex';
    promptInput.focus();
});

// 顯示錯誤
function showError(message) {
    hideAllSections();
    errorMessage.textContent = message;
    errorSection.style.display = 'flex';
}

// 隱藏所有區塊
function hideAllSections() {
    loadingSection.style.display = 'none';
    resultSection.style.display = 'none';
    batchResultSection.style.display = 'none';
    errorSection.style.display = 'none';
    welcomeSection.style.display = 'none';
    batchProgress.style.display = 'none';

    // 隱藏文字疊加編輯器
    if (typeof hideTextOverlayEditor === 'function') {
        hideTextOverlayEditor();
    }
}

// 支援 Enter 快速生成 (Shift+Enter 換行)
promptInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        generateBtn.click();
    }
});

// 頁面載入時執行
window.addEventListener('load', () => {
    promptInput.focus();
    loadHistory();
});
