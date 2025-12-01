// ==================== 批量導出管理器 ====================

let selectMode = false;  // 多選模式
let selectedFiles = new Set();  // 已選檔案集合
let exportFormat = 'pdf';  // 導出格式
let exportLayout = 'single';  // PDF 版面
let exportTheme = 'default';  // PPT 主題

// 初始化導出管理器
function initExportManager() {
    console.log('✓ 導出管理器已初始化');

    // 多選模式切換按鈕
    const toggleSelectBtn = document.getElementById('toggleSelectModeBtn');
    if (toggleSelectBtn) {
        toggleSelectBtn.addEventListener('click', toggleSelectMode);
    }

    // 批量操作按鈕
    const selectAllBtn = document.getElementById('selectAllBtn');
    const deselectAllBtn = document.getElementById('deselectAllBtn');
    const deleteBtn = document.getElementById('deleteBtn');
    const exportBtn = document.getElementById('exportBtn');

    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', selectAll);
    }

    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', deselectAll);
    }

    if (deleteBtn) {
        deleteBtn.addEventListener('click', deleteSelectedImages);
    }

    if (exportBtn) {
        exportBtn.addEventListener('click', showExportDialog);
    }

    // 導出對話框按鈕
    const closeDialogBtn = document.getElementById('closeExportDialog');
    const cancelExportBtn = document.getElementById('cancelExportBtn');
    const confirmExportBtn = document.getElementById('confirmExportBtn');

    if (closeDialogBtn) {
        closeDialogBtn.addEventListener('click', hideExportDialog);
    }

    if (cancelExportBtn) {
        cancelExportBtn.addEventListener('click', hideExportDialog);
    }

    if (confirmExportBtn) {
        confirmExportBtn.addEventListener('click', executeExport);
    }

    // 格式選擇按鈕
    const formatBtns = document.querySelectorAll('.format-btn');
    formatBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            formatBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            exportFormat = btn.getAttribute('data-format');
            toggleFormatOptions();
        });
    });

    // 版面選擇按鈕 (PDF)
    const layoutBtns = document.querySelectorAll('.layout-btn');
    layoutBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            layoutBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            exportLayout = btn.getAttribute('data-layout');
        });
    });

    // 主題選擇按鈕 (PPT)
    const themeBtns = document.querySelectorAll('.theme-btn');
    themeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            themeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            exportTheme = btn.getAttribute('data-theme');
        });
    });

    // 點擊對話框外部關閉
    const exportDialog = document.getElementById('exportDialog');
    if (exportDialog) {
        exportDialog.addEventListener('click', (e) => {
            if (e.target === exportDialog) {
                hideExportDialog();
            }
        });
    }
}

// 切換多選模式
function toggleSelectMode() {
    selectMode = !selectMode;
    const toolbar = document.getElementById('batchToolbar');
    const toggleBtn = document.getElementById('toggleSelectModeBtn');

    if (selectMode) {
        toolbar.style.display = 'block';
        toggleBtn.classList.add('active');
        console.log('✓ 多選模式已啟用');
    } else {
        toolbar.style.display = 'none';
        toggleBtn.classList.remove('active');
        selectedFiles.clear();
        updateSelectedCount();
        console.log('✓ 多選模式已停用');
    }

    // 更新歷史記錄顯示
    if (typeof loadHistory === 'function') {
        loadHistory();
    }
}

// 切換檔案選擇狀態
function toggleFileSelection(filename, checkbox) {
    if (checkbox.checked) {
        selectedFiles.add(filename);
    } else {
        selectedFiles.delete(filename);
    }
    updateSelectedCount();
}

// 全選
function selectAll() {
    const checkboxes = document.querySelectorAll('.history-item-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
        const filename = checkbox.getAttribute('data-filename');
        selectedFiles.add(filename);
    });
    updateSelectedCount();
}

// 取消全選
function deselectAll() {
    const checkboxes = document.querySelectorAll('.history-item-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    selectedFiles.clear();
    updateSelectedCount();
}

// 更新已選數量顯示
function updateSelectedCount() {
    const countElement = document.getElementById('selectedCount');
    const deleteBtn = document.getElementById('deleteBtn');
    const exportBtn = document.getElementById('exportBtn');

    if (countElement) {
        countElement.textContent = selectedFiles.size;
    }

    // 啟用/停用刪除按鈕
    if (deleteBtn) {
        deleteBtn.disabled = selectedFiles.size === 0;
    }

    // 啟用/停用導出按鈕
    if (exportBtn) {
        exportBtn.disabled = selectedFiles.size === 0;
    }
}

// 顯示導出對話框
function showExportDialog() {
    if (selectedFiles.size === 0) {
        alert('請先選擇要導出的圖片');
        return;
    }

    const exportDialog = document.getElementById('exportDialog');
    const exportImageCount = document.getElementById('exportImageCount');

    if (exportDialog) {
        exportDialog.style.display = 'flex';
    }

    if (exportImageCount) {
        exportImageCount.textContent = selectedFiles.size;
    }

    console.log(`✓ 準備導出 ${selectedFiles.size} 張圖片`);
}

// 隱藏導出對話框
function hideExportDialog() {
    const exportDialog = document.getElementById('exportDialog');
    if (exportDialog) {
        exportDialog.style.display = 'none';
    }
}

// 切換格式專用選項顯示
function toggleFormatOptions() {
    const pdfOptions = document.getElementById('pdfOptions');
    const pptOptions = document.getElementById('pptOptions');

    if (exportFormat === 'pdf') {
        pdfOptions.style.display = 'block';
        pptOptions.style.display = 'none';
    } else {
        pdfOptions.style.display = 'none';
        pptOptions.style.display = 'block';
    }
}

// 執行導出
async function executeExport() {
    const title = document.getElementById('exportTitle').value || '圖片集';
    const includePrompts = document.getElementById('includePromptsCheck').checked;
    const confirmBtn = document.getElementById('confirmExportBtn');

    if (selectedFiles.size === 0) {
        alert('請選擇至少一張圖片');
        return;
    }

    // 禁用按鈕
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = `
        <div class="spinner-small"></div>
        處理中...
    `;

    try {
        const filenames = Array.from(selectedFiles);

        let endpoint, requestData;

        if (exportFormat === 'pdf') {
            // PDF 導出
            endpoint = '/export-pdf';
            requestData = {
                filenames: filenames,
                title: title,
                include_prompts: includePrompts,
                layout: exportLayout
            };
        } else {
            // PowerPoint 導出
            endpoint = '/export-ppt';
            requestData = {
                filenames: filenames,
                title: title,
                include_prompts: includePrompts,
                theme: exportTheme
            };
        }

        console.log(`開始導出 ${exportFormat.toUpperCase()}...`);

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (response.ok) {
            // 下載檔案
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;

            // 從 Content-Disposition header 取得檔名
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `export_${Date.now()}.${exportFormat === 'pdf' ? 'pdf' : 'pptx'}`;

            if (contentDisposition) {
                const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }

            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            console.log(`✓ ${exportFormat.toUpperCase()} 導出成功: ${filename}`);
            alert(`導出成功！檔案已下載: ${filename}`);

            // 關閉對話框
            hideExportDialog();

        } else {
            const error = await response.json();
            throw new Error(error.error || '導出失敗');
        }

    } catch (error) {
        console.error('導出錯誤:', error);
        alert(`導出失敗: ${error.message}`);
    } finally {
        // 恢復按鈕
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 10L12 15L17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 15V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            開始導出
        `;
    }
}

// 刪除選定的圖片
async function deleteSelectedImages() {
    if (selectedFiles.size === 0) {
        alert('請先選擇要刪除的圖片');
        return;
    }

    // 確認對話框
    const confirmMessage = `確定要刪除選定的 ${selectedFiles.size} 張圖片嗎？\n此操作無法復原！`;
    if (!confirm(confirmMessage)) {
        return;
    }

    const deleteBtn = document.getElementById('deleteBtn');

    // 禁用按鈕並顯示載入狀態
    if (deleteBtn) {
        deleteBtn.disabled = true;
        deleteBtn.innerHTML = `
            <div class="spinner-small"></div>
            刪除中...
        `;
    }

    try {
        const filenames = Array.from(selectedFiles);

        console.log(`開始刪除 ${filenames.length} 張圖片...`);

        const response = await fetch('/delete-images', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filenames: filenames })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            console.log(`✓ 成功刪除 ${result.deleted} 張圖片`);

            if (result.failed && result.failed > 0) {
                alert(`刪除完成！\n成功: ${result.deleted} 張\n失敗: ${result.failed} 張`);
            } else {
                alert(`成功刪除 ${result.deleted} 張圖片！`);
            }

            // 清空選擇集合
            selectedFiles.clear();
            updateSelectedCount();

            // 重新載入歷史記錄
            if (typeof loadHistory === 'function') {
                loadHistory();
            }

        } else {
            throw new Error(result.error || '刪除失敗');
        }

    } catch (error) {
        console.error('刪除錯誤:', error);
        alert(`刪除失敗: ${error.message}`);
    } finally {
        // 恢復按鈕
        if (deleteBtn) {
            deleteBtn.disabled = selectedFiles.size === 0;
            deleteBtn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2M10 11v6M14 11v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                刪除
            `;
        }
    }
}

// 頁面載入時初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initExportManager);
} else {
    initExportManager();
}
