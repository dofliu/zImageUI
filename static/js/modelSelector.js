/**
 * Model Selector - 模型選擇器 UI
 * 提供多模型切換、狀態顯示和模型資訊面板
 */
(function () {
    'use strict';

    let currentModelId = null;
    let availableModels = [];

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
                renderModelSelector();
            }
        } catch (error) {
            console.error('載入模型列表失敗:', error);
        }
    }

    function renderModelSelector() {
        const container = document.getElementById('modelSelectorContainer');
        if (!container) return;

        const activeModel = availableModels.find(m => m.id === currentModelId);

        container.innerHTML = `
            <div class="model-selector-header">
                <span class="model-selector-label">AI 模型</span>
                <span class="model-selector-active">${activeModel ? activeModel.name : '未載入'}</span>
            </div>
            <div class="model-selector-grid">
                ${availableModels.map(model => `
                    <div class="model-card ${model.id === currentModelId ? 'active' : ''} ${model.is_cached ? '' : 'not-cached'}"
                         data-model-id="${model.id}">
                        <div class="model-card-header">
                            <span class="model-name">${model.name}</span>
                            ${model.is_cached ? '<span class="cached-badge">已快取</span>' : '<span class="download-badge">需下載</span>'}
                        </div>
                        <p class="model-desc">${model.description}</p>
                        <div class="model-meta">
                            <span class="model-vram">${model.vram_requirement}</span>
                            <span class="model-steps">${model.default_steps} 步</span>
                        </div>
                        <div class="model-tags">
                            ${(model.tags || []).map(t => `<span class="model-tag">${t}</span>`).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // 綁定點擊事件
        container.querySelectorAll('.model-card').forEach(card => {
            card.addEventListener('click', () => {
                const modelId = card.dataset.modelId;
                switchModel(modelId);
            });
        });
    }

    async function switchModel(modelId) {
        if (modelId === currentModelId) return;

        const model = availableModels.find(m => m.id === modelId);
        if (!model) return;

        // 確認切換
        if (!model.is_cached) {
            if (!confirm(`模型 "${model.name}" 尚未快取，需要從 Hugging Face 下載。是否繼續？`)) {
                return;
            }
        }

        // 顯示載入狀態
        const container = document.getElementById('modelSelectorContainer');
        const card = container.querySelector(`[data-model-id="${modelId}"]`);
        if (card) {
            card.classList.add('loading');
            card.querySelector('.model-name').textContent = `${model.name} (載入中...)`;
        }

        try {
            const response = await fetch('/models/switch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_id: modelId })
            });

            const data = await response.json();

            if (data.success) {
                currentModelId = modelId;
                renderModelSelector();
                // 更新生成按鈕狀態
                updateGenerateButton(model);
            } else {
                alert('切換模型失敗: ' + (data.error || '未知錯誤'));
                renderModelSelector();
            }
        } catch (error) {
            alert('切換模型失敗: ' + error.message);
            renderModelSelector();
        }
    }

    function updateGenerateButton(model) {
        const btnText = document.getElementById('btnText');
        if (btnText && btnText.textContent.includes('生成')) {
            // 保持原本的文字
        }

        // 更新 img2img 按鈕可見性
        const img2imgSection = document.getElementById('img2imgSection');
        if (img2imgSection) {
            img2imgSection.style.display = model.supports_img2img ? 'block' : 'none';
        }
    }

    // 暴露給全域
    window.ModelSelector = {
        getCurrentModel: () => currentModelId,
        getModels: () => availableModels,
        refresh: loadModels
    };

})();
