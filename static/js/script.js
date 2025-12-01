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

let currentImageData = null;
let currentFilename = null;

// 字數計數器
promptInput.addEventListener('input', () => {
    const count = promptInput.value.length;
    charCount.textContent = `${count} 字`;
});

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

    // 點擊歷史記錄項目顯示該圖片
    div.addEventListener('click', () => {
        showHistoryImage(item);
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
    currentFilename = item.filename;

    resultSection.style.display = 'block';
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
generateBtn.addEventListener('click', async () => {
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
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt
            }),
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // 顯示結果
            currentImageData = data.image;
            currentFilename = data.filename;

            generatedImage.src = data.image;
            currentPrompt.textContent = data.prompt;
            filename.textContent = `檔案名稱: ${data.filename}`;

            loadingSection.style.display = 'none';
            resultSection.style.display = 'block';

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
        btnText.textContent = '開始生成圖片';
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
    errorSection.style.display = 'none';
    welcomeSection.style.display = 'none';
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
