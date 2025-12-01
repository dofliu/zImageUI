// ==================== 文字疊加功能 ====================

// 注意: currentFilename 使用 script.js 中的全域變數
let overlaySelectedPosition = 'top';  // 預設位置
let overlaySelectedColor = 'white';  // 預設顏色

// 初始化文字疊加功能
function initTextOverlay() {
    console.log('✓ 文字疊加功能已初始化');

    const toggleBtn = document.getElementById('toggleTextEditor');
    const textEditorPanel = document.getElementById('textEditorPanel');
    const overlayText = document.getElementById('overlayText');
    const textCounter = document.querySelector('.text-counter');
    const applyTextBtn = document.getElementById('applyTextBtn');
    const positionBtns = document.querySelectorAll('.position-btn');
    const colorBtns = document.querySelectorAll('.color-btn');

    // 折疊/展開編輯器
    if (toggleBtn && textEditorPanel) {
        toggleBtn.addEventListener('click', () => {
            const isVisible = textEditorPanel.style.display !== 'none';
            textEditorPanel.style.display = isVisible ? 'none' : 'flex';
            toggleBtn.classList.toggle('rotated', !isVisible);
        });
    }

    // 文字輸入計數器
    if (overlayText && textCounter) {
        overlayText.addEventListener('input', () => {
            const length = overlayText.value.length;
            textCounter.textContent = `${length} / 100`;
        });
    }

    // 位置選擇
    positionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            positionBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            overlaySelectedPosition = btn.getAttribute('data-position');
        });
    });

    // 顏色選擇
    colorBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            colorBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            overlaySelectedColor = btn.getAttribute('data-color');
        });
    });

    // 套用文字按鈕
    if (applyTextBtn) {
        applyTextBtn.addEventListener('click', applyTextOverlay);
    }
}

// 顯示文字疊加編輯器
function showTextOverlayEditor(filename) {
    // currentFilename 是 script.js 中的全域變數，這裡直接設置
    if (typeof window !== 'undefined') {
        window.currentFilename = filename;
    }
    const textOverlaySection = document.getElementById('textOverlaySection');

    if (textOverlaySection) {
        textOverlaySection.style.display = 'block';

        // 清空輸入
        const overlayText = document.getElementById('overlayText');
        if (overlayText) {
            overlayText.value = '';
            overlayText.dispatchEvent(new Event('input'));
        }

        console.log(`✓ 文字疊加編輯器已顯示 (檔案: ${filename})`);
    }
}

// 隱藏文字疊加編輯器
function hideTextOverlayEditor() {
    const textOverlaySection = document.getElementById('textOverlaySection');
    if (textOverlaySection) {
        textOverlaySection.style.display = 'none';
    }
    // 不需要重設 currentFilename，因為它由 script.js 管理
}

// 套用文字疊加
async function applyTextOverlay() {
    const overlayText = document.getElementById('overlayText');
    const bgOverlayCheck = document.getElementById('bgOverlayCheck');
    const applyTextBtn = document.getElementById('applyTextBtn');

    // 獲取全域 currentFilename
    const filename = (typeof window !== 'undefined' && window.currentFilename) || currentFilename;

    if (!overlayText || !filename) {
        console.error('文字輸入或檔案名稱遺失');
        return;
    }

    const text = overlayText.value.trim();
    if (!text) {
        alert('請輸入文字內容');
        return;
    }

    // 禁用按鈕
    applyTextBtn.disabled = true;
    applyTextBtn.textContent = '處理中...';

    try {
        const response = await fetch('/add-text-overlay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: filename,
                text: text,
                position: overlaySelectedPosition,
                text_color: overlaySelectedColor,
                bg_overlay: bgOverlayCheck ? bgOverlayCheck.checked : true,
                font_size: 48
            })
        });

        const data = await response.json();

        if (data.success) {
            console.log('✓ 文字疊加成功');

            // 更新圖片顯示
            const generatedImage = document.getElementById('generatedImage');
            const filenameDisplay = document.getElementById('filename');
            const downloadBtn = document.getElementById('downloadBtn');

            if (generatedImage) {
                generatedImage.src = data.image;
            }

            if (filenameDisplay) {
                filenameDisplay.textContent = `檔案名稱: ${data.filename}`;
            }

            // 更新當前檔名 (全域變數)
            if (typeof window !== 'undefined') {
                window.currentFilename = data.filename;
            }

            // 更新下載按鈕
            if (downloadBtn) {
                downloadBtn.onclick = () => downloadImage(data.filename);
            }

            // 重新載入歷史記錄
            if (typeof loadHistory === 'function') {
                loadHistory();
            }

            alert('文字疊加完成！');
        } else {
            throw new Error(data.error || '文字疊加失敗');
        }
    } catch (error) {
        console.error('文字疊加錯誤:', error);
        alert(`錯誤: ${error.message}`);
    } finally {
        // 恢復按鈕
        applyTextBtn.disabled = false;
        applyTextBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            套用文字
        `;
    }
}

// 下載圖片
function downloadImage(filename) {
    window.location.href = `/images/${filename}`;
}

// 頁面載入時初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTextOverlay);
} else {
    initTextOverlay();
}
