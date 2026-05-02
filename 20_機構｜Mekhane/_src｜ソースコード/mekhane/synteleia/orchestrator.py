# PROOF: [L2/インフラ] <- mekhane/synteleia/orchestrator.py Synteleia 3×4 オーケストレーター
"""
Synteleia Orchestrator v2.0

12法 (Nomoi) ベースの 3×4 テンソル積監査。

構造:
    3 Stoicheia (S-I/S-II/S-III) × 4 Phase (P1/P2/P3/P4) = 12 Agent

CCL:
    @syn·  内積モード（12 Agent を並列実行し統合）
    @syn×  外積モード（原理内 P1×P2-P4 交差検証 = 9ペア + 12内積）

深度連動 (with_depth):
    L0: N06AnomalyAgent のみ（最小構成）
    L1: 12 Agent 内積
    L2: 12 Agent 内積 + L2 SemanticAgent
    L3: 12 Agent 外積 + L2 SemanticAgent

後方互換:
    poiesis_agents / kritai_agents プロパティは nomoi_agents の
    S-I/S-II/S-III グループにマッピングされる。
"""

import logging

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Literal, Optional

logger = logging.getLogger(__name__)

from .base import (
    AgentResult,
    AuditAgent,
    AuditResult,
    AuditSeverity,
    AuditTarget,
)

# 12法エージェント
from .nomoi import (
    ALL_AGENTS,
    S1_AGENTS,
    S2_AGENTS,
    S3_AGENTS,
    P1_AGENTS,
    N06AnomalyAgent,
)

# 旧エージェント (後方互換: with_l2/with_l3 + audit_quick で使用)
from .kritai import LogicAgent


# デフォルト除外パターン — パターン定義ファイル等の自動除外
DEFAULT_EXCLUDES = [
    "**/patterns.yaml",
    "**/persona.yaml",
    "**/*.prompt",
    "**/__pycache__/**",
]


# PURPOSE: Synteleia 3×4 オーケストレーター
class SynteleiaOrchestrator:
    """Synteleia 3×4 オーケストレーター

    実行モード:
        inner (内積): 12 Agent を並列実行し統合 (@syn·)
        outer (外積): 原理内 P1×P2-P4 交差検証 + 内積 (@syn×)
    """

    # PURPOSE: 初期化
    def __init__(
        self,
        nomoi_agents: Optional[List[AuditAgent]] = None,
        parallel: bool = True,
        default_excludes: Optional[List[str]] = None,
        mode: Literal["inner", "outer"] = "inner",
        *,
        # 後方互換パラメータ (非推奨)
        poiesis_agents: Optional[List[AuditAgent]] = None,
        kritai_agents: Optional[List[AuditAgent]] = None,
    ):
        """
        初期化。

        Args:
            nomoi_agents: 12法エージェント（省略時はデフォルト12エージェント）
            parallel: 並列実行するか
            default_excludes: デフォルト除外パターン
            mode: 実行モード — "inner" (内積) / "outer" (外積)
            poiesis_agents: 非推奨。後方互換用
            kritai_agents: 非推奨。後方互換用
        """
        # 後方互換: 旧パラメータが渡された場合はそれを使用
        if poiesis_agents is not None or kritai_agents is not None:
            logger.warning(
                "SynteleiaOrchestrator: poiesis_agents/kritai_agents は非推奨。"
                "nomoi_agents を使用してください。"
            )
            combined = []
            if poiesis_agents:
                combined.extend(poiesis_agents)
            if kritai_agents:
                combined.extend(kritai_agents)
            self._nomoi_agents = combined if combined else self._default_agents()
        elif nomoi_agents is not None:
            self._nomoi_agents = nomoi_agents
        else:
            self._nomoi_agents = self._default_agents()

        # L2/L3 用の追加エージェント（SemanticAgent 等）
        self._extra_agents: List[AuditAgent] = []

        self.parallel = parallel
        self.default_excludes = default_excludes if default_excludes is not None else DEFAULT_EXCLUDES
        self.mode = mode

    @staticmethod
    def _default_agents() -> List[AuditAgent]:
        """デフォルト12法エージェントをインスタンス化。"""
        return [cls() for cls in ALL_AGENTS]

    # -------------------------------------------
    # プロパティ
    # -------------------------------------------

    @property
    def nomoi_agents(self) -> List[AuditAgent]:
        """12法エージェント。"""
        return self._nomoi_agents

    @property
    def agents(self) -> List[AuditAgent]:
        """全エージェントを返す（互換性維持）。"""
        return self._nomoi_agents + self._extra_agents

    # 後方互換プロパティ
    @property
    def poiesis_agents(self) -> List[AuditAgent]:
        """非推奨。S-I エージェント (N01-N04) を返す。"""
        return [a for a in self._nomoi_agents if getattr(a, 'stoicheion', '') == 'S-I']

    @property
    def kritai_agents(self) -> List[AuditAgent]:
        """非推奨。S-II + S-III エージェント (N05-N12) を返す。
        
        Note: _extra_agents は含まない (poiesis_agents との対称性維持)。
              全エージェントが必要な場合は agents プロパティを使用。
        """
        return [
            a for a in self._nomoi_agents
            if getattr(a, 'stoicheion', '') in ('S-II', 'S-III')
        ]

    # 原理別プロパティ
    @property
    def s1_agents(self) -> List[AuditAgent]:
        """S-I Tapeinophrosyne エージェント (N01-N04)。"""
        return [a for a in self._nomoi_agents if getattr(a, 'stoicheion', '') == 'S-I']

    @property
    def s2_agents(self) -> List[AuditAgent]:
        """S-II Autonomia エージェント (N05-N08)。"""
        return [a for a in self._nomoi_agents if getattr(a, 'stoicheion', '') == 'S-II']

    @property
    def s3_agents(self) -> List[AuditAgent]:
        """S-III Akribeia エージェント (N09-N12)。"""
        return [a for a in self._nomoi_agents if getattr(a, 'stoicheion', '') == 'S-III']

    # 位相別プロパティ
    @property
    def p1_agents(self) -> List[AuditAgent]:
        """P1 Aisthēsis (入力段階) エージェント。"""
        return [a for a in self._nomoi_agents if getattr(a, 'phase', '') == 'P1']

    @property
    def p2_agents(self) -> List[AuditAgent]:
        """P2 Dianoia (処理段階) エージェント。"""
        return [a for a in self._nomoi_agents if getattr(a, 'phase', '') == 'P2']

    @property
    def p3_agents(self) -> List[AuditAgent]:
        """P3 Ekphrasis (出力段階) エージェント。"""
        return [a for a in self._nomoi_agents if getattr(a, 'phase', '') == 'P3']

    @property
    def p4_agents(self) -> List[AuditAgent]:
        """P4 Praxis (行動段階) エージェント。"""
        return [a for a in self._nomoi_agents if getattr(a, 'phase', '') == 'P4']

    # -------------------------------------------
    # ファクトリメソッド
    # -------------------------------------------

    # PURPOSE: L1 + L2 統合監査 (/dia+ 用ファクトリ)
    @classmethod
    def with_l2(cls, backend=None) -> "SynteleiaOrchestrator":
        """
        12法 + L2 SemanticAgent を含むオーケストレータを生成。

        /dia+ ワークフローから呼ばれる想定。

        Args:
            backend: LLM バックエンド（省略時は自動選択）

        Returns:
            SynteleiaOrchestrator: Nomoi + L2 統合オーケストレータ
        """
        from .kritai.semantic_agent import SemanticAgent

        orchestrator = cls()  # 12法デフォルト構成
        semantic = SemanticAgent(backend=backend)
        orchestrator._extra_agents.append(semantic)
        return orchestrator

    # PURPOSE: [L2-auto] Nomoi + Layer B Multi-LLM アンサンブル
    @classmethod
    def with_multi_l2(cls) -> "SynteleiaOrchestrator":
        """
        12法 + Layer B Multi-LLM アンサンブルを含むオーケストレータ。

        3 LLM に異なる persona を付与し、confidence-weighted majority voting で統合判断。

        Returns:
            SynteleiaOrchestrator: Nomoi + Multi-L2 統合オーケストレータ
        """
        from .kritai.multi_semantic_agent import MultiSemanticAgent

        orchestrator = cls()
        multi_agent = MultiSemanticAgent.default()
        orchestrator._extra_agents.append(multi_agent)
        return orchestrator

    # PURPOSE: L3 コンセンサス監査
    @classmethod
    def with_l3(
        cls,
        backends: Optional[list] = None,
    ) -> "SynteleiaOrchestrator":
        """
        Nomoi + L2 + L3 (ConsensusAgent) 統合オーケストレータ。

        Returns:
            SynteleiaOrchestrator: Nomoi + L2 + L3 統合
        """
        from .kritai.consensus_agent import ConsensusAgent
        from .kritai.multi_semantic_agent import MultiSemanticAgent

        orchestrator = cls()
        multi_agent = MultiSemanticAgent.default()
        consensus_agent = ConsensusAgent(backends=backends)
        orchestrator._extra_agents.append(multi_agent)
        orchestrator._extra_agents.append(consensus_agent)
        return orchestrator

    # PURPOSE: 深度連動ファクトリ — CCL 深度レベルに応じた自動構成
    @classmethod
    def with_depth(
        cls,
        depth: str = "L2",
        backend=None,
    ) -> "SynteleiaOrchestrator":
        """深度レベルに応じた Synteleia オーケストレータを生成。

        Args:
            depth: 深度レベル ("L0", "L1", "L2", "L3")
            backend: LLM バックエンド (L2+ で使用)

        Returns:
            SynteleiaOrchestrator:
                L0 → N06AnomalyAgent のみ (最小構成)
                L1 → 12法内積
                L2 → 12法内積 + L2 SemanticAgent
                L3 → 12法外積 + L2 SemanticAgent (原理内交差検証)
        """
        depth = depth.upper()

        if depth == "L0":
            # L0: 最小構成 (N06AnomalyAgent = 矛盾検出のみ)
            return cls(
                nomoi_agents=[N06AnomalyAgent()],
                parallel=False,
                mode="inner",
            )
        elif depth == "L1":
            # L1: 12法内積
            return cls(mode="inner")
        elif depth == "L3":
            # L3: 12法外積 + L2 SemanticAgent
            from .kritai.semantic_agent import SemanticAgent

            orchestrator = cls(mode="outer")
            semantic = SemanticAgent(backend=backend)
            orchestrator._extra_agents.append(semantic)
            logger.info(
                "Synteleia with_depth(L3): outer product mode, "
                "%d nomoi agents + %d extra = %d total",
                len(orchestrator._nomoi_agents),
                len(orchestrator._extra_agents),
                len(orchestrator.agents),
            )
            return orchestrator
        else:
            # L2 (デフォルト): 12法内積 + L2 SemanticAgent
            return cls.with_l2(backend=backend)

    # -------------------------------------------
    # 監査実行
    # -------------------------------------------

    # PURPOSE: 監査を実行
    def audit(self, target: AuditTarget) -> AuditResult:
        """監査を実行。

        mode="inner" (内積): 全エージェントを並列実行し統合。
        mode="outer" (外積): 原理内 P1×P2-P4 交差検証 + 内積。

        Args:
            target: 監査対象

        Returns:
            AuditResult: 統合監査結果
        """
        # デフォルト除外 + ターゲット除外パターンをマージ
        all_excludes = list(self.default_excludes)
        if target.exclude_patterns:
            all_excludes.extend(target.exclude_patterns)

        if target.source and all_excludes:
            from fnmatch import fnmatch

            for pat in all_excludes:
                if fnmatch(target.source, pat):
                    return AuditResult(
                        target=target,
                        passed=True,
                        summary=f"Excluded by pattern: {pat}",
                    )

        # モード分岐
        if self.mode == "outer" and len(self._nomoi_agents) > 1:
            agent_results = self._audit_outer_product(target)
        elif self.parallel and len(self.agents) > 1:
            agent_results = self._audit_parallel(target)
        else:
            agent_results = self._audit_sequential(target)

        # 結果を統合
        return self._aggregate_results(target, agent_results)

    # PURPOSE: 並列監査
    def _audit_parallel(self, target: AuditTarget) -> List[AgentResult]:
        """並列監査"""
        results = []

        with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            futures = {
                executor.submit(agent.audit, target): agent
                for agent in self.agents
                if agent.supports(target.target_type)
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:  # noqa: BLE001
                    agent = futures[future]
                    results.append(
                        AgentResult(
                            agent_name=agent.name,
                            passed=False,
                            issues=[],
                            confidence=0.0,
                            metadata={"error": str(e)},
                        )
                    )

        return results

    # PURPOSE: 外積モード — 原理内 P1×P2-P4 交差検証
    def _audit_outer_product(self, target: AuditTarget) -> List[AgentResult]:
        """外積モード (@syn×)。

        各原理内で P1 (入力段階) エージェントの結果を
        P2-P4 (処理/出力/行動) エージェントのコンテキストに注入して
        交差検証する。

        3原理 × 3ペア = 9 交差検証 + 12 内積 = 最大 21 並列タスク。
        """
        results: List[AgentResult] = []

        # Phase 1: 全 Nomoi + Extra を内積で並列実行
        all_results: Dict[str, AgentResult] = {}
        all_agents_to_run = self.agents
        with ThreadPoolExecutor(max_workers=len(all_agents_to_run)) as executor:
            futures = {
                executor.submit(agent.audit, target): agent
                for agent in all_agents_to_run
                if agent.supports(target.target_type)
            }
            for future in as_completed(futures):
                agent = futures[future]
                try:
                    result = future.result()
                    all_results[agent.name] = result
                    results.append(result)
                except Exception as e:  # noqa: BLE001
                    error_result = AgentResult(
                        agent_name=agent.name,
                        passed=False,
                        issues=[],
                        confidence=0.0,
                        metadata={"error": str(e)},
                    )
                    all_results[agent.name] = error_result
                    results.append(error_result)

        # Phase 2: 原理内 P1×P2-P4 交差検証
        # 各原理の P1 エージェント結果を同じ原理の P2-P4 に注入
        stoicheia_groups = [
            (self.s1_agents, "S-I"),
            (self.s2_agents, "S-II"),
            (self.s3_agents, "S-III"),
        ]

        cross_pairs = []
        for agents_in_principle, principle_name in stoicheia_groups:
            # P1 エージェントを特定
            p1_in_group = [a for a in agents_in_principle if getattr(a, 'phase', '') == 'P1']
            # P2-P4 エージェント
            p234_in_group = [a for a in agents_in_principle if getattr(a, 'phase', '') != 'P1']

            for p1_agent in p1_in_group:
                p1_result = all_results.get(p1_agent.name)
                if p1_result is None:
                    continue
                for cross_agent in p234_in_group:
                    if cross_agent.supports(target.target_type):
                        cross_pairs.append((p1_agent.name, p1_result, cross_agent, principle_name))

        if cross_pairs:
            logger.info(
                "Synteleia outer product: %d cross-validation pairs across 3 principles",
                len(cross_pairs),
            )

            def _run_cross(p1_name: str, p1_result: AgentResult, cross_agent: AuditAgent, principle: str) -> AgentResult:
                """1つの交差検証ペアを実行。"""
                # P1 の検出結果をコンテキストに注入
                augmented_content = (
                    f"{target.content}\n\n"
                    f"--- {principle} P1 '{p1_name}' 検出結果 ---\n"
                    f"{'PASS' if p1_result.passed else 'FAIL'} "
                    f"(confidence={p1_result.confidence:.0%})\n"
                )
                for issue in p1_result.issues:
                    augmented_content += f"  [{issue.severity.value}] {issue.message}\n"

                augmented_target = AuditTarget(
                    content=augmented_content,
                    target_type=target.target_type,
                    source=target.source,
                    exclude_patterns=target.exclude_patterns,
                )
                try:
                    cross_result = cross_agent.audit(augmented_target)
                    cross_result.metadata = cross_result.metadata or {}
                    cross_result.metadata["outer_product_pair"] = f"{p1_name}×{cross_agent.name}"
                    cross_result.metadata["principle"] = principle
                    return cross_result
                except Exception as e:  # noqa: BLE001
                    return AgentResult(
                        agent_name=cross_agent.name,
                        passed=False,
                        issues=[],
                        confidence=0.0,
                        metadata={
                            "error": str(e),
                            "outer_product_pair": f"{p1_name}×{cross_agent.name}",
                            "principle": principle,
                        },
                    )

            with ThreadPoolExecutor(max_workers=min(len(cross_pairs), 9)) as executor:
                futures = {
                    executor.submit(_run_cross, p1_name, p1_result, cross_agent, principle): (p1_name, cross_agent.name)
                    for p1_name, p1_result, cross_agent, principle in cross_pairs
                }
                for future in as_completed(futures):
                    try:
                        results.append(future.result())
                    except Exception as e:  # noqa: BLE001
                        pair_name = futures[future]
                        results.append(
                            AgentResult(
                                agent_name=f"{pair_name[0]}×{pair_name[1]}",
                                passed=False,
                                issues=[],
                                confidence=0.0,
                                metadata={"error": str(e)},
                            )
                        )

        return results

    # PURPOSE: 逐次監査
    def _audit_sequential(self, target: AuditTarget) -> List[AgentResult]:
        """逐次監査"""
        results = []

        for agent in self.agents:
            if agent.supports(target.target_type):
                try:
                    result = agent.audit(target)
                    results.append(result)
                except Exception as e:  # noqa: BLE001
                    results.append(
                        AgentResult(
                            agent_name=agent.name,
                            passed=False,
                            issues=[],
                            confidence=0.0,
                            metadata={"error": str(e)},
                        )
                    )

        return results

    # PURPOSE: 結果を統合
    def _aggregate_results(
        self, target: AuditTarget, agent_results: List[AgentResult]
    ) -> AuditResult:
        """結果を統合"""
        # 全エージェントが PASS なら PASS
        all_passed = all(ar.passed for ar in agent_results)

        # サマリー生成
        total_issues = sum(len(ar.issues) for ar in agent_results)
        critical_count = sum(
            1
            for ar in agent_results
            for i in ar.issues
            if i.severity == AuditSeverity.CRITICAL
        )
        high_count = sum(
            1
            for ar in agent_results
            for i in ar.issues
            if i.severity == AuditSeverity.HIGH
        )

        # ヒットカウンター記録
        from .pattern_loader import record_hit

        for ar in agent_results:
            for issue in ar.issues:
                record_hit(issue.code)

        if all_passed:
            summary = f"✅ PASS — {len(agent_results)} agents, {total_issues} issues (none critical/high)"
        else:
            summary = f"❌ FAIL — {critical_count} critical, {high_count} high issues"

        return AuditResult(
            target=target,
            agent_results=agent_results,
            passed=all_passed,
            summary=summary,
        )

    # -------------------------------------------
    # ユーティリティ
    # -------------------------------------------

    # PURPOSE: パターン統計取得
    @staticmethod
    def get_pattern_stats() -> Dict[str, int]:
        """パターンヒット統計を取得。"""
        from .pattern_loader import get_stats

        return get_stats()

    # PURPOSE: 高速監査 (N06AnomalyAgent のみ)
    def audit_quick(self, target: AuditTarget) -> AuditResult:
        """
        高速監査（N06AnomalyAgent のみ）。

        CCL: /audit-
        """
        quick_orchestrator = SynteleiaOrchestrator(
            nomoi_agents=[N06AnomalyAgent()],
            parallel=False,
        )
        return quick_orchestrator.audit(target)

    # PURPOSE: 監査結果をフォーマット
    def format_report(self, result: AuditResult) -> str:
        """監査結果をフォーマット"""
        lines = [
            "=" * 60,
            "Hegemonikón Audit Report",
            "=" * 60,
            "",
            f"Target: {result.target.target_type.value}",
            f"Status: {result.summary}",
            "",
        ]

        for ar in result.agent_results:
            lines.append(f"--- {ar.agent_name} ---")
            lines.append(f"Passed: {'✅' if ar.passed else '❌'}")
            lines.append(f"Confidence: {ar.confidence:.0%}")

            if ar.issues:
                lines.append(f"Issues ({len(ar.issues)}):")
                for issue in ar.issues:
                    severity_icon = {
                        AuditSeverity.CRITICAL: "🔴",
                        AuditSeverity.HIGH: "🟠",
                        AuditSeverity.MEDIUM: "🟡",
                        AuditSeverity.LOW: "🟢",
                        AuditSeverity.INFO: "⚪",
                    }.get(issue.severity, "⚪")
                    lines.append(f"  {severity_icon} [{issue.code}] {issue.message}")
                    if issue.suggestion:
                        lines.append(f"      💡 {issue.suggestion}")
            lines.append("")

        return "\n".join(lines)

    # PURPOSE: 監査結果から Sympatheia WBC アラートを生成
    def to_wbc_alert(self, result: AuditResult) -> Optional[dict]:
        """
        監査結果を Sympatheia WBC アラート形式に変換。

        HIGH/CRITICAL が検出された場合のみアラートを生成。

        Returns:
            dict | None: WBC アラートパラメータ or None
        """
        if result.critical_count == 0 and result.high_count == 0:
            return None

        # severity 決定: CRITICAL > HIGH
        severity = "critical" if result.critical_count > 0 else "high"

        # 問題サマリー
        issue_lines = []
        for ar in result.agent_results:
            for issue in ar.issues:
                if issue.severity in (AuditSeverity.CRITICAL, AuditSeverity.HIGH):
                    issue_lines.append(
                        f"[{issue.severity.value}] {ar.agent_name}: {issue.message}"
                    )

        details = (
            f"Synteleia 監査: {result.critical_count} CRITICAL, "
            f"{result.high_count} HIGH 検出\n"
            + "\n".join(issue_lines[:10])  # 最大10件
        )

        return {
            "details": details,
            "severity": severity,
            "source": "synteleia",
            "files": [result.target.source] if result.target.source else [],
        }

    # PURPOSE: WBC アラートを生成し Sympatheia に送信
    def notify_wbc(self, result: AuditResult) -> bool:
        """WBC アラートを生成・送信する統合メソッド。

        Returns:
            True if alert was sent successfully, False otherwise.
        """
        alert = self.to_wbc_alert(result)
        if alert is None:
            return False

        try:
            import httpx

            resp = httpx.post(
                "http://127.0.0.1:8392/api/wbc/alert",
                json=alert,
                timeout=5.0,
            )
            if resp.status_code == 200:
                return True
        except Exception:  # noqa: BLE001
            pass
        return False
