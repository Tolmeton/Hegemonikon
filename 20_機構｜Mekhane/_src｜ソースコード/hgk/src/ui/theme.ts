/**
 * Theme Toggle — ダーク/ライト テーマ切替
 */

export function initThemeToggle(): void {
    const saved = localStorage.getItem('hgk-theme') ?? 'dark'; // デフォルト: dark
    document.documentElement.setAttribute('data-theme', saved);

    const isDark = () => document.documentElement.getAttribute('data-theme') !== 'light';

    const btn = document.createElement('button');
    btn.className = 'theme-toggle';
    btn.setAttribute('aria-label', 'Toggle theme');
    btn.setAttribute('title', 'テーマ切替 (Ctrl+Shift+T)');
    btn.textContent = isDark() ? '☀️' : '🌙';
    document.body.appendChild(btn);

    const toggle = () => {
        const next = isDark() ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('hgk-theme', next);
        btn.textContent = next === 'dark' ? '☀️' : '🌙';
    };

    btn.addEventListener('click', toggle);

    document.addEventListener('keydown', (e: KeyboardEvent) => {
        if (e.ctrlKey && e.shiftKey && e.key === 'T') {
            e.preventDefault();
            toggle();
        }
    });
}
