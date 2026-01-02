/**
 * LLM Manager - 本地大語言模型管理器
 * 負責與後端 LLM 服務互動
 */

class LLMManager {
    constructor() {
        this.modelSelect = document.getElementById('llmModelSelect');
        this.loadBtn = document.getElementById('loadLlmModelBtn');
        this.unloadBtn = document.getElementById('unloadLlmModelBtn');
        this.statusEl = document.getElementById('llmStatus');
        this.styleSelect = document.getElementById('llmStyleSelect');
        this.aiExpandBtn = document.getElementById('aiExpandPromptBtn');
        this.promptTextarea = document.getElementById('prompt');

        this.isModelLoaded = false;
        this.isLoading = false;

        this.init();
    }

    async init() {
        // 檢查 LLM 服務狀態
        await this.checkStatus();

        // 載入可用模型清單
        await this.loadAvailableModels();

        // 綁定事件
        this.bindEvents();
    }

    bindEvents() {
        // 載入模型按鈕
        this.loadBtn.addEventListener('click', () => this.loadSelectedModel());

        // 卸載模型按鈕
        this.unloadBtn.addEventListener('click', () => this.unloadModel());

        // AI 擴展按鈕
        this.aiExpandBtn.addEventListener('click', () => this.expandPrompt());
    }

    async checkStatus() {
        try {
            const response = await fetch('/llm/status');
            const data = await response.json();

            if (!data.available) {
                this.setStatus('未安裝', 'status-error');
                this.showInstallHint();
                return;
            }

            if (data.model_loaded) {
                this.isModelLoaded = true;
                this.setStatus('已載入', 'status-ready');
                this.updateUIForLoadedModel();
            } else {
                this.setStatus('未載入', 'status-idle');
            }
        } catch (error) {
            console.error('檢查 LLM 狀態失敗:', error);
            this.setStatus('錯誤', 'status-error');
        }
    }

    async loadAvailableModels() {
        try {
            const response = await fetch('/llm/models');
            const data = await response.json();

            if (!data.success) {
                console.warn('無法載入模型清單:', data.error);
                return;
            }

            // 清空現有選項
            this.modelSelect.innerHTML = '<option value="">選擇 LLM 模型</option>';

            // 添加可用模型
            if (data.models.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = '(資料夾內無 .gguf 模型)';
                option.disabled = true;
                this.modelSelect.appendChild(option);
            } else {
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.id;
                    option.textContent = `${model.name} (${model.size_gb} GB)`;
                    this.modelSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('載入模型清單失敗:', error);
        }
    }

    async loadSelectedModel() {
        const modelId = this.modelSelect.value;

        if (!modelId) {
            alert('請先選擇一個模型');
            return;
        }

        if (this.isLoading) return;

        this.isLoading = true;
        this.setStatus('載入中...', 'status-loading');
        this.loadBtn.disabled = true;

        try {
            const response = await fetch('/llm/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_id: modelId })
            });

            const data = await response.json();

            if (data.success) {
                this.isModelLoaded = true;
                this.setStatus('已載入', 'status-ready');
                this.updateUIForLoadedModel();
            } else {
                this.setStatus('載入失敗', 'status-error');
                alert('模型載入失敗: ' + data.message);
            }
        } catch (error) {
            console.error('載入模型失敗:', error);
            this.setStatus('錯誤', 'status-error');
        } finally {
            this.isLoading = false;
            this.loadBtn.disabled = false;
        }
    }

    async unloadModel() {
        if (!this.isModelLoaded) return;

        try {
            const response = await fetch('/llm/unload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();

            if (data.success) {
                this.isModelLoaded = false;
                this.setStatus('未載入', 'status-idle');
                this.updateUIForUnloadedModel();
            }
        } catch (error) {
            console.error('卸載模型失敗:', error);
        }
    }

    async expandPrompt() {
        if (!this.isModelLoaded) {
            alert('請先載入 LLM 模型');
            return;
        }

        const idea = this.promptTextarea.value.trim();

        if (!idea) {
            alert('請先輸入簡單的想法或描述');
            return;
        }

        const style = this.styleSelect.value;

        // 顯示載入狀態
        this.aiExpandBtn.disabled = true;
        this.aiExpandBtn.innerHTML = '<span class="spinner-small"></span> 生成中...';

        try {
            const response = await fetch('/llm/generate-prompt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ idea, style })
            });

            const data = await response.json();

            if (data.success) {
                // 將生成的提示詞放入輸入框
                this.promptTextarea.value = data.prompt;
                // 觸發字數統計更新
                this.promptTextarea.dispatchEvent(new Event('input'));
            } else {
                alert('提示詞生成失敗: ' + data.error);
            }
        } catch (error) {
            console.error('擴展提示詞失敗:', error);
            alert('擴展提示詞時發生錯誤');
        } finally {
            this.aiExpandBtn.disabled = false;
            this.aiExpandBtn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                🤖 AI 擴展
            `;
        }
    }

    setStatus(text, className) {
        this.statusEl.textContent = text;
        this.statusEl.className = 'llm-status ' + className;
    }

    updateUIForLoadedModel() {
        this.loadBtn.style.display = 'none';
        this.unloadBtn.style.display = 'flex';
        this.aiExpandBtn.disabled = false;
        this.modelSelect.disabled = true;
    }

    updateUIForUnloadedModel() {
        this.loadBtn.style.display = 'flex';
        this.unloadBtn.style.display = 'none';
        this.aiExpandBtn.disabled = true;
        this.modelSelect.disabled = false;
    }

    showInstallHint() {
        const hint = document.createElement('p');
        hint.className = 'llm-install-hint';
        hint.innerHTML = '⚠️ 請執行: <code>pip install llama-cpp-python</code>';
        this.modelSelect.parentNode.appendChild(hint);
    }
}

// 頁面載入後初始化
document.addEventListener('DOMContentLoaded', () => {
    window.llmManager = new LLMManager();
});
