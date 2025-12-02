// ==================== 提示詞智能助手 ====================

let promptTemplates = [];  // 提示詞範本
let currentSuggestions = [];  // 當前建議列表
let suggestionTimeout = null;  // 建議延遲計時器
let selectedSuggestionIndex = -1;  // 選中的建議索引

// 初始化提示詞助手
function initPromptAssistant() {
    console.log('✓ 提示詞助手已初始化');

    // 載入提示詞範本
    loadPromptTemplates();

    // 綁定提示詞輸入框事件
    const promptInput = document.getElementById('prompt');
    if (promptInput) {
        // 輸入時觸發建議
        promptInput.addEventListener('input', handlePromptInput);

        // 鍵盤導航
        promptInput.addEventListener('keydown', handleSuggestionKeyDown);

        // 失去焦點時隱藏建議
        promptInput.addEventListener('blur', () => {
            setTimeout(hideSuggestions, 200);
        });
    }

    // 綁定增強按鈕
    const enhanceBtn = document.getElementById('enhancePromptBtn');
    if (enhanceBtn) {
        enhanceBtn.addEventListener('click', enhancePrompt);
    }

    // 綁定範本選擇器
    const templateSelect = document.getElementById('promptTemplateSelect');
    if (templateSelect) {
        templateSelect.addEventListener('change', handleTemplateSelect);
    }

    // 綁定快速應用按鈕
    const applyTemplateBtn = document.getElementById('applyTemplateBtn');
    if (applyTemplateBtn) {
        applyTemplateBtn.addEventListener('click', applyQuickTemplate);
    }
}

// 載入提示詞範本
async function loadPromptTemplates() {
    try {
        const response = await fetch('/prompt/templates');
        if (response.ok) {
            const data = await response.json();
            promptTemplates = data.templates || [];

            // 填充範本選擇器
            populateTemplateSelector(data.categories || {});

            console.log(`✓ 已載入 ${promptTemplates.length} 個提示詞範本`);
        }
    } catch (error) {
        console.error('載入範本錯誤:', error);
    }
}

// 填充範本選擇器
function populateTemplateSelector(categories) {
    const select = document.getElementById('promptTemplateSelect');
    if (!select) return;

    // 清空現有選項
    select.innerHTML = '<option value="">選擇提示詞範本（可選）</option>';

    // 按分類添加選項
    for (const [category, templates] of Object.entries(categories)) {
        const optgroup = document.createElement('optgroup');
        optgroup.label = category;

        templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            option.dataset.prompt = template.prompt;
            option.dataset.placeholder = template.placeholder;
            optgroup.appendChild(option);
        });

        select.appendChild(optgroup);
    }
}

// 處理提示詞輸入
function handlePromptInput(event) {
    const input = event.target.value;
    const cursorPos = event.target.selectionStart;

    // 取得游標前的文字
    const textBeforeCursor = input.substring(0, cursorPos);
    const words = textBeforeCursor.split(/[\s,]+/);
    const currentWord = words[words.length - 1] || '';

    // 清除之前的計時器
    if (suggestionTimeout) {
        clearTimeout(suggestionTimeout);
    }

    // 如果輸入太短，隱藏建議
    if (currentWord.length < 2) {
        hideSuggestions();
        return;
    }

    // 延遲獲取建議（防止頻繁請求）
    suggestionTimeout = setTimeout(() => {
        getSuggestions(currentWord);
    }, 300);
}

// 獲取提示詞建議
async function getSuggestions(input) {
    try {
        const response = await fetch('/prompt/suggestions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ input: input })
        });

        if (response.ok) {
            const data = await response.json();
            currentSuggestions = data.suggestions || [];

            if (currentSuggestions.length > 0) {
                showSuggestions(currentSuggestions);
            } else {
                hideSuggestions();
            }
        }
    } catch (error) {
        console.error('獲取建議錯誤:', error);
    }
}

// 顯示建議下拉選單
function showSuggestions(suggestions) {
    let dropdown = document.getElementById('promptSuggestions');

    // 如果不存在，創建下拉選單
    if (!dropdown) {
        dropdown = document.createElement('div');
        dropdown.id = 'promptSuggestions';
        dropdown.className = 'prompt-suggestions';

        const promptInput = document.getElementById('prompt');
        promptInput.parentNode.appendChild(dropdown);
    }

    // 清空並填充建議
    dropdown.innerHTML = '';
    selectedSuggestionIndex = -1;

    suggestions.forEach((suggestion, index) => {
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        item.textContent = suggestion.display || suggestion.text;
        item.dataset.index = index;
        item.dataset.text = suggestion.text;

        // 點擊插入建議
        item.addEventListener('mousedown', () => {
            insertSuggestion(suggestion.text);
        });

        // Hover 高亮
        item.addEventListener('mouseenter', () => {
            selectedSuggestionIndex = index;
            updateSuggestionHighlight();
        });

        dropdown.appendChild(item);
    });

    dropdown.style.display = 'block';
}

// 隱藏建議下拉選單
function hideSuggestions() {
    const dropdown = document.getElementById('promptSuggestions');
    if (dropdown) {
        dropdown.style.display = 'none';
    }
    selectedSuggestionIndex = -1;
}

// 鍵盤導航建議
function handleSuggestionKeyDown(event) {
    const dropdown = document.getElementById('promptSuggestions');
    if (!dropdown || dropdown.style.display === 'none') return;

    const items = dropdown.querySelectorAll('.suggestion-item');
    if (items.length === 0) return;

    switch (event.key) {
        case 'ArrowDown':
            event.preventDefault();
            selectedSuggestionIndex = Math.min(selectedSuggestionIndex + 1, items.length - 1);
            updateSuggestionHighlight();
            break;

        case 'ArrowUp':
            event.preventDefault();
            selectedSuggestionIndex = Math.max(selectedSuggestionIndex - 1, 0);
            updateSuggestionHighlight();
            break;

        case 'Enter':
            if (selectedSuggestionIndex >= 0) {
                event.preventDefault();
                const selectedText = items[selectedSuggestionIndex].dataset.text;
                insertSuggestion(selectedText);
            }
            break;

        case 'Escape':
            event.preventDefault();
            hideSuggestions();
            break;
    }
}

// 更新建議高亮
function updateSuggestionHighlight() {
    const items = document.querySelectorAll('.suggestion-item');
    items.forEach((item, index) => {
        if (index === selectedSuggestionIndex) {
            item.classList.add('selected');
            item.scrollIntoView({ block: 'nearest' });
        } else {
            item.classList.remove('selected');
        }
    });
}

// 插入建議到提示詞
function insertSuggestion(text) {
    const promptInput = document.getElementById('prompt');
    if (!promptInput) {
        console.error('找不到提示詞輸入框');
        return;
    }

    const currentValue = promptInput.value;
    const cursorPos = promptInput.selectionStart;

    // 找到當前單詞的開始位置
    const textBeforeCursor = currentValue.substring(0, cursorPos);
    const lastSpaceIndex = Math.max(
        textBeforeCursor.lastIndexOf(' '),
        textBeforeCursor.lastIndexOf(',')
    );

    const start = lastSpaceIndex + 1;
    const end = cursorPos;

    // 替換當前單詞
    const newValue = currentValue.substring(0, start) + text + currentValue.substring(end);
    promptInput.value = newValue;

    // 設置新的游標位置
    const newCursorPos = start + text.length;
    promptInput.setSelectionRange(newCursorPos, newCursorPos);

    // 觸發 input 事件
    promptInput.dispatchEvent(new Event('input'));

    // 隱藏建議
    hideSuggestions();

    // 聚焦回輸入框
    promptInput.focus();
}

// 增強提示詞
async function enhancePrompt() {
    const promptInput = document.getElementById('prompt');
    if (!promptInput) {
        console.error('找不到提示詞輸入框');
        return;
    }

    const originalPrompt = promptInput.value.trim();
    if (!originalPrompt) {
        alert('請先輸入提示詞');
        return;
    }

    const enhanceBtn = document.getElementById('enhancePromptBtn');
    const originalText = enhanceBtn.innerHTML;

    try {
        // 顯示載入狀態
        enhanceBtn.disabled = true;
        enhanceBtn.innerHTML = `
            <div class="spinner-small"></div>
            增強中...
        `;

        const response = await fetch('/prompt/enhance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt: originalPrompt })
        });

        if (response.ok) {
            const data = await response.json();

            // 更新提示詞
            promptInput.value = data.enhanced;

            // 顯示改進資訊
            if (data.improvements > 0) {
                const message = `✓ 已增強！添加了 ${data.improvements} 個關鍵字：\n${data.added_keywords.join(', ')}`;
                console.log(message);

                // 可選：顯示提示
                showEnhancementToast(data.improvements, data.added_keywords);
            } else {
                alert('提示詞已經很完整了！');
            }
        } else {
            const error = await response.json();
            alert(`增強失敗: ${error.error || '未知錯誤'}`);
        }

    } catch (error) {
        console.error('增強提示詞錯誤:', error);
        alert('增強失敗，請稍後再試');
    } finally {
        // 恢復按鈕
        enhanceBtn.disabled = false;
        enhanceBtn.innerHTML = originalText;
    }
}

// 顯示增強提示
function showEnhancementToast(count, keywords) {
    // 創建提示元素
    let toast = document.getElementById('enhancementToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'enhancementToast';
        toast.className = 'enhancement-toast';
        document.body.appendChild(toast);
    }

    toast.innerHTML = `
        <div class="toast-icon">✨</div>
        <div class="toast-content">
            <div class="toast-title">提示詞已增強！</div>
            <div class="toast-message">添加了 ${count} 個關鍵字</div>
            <div class="toast-keywords">${keywords.join(', ')}</div>
        </div>
    `;

    toast.classList.add('show');

    // 3 秒後隱藏
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 處理範本選擇
function handleTemplateSelect(event) {
    const select = event.target;
    const selectedOption = select.options[select.selectedIndex];

    if (!selectedOption.value) return;

    // 顯示應用按鈕
    const applyBtn = document.getElementById('applyTemplateBtn');
    if (applyBtn) {
        applyBtn.style.display = 'inline-block';
    }
}

// 快速應用範本
async function applyQuickTemplate() {
    const select = document.getElementById('promptTemplateSelect');
    const promptInput = document.getElementById('prompt');

    if (!select || !promptInput) {
        console.error('找不到範本選擇器或提示詞輸入框');
        return;
    }

    const templateId = select.value;
    if (!templateId) {
        alert('請選擇範本');
        return;
    }

    // 獲取當前輸入作為主題
    const currentInput = promptInput.value.trim();

    try {
        const response = await fetch('/prompt/apply-template', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                template_id: templateId,
                subject: currentInput
            })
        });

        if (response.ok) {
            const data = await response.json();

            // 應用生成的提示詞
            promptInput.value = data.generated_prompt;

            console.log(`✓ 已應用範本: ${data.template_name}`);

            // 隱藏應用按鈕
            const applyBtn = document.getElementById('applyTemplateBtn');
            if (applyBtn) {
                applyBtn.style.display = 'none';
            }

            // 重置選擇器
            select.value = '';

        } else {
            const error = await response.json();
            alert(`應用範本失敗: ${error.error || '未知錯誤'}`);
        }

    } catch (error) {
        console.error('應用範本錯誤:', error);
        alert('應用範本失敗，請稍後再試');
    }
}

// 頁面載入時初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPromptAssistant);
} else {
    initPromptAssistant();
}
