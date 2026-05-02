/**
 * Slide Panel — 右サイドパネル (U3) — ターミナル + アーティファクト
 */

export function setupSlidePanel(): void {
    const trigger = document.getElementById('slide-trigger');
    const panel = document.getElementById('slide-panel');
    const closeBtn = document.getElementById('slide-panel-close');

    /* ── Open/Close helpers ── */
    const openPanel = () => {
        panel?.classList.add('open');
        trigger?.classList.add('hidden');
    };
    const closePanel = () => {
        panel?.classList.remove('open');
        trigger?.classList.remove('hidden');
    };

    /* ── Trigger (right edge) ── */
    if (trigger) {
        trigger.addEventListener('mouseenter', () => trigger.classList.add('hover'));
        trigger.addEventListener('mouseleave', () => trigger.classList.remove('hover'));
        trigger.addEventListener('click', openPanel);
    }
    closeBtn?.addEventListener('click', closePanel);

    /* ── Tab switching (Terminal / Artifacts) ── */
    const tabs = panel?.querySelectorAll('.sp-tab');
    const panes = panel?.querySelectorAll('.sp-pane');

    tabs?.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = (tab as HTMLElement).dataset.spTab;
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            panes?.forEach(p => {
                p.classList.toggle('sp-pane-active', p.id === `sp-${target}`);
            });
        });
    });
}

/** Append text to the slide-panel terminal output */
export function appendTerminalOutput(text: string): void {
    const el = document.getElementById('sp-terminal-output');
    if (!el) return;
    el.textContent += text;
    el.scrollTop = el.scrollHeight;
}
