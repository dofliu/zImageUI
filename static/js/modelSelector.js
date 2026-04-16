/**
 * Model Selector - 模型狀態顯示
 * 精簡版：顯示目前模型狀態，支援一鍵載入
 */
(function () {
    'use strict';

    let currentModelId = null;
    let availableModels = [];
    let pollTimer = null;

    // ===== 初始化 =====
    document.addEventListener('DOMContentLoaded', () => {
        loadModels();
    });

    async function loadModels() {
        try {
            const response = await fetch('/models');
            const data = await response.json();

            if (data.success) {
                availableModels = data.models;
                currentModelId = data.active_model;
                renderModelStatus();
            }
        } catch (error) {
            console.error('載入模型列表失敗:', error);
            renderError();
        }
    }

    function renderModelStatus() {
        const container = document.getElementById('modelSelectorContainer');
        if (!container) return;

        const activeModel = availableModels.find(m => m.id === currentModelId);
        const defaultModel = availableModels[0]; // 唯一的模型

        if (activeModel) {
            // 模型已載入 - 顯示就緒狀態
            container.innerHTML = `
                <div class="model-status ready">
                    <div class="model-status-icon">✓</div>
                    <div class="model-status-info">
                        <span class="model-status-name">${activeModel.name}</span>
                        <span class="model-status-detail">模型就緒 · ${activeModel.default_steps} 步 · ${activeModel.vram_requirement}</span>
                    </div>
                </div>
            `;
        } else if (defaultModel) {
            // 模型未載入 - 顯示載入按鈕
            container.innerHTML = `
                <div class="model-status idle" id="modelLoadArea">
                    <div class="model-status-icon">○</div>
                    <div class="model-status-info">
                        <span class="model-status-name">${defaultModel.name}</span>
                        <span class="model-status-detail">尚未載入</span>
                    </div>
                    <button class="model-load-btn" id="loadModelBtn">載入模型</button>
                </div>
            `;
            document.getElementById('loadModelBtn').addEventListener('click', () => {
                loadDefaultModel(defaultModel);
            });
        } else {
            renderError();
        }
    }

    function renderLoading(modelName) {
        const container = document.getElementById('modelSelectorContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="model-status loading">
                <div class="model-status-spinner"></div>
                <div class="model-status-info">
                    <span class="model-status-name">${modelName}</span>
                    <span class="model-status-detail">模型載入中，請稍候...</span>
                </div>
            </div>
        `;
    }

    function renderError() {
        const container = document.getElementById('modelSelectorContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="model-status error">
                <div class="model-status-icon">!</div>
                <div class="model-status-info">
                    <span class="model-status-name">模型載入失敗</span>
                    <span class="model-status-detail">請檢查模型檔案或重新整理頁面</span>
                </div>
                <button class="model-load-btn" onclick="location.reload()">重試</button>
            </div>
        `;
    }

    async function loadDefaultModel(model) {
        renderLoading(model.name);

        try {
            const response = await fetch('/models/switch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_id: model.id })
            });

            const data = await response.json();

            if (data.success) {
                currentModelId = model.id;
                renderModelStatus();
            } else {
                renderError();
                console.error('載入模型失敗:', data.error);
            }
        } catch (error) {
            renderError();
            console.error('載入模型失敗:', error);
        }
    }

    // 暴露給全域
    window.ModelSelector = {
        getCurrentModel: () => currentModelId,
        getModels: () => availableModels,
        refresh: loadModels,
        isReady: () => currentModelId !== null
    };

})();
