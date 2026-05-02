import './css/aristos.css';
import { esc } from '../utils';

// --- Types ---
interface AristosTheorem {
  theorem: string;
  scalar: number;
  generation: number;
  weights: Record<string, number>;
  depth: number;
  precision: number;
  efficiency: number;
  novelty: number;
}

interface AristosStatusResponse {
  has_weights: boolean;
  has_feedback: boolean;
  total_weights: number;
  total_theorems: number;
  total_feedback: number;
  theorems: AristosTheorem[];
}

// --- Series color map ---
const SERIES_COLORS: Record<string, string> = {
  O: '#e6b422',  // Gold
  S: '#1e90ff',  // Blue
  H: '#ff6347',  // Red
  P: '#2ecc71',  // Green
  K: '#9b59b6',  // Purple
  A: '#e67e22',  // Orange
};

function getSeriesColor(theorem: string): string {
  const key = theorem[0] ?? '';
  return SERIES_COLORS[key] || '#8b949e';
}

function renderFitnessBar(value: number, label: string, color: string): string {
  const pct = Math.min(Math.max(value * 100, 0), 100);
  return `
    <div class="ar-fitness-row">
      <span class="ar-fitness-label">${esc(label)}</span>
      <div class="ar-fitness-track">
        <div class="ar-fitness-fill" style="width:${pct}%;background:${color}"></div>
      </div>
      <span class="ar-fitness-value">${value.toFixed(3)}</span>
    </div>`;
}

function renderTheoremCard(th: AristosTheorem): string {
  const color = getSeriesColor(th.theorem);
  const weightEntries = Object.entries(th.weights);

  return `
    <div class="card ar-theorem-card" style="border-left:3px solid ${color}">
      <div class="ar-theorem-header">
        <span class="ar-theorem-name" style="color:${color}">${esc(th.theorem)}</span>
        <span class="ar-theorem-scalar">fitness: ${th.scalar.toFixed(3)}</span>
        <span class="ar-theorem-gen">Gen ${th.generation}</span>
      </div>
      <div class="ar-fitness-bars">
        ${renderFitnessBar(th.depth, 'Depth', '#6366f1')}
        ${renderFitnessBar(th.precision, 'Precision', '#22d3ee')}
        ${renderFitnessBar(th.efficiency, 'Efficiency', '#10b981')}
        ${renderFitnessBar(th.novelty, 'Novelty', '#f59e0b')}
      </div>
      ${weightEntries.length > 0 ? `
      <details class="ar-weights-detail">
        <summary>重み (${weightEntries.length})</summary>
        <div class="ar-weights-grid">
          ${weightEntries.map(([k, v]) => `<span class="ar-weight-item">${esc(k)}: ${v.toFixed(4)}</span>`).join('')}
        </div>
      </details>` : ''}
    </div>`;
}

export async function renderAristosView(): Promise<void> {
  const app = document.getElementById('view-content')!;
  app.innerHTML = '<div class="loading">Aristos L2 読み込み中...</div>';

  try {
    let data: AristosStatusResponse;
    if (window.__TAURI_INTERNALS__) {
      const { invoke } = await import('@tauri-apps/api/core');
      data = await invoke('api_proxy', { request: { path: '/api/aristos/status' } });
    } else {
      const res = await fetch('/api/aristos/status');
      if (!res.ok) throw new Error(`API Error: ${res.status}`);
      data = await res.json();
    }

    if (!data.has_weights) {
      app.innerHTML = `
        <h1>🧬 Aristos L2 Evolution</h1>
        <div class="card">
          <p>進化済み重みが見つかりません。</p>
          <p style="color:#8b949e;">evolve_cli.py --all --gen 50 を実行してください。</p>
        </div>`;
      return;
    }

    // Group by series
    const bySeries: Record<string, AristosTheorem[]> = {};
    for (const th of data.theorems) {
      const s = th.theorem[0] ?? '?';
      (bySeries[s] ??= []).push(th);
    }

    const seriesNames: Record<string, string> = {
      O: 'Ousia (本質)', S: 'Schema (様態)', H: 'Hormē (傾向)',
      P: 'Perigraphē (条件)', K: 'Kairos (文脈)', A: 'Akribeia (精密)',
    };

    const seriesSections = Object.entries(bySeries)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([series, theorems]) => `
        <div class="ar-series-section">
          <h2 style="color:${getSeriesColor(series)}">${series}-Series — ${esc(seriesNames[series] || series)}</h2>
          ${theorems.map(renderTheoremCard).join('')}
        </div>`).join('');

    app.innerHTML = `
      <h1>🧬 Aristos L2 Evolution</h1>
      <div class="grid" style="margin-bottom:1rem;">
        <div class="card">
          <h3>定理数</h3>
          <div class="metric">${data.total_theorems}</div>
        </div>
        <div class="card">
          <h3>重みパラメータ</h3>
          <div class="metric">${data.total_weights}</div>
        </div>
        <div class="card">
          <h3>フィードバック</h3>
          <div class="metric">${data.total_feedback}</div>
          <p>${data.has_feedback ? '✅ 蓄積済み' : '⚠️ 未収集'}</p>
        </div>
      </div>
      ${seriesSections}
    `;

  } catch (e) {
    app.innerHTML = `<div class="card status-error">Aristos エラー: ${esc((e as Error).message)}</div>`;
  }
}
