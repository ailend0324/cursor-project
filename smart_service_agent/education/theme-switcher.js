/**
 * 主题管理系统 - 鹏十三不下山大会网站
 */

// 网站主题管理
document.addEventListener('DOMContentLoaded', function() {
    // 初始化主题系统
    initThemeSystem();

    // 主题切换按钮点击事件
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
        updateToggleIcon(); // 初始化图标状态
    }

    // 主题选择下拉列表变化事件
    const themeSelector = document.getElementById('custom-theme-selector');
    if (themeSelector) {
        themeSelector.addEventListener('change', function(e) {
            applyCustomTheme(e.target.value);
        });

        // 初始化选择器状态
        if (localStorage.getItem('customTheme')) {
            themeSelector.value = localStorage.getItem('customTheme');
        }

        // 启用马卡龙主题选项
        const macaronOption = themeSelector.querySelector('option[value="theme-macaron"]');
        if (macaronOption) {
            macaronOption.disabled = false;
        }
    }
});

// 初始化主题系统
function initThemeSystem() {
    // 应用保存的深色/浅色模式
    if (localStorage.getItem('darkMode') === 'true' ||
        (!localStorage.getItem('darkMode') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }

    // 应用保存的自定义主题
    const savedCustomTheme = localStorage.getItem('customTheme');
    if (savedCustomTheme) {
        applyCustomTheme(savedCustomTheme);
    }
}

// 切换深色/浅色模式
function toggleTheme() {
    const isDarkMode = document.documentElement.classList.toggle('dark');
    localStorage.setItem('darkMode', isDarkMode);
    updateToggleIcon();
    console.log('主题已切换为: ' + (isDarkMode ? '深色模式' : '浅色模式'));
}

// 更新主题切换按钮图标
function updateToggleIcon() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;

    const sunIcon = themeToggle.querySelector('.sun-icon');
    const moonIcon = themeToggle.querySelector('.moon-icon');

    if (document.documentElement.classList.contains('dark')) {
        sunIcon.classList.remove('hidden');
        moonIcon.classList.add('hidden');
    } else {
        sunIcon.classList.add('hidden');
        moonIcon.classList.remove('hidden');
    }
}

// 应用自定义主题
function applyCustomTheme(themeName) {
    // 移除所有主题类
    document.documentElement.classList.remove('theme-default', 'theme-macaron');

    // 如果选择了默认以外的主题，添加对应类名
    if (themeName && themeName !== 'theme-default') {
        document.documentElement.classList.add(themeName);
        localStorage.setItem('customTheme', themeName);
        console.log('已应用自定义主题: ' + themeName);
    } else {
        // 如果选择了默认主题，清除自定义主题存储
        localStorage.removeItem('customTheme');
        console.log('已恢复默认主题');
    }
}