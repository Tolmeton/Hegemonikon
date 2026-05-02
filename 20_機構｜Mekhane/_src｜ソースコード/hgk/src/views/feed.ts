import './css/feed.css';
import { api } from '../api/client';
import { getCurrentRoute, esc, startPolling } from '../utils';

// ─── Types (inline — api-types.ts に追加後は import に切替) ──

interface FeedItem {
  id: string;
  persona_id: string;
  persona_name: string;
  persona_icon: string;
  headline: string;
  body: string;
  source_url: string;
  source_type: string;
  tags: string[];
  liked: boolean;
  comments: Array<{ text: string; timestamp: string }>;
  created_at: string;
  relevance_score: number;
}

interface FeedTimeline {
  items: FeedItem[];
  total: number;
  has_more: boolean;
}

interface FeedStats {
  total_items: number;
  total_likes: number;
  total_comments: number;
  persona_counts: Record<string, number>;
}

// ─── State ──────────────────────────────────────────────────

let currentItems: FeedItem[] = [];

// ─── Main Renderer ──────────────────────────────────────────

export async function renderFeedView(): Promise<void> {
  await renderFeedContent();
  startPolling(renderFeedContent, 60_000);
}

async function renderFeedContent(): Promise<void> {
  const app = document.getElementById('view-content')!;
  if (getCurrentRoute() !== 'feed') return;

  // Show loading
  app.innerHTML = `
    <div class="feed-layout">
      <div class="feed-loading">
        <div class="feed-spinner"></div>
        フィードを読み込み中...
      </div>
    </div>`;

  let timeline: FeedTimeline | null = null;
  let stats: FeedStats | null = null;

  try {
    const [rawTimeline, rawStats] = await Promise.all([
      api.feedTimeline(20, 0).catch((): null => null),
      api.feedStats().catch((): null => null),
    ]);
    timeline = rawTimeline as FeedTimeline | null;
    stats = rawStats as FeedStats | null;
  } catch { /* ok */ }

  if (getCurrentRoute() !== 'feed') return;

  currentItems = timeline?.items ?? [];

  const statsBar = stats ? `
    <div class="feed-stats">
      <div class="feed-stat">📝 <span class="feed-stat-value">${stats.total_items}</span> ポスト</div>
      <div class="feed-stat">❤️ <span class="feed-stat-value">${stats.total_likes}</span> いいね</div>
      <div class="feed-stat">💬 <span class="feed-stat-value">${stats.total_comments}</span> コメント</div>
    </div>` : '';

  const tweetsHtml = currentItems.length > 0
    ? currentItems.map(renderTweet).join('')
    : `<div class="feed-empty">
             <div class="feed-empty-icon">📰</div>
             <div class="feed-empty-title">まだポストがありません</div>
             <div class="feed-empty-desc">
               「PKS から生成」ボタンで、知識プッシュからツイートを生成できます。
             </div>
           </div>`;

  app.innerHTML = `
    <div class="feed-layout">
      <div class="feed-header">
        <div class="feed-header-left">
          <span class="feed-header-title">📰 フィード</span>
          ${timeline ? `<span class="feed-header-count">${timeline.total} 件</span>` : ''}
        </div>
        <div class="feed-header-actions">
          <button id="feed-generate-btn" class="feed-btn feed-btn-primary">PKS から生成</button>
          <button id="feed-refresh-btn" class="feed-btn">更新</button>
        </div>
      </div>
      ${statsBar}
      <div class="feed-timeline" id="feed-timeline">
        ${tweetsHtml}
      </div>
    </div>`;

  bindEvents();
}

// ─── Tweet Renderer ─────────────────────────────────────────

function renderTweet(item: FeedItem): string {
  const timeAgo = formatTimeAgo(item.created_at);
  const relevanceClass = item.relevance_score >= 0.7 ? 'high'
    : item.relevance_score >= 0.4 ? 'mid' : 'low';

  const tagsHtml = item.tags.length > 0
    ? `<div class="feed-tags">${item.tags.map(t => `<span class="feed-tag">${esc(t)}</span>`).join('')}</div>`
    : '';

  const commentsHtml = item.comments.length > 0
    ? `<div class="feed-comments">
             ${item.comments.map(c => `
               <div class="feed-comment">
                 <span class="feed-comment-text">${esc(c.text)}</span>
                 <span class="feed-comment-time">${formatTimeAgo(c.timestamp)}</span>
               </div>
             `).join('')}
           </div>`
    : '';

  const sourceLabel = item.source_url
    ? `<a href="${esc(item.source_url)}" target="_blank" rel="noopener" class="feed-action-btn">🔗 ソース</a>`
    : '';

  return `
    <div class="feed-tweet" data-id="${esc(item.id)}">
      <div class="feed-tweet-header">
        <div class="feed-avatar">${esc(item.persona_icon)}</div>
        <div class="feed-tweet-body-wrap">
          <div class="feed-tweet-identity">
            <span class="feed-persona-name">${esc(item.persona_name)}</span>
            <span class="feed-source-badge ${esc(item.source_type)}">${esc(item.source_type)}</span>
            ${item.relevance_score > 0 ? `<span class="feed-relevance ${relevanceClass}">${(item.relevance_score * 100).toFixed(0)}%</span>` : ''}
            <span class="feed-tweet-time">${timeAgo}</span>
          </div>
          <div class="feed-tweet-headline">${esc(item.headline)}</div>
          <div class="feed-tweet-content">${esc(item.body)}</div>
          ${tagsHtml}
          <div class="feed-actions">
            <button class="feed-action-btn feed-like-btn ${item.liked ? 'liked' : ''}" data-id="${esc(item.id)}">
              ${item.liked ? '❤️' : '🤍'} いいね
            </button>
            <button class="feed-action-btn feed-comment-toggle" data-id="${esc(item.id)}">
              💬 コメント ${item.comments.length > 0 ? `(${item.comments.length})` : ''}
            </button>
            ${sourceLabel}
          </div>
          ${commentsHtml}
          <div class="feed-comment-input-row" id="comment-input-${esc(item.id)}" style="display:none;">
            <input class="feed-comment-input" placeholder="メモやボヤキを書く..." data-id="${esc(item.id)}" />
            <button class="feed-comment-submit" data-id="${esc(item.id)}">送信</button>
          </div>
        </div>
      </div>
    </div>`;
}

// ─── Event Binding ──────────────────────────────────────────

function bindEvents(): void {
  // Generate from PKS
  document.getElementById('feed-generate-btn')?.addEventListener('click', async () => {
    const btn = document.getElementById('feed-generate-btn') as HTMLButtonElement;
    btn.disabled = true;
    btn.textContent = '生成中...';
    try {
      await api.feedGenerate();
      void renderFeedContent();
    } catch (e) {
      btn.textContent = `エラー: ${(e as Error).message}`;
      setTimeout(() => { btn.textContent = 'PKS から生成'; btn.disabled = false; }, 3000);
    }
  });

  // Refresh
  document.getElementById('feed-refresh-btn')?.addEventListener('click', () => {
    void renderFeedContent();
  });

  // Like buttons
  document.querySelectorAll('.feed-like-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const target = e.currentTarget as HTMLButtonElement;
      const itemId = target.dataset.id ?? '';
      target.disabled = true;
      try {
        const result = await api.feedLike(itemId) as { liked: boolean };
        target.classList.toggle('liked', result.liked);
        target.innerHTML = `${result.liked ? '❤️' : '🤍'} いいね`;
      } catch {
        // silent
      }
      target.disabled = false;
    });
  });

  // Comment toggle
  document.querySelectorAll('.feed-comment-toggle').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const target = e.currentTarget as HTMLButtonElement;
      const itemId = target.dataset.id ?? '';
      const inputRow = document.getElementById(`comment-input-${itemId}`);
      if (inputRow) {
        inputRow.style.display = inputRow.style.display === 'none' ? 'flex' : 'none';
        const input = inputRow.querySelector('input');
        if (input && inputRow.style.display === 'flex') input.focus();
      }
    });
  });

  // Comment submit
  document.querySelectorAll('.feed-comment-submit').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const target = e.currentTarget as HTMLButtonElement;
      const itemId = target.dataset.id ?? '';
      const inputRow = document.getElementById(`comment-input-${itemId}`);
      const input = inputRow?.querySelector('input') as HTMLInputElement | null;
      if (!input || !input.value.trim()) return;

      target.disabled = true;
      try {
        await api.feedComment(itemId, input.value.trim());
        void renderFeedContent();
      } catch {
        target.disabled = false;
      }
    });
  });

  // Enter key for comment
  document.querySelectorAll('.feed-comment-input').forEach(input => {
    input.addEventListener('keydown', (e) => {
      if ((e as KeyboardEvent).key === 'Enter') {
        const itemId = (input as HTMLInputElement).dataset.id ?? '';
        const submitBtn = document.querySelector(`.feed-comment-submit[data-id="${itemId}"]`) as HTMLButtonElement | null;
        submitBtn?.click();
      }
    });
  });
}

// ─── Helpers ────────────────────────────────────────────────

function formatTimeAgo(isoDate: string): string {
  try {
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'たった今';
    if (diffMins < 60) return `${diffMins}分前`;
    if (diffHours < 24) return `${diffHours}時間前`;
    if (diffDays < 7) return `${diffDays}日前`;
    return date.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}
