import './css/dashboard.css';
import { api } from '../api/client';
import type {
  HealthReportResponse, Notification, DigestCandidate, DigestReport,
  QuotaResponse, QuotaModel, PKSGatewayStatsResponse,
  SentinelLatest, SentinelPaper,
  EpistemicHealthResponse,
  BasanosL2ScanResponse,
  BasanosL2HistoryResponse, BasanosL2TrendResponse,
  SchedulerStatusResponse, SchedulerRun, SchedulerTrendResponse,
  SchedulerEvolutionResponse, SchedulerRotationResponse, RotationDay,
  TheoremUsageResponse,
  WALStatusResponse,
  MotherbrainStatusResponse, MotherbrainNarrateResponse,
} from '../api/client';
import { getCurrentRoute, esc, applyCountUpAnimations, applyStaggeredFadeIn, startPolling, relativeTime } from '../utils';
import { renderUsageCard } from '../telemetry';

// ─── Dashboard ───────────────────────────────────────────────

export async function renderDashboard(): Promise<void> {
  await renderDashboardContent();
  startPolling(renderDashboardContent, 60_000);
}

async function renderDashboardContent(): Promise<void> {
  const [health, healthCheck, fep, gnosisStats, criticals, kalonHist, quota, digestLatest, gatewayStats, sentinel, epistemicHealth, basanosL2, basanosL2History, basanosL2Trend, schedulerStatus, schedulerTrend, schedulerEvolution, schedulerRotation, theoremUsage, walStatus, hgkHealthMd, hgkProactiveMd, motherbrainStatus, motherbrainNarration] = await Promise.all([
    api.status().catch((): null => null),
    api.health().catch((): null => null),
    api.fepState().catch((): null => null),
    api.gnosisStats().catch((): null => null),
    api.notifications(5, 'CRITICAL').catch((): Notification[] => []),
    api.kalonHistory(5).catch((): null => null),
    api.quota().catch((): null => null),
    api.digestorLatest().catch((): null => null),
    api.pksGatewayStats().catch((): null => null),
    api.sentinelLatest().catch((): null => null),
    api.epistemicHealth().catch((): null => null),
    api.basanosL2Scan().catch((): null => null),
    api.basanosL2History(10).catch((): null => null),
    api.basanosL2Trend(10).catch((): null => null),
    api.schedulerStatus().catch((): null => null),
    api.schedulerTrend(14).catch((): null => null),
    api.schedulerEvolution().catch((): null => null),
    api.schedulerRotation().catch((): null => null),
    api.theoremUsage().catch((): null => null),
    api.walStatus().catch((): null => null),
    // Phase 6: HGK Gateway data for WBC + Proactive Push
    api.hgkHealth().catch((): null => null),
    api.hgkProactive('', 3, true).catch((): null => null),
    api.motherbrainGetStatus().catch((): null => null),
    api.motherbrainGetNarration('handoff').catch((): null => null),
  ]);

  const app = document.getElementById('view-content')!;
  if (getCurrentRoute() !== 'dashboard') return;

  const score = health ? health.score : 0;
  const scoreClass = score >= 0.8 ? 'status-ok' : score >= 0.5 ? 'status-warn' : 'status-error';
  const healthStatus = health
    ? `<span class="${scoreClass}">稼働中 (${score.toFixed(2)})</span>`
    : '<span class="status-error">オフライン</span>';

  const historyLen = fep ? fep.history_length : '-';
  const uptimeSec = healthCheck?.uptime_seconds ?? 0;
  const uptimeDisplay = uptimeSec >= 3600 ? `${(uptimeSec / 3600).toFixed(1)}時間`
    : uptimeSec >= 60 ? `${Math.floor(uptimeSec / 60)}分`
      : `${Math.floor(uptimeSec)}秒`;

  const gnosisCount = gnosisStats?.total ?? '-';

  const alertHtml = criticals.length > 0 ? `
    <div class="alert-banner fade-in">
      <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.5rem;">
        <span class="status-dot error"></span>
        <strong style="color:var(--error-color);">緊急通知 ${criticals.length}件</strong>
      </div>
      ${criticals.slice(0, 3).map((n: Notification) => `
        <div style="padding:0.2rem 0; font-size:0.875rem;">
          ${esc(n.title)}
          <span style="color:var(--text-secondary); font-size:0.75rem;"> — ${esc(relativeTime(n.timestamp))}</span>
        </div>
      `).join('')}
      ${criticals.length > 3 ? `<div style="color:var(--text-secondary); font-size:0.8rem;">他 ${criticals.length - 3}件...</div>` : ''}
    </div>
  ` : '';

  app.innerHTML = `
    <h1>ダッシュボード <small class="poll-badge">自動更新 60秒</small></h1>
    ${alertHtml}
    <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
      <div class="card">
        <div class="metric-label">システム状態</div>
        <div class="metric">
          <span class="status-dot ${score >= 0.8 ? 'ok' : score >= 0.5 ? 'warn' : 'error'}"></span>
          ${healthStatus}
        </div>
        <p style="color:var(--text-secondary); font-size:0.8rem; margin:0.25rem 0 0;">稼働時間: ${esc(uptimeDisplay)}</p>
      </div>
      <div class="card">
        <div class="metric-label">FEP エージェント</div>
        <div class="metric"><span data-count-target="${typeof historyLen === 'number' ? historyLen : 0}">${String(historyLen)}</span></div>
        <p style="color:var(--text-secondary); font-size:0.8rem; margin:0.25rem 0 0;">推論ステップ数</p>
      </div>
      <div class="card">
        <div class="metric-label">Gnōsis</div>
        <div class="metric"><span data-count-target="${typeof gnosisCount === 'number' ? gnosisCount : 0}">${String(gnosisCount)}</span></div>
        <p style="color:var(--text-secondary); font-size:0.8rem; margin:0.25rem 0 0;">収集済み論文</p>
      </div>
      <div class="card kalon-card">
        <div class="kalon-card-header">
          <span class="kalon-card-icon">◆</span>
          <span class="kalon-card-title">Kalon</span>
        </div>
        <div class="kalon-card-equation">Kalon(x) ⟺ x = Fix(G∘F)</div>
        <div class="kalon-card-attrs">
          <span class="kalon-card-attr">判定数: <strong>${kalonHist?.total ?? 0}</strong></span>
          ${kalonHist?.judgments?.[0] ? `<span class="kalon-card-attr">最新: ${esc(kalonHist.judgments[0].verdict)} ${esc(kalonHist.judgments[0].concept)}</span>` : ''}
        </div>
        <div class="kalon-card-hint">Ctrl+K → kalon [概念] で判定</div>
      </div>
    </div>
    ${renderMotherbrainCard(motherbrainStatus, motherbrainNarration)}
    ${renderWbcCard(hgkHealthMd)}
    ${renderProactivePushCard(hgkProactiveMd)}
    ${renderSentinelCard(sentinel)}
    ${renderEpistemicCard(epistemicHealth)}
    ${renderBasanosL2Card(basanosL2)}
    ${renderBasanosL2HistoryCard(basanosL2History, basanosL2Trend)}
    ${renderQuotaCard(quota)}
    ${renderDigestCard(digestLatest)}
    ${renderGatewayCard(gatewayStats)}
    ${renderSchedulerCard(schedulerStatus, schedulerTrend, schedulerEvolution, schedulerRotation)}
    ${renderTheoremCard(theoremUsage)}
    ${renderWALCard(walStatus)}
    ${renderHealthItems(health)}
    ${renderUsageCard()}
    <footer class="dashboard-footer">
      <span>Hegemonikón Desktop v0.3.0</span>
      <span>·</span>
      <span>FEP-based Cognitive Hypervisor</span>
      <span>·</span>
      <span>${new Date().toLocaleDateString('ja-JP')}</span>
    </footer>
  `;

  applyCountUpAnimations(app);
  applyStaggeredFadeIn(app);
}

// ─── Motherbrain Card Rendering ───
(window as any).refreshMotherbrain = async () => {
  try {
    await api.motherbrainRefreshStatus("fast");
    renderDashboard();
  } catch (e) {
    console.error(e);
  }
};

function renderMotherbrainCard(status: MotherbrainStatusResponse | null, narration: MotherbrainNarrateResponse | null): string {
  if (!status || !narration) return '';

  const urgencyColor = narration.urgency === 'high' ? 'var(--error-color, #ef4444)'
    : narration.urgency === 'medium' ? 'var(--warning-color, #eab308)'
      : 'var(--success-color, #22c55e)';

  const timeStr = status.last_boot_time
    ? (() => {
      try {
        const d = new Date(status.last_boot_time * 1000);
        return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
      } catch { return ''; }
    })()
    : '';

  const axesCount = Object.keys(status.axes || {}).length;

  return `
    <div class="card" style="margin-top:1rem; border-left: 4px solid ${urgencyColor};">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
        <span class="metric-label" style="display:flex; align-items:center; gap:0.5rem; color:var(--text-primary);">
          🧠 <strong>Motherbrain</strong>
        </span>
        <span style="color:var(--text-secondary); font-size:0.8rem;">
          Boot Context (${axesCount} axes) ${timeStr ? `· Sync: ${esc(timeStr)}` : ''}
          <button onclick="window.refreshMotherbrain()" class="icon-btn" style="margin-left:0.5rem;" title="Refresh Boot Context" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.7" style="opacity:0.7; cursor:pointer; background:transparent; border:none; color:var(--text-secondary);">↻</button>
        </span>
      </div>
      <div style="font-size:0.95rem; line-height:1.5; margin-bottom:0.75rem; color: var(--text-primary);">
        ${esc(narration.narration)}
      </div>
      ${narration.action_suggestions && narration.action_suggestions.length > 0 ? `
        <div style="background:var(--bg-tertiary); padding:0.5rem 0.75rem; border-radius:4px; font-family:var(--font-mono); font-size:0.8rem; color:var(--text-primary);">
          <div style="color:var(--accent-color); font-weight:600; margin-bottom:0.25rem;">Action Suggestions:</div>
          ${narration.action_suggestions.map(s => `<div>${esc(s)}</div>`).join('')}
        </div>
      ` : ''}
    </div>
  `;
}


function renderQuotaCard(quota: QuotaResponse | null): string {
  if (!quota) return '';
  if (quota.error) {
    const isLsError = quota.error.includes('Language Server') || quota.error.includes('agq-check');
    if (isLsError) {
      return `
        <div class="card quota-card" style="margin-top:1rem;">
          <div class="quota-header">
            <span class="metric-label">⚡ Quota</span>
            <span class="quota-plan" style="color: var(--text-secondary);">スタンドアロン</span>
          </div>
          <div style="color: var(--text-secondary); font-size: 0.85rem; padding: 0.5rem 0;">
            📡 Language Server 未接続 — Quota 追跡は LS 起動後に有効になります
          </div>
        </div>
      `;
    }
    return `
      <div class="card quota-card" style="margin-top:1rem;">
        <div class="metric-label">⚡ Quota</div>
        <div class="status-error" style="font-size:0.85rem;">Quota 情報取得不可: ${esc(quota.error)}</div>
      </div>
    `;
  }

  const statusIcon: Record<string, string> = {
    green: '🟢', yellow: '🟡', orange: '🟠', red: '🔴', unknown: '⚪',
  };
  const statusColor: Record<string, string> = {
    green: 'var(--success-color, #22c55e)',
    yellow: 'var(--warning-color, #eab308)',
    orange: 'var(--quota-orange, #f97316)',
    red: 'var(--error-color, #ef4444)',
    unknown: 'var(--text-secondary)',
  };

  const modelsHtml = quota.models.map((m: QuotaModel) => `
    <div class="quota-model">
      <div class="quota-model-header">
        <span class="quota-model-icon">${statusIcon[m.status] ?? '⚪'}</span>
        <span class="quota-model-label">${esc(m.label)}</span>
        <span class="quota-model-pct" style="color:${statusColor[m.status] ?? ''}">${m.remaining_pct}%</span>
      </div>
      <div class="quota-bar">
        <div class="quota-bar-fill" style="width:${m.remaining_pct}%; background:${statusColor[m.status] ?? ''}"></div>
      </div>
      ${m.reset_time ? `<div class="quota-model-reset">↻ ${esc(m.reset_time)} UTC</div>` : ''}
    </div>
  `).join('');

  const alertHtml = (quota.overall_status === 'orange' || quota.overall_status === 'red')
    ? `<div class="alert-banner quota-alert fade-in" style="margin-bottom:0.75rem;">
         <span class="status-dot ${quota.overall_status === 'red' ? 'error' : 'warn'}"></span>
         <strong style="color:${quota.overall_status === 'red' ? 'var(--error-color)' : 'var(--quota-orange, #f97316)'}">
           ${quota.overall_status === 'red' ? '🔴 Quota 残量危険 — Turtle Mode 推奨' : '🟠 Quota 残量低下'}
         </strong>
       </div>`
    : '';

  const pc = quota.prompt_credits;
  const fc = quota.flow_credits;

  return `
    <div class="card quota-card" style="margin-top:1rem;">
      ${alertHtml}
      <div class="quota-header">
        <span class="metric-label">⚡ Quota</span>
        <span class="quota-plan">${esc(quota.plan)}</span>
      </div>
      ${modelsHtml}
      <div class="quota-credits">
        <span>💳 Prompt: <strong>${pc.available}</strong>/${pc.monthly}</span>
        <span>🌊 Flow: <strong>${fc.available}</strong>/${fc.monthly}</span>
      </div>
    </div>
  `;
}

function renderDigestCard(digest: DigestReport | null): string {
  if (!digest) return '';

  const timeStr = digest.timestamp
    ? (() => {
      try {
        const d = new Date(digest.timestamp);
        return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
      } catch { return digest.timestamp; }
    })()
    : '';

  if (digest.candidates.length === 0) {
    return `
      <div class="card digest-card" style="margin-top:1rem;">
        <div class="digest-header">
          <span class="metric-label">🔬 最新消化</span>
          <span class="digest-timestamp">${esc(timeStr)}</span>
        </div>
        <div style="color:var(--text-secondary); font-size:0.85rem; padding:0.5rem 0;">
          消化候補なし — <code>digest_to_ki.py</code> を実行してください
        </div>
      </div>
    `;
  }

  const candidatesHtml = digest.candidates.slice(0, 5).map((c: DigestCandidate) => {
    const scoreWidth = Math.round(c.score * 100);
    const scoreColor = c.score >= 0.7 ? 'var(--success-color, #22c55e)'
      : c.score >= 0.4 ? 'var(--warning-color, #eab308)'
        : 'var(--text-secondary)';
    const topicTags = c.matched_topics.map(t =>
      `<span class="digest-topic-tag">${esc(t)}</span>`
    ).join('');

    return `
      <div class="digest-candidate">
        <div class="digest-candidate-header">
          <span class="digest-candidate-title">${c.url
        ? `<a href="${esc(c.url)}" target="_blank" rel="noopener" class="digest-link">${esc(c.title)}</a>`
        : esc(c.title)
      }</span>
          <span class="digest-candidate-score" style="color:${scoreColor}">${c.score.toFixed(2)}</span>
        </div>
        <div class="quota-bar" style="margin:0.2rem 0;">
          <div class="quota-bar-fill" style="width:${scoreWidth}%; background:${scoreColor}"></div>
        </div>
        <div class="digest-candidate-meta">
          <span class="digest-source">${esc(c.source)}</span>
          ${topicTags}
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="card digest-card" style="margin-top:1rem;">
      <div class="digest-header">
        <span class="metric-label">🔬 最新消化</span>
        <span class="digest-meta">
          ${digest.total_papers}件中 ${digest.candidates_selected}件選出
          <span class="digest-timestamp">${esc(timeStr)}</span>
        </span>
      </div>
      ${candidatesHtml}
    </div>
  `;
}

function renderHealthItems(health: HealthReportResponse | null): string {
  if (!health) return '';
  return `
    <div class="card" style="margin-top: 1rem;">
      <h3>サービス詳細</h3>
      <table class="data-table">
        <thead><tr><th>サービス</th><th>状態</th><th>詳細</th></tr></thead>
        <tbody>
          ${health.items.map((item: HealthReportResponse['items'][number]) => {
    const dotCls = item.status === 'ok' ? 'ok' : item.status === 'warn' ? 'warn' : 'error';
    const tagCls = item.status === 'ok' ? 'tag-success' : item.status === 'warn' ? 'tag-warning' : 'tag-error';
    const statusJa = item.status === 'ok' ? '正常' : item.status === 'warn' ? '注意' : 'エラー';
    return `<tr>
              <td>${esc(item.emoji)} ${esc(item.name)}</td>
              <td><span class="status-dot ${dotCls}"></span><span class="tag ${tagCls}">${esc(statusJa)}</span></td>
              <td style="color:var(--text-secondary);">${esc(item.detail)}</td>
            </tr>`;
  }).join('')}
        </tbody>
      </table>
    </div>
  `;
}

// ─── Phase 6: WBC Card ──────────────────────────────────────

function renderWbcCard(data: { result: string } | null): string {
  if (!data?.result) return '';
  const md = data.result;

  // Parse markdown: extract WBC alerts count, health score, heartbeat
  const wbcMatch = md.match(/総アラート数[:\s]*(\d+)/);
  const scoreMatch = md.match(/最新スコア[:\s]*([\d.]+)/);
  const heartbeatMatch = md.match(/総拍動数[:\s]*(\d+)/);
  const lastBeatMatch = md.match(/最終拍動[:\s]*(.+)/);
  const gitDirtyMatch = md.match(/Dirty[:\s]*(True|False)/i);

  const wbcCount = wbcMatch?.[1] ? parseInt(wbcMatch[1]) : 0;
  const healthScore = scoreMatch?.[1] ? parseFloat(scoreMatch[1]) : 0;
  const heartbeats = heartbeatMatch?.[1] ? parseInt(heartbeatMatch[1]) : 0;
  const lastBeat = lastBeatMatch?.[1]?.trim() ?? '不明';
  const gitDirty = gitDirtyMatch?.[1] === 'True';

  const scoreClass = healthScore >= 0.8 ? 'ok' : healthScore >= 0.5 ? 'warn' : 'error';
  const wbcClass = wbcCount === 0 ? 'ok' : wbcCount < 10 ? 'warn' : 'error';

  return `
    <div class="card wbc-card" style="margin-top: 1rem;">
      <h3>🛡️ HGK Health / WBC</h3>
      <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.75rem;">
        <div style="text-align:center;">
          <div class="metric-label">Health Score</div>
          <div class="metric"><span class="status-dot ${scoreClass}"></span> ${healthScore.toFixed(2)}</div>
        </div>
        <div style="text-align:center;">
          <div class="metric-label">WBC Alerts</div>
          <div class="metric"><span class="status-dot ${wbcClass}"></span> <span data-count-target="${wbcCount}">${wbcCount}</span></div>
        </div>
        <div style="text-align:center;">
          <div class="metric-label">💓 Heartbeat</div>
          <div class="metric"><span data-count-target="${heartbeats}">${heartbeats}</span></div>
          <div style="color:var(--text-secondary); font-size:0.75rem;">最終: ${esc(lastBeat)}</div>
        </div>
        <div style="text-align:center;">
          <div class="metric-label">Git 状態</div>
          <div class="metric">${gitDirty ? '<span class="status-dot warn"></span> Dirty' : '<span class="status-dot ok"></span> Clean'}</div>
        </div>
      </div>
    </div>
  `;
}

// ─── Phase 6: Proactive Push Card ───────────────────────────

function renderProactivePushCard(data: { result: string } | null): string {
  if (!data?.result) return '';
  const md = data.result;

  // Parse the markdown to extract individual push entries
  const entries: { title: string; message: string; relevance: string }[] = [];
  const sections = md.split(/---\s*\n/).filter(s => s.includes('が語りかけています'));

  for (const section of sections.slice(0, 3)) {
    const titleMatch = section.match(/\*\*(.+?)\*\*\s*が語りかけています/);
    const msgMatch = section.match(/>\s*(.+?)(?:\n\n|\n\*\*)/s);
    const relMatch = section.match(/関連度[:\s]*([\d.]+)/);
    if (titleMatch?.[1]) {
      entries.push({
        title: titleMatch[1].trim(),
        message: msgMatch?.[1]?.trim().slice(0, 150) ?? '',
        relevance: relMatch?.[1] ?? '?',
      });
    }
  }

  if (entries.length === 0) return '';

  return `
    <div class="card proactive-card" style="margin-top: 1rem;">
      <h3>📣 Autophōnos — 論文の語りかけ</h3>
      <div style="display: flex; flex-direction: column; gap: 0.5rem;">
        ${entries.map(e => `
          <div class="proactive-entry fade-in">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
              <strong style="font-size: 0.85rem;">${esc(e.title)}</strong>
              <span class="tag tag-info" style="font-size: 0.7rem;">📊 ${esc(e.relevance)}</span>
            </div>
            <div style="color: var(--text-secondary); font-size: 0.82rem; line-height: 1.4;">${esc(e.message)}${e.message.length >= 150 ? '...' : ''}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

function renderGatewayCard(stats: PKSGatewayStatsResponse | null): string {
  if (!stats || !stats.enabled) return '';

  const timeStr = stats.timestamp
    ? (() => {
      try {
        const d = new Date(stats.timestamp);
        return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
      } catch { return ''; }
    })()
    : '';

  const sourceEntries = Object.entries(stats.sources);
  if (sourceEntries.length === 0) {
    return `
      <div class="card" style="margin-top:1rem;">
        <div class="metric-label">🌉 Gateway ソース</div>
        <div style="color:var(--text-secondary); font-size:0.85rem; padding:0.5rem 0;">
          Gateway 有効 — ソース未検出
        </div>
      </div>
    `;
  }

  const maxCount = Math.max(...sourceEntries.map(([, v]) => (typeof v === 'object' ? v.count ?? 0 : 0)), 1);
  const sourceColors: Record<string, string> = {
    ideas: 'var(--warning-color, #eab308)',
    doxa: 'var(--info-color, #3b82f6)',
    handoff: 'var(--success-color, #22c55e)',
    ki: 'var(--accent-color, #a855f7)',
  };
  const sourceIcons: Record<string, string> = {
    ideas: '💡',
    doxa: '📜',
    handoff: '🤝',
    ki: '📚',
  };

  const barsHtml = sourceEntries.map(([key, val]) => {
    const count = typeof val === 'object' ? (val as any).count ?? 0 : 0;
    const pct = Math.round((count / maxCount) * 100);
    const color = sourceColors[key] ?? 'var(--text-secondary)';
    const icon = sourceIcons[key] ?? '📄';
    return `
      <div style="margin-bottom:0.5rem;">
        <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:0.15rem;">
          <span>${icon} ${esc(key)}</span>
          <span style="color:${color}; font-weight:600;">${count}</span>
        </div>
        <div class="quota-bar">
          <div class="quota-bar-fill" style="width:${pct}%; background:${color}"></div>
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="card" style="margin-top:1rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
        <span class="metric-label">🌉 Gateway ソース</span>
        <span style="color:var(--text-secondary); font-size:0.8rem;">
          合計 <strong>${stats.total_files}</strong> ファイル${timeStr ? ` · ${esc(timeStr)}` : ''}
        </span>
      </div>
      ${barsHtml}
    </div>
  `;
}

function renderSentinelCard(data: SentinelLatest | null): string {
  if (!data || data.status === 'no_data') {
    return `
      <div class="card" style="margin-top:1rem;">
        <div class="metric-label">🔭 Paper Sentinel</div>
        <div style="color:var(--text-secondary); font-size:0.85rem; padding:0.5rem 0;">
          Sentinel 未実行 — 6時間毎に自動スキャン
        </div>
      </div>
    `;
  }

  const timeStr = data.timestamp
    ? (() => {
      try {
        const d = new Date(data.timestamp);
        return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
      } catch { return data.timestamp; }
    })()
    : '';

  const topicsStr = (data.topics || []).join(', ');
  const papers = (data.topPapers || []).slice(0, 5);

  const papersHtml = papers.map((p: SentinelPaper) => {
    const scoreWidth = Math.round((p.score || 0) * 100);
    const scoreColor = (p.score || 0) >= 0.7 ? 'var(--success-color, #22c55e)'
      : (p.score || 0) >= 0.4 ? 'var(--warning-color, #eab308)'
        : 'var(--text-secondary)';
    return `
      <div class="digest-candidate">
        <div class="digest-candidate-header">
          <span class="digest-candidate-title">${esc(p.title)}</span>
          <span class="digest-candidate-score" style="color:${scoreColor}">${(p.score || 0).toFixed(2)}</span>
        </div>
        <div class="quota-bar" style="margin:0.2rem 0;">
          <div class="quota-bar-fill" style="width:${scoreWidth}%; background:${scoreColor}"></div>
        </div>
        <div class="digest-candidate-meta">
          <span class="digest-source">${esc(p.topic)}</span>
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="card" style="margin-top:1rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
        <span class="metric-label">🔭 Paper Sentinel</span>
        <span style="color:var(--text-secondary); font-size:0.8rem;">
          ${data.totalPapers}件発見
          <span class="digest-timestamp">${esc(timeStr)}</span>
        </span>
      </div>
      <div style="color:var(--text-secondary); font-size:0.75rem; margin-bottom:0.5rem;">
        📡 ${esc(topicsStr)}
      </div>
      ${papersHtml}
    </div>
  `;
}

function renderEpistemicCard(data: EpistemicHealthResponse | null): string {
  if (!data || data.details === 'Registry not found') {
    return `
      <div class="card" style="margin-top:1rem;">
        <div class="metric-label">🧬 Epistemic Health</div>
        <div style="color:var(--text-secondary); font-size:0.85rem; padding:0.5rem 0;">
          epistemic_status.yaml 未検出
        </div>
      </div>
    `;
  }

  const gradeColor: Record<string, string> = {
    A: 'var(--success-color, #22c55e)',
    B: 'var(--info-color, #3b82f6)',
    C: 'var(--warning-color, #eab308)',
    D: 'var(--error-color, #ef4444)',
  };
  const color = gradeColor[data.grade] ?? 'var(--text-secondary)';
  const scorePct = Math.round(data.score);
  const falsifPct = Math.round(data.falsification_coverage);

  return `
    <div class="card" style="margin-top:1rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
        <span class="metric-label">🧬 Epistemic Health</span>
        <span style="font-size:1.5rem; font-weight:700; color:${color};">${esc(data.grade)}</span>
      </div>
      <div style="display:flex; gap:1.5rem; margin-bottom:0.5rem;">
        <div style="flex:1;">
          <div style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:0.15rem;">健全性スコア</div>
          <div class="quota-bar">
            <div class="quota-bar-fill" style="width:${scorePct}%; background:${color}"></div>
          </div>
          <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:0.1rem;">${data.score}/100</div>
        </div>
        <div style="flex:1;">
          <div style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:0.15rem;">反証カバレッジ</div>
          <div class="quota-bar">
            <div class="quota-bar-fill" style="width:${falsifPct}%; background:var(--accent-color, #a855f7)"></div>
          </div>
          <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:0.1rem;">${data.falsification_coverage}%</div>
        </div>
      </div>
      <div style="color:var(--text-secondary); font-size:0.8rem;">
        📊 ${data.total_patches} パッチ登録済み
      </div>
    </div>
  `;
}


function renderBasanosL2Card(data: BasanosL2ScanResponse | null): string {
  if (!data || data.error) {
    return `
      <div class="card" style="margin-top:1rem;">
        <div class="metric-label">🔍 Basanos L2</div>
        <div style="color:var(--text-secondary); font-size:0.85rem; padding:0.5rem 0;">
          ${data?.error ? esc(data.error) : 'L2 構造スキャン未実行'}
        </div>
      </div>
    `;
  }

  const statusIcon: Record<string, string> = { ok: '✅', warn: '⚠️', error: '🔴' };
  const statusColor: Record<string, string> = {
    ok: 'var(--success-color, #22c55e)',
    warn: 'var(--warning-color, #eab308)',
    error: 'var(--error-color, #ef4444)',
  };
  const typeLabels: Record<string, string> = {
    eta: 'η 未吸収',
    'epsilon-impl': 'ε 未実装',
    'epsilon-just': 'ε 根拠なし',
    delta: 'Δε/Δt 変更不整合',
  };
  const typeColors: Record<string, string> = {
    eta: 'var(--info-color, #3b82f6)',
    'epsilon-impl': 'var(--warning-color, #eab308)',
    'epsilon-just': 'var(--accent-color, #a855f7)',
    delta: 'var(--quota-orange, #f97316)',
  };

  const maxCount = Math.max(...Object.values(data.by_type), 1);
  const barsHtml = Object.entries(data.by_type).map(([key, count]) => {
    const pct = Math.round((count / maxCount) * 100);
    const color = typeColors[key] ?? 'var(--text-secondary)';
    const label = typeLabels[key] ?? key;
    return `
      <div style="margin-bottom:0.4rem;">
        <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:0.1rem;">
          <span>${esc(label)}</span>
          <span style="color:${color}; font-weight:600;">${count}</span>
        </div>
        <div class="quota-bar">
          <div class="quota-bar-fill" style="width:${pct}%; background:${color}"></div>
        </div>
      </div>
    `;
  }).join('');

  const deficitsHtml = data.top_deficits.slice(0, 3).map(d => `
    <div style="padding:0.3rem 0; border-bottom:1px solid var(--border-color); font-size:0.8rem;">
      <div style="display:flex; justify-content:space-between;">
        <span style="color:var(--text-primary);">${esc(d.target)}</span>
        <span style="color:${d.severity >= 0.7 ? 'var(--error-color)' : 'var(--text-secondary)'}; font-size:0.75rem;">${d.severity.toFixed(1)}</span>
      </div>
      <div style="color:var(--text-secondary); font-size:0.75rem;">${esc(d.description).slice(0, 80)}</div>
    </div>
  `).join('');

  return `
    <div class="card" style="margin-top:1rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
        <span class="metric-label">🔍 Basanos L2</span>
        <span style="font-size:1.1rem; font-weight:700; color:${statusColor[data.status] ?? ''}">
          ${statusIcon[data.status] ?? ''} ${data.total}件
        </span>
      </div>
      ${barsHtml}
      ${deficitsHtml ? `<div style="margin-top:0.5rem;">${deficitsHtml}</div>` : ''}
    </div>
  `;
}

function renderBasanosL2HistoryCard(
  history: BasanosL2HistoryResponse | null,
  trend: BasanosL2TrendResponse | null,
): string {
  if (!history && !trend) return '';

  const directionIcon: Record<string, string> = {
    improving: '📉',
    worsening: '📈',
    stable: '➡️',
  };
  const directionLabel: Record<string, string> = {
    improving: '改善傾向',
    worsening: '悪化傾向',
    stable: '安定',
  };
  const directionColor: Record<string, string> = {
    improving: 'var(--clr-green, #4caf50)',
    worsening: 'var(--clr-red, #f44336)',
    stable: 'var(--clr-yellow, #ffc107)',
  };

  const dir = trend?.direction ?? 'unknown';
  const trendHtml = trend ? `
    <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.75rem;">
      <span style="font-size:1.5rem;">${directionIcon[dir] ?? '❓'}</span>
      <div>
        <div style="font-weight:700; color:${directionColor[dir] ?? ''}">${directionLabel[dir] ?? dir}</div>
        <div style="font-size:0.8rem; opacity:0.7;">
          現在 ${trend.current}件 · 前回 ${trend.previous}件 · Δ${trend.delta >= 0 ? '+' : ''}${trend.delta}
        </div>
      </div>
      <div style="font-family:monospace; font-size:1.2rem; letter-spacing:2px; margin-left:auto;">
        ${esc(trend.sparkline)}
      </div>
    </div>
  ` : '';

  const records = history?.records ?? [];
  const historyRows = records.slice(0, 8).map(r => {
    const ts = r.timestamp?.slice(0, 16).replace('T', ' ') ?? '?';
    const total = r.total ?? 0;
    const color = total === 0 ? 'var(--clr-green, #4caf50)'
      : total <= 5 ? 'var(--clr-yellow, #ffc107)'
        : 'var(--clr-red, #f44336)';
    const types = Object.entries(r.by_type ?? {}).map(([k, v]) => `${k}:${v}`).join(' ') || '—';
    return `<tr>
      <td style="opacity:0.6; font-size:0.8rem;">${esc(ts)}</td>
      <td style="font-weight:700; color:${color}; text-align:right;">${total}</td>
      <td style="font-size:0.8rem; opacity:0.7;">${esc(types)}</td>
    </tr>`;
  }).join('');

  return `
    <div class="card card-fade" style="grid-column: span 1;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
        <span class="metric-label">📊 Deficit 履歴</span>
        <span style="font-size:0.8rem; opacity:0.6;">直近 ${records.length} 件</span>
      </div>
      ${trendHtml}
      ${records.length > 0 ? `
        <table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
          <thead>
            <tr style="opacity:0.5; font-size:0.75rem;">
              <th style="text-align:left;">日時</th>
              <th style="text-align:right;">件数</th>
              <th>内訳</th>
            </tr>
          </thead>
          <tbody>${historyRows}</tbody>
        </table>
      ` : '<div style="opacity:0.5; text-align:center; padding:1rem;">履歴なし</div>'}
    </div>
  `;
}

// ─── Scheduler Card ──────────────────────────────────────────

function renderSparkline(points: number[], width = 200, height = 40): string {
  if (points.length < 2) return '';
  const max = Math.max(...points, 100);
  const min = Math.min(...points, 0);
  const range = max - min || 1;
  const step = width / (points.length - 1);
  const coords = points.map((v, i) => {
    const x = i * step;
    const y = height - ((v - min) / range) * height;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const path = `M ${coords.join(' L ')}`;
  // 90% threshold line
  const thresholdY = (height - ((90 - min) / range) * height).toFixed(1);
  return `
    <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" style="overflow:visible;">
      <line x1="0" y1="${thresholdY}" x2="${width}" y2="${thresholdY}" stroke="var(--success-color, #22c55e)" stroke-width="0.5" stroke-dasharray="3 2" opacity="0.5"/>
      <path d="${path}" fill="none" stroke="var(--accent-color, #38bdf8)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="${coords[coords.length - 1]!.split(',')[0]}" cy="${coords[coords.length - 1]!.split(',')[1]}" r="2.5" fill="var(--accent-color, #38bdf8)"/>
    </svg>
  `;
}

function renderSchedulerCard(
  data: SchedulerStatusResponse | null,
  trend: SchedulerTrendResponse | null = null,
  evolution: SchedulerEvolutionResponse | null = null,
  rotation: SchedulerRotationResponse | null = null,
): string {
  if (!data || data.status === 'no_data') return '';

  const summary = data.summary;
  if (!summary) return '';

  const statusIcon: Record<string, string> = { ok: '🟢', warn: '🟡', error: '🔴' };
  const statusColor: Record<string, string> = {
    ok: 'var(--success-color, #22c55e)',
    warn: 'var(--warning-color, #eab308)',
    error: 'var(--error-color, #ef4444)',
  };
  const icon = statusIcon[summary.status] ?? '⚪';
  const color = statusColor[summary.status] ?? 'var(--text-secondary)';

  const ratePct = Math.round(summary.success_rate);

  const modesHtml = Object.entries(summary.modes).map(([mode, count]) =>
    `<span style="background:var(--bg-secondary); padding:0.15rem 0.5rem; border-radius:0.25rem; font-size:0.75rem;">${esc(mode)} ×${count}</span>`
  ).join(' ');

  const runsHtml = data.runs.slice(0, 3).map((r: SchedulerRun) => {
    const runStatus = r.total_failed === 0 ? '🟢' : r.total_failed <= 2 ? '🟡' : '🔴';
    const ts = r.timestamp ? relativeTime(r.timestamp) : r.filename;
    return `
      <div style="display:flex; justify-content:space-between; align-items:center; padding:0.3rem 0; border-bottom:1px solid var(--border-color);">
        <div style="display:flex; gap:0.5rem; align-items:center;">
          <span>${runStatus}</span>
          <span style="font-size:0.8rem;">${esc(r.slot || 'N/A')}</span>
          <span style="font-size:0.7rem; opacity:0.6;">${esc(ts)}</span>
        </div>
        <div style="font-size:0.75rem; color:var(--text-secondary);">
          ${r.files_reviewed}件 / ${esc(r.mode)}${r.dynamic ? ' ⚡' : ''}
        </div>
      </div>
    `;
  }).join('');

  // Sparkline from trend data
  let sparklineHtml = '';
  if (trend?.trend && trend.trend.length >= 2) {
    const rates = trend.trend.map((t: { success_rate: number }) => t.success_rate);
    sparklineHtml = `
      <div style="margin-top:0.5rem; padding-top:0.5rem; border-top:1px solid var(--border-color);">
        <div style="font-size:0.7rem; color:var(--text-secondary); margin-bottom:0.25rem;">📈 14日間 成功率推移</div>
        ${renderSparkline(rates, 280, 36)}
      </div>
    `;
  }

  // F19: Evolution proposals section
  let evolutionHtml = '';
  if (evolution && evolution.proposals && evolution.proposals.length > 0) {
    const items = evolution.proposals.slice(0, 3).map(p =>
      `<div style="display:flex; justify-content:space-between; padding:0.2rem 0; font-size:0.75rem;">
        <span>🧬 ${esc(p.domain)} / ${esc(p.axis)}</span>
        <span style="opacity:0.6;">${Math.round(p.usefulness_rate * 100)}%</span>
      </div>`
    ).join('');
    evolutionHtml = `
      <div style="margin-top:0.5rem; padding-top:0.5rem; border-top:1px solid var(--border-color);">
        <div style="font-size:0.7rem; color:var(--text-secondary); margin-bottom:0.25rem;">🔬 進化提案 (${evolution.total_proposals}件)</div>
        ${items}
      </div>
    `;
  }

  // F19: Rotation comparison section
  let rotationHtml = '';
  if (rotation?.rotation) {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const dayLabels: Record<string, string> = { Mon: '月', Tue: '火', Wed: '水', Thu: '木', Fri: '金', Sat: '土', Sun: '日' };
    const cells = days.map(d => {
      const r = rotation.rotation[d] as RotationDay | undefined;
      if (!r) return '';
      const isAdapted = r.static !== r.adaptive;
      const badge = isAdapted ? '⚡' : '';
      return `<span style="font-size:0.7rem; padding:0.1rem 0.3rem; border-radius:0.2rem; background:${isAdapted ? 'var(--accent-bg, rgba(99,102,241,0.15))' : 'var(--bg-secondary)'}">${dayLabels[d]}:${esc(r.adaptive)}${badge}</span>`;
    }).join(' ');
    rotationHtml = `
      <div style="margin-top:0.5rem; padding-top:0.5rem; border-top:1px solid var(--border-color);">
        <div style="font-size:0.7rem; color:var(--text-secondary); margin-bottom:0.25rem;">📅 今週のローテーション ${rotation.total_data_points > 0 ? '(適応)' : '(静的)'}</div>
        <div style="display:flex; flex-wrap:wrap; gap:0.25rem;">${cells}</div>
      </div>
    `;
  }

  return `
    <div class="card card-fade" style="margin-top:1rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
        <span class="metric-label">🗓️ Jules Scheduler</span>
        <span style="font-size:1.2rem; font-weight:700; color:${color}">${icon} ${ratePct}%</span>
      </div>
      <div style="margin-bottom:0.5rem;">
        <div style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:0.15rem;">成功率</div>
        <div class="quota-bar">
          <div class="quota-bar-fill" style="width:${ratePct}%; background:${color}"></div>
        </div>
      </div>
      <div style="display:flex; gap:1rem; margin-bottom:0.5rem; font-size:0.8rem; color:var(--text-secondary);">
        <span>📁 ${summary.total_files_reviewed} ファイル</span>
        <span>🚀 ${summary.total_started} タスク</span>
        <span>❌ ${summary.total_failed} 失敗</span>
      </div>
      <div style="margin-bottom:0.5rem;">${modesHtml}</div>
      ${runsHtml}
      ${sparklineHtml}
      ${evolutionHtml}
      ${rotationHtml}
    </div>
  `;
}


function renderTheoremCard(data: TheoremUsageResponse | null): string {
  if (!data) {
    return `
      <div class="card" style="margin-top:1rem;">
        <div class="metric-label">📐 Theorem Activity</div>
        <div style="color:var(--text-secondary); font-size:0.85rem; padding:0.5rem 0;">
          定理使用データなし
        </div>
      </div>
    `;
  }

  const ratePct = Math.round(data.usage_rate);
  const rateColor = ratePct >= 60 ? 'var(--success-color, #22c55e)'
    : ratePct >= 30 ? 'var(--warning-color, #eab308)'
      : 'var(--error-color, #ef4444)';

  // Series bars — 6 Series を横棒で
  const seriesOrder = ['O', 'S', 'H', 'P', 'K', 'A'];
  const maxUsage = Math.max(1, ...Object.values(data.series).map(s => s.total_usage));
  const seriesBarsHtml = seriesOrder.map(key => {
    const s = data.series[key];
    if (!s) return '';
    const barW = Math.round((s.total_usage / maxUsage) * 100);
    const usedCount = s.theorems.filter(t => t.usage_count > 0).length;
    return `
      <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.25rem;">
        <span style="width:3rem; font-size:0.75rem; color:var(--text-secondary); text-align:right;">${esc(key)}-${esc(s.name.slice(0, 3))}</span>
        <div style="flex:1; height:0.5rem; background:var(--bg-tertiary, #333); border-radius:0.25rem; overflow:hidden;">
          <div style="width:${barW}%; height:100%; background:${s.color}; border-radius:0.25rem; transition: width 0.5s ease;"></div>
        </div>
        <span style="width:3rem; font-size:0.7rem; color:var(--text-secondary);">${usedCount}/4</span>
      </div>
    `;
  }).join('');

  // Most used top 3
  const topHtml = data.most_used.slice(0, 3).filter(m => m.count > 0).map(m =>
    `<span style="display:inline-block; padding:0.1rem 0.4rem; background:var(--bg-tertiary, #333); border-radius:0.25rem; font-size:0.7rem; margin-right:0.25rem;">${esc(m.theorem_id)} ×${m.count}</span>`
  ).join('');

  return `
    <div class="card" style="margin-top:1rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
        <span class="metric-label">📐 Theorem Activity</span>
        <span style="font-size:1.25rem; font-weight:700; color:${rateColor};">${ratePct}%</span>
      </div>
      <div style="display:flex; gap:1.5rem; margin-bottom:0.75rem;">
        <div style="flex:1;">
          <div style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:0.15rem;">使用率 (${24 - data.unused_count}/24)</div>
          <div class="quota-bar">
            <div class="quota-bar-fill" style="width:${ratePct}%; background:${rateColor}"></div>
          </div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:0.8rem; color:var(--text-secondary);">使用回数</div>
          <div style="font-size:1.1rem; font-weight:600;">${data.total_usage}</div>
        </div>
      </div>
      <div style="margin-bottom:0.5rem;">
        ${seriesBarsHtml}
      </div>
      ${topHtml ? `<div style="margin-top:0.25rem;">${topHtml}</div>` : ''}
    </div>
  `;
}

function renderWALCard(data: WALStatusResponse | null): string {
  if (!data || data.total_wals === 0) return '';

  const activeColor = data.active_wals > 0 ? 'var(--accent-primary, #6366f1)' : 'var(--text-secondary)';
  const activeIcon = data.active_wals > 0 ? '🟢' : '⚪';

  let latestHtml = '';
  if (data.latest) {
    const progressItems = data.latest.progress.slice(-3).map(p =>
      `<div style="font-size:0.7rem; padding:0.15rem 0; color:var(--text-secondary);">• ${esc(p)}</div>`
    ).join('');
    latestHtml = `
      <div style="margin-top:0.5rem; padding-top:0.5rem; border-top:1px solid var(--border-color);">
        <div style="font-size:0.75rem; font-weight:500; margin-bottom:0.25rem;">${esc(data.latest.goal)}</div>
        <div style="display:flex; gap:0.5rem; font-size:0.7rem; color:var(--text-secondary); margin-bottom:0.25rem;">
          <span>${esc(data.latest.status)}</span>
          <span>•</span>
          <span>${relativeTime(data.latest.created)}</span>
        </div>
        ${progressItems}
      </div>
    `;
  }

  let recentHtml = '';
  const otherRecent = data.recent.filter(r => r.filename !== data.latest?.filename).slice(0, 2);
  if (otherRecent.length > 0) {
    const items = otherRecent.map(r =>
      `<div style="display:flex; justify-content:space-between; padding:0.15rem 0; font-size:0.7rem;">
        <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:70%;">${esc(r.goal)}</span>
        <span style="color:var(--text-secondary);">${esc(r.status)}</span>
      </div>`
    ).join('');
    recentHtml = `
      <div style="margin-top:0.5rem; padding-top:0.5rem; border-top:1px solid var(--border-color);">
        <div style="font-size:0.7rem; color:var(--text-secondary); margin-bottom:0.25rem;">Recent</div>
        ${items}
      </div>
    `;
  }

  return `
    <div class="card card-fade" style="margin-top:1rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
        <div style="font-weight:600;">📋 Intent-WAL</div>
        <div style="font-size:0.75rem; color:var(--text-secondary);">${data.total_wals} total</div>
      </div>
      <div style="display:flex; gap:1.5rem; margin-bottom:0.5rem;">
        <div style="text-align:center;">
          <div style="font-size:0.8rem; color:var(--text-secondary);">アクティブ</div>
          <div style="font-size:1.3rem; font-weight:700; color:${activeColor};">${activeIcon} ${data.active_wals}</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:0.8rem; color:var(--text-secondary);">累計</div>
          <div style="font-size:1.1rem; font-weight:600;">${data.total_wals}</div>
        </div>
      </div>
      ${latestHtml}
      ${recentHtml}
    </div>
  `;
}
