/**
 * Route Configuration — Single Source of Truth
 *
 * index.html のナビと main.ts のルーティングを統一する設定。
 * ルート追加・変更はここだけで完結する。
 */

import { renderDashboard } from './views/dashboard';
import { renderOrchestratorView } from './views/orchestrator';
import { renderAgentManagerView } from './views/agent-manager';
import { renderSearch } from './views/search';
import { renderFep } from './views/fep';
import { renderGnosis } from './views/gnosis';
import { renderQuality } from './views/quality';
import { renderPostcheck } from './views/postcheck';
// Three.js graph — lazy loaded to split the 700KB+ chunk
const renderGraph3D = async () => {
    const { renderGraph3D: render } = await import('./views/graph3d');
    await render();
};
import { renderNotifications } from './views/notifications';
import { renderPKS } from './views/pks';
import { renderSophiaView } from './views/sophia';
import { renderTimelineView } from './views/timeline';
import { renderSynteleiaView } from './views/synteleia';
import { renderSynedrionView } from './views/synedrion';
import { renderDigestorView } from './views/digestor';
import { renderDesktopDomView } from './views/desktop-dom';
import { renderChatView } from './views/chat';
import { renderAristosView } from './views/aristos';
import { renderDevToolsView } from './views/devtools';
import { renderJulesView } from './views/jules';
import { renderSettingsView } from './views/settings';
import { renderCoworkView } from './views/cowork';
import { renderNotesView } from './views/notes';

// ─── Types ───────────────────────────────────────────────────

export type ViewRenderer = () => Promise<void>;

export interface RouteConfig {
    key: string;
    label: string;
    icon: string;
    renderer: ViewRenderer;
}

// ─── Route Definitions ───────────────────────────────────────

export const ROUTES: RouteConfig[] = [
    { key: 'dashboard', label: 'Dashboard', icon: '📊', renderer: renderDashboard },
    { key: 'orchestrator', label: 'Orchestrator', icon: '🎯', renderer: renderOrchestratorView },
    { key: 'agents', label: 'Agents', icon: '🤖', renderer: renderAgentManagerView },
    { key: 'search', label: 'Search', icon: '🔍', renderer: renderSearch },
    { key: 'fep', label: 'FEP Agent', icon: '🧠', renderer: renderFep },
    { key: 'gnosis', label: 'Gnōsis', icon: '📖', renderer: renderGnosis },
    { key: 'quality', label: 'Quality', icon: '✅', renderer: renderQuality },
    { key: 'postcheck', label: 'Postcheck', icon: '🔄', renderer: renderPostcheck },
    { key: 'graph', label: 'Graph', icon: '🔮', renderer: renderGraph3D },
    { key: 'notifications', label: 'Notifications', icon: '🔔', renderer: renderNotifications },
    { key: 'pks', label: 'PKS', icon: '📡', renderer: renderPKS },
    { key: 'sophia', label: 'Sophia KI', icon: '📚', renderer: renderSophiaView },
    { key: 'timeline', label: 'Timeline', icon: '📅', renderer: renderTimelineView },
    { key: 'synteleia', label: 'Synteleia', icon: '🛡️', renderer: renderSynteleiaView },
    { key: 'synedrion', label: 'Synedrion', icon: '🔭', renderer: renderSynedrionView },
    { key: 'digestor', label: 'Digestor', icon: '🧬', renderer: renderDigestorView },
    { key: 'desktop', label: 'Desktop', icon: '🖥️', renderer: renderDesktopDomView },
    { key: 'chat', label: 'Chat', icon: '💬', renderer: renderChatView },
    { key: 'devtools', label: 'DevTools', icon: '🛠️', renderer: renderDevToolsView },
    { key: 'jules', label: 'Jules', icon: '⚡', renderer: renderJulesView },
    { key: 'cowork', label: 'Cowork', icon: '🤝', renderer: renderCoworkView },
    { key: 'aristos', label: 'Aristos', icon: '🧬', renderer: renderAristosView },
    { key: 'notes', label: 'Notes', icon: '📝', renderer: renderNotesView },
    { key: 'settings', label: 'Settings', icon: '⚙️', renderer: renderSettingsView },
];

// ─── Icon Groups (MECE 認知フロー) ───────────────────────────

export interface IconGroup {
    id: string;
    icon: string;
    label: string;
    routes: string[];
    desc: string;
}

export const ICON_GROUPS: IconGroup[] = [
    {
        id: 'dialogue',
        icon: 'η',          // eta: 自然変換の単位 = 入力・対話の始点
        label: '対話',
        routes: ['orchestrator', 'chat', 'agents', 'jules', 'cowork'],
        desc: 'AI との対話・指揮・エージェント操作・Jules・Cowork (入力層)',
    },
    {
        id: 'knowledge',
        icon: 'K',           // K-series (Kairos): 知識・文脈
        label: '知識',
        routes: ['search', 'notes', 'gnosis', 'sophia', 'digestor', 'fep'],
        desc: '知識検索・論文・KI・消化・FEP理論 (記憶層)',
    },
    {
        id: 'judgement',
        icon: 'Δ',           // Delta-layer: 判断・批評
        label: '判断',
        routes: ['quality', 'postcheck', 'synteleia', 'synedrion', 'aristos'],
        desc: '品質検証・監査・判定 (処理層)',
    },
    {
        id: 'output',
        icon: 'ε',           // epsilon: 余単位 = 射出・具現化
        label: '可視化',
        routes: ['dashboard', 'graph', 'timeline'],
        desc: 'ダッシュボード・グラフ・タイムライン (出力層)',
    },
    {
        id: 'system',
        icon: 'Ω',           // Omega-layer: 全体統御
        label: '運用',
        routes: ['notifications', 'pks', 'devtools', 'desktop', 'settings'],
        desc: '通知・インフラ・DevTools・設定 (管理層)',
    },
];

// ─── Derived Maps ────────────────────────────────────────────

/** Route key → renderer lookup (for navigate()) */
export const ROUTE_MAP: Record<string, ViewRenderer> =
    Object.fromEntries(ROUTES.map(r => [r.key, r.renderer]));

/** Default route */
export const DEFAULT_ROUTE = 'chat';
