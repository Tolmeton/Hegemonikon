import './css/audit.css';
import { api } from '../api/client';
import type { DigestCandidate, DigestorTopic } from '../api/client';
import { esc } from '../utils';

function renderCandidateCard(c: DigestCandidate, idx: number): string {
  const scorePercent = Math.min(c.score * 100, 100);
  const scoreClass = c.score >= 0.7 ? 'dg-score-high' : c.score >= 0.5 ? 'dg-score-mid' : 'dg-score-low';
  const topicsTags = c.matched_topics
    .map(t => `<span class="dg-topic-tag">${esc(t)}</span>`).join('');
  const templates = c.suggested_templates?.length > 0
    ? c.suggested_templates.slice(0, 2)
      .map(t => `<span class="dg-template-tag">${esc(t.id || String(t))}</span>`).join('')
    : '';

  return `
    <div class="card dg-candidate">
      <div class="dg-candidate-rank">#${idx + 1}</div>
      <div class="dg-candidate-body">
        <div class="dg-candidate-header">
          <h3 class="dg-candidate-title">
            ${c.url ? `<a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.title)}</a>` : esc(c.title)}
          </h3>
          <div class="dg-score-bar-wrap">
            <div class="dg-score-bar ${scoreClass}" style="width:${scorePercent}%"></div>
            <span class="dg-score-label">${c.score.toFixed(2)}</span>
          </div>
        </div>
          ${c.source ? `<span class="dg-source">${esc(c.source)}</span>` : ''}
        </div>
        ${c.rationale ? `<div class="dg-rationale">${esc(c.rationale)}</div>` : ''}
        <div style="margin-top:0.8rem; display:flex; justify-content:flex-end;">
          <button class="btn btn-sm btn-outline dg-approve-btn" 
            data-title="${esc(c.title)}"
            data-source="${esc(c.source)}"
            data-url="${esc(c.url || '')}"
            data-score="${c.score}"
            data-topics="${esc(c.matched_topics.join(','))}"
            data-rationale="${esc(c.rationale || '')}">
            ✅ 承認して /eat に送る
          </button>
        </div>
      </div>
    </div>`;
}

export async function renderDigestorView(): Promise<void> {
  const app = document.getElementById('view-content')!;
  app.innerHTML = '<div class="loading">Digestor 読み込み中...</div>';

  try {
    const data = await api.digestorReports(10);
    if (!data || data.reports.length === 0) {
      app.innerHTML = `
        <h1>🧬 Digestor</h1>
        <div class="card">
          <p>レポートが見つかりません。</p>
          <p style="color:#8b949e;">次回のスケジュール実行後に表示されます。</p>
        </div>`;
      return;
    }

    const totalReports = data.total;
    const latest = data.reports[0]!;
    const latestDate = latest.timestamp ? new Date(latest.timestamp).toLocaleString('ja-JP') : '-';

    let activeTab: 'reports' | 'news' | 'topics' = 'news';

    function render() {
      const reportOptions = data.reports.map((r, i) => {
        const dt = r.timestamp ? new Date(r.timestamp).toLocaleDateString('ja-JP') : r.filename;
        const label = `${dt} — ${r.candidates_selected}件 ${r.dry_run ? '(DRY)' : ''}`;
        return `<option value="${i}">${esc(label)}</option>`;
      }).join('');

      app.innerHTML = `
        <h1>🧬 Digestor</h1>
        <div class="dg-tabs">
          <button class="dg-tab${activeTab === 'news' ? ' dg-tab-active' : ''}" data-tab="news">📰 AI ニュース</button>
          <button class="dg-tab${activeTab === 'reports' ? ' dg-tab-active' : ''}" data-tab="reports">📊 レポート</button>
          <button class="dg-tab${activeTab === 'topics' ? ' dg-tab-active' : ''}" data-tab="topics">⚙️ トピック</button>
        </div>
        <div class="grid" style="margin-bottom:1rem;">
          <div class="card">
            <h3>レポート数</h3>
            <div class="metric">${totalReports}</div>
          </div>
          <div class="card">
            <h3>最新レポート</h3>
            <div class="metric" style="font-size:1.2rem;">${esc(latestDate)}</div>
            <p>${latest.total_papers} 論文 → ${latest.candidates_selected} 候補</p>
          </div>
          <div class="card">
            <h3>ステータス</h3>
            <div class="metric ${latest.dry_run ? 'status-warn' : 'status-ok'}">
              ${latest.dry_run ? 'DRY RUN' : 'LIVE'}
            </div>
          </div>
        </div>
        ${activeTab === 'news' ? renderNewsTab(data) : activeTab === 'reports' ? renderReportsTab(data, reportOptions) : '<div id="dg-topics-container"><div class="loading">トピック読み込み中...</div></div>'}
      `;

      app.querySelectorAll('.dg-tab').forEach(btn => {
        btn.addEventListener('click', () => {
          activeTab = (btn as HTMLElement).dataset.tab as 'reports' | 'news' | 'topics';
          render();
        });
      });

      if (activeTab === 'reports') {
        document.getElementById('dg-report-select')?.addEventListener('change', (e) => {
          const idx = parseInt((e.target as HTMLSelectElement).value, 10);
          showReportCandidates(data, idx);
        });
        showReportCandidates(data, 0);
      }
      if (activeTab === 'topics') {
        loadTopicsTab(render);
      }
    }

    render();

  } catch (e) {
    app.innerHTML = `<div class="card status-error">Digestor エラー: ${esc((e as Error).message)}</div>`;
  }
}

function renderNewsTab(data: { reports: Array<{ timestamp: string; candidates: DigestCandidate[] }> }): string {
  const latest = data.reports[0];
  if (!latest || latest.candidates.length === 0) {
    return '<div class="dg-empty-state"><div class="dg-empty-icon">📰</div><p>ニュースはまだありません。<br>Digestor が論文を収集すると、ここに表示されます。</p></div>';
  }

  const reportDate = latest.timestamp ? new Date(latest.timestamp).toLocaleDateString('ja-JP') : '';

  const newsCards = latest.candidates.map((c, i) => {
    const scorePercent = Math.min(c.score * 100, 100);
    const topicTags = c.matched_topics
      .slice(0, 4)
      .map(t => `<span class="dg-news-tag">${esc(t)}</span>`).join('');

    return `
      <div class="card dg-news-card">
        <div class="dg-news-header">
          <span class="dg-news-rank">#${i + 1}</span>
          <span class="dg-news-score">${scorePercent.toFixed(0)}%</span>
        </div>
        <h3 class="dg-news-title">
          ${c.url ? `<a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.title)}</a>` : esc(c.title)}
        </h3>
        ${c.rationale ? `<p class="dg-news-rationale">${esc(c.rationale)}</p>` : ''}
        <div class="dg-news-topics">${topicTags}</div>
        ${c.url ? `<a href="${esc(c.url)}" target="_blank" rel="noopener" class="dg-news-link">📎 論文を開く</a>` : ''}
      </div>`;
  }).join('');

  return `
    <div class="dg-news-date">📅 ${esc(reportDate)} の AI ニュース</div>
    ${newsCards}
  `;
}

function renderReportsTab(_data: { reports: Array<{ timestamp: string; candidates_selected: number; dry_run: boolean; filename: string; candidates: DigestCandidate[] }> }, reportOptions: string): string {
  return `
    <div class="card" style="margin-bottom:1rem;">
      <div style="display:flex; gap:0.5rem; align-items:center;">
        <label>レポート選択:</label>
        <select id="dg-report-select" class="input" style="flex:1;">${reportOptions}</select>
      </div>
    </div>
    <div id="dg-candidates"></div>
  `;
}

function showReportCandidates(data: { reports: Array<{ filename: string; total_papers: number; candidates: DigestCandidate[] }> }, idx: number): void {
  const report = data.reports[idx];
  const candidatesDiv = document.getElementById('dg-candidates');
  if (!candidatesDiv) return;
  if (!report || report.candidates.length === 0) {
    candidatesDiv.innerHTML = '<div class="card"><p>候補なし</p></div>';
    return;
  }
  candidatesDiv.innerHTML = `
    <div class="dg-report-header">
      <span>${esc(report.filename)}</span>
      <span>${report.candidates.length} 候補 / ${report.total_papers} 論文</span>
    </div>
    ${report.candidates.map((c: DigestCandidate, i: number) => renderCandidateCard(c, i)).join('')}
  `;

  // Bind approve buttons
  candidatesDiv.querySelectorAll('.dg-approve-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const target = e.currentTarget as HTMLButtonElement;
      target.disabled = true;
      target.textContent = '⏱️ 処理中...';

      try {
        const req = {
          title: target.dataset.title!,
          source: target.dataset.source!,
          url: target.dataset.url || undefined,
          score: parseFloat(target.dataset.score!),
          matched_topics: target.dataset.topics ? target.dataset.topics.split(',') : [],
          rationale: target.dataset.rationale || undefined,
        };
        const res = await api.digestorApproveCandidate(req);
        target.textContent = '✅ ' + res.message;
        target.className = 'btn btn-sm dg-approve-btn'; // remove outline
        target.style.backgroundColor = '#238636';
        target.style.color = '#ffffff';
        target.style.borderColor = 'transparent';
      } catch (err) {
        target.disabled = false;
        target.textContent = '❌ エラー';
        alert(`承認エラー: ${(err as Error).message}`);
      }
    });
  });
}

// ─── Topics Management Tab ───────────────────────────────
async function loadTopicsTab(rerender: () => void): Promise<void> {
  const container = document.getElementById('dg-topics-container');
  if (!container) return;

  try {
    const resp = await api.digestorTopics();
    const topics = resp.topics || [];

    const topicCards = topics.map(t => `
          <div class="card dg-topic-card" data-topic-id="${esc(t.id)}">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
              <div>
                <h3 style="margin:0 0 0.3rem 0;">${esc(t.id)}</h3>
                <p style="color:#8b949e; margin:0 0 0.5rem 0; font-size:0.9rem;">${esc(t.description)}</p>
              </div>
              <button class="dg-topic-delete" data-id="${esc(t.id)}" title="削除"
                style="background:none; border:none; color:#f85149; cursor:pointer; font-size:1.2rem; padding:0.2rem 0.4rem;">🗑️</button>
            </div>
            <div style="display:flex; gap:0.4rem; flex-wrap:wrap; margin-bottom:0.4rem;">
              ${t.digest_to.map(d => `<span class="dg-topic-tag">${esc(d)}</span>`).join('')}
              <span class="dg-template-tag">${esc(t.template_hint)}</span>
            </div>
            <details style="margin-top:0.3rem;">
              <summary style="color:#8b949e; cursor:pointer; font-size:0.85rem;">クエリ表示</summary>
              <pre style="white-space:pre-wrap; font-size:0.8rem; color:#c9d1d9; margin:0.3rem 0 0 0; background:#161b22; padding:0.5rem; border-radius:4px;">${esc(t.query)}</pre>
            </details>
          </div>`).join('');

    container.innerHTML = `
          <div class="card" style="margin-bottom:1rem;">
            <h3 style="margin:0 0 0.8rem 0;">➕ 新規トピック追加</h3>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem;">
              <input id="dg-new-id" class="input" placeholder="ID (例: bayesian-learning)">
              <input id="dg-new-desc" class="input" placeholder="説明 (例: ベイズ学習の消化)">
              <input id="dg-new-digest" class="input" placeholder="digest_to (例: /noe,/dia)">
              <select id="dg-new-template" class="input">
                <option value="T1_mapping">T1 対応表</option>
                <option value="T2_extraction">T2 哲学抽出</option>
                <option value="T3_absorption" selected>T3 機能消化</option>
                <option value="T4_import">T4 概念輸入</option>
              </select>
            </div>
            <textarea id="dg-new-query" class="input" rows="3" placeholder="検索クエリ (例: Bayesian learning, posterior inference...)" style="width:100%; margin-top:0.5rem;"></textarea>
            <button id="dg-add-btn" class="btn" style="margin-top:0.5rem;">追加</button>
          </div>
          <h3 style="margin:0 0 0.5rem 0;">登録トピック (${topics.length}件)</h3>
          ${topicCards || '<p style="color:#8b949e;">トピックがありません</p>'}
        `;

    // Add topic button
    document.getElementById('dg-add-btn')?.addEventListener('click', async () => {
      const id = (document.getElementById('dg-new-id') as HTMLInputElement).value.trim();
      const desc = (document.getElementById('dg-new-desc') as HTMLInputElement).value.trim();
      const digestRaw = (document.getElementById('dg-new-digest') as HTMLInputElement).value.trim();
      const template = (document.getElementById('dg-new-template') as HTMLSelectElement).value;
      const query = (document.getElementById('dg-new-query') as HTMLTextAreaElement).value.trim();

      if (!id || !query) {
        alert('ID とクエリは必須です');
        return;
      }

      const digest_to = digestRaw.split(',').map(s => s.trim()).filter(Boolean);
      try {
        await api.digestorCreateTopic({ id, query, digest_to, template_hint: template, description: desc || id });
        rerender();
      } catch (e) {
        alert(`追加失敗: ${(e as Error).message}`);
      }
    });

    // Delete buttons
    container.querySelectorAll('.dg-topic-delete').forEach(btn => {
      btn.addEventListener('click', async () => {
        const topicId = (btn as HTMLElement).dataset.id!;
        if (!confirm(`トピック「${topicId}」を削除しますか？`)) return;
        try {
          await api.digestorDeleteTopic(topicId);
          rerender();
        } catch (e) {
          alert(`削除失敗: ${(e as Error).message}`);
        }
      });
    });

  } catch (e) {
    container.innerHTML = `<div class="card status-error">トピック読み込みエラー: ${esc((e as Error).message)}</div>`;
  }
}
