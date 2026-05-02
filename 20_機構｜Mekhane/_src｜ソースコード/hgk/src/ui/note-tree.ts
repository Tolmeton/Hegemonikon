import { api, NoteListItem } from '../api/client';
import { esc } from '../utils';

/**
 * F2 Session=Note: ディレクトリツリー UI
 * 
 * 左パネル用。プロジェクトごとにセッション（ノート）をグループ化してツリー表示する。
 */
export class NoteTree {
    private container: HTMLElement;
    private notes: NoteListItem[] = [];
    private onNoteSelect: (sessionId: string) => void;
    private activeSessionId: string | null = null;
    private expandedProjects: Set<string> = new Set(['']); // '' (無名PJ) はデフォルトで開く

    constructor(containerId: string, onNoteSelect: (sessionId: string) => void) {
        const el = document.getElementById(containerId);
        if (!el) throw new Error(`Container ${containerId} not found`);
        this.container = el;
        this.onNoteSelect = onNoteSelect;
    }

    public async loadNotes(): Promise<void> {
        try {
            this.container.innerHTML = `<div style="padding: 1rem; color: var(--cw-text-secondary); text-align: center;">Loading notes...</div>`;
            const res = await api.notesList();
            this.notes = res.items || [];
            this.render();
        } catch (error) {
            console.error('Failed to load notes:', error);
            this.container.innerHTML = `<div style="padding: 1rem; color: var(--cw-color-danger); text-align: center;">Failed to load notes</div>`;
        }
    }

    public setActive(sessionId: string) {
        this.activeSessionId = sessionId;
        this.render();
    }

    private toggleProject(project: string) {
        if (this.expandedProjects.has(project)) {
            this.expandedProjects.delete(project);
        } else {
            this.expandedProjects.add(project);
        }
        this.render();
    }

    private render() {
        if (this.notes.length === 0) {
            this.container.innerHTML = `<div style="padding: 1rem; color: var(--cw-text-secondary); text-align: center;">No notes found</div>`;
            return;
        }

        // Group by project
        const grouped: Record<string, NoteListItem[]> = {};
        for (const note of this.notes) {
            const pj = note.project || 'Uncategorized';
            if (!grouped[pj]) grouped[pj] = [];
            grouped[pj].push(note);
        }

        // Sort projects (Uncategorized at bottom, others alphabetical)
        const projects = Object.keys(grouped).sort((a, b) => {
            if (a === 'Uncategorized') return 1;
            if (b === 'Uncategorized') return -1;
            return a.localeCompare(b);
        });

        let html = '<div class="note-tree">';

        for (const pj of projects) {
            const isExpanded = this.expandedProjects.has(pj) || (pj === 'Uncategorized' && this.expandedProjects.has(''));

            html += `
                <div class="note-tree-folder">
                    <div class="note-tree-folder-header" data-project="${pj}">
                        <span class="note-tree-icon">${isExpanded ? '📂' : '📁'}</span>
                        <span class="note-tree-folder-name">${esc(pj)}</span>
                        <span class="note-tree-count">${grouped[pj].length}</span>
                    </div>
            `;

            if (isExpanded) {
                html += '<div class="note-tree-items">';
                // Sort by date desc
                const items = grouped[pj].sort((a, b) => b.date.localeCompare(a.date));
                for (const item of items) {
                    const isActive = item.sessionId === this.activeSessionId;
                    const title = item.title || item.sessionId;
                    // Format date to MM/DD HH:mm if possible
                    let displayDate = item.date;
                    try {
                        if (item.date) {
                            const d = new Date(item.date);
                            if (!isNaN(d.getTime())) {
                                displayDate = `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`;
                            }
                        }
                    } catch { }

                    html += `
                        <div class="note-tree-item ${isActive ? 'active' : ''}" data-id="${item.sessionId}" title="${esc(title)}">
                            <span class="note-tree-item-icon">📄</span>
                            <div class="note-tree-item-main">
                                <span class="note-tree-item-title">${esc(title)}</span>
                                <span class="note-tree-item-date">${displayDate}</span>
                            </div>
                        </div>
                    `;
                }
                html += '</div>';
            }
            html += '</div>'; // close folder
        }

        html += '</div>';
        this.container.innerHTML = html;

        this.bindEvents();
    }

    private bindEvents() {
        const headers = this.container.querySelectorAll('.note-tree-folder-header');
        headers.forEach(h => {
            h.addEventListener('click', (e) => {
                const target = e.currentTarget as HTMLElement;
                const pj = target.getAttribute('data-project');
                if (pj) this.toggleProject(pj);
            });
        });

        const items = this.container.querySelectorAll('.note-tree-item');
        items.forEach(item => {
            item.addEventListener('click', (e) => {
                const target = e.currentTarget as HTMLElement;
                const id = target.getAttribute('data-id');
                if (id) {
                    this.setActive(id);
                    this.onNoteSelect(id);
                }
            });
        });
    }
}
