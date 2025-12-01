// 風格模板和尺寸預設功能

// 全局變數
let currentStyleKeywords = '';
let customSize = null;
let templatesData = null;
let sizesData = null;

// 載入風格模板
async function loadTemplates() {
    try {
        const response = await fetch('/templates');
        const data = await response.json();

        if (data.success) {
            templatesData = data.templates;
            populateStyleSelect();
        }
    } catch (error) {
        console.error('載入風格模板失敗:', error);
    }
}

// 載入尺寸預設
async function loadSizePresets() {
    try {
        const response = await fetch('/size-presets');
        const data = await response.json();

        if (data.success) {
            sizesData = data.presets;
            populateSizeSelect(data.current);
        }
    } catch (error) {
        console.error('載入尺寸預設失敗:', error);
    }
}

// 填充風格選擇器
function populateStyleSelect() {
    const styleSelect = document.getElementById('styleSelect');
    styleSelect.innerHTML = '<option value="">無風格（使用原始提示詞）</option>';

    for (const [category, styles] of Object.entries(templatesData)) {
        const optgroup = document.createElement('optgroup');
        optgroup.label = category;

        styles.forEach(style => {
            const option = document.createElement('option');
            option.value = style.keywords;
            option.textContent = `${style.name} - ${style.description}`;
            option.dataset.name = style.name;
            optgroup.appendChild(option);
        });

        styleSelect.appendChild(optgroup);
    }
}

// 填充尺寸選擇器
function populateSizeSelect(currentSize) {
    const sizeSelect = document.getElementById('sizeSelect');
    sizeSelect.innerHTML = `<option value="default">預設尺寸 (${currentSize.width}x${currentSize.height})</option>`;

    for (const [category, sizes] of Object.entries(sizesData)) {
        const optgroup = document.createElement('optgroup');
        optgroup.label = category;

        sizes.forEach(size => {
            const option = document.createElement('option');
            option.value = JSON.stringify({width: size.width, height: size.height});
            const vramInfo = size.vram ? ` [VRAM: ${size.vram}]` : '';
            option.textContent = `${size.name} (${size.width}x${size.height})${vramInfo}`;
            optgroup.appendChild(option);
        });

        sizeSelect.appendChild(optgroup);
    }
}

// 風格選擇變更事件
document.addEventListener('DOMContentLoaded', () => {
    const styleSelect = document.getElementById('styleSelect');
    const sizeSelect = document.getElementById('sizeSelect');
    const refreshStylesBtn = document.getElementById('refreshStylesBtn');

    if (styleSelect) {
        styleSelect.addEventListener('change', (e) => {
            currentStyleKeywords = e.target.value;
            console.log('選擇風格:', currentStyleKeywords || '無');
        });
    }

    if (sizeSelect) {
        sizeSelect.addEventListener('change', (e) => {
            const value = e.target.value;
            if (value === 'default') {
                customSize = null;
            } else {
                try {
                    customSize = JSON.parse(value);
                    console.log('選擇尺寸:', customSize);
                } catch (error) {
                    console.error('解析尺寸錯誤:', error);
                    customSize = null;
                }
            }
        });
    }

    if (refreshStylesBtn) {
        refreshStylesBtn.addEventListener('click', async () => {
            refreshStylesBtn.style.transform = 'rotate(360deg)';
            await loadTemplates();
            setTimeout(() => {
                refreshStylesBtn.style.transform = '';
            }, 300);
        });
    }

    // 初始化載入
    loadTemplates();
    loadSizePresets();
});

// 導出函數供主腳本使用
function getSelectedStyle() {
    return currentStyleKeywords;
}

function getSelectedSize() {
    return customSize;
}
