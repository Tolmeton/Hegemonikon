import './css/content.css';
import { api } from '../api/client';
import type { GnosisStatsResponse, PaperCard, GnosisPapersResponse, GnosisNarrateResponse } from '../api/client';
import { esc } from '../utils';

function renderPaperCard(p: PaperCard): string {
  const score = p.relevance_score > 0
    ? `<span class="nr-score">${(p.relevance_score * 100).toFixed(0)}%</span>`
    : '';
  const topics = p.topics.length > 0
    ? p.topics.slice(0, 3).map(t => `<span class="nr-tag">${esc(t)}</span>`).join('')
    : '';
  return `
    <div class="nr-card" data-title="${esc(p.title)}">
      <div class="nr-card-header">
        <h3 class="nr-title">${esc(p.title)}</h3>
        ${score}
      </div>
      ${p.authors ? `<div class="nr-authors">${esc(p.authors)}</div>` : ''}
      ${topics ? `<div class="nr-topics">${topics}</div>` : ''}
      ${p.abstract ? `<p class="nr-abstract">${esc(p.abstract.substring(0, 200))}${p.abstract.length > 200 ? '...' : ''}</p>` : ''}
      ${p.question ? `<div class="nr-question">💡 ${esc(p.question)}</div>` : ''}
      <div class="nr-actions">
        <button class="btn btn-sm nr-narrate-btn" data-title="${esc(p.title)}" data-fmt="deep_dive">🎙️ ナレーション</button>
        <button class="btn btn-sm btn-outline nr-narrate-btn" data-title="${esc(p.title)}" data-fmt="brief">📝 概要</button>
        <button class="btn btn-sm btn-outline nr-narrate-btn" data-title="${esc(p.title)}" data-fmt="critique">🔍 批評</button>
      </div>
      <div class="nr-narration" style="display:none;"></div>
    </div>
  `;
}

async function handleNarrate(btn: HTMLButtonElement): Promise<void> {
  const title = btn.dataset.title ?? '';
  const fmt = btn.dataset.fmt ?? 'deep_dive';
  const card = btn.closest('.nr-card') as HTMLElement;
  const narrationDiv = card.querySelector('.nr-narration') as HTMLElement;

  narrationDiv.style.display = 'block';
  narrationDiv.innerHTML = '<div class="loading">ナレーション生成中...</div>';

  try {
    const res: GnosisNarrateResponse = await api.gnosisNarrate(title, fmt);
    if (!res.generated || res.segments.length === 0) {
      narrationDiv.innerHTML = '<div class="nr-narration-empty">ナレーション利用不可</div>';
      return;
    }
    narrationDiv.innerHTML = `
      <div class="nr-narration-header">${esc(res.icon)} ${esc(res.fmt.toUpperCase())}</div>
      ${res.segments.map(s => `
        <div class="nr-segment">
          <span class="nr-speaker">${esc(s.speaker)}:</span>
          <span class="nr-content">${esc(s.content)}</span>
        </div>
      `).join('')}
    `;
  } catch (e) {
    narrationDiv.innerHTML = `<div class="status-error">ナレーション失敗: ${esc((e as Error).message)}</div>`;
  }
}

export async function renderGnosis(): Promise<void> {
  let stats: GnosisStatsResponse | null = null;
  try {
    stats = await api.gnosisStats();
  } catch { /* ok */ }

  const app = document.getElementById('view-content')!;

  const statsHtml = stats ? `
    <div class="grid" style="margin-bottom:1rem;">
      <div class="card">
        <h3>論文総数</h3>
        <div class="metric">${stats.total}</div>
      </div>
      <div class="card">
        <h3>固有 DOI</h3>
        <div class="metric">${stats.unique_dois}</div>
      </div>
      <div class="card">
        <h3>固有 arXiv</h3>
        <div class="metric">${stats.unique_arxiv}</div>
      </div>
      <div class="card">
        <h3>ソース</h3>
        <div style="font-size:0.9rem;">
          ${Object.entries(stats.sources).map(([k, v]) => `${esc(k)}: <strong>${String(v)}</strong>`).join(' · ')}
        </div>
        <small>最終収集: ${esc(stats.last_collected)}</small>
      </div>
    </div>
  ` : '';

  app.innerHTML = `
    <h1>Gnōsis</h1>
    ${statsHtml}
    <div class="card">
      <div style="display:flex; gap:0.5rem;">
        <input type="text" id="gnosis-search-input" class="input" placeholder="知識基盤を検索..." style="flex:1;" />
        <button id="gnosis-search-btn" class="btn">🔍 検索</button>
        <button id="gnosis-papers-btn" class="btn btn-outline">📚 論文</button>
      </div>
    </div>
    <div id="search-results"></div>
  `;

  const searchBtn = document.getElementById('gnosis-search-btn')!;
  const papersBtn = document.getElementById('gnosis-papers-btn')!;
  const searchInput = document.getElementById('gnosis-search-input') as HTMLInputElement;

  const doSearch = async (): Promise<void> => {
    const query = searchInput.value.trim();
    if (!query) return;
    const resultsDiv = document.getElementById('search-results')!;
    resultsDiv.innerHTML = '<div class="loading">検索中...</div>';
    try {
      const res = await api.symplokeSearch(query, 50, 'gnosis');
      if (res.results.length === 0) {
        resultsDiv.innerHTML = '<div class="card">結果が見つかりませんでした。</div>';
        return;
      }
      resultsDiv.innerHTML = res.results.map(r => `
        <div class="search-result card">
          <h3><a href="${esc(String(r.metadata?.url || '')) || '#'}" target="_blank" rel="noopener">${esc(r.title) || '無題'}</a></h3>
          <p>${esc(r.snippet?.substring(0, 300))}</p>
          <small>スコア: ${r.score?.toFixed(3) ?? '-'} | ソース: ${esc(r.source)} | ${esc(String(r.metadata?.authors || ''))}</small>
        </div>
      `).join('');
    } catch (e) {
      resultsDiv.innerHTML = `<div class="card status-error">検索失敗: ${esc((e as Error).message)}</div>`;
    }
  };

  const loadPapers = async (): Promise<void> => {
    const query = searchInput.value.trim();
    const resultsDiv = document.getElementById('search-results')!;
    resultsDiv.innerHTML = '<div class="loading">論文読み込み中...</div>';
    try {
      const res: GnosisPapersResponse = await api.gnosisPapers(query, 20);
      if (res.papers.length === 0) {
        resultsDiv.innerHTML = '<div class="card">論文が見つかりませんでした。</div>';
        return;
      }
      resultsDiv.innerHTML = `
        <div class="nr-header">📚 ${res.total} 件 ${query ? `「${esc(query)}」に一致` : ''}</div>
        ${res.papers.map(p => renderPaperCard(p)).join('')}
      `;
      resultsDiv.querySelectorAll('.nr-narrate-btn').forEach(btn => {
        btn.addEventListener('click', () => void handleNarrate(btn as HTMLButtonElement));
      });
    } catch (e) {
      resultsDiv.innerHTML = `<div class="card status-error">論文読み込み失敗: ${esc((e as Error).message)}</div>`;
    }
  };

  searchBtn.addEventListener('click', doSearch);
  papersBtn.addEventListener('click', () => void loadPapers());
  searchInput.addEventListener('keydown', (e: KeyboardEvent) => {
    if (e.key === 'Enter') void doSearch();
  });
  searchInput.focus();
}
