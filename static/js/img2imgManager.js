/**
 * img2img Manager - 圖生圖功能管理
 * 處理參考圖片上傳、預覽和 img2img 生成
 */
(function () {
    'use strict';

    let referenceImage = null; // base64 data

    document.addEventListener('DOMContentLoaded', () => {
        initImg2Img();
    });

    function initImg2Img() {
        // 圖生圖模式切換
        const img2imgModeBtn = document.getElementById('img2imgModeBtn');
        if (img2imgModeBtn) {
            img2imgModeBtn.addEventListener('click', toggleImg2ImgMode);
        }

        // 拖放上傳區域
        const dropZone = document.getElementById('img2imgDropZone');
        if (dropZone) {
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('drag-over');
            });

            dropZone.addEventListener('dragleave', () => {
                dropZone.classList.remove('drag-over');
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('drag-over');
                const files = e.dataTransfer.files;
                if (files.length > 0) handleImageFile(files[0]);
            });

            dropZone.addEventListener('click', () => {
                document.getElementById('img2imgFileInput').click();
            });
        }

        // 檔案選擇
        const fileInput = document.getElementById('img2imgFileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) handleImageFile(e.target.files[0]);
            });
        }

        // 強度滑桿
        const strengthSlider = document.getElementById('img2imgStrength');
        const strengthValue = document.getElementById('strengthValue');
        if (strengthSlider && strengthValue) {
            strengthSlider.addEventListener('input', () => {
                strengthValue.textContent = strengthSlider.value;
            });
        }

        // 清除參考圖
        const clearBtn = document.getElementById('clearReferenceBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', clearReference);
        }

        // 生成變體
        const variationsBtn = document.getElementById('generateVariationsBtn');
        if (variationsBtn) {
            variationsBtn.addEventListener('click', handleGenerateVariations);
        }
    }

    function toggleImg2ImgMode() {
        const section = document.getElementById('img2imgSection');
        const btn = document.getElementById('img2imgModeBtn');
        if (!section) return;

        const isVisible = section.style.display !== 'none';
        section.style.display = isVisible ? 'none' : 'block';
        if (btn) {
            btn.classList.toggle('active', !isVisible);
        }
    }

    function handleImageFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('請選擇圖片檔案');
            return;
        }

        if (file.size > 20 * 1024 * 1024) {
            alert('圖片大小不能超過 20MB');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            referenceImage = e.target.result;
            showReferencePreview(referenceImage);
        };
        reader.readAsDataURL(file);
    }

    function showReferencePreview(imageData) {
        const preview = document.getElementById('img2imgPreview');
        const dropZone = document.getElementById('img2imgDropZone');
        const controls = document.getElementById('img2imgControls');

        if (preview) {
            preview.innerHTML = `<img src="${imageData}" alt="參考圖片">`;
            preview.style.display = 'block';
        }
        if (dropZone) dropZone.style.display = 'none';
        if (controls) controls.style.display = 'block';
    }

    function clearReference() {
        referenceImage = null;
        const preview = document.getElementById('img2imgPreview');
        const dropZone = document.getElementById('img2imgDropZone');
        const controls = document.getElementById('img2imgControls');

        if (preview) {
            preview.innerHTML = '';
            preview.style.display = 'none';
        }
        if (dropZone) dropZone.style.display = 'flex';
        if (controls) controls.style.display = 'none';
    }

    async function handleGenerateVariations() {
        if (!referenceImage) {
            alert('請先上傳參考圖片');
            return;
        }

        const prompt = document.getElementById('prompt')?.value?.trim();
        if (!prompt) {
            alert('請輸入提示詞');
            return;
        }

        const btn = document.getElementById('generateVariationsBtn');
        if (btn) {
            btn.disabled = true;
            btn.textContent = '生成中...';
        }

        try {
            const response = await fetch('/img2img/variations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image: referenceImage,
                    prompt: prompt,
                    count: 4,
                    strength_range: [0.3, 0.5, 0.7, 0.9]
                })
            });

            const data = await response.json();
            if (data.success) {
                displayVariationResults(data.results);
            } else {
                alert('生成失敗: ' + (data.error || '未知錯誤'));
            }
        } catch (error) {
            alert('生成變體失敗: ' + error.message);
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = '生成 4 個變體';
            }
        }
    }

    function displayVariationResults(results) {
        const container = document.getElementById('variationResults');
        if (!container) return;

        container.innerHTML = '';
        container.style.display = 'grid';

        results.forEach(result => {
            const item = document.createElement('div');
            item.className = 'variation-item';

            if (result.success) {
                item.innerHTML = `
                    <img src="${result.image}" alt="變體 ${result.index}">
                    <div class="variation-info">
                        <span>強度: ${result.strength.toFixed(2)}</span>
                    </div>
                `;
            } else {
                item.innerHTML = `
                    <div class="variation-error">生成失敗</div>
                `;
            }

            container.appendChild(item);
        });
    }

    // 暴露 img2img 生成函數給主腳本使用
    window.Img2Img = {
        getReferenceImage: () => referenceImage,
        hasReference: () => referenceImage !== null,
        clear: clearReference
    };

})();
