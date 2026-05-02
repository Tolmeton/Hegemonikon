/**
 * enhance.ts — Shared Markdown enhancement module
 *
 * Provides syntax highlighting (highlight.js), GitHub-style alerts,
 * and copy buttons for code blocks. Used by chat.ts, devtools.ts,
 * sophia.ts, notes.ts, timeline.ts.
 */

import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import typescript from 'highlight.js/lib/languages/typescript';
import javascript from 'highlight.js/lib/languages/javascript';
import bash from 'highlight.js/lib/languages/bash';
import json from 'highlight.js/lib/languages/json';
import yaml from 'highlight.js/lib/languages/yaml';
import css from 'highlight.js/lib/languages/css';
import xml from 'highlight.js/lib/languages/xml';
import markdown from 'highlight.js/lib/languages/markdown';
import sql from 'highlight.js/lib/languages/sql';
import rust from 'highlight.js/lib/languages/rust';
import diff from 'highlight.js/lib/languages/diff';

// Register languages once
hljs.registerLanguage('python', python);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('bash', bash);
hljs.registerLanguage('shell', bash);
hljs.registerLanguage('sh', bash);
hljs.registerLanguage('json', json);
hljs.registerLanguage('yaml', yaml);
hljs.registerLanguage('yml', yaml);
hljs.registerLanguage('css', css);
hljs.registerLanguage('html', xml);
hljs.registerLanguage('xml', xml);
hljs.registerLanguage('markdown', markdown);
hljs.registerLanguage('md', markdown);
hljs.registerLanguage('sql', sql);
hljs.registerLanguage('rust', rust);
hljs.registerLanguage('diff', diff);
hljs.registerLanguage('ts', typescript);
hljs.registerLanguage('js', javascript);
hljs.registerLanguage('py', python);

// ─── Code Block Enhancement ─────────────────────────────────

export function enhanceCodeBlocks(container: HTMLElement): void {
    container.querySelectorAll('pre').forEach(pre => {
        if (pre.querySelector('.cw-code-copy')) return;

        const codeEl = pre.querySelector('code');

        // S1: Syntax highlighting
        if (codeEl) {
            const langClass = Array.from(codeEl.classList).find(c => c.startsWith('language-'));
            const lang = langClass?.replace('language-', '') || '';

            if (lang && hljs.getLanguage(lang)) {
                try {
                    const result = hljs.highlight(codeEl.textContent || '', { language: lang });
                    codeEl.innerHTML = result.value;
                    codeEl.classList.add('hljs');
                } catch { /* fallback */ }
            } else if (!codeEl.classList.contains('hljs')) {
                try {
                    const result = hljs.highlightAuto(codeEl.textContent || '');
                    if (result.language && result.relevance > 0) {
                        codeEl.innerHTML = result.value;
                        codeEl.classList.add('hljs');
                        if (!langClass) codeEl.classList.add(`language-${result.language}`);
                    }
                } catch { /* fallback */ }
            }
        }

        // S2: Language label
        const detectedLang = codeEl
            ? Array.from(codeEl.classList).find(c => c.startsWith('language-'))?.replace('language-', '')
            : '';
        if (detectedLang) {
            const label = document.createElement('span');
            label.className = 'cw-code-lang';
            label.textContent = detectedLang;
            pre.appendChild(label);
        }

        // S3: Copy button
        const btn = document.createElement('button');
        btn.className = 'cw-code-copy';
        btn.textContent = 'Copy';
        btn.addEventListener('click', () => {
            const code = codeEl?.textContent ?? pre.textContent ?? '';
            void navigator.clipboard.writeText(code).then(() => {
                btn.textContent = '✓';
                setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
            });
        });

        pre.style.position = 'relative';
        pre.appendChild(btn);
    });
}

// ─── GitHub-style Alerts ─────────────────────────────────────

const ALERT_TYPES: Record<string, { icon: string; label: string; cssClass: string }> = {
    'NOTE': { icon: 'ℹ️', label: 'Note', cssClass: 'cw-alert-note' },
    'TIP': { icon: '💡', label: 'Tip', cssClass: 'cw-alert-tip' },
    'IMPORTANT': { icon: '❗', label: 'Important', cssClass: 'cw-alert-important' },
    'WARNING': { icon: '⚠️', label: 'Warning', cssClass: 'cw-alert-warning' },
    'CAUTION': { icon: '🔴', label: 'Caution', cssClass: 'cw-alert-caution' },
};

export function enhanceAlerts(container: HTMLElement): void {
    container.querySelectorAll('blockquote').forEach(bq => {
        if (bq.classList.contains('cw-alert')) return;

        const firstP = bq.querySelector('p');
        if (!firstP) return;

        const text = firstP.innerHTML;
        const match = text.match(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(?:<br\s*\/?>)?\s*/i);
        if (!match) return;

        const alertType = match[1]!.toUpperCase();
        const alertInfo = ALERT_TYPES[alertType];
        if (!alertInfo) return;

        firstP.innerHTML = text.replace(match[0], '');
        if (!firstP.textContent?.trim() && !firstP.querySelector('*')) {
            firstP.remove();
        }

        bq.classList.add('cw-alert', alertInfo.cssClass);

        const title = document.createElement('div');
        title.className = 'cw-alert-title';
        title.innerHTML = `${alertInfo.icon} <strong>${alertInfo.label}</strong>`;
        bq.insertBefore(title, bq.firstChild);
    });
}

// ─── Combined enhancer ───────────────────────────────────────

export function enhanceMarkdown(container: HTMLElement): void {
    enhanceCodeBlocks(container);
    enhanceAlerts(container);
}
