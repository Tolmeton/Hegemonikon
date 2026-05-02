import './css/notes.css';
import { api } from '../api/client';
import { NoteTree } from '../ui/note-tree';
import { marked } from 'marked';
import { enhanceMarkdown } from './enhance';
import { esc } from '../utils';

let noteTree: NoteTree | null = null;
let currentSessionId: string | null = null;

export async function renderNotesView(): Promise<void> {
    const app = document.getElementById('view-content');
    if (!app) return;

    app.innerHTML = `
    <div class="notes-layout">
        <div class="notes-sidebar">
            <div class="notes-sidebar-header">
                <div class="notes-actions">
                    <button id="btn-refresh-notes" class="btn btn-sm" title="更新">🔄</button>
                    <button id="btn-digest-all" class="btn btn-sm" title="全消化">🧠</button>
                    <button id="btn-f2-summary" class="btn btn-sm" title="F2自動分類サマリー">📊</button>
                </div>
            </div>
            <div class="notes-search-bar">
                <input type="text" id="notes-search-input" placeholder="Search notes... (Enter)" class="notes-search-input" />
            </div>
            <div id="notes-tree-container"></div>
        </div>
        <div class="notes-main">
            <div id="notes-detail-container" class="notes-detail">
                <div class="notes-empty-state">
                    <span class="notes-empty-icon">📝</span>
                    <p>左側のツリーからノートを選択してください</p>
                </div>
            </div>
        </div>
    </div>
    `;

    document.getElementById('btn-refresh-notes')?.addEventListener('click', async () => {
        if (noteTree) {
            await noteTree.loadNotes();
            if (currentSessionId) {
                noteTree.setActive(currentSessionId);
            }
        }
    });

    document.getElementById('btn-digest-all')?.addEventListener('click', async () => {
        try {
            const btn = document.getElementById('btn-digest-all') as HTMLButtonElement;
            btn.disabled = true;
            btn.textContent = '...';
            const res = await api.notesDigestAll();
            alert(`Digest All Complete. Total chunks processed: ${res.total_chunks}`);
            if (noteTree) await noteTree.loadNotes();
        } catch (e: any) {
            alert(`Error: ${e.message}`);
        } finally {
            const btn = document.getElementById('btn-digest-all') as HTMLButtonElement;
            btn.disabled = false;
            btn.textContent = '🧠';
        }
    });

    document.getElementById('btn-f2-summary')?.addEventListener('click', async () => {
        const detailEl = document.getElementById('notes-detail-container');
        if (!detailEl) return;
        detailEl.innerHTML = `<div class="loading">Loading F2 Summary...</div>`;
        try {
            const res = await api.noteF2Summary();
            let html = `<div class="note-detail-header">
                <h1 class="note-detail-title">F2 Classification Summary</h1>
                <div class="note-detail-project">Total Semantics Classified: ${res.total}</div>
            </div>
            <div class="note-detail-body"><table class="dashboard-table">
                <thead><tr><th>Cluster Label</th><th>Count</th><th>Avg Confidence</th></tr></thead>
                <tbody>`;
            for (const c of res.clusters) {
                html += `<tr>
                    <td>${esc(c.cluster_label)}</td>
                    <td>${c.count}</td>
                    <td>${c.avg_confidence.toFixed(3)}</td>
                </tr>`;
            }
            html += `</tbody></table></div>`;
            detailEl.innerHTML = html;
        } catch (e: any) {
            detailEl.innerHTML = `<div class="card status-error">Error: ${esc(e.message)}</div>`;
        }
    });

    noteTree = new NoteTree('notes-tree-container', (sessionId) => {
        currentSessionId = sessionId;
        void loadNoteDetail(sessionId);
    });

    const searchInput = document.getElementById('notes-search-input') as HTMLInputElement;
    searchInput?.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
            const q = searchInput.value.trim();
            if (q) {
                await doSearch(q);
            }
        }
    });

    await noteTree.loadNotes();
}

async function doSearch(query: string): Promise<void> {
    const detailEl = document.getElementById('notes-detail-container');
    if (!detailEl) return;

    detailEl.innerHTML = `<div class="loading">Searching...</div>`;
    try {
        const res = await api.notesSearch(query, 10);
        let resultsHtml = '';
        if (res.results.length === 0) {
            resultsHtml = `<div class="notes-empty-state"><p>No results found for "${esc(query)}".</p></div>`;
        } else {
            resultsHtml = res.results.map(r => `
                <div class="note-chunk search-result">
                    <div class="note-chunk-meta">
                        <span class="note-chunk-path">${esc(r.path)}</span>
                        <span class="note-chunk-turns">Distance: ${r.distance.toFixed(4)}</span>
                    </div>
                    <div class="note-chunk-content markdown-body">
                        ${esc(r.content).replace(/\n/g, '<br>')}
                    </div>
                </div>
            `).join('');
        }

        detailEl.innerHTML = `
            <div class="note-detail-header">
                <h1 class="note-detail-title">Search Results for "${esc(query)}"</h1>
                <div class="note-detail-project">${res.total} matches</div>
            </div>
            <div class="note-detail-body">
                ${resultsHtml}
            </div>
        `;
    } catch (e: any) {
        detailEl.innerHTML = `<div class="card status-error">Search Error: ${esc(e.message)}</div>`;
    }
}

async function loadNoteDetail(sessionId: string): Promise<void> {
    const detailEl = document.getElementById('notes-detail-container');
    if (!detailEl) return;

    detailEl.innerHTML = `<div class="loading">Loading note details...</div>`;

    try {
        const [detail, f2Class] = await Promise.all([
            api.noteDetail(sessionId),
            api.noteF2Classify(sessionId).catch(() => null) // F2分類がない場合もエラーにしない
        ]);
        const title = detail.title || sessionId;
        const project = detail.project || 'Uncategorized';

        let chunksHtml = '';
        if (detail.chunks && detail.chunks.length > 0) {
            for (const chunk of detail.chunks) {
                let parsedContent = await marked.parse(chunk.content || '');
                // C6 FIX: Basic sanitization to prevent XSS from raw markdown
                parsedContent = parsedContent.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
                chunksHtml += `
                    <div class="note-chunk">
                        <div class="note-chunk-meta">
                            <span class="note-chunk-path">${esc(chunk.path)}</span>
                            <span class="note-chunk-turns">Turns: ${chunk.turn_range[0]} - ${chunk.turn_range[1]}</span>
                        </div>
                        <div class="note-chunk-content markdown-body">
                            ${parsedContent}
                        </div>
                    </div>
                `;
            }
        } else {
            chunksHtml = `<div class="notes-empty-state"><p>No parsed chunks for this session.</p></div>`;
        }

        let f2Html = '';
        if (f2Class && f2Class.found) {
            const tagsHtml = f2Class.tags.map(t => `<span class="tag">${esc(t)}</span>`).join(' ');
            f2Html = `
            <div class="card" style="margin-bottom: 1rem; background: var(--bg-card); border-left: 3px solid var(--accent-color);">
                <strong>F2 Classification</strong><br>
                <div style="margin-top: 0.5rem;">
                    Cluster: <span class="tag" style="background: var(--accent-opaque);">${esc(f2Class.cluster_label)}</span> 
                    Confidence: ${f2Class.confidence.toFixed(3)}
                </div>
                <div style="margin-top: 0.5rem;">Tags: ${tagsHtml}</div>
            </div>`;
        }

        detailEl.innerHTML = `
            <div class="note-detail-header">
                <div class="note-detail-project">${esc(project)}</div>
                <h1 class="note-detail-title">${esc(title)}</h1>
                <div class="note-detail-actions">
                    <button id="btn-note-digest" class="btn btn-sm">🧠 Digest</button>
                    <button id="btn-note-links" class="btn btn-sm">🔗 Links</button>
                    <button id="btn-note-classify" class="btn btn-sm">🏷️ Classify (LLM)</button>
                    <button id="btn-note-resume" class="btn btn-sm" title="このセッションを Chat で再開する">▶️ Resume</button>
                </div>
            </div>
            <div class="note-detail-body">
                ${f2Html}
                ${chunksHtml}
            </div>
        `;

        // Enhance code blocks & alerts in note chunks
        const bodyEl = detailEl.querySelector('.note-detail-body');
        if (bodyEl) enhanceMarkdown(bodyEl as HTMLElement);

        document.getElementById('btn-note-digest')?.addEventListener('click', async (e) => {
            const btn = e.target as HTMLButtonElement;
            const originalText = btn.textContent;
            try {
                btn.disabled = true;
                btn.textContent = '...';
                const res = await api.noteDigest(sessionId);
                btn.textContent = `✅ Created ${res.chunks_created}`;
                setTimeout(() => loadNoteDetail(sessionId), 1000);
            } catch (e: any) {
                alert(`Error: ${e.message}`);
                btn.disabled = false;
                btn.textContent = originalText;
            }
        });

        document.getElementById('btn-note-links')?.addEventListener('click', async (e) => {
            const btn = e.target as HTMLButtonElement;
            const originalText = btn.textContent;
            try {
                btn.disabled = true;
                btn.textContent = '...';
                const res = await api.noteLinks(sessionId);
                btn.textContent = `✅ Created ${res.links_created}`;
                setTimeout(() => { btn.textContent = originalText; btn.disabled = false; }, 2000);
            } catch (e: any) {
                alert(`Error: ${e.message}`);
                btn.disabled = false;
                btn.textContent = originalText;
            }
        });

        document.getElementById('btn-note-classify')?.addEventListener('click', async (e) => {
            const btn = e.target as HTMLButtonElement;
            const originalText = btn.textContent;
            try {
                btn.disabled = true;
                btn.textContent = '...';
                await api.noteClassify(sessionId);
                btn.textContent = '✅ Classified';
                if (noteTree) await noteTree.loadNotes();
                setTimeout(() => loadNoteDetail(sessionId), 1000);
            } catch (e: any) {
                alert(`Error: ${e.message}`);
                btn.disabled = false;
                btn.textContent = originalText;
            }
        });

        document.getElementById('btn-note-resume')?.addEventListener('click', async () => {
            const btn = document.getElementById('btn-note-resume') as HTMLButtonElement;
            try {
                btn.disabled = true;
                btn.textContent = '...';

                const res = await api.noteResume(sessionId);

                // C4 FIX: Convert Cortex turns to correct Chat UI format (including thinking + model)
                const turns = res.turns.map((t: any) => ({
                    role: t.role === 'user' ? 'user' : 'model',
                    content: t.parts?.[0]?.text || '',
                    thinking: '', // Default empty thinking
                    timestamp: new Date().toISOString()
                }));

                const newConv = {
                    id: sessionId,
                    title: title,
                    messages: turns,
                    model: 'resumed-session',
                    createdAt: new Date().toISOString()
                };

                const rawConvs = localStorage.getItem('hgk-conversations');
                let convs = rawConvs ? JSON.parse(rawConvs) : [];
                convs = convs.filter((c: any) => c.id !== sessionId);
                convs.unshift(newConv);
                localStorage.setItem('hgk-conversations', JSON.stringify(convs));

                btn.textContent = '✅ Ready to Resume';
                setTimeout(() => {
                    location.hash = '#/chat';
                }, 1000);
            } catch (e: any) {
                alert(`Error: ${e.message}`);
                btn.disabled = false;
                btn.textContent = '▶️ Resume';
            }
        });

    } catch (error: any) {
        detailEl.innerHTML = `<div class="card status-error">Error loading details: ${esc(error.message)}</div>`;
    }
}
