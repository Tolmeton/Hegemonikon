import './css/content.css';
import { api } from '../api/client';
import type { TimelineEvent, TimelineEventDetail } from '../api/client';
import { esc } from '../utils';
import { marked } from 'marked';
import { enhanceMarkdown } from './enhance';

let tlCurrentType: string | undefined;
let tlCurrentOffset = 0;
const TL_PAGE_SIZE = 30;

export async function renderTimelineView(): Promise<void> {
  const app = document.getElementById('view-content');
  if (!app) return;
  tlCurrentType = undefined;
  tlCurrentOffset = 0;

  let statsHtml = '';
  try {
    const stats = await api.timelineStats();
    statsHtml = `
      <div class="tl-stats">
        <span class="tl-stat">📋 Handoff: <strong>${stats.by_type.handoff}</strong></span>
        <span class="tl-stat">💡 Doxa: <strong>${stats.by_type.doxa}</strong></span>
        <span class="tl-stat">⚙️ WF: <strong>${stats.by_type.workflow}</strong></span>
        <span class="tl-stat">◆ Kalon: <strong>${stats.by_type.kalon || 0}</strong></span>
        <span class="tl-stat tl-stat-total">合計: <strong>${stats.total}</strong></span>
      </div>`;
  } catch { /* ignore */ }

  app.innerHTML = `
    <div class="tl-view">
      <div class="tl-header">
        <h2>📅 セッション・タイムライン</h2>
        ${statsHtml}
        <div class="tl-filters">
          <button class="tl-filter active" data-type="">全て</button>
          <button class="tl-filter" data-type="handoff">📋 Handoff</button>
          <button class="tl-filter" data-type="doxa">💡 Doxa</button>
          <button class="tl-filter" data-type="workflow">⚙️ Workflow</button>
          <button class="tl-filter" data-type="kalon">◆ Kalon</button>
        </div>
      </div>
      <div class="tl-body">
        <div class="tl-list" id="tl-list"><div class="loading">読み込み中...</div></div>
        <div class="tl-detail" id="tl-detail"><div class="tl-empty">← イベントを選択してください</div></div>
      </div>
    </div>`;

  app.querySelectorAll('.tl-filter').forEach(btn => {
    btn.addEventListener('click', () => {
      app.querySelectorAll('.tl-filter').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const t = (btn as HTMLElement).dataset.type;
      tlCurrentType = t || undefined;
      tlCurrentOffset = 0;
      void loadTimelineEvents();
    });
  });
  await loadTimelineEvents();
}

async function loadTimelineEvents(): Promise<void> {
  const listEl = document.getElementById('tl-list');
  if (!listEl) return;
  try {
    const data = await api.timelineEvents(TL_PAGE_SIZE, tlCurrentOffset, tlCurrentType);
    if (data.events.length === 0) {
      listEl.innerHTML = '<div class="tl-empty">イベントがありません</div>';
      return;
    }
    const typeIcon = (t: string) => t === 'handoff' ? '📋' : t === 'doxa' ? '💡' : t === 'kalon' ? '◆' : '⚙️';
    const typeClass = (t: string) => `tl-type-${t}`;
    const eventsHtml = data.events.map((e: TimelineEvent) => `
      <div class="tl-event-card" data-event-id="${esc(e.id)}">
        <div class="tl-event-top">
          <span class="tl-event-icon ${typeClass(e.type)}">${typeIcon(e.type)}</span>
          <span class="tl-event-date">${esc(e.date || e.mtime?.substring(0, 10))}</span>
        </div>
        <div class="tl-event-title">${esc(e.title)}</div>
        <div class="tl-event-summary">${esc(e.summary?.substring(0, 120))}${(e.summary?.length || 0) > 120 ? '...' : ''}</div>
        <div class="tl-event-meta">
          <span class="tl-event-type">${esc(e.type)}</span>
          <span class="tl-event-size">${Math.round((e.size_bytes || 0) / 1024)}KB</span>
        </div>
      </div>`).join('');
    const paginationHtml = `
      <div class="tl-pagination">
        ${tlCurrentOffset > 0 ? '<button class="btn btn-sm" id="tl-prev">← 前へ</button>' : ''}
        <span class="tl-page-info">${tlCurrentOffset + 1}–${Math.min(tlCurrentOffset + TL_PAGE_SIZE, data.total)} / ${data.total}</span>
        ${data.has_more ? '<button class="btn btn-sm" id="tl-next">次へ →</button>' : ''}
      </div>`;
    listEl.innerHTML = eventsHtml + paginationHtml;
    listEl.querySelectorAll('.tl-event-card').forEach(el => {
      el.addEventListener('click', () => {
        listEl.querySelectorAll('.tl-event-card').forEach(c => c.classList.remove('active'));
        el.classList.add('active');
        const eventId = (el as HTMLElement).dataset.eventId;
        if (eventId) void loadTimelineDetail(eventId);
      });
    });
    document.getElementById('tl-prev')?.addEventListener('click', () => {
      tlCurrentOffset = Math.max(0, tlCurrentOffset - TL_PAGE_SIZE);
      void loadTimelineEvents();
    });
    document.getElementById('tl-next')?.addEventListener('click', () => {
      tlCurrentOffset += TL_PAGE_SIZE;
      void loadTimelineEvents();
    });
  } catch (e) {
    listEl.innerHTML = `<div class="card status-error">Timeline 読み込み失敗: ${esc((e as Error).message)}</div>`;
  }
}

async function loadTimelineDetail(eventId: string): Promise<void> {
  const detailEl = document.getElementById('tl-detail');
  if (!detailEl) return;
  detailEl.innerHTML = '<div class="loading">読み込み中...</div>';
  try {
    const event: TimelineEventDetail = await api.timelineEvent(eventId);
    const typeIcon = event.type === 'handoff' ? '📋' : event.type === 'doxa' ? '💡' : event.type === 'kalon' ? '◆' : '⚙️';
    const htmlContent = marked.parse(event.content || '') as string;
    detailEl.innerHTML = `
      <div class="tl-detail-header">
        <span class="tl-detail-icon">${typeIcon}</span>
        <div class="tl-detail-info">
          <h3>${esc(event.title)}</h3>
          <div class="tl-detail-meta">
            <span>${esc(event.type)}</span>
            <span>${esc(event.date || event.mtime?.substring(0, 10))}</span>
            <span>${esc(event.filename)}</span>
            <span>${Math.round((event.size_bytes || 0) / 1024)}KB</span>
          </div>
        </div>
      </div>
      <div class="tl-detail-content">${htmlContent}</div>`;

    // Enhance code blocks & alerts
    const contentEl = detailEl.querySelector('.tl-detail-content');
    if (contentEl) enhanceMarkdown(contentEl as HTMLElement);
  } catch (e) {
    detailEl.innerHTML = `<div class="card status-error">詳細読み込み失敗: ${esc((e as Error).message)}</div>`;
  }
}
