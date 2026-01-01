/**
 * Theme Manager - 主題切換管理
 */

// 初始化主題
function initTheme() {
    // 從 localStorage 讀取主題偏好
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);

    // 綁定切換按鈕事件
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

// 設定主題
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);

    // 更新按鈕狀態
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.classList.toggle('light-mode', theme === 'light');
    }
}

// 切換主題
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

// 獲取當前主題
function getCurrentTheme() {
    return document.documentElement.getAttribute('data-theme') || 'dark';
}

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', initTheme);
