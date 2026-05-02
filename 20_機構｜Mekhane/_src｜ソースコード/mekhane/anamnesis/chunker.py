# PROOF: [L2/インフラ] <- mekhane/anamnesis/chunker.py
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

P3 → 記憶の永続化が必要
   → 長文記憶 (Handoff/ROM) のセマンティック検索精度向上
   → 意味的単位 (Chunk) への分割が必要
   → chunker.py が担う

Q.E.D.

---

Gnōsis Chunker - Markdown Structure-Aware Chunking
"""

import logging
import re
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class MarkdownChunker:
    """Markdownドキュメントをセクション (##, ###) 単位で分割する"""

    def __init__(self, max_chars: int = 2000, overlap: int = 200):
        self.max_chars = max_chars
        self.overlap = overlap

    def chunk(self, text: str, source_id: str, title: str = "") -> List[Dict]:
        """
        Markdownテキストをチャンクに分割する。
        各チャンクは独立した文書として扱えるよう、親のタイトルや見出し情報を付与する。

        Args:
            text: 分割対象のMarkdownテキスト
            source_id: 元ドキュメントの識別子 (primary_key)
            title: 元ドキュメントのタイトル

        Returns:
            List of dicts containing chunk text and metadata
        """
        if not text:
            return []

        # 1. 見出しでセクションに分割
        sections = self._split_by_headers(text)

        chunks = []
        for i, section in enumerate(sections):
            section_title = section["title"]
            content = section["content"]

            # Context enrichment: チャンク自体に親情報を埋め込むことで、
            # Embedding モデルが「何について書かれた部分か」を文脈として理解しやすくなる。
            context_header = ""
            if title or section_title:
                parts = []
                if title:
                    parts.append(title)
                if section_title and section_title != title:
                    parts.append(section_title)
                if parts:
                    context_header = f"[{' > '.join(parts)}]\n"

            # 2. セクションが長すぎる場合はさらにサイズで分割
            if len(content) > self.max_chars:
                sub_chunks = self._split_by_length(content)
                for j, sub_chunk in enumerate(sub_chunks):
                    # Combine context header with content
                    combined_text = context_header + sub_chunk
                    chunks.append({
                        "id": f"{source_id}_sec{i}_chunk{j}",
                        "parent_id": source_id,
                        "text": combined_text,
                        "section_title": section_title,
                        "chunk_index": len(chunks)
                    })
            else:
                # Combine context header with content
                combined_text = context_header + content
                if combined_text.strip():
                    chunks.append({
                        "id": f"{source_id}_sec{i}",
                        "parent_id": source_id,
                        "text": combined_text,
                        "section_title": section_title,
                        "chunk_index": len(chunks)
                    })

        # 番号の再割り当て
        for i, c in enumerate(chunks):
            c["chunk_index"] = i

        return chunks

    def _split_by_headers(self, text: str) -> List[Dict]:
        """Header (##, ###) でテキストを分割する"""
        # H1 (#) はタイトルとみなし、H2/H3 (##, ###) をセクションの区切りとする
        pattern = re.compile(r'^(#{2,3})\s+(.+)$', re.MULTILINE)
        
        matches = list(pattern.finditer(text))
        
        if not matches:
            # 見出しがない場合は全体を1つのセクションとする
            return [{"title": "", "content": text}]

        sections = []
        
        # 最初の見出しまでのテキスト (Introduction)
        intro_text = text[:matches[0].start()].strip()
        if intro_text:
            sections.append({"title": "Introduction", "content": intro_text})

        # 見出し間のテキスト
        for i, match in enumerate(matches):
            title = match.group(2).strip()
            start_pos = match.end()
            end_pos = matches[i+1].start() if i + 1 < len(matches) else len(text)
            
            content = text[start_pos:end_pos].strip()
            if content:
                sections.append({"title": title, "content": content})

        return sections

    def _split_by_length(self, text: str) -> List[str]:
        """指定の長さでテキストをスライディングウィンドウ分割する (overlap考慮)"""
        chunks = []
        
        # 段落区切りで分割を試みる
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # 段落自体が max_chars より大きい場合は強制分割 (文・単語レベルでの分割は省略し単純にスライス)
            if len(para) > self.max_chars:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # スライディングウィンドウで分割
                pos = 0
                while pos < len(para):
                    end_pos = min(pos + self.max_chars, len(para))
                    chunks.append(para[pos:end_pos])
                    pos += (self.max_chars - self.overlap)
                continue
            
            # 追加すると max_chars を超える場合は現在の塊を保存し、新しい塊を開始
            if len(current_chunk) + len(para) + 2 > self.max_chars: # +2 is for '\n\n'
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                    
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks


class NucleatorChunker:
    """Nucleator (embedding ベース意味的チャンク) アダプタ。

    MarkdownChunker と同じ chunk(text, source_id, title) -> List[Dict]
    インターフェースを実装。embedding 関数を注入して使用する。

    理論的背景: linkage_hyphe.md §3-§8
      - 類似度トレース → 境界検出 → G∘F 反復 → L(c) 計算
      - τ がチャンクのスケール (粒度) を制御

    tau="auto" 指定時は統計的戦略 (μ-1.5σ) で τ を動的に決定する。
    Phantazein のエントロピーベース τ 決定も resolve_tau() で利用可能。
    """

    def __init__(
        self,
        embed_fn=None,
        tau: float | str = 0.70,
        min_steps: int = 2,
        max_iterations: int = 10,
        sim_mode: str = "knn",
        sim_k: int = 3,
        max_chars: int = 2000,
        overlap: int = 200,
        precision_gate: float = 0.0,
    ):
        """
        Args:
            embed_fn: テキスト列 -> embedding 列 の関数 (None の場合 MarkdownChunker にフォールバック)
            tau: 境界検出閾値 (0.60-0.80) or "auto" (統計的に動的決定)
            min_steps: チャンク最小ステップ数
            max_iterations: G∘F 最大反復回数
            sim_mode: 類似度モード ("pairwise" or "knn")
            sim_k: knn の k 値
            max_chars: フォールバック用 max_chars
            overlap: フォールバック用 overlap
            precision_gate: precision がこの値未満のチャンクを除外 (0.0 = 無効)
        """
        self.embed_fn = embed_fn
        self._tau_spec = tau  # "auto" or float
        self.min_steps = min_steps
        self.max_iterations = max_iterations
        self.sim_mode = sim_mode
        self.sim_k = sim_k
        self.precision_gate = precision_gate
        self.ensemble_weight: float = 0.5  # デフォルト: グリッドサーチ最適値
        # フォールバック用
        self._fallback = MarkdownChunker(max_chars=max_chars, overlap=overlap)
        # τ 解決キャッシュ (auto 時に一度だけ計算)
        self._resolved_tau: Optional[float] = None

    @property
    def tau(self) -> float:
        """現在の τ 値を返す。auto の場合は遅延解決。"""
        if self._resolved_tau is not None:
            return self._resolved_tau
        if isinstance(self._tau_spec, (int, float)):
            return float(self._tau_spec)
        # "auto" → 類似度トレースから統計的に決定 (chunk 時に解決)
        return 0.70  # chunk() 内で similarity から動的決定される

    def resolve_tau(self, issues: Optional[list] = None) -> float:
        """Phantazein の consistency_log から τ を動的に決定する。

        issues が明示されない場合は PhantazeinStore から自動取得。
        取得失敗時は τ_base=0.70 をフォールバック。

        Returns:
            解決された τ 値 (キャッシュされる)
        """
        if issues is None:
            issues = self._fetch_issues()

        from mekhane.anamnesis.chunker_nucleator import compute_tau_from_entropy
        self._resolved_tau = compute_tau_from_entropy(issues)
        return self._resolved_tau

    @staticmethod
    def _fetch_issues() -> list[dict]:
        """PhantazeinStore から直近の consistency issues を取得。

        PhantazeinStore が利用不可の場合は空リスト (→ τ_base フォールバック)。
        """
        try:
            from mekhane.symploke.phantazein_store import PhantazeinStore
            store = PhantazeinStore()
            return store.get_recent_issues(limit=50)
        except Exception:  # noqa: BLE001
            return []

    def chunk(self, text: str, source_id: str, title: str = "") -> List[Dict]:
        """MarkdownChunker 互換インターフェースで意味的チャンクを返す。

        embed_fn が None の場合、MarkdownChunker にフォールバック。
        """
        if not text or not text.strip():
            return []

        # embed_fn がなければ正規表現ベースにフォールバック
        if self.embed_fn is None:
            return self._fallback.chunk(text, source_id, title)

        try:
            return self._chunk_with_nucleator(text, source_id, title)
        except Exception as e:  # noqa: BLE001
            # Nucleator 失敗時もフォールバック
            logger.warning("Nucleator 失敗、MarkdownChunker にフォールバック: %s", e)
            return self._fallback.chunk(text, source_id, title)

    def _chunk_with_nucleator(self, text: str, source_id: str, title: str) -> List[Dict]:
        """Nucleator アルゴリズムでチャンク化し、MarkdownChunker 互換 dict を返す。"""
        from mekhane.anamnesis.chunker_nucleator import (
            Step,
            chunk_session,
        )

        # テキストを意味的段落 (ステップ) に分割
        steps = self._text_to_steps(text)
        if len(steps) < 2:
            return self._fallback.chunk(text, source_id, title)

        # embedding 生成
        step_texts = [s.text for s in steps]
        embeddings = self.embed_fn(step_texts)

        if not embeddings or len(embeddings) != len(steps):
            return self._fallback.chunk(text, source_id, title)

        # τ 解決
        effective_tau = self._tau_spec if isinstance(self._tau_spec, (int, float)) else "auto"

        # Nucleator 実行
        result = chunk_session(
            steps, embeddings,
            tau=effective_tau,
            min_steps=self.min_steps,
            max_iterations=self.max_iterations,
            sim_mode=self.sim_mode,
            sim_k=self.sim_k,
            ensemble_weight=self.ensemble_weight,
        )

        # MarkdownChunker 互換 dict に変換
        chunks = []
        gated_count = 0
        for i, c in enumerate(result.chunks):
            # 品質ゲート: precision が閾値未満のチャンクを除外
            if self.precision_gate > 0 and c.precision < self.precision_gate:
                gated_count += 1
                logger.info(
                    "  🚫 チャンク %d 除外 (precision=%.3f < gate=%.3f)",
                    i, c.precision, self.precision_gate,
                )
                continue

            context_header = ""
            if title:
                section_label = c.topic if c.topic else f"Chunk {i}"
                context_header = f"[{title} > {section_label}]\n"

            combined_text = context_header + c.text

            chunks.append({
                "id": f"{source_id}_nuc{i}",
                "parent_id": source_id,
                "text": combined_text,
                "section_title": c.topic or f"Chunk {i} (steps {c.step_range[0]}-{c.step_range[1]})",
                "chunk_index": len(chunks),
                # Nucleator 固有メトリクス (拡張)
                "coherence": round(c.coherence, 3),
                "drift": round(c.drift, 3),
                "efe": round(c.efe, 4),
                "precision": round(c.precision, 4),
                "precision_ensemble": round(c.precision_ensemble, 4),
            })

        if gated_count > 0:
            logger.info(
                "  📊 品質ゲート結果: %d/%d チャンク通過 (%d 除外, gate=%.2f)",
                len(chunks), len(result.chunks), gated_count, self.precision_gate,
            )

        return chunks

    @staticmethod
    def _text_to_steps(text: str) -> list:
        """テキストを段落単位で Step に変換する。

        ## マーカーがあればセクション区切り、なければ段落区切り。
        """
        from mekhane.anamnesis.chunker_nucleator import Step

        # まず ## マーカーで分割を試みる
        section_pattern = re.compile(r'^##\s+', re.MULTILINE)
        sections = section_pattern.split(text)

        if len(sections) > 2:
            # ## セクションが複数ある → セクション単位
            steps = []
            for idx, sec in enumerate(sections):
                sec = sec.strip()
                if sec:
                    steps.append(Step(index=idx, text=sec))
            return steps

        # ## がない or 1つしかない → 段落区切り
        paragraphs = re.split(r'\n\s*\n', text)
        steps = []
        idx = 0
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 20:  # 短すぎる段落はスキップ
                steps.append(Step(index=idx, text=para))
                idx += 1

        return steps

    # ── Cross-Session チャンキング ────────────────────────────

    @staticmethod
    def cross_ref_to_text(entries: list[dict]) -> str:
        """get_session_cross_ref() の出力をチャンキング用テキストに変換する。

        各セッションを ## セクションとして構造化し、時系列昇順で連結する。
        """
        if not entries:
            return ""

        sorted_entries = sorted(
            entries,
            key=lambda e: e.get("created_at", 0),
        )

        sections: list[str] = []
        for entry in sorted_entries:
            title = entry.get("title") or entry.get("id", "unknown")
            status = entry.get("status", "")
            agent = entry.get("agent", "")

            lines = [f"## Session: {title}"]
            if status:
                lines.append(f"Status: {status}")
            if agent:
                lines.append(f"Agent: {agent}")

            projects = entry.get("projects", [])
            if projects:
                pnames = [p.get("name", p.get("project_id", "?")) for p in projects]
                lines.append(f"Projects: {', '.join(pnames)}")

            handoffs = entry.get("handoffs", [])
            for h in handoffs:
                summary = h.get("summary", "")
                if summary:
                    lines.append(f"Handoff: {summary[:500]}")

            roms = entry.get("roms", [])
            for r in roms:
                topic = r.get("topic", "")
                if topic:
                    lines.append(f"ROM: {topic}")

            artifacts = entry.get("artifacts", [])
            if artifacts:
                anames = [a.get("filename", "?") for a in artifacts[:10]]
                lines.append(f"Artifacts: {', '.join(anames)}")

            text = "\n".join(lines)
            if len(text.strip()) > 20:
                sections.append(text)

        return "\n\n".join(sections)

    def chunk_cross_ref(
        self,
        entries: list[dict],
        source_id: str = "",
        days: int = 7,
        save_kernel: bool = False,
    ) -> List[Dict]:
        """cross_ref エントリ群を Nucleator でチャンキングする。"""
        if not source_id:
            source_id = f"xref_{days}d"

        text = self.cross_ref_to_text(entries)
        if not text.strip():
            return []

        chunks = self.chunk(
            text,
            source_id=source_id,
            title=f"Cross-Session Knowledge ({days}d)",
        )

        if save_kernel and len(chunks) >= 2:
            try:
                from mekhane.symploke.phantazein_store import PhantazeinStore
                store = PhantazeinStore()
                n = store.save_chunk_kernel(chunks, source_sessions=entries)
                logger.info(f"  🧠 ker(G) 保管: {n} エッジを knowledge_edges に保存")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"  ⚠ ker(G) 保管失敗 (chunk 結果は正常): {e}")

        return chunks

