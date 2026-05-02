# PROOF: [L2/インフラ] <- hermeneus/src/skill_registry.py Skill Registry
"""
Hermēneus SkillRegistry — SKILL.md パーサー & Phase 定義管理

SKILL.md を構造化データ (SkillDefinition) にパースし、
WF 実行に必要な Phase 定義、テンプレート、派生情報を提供する。

Usage:
    registry = SkillRegistry()
    skill = registry.get("V05")
    phases = skill.get_execution_plan(derivative="struct", depth="L2")
    template = phases[0].output_template
"""

import re
import json
import yaml
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

WF_NAME_TO_ID = {
    "noe": "O1", "bou": "O2", "zet": "O3", "ene": "O4",
    "ske": "V05", "sag": "V06", "pei": "V07", "tek": "V08",
    "kat": "V09", "epo": "V10", "pai": "V11", "dok": "V12",
    "lys": "V13", "ops": "V14", "akr": "V15", "arh": "V16", "ark": "V16",
    "beb": "V17", "ele": "V18", "kop": "V19", "dio": "V20",
    "hyp": "V21", "prm": "V22", "ath": "V23", "par": "V24",
    "the": "V25", "ant": "V26", "ere": "V27", "agn": "V28",
    "sap": "V29", "ski": "V30", "prs": "V31", "per": "V32",
    "apo": "V33", "exe": "V34", "his": "V35", "prg": "V36",
}
ID_TO_WF_NAME = {value: key for key, value in WF_NAME_TO_ID.items()}


# =============================================================================
# Types
# =============================================================================

# PURPOSE: WF の1フェーズ定義
@dataclass
class PhaseDefinition:
    """WF の1フェーズ"""
    number: int                    # Phase 番号 (0, 1, 2, 3, 4...)
    name: str                      # "Prolegomena", "Deconstruction" 等
    algorithm: str = ""            # 認知アルゴリズム名
    steps: List[str] = field(default_factory=list)       # 実行ステップ
    output_template: str = ""      # 出力テンプレート (Markdown)
    required_for: List[str] = field(default_factory=list) # どの派生で必須か
    raw_content: str = ""          # Phase セクションの生コンテンツ
    
    def to_prompt(self, skill_id: str, skill_name: str, context: str = "") -> str:
        """この Phase を実行するための LLM 命令プロンプトを生成する"""
        algo_str = f" (Cognitive Algorithm: {self.algorithm})" if self.algorithm else ""
        lines = [
            f"あなたは Hegemonikón の {skill_id} {skill_name} スキルを構成するエージェントです。",
            f"現在実行中のフェーズ: Phase {self.number} - {self.name}{algo_str}",
            "以下の手順・留意事項・出力形式に従って、このフェーズのタスクを実行してください。",
            "\n--- [PHASE DEFINITION] ---",
            self.raw_content.strip(),
            "--------------------------\n"
        ]
        
        if self.steps:
            lines.append("## 実行ステップ")
            for i, step in enumerate(self.steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")
        
        if self.output_template:
            lines.extend([
                "## 出力テンプレート (この形式で出力せよ)",
                "```",
                self.output_template.strip(),
                "```\n"
            ])
        
        if context:
            lines.extend([
                "## 入力コンテキスト / 前フェーズまでの状態",
                context.strip()
            ])

        lines.extend([
            "",
            "## 実行上の強制規約 (Anti-Shallow)",
            "1. 入力や raw_content の言い換えで埋めず、このフェーズで得た新しい観測・比較・判断を追加すること。",
            "2. 前フェーズから受け取った固有名詞・仮説・候補・結論を維持し、何を受け取り何を変換したかを明示すること。",
            "3. Trace 必須: 少なくとも1つは理由・根拠・順序の必然を明示すること。",
            "4. Negativa 必須: 候補・前提・代替案がある場合、少なくとも1つの非採用/棄却理由を残すこと。",
            "5. Iso 必須: raw_content に表・ラベル・S[x.y]・CHECKPOINT・WM・QS がある場合、その構造を prose に潰さず出力へ保存すること。",
        ])
            
        return "\n".join(lines)


# PURPOSE: 派生モードの定義
@dataclass 
class DerivativeMode:
    """派生モード"""
    name: str                      # "wild", "struct", "strict", etc.
    ccl: str = ""                  # "/ske.wild" etc.
    description: str = ""          # 用途の説明
    focus: str = ""                # 焦点
    extra_process: str = ""        # 派生固有の追加プロセス


# PURPOSE: execution_contract frontmatter の定義
@dataclass
class ExecutionContractDefinition:
    """明示 invocation 時の実行契約。"""

    explicit_invocation: str = "strict"
    implicit_trigger: str = "flexible"
    fallback_behavior: str = "declare_and_stop"
    default_depth: str = "L2"
    macro_expansion: str = "optional"
    required_outputs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "explicit_invocation": self.explicit_invocation,
            "implicit_trigger": self.implicit_trigger,
            "fallback_behavior": self.fallback_behavior,
            "default_depth": self.default_depth,
            "macro_expansion": self.macro_expansion,
            "required_outputs": list(self.required_outputs),
        }


# PURPOSE: SKILL.md のパース結果
@dataclass
class SkillDefinition:
    """SKILL.md のパース結果"""
    id: str                        # "V05"
    name: str                      # "Skepsis"
    family: str = ""               # "Methodos"
    generation: str = ""           # "Flow (I) × Function (Explore)"
    description: str = ""          # 1行説明
    version: str = ""              # "4.2.0"
    derivatives: List[DerivativeMode] = field(default_factory=list)
    phases: List[PhaseDefinition] = field(default_factory=list)
    quality_score_name: str = ""   # "SkQS", "SgQS" etc.
    quality_score_template: str = "" # 品質スコアテンプレート
    anti_skip_rules: List[str] = field(default_factory=list)
    output_template: str = ""      # 統合出力テンプレート
    cognitive_algebra: Dict[str, str] = field(default_factory=dict)
    schedule: str = ""             # B2 Scheduled Workflows: cron syntax etc.
    source_path: Optional[Path] = None
    raw_frontmatter: Dict[str, Any] = field(default_factory=dict)
    execution_contract: ExecutionContractDefinition = field(
        default_factory=ExecutionContractDefinition
    )
    # ClawX Skill System Adjunction — 以下3フィールド追加
    is_core: bool = False          # ClawX: Skill.isCore (always=true → disable 不可)
    is_bundled: bool = True        # ClawX: Skill.isBundled (初期デプロイ済)
    config_schema: List[Dict[str, Any]] = field(default_factory=list)  # ClawX: SkillConfigSchema
    
    def get_execution_plan(
        self, derivative: str = "", depth: str = "L2"
    ) -> List[PhaseDefinition]:
        """派生と深度に基づいて実行すべき Phase リストを返す"""
        if depth == "L0":
            # Bypass: Phase 0 only
            return [p for p in self.phases if p.number == 0]
        elif depth == "L1":
            # Quick: Phase 0-2 (Synthesis 省略)
            return [p for p in self.phases if p.number <= 2]
        elif depth == "L3":
            # Deep: 全 Phase
            return self.phases
        else:
            # L2 Standard: + を除く Phase
            return [
                p for p in self.phases
                if not p.required_for or "" in p.required_for or depth in p.required_for
            ]
    
    def get_derivative(self, name: str) -> Optional[DerivativeMode]:
        """派生モードを名前で取得"""
        for d in self.derivatives:
            if d.name == name:
                return d
        return None


# =============================================================================
# Parser
# =============================================================================

# PURPOSE: SKILL.md パーサー
class SkillParser:
    """SKILL.md を SkillDefinition にパース"""
    
    FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    # ## PHASE N: Name, ### PHASE N 追加ガイダンス: Name, ## PHASE 1-2: Name 等に対応
    # 番号は N または N-M (結合ヘッダー)。セパレータは : — – のみ (- は番号範囲に使うため除外)
    PHASE_HEADER_RE = re.compile(
        r"^#{2,3}\s+PHASE\s+(\d+)(?:-\d+)?(?:[^:\—–]*?)[:\—–]\s*(.+?)(?:\s*\(.*\))?\s*$",
        re.MULTILINE | re.IGNORECASE
    )
    # 「## PHASE 0 〜 PHASE 5」のような一覧ヘッダー（スキップ用）
    PHASE_RANGE_RE = re.compile(
        r"^#{2,3}\s+PHASE\s+\d+\s*〜",
        re.MULTILINE | re.IGNORECASE
    )
    # Phase ガイダンスセクション (### PHASE N 追加ガイダンス)
    PHASE_GUIDANCE_RE = re.compile(
        r"^#{2,3}\s+PHASE\s+(\d+)\s+追加ガイダンス\s*[:\—–\-]\s*(.+?)$",
        re.MULTILINE | re.IGNORECASE
    )
    OUTPUT_TEMPLATE_RE = re.compile(
        r"```\s*\n(┌─\[.*?\].*?└─+┘)\s*\n```",
        re.DOTALL
    )
    ALGORITHM_RE = re.compile(
        r'>\s*\*\*認知アルゴリズム\*\*:\s*"(.+?)"',
        re.MULTILINE
    )
    
    def parse(self, path: Path) -> Optional[SkillDefinition]:
        """SKILL.md をパースして SkillDefinition を返す"""
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to read {path}: {e}")
            return None
        
        # 1. Frontmatter のパース
        frontmatter = self._parse_frontmatter(content)
        if not frontmatter:
            logger.warning(f"No frontmatter in {path}")
            return None
        
        skill_id = frontmatter.get("id", "") or self._infer_skill_id(path, frontmatter)
        skill_name = frontmatter.get("name", "")

        if not skill_id:
            logger.warning(f"No id in frontmatter: {path}")
            return None
        
        # 2. Phase のパース
        phases = self._parse_phases(content)
        
        # 3. 派生モードのパース
        derivatives = self._parse_derivatives(content, frontmatter)
        
        # 4. 品質スコアのパース
        qs_name, qs_template = self._parse_quality_score(content)
        
        # 5. Anti-Skip Protocol のパース
        anti_skip = self._parse_anti_skip(content)
        
        # 6. 統合出力テンプレートのパース
        output_template = self._parse_output_template(content)
        
        # 7. Cognitive Algebra
        ca = {}
        ca_raw = frontmatter.get("cognitive_algebra", {})
        if isinstance(ca_raw, dict):
            ca = {str(k): str(v) for k, v in ca_raw.items()}

        # 8. execution_contract
        execution_contract = self._parse_execution_contract(frontmatter)

        # 9. Generation
        gen = frontmatter.get("generation", {})
        if isinstance(gen, dict):
            gen_str = gen.get("formula", "") or gen.get("result", "")
        else:
            gen_str = str(gen)
        
        return SkillDefinition(
            id=str(skill_id),
            name=str(skill_name),
            family=str(frontmatter.get("family", "")),
            generation=gen_str,
            description=str(frontmatter.get("description", "")),
            version=str(frontmatter.get("version", "")),
            derivatives=derivatives,
            phases=phases,
            quality_score_name=qs_name,
            quality_score_template=qs_template,
            anti_skip_rules=anti_skip,
            output_template=output_template,
            cognitive_algebra=ca,
            schedule=str(frontmatter.get("schedule", "")),
            source_path=path,
            raw_frontmatter=frontmatter,
            execution_contract=execution_contract,
            # ClawX Adjunction fields
            is_core=bool(frontmatter.get("is_core", False)),
            is_bundled=bool(frontmatter.get("is_bundled", True)),
            config_schema=frontmatter.get("config_schema", []) or [],
        )

    def _infer_skill_id(self, path: Path, frontmatter: Dict[str, Any]) -> str:
        """frontmatter id がない SKILL.md の最小フォールバック。"""
        dir_name = path.parent.name.strip().lower()
        if dir_name in WF_NAME_TO_ID:
            return WF_NAME_TO_ID[dir_name]
        if isinstance(frontmatter.get("name"), str) and frontmatter["name"].strip():
            name = frontmatter["name"].strip()
            return WF_NAME_TO_ID.get(name.lower(), name)
        return path.parent.name.strip()
    
    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """YAML frontmatter をパース"""
        match = self.FRONTMATTER_RE.match(content)
        if not match:
            return {}
        try:
            return yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as e:
            logger.warning(f"YAML parse error: {e}")
            return {}
    
    def _parse_phases(self, content: str) -> List[PhaseDefinition]:
        """Phase 定義をパース"""
        phases = []
        seen_numbers = set()
        
        # PHASE ヘッダーの位置を全て取得
        all_headers = list(self.PHASE_HEADER_RE.finditer(content))
        
        # 「〜」パターン（範囲指定）のみを除外
        headers = []
        for m in all_headers:
            full_line = content[m.start():m.end()]
            if "〜" in full_line:
                continue
            headers.append(m)
        
        for i, match in enumerate(headers):
            phase_num = int(match.group(1))
            phase_name = match.group(2).strip()
            
            # 同じ番号の Phase が既にある場合はスキップ (追加ガイダンス等の重複)
            if phase_num in seen_numbers:
                continue
            seen_numbers.add(phase_num)
            
            # このPhaseの内容範囲を決定
            start = match.end()
            if i + 1 < len(headers):
                end = headers[i + 1].start()
            else:
                # 次の ##/### セクション (Phase でないもの) まで
                next_section = re.search(r"\n#{2,3} (?!PHASE)", content[start:], re.IGNORECASE)
                end = start + next_section.start() if next_section else len(content)
            
            raw = content[start:end]
            
            # 認知アルゴリズム名を抽出
            algo_match = self.ALGORITHM_RE.search(raw)
            algorithm = algo_match.group(1) if algo_match else ""
            
            # 出力テンプレートを抽出
            tmpl_match = self.OUTPUT_TEMPLATE_RE.search(raw)
            output_template = tmpl_match.group(1) if tmpl_match else ""
            
            # required_for を検出 ("+のみ" 等)
            required_for = [""]  # デフォルト: 全派生で必須
            if "のみ" in phase_name or "`+` のみ" in raw[:200]:
                required_for = ["+"]
            
            phases.append(PhaseDefinition(
                number=phase_num,
                name=phase_name,
                algorithm=algorithm,
                output_template=output_template,
                required_for=required_for,
                raw_content=raw.strip(),
            ))
        
        return sorted(phases, key=lambda p: p.number)
    
    def _parse_derivatives(
        self, content: str, frontmatter: Dict
    ) -> List[DerivativeMode]:
        """派生モードをパース"""
        derivatives = []
        
        # Frontmatter の derivatives リスト
        raw_derivs = frontmatter.get("derivatives", [])
        if isinstance(raw_derivs, list):
            for d in raw_derivs:
                if isinstance(d, str):
                    derivatives.append(DerivativeMode(name=d))
                elif isinstance(d, dict):
                    derivatives.append(DerivativeMode(
                        name=d.get("name", ""),
                        description=d.get("description", ""),
                    ))
        
        return derivatives
    
    def _parse_quality_score(self, content: str) -> tuple:
        """品質スコアをパース"""
        # SkQS, SgQS 等のパターンを探す
        qs_match = re.search(
            r"##\s+.*?((?:\w+QS|Quality Score).*?)\n",
            content, re.IGNORECASE
        )
        qs_name = qs_match.group(1).strip() if qs_match else ""
        
        # テンプレートを探す
        qs_tmpl_match = re.search(
            r"```\s*\n(┌─\[(?:\w+QS|.*Quality).*?└─+┘)\s*\n```",
            content, re.DOTALL
        )
        qs_template = qs_tmpl_match.group(1) if qs_tmpl_match else ""
        
        return qs_name, qs_template
    
    def _parse_anti_skip(self, content: str) -> List[str]:
        """Anti-Skip Protocol のルールをパース"""
        rules = []
        anti_skip_section = re.search(
            r"## .*Anti-Skip.*?\n(.*?)(?=\n## |\Z)",
            content, re.DOTALL | re.IGNORECASE
        )
        if anti_skip_section:
            # 番号付きリスト項目を抽出
            for match in re.finditer(
                r"^\d+\.\s+\*\*(.+?)\*\*", 
                anti_skip_section.group(1), 
                re.MULTILINE
            ):
                rules.append(match.group(1))
        return rules
    
    def _parse_output_template(self, content: str) -> str:
        """統合出力形式をパース"""
        section = re.search(
            r"## 統合出力形式\s*\n(.*?)(?=\n## |\Z)",
            content, re.DOTALL
        )
        if section:
            tmpl = self.OUTPUT_TEMPLATE_RE.search(section.group(1))
            if tmpl:
                return tmpl.group(1)
        return ""

    def _parse_execution_contract(
        self, frontmatter: Dict[str, Any]
    ) -> ExecutionContractDefinition:
        """execution_contract frontmatter をパース。"""
        raw = frontmatter.get("execution_contract", {})
        if not isinstance(raw, dict):
            raw = {}

        required_outputs = raw.get("required_outputs", [])
        if not isinstance(required_outputs, list):
            required_outputs = []

        return ExecutionContractDefinition(
            explicit_invocation=str(raw.get("explicit_invocation", "strict")),
            implicit_trigger=str(raw.get("implicit_trigger", "flexible")),
            fallback_behavior=str(raw.get("fallback_behavior", "declare_and_stop")),
            default_depth=str(raw.get("default_depth", "L2")),
            macro_expansion=str(raw.get("macro_expansion", "optional")),
            required_outputs=[str(item) for item in required_outputs if str(item).strip()],
        )


# =============================================================================
# Registry
# =============================================================================

# PURPOSE: Skill レジストリ
class SkillRegistry:
    """SKILL.md をロード・パース・キャッシュ"""
    
    # __file__ = hermeneus/src/skill_registry.py
    # parents[0]=src, parents[1]=hermeneus, parents[2]=_src｜ソースコード, parents[3]=20_機構｜Mekhane, parents[4]=project root
    _PROJECT_ROOT = Path(__file__).resolve().parents[4]
    DEFAULT_PATHS = [
        Path.home() / ".claude" / "skills",
        _PROJECT_ROOT / "10_知性｜Nous" / "02_手順｜Procedures" / "C_技能｜Skills",
    ]
    
    def __init__(
        self,
        skills_dir: Optional[Path] = None,
        search_paths: Optional[List[Path]] = None
    ):
        self._parser = SkillParser()
        self._cache: Dict[str, SkillDefinition] = {}
        self._search_paths = search_paths or self.DEFAULT_PATHS
        if skills_dir:
            self._search_paths = [skills_dir] + self._search_paths
        self._build_aliases()
        # ClawX Adjunction: state store (lazy init)
        self._state_store = None
    
    def get(self, skill_id: str) -> Optional[SkillDefinition]:
        """Skill 定義を取得
        
        Args:
            skill_id: Skill ID (例: "V05", "v05", "V05-skepsis")
        
        Returns:
            SkillDefinition or None
            Disabled skill は None を返す (isCore は常に enabled)
        """
        normalized = self._normalize_id(skill_id)
        
        if normalized in self._cache:
            skill = self._cache[normalized]
        else:
            # ファイルを検索
            path = self._find_skill_file(normalized)
            if not path:
                logger.warning(f"Skill not found: {skill_id}")
                return None
            
            # パース
            skill = self._parser.parse(path)
            if skill:
                self._cache[normalized] = skill
            else:
                return None
        
        # ClawX Adjunction: enabled チェック (isCore は常に enabled)
        if not skill.is_core:
            try:
                if self._state_store is None:
                    from hermeneus.src.skill_state import SkillStateStore
                    self._state_store = SkillStateStore()
                if not self._state_store.get_skill_enabled(skill.id):
                    return None
            except Exception:  # noqa: BLE001
                pass  # state store 障害時は全 skill enabled として扱う
        
        return skill
    
    def get_phase_template(
        self, skill_id: str, phase_number: int
    ) -> str:
        """特定 Phase の出力テンプレートを取得"""
        skill = self.get(skill_id)
        if not skill:
            return ""
        for phase in skill.phases:
            if phase.number == phase_number:
                return phase.output_template
        return ""
    
    def get_execution_plan(
        self,
        skill_id: str,
        derivative: str = "",
        depth: str = "L2"
    ) -> List[PhaseDefinition]:
        """実行すべき Phase リストを取得"""
        skill = self.get(skill_id)
        if not skill:
            return []
        return skill.get_execution_plan(derivative, depth)
    
    def load_all(self) -> Dict[str, SkillDefinition]:
        """全 SKILL.md をロード"""
        for search_path in self._search_paths:
            if not search_path.exists():
                continue
            for skill_file in search_path.rglob("*/SKILL.md"):
                # _archive 内は除外
                if "_archive" in skill_file.parts:
                    continue
                skill = self._parser.parse(skill_file)
                if skill:
                    self._cache[str(skill.id).upper()] = skill
        return dict(self._cache)
    
    def list_ids(self) -> List[str]:
        """ロード済み Skill ID 一覧"""
        if not self._cache:
            self.load_all()
        return sorted(self._cache.keys())
    
    def _build_aliases(self) -> None:
        """frontmatter ID ≠ ディレクトリ名 のケースを動的にマッピング構築。
        例: ディレクトリ v01-noesis の SKILL.md の frontmatter id が O1 の場合、
            _id_aliases["O1"] = "V01", _id_reverse["V01"] = "O1" を生成。
        """
        self._id_aliases: Dict[str, str] = {}
        self._id_reverse: Dict[str, str] = {}
        
        for search_path in self._search_paths:
            if not search_path.exists():
                continue
            for skill_file in search_path.rglob("*/SKILL.md"):
                if "_archive" in skill_file.parts:
                    continue
                parent = skill_file.parent.name
                match = re.match(r"([a-zA-Z]\d+)[-_]", parent)
                if not match:
                    continue
                dir_id = match.group(1).upper()  # e.g. "V01" or "O2"
                
                # frontmatter から ID を取得
                try:
                    content = skill_file.read_text(encoding="utf-8")
                    fm_match = self._parser.FRONTMATTER_RE.match(content)
                    if not fm_match:
                        continue
                    fm = yaml.safe_load(fm_match.group(1))
                    if not isinstance(fm, dict):
                        continue
                    fm_id = str(fm.get("id", "")).upper().strip()
                    if not fm_id:
                        continue
                except Exception:  # noqa: BLE001
                    continue
                
                # frontmatter ID とディレクトリ ID が異なる場合のみエイリアス登録
                if fm_id != dir_id:
                    self._id_aliases[fm_id] = dir_id
                    self._id_reverse[dir_id] = fm_id
    
    def _normalize_id(self, skill_id: str) -> str:
        """ID を正規化 (V05, v05, V05-skepsis → V05)"""
        # 大文字化
        s = skill_id.upper().strip()
        # ハイフン以降を除去
        if "-" in s:
            s = s.split("-")[0]
        if s in WF_NAME_TO_ID:
            return WF_NAME_TO_ID[s]
        return s
    
    def _find_skill_file(self, normalized_id: str) -> Optional[Path]:
        """Skill ID からファイルパスを検索"""
        # 検索候補: 元の ID + エイリアス
        search_ids = [normalized_id]
        if normalized_id in self._id_aliases:
            search_ids.append(self._id_aliases[normalized_id])
        if normalized_id in self._id_reverse:
            search_ids.append(self._id_reverse[normalized_id])
        if normalized_id in ID_TO_WF_NAME:
            search_ids.append(ID_TO_WF_NAME[normalized_id])

        for sid in search_ids:
            lower_id = sid.lower()
            upper_id = sid.upper()
            for search_path in self._search_paths:
                if not search_path.exists():
                    continue
                for exact_dir in (search_path / lower_id, search_path / upper_id, search_path / sid):
                    skill_file = exact_dir / "SKILL.md"
                    if skill_file.exists():
                        return skill_file
                for pattern in [f"{lower_id}-*", f"{lower_id}_*", f"{upper_id}-*", f"{upper_id}_*"]:
                    for skill_dir in search_path.rglob(pattern):
                        if "_archive" in skill_dir.parts:
                            continue
                        if skill_dir.is_dir():
                            skill_file = skill_dir / "SKILL.md"
                            if skill_file.exists():
                                return skill_file
        return None
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self._cache.clear()

    # PURPOSE: bundles.json からカテゴリプリセットをロード
    def load_bundles(self) -> List[Dict[str, Any]]:
        """skill_bundles.json からカテゴリプリセットをロード。
        
        ClawX mapping: bundles.json の 7 カテゴリを
        HGK の 9 カテゴリに翻訳した定義を読み込む。
        """
        for search_path in self._search_paths:
            bundles_file = search_path / "skill_bundles.json"
            if bundles_file.exists():
                try:
                    data = json.loads(bundles_file.read_text(encoding="utf-8"))
                    return data.get("bundles", [])
                except (json.JSONDecodeError, OSError) as exc:
                    logger.warning(f"Failed to load bundles: {exc}")
        return []

    # PURPOSE: 全スキルの詳細一覧 (state 含む)
    def list_all(self) -> List[Dict[str, Any]]:
        """全 Skill の詳細一覧を取得 (state 含む)。
        
        ClawX mapping: stores/skills.ts fetchSkills() の
        3 層マージ (Gateway + ClawHub + Config) に対応。
        HGK: SKILL.md (定義) + skill_state.json (状態) の 2 層マージ。
        """
        all_skills = self.load_all()
        
        try:
            if self._state_store is None:
                from hermeneus.src.skill_state import SkillStateStore
                self._state_store = SkillStateStore()
            states = self._state_store.get_all_states()
        except Exception:  # noqa: BLE001
            states = {}
        
        result = []
        for skill_id, skill in sorted(all_skills.items()):
            skill_state = states.get(skill_id, {})
            result.append({
                "id": skill.id,
                "name": skill.name,
                "family": skill.family,
                "version": skill.version,
                "is_core": skill.is_core,
                "is_bundled": skill.is_bundled,
                "enabled": skill_state.get("enabled", True),
                "has_config": bool(skill.config_schema),
                "config": skill_state.get("config", {}),
                "phases": len(skill.phases),
                "derivatives": [d.name for d in skill.derivatives],
            })
        return result

    def extract_cognitive_supplements(
        self,
        skill_id: str,
        max_chars: int = 3000,
    ) -> str:
        """SKILL.md から認知代数・Anti-Patterns・WM管理ブロックを抽出

        SkillParser はフェーズ (## PHASE X) しか構造化しないため、
        非フェーズのセクション（認知代数、Anti-Patterns 等）はここで
        SKILL.md の生テキストから直接取得する。

        Args:
            skill_id: Skill ID (例: "V01", "noe")
                      WF 短縮名 (noe, bou 等) も受け付ける
            max_chars: 抽出最大文字数

        Returns:
            抽出されたセクションテキスト（見つからない場合は空文字列）
        """
        # WF 短縮名 → Skill ID 変換
        WF_TO_SKILL = {
            "noe": "O1", "bou": "O2", "zet": "O3", "ene": "O4",
            "ske": "V05", "sag": "V06", "pei": "V07", "tek": "V08",
            "kat": "V09", "epo": "V10", "pai": "V11", "dok": "V12",
            "lys": "V13", "ops": "V14", "akr": "V15", "arc": "V16",
            "beb": "V17", "ele": "V18", "kop": "V19", "dio": "V20",
            "hyp": "V21", "prm": "V22", "ath": "V23", "par": "V24",
            "pro": "H01", "pis": "H02", "ore": "H03", "dox": "H04",
            "dia": "A02",
        }
        resolved_id = WF_TO_SKILL.get(skill_id.lower(), skill_id)
        normalized = self._normalize_id(resolved_id)

        # SKILL.md ファイルパスを解決
        skill_path = self._find_skill_file(normalized)
        if not skill_path or not skill_path.exists():
            return ""

        try:
            raw = skill_path.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            return ""

        # 抽出対象のセクションヘッダ（複数の表記揺れに対応）
        TARGETS = [
            ("## 認知代数", "認知代数"),
            ("## Anti-Patterns", "Anti-Patterns"),
            ("## Working Memory (WM) 管理", "WM管理"),
        ]

        blocks = []
        for header, label in TARGETS:
            pos = raw.find(header)
            if pos == -1:
                continue
            # セクション末尾: 次の ## まで、または --- まで
            next_h2 = raw.find("\n## ", pos + len(header))
            next_sep = raw.find("\n---\n", pos + len(header))
            if next_h2 == -1:
                next_h2 = len(raw)
            if next_sep == -1:
                next_sep = len(raw)
            end = min(next_h2, next_sep)
            block = raw[pos:end].strip()
            if block:
                blocks.append(block)

        result = "\n\n".join(blocks)
        return result[:max_chars] if result else ""

    # PURPOSE: SKILL.md から Phase-U 対応マッピングを抽出 (環境強制)
    def extract_phase_u(self, skill_id: str) -> str:
        """SKILL.md の context ブロックから Phase-U 対応を抽出する。

        Phase-U は Purge/Build/Audit 3層に分かれ、各 Phase が
        どの U (忘却) / N (回復) / F (自由) 成分で認知制御されるかを定義する。

        Args:
            skill_id: Skill ID (例: "V01", "noe")

        Returns:
            Phase-U セクションテキスト (存在しない場合は空文字列)
        """
        # WF 短縮名 → Skill ID 変換
        WF_TO_SKILL = {
            "noe": "V01", "bou": "V02", "zet": "V03", "ene": "V04",
            "ske": "V05", "sag": "V06", "pei": "V07", "tek": "V08",
            "kat": "V09", "epo": "V10", "pai": "V11", "dok": "V12",
            "lys": "V13", "ops": "V14", "akr": "V15", "arh": "V16",
            "beb": "V17", "ele": "V18", "kop": "V19", "dio": "V20",
            "hyp": "V21", "prm": "V22", "ath": "V23", "par": "V24",
            "the": "V25", "ant": "V26", "ere": "V27", "agn": "V28",
            "sap": "V29", "ski": "V30", "prs": "V31", "per": "V32",
            "apo": "V33", "exe": "V34", "his": "V35", "prg": "V36",
        }
        resolved_id = WF_TO_SKILL.get(skill_id.lower(), skill_id)
        normalized = self._normalize_id(resolved_id)

        # SKILL.md ファイルパスを解決
        skill_path = self._find_skill_file(normalized)

        # フォールバック: DEFAULT_PATHS で見つからない場合、C_技能｜Skills を rglob 探索
        if not skill_path:
            _fb = Path(__file__).resolve().parents[4] / "10_知性｜Nous" / "02_手順｜Procedures" / "C_技能｜Skills"
            if _fb.exists():
                # エイリアス解決: O1→V01 等の候補を含める
                _candidates = {normalized}
                if normalized in self._id_aliases:
                    _candidates.add(self._id_aliases[normalized])
                if normalized in self._id_reverse:
                    _candidates.add(self._id_reverse[normalized])
                for _skill_md in _fb.rglob("*/SKILL.md"):
                    _dir_upper = _skill_md.parent.name.upper()
                    if any(_dir_upper.startswith(c) for c in _candidates):
                        skill_path = _skill_md
                        break

        if not skill_path or not skill_path.exists():
            return ""

        try:
            raw = skill_path.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            return ""

        # Phase-U対応 ブロックを抽出 — 2つのフォーマットに対応
        # パターン1 (I/A 3行形式): "Phase-U対応 (Purge/Build/Audit 3層):" + 改行 + Purge/Build/Audit 行
        phase_u_match = re.search(
            r"Phase-U対応[^\n]*:\s*\n((?:[ \t]+(?:Purge|Build|Audit):.*\n?)+)",
            raw,
        )
        # パターン2 (S極1行形式): "Phase-U: Purge=P-0(...) / Build=... / Audit=..."
        if not phase_u_match:
            phase_u_match = re.search(
                r"Phase-U:\s*(Purge=.*(?:/\s*(?:Build|Audit)=.*)+)",
                raw,
            )
        if not phase_u_match:
            return ""

        phase_u_text = phase_u_match.group(0).strip()

        # 構造化出力: Phase 実行時のプロンプト注入用
        lines = [
            "### 🧠 Phase-U 認知制御 (環境強制)",
            "",
            "各 Phase で以下の認知操作を適用せよ:",
            f"```",
            phase_u_text,
            f"```",
            "",
            "> Purge = バイアス/prior の忘却 (U 成分)",
            "> Build = 構造の構築/再構成 (N/F 成分)",
            "> Audit = 品質検証 (Dokimasia)",
            "",
        ]
        return "\n".join(lines)

    # PURPOSE: compile-only パス向けの Phase 分解実行指示を生成する
    def build_phase_instructions(
        self,
        skill_id: str,
        depth: str = "L2",
        context: str = "",
        derivative: str = "",
    ) -> str:
        """WF の Phase を分解し、逐次実行指示 + 品質強制プリアンブルを生成する。

        hermeneus の compile-only パスで raw_content を丸ごと渡す代わりに、
        各 Phase の独立プロンプトと品質強制ルールを構造化テキストとして返す。

        目的: Claude が 600 行の WF を「読んだつもり」で echo (パラフレーズ) する
        問題を環境強制で解決する。Phase ごとの指示に分解し、各 Phase の完了条件を明示する。

        Args:
            skill_id: Skill ID (例: "V05", "noe")
            depth: 実行深度 (L0-L3)
            context: 実行コンテキスト (前 Phase の出力等)
            derivative: 派生モード名 (例: "struct")

        Returns:
            Phase 分解テキスト (Phase が見つからない場合は空文字列)
        """
        # WF 短縮名 → Skill ID 変換
        WF_TO_SKILL = {
            "noe": "O1", "bou": "O2", "zet": "O3", "ene": "O4",
            "ske": "V05", "sag": "V06", "pei": "V07", "tek": "V08",
            "kat": "V09", "epo": "V10", "pai": "V11", "dok": "V12",
            "lys": "V13", "ops": "V14", "akr": "V15", "arh": "V16",
            "beb": "V17", "ele": "V18", "kop": "V19", "dio": "V20",
            "hyp": "V21", "prm": "V22", "ath": "V23", "par": "V24",
            "the": "V25", "ant": "V26", "ere": "V27", "agn": "V28",
            "sap": "V29", "ski": "V30", "prs": "V31", "per": "V32",
            "apo": "V33", "exe": "V34", "his": "V35", "prg": "V36",
        }
        resolved_id = WF_TO_SKILL.get(skill_id.lower(), skill_id)
        skill = self.get(resolved_id)
        if not skill:
            return ""

        phases = skill.get_execution_plan(derivative=derivative, depth=depth)
        if not phases:
            return ""

        total_phases = len(phases)
        is_implementation_report = resolved_id == "O4"

        def _infer_representation_role(phase: PhaseDefinition) -> str:
            phase_key = f"{phase.name} {phase.raw_content}".lower()
            if any(token in phase_key for token in ("prolegomena", "target", "selection", "scope", "入口", "対象")):
                return "対象固定 / prior 棚卸し / SOURCE 整列"
            if any(token in phase_key for token in ("excavation", "premise", "前提", "assumption", "axiom")):
                return "前提棚卸し / AXIOM-ASSUMPTION 分離 / 論点在庫"
            if any(token in phase_key for token in ("diaphaneia", "analysis", "構造", "透徹", "bond", "結合")):
                return "構造透視 / 比較表 / 結合分析 / 溶解記録"
            if any(token in phase_key for token in ("kalon", "factor", "axiom", "因子", "普遍")):
                return "因子分解 / 公理テスト / 普遍候補"
            if any(token in phase_key for token in ("synthesis", "統合", "convergence", "収束")):
                return "収束命題 / 統合洞察 / 収斂ノード"
            if any(token in phase_key for token in ("dokimasia", "verify", "audit", "忠実性", "反論", "検証")):
                return "反論台帳 / 保存検証 / rejection_ledger"
            if any(token in phase_key for token in ("theoria", "output", "保存", "yoneda", "projection")):
                return "波及先 / WM / 次アクション / handoff"
            return "phase 固有の native artifact"

        def _implementation_renderer_template() -> List[str]:
            return [
                "### 🧭 実装報告 Renderer Policy (reader-facing artifact)",
                "",
                "| 面 | 既定 renderer | 目的 |",
                "|---|---|---|",
                "| 成果核 | 短い段落 | 何が変わったかを最短で固定する |",
                "| 変更面 | 表 | どのファイルを、何のために触ったかを一覧化する |",
                "| 検証 | fenced code block + 判定文 | 機械的証拠を本文から分離する |",
                "| 偏差 | 対比段落 | 計画との差を短く固定する |",
                "| 復元 | rollback 段落 | 戻し方と撤退条件を残す |",
                "| annex | path table | raw absolute path を本文から隔離する |",
                "",
                "> [!IMPORTANT]",
                "> unordered list を default renderer にしてはならない。",
                "> 実装報告では、まず段落・表・code block・annex を選ぶこと。",
                "> 箇条書きは skill が checklist/progress marker を native に要求する場合のみ許可。",
                "",
                "```text",
                "[Implementation Report Template]",
                "成果核:",
                "  2-4 文の短い段落で、変更の核と効能を閉じる",
                "",
                "変更面:",
                "  表で出す。列の目安 = path | intent | change",
                "",
                "検証:",
                "  実行コマンドは fenced code block、結果は直後の短い判定文",
                "",
                "偏差:",
                "  計画との差がある場合のみ、対比段落で出す",
                "",
                "復元:",
                "  rollback 条件と戻し方を 1 段落で出す",
                "",
                "annex:",
                "  raw absolute path は本文に散らさず、最後にまとめる",
                "```",
                "",
            ]

        # 品質強制プリアンブル — echo (パラフレーズ) の環境的禁止
        lines = [
            "### 🎯 Phase 分解実行指示 (品質強制・環境注入)",
            "",
            f"**Skill**: {skill.id} {skill.name} | **深度**: {depth} | **Phase 数**: {total_phases}",
            "",
            "> [!CAUTION]",
            "> **以下の7ルールは省略禁止 (環境強制)**:",
            "> 1. **CHECKPOINT 出力義務**: 各 Phase 終了時に `[CHECKPOINT PHASE X/{total_phases}]` を出力",
            "> 2. **独自調査義務**: 各 Phase で最低1つのツール呼出 (view_file, grep_search, mneme search 等) を含める。入力のパラフレーズだけの Phase = echo = 品質ゼロ",
            "> 3. **anti-echo**: 入力テキストを再構成して返すのではなく、ツールで得た新情報を基に分析・判断すること",
            "> 4. **Trace 義務**: 各 Phase で `なぜ/根拠/前Phaseから何を受け取り何を変換したか` を少なくとも1つ残すこと",
            "> 5. **Negativa 義務**: 候補・仮説・前提・代替案がある場合、少なくとも1つの非採用/棄却理由を残すこと",
            "> 6. **Iso 義務**: WF が表・ラベル・S[x.y]・NQS/AQS・WM・箱組みを要求する場合、説明文に潰さず native artifact として保存すること",
            "> 7. **累積義務**: 後続 Phase は前 Phase のラベル・候補・決定語彙を維持し、唐突にリセットしないこと",
            "> 8. **representation_role 義務**: 各 Phase は自分の表現役割 (棚卸し / 比較 / 収束 / 監査 / WM 等) を守り、全 Phase を同じ prose に均すな",
            "> 9. **rejection_ledger 義務**: 候補・前提・代替案が複数あるなら `棄却台帳 / rejection_ledger` を残すこと",
            "> 10. **carry-forward manifest 義務**: 各 Phase 末に `received / transformed / to_next` を明示し、phase 間の受け渡しを可視化すること",
            "",
        ]

        # 派生モード情報
        if derivative:
            deriv = skill.get_derivative(derivative)
            if deriv:
                lines.extend([
                    f"**派生モード**: {deriv.name} — {deriv.description}",
                    "",
                ])

        if is_implementation_report:
            lines.extend(_implementation_renderer_template())

        lines.append("---")
        lines.append("")

        # 各 Phase の実行指示を生成
        for i, phase in enumerate(phases):
            representation_role = _infer_representation_role(phase)
            phase_prompt = phase.to_prompt(
                skill_id=skill.id,
                skill_name=skill.name,
                context=context if i == 0 else "",
            )
            lines.extend([
                f"#### 📌 PHASE {phase.number}: {phase.name}",
                "",
                f"**representation_role**: {representation_role}",
                "",
                phase_prompt,
                "",
                "> 出力末尾に次の mini-manifest を付けること:",
                "> ```text",
                "> [Carry-Forward Manifest]",
                "> received: 前 Phase から受け取ったラベル / 候補 / 中間結論",
                "> transformed: この Phase で追加・更新・圧縮・検証した内容",
                "> to_next: 次 Phase に持ち越すラベル / 決定 / 未解決点",
                "> ```",
                "> 候補や前提を捨てた場合は次を追加:",
                "> ```text",
                "> [Rejection Ledger]",
                "> rejected: 非採用にした候補 / 前提 / 代替案",
                "> why_not: 棄却理由",
                "> ```",
                f"> Phase {phase.number} 完了後、`[CHECKPOINT PHASE {phase.number}/{total_phases}]` を出力してから次へ進め。",
                f"> 次 Phase では Phase {phase.number} の固有語・候補・棄却理由・中間結論を必ず引き継げ。",
                "",
                "---",
                "",
            ])

        # 最終指示
        lines.extend([
            "### ✅ 全 Phase 完了後",
            "",
            "1. 品質スコア (QS) を出力 (SKILL 定義に QS テンプレートがある場合)",
            "2. WF が WM/NQS/AQS/盲点/残差/次アクションを要求する場合、省略せず native 形式で出力",
            "3. skill 本来の終端 artifact を prose summary に潰さず、そのまま閉じる",
            "4. `→次:` で次のアクションを提案 (なぜ: {1行理由})",
            "5. `[主観]` で全体への批評を添える",
            "6. O4 実装報告では `成果核 / 変更面 / 検証 / 偏差 / 復元 / annex` の面を保ち、unordered list に流すな",
            "",
        ])

        return "\n".join(lines)


# =============================================================================
# Convenience Functions
# =============================================================================

_default_registry: Optional[SkillRegistry] = None

# PURPOSE: デフォルトレジストリを取得
def get_default_skill_registry() -> SkillRegistry:
    """デフォルト SkillRegistry を取得"""
    global _default_registry
    if _default_registry is None:
        _default_registry = SkillRegistry()
    return _default_registry


# PURPOSE: Skill 定義を取得 (便利関数)
def get_skill(skill_id: str) -> Optional[SkillDefinition]:
    """Skill 定義を取得 (便利関数)"""
    return get_default_skill_registry().get(skill_id)


# PURPOSE: 全 Skill ID 一覧を取得 (便利関数)
def list_skills() -> List[str]:
    """全 Skill ID 一覧を取得 (便利関数)"""
    return get_default_skill_registry().list_ids()


# PURPOSE: 全 Skill の詳細一覧を取得 (ClawX fetchSkills() 相当)
def list_all_skills() -> List[Dict[str, Any]]:
    """全 Skill の詳細一覧を取得 (state 含む)
    
    ClawX mapping: stores/skills.ts fetchSkills() の
    3 層マージ (Gateway + ClawHub + Config) に対応。
    HGK: SKILL.md (定義) + skill_state.json (状態) の 2 層マージ。
    """
    registry = get_default_skill_registry()
    all_skills = registry.load_all()
    
    try:
        from hermeneus.src.skill_state import SkillStateStore
        store = SkillStateStore()
        states = store.get_all_states()
    except Exception:  # noqa: BLE001
        states = {}
    
    result = []
    for skill_id, skill in sorted(all_skills.items()):
        skill_state = states.get(skill_id, {})
        result.append({
            "id": skill.id,
            "name": skill.name,
            "family": skill.family,
            "version": skill.version,
            "is_core": skill.is_core,
            "is_bundled": skill.is_bundled,
            "enabled": skill_state.get("enabled", True),
            "has_config": bool(skill.config_schema),
            "config": skill_state.get("config", {}),
            "phases": len(skill.phases),
            "derivatives": [d.name for d in skill.derivatives],
        })
    return result


# PURPOSE: スキルの enable/disable (便利関数)
def set_skill_enabled(skill_id: str, enabled: bool) -> None:
    """スキルの enable/disable を設定 (便利関数)
    
    ClawX mapping: ipcMain.handle('skill:toggle') →
      skill-config.ts updateSkillConfig()
    """
    registry = get_default_skill_registry()
    skill = registry.get(skill_id)
    is_core = skill.is_core if skill else False
    
    from hermeneus.src.skill_state import SkillStateStore
    store = SkillStateStore()
    store.set_skill_enabled(skill_id, enabled, is_core=is_core)
