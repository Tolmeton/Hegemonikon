import type { paths, components } from '../api-types';
// ─── ConnectionState — LifecycleEpoch パターン (from ClawX adjoint) ────────
// 接続の健全性を追跡し、race condition を防止する。
// epoch カウンタにより、古い操作 (再起動前のリクエスト等) を即座に無効化できる。

export interface ConnectionStatus {
    state: 'connected' | 'reconnecting' | 'error';
    epoch: number;
    consecutiveErrors: number;
    lastSuccessAt: number;
    lastProbeAt: number;  // Recovery probe の最終送信時刻 (P0: レート制限)
    lastErrorMessage: string | null;
}

const _connState: ConnectionStatus = {
    state: 'connected',
    epoch: 0,
    consecutiveErrors: 0,
    lastSuccessAt: Date.now(),
    lastProbeAt: 0,
    lastErrorMessage: null,
};

const MAX_CONSECUTIVE_ERRORS = 3;
const RECOVERY_PROBE_MS = 10_000;  // Recovery probe 間隔
const ERROR_DEBOUNCE_MS = 2_000;   // P1a: recordError の通知 debounce
const _listeners: Array<(status: ConnectionStatus) => void> = [];
let _errorDebounceTimer: ReturnType<typeof setTimeout> | null = null;

/** LifecycleEpoch をインクリメント。古い操作を無効化する。 */
export function bumpEpoch(reason: string): number {
    _connState.epoch = (_connState.epoch + 1) % Number.MAX_SAFE_INTEGER;
    _connState.consecutiveErrors = 0;
    _connState.state = 'reconnecting';
    _connState.lastErrorMessage = null;
    console.debug(`[ConnectionState] epoch=${_connState.epoch} (${reason})`);
    _notifyListeners();
    return _connState.epoch;
}

/** 指定 epoch が現在の epoch と一致するか (古い操作の検出) */
export function isSuperseded(expectedEpoch: number): boolean {
    return expectedEpoch !== _connState.epoch;
}

/** API 呼び出し成功時に呼ぶ */
export function recordSuccess(): void {
    _connState.consecutiveErrors = 0;
    _connState.lastSuccessAt = Date.now();
    if (_connState.state !== 'connected') {
        _connState.state = 'connected';
        _notifyListeners();
    }
}

/** API 呼び出し失敗時に呼ぶ (P1a: debounced notification) */
export function recordError(message: string): void {
    _connState.consecutiveErrors++;
    _connState.lastErrorMessage = message;
    if (_connState.consecutiveErrors >= MAX_CONSECUTIVE_ERRORS && _connState.state !== 'error') {
        // Debounce: 2 秒以内の連続エラーは 1 回の通知にまとめる
        if (_errorDebounceTimer) clearTimeout(_errorDebounceTimer);
        _errorDebounceTimer = setTimeout(() => {
            _errorDebounceTimer = null;
            if (_connState.consecutiveErrors >= MAX_CONSECUTIVE_ERRORS && _connState.state !== 'error') {
                _connState.state = 'error';
                console.warn(`[ConnectionState] ${MAX_CONSECUTIVE_ERRORS} 連続エラー → error 状態に遷移: ${message}`);
                _notifyListeners();
            }
        }, ERROR_DEBOUNCE_MS);
    }
}

/** 接続状態の購読 */
export function onConnectionChange(listener: (status: ConnectionStatus) => void): () => void {
    _listeners.push(listener);
    return () => { const idx = _listeners.indexOf(listener); if (idx >= 0) _listeners.splice(idx, 1); };
}

/** 現在の接続状態を取得 */
export function getConnectionStatus(): Readonly<ConnectionStatus> {
    return { ..._connState };
}

function _notifyListeners(): void {
    const snapshot = { ..._connState };
    for (const fn of _listeners) { try { fn(snapshot); } catch { /* ignore */ } }
}

// API ベース URL: Vite の環境変数 VITE_API_BASE があれば優先、なければ相対パス (Vite プロキシ経由)
const API_BASE = import.meta.env.VITE_API_BASE || '';

// Tauri 環境判定: __TAURI_INTERNALS__ 存在時のみ Tauri fetch を使用
let resolvedFetch: typeof globalThis.fetch | null = null;

async function getFetch(): Promise<typeof globalThis.fetch> {
    if (resolvedFetch) return resolvedFetch;
    if ((window as any).__TAURI_INTERNALS__) {
        try {
            const mod = await import('@tauri-apps/plugin-http');
            resolvedFetch = mod.fetch as unknown as typeof globalThis.fetch;
        } catch {
            resolvedFetch = globalThis.fetch;
        }
    } else {
        resolvedFetch = globalThis.fetch;
    }
    return resolvedFetch;
}

// Helper for type-safe fetch — Tauri 環境では invoke('api_proxy') 経由
async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
    // Circuit Breaker: 連続エラー状態では新規リクエストを即座に拒否
    // ただし最終成功から RECOVERY_PROBE_MS 経過後は 1 リクエストだけ通す (回復 probe)
    if (_connState.state === 'error') {
        const now = Date.now();
        const sinceLastSuccess = now - _connState.lastSuccessAt;
        const sinceLastProbe = now - _connState.lastProbeAt;
        // P0: lastSuccessAt と lastProbeAt の両方から RECOVERY_PROBE_MS 経過していなければ reject
        if (sinceLastSuccess < RECOVERY_PROBE_MS || sinceLastProbe < RECOVERY_PROBE_MS) {
            throw new Error(`API unreachable (${_connState.consecutiveErrors} consecutive errors). Last: ${_connState.lastErrorMessage}`);
        }
        // Recovery probe: 両方から 10秒経過 → 1リクエストだけ通す
        _connState.lastProbeAt = now;
        console.debug("[ConnectionState] Recovery probe — attempting request");
    }
    // Tauri IPC — HTTP を完全に排除
    if (window.__TAURI_INTERNALS__) {
        const { invoke } = await import("@tauri-apps/api/core");
        try {
            const result = await invoke("api_proxy", {
                request: {
                    path,
                    method: options?.method || "GET",
                    body: options?.body ? String(options.body) : null,
                }
            }) as T;
            recordSuccess();
            return result;
        } catch (e) {
            recordError(e instanceof Error ? e.message : String(e));
            throw e;
        }
    }
    const fetchFn = await getFetch();
    const response = await fetchFn(`${API_BASE}${path}`, options);
    if (!response.ok) {
        const errMsg = `API Error: ${response.status} ${response.statusText}`;
        recordError(errMsg);
        throw new Error(errMsg);
    }
    recordSuccess();
    return response.json() as Promise<T>;
}

// --- Exported Types ---
export type HealthCheckResponse = paths['/api/status/health']['get']['responses']['200']['content']['application/json'];
export type HealthReportResponse = paths['/api/status']['get']['responses']['200']['content']['application/json'];
export type FEPStateResponse = paths['/api/fep/state']['get']['responses']['200']['content']['application/json'];
export type FEPStepRequest = components['schemas']['FEPStepRequest'];
export type FEPStepResponse = paths['/api/fep/step']['post']['responses']['200']['content']['application/json'];
export type FEPDashboardResponse = paths['/api/fep/dashboard']['get']['responses']['200']['content']['application/json'];
export type GnosisStatsResponse = paths['/api/gnosis/stats']['get']['responses']['200']['content']['application/json'];
export type DendronReportResponse = paths['/api/dendron/report']['get']['responses']['200']['content']['application/json'];
export type PostcheckResponse = paths['/api/postcheck/run']['post']['responses']['200']['content']['application/json'];
export type SELListResponse = paths['/api/postcheck/list']['get']['responses']['200']['content']['application/json'];

// --- Timeline Types ---
export interface TimelineEvent {
    id: string;
    type: 'handoff' | 'doxa' | 'workflow' | 'kalon';
    title: string;
    date: string;
    summary: string;
    filename: string;
    size_bytes: number;
    mtime: string;
}
export interface TimelineEventsResponse {
    events: TimelineEvent[];
    total: number;
    offset: number;
    limit: number;
    has_more: boolean;
}
export interface TimelineEventDetail extends TimelineEvent {
    content: string;
}
export interface TimelineStatsResponse {
    total: number;
    by_type: { handoff: number; doxa: number; workflow: number; kalon: number };
    latest_handoff: string | null;
}

// --- Kalon Types ---
export interface KalonJudgeResponse {
    concept: string;
    verdict: string;
    label: string;
    g_test: boolean;
    f_test: boolean;
    timestamp: string;
    filename: string;
}
export interface KalonJudgment {
    concept: string;
    verdict: string;
    filename: string;
    mtime: string;
}
export interface KalonHistoryResponse {
    judgments: KalonJudgment[];
    total: number;
}

// --- Synteleia Types ---
export interface SynteleiaIssue {
    agent: string;
    code: string;
    severity: string;
    message: string;
    location?: string;
    suggestion?: string;
}
export interface SynteleiaAgentResult {
    agent_name: string;
    passed: boolean;
    confidence: number;
    issues: SynteleiaIssue[];
}
export interface SynteleiaAuditResponse {
    passed: boolean;
    summary: string;
    critical_count: number;
    high_count: number;
    total_issues: number;
    agent_results: SynteleiaAgentResult[];
    report: string;
    wbc_alerted: boolean;
}
export interface SynteleiaAgentInfo {
    name: string;
    description: string;
    layer: string;
}

// --- Synedrion Types ---
export interface SynedrionSweepIssue {
    perspective_id: string;
    domain: string;
    axis: string;
    severity: string;
    description: string;
    recommendation: string;
}
export interface SynedrionSweepResult {
    filepath: string;
    issue_count: number;
    issues: SynedrionSweepIssue[];
    severity: Record<string, number>;
    silences: number;
    errors: number;
    total_perspectives: number;
    coverage: number;
    elapsed_seconds: number;
}
export interface SynedrionPerspective {
    id: string;
    domain: string;
    axis: string;
    system_instruction: string;
}
export interface SynedrionCacheStats {
    total_entries: number;
    size_mb: number;
    hits: number;
    misses: number;
    hit_rate: number;
    oldest_age_hours: number;
    ttl_seconds: number;
    max_size_mb: number;
}
export interface SynedrionCacheClear {
    cleared: number;
    message: string;
}

// --- Digestor Types ---
export interface DigestorTopic {
    id: string;
    query: string;
    digest_to: string[];
    template_hint: string;
    description: string;
}
export interface DigestorTopicsResponse {
    topics: DigestorTopic[];
}
export interface SuccessResponse {
    success: boolean;
    message: string;
}

export interface ApproveRequest {
    title: string;
    source: string;
    url?: string;
    score: number;
    matched_topics: string[];
    rationale?: string;
}

export interface ApproveResponse {
    success: boolean;
    filename: string;
    message: string;
}

export interface DigestCandidate {
    title: string;
    source: string;
    url: string;
    score: number;
    matched_topics: string[];
    rationale: string;
    suggested_templates: Array<{ id: string; score: number }>;
}
export interface DigestReport {
    timestamp: string;
    source: string;
    total_papers: number;
    candidates_selected: number;
    dry_run: boolean;
    candidates: DigestCandidate[];
    filename: string;
}
export interface DigestReportListResponse {
    reports: DigestReport[];
    total: number;
}

// --- Sentinel Types ---
export interface SentinelPaper {
    title: string;
    score: number;
    topic: string;
    abstract: string;
}
export interface SentinelLatest {
    timestamp: string;
    topics: string[];
    totalPapers: number;
    highScorePapers: number;
    hasPapers: boolean;
    shouldAlert: boolean;
    topPapers: SentinelPaper[];
    status?: string;
    message?: string;
}

// --- Epistemic Types ---
export interface EpistemicPatch {
    id: string;
    claim: string;
    status: string;
    file: string;
    line: number;
    source: string;
    falsification: string;
    updated: string;
}
export interface EpistemicStatusResponse {
    total: number;
    summary: Record<string, number>;
    patches: EpistemicPatch[];
    status?: string;
}
export interface EpistemicHealthResponse {
    score: number;
    total_patches: number;
    falsification_coverage: number;
    grade: string;
    details?: string;
}

// --- Basanos L2 Types ---
export interface BasanosL2DeficitItem {
    type: string;
    severity: number;
    source: string;
    target: string;
    description: string;
    suggested_action: string;
}
export interface BasanosL2ScanResponse {
    total: number;
    by_type: Record<string, number>;
    top_deficits: BasanosL2DeficitItem[];
    status: string;
    error: string;
}

// --- Basanos L2 History/Trend Types ---
export interface BasanosL2HistoryRecord {
    timestamp: string;
    scan_type: string;
    total: number;
    by_type: Record<string, number>;
}
export interface BasanosL2HistoryResponse {
    records: BasanosL2HistoryRecord[];
    count: number;
}
export interface BasanosL2TrendResponse {
    direction: string;
    current: number;
    previous: number;
    delta: number;
    sparkline: string;
    window: number;
}

// --- Scheduler Types ---
export interface SchedulerRun {
    filename: string;
    timestamp: string;
    slot: string;
    mode: string;
    total_tasks: number;
    total_started: number;
    total_failed: number;
    files_reviewed: number;
    dynamic: boolean;
}
export interface SchedulerSummary {
    total_runs: number;
    total_files_reviewed: number;
    total_started: number;
    total_failed: number;
    success_rate: number;
    modes: Record<string, number>;
    status: string;
}
export interface SchedulerStatusResponse {
    status: string;
    runs: SchedulerRun[];
    summary: SchedulerSummary | null;
    message?: string;
}

// --- Scheduler Trend Types ---
export interface SchedulerTrendPoint {
    date: string;
    success_rate: number;
    runs: number;
    started: number;
    failed: number;
}
export interface SchedulerTrendResponse {
    trend: SchedulerTrendPoint[];
    days: number;
}

// --- Scheduler Analysis Types ---
export interface PerspectiveRank {
    perspective_id: string;
    domain: string;
    axis: string;
    total_reviews: number;
    useful_count: number;
    usefulness_rate: number;
    last_used: string;
}
export interface DomainAggregate {
    domain: string;
    perspectives: number;
    total_reviews: number;
    useful_count: number;
    usefulness_rate: number;
}
export interface AxisAggregate {
    axis: string;
    perspectives: number;
    total_reviews: number;
    useful_count: number;
    usefulness_rate: number;
}
export interface SchedulerAnalysisResponse {
    ranking: PerspectiveRank[];
    by_domain: DomainAggregate[];
    by_axis: AxisAggregate[];
    low_quality_ids?: string[];
    total_perspectives?: number;
    error?: string;
}
export interface EvolutionProposal {
    domain: string;
    axis: string;
    reason: string;
    usefulness_rate: number;
}
export interface SchedulerEvolutionResponse {
    proposals: EvolutionProposal[];
    applied: number;
    dry_run: boolean;
    total_proposals: number;
    error?: string;
}
export interface RotationDay {
    static: string;
    adaptive: string;
}
export interface SchedulerRotationResponse {
    mode_scores: Record<string, number>;
    total_data_points: number;
    window_days: number;
    rotation: Record<string, RotationDay>;
    error?: string;
}

// --- Theorem Usage Types ---
export interface TheoremInfo {
    id: string;
    name: string;
    command: string;
    question: string;
    usage_count: number;
}
export interface TheoremSeriesInfo {
    name: string;
    color: string;
    total_usage: number;
    theorems: TheoremInfo[];
}
export interface TheoremUsageResponse {
    total_usage: number;
    total_theorems: number;
    unused_count: number;
    usage_rate: number;
    series: Record<string, TheoremSeriesInfo>;
    most_used: Array<{ theorem_id: string; count: number }>;
}
export interface TheoremTodayResponse {
    suggestions: Array<{
        id: string;
        name: string;
        series: string;
        command: string;
        question: string;
        usage_count: number;
        prompt: string;
    }>;
}

// --- WAL Types ---
export interface WALEntry {
    filename: string;
    session_id: string;
    goal: string;
    status: string;
    progress: string[];
    created: string;
}
export interface WALStatusResponse {
    total_wals: number;
    active_wals: number;
    latest: WALEntry | null;
    recent: WALEntry[];
}

// --- IDE ConnectRPC Types ---
export interface IdeStatusResponse {
    status: string;
    pid?: string;
    port?: number;
    error?: string;
}
export interface IdeApiResponse {
    error?: string;
    [key: string]: unknown;
}


// --- Session Notes Types ---
export interface NoteChunkItem {
    path: string;
    content: string;
    turn_range: number[];
    metadata: Record<string, unknown>;
}
export interface NoteListItem {
    sessionId: string;
    project: string;
    date: string;
    title: string;
}
export interface NoteListResponse {
    items: NoteListItem[];
    total: number;
}
export interface NoteDetailResponse {
    sessionId: string;
    project: string;
    title: string;
    chunks: NoteChunkItem[];
    total_chunks: number;
}
export interface DigestResponse {
    sessionId: string;
    chunks_created: number;
    chunk_paths: string[];
}
export interface DigestAllResponse {
    total_chunks: number;
}
export interface LinkItem {
    source: string;
    target: string;
    distance: number;
}
export interface LinksResponse {
    sessionId: string;
    links_created: number;
    backlinks: LinkItem[];
}
export interface SearchResultItem {
    path: string;
    content: string;
    distance: number;
    metadata: Record<string, unknown>;
}
export interface SearchResponse {
    query: string;
    results: SearchResultItem[];
    total: number;
}
export interface ClassifyResponse {
    sessionId: string;
    project: string;
    topics: string[];
    summary: string;
    confidence: number;
}
export interface F2ClassificationResponse {
    session_id: string;
    cluster_label: string;
    cluster_id: number;
    tags: string[];
    confidence: number;
    coords: number[];
    classified_at: string;
    found: boolean;
}
export interface F2SummaryItem {
    cluster_label: string;
    count: number;
    avg_confidence: number;
}
export interface F2SummaryResponse {
    clusters: F2SummaryItem[];
    total: number;
}
export interface MergeCandidateItem {
    chunk_a: string;
    chunk_b: string;
    similarity: number;
    synthesis?: string;
}
export interface MergeResponse {
    candidates: MergeCandidateItem[];
    total: number;
}
export interface ResumeResponse {
    sessionId: string;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    turns: any[];
    total_turns: number;
}


// --- Orchestrator (AI 指揮台) Types ---
export interface FileEntry {
    name: string;
    path: string;
    is_dir: boolean;
    size?: number;
    children?: number;
}
export interface FilesListResponse {
    entries: FileEntry[];
    path: string;
}
export interface FilesReadResponse {
    content: string;
    path: string;
    size: number;
}
export interface GitFileStatus {
    path: string;
    status: string;
    code: string;
}
export interface GitStatusResponse {
    files: GitFileStatus[];
    total: number;
    repo: string;
}
export interface GitDiffResponse {
    diff: string;
    path: string;
    staged: boolean;
    repo: string;
}
export interface OrchestratorChatResponse {
    text: string;
    model: string;
    thinking: string;
}
export interface TerminalResponse {
    output: string;
    stdout?: string;
    stderr?: string;
    returncode: number;
    command: string;
    cwd: string;
}

// --- Quota Types ---
export interface QuotaModel {
    label: string;
    remaining_pct: number;
    reset_time: string;
    status: 'green' | 'yellow' | 'orange' | 'red';
}

export interface QuotaCredits {
    available: number;
    monthly: number;
}

export interface QuotaResponse {
    name: string;
    plan: string;
    prompt_credits: QuotaCredits;
    flow_credits: QuotaCredits;
    models: QuotaModel[];
    overall_status: 'green' | 'yellow' | 'orange' | 'red' | 'unknown';
    timestamp: string;
    error: string | null;
}

export const api = {
    // Status
    health: () => apiFetch<HealthCheckResponse>('/api/status/health'),
    status: () => apiFetch<HealthReportResponse>('/api/status'),

    // FEP
    fepState: () => apiFetch<FEPStateResponse>('/api/fep/state'),
    fepStep: (observation: number) => apiFetch<FEPStepResponse>('/api/fep/step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ observation } satisfies FEPStepRequest),
    }),
    fepDashboard: () => apiFetch<FEPDashboardResponse>('/api/fep/dashboard'),

    // Session Notes
    notesList: (project = '') =>
        apiFetch<NoteListResponse>(`/api/notes${project ? `?project=${encodeURIComponent(project)}` : ''}`),
    notesSearch: (q: string, topK = 5) =>
        apiFetch<SearchResponse>(`/api/notes/search?q=${encodeURIComponent(q)}&top_k=${topK}`),
    notesMerge: (project = '', threshold = 0.5, synthesize = false) =>
        apiFetch<MergeResponse>(`/api/notes/merge?threshold=${threshold}&synthesize=${synthesize}${project ? `&project=${encodeURIComponent(project)}` : ''}`),
    notesDigestAll: () =>
        apiFetch<DigestAllResponse>('/api/notes/digest-all', { method: 'POST' }),
    noteDetail: (sessionId: string) =>
        apiFetch<NoteDetailResponse>(`/api/notes/${encodeURIComponent(sessionId)}`),
    noteDigest: (sessionId: string) =>
        apiFetch<DigestResponse>(`/api/notes/${encodeURIComponent(sessionId)}/digest`, { method: 'POST' }),
    noteLinks: (sessionId: string) =>
        apiFetch<LinksResponse>(`/api/notes/${encodeURIComponent(sessionId)}/links`, { method: 'POST' }),
    noteClassify: (sessionId: string) =>
        apiFetch<ClassifyResponse>(`/api/notes/${encodeURIComponent(sessionId)}/classify`, { method: 'POST' }),
    noteF2Classify: (sessionId: string) =>
        apiFetch<F2ClassificationResponse>(`/api/notes/${encodeURIComponent(sessionId)}/classification`),
    noteF2Summary: () =>
        apiFetch<F2SummaryResponse>('/api/notes/classification-summary'),
    noteResume: (sessionId: string, maxChunks = 5) =>
        apiFetch<ResumeResponse>(`/api/notes/${encodeURIComponent(sessionId)}/resume?max_chunks=${maxChunks}`),

    // Gnōsis
    gnosisStats: () => apiFetch<GnosisStatsResponse>('/api/gnosis/stats'),

    // Quality
    dendronReport: (detail: 'summary' | 'full' = 'summary') =>
        apiFetch<DendronReportResponse>(`/api/dendron/report?detail=${detail}`),

    // Postcheck
    postcheckList: () => apiFetch<SELListResponse>('/api/postcheck/list'),
    postcheckRun: (wfName: string, content: string, mode = '') =>
        apiFetch<PostcheckResponse>('/api/postcheck/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ wf_name: wfName, content, mode }),
        }),

    // Graph
    graphNodes: () => apiFetch<GraphNode[]>('/api/graph/nodes'),
    graphEdges: () => apiFetch<GraphEdge[]>('/api/graph/edges'),
    graphFull: () => apiFetch<GraphFullResponse>('/api/graph/full'),

    // Notifications (Sympatheia)
    notifications: (limit = 50, level?: string) =>
        apiFetch<Notification[]>(
            `/api/sympatheia/notifications?limit=${limit}${level ? `&level=${level}` : ''}`
        ),

    // PKS
    pksPush: () => apiFetch<PKSPushResponse>('/api/pks/push'),
    pksTriggerPush: (_k = 20) => apiFetch<PKSPushResponse>('/api/pks/push', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
    }),
    pksFeedback: (title: string, reaction: string, series = '') =>
        apiFetch<PKSFeedbackResponse>('/api/pks/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, reaction, series }),
        }),
    pksStats: () => apiFetch<PKSStatsResponse>('/api/pks/stats'),
    pksGatewayStats: () => apiFetch<PKSGatewayStatsResponse>('/api/pks/gateway-stats'),

    // Gnōsis Narrator
    gnosisPapers: (query = '', limit = 20) =>
        apiFetch<GnosisPapersResponse>(`/api/gnosis/papers?query=${encodeURIComponent(query)}&limit=${limit}`),
    gnosisNarrate: (title: string, fmt = 'deep_dive') =>
        apiFetch<GnosisNarrateResponse>('/api/gnosis/narrate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, fmt }),
        }),

    // Link Graph
    linkGraphFull: (sourceType?: string) =>
        apiFetch<LinkGraphFullResponse>(
            `/api/link-graph/full${sourceType ? `?source_type=${encodeURIComponent(sourceType)}` : ''}`
        ),
    linkGraphStats: () => apiFetch<LinkGraphStatsResponse>('/api/link-graph/stats'),
    linkGraphNeighbors: (nodeId: string, hops = 2) =>
        apiFetch<LinkGraphNeighborsResponse>(`/api/link-graph/neighbors/${encodeURIComponent(nodeId)}?hops=${hops}`),

    // CCL + Workflows
    cclParse: (ccl: string) =>
        apiFetch<CCLParseResponse>('/api/ccl/parse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ccl }),
        }),
    cclExecute: (ccl: string, context = '') =>
        apiFetch<CCLExecuteResponse>('/api/ccl/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ccl, context }),
        }),
    wfList: () => apiFetch<WFListResponse>('/api/wf/list'),
    wfDetail: (name: string) => apiFetch<WFDetailResponse>(`/api/wf/${encodeURIComponent(name)}`),

    // Symploke 統合検索
    symplokeSearch: (q: string, k = 10, sources = 'handoff,sophia,kairos,gnosis,chronos') =>
        apiFetch<SymplokeSearchResponse>(
            `/api/symploke/search?q=${encodeURIComponent(q)}&k=${k}&sources=${encodeURIComponent(sources)}`
        ),
    symplokeStats: () => apiFetch<SymplokeStatsResponse>('/api/symploke/stats'),

    // F1 Motherbrain
    motherbrainGetStatus: () => apiFetch<MotherbrainStatusResponse>('/api/motherbrain/status'),
    motherbrainRefreshStatus: (mode: string = "fast") =>
        apiFetch<MotherbrainStatusResponse>(`/api/motherbrain/refresh?mode=${encodeURIComponent(mode)}`, { method: 'POST' }),
    motherbrainGetNarration: (section: string) =>
        apiFetch<MotherbrainNarrateResponse>(`/api/motherbrain/narrate/${encodeURIComponent(section)}`),


    // Timeline
    timelineEvents: (limit = 50, offset = 0, type?: string) => {
        let url = `/api/timeline/events?limit=${limit}&offset=${offset}`;
        if (type) url += `&event_type=${type}`;
        return apiFetch<TimelineEventsResponse>(url);
    },
    timelineEvent: (id: string) => apiFetch<TimelineEventDetail>(`/api/timeline/event/${id}`),
    timelineStats: () => apiFetch<TimelineStatsResponse>('/api/timeline/stats'),

    // Kalon
    kalonJudge: (concept: string, g_test: boolean, f_test: boolean, notes = '') =>
        apiFetch<KalonJudgeResponse>('/api/kalon/judge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ concept, g_test, f_test, notes }),
        }),
    kalonHistory: (limit = 50) =>
        apiFetch<KalonHistoryResponse>(`/api/kalon/history?limit=${limit}`),

    // Synteleia
    synteleiaAudit: (content: string, targetType = 'generic', withL2 = false, source?: string) =>
        apiFetch<SynteleiaAuditResponse>('/api/synteleia/audit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, target_type: targetType, with_l2: withL2, source }),
        }),
    synteleiaQuick: (content: string, targetType = 'generic') =>
        apiFetch<SynteleiaAuditResponse>('/api/synteleia/audit-quick', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, target_type: targetType }),
        }),
    synteleiaAgents: () => apiFetch<SynteleiaAgentInfo[]>('/api/synteleia/agents'),

    // Synedrion
    synedrionSweep: (filepath: string, domains?: string[], axes?: string[], maxPerspectives = 10, model = 'gemini-2.0-flash') =>
        apiFetch<SynedrionSweepResult>('/api/synedrion/sweep', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filepath, domains, axes, max_perspectives: maxPerspectives, model }),
        }),
    synedrionPerspectives: () => apiFetch<SynedrionPerspective[]>('/api/synedrion/perspectives'),
    synedrionCacheStats: () => apiFetch<SynedrionCacheStats>('/api/synedrion/cache/stats'),
    synedrionCacheClear: () => apiFetch<SynedrionCacheClear>('/api/synedrion/cache/clear', { method: 'POST' }),

    // Digestor
    digestorReports: (limit = 10) =>
        apiFetch<DigestReportListResponse>(`/api/digestor/reports?limit=${limit}`),
    digestorLatest: () =>
        apiFetch<DigestReport | null>('/api/digestor/latest'),
    digestorTopics: () =>
        apiFetch<DigestorTopicsResponse>('/api/digestor/topics'),
    digestorCreateTopic: (topic: DigestorTopic) =>
        apiFetch<DigestorTopic>('/api/digestor/topics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(topic),
        }),
    digestorUpdateTopic: (topicId: string, topic: DigestorTopic) =>
        apiFetch<DigestorTopic>(`/api/digestor/topics/${encodeURIComponent(topicId)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(topic),
        }),
    digestorDeleteTopic: (topicId: string) =>
        apiFetch<SuccessResponse>(`/api/digestor/topics/${encodeURIComponent(topicId)}`, {
            method: 'DELETE',
        }),
    digestorApproveCandidate: (req: ApproveRequest) =>
        apiFetch<ApproveResponse>('/api/digestor/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(req),
        }),

    // Sentinel
    sentinelLatest: () =>
        apiFetch<SentinelLatest>('/api/sentinel/latest'),

    // Epistemic
    epistemicStatus: () =>
        apiFetch<EpistemicStatusResponse>('/api/epistemic/status'),
    epistemicHealth: () =>
        apiFetch<EpistemicHealthResponse>('/api/epistemic/health'),

    // Basanos L2
    basanosL2Scan: () =>
        apiFetch<BasanosL2ScanResponse>('/api/basanos/l2/scan'),
    basanosL2History: (limit = 10) =>
        apiFetch<BasanosL2HistoryResponse>(`/api/basanos/l2/history?limit=${limit}`),
    basanosL2Trend: (window = 10) =>
        apiFetch<BasanosL2TrendResponse>(`/api/basanos/l2/trend?window=${window}`),

    // Scheduler
    schedulerStatus: (limit = 5) =>
        apiFetch<SchedulerStatusResponse>(`/api/scheduler/status?limit=${limit}`),
    schedulerTrend: (days = 14) =>
        apiFetch<SchedulerTrendResponse>(`/api/scheduler/trend?days=${days}`),
    schedulerAnalysis: () =>
        apiFetch<SchedulerAnalysisResponse>('/api/scheduler/analysis'),
    schedulerEvolution: () =>
        apiFetch<SchedulerEvolutionResponse>('/api/scheduler/evolution'),
    schedulerRotation: () =>
        apiFetch<SchedulerRotationResponse>('/api/scheduler/rotation'),

    // Theorem Usage
    theoremUsage: () => apiFetch<TheoremUsageResponse>('/api/theorem/usage'),
    theoremToday: () => apiFetch<TheoremTodayResponse>('/api/theorem/today'),

    // WAL
    walStatus: () => apiFetch<WALStatusResponse>('/api/wal/status'),

    // Quota
    quota: () => apiFetch<QuotaResponse>('/api/quota'),

    // --- Orchestrator (AI 指揮台) ---

    // DevTools: File Operations
    filesList: (path = '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon') =>
        apiFetch<FilesListResponse>(`/api/files/list?path=${encodeURIComponent(path)}`),
    filesRead: (path: string) =>
        apiFetch<FilesReadResponse>(`/api/files/read?path=${encodeURIComponent(path)}`),
    filesWrite: (path: string, content: string, encoding = 'text') =>
        apiFetch<{ success: boolean; path: string; size: number }>('/api/files/write', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path, content, encoding }),
        }),
    filesSearch: (query: string, path = '~/oikos', is_regex = false, match_case = false) =>
        apiFetch<{ matches: any[], count: number }>('/api/files/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, path, is_regex, match_case }),
        }),
    filesRename: (path: string, new_path: string) =>
        apiFetch<{ success: boolean; path: string }>('/api/files/rename', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path, new_path }),
        }),
    filesDelete: (path: string) =>
        apiFetch<{ success: boolean; path: string }>('/api/files/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path }),
        }),

    // DevTools: Git Operations
    gitStatus: (repo = '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon') =>
        apiFetch<GitStatusResponse>(`/api/git/status?repo=${encodeURIComponent(repo)}`),
    gitDiff: (repo = '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon', path = '', staged = false) =>
        apiFetch<GitDiffResponse>(
            `/api/git/diff?repo=${encodeURIComponent(repo)}&path=${encodeURIComponent(path)}&staged=${staged}`
        ),

    // DevTools: Ochema AI
    orchestratorChat: (message: string, model = 'gemini-2.0-flash', systemInstruction = '') =>
        apiFetch<OrchestratorChatResponse>('/api/ochema/ask_with_tools', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                model,
                system_instruction: systemInstruction,
                max_iterations: 10,
                max_tokens: 8192,
            }),
        }),

    // DevTools: Terminal
    terminalExecute: (command: string, cwd = '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon') =>
        apiFetch<TerminalResponse>('/api/terminal/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command, cwd }),
        }),

    // ─── HGK Gateway API ─────────────────────────────────────
    // GET endpoints
    hgkStatus: () => apiFetch<{ result: string }>('/api/hgk/status'),
    hgkHealth: () => apiFetch<{ result: string }>('/api/hgk/health'),
    hgkDoxa: () => apiFetch<{ result: string }>('/api/hgk/doxa'),
    hgkPksStats: () => apiFetch<{ result: string }>('/api/hgk/pks/stats'),
    hgkPksHealth: () => apiFetch<{ result: string }>('/api/hgk/pks/health'),
    hgkDigestCheck: () => apiFetch<{ result: string }>('/api/hgk/digest/check'),
    hgkDigestTopics: () => apiFetch<{ result: string }>('/api/hgk/digest/topics'),
    hgkModels: () => apiFetch<{ result: string }>('/api/hgk/models'),
    hgkGatewayHealth: () => apiFetch<{ result: string }>('/api/hgk/gateway/health'),
    hgkSessions: () => apiFetch<{ result: string }>('/api/hgk/sessions'),
    hgkNotifications: (limit = 10) =>
        apiFetch<{ result: string }>(`/api/hgk/notifications?limit=${limit}`),
    hgkHandoff: (count = 1) =>
        apiFetch<{ result: string }>(`/api/hgk/handoff?count=${count}`),

    // POST endpoints
    hgkCclDispatch: (ccl: string) =>
        apiFetch<{ result: string }>('/api/hgk/ccl/dispatch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ccl }),
        }),
    hgkCclExecute: (ccl: string, context = '') =>
        apiFetch<{ result: string }>('/api/hgk/ccl/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ccl, context }),
        }),
    hgkIdea: (idea: string, tags = '') =>
        apiFetch<{ result: string }>('/api/hgk/idea', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idea, tags }),
        }),
    hgkPaperSearch: (query: string, limit = 5) =>
        apiFetch<{ result: string }>('/api/hgk/papers/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, limit }),
        }),
    hgkDigestList: (topics = '', maxCandidates = 10) =>
        apiFetch<{ result: string }>('/api/hgk/digest/list', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topics, max_candidates: maxCandidates }),
        }),
    hgkDigestRun: (topics = '', maxPapers = 20, dryRun = true) =>
        apiFetch<{ result: string }>('/api/hgk/digest/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topics, max_papers: maxPapers, dry_run: dryRun }),
        }),
    hgkDigestMark: (filenames = '') =>
        apiFetch<{ result: string }>('/api/hgk/digest/mark', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filenames }),
        }),
    hgkProactive: (topics = '', maxResults = 5, useAdvocacy = true) =>
        apiFetch<{ result: string }>('/api/hgk/proactive', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topics, max_results: maxResults, use_advocacy: useAdvocacy }),
        }),
    hgkSop: (topic: string, decision = '', hypothesis = '') =>
        apiFetch<{ result: string }>('/api/hgk/sop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, decision, hypothesis }),
        }),
    hgkSessionRead: (cascadeId: string, maxTurns = 10, full = false) =>
        apiFetch<{ result: string }>('/api/hgk/sessions/read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cascade_id: cascadeId, max_turns: maxTurns, full }),
        }),

    // ─── Agent Mode ──────────────────────────────────────────
    agentAsk: (message: string, model = 'gemini-2.5-flash', options?: {
        systemInstruction?: string;
        maxIterations?: number;
        thinkingBudget?: number;
    }) =>
        apiFetch<{ text: string; model: string; token_usage: Record<string, number> }>(
            '/api/ask/agent',
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    model,
                    system_instruction: options?.systemInstruction,
                    max_iterations: options?.maxIterations ?? 10,
                    thinking_budget: options?.thinkingBudget,
                }),
            }
        ),

    // ─── IDE ConnectRPC API ──────────────────────────────────
    ideStatus: () => apiFetch<IdeStatusResponse>('/api/hgk/ide/status'),
    ideWorkflows: () => apiFetch<IdeApiResponse>('/api/hgk/ide/workflows'),
    ideMemories: () => apiFetch<IdeApiResponse>('/api/hgk/ide/memories'),
    ideTrajectories: () => apiFetch<IdeApiResponse>('/api/hgk/ide/trajectories'),
};

// --- Notification Types ---
export interface Notification {
    id: string;
    timestamp: string;
    source: string;
    level: 'INFO' | 'HIGH' | 'CRITICAL';
    title: string;
    body: string;
    data: Record<string, unknown>;
}

// --- PKS Types ---
export interface PKSNugget {
    title: string;
    abstract: string;
    source: string;
    relevance_score: number;
    url: string;
    authors: string;
    push_reason: string;
    serendipity_score: number;
    suggested_questions: string[];
}

export interface PKSPushResponse {
    timestamp: string;
    topics: string[];
    nuggets: PKSNugget[];
    total: number;
}

export interface PKSFeedbackResponse {
    timestamp: string;
    title: string;
    reaction: string;
    recorded: boolean;
}

export interface PKSStatsResponse {
    timestamp: string;
    series_stats: Record<string, { count: number; avg_score: number; threshold_adjustment: number }>;
    total_feedbacks: number;
}

export interface PKSGatewayStatsResponse {
    timestamp: string;
    enabled: boolean;
    sources: Record<string, { count: number }>;
    total_files: number;
}

// --- Graph Types ---
export interface GraphNode {
    id: string;
    series: string;
    name: string;
    greek: string;
    meaning: string;
    workflow: string;
    type: string;
    color: string;
    position: { x: number; y: number; z: number };
}

export interface GraphEdge {
    id: string;
    pair: string;
    source: string;
    target: string;
    shared_coordinate: string;
    naturality: string;
    meaning: string;
    type: string;
}

export interface GraphFullResponse {
    nodes: GraphNode[];
    edges: GraphEdge[];
    meta: {
        total_nodes: number;
        total_edges: number;
        series: Record<string, { name: string; color: string; theorems: number }>;
        trigonon: { vertices: string[]; description: string };
        naturality: Record<string, string>;
    };
}

// --- Gnōsis Narrator Types ---
export interface PaperCard {
    title: string;
    authors: string;
    abstract: string;
    source: string;
    topics: string[];
    relevance_score: number;
    question: string;  // kalon: この論文が投げかける問い
}

export interface GnosisPapersResponse {
    timestamp: string;
    papers: PaperCard[];
    total: number;
}

export interface NarrateSegment {
    speaker: string;
    content: string;
}

export interface GnosisNarrateResponse {
    timestamp: string;
    title: string;
    fmt: string;
    segments: NarrateSegment[];
    icon: string;
    generated: boolean;
}

// --- CCL Types ---
export interface CCLParseResponse {
    success: boolean;
    ccl: string;
    tree: string | null;
    workflows: string[];
    wf_paths: Record<string, string>;
    plan_template: string | null;
    error: string | null;
}

export interface CCLExecuteResponse {
    success: boolean;
    ccl: string;
    result: Record<string, unknown> | null;
    error: string | null;
}

export interface WFSummary {
    name: string;
    description: string;
    ccl: string;
    modes: string[];
}

export interface WFListResponse {
    total: number;
    workflows: WFSummary[];
}

export interface WFDetailResponse {
    name: string;
    description: string;
    ccl: string;
    stages: Array<{ name?: string; description?: string }>;
    modes: string[];
    source_path: string | null;
    raw_content: string | null;
    metadata: Record<string, unknown>;
}

// --- Link Graph Types ---
export interface LinkGraphNode {
    id: string;
    title: string;
    source_type: string;
    projected_series: string;
    projected_theorem: string;
    degree: number;
    backlink_count: number;
    community: number;
    orbit_angle: number;
    orbit_radius: number;
}

export interface LinkGraphEdge {
    source: string;
    target: string;
    type: string;
}

export interface LinkGraphFullResponse {
    nodes: LinkGraphNode[];
    edges: LinkGraphEdge[];
    meta: {
        total_nodes: number;
        total_edges: number;
        source_type_counts: Record<string, number>;
        projection_counts: Record<string, number>;
        projection_map: Record<string, string>;
    };
}

export interface LinkGraphStatsResponse {
    total_nodes: number;
    total_edges: number;
    bridge_nodes: string[];
    source_type_counts: Record<string, number>;
    projection_counts: Record<string, number>;
}

export interface LinkGraphNeighborsResponse {
    node_id: string;
    hops: number;
    neighbors: Array<{
        id: string;
        title: string;
        source_type: string;
        projected_series: string;
        projected_theorem: string;
        degree: number;
    }>;
    total: number;
    error?: string;
}

// ─── Sophia KI Types ─────────────────────────────────────

export interface KIListItem {
    id: string;
    title: string;
    source_type: string;
    updated: string;
    created: string;
    size_bytes: number;
}

export interface KIDetail {
    id: string;
    title: string;
    content: string;
    source_type: string;
    updated: string;
    created: string;
    size_bytes: number;
    backlinks: string[];
}

export interface KICreateRequest {
    title: string;
    content?: string;
    source_type?: string;
}

export interface KIUpdateRequest {
    title?: string;
    content?: string;
}

export interface KIListResponse {
    items: KIListItem[];
    total: number;
}

// ─── Symploke 統合検索 Types ─────────────────────────────

export interface SymplokeSearchResultItem {
    id: string;
    source: string; // "handoff" | "sophia" | "kairos" | "gnosis" | "chronos"
    score: number;
    title: string;
    snippet: string;
    metadata: Record<string, unknown>;
}

export interface SymplokeSearchResponse {
    query: string;
    results: SymplokeSearchResultItem[];
    total: number;
    sources_searched: string[];
}

export interface SymplokeStatsResponse {
    handoff_count: number;
    sophia_index_exists: boolean;
    kairos_index_exists: boolean;
    persona_exists: boolean;
    boot_axes_available: string[];
}

// ─── Sophia KI API Methods ───────────────────────────────

export async function kiList(): Promise<KIListResponse> {
    return apiFetch<KIListResponse>('/api/sophia/ki');
}

export async function kiGet(id: string): Promise<KIDetail> {
    return apiFetch<KIDetail>(`/api/sophia/ki/${encodeURIComponent(id)}`);
}

export async function cortexAsk(message: string, model: string = "gemini-2.5-flash"): Promise<{ text: string, model: string }> {
    try {
        const response = await fetch(`${API_BASE}/api/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, model }),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `API error: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Error in cortexAsk:", error);
        throw error;
    }
}

export async function kiCreate(req: KICreateRequest): Promise<KIDetail> {
    return apiFetch<KIDetail>('/api/sophia/ki', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
    });
}

export async function kiUpdate(id: string, req: KIUpdateRequest): Promise<KIDetail> {
    return apiFetch<KIDetail>(`/api/sophia/ki/${encodeURIComponent(id)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
    });
}

export async function kiDelete(id: string): Promise<{ status: string; id: string }> {
    return apiFetch<{ status: string; id: string }>(`/api/sophia/ki/${encodeURIComponent(id)}`, {
        method: 'DELETE',
    });
}

// ─── F1 Motherbrain Types ─────────────────────────────────────

export interface MotherbrainStatusResponse {
    status: string;
    last_boot_time: number;
    axes: Record<string, any>;
}

export interface MotherbrainNarrateResponse {
    section: string;
    narration: string;
    urgency: 'high' | 'medium' | 'low';
    action_suggestions: string[];
}

