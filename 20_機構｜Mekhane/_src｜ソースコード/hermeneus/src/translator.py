# PROOF: [L2/インフラ] <- hermeneus/src/translator.py CCL → LMQL 翻訳器
"""
Hermēneus Translator — AST を LMQL プログラムに変換

PoC (mekhane/ccl/lmql_translator.py) から正式版へリファクタ。
SEL (Semantic Enforcement Layer) 義務を LMQL 制約に変換。

Origin: 2026-01-31 CCL Execution Guarantee Architecture
"""

from typing import Any
from .ccl_ast import (
    OpType, Workflow, MacroRef,
    ConvergenceLoop, Sequence, Fusion, Oscillation,
    ForLoop, IfCondition, WhileLoop, Lambda, ModifierPeras
)


# =============================================================================
# Workflow Prompts
# =============================================================================

WORKFLOW_PROMPTS = {
    # Telos Series
    "noe": "深い認識 (Noēsis): 以下について多角的に分析し、本質を把握してください。",
    "o1": "深い認識 (Noēsis): 以下について多角的に分析し、本質を把握してください。",
    "bou": "意志確認 (Boulēsis): あなたは何を望んでいますか？目的を明確にしてください。",
    "o2": "意志確認 (Boulēsis): あなたは何を望んでいますか？目的を明確にしてください。",
    "zet": "問い発見 (Zētēsis): 何を問うべきですか？重要な問いを発見してください。",
    "o3": "問い発見 (Zētēsis): 何を問うべきですか？重要な問いを発見してください。",
    "ene": "実行 (Energeia): 以下を具体的なステップで実行してください。",
    "o4": "実行 (Energeia): 以下を具体的なステップで実行してください。",
    
    # Methodos Series
    "ske": "探索 (Skepsis): 仮説空間を拡げ、前提を破壊してください。",
    "sag": "統合 (Synagōgē): 仮説空間を絞り込み、最適構造を統合してください。",
    "pei": "実験 (Peira): 未知領域で情報を集め、仮説を実験で検証してください。",
    "tek": "構築 (Tekhnē): 既知の手法を使って確実に成果を出してください。",
    
    # Orexis Series
    "dia": "判定 (Krisis): 以下を批判的に評価してください。",
    "a2": "判定 (Krisis): 以下を批判的に評価してください。",
    
    # Chronos Series
    "sop": "調査 (Sophia): 以下について詳細に調査してください。",
    "k4": "調査 (Sophia): 以下について詳細に調査してください。",
    
    # Meta
    "u": "主観的意見: あなたの本音を述べてください。",
    "syn": "評議会 (Synedrion): 複数の視点から批評してください。",
    "pan": "パノラマ: 盲点を発見し、メタ認知を実行してください。",
}

# 演算子 → LMQL 制約
OPERATOR_CONSTRAINTS = {
    OpType.DEEPEN: {
        "instruction": "詳細に、3つ以上の視点で、根拠を明示して",
        "constraint": "len(RESULT) > 500 and '理由' in RESULT",
    },
    OpType.CONDENSE: {
        "instruction": "簡潔に、要点のみ、3文以内で",
        "constraint": "len(RESULT) < 300",
    },
    OpType.ASCEND: {
        "instruction": "メタ的に、前提を検証しながら",
        "constraint": "'前提' in RESULT or 'メタ' in RESULT",
    },
    OpType.INVERT: {
        "instruction": "批判的に、反対の視点から",
        "constraint": "'しかし' in RESULT or '問題' in RESULT",
    },
    OpType.EXPAND: {
        "instruction": "全ての派生を網羅的に",
        "constraint": "len(RESULT) > 800",
    },
}


# 修飾座標パラメータ → LMQL 指示 (v4.1 Dokimasia)
# 各プロンプトは出力の構造・形式・焦点を具体的に変える
MODIFIER_PROMPTS = {
    "Va": {
        "E": (
            "【Value:認識 (Epistemic)】\n"
            "- 目的: 真理の探求と認識の深化。実用性は度外視してよい\n"
            "- 出力形式: 概念の定義→構造分析→本質の抽出→普遍性の検証\n"
            "- 問い: 「これは何か」「なぜそうなのか」「どこまで一般化できるか」\n"
            "- 禁止: 「〜すべき」「〜に役立つ」等の実用的判断"
        ),
        "P": (
            "【Value:実用 (Pragmatic)】\n"
            "- 目的: 即座に行動に移せる具体的な出力。抽象論は排除\n"
            "- 出力形式: 結論→手順→チェックリスト→実行コマンド\n"
            "- 問い: 「何をすればよいか」「いつまでに」「リスクは何か」\n"
            "- 禁止: 学術的な議論、歴史的背景の長い説明"
        ),
    },
    "Fu": {
        "Explore": (
            "【Function:探索 (Explore)】\n"
            "- 目的: 既存の枠組みを壊し、可能な限り広い選択肢を発散させる\n"
            "- 出力形式: 仮説A / 仮説B / 仮説C... (最低3つ)。各仮説に「なぜありえるか」を1行\n"
            "- 制約: 最初に思いついた案に固執しない。「他にないか？」を3回自問する\n"
            "- 推奨: 異分野からのアナロジー、反直感的な選択肢も含める"
        ),
        "Exploit": (
            "【Function:活用 (Exploit)】\n"
            "- 目的: 確立された最善の方法を選び、確実に実行する\n"
            "- 出力形式: 最適解→根拠→実行手順→品質基準\n"
            "- 制約: 新しい方法を試みない。既知のベストプラクティスのみ使用\n"
            "- 推奨: 過去の成功事例、公式ドキュメント、テスト済みの手法を参照"
        ),
    },
    "Pr": {
        "C": (
            "【Precision:確信 (Confident)】\n"
            "- 目的: 曖昧さを完全に排除し、明確な結論を出す\n"
            "- 出力形式: 「Xである」の断定形。根拠を1つ以上添える\n"
            "- 制約: 「〜かもしれない」「〜の可能性がある」を使わない\n"
            "- N-10連携: [確信: 90%+] ラベルを付与できる内容のみ出力"
        ),
        "U": (
            "【Precision:留保 (Uncertain)】\n"
            "- 目的: 複数の可能性を保持し、早計な結論を避ける\n"
            "- 出力形式: 「可能性1 (条件A), 可能性2 (条件B), ...」の並記\n"
            "- 制約: 1つの正解を選ばない。各可能性の条件と確率を明示\n"
            "- N-10連携: [仮説] または [推定] ラベルで確信度を明示"
        ),
    },
    "Sc": {
        "Mi": (
            "【Scale:微視 (Micro)】\n"
            "- 目的: 1つの要素を極限まで深掘りする\n"
            "- 出力形式: 対象の内部構造→構成要素→各要素の振る舞い→エッジケース\n"
            "- スコープ: 関数1つ、定義1つ、概念1つ。隣接する要素には触れない\n"
            "- 禁止: 「全体としては...」「アーキテクチャ的には...」等の俯瞰"
        ),
        "Ma": (
            "【Scale:巨視 (Macro)】\n"
            "- 目的: 全体の構造と関係性を俯瞰する\n"
            "- 出力形式: 構成要素の一覧→関係図→依存関係→全体の傾向\n"
            "- スコープ: システム全体、プロジェクト全体、概念体系全体\n"
            "- 禁止: 個別の実装詳細、1行のコード修正、局所的な問題"
        ),
    },
    "Vl": {
        "+": (
            "【Valence:肯定 (+)】\n"
            "- 目的: 対象の強み・長所・成功要因を引き出す\n"
            "- 出力形式: 強み1→なぜ強みか→どう伸ばすか / 強み2→...\n"
            "- 制約: 問題点への言及は最小限に。「これをさらに良くするには」の視点\n"
            "- Bebaiōsis (V17) の姿勢で接する"
        ),
        "-": (
            "【Valence:否定 (-)】\n"
            "- 目的: 対象の弱み・欠陥・矛盾・リスクを厳しく指摘する\n"
            "- 出力形式: 問題1→根拠→影響範囲→是正案 / 問題2→...\n"
            "- 制約: 良い点への言及は不要。「何が壊れているか」の視点\n"
            "- Elenchos (V18) の姿勢で接する"
        ),
    },
    "Te": {
        "Past": (
            "【Temporality:過去 (Past)】\n"
            "- 目的: 歴史・前例・蓄積された経験から学ぶ\n"
            "- 出力形式: 過去の事例→そこから得られた教訓→現在への適用\n"
            "- 情報源: Handoff, KI, パターンDB, 過去のセッション記録\n"
            "- 問い: 「前にどうだったか」「何を学んだか」「同じ轍を踏んでいないか」"
        ),
        "Future": (
            "【Temporality:未来 (Future)】\n"
            "- 目的: まだ起きていない事態を予測し、先手を打つ\n"
            "- 出力形式: シナリオA (確率高) / シナリオB (確率中) / シナリオC (確率低) + 各シナリオへの先制行動\n"
            "- 制約: 現状の延長だけでなく、不連続な変化も想定する\n"
            "- 問い: 「6ヶ月後にどうなっているか」「最悪のケースは」「今打てる手は」"
        ),
    }
}

# WFごとのデフォルト修飾子 (v4.1)
# workflow_defaults.py から再エクスポート (ccl_ast 非依存の軽量モジュール)
from .workflow_defaults import WORKFLOW_DEFAULT_MODIFIERS  # noqa: F401


# PURPOSE: [L2-auto] CCL AST → LMQL プログラム変換
class LMQLTranslator:
    """CCL AST → LMQL プログラム変換"""
    
    # PURPOSE: Initialize instance
    def __init__(self, model: str = "openai/gpt-4o"):
        self.model = model
    
    # PURPOSE: AST を LMQL プログラムに変換
    def translate(self, ast: Any) -> str:
        """AST を LMQL プログラムに変換"""
        if isinstance(ast, ConvergenceLoop):
            return self._translate_convergence(ast)
        elif isinstance(ast, Sequence):
            return self._translate_sequence(ast)
        elif isinstance(ast, Fusion):
            return self._translate_fusion(ast)
        elif isinstance(ast, Oscillation):
            return self._translate_oscillation(ast)
        elif isinstance(ast, ForLoop):
            return self._translate_for(ast)
        elif isinstance(ast, IfCondition):
            return self._translate_if(ast)
        elif isinstance(ast, WhileLoop):
            return self._translate_while(ast)
        elif isinstance(ast, Lambda):
            return self._translate_lambda(ast)
        elif isinstance(ast, MacroRef):
            return self._translate_macro(ast)
        elif isinstance(ast, ModifierPeras):
            return self._translate_modifier_peras(ast)
        elif isinstance(ast, Workflow):
            return self._translate_workflow(ast)
        else:
            raise ValueError(f"Unknown AST node: {type(ast)}")
    
    # PURPOSE: 修飾子空間の Peras (ドットサフィックス) を LMQL に変換
    def _translate_modifier_peras(self, node: ModifierPeras) -> str:
        """修飾子空間の Peras (ドットサフィックス) を LMQL に変換"""
        base_id = node.base_wf.id
        coords = node.coordinates
        preset = node.preset_name
        
        # どの座標を展開するか決定
        if preset:
            desc = f"プリセット '{preset}' の適用"
            # プリセット展開: parser 側で bracket_modifiers に変換済みなので、
            # 実行時は通常の WF 実行と同じ扱いになるが、
            # ax演算子として評価プロセス (C1-C3) も回す
            targets = [preset]
        elif not coords:
            desc = "全6座標 (Va, Fu, Pr, Sc, Vl, Te) の全極展開と対比"
            targets = ["Va", "Fu", "Pr", "Sc", "Vl", "Te"]
        else:
            desc = f"指定座標 ({', '.join(coords)}) の極展開と対比"
            targets = coords
            
        steps = []
        for target in targets:
            steps.append(f'        "【{target} 座標の分析】"\n        "[{target}_RESULT]"')
            steps.append(f'        where len({target}_RESULT) > 50')
            
        steps_str = "\n".join(steps)
        
        return f'''
# CCL Modifier Peras: {base_id}.ax
# 説明: {desc}

import lmql

@lmql.query
def modifier_peras_execution(context: str):
    """修飾子空間の Peras 実行"""
    argmax
        "コンテキスト: {{context}}"
        "ワークフロー /{base_id} を修飾子空間で多角的に展開し、最適なアプローチを探索します。"
        
{steps_str}

        "⊕ C1: 対比 (Contrast) — 各座標の Limit 出力の比較"
        "[C1_CONTRAST]"
        where len(C1_CONTRAST) > 100
        
        "⊕ C2: 解消 (Resolve) — 座標間の矛盾と調停"
        "[C2_RESOLVE]"
        where len(C2_RESOLVE) > 100
        
        "⊕ C3: 検証 (Verify) — 最適な修飾子配置の推奨"
        "[C3_VERIFY]"
        where len(C3_VERIFY) > 50
        
        "最終推奨プリセット: [FINAL_PRESET]"
    from
        "{self.model}"
'''

    
    # PURPOSE: マクロ参照を LMQL に変換（Synteleia 統合）
    def _translate_macro(self, macro: MacroRef) -> str:
        """マクロ参照を LMQL に変換（Synteleia 統合）"""
        name = macro.name
        args = macro.args
        
        # Synteleia マクロ: @syn, @syn·, @syn×, @poiesis, @dokimasia, @S
        if name in ("syn", "syn·", "poiesis", "dokimasia", "S"):
            return self._translate_synteleia_macro(name, args)
        
        # 一般マクロ: ビルトインまたはユーザー定義
        return f'''
# CCL マクロ: @{name}
# TODO: マクロ展開 → 他の CCL 式に変換
@lmql.query
def macro_{name}(context: str):
    """マクロ @{name} の実行"""
    argmax
        "マクロ @{name} を実行: コンテキスト: {{context}}"
        "[RESULT]"
    from
        "{self.model}"
'''
    
    # PURPOSE: Synteleia マクロを LMQL + Python に変換
    def _translate_synteleia_macro(self, name: str, args: list) -> str:
        """Synteleia マクロを LMQL + Python に変換"""
        # 層選択を決定
        if name == "poiesis":
            layers = "poiesis_only=True"
            desc = "生成層 (O,S,H) のみ"
        elif name == "dokimasia":
            layers = "dokimasia_only=True"
            desc = "審査層 (P,K,A) のみ"
        elif name == "S" and args:
            # @S{O,A,K} 形式: 特定エージェント選択
            agents_str = args[0] if args else "O,S,H,P,K,A"
            agents_list = agents_str.replace(',', "', '")
            layers = f"agents=['{agents_list}']"
            desc = f"選択エージェント: {agents_str}"
        else:
            # @syn または @syn· (内積)
            layers = ""
            desc = "全エージェント (内積モード)"
        
        return f'''
# CCL Synteleia: @{name}
# 説明: {desc}

from mekhane.synteleia.orchestrator import SynteleiaOrchestrator
from mekhane.synteleia.base import AuditTarget, AuditTargetType

def synteleia_audit(context: str):
    \"\"\"Synteleia 監査を実行\"\"\"
    orch = SynteleiaOrchestrator({layers})
    target = AuditTarget(
        content=context,
        target_type=AuditTargetType.GENERIC
    )
    result = orch.audit(target)
    return orch.format_report(result)

# LMQL 統合
@lmql.query
def synteleia_integrated(context: str):
    \"\"\"Synteleia 統合監査\"\"\"
    argmax
        # Python 関数呼び出し
        audit_result = synteleia_audit(context)
        "Synteleia 監査結果:\\n{{audit_result}}"
        "分析と推奨: [ANALYSIS]"
    where
        len(ANALYSIS) > 100
    from
        "{self.model}"
'''
    
    # PURPOSE: Lambda を LMQL に変換
    def _translate_lambda(self, node: Lambda) -> str:
        """Lambda を LMQL に変換"""
        params = ", ".join(node.params)
        return f'''
# CCL Lambda: L:[{params}]{{body}}
@lmql.query
def lambda_execution({params}, context: str):
    \"\"\"CCL Lambda 実行\"\"\"
    argmax
        "Lambda パラメータ: {params}"
        "コンテキスト: {{context}}"
        "[RESULT]"
    from
        "{self.model}"
'''
    
    # PURPOSE: ワークフローを LMQL に変換
    def _translate_workflow(self, wf: Workflow) -> str:
        """ワークフローを LMQL に変換"""
        prompt = WORKFLOW_PROMPTS.get(wf.id, f"/{wf.id} を実行:")
        
        # 演算子による修飾
        instructions = []
        constraints = []
        
        for op in wf.operators:
            if op in OPERATOR_CONSTRAINTS:
                spec = OPERATOR_CONSTRAINTS[op]
                instructions.append(spec["instruction"])
                constraints.append(spec["constraint"])
        
        # v4.1 修飾子 (Dokimasia) — デフォルト + ユーザー指定のマージ
        # ユーザー指定がデフォルトを上書き
        effective_modifiers = {}
        if wf.id in WORKFLOW_DEFAULT_MODIFIERS:
            effective_modifiers.update(WORKFLOW_DEFAULT_MODIFIERS[wf.id])
        if wf.modifiers:
            effective_modifiers.update(wf.modifiers)  # ユーザー指定が優先
        
        modifier_instructions = []
        for mod_key, mod_value in effective_modifiers.items():
            if mod_key in MODIFIER_PROMPTS and mod_value in MODIFIER_PROMPTS[mod_key]:
                modifier_instructions.append(f'        "{MODIFIER_PROMPTS[mod_key][mod_value]}"')
            elif not isinstance(mod_value, int):
                # 旧形式 (a1:2) は無視、文字列値のみプロンプト化
                modifier_instructions.append(f'        "追加制約: {mod_key}={mod_value}"')
        
        instruction_str = "。".join(instructions) if instructions else ""
        constraint_str = " and ".join(constraints) if constraints else "len(RESULT) > 100"
        
        # モード追加
        mode_str = f" モード: {wf.mode}" if wf.mode else ""
        
        # Q4: 出力テンプレートの埋め込み (WF → SKILL フォールバック)
        template_instruction = ""
        tmpl_content = None
        try:
            # 1st: WorkflowRegistry から外部テンプレートファイルを参照
            from hermeneus.src.registry import get_workflow
            wf_def = get_workflow(wf.id)
            if wf_def and wf_def.metadata.get("output_template"):
                tmpl_path = wf_def.metadata.get("output_template")
                if wf_def.source_path:
                    tmpl_file = wf_def.source_path.parent / tmpl_path
                    # もし存在しなければ、親ディレクトリを遡って探す (nous 等を含む相対パス対応)
                    if not tmpl_file.exists():
                        for p in wf_def.source_path.parents:
                            if (p / tmpl_path).exists():
                                tmpl_file = p / tmpl_path
                                break
                    if tmpl_file.exists():
                        tmpl_content = tmpl_file.read_text(encoding="utf-8").strip()
            
            # 2nd: WF定義の skill_ref から SKILL.md を直接読み、
            #      「統合出力形式」セクション内の code block を正規表現で軽量抽出
            if not tmpl_content and wf_def:
                import re as _re
                skill_ref = wf_def.metadata.get("skill_ref", "")
                # skill_ref はリストの場合がある
                if isinstance(skill_ref, list):
                    skill_ref = skill_ref[0] if skill_ref else ""
                if skill_ref and wf_def.source_path:
                    for p in wf_def.source_path.parents:
                        skill_file = p / skill_ref
                        if skill_file.exists():
                            skill_text = skill_file.read_text(encoding="utf-8")
                            # 「統合出力形式」セクション内の code block を抽出
                            section = _re.search(
                                r"## 統合出力形式\s*\n(.*?)(?=\n## |\Z)",
                                skill_text, _re.DOTALL
                            )
                            if section:
                                code_block = _re.search(
                                    r"```[^\n]*\n(.*?)```",
                                    section.group(1), _re.DOTALL
                                )
                                if code_block:
                                    tmpl_content = code_block.group(1).strip()
                            break
            
            if tmpl_content:
                # LMQL文字列として安全に埋め込むため、\ と " をエスケープ、改行を \n に変換
                safe_tmpl = tmpl_content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                template_instruction = f'\n        "【出力テンプレート (以下の形式に厳密に従うこと)】\\n{safe_tmpl}\\n"\n'
        except Exception:  # noqa: BLE001
            pass
        
        # 組み立て
        modifier_lines = "\n".join(modifier_instructions) if modifier_instructions else ""
        if modifier_lines:
            modifier_lines = "\n" + modifier_lines
        
        return f'''
@lmql.query
def ccl_{wf.id}(context: str):
    """CCL /{wf.id} の実行"""
    argmax
        "{prompt}{mode_str}"
        "{instruction_str}"{modifier_lines}{template_instruction}
        "コンテキスト: {{context}}"
        "[RESULT]"
    where
        {constraint_str}
    from
        "{self.model}"
'''
    
    # PURPOSE: 収束ループを LMQL に変換
    def _translate_convergence(self, node: ConvergenceLoop) -> str:
        """収束ループを LMQL に変換"""
        cond = node.condition
        wf_id = node.body.id if isinstance(node.body, Workflow) else "workflow"
        
        return f'''
# CCL 収束ループ: {wf_id} >> {cond.var} {cond.op} {cond.value}

import lmql

MAX_ITERATIONS = {node.max_iterations}

@lmql.query
def convergence_loop(context: str):
    """収束するまで繰り返す"""
    argmax
        V = 1.0  # 初期不確実性
        iteration = 0
        
        while V {cond.op.replace('<', '>')} {cond.value} and iteration < MAX_ITERATIONS:
            # ワークフロー実行
            "Iteration {{iteration}}: /{wf_id} を実行"
            "[STEP_RESULT]"
            where len(STEP_RESULT) > 50
            
            # 不確実性評価
            "現在の不確実性レベル (0.0-1.0): [V_ESTIMATE]"
            where V_ESTIMATE in ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9"]
            
            V = float(V_ESTIMATE)
            iteration += 1
        
        "収束完了。最終結果: [FINAL_RESULT]"
    from
        "{self.model}"
'''
    
    # PURPOSE: シーケンスを LMQL に変換
    def _translate_sequence(self, node: Sequence) -> str:
        """シーケンスを LMQL に変換"""
        steps = []
        for i, step in enumerate(node.steps):
            if isinstance(step, Workflow):
                prompt = WORKFLOW_PROMPTS.get(step.id, f"/{step.id}")
                steps.append(f'        "Step {i+1}: {prompt}"')
                steps.append(f'        "[STEP_{i}_RESULT]"')
        
        steps_str = "\n".join(steps)
        
        return f'''
@lmql.query
def sequence_execution(context: str):
    """CCL シーケンス実行"""
    argmax
        "コンテキスト: {{context}}"
{steps_str}
        "全ステップ完了。統合結果: [FINAL_RESULT]"
    from
        "{self.model}"
'''
    
    # PURPOSE: 融合を LMQL に変換
    def _translate_fusion(self, node: Fusion) -> str:
        """融合を LMQL に変換"""
        left_id = node.left.id if isinstance(node.left, Workflow) else "A"
        right_id = node.right.id if isinstance(node.right, Workflow) else "B"
        
        meta_instruction = ""
        if node.meta_display:
            meta_instruction = '"[META_EXPLANATION]"\nwhere len(META_EXPLANATION) > 100 and "融合" in META_EXPLANATION'
        
        return f'''
@lmql.query
def fusion_execution(context: str):
    """CCL 融合: {left_id} * {right_id}"""
    argmax
        "コンテキスト: {{context}}"
        "/{left_id} と /{right_id} を融合して実行:"
        "[FUSED_RESULT]"
        {meta_instruction}
    where
        len(FUSED_RESULT) > 200
    from
        "{self.model}"
'''
    
    # PURPOSE: 振動を LMQL に変換
    def _translate_oscillation(self, node: Oscillation) -> str:
        """振動を LMQL に変換"""
        left_id = node.left.id if isinstance(node.left, Workflow) else "A"
        right_id = node.right.id if isinstance(node.right, Workflow) else "B"
        
        return f'''
@lmql.query
def oscillation_execution(context: str):
    """CCL 振動: {left_id} ~ {right_id}"""
    argmax
        "コンテキスト: {{context}}"
        
        "Phase 1: /{left_id} を実行"
        "[PHASE_1_RESULT]"
        
        "Phase 2: /{right_id} の視点から Phase 1 を検証・拡張"
        "[PHASE_2_RESULT]"
        
        "Phase 3: 両視点を統合した最終結果"
        "[FINAL_RESULT]"
    where
        len(FINAL_RESULT) > 300
    from
        "{self.model}"
'''
    
    # PURPOSE: FOR ループを LMQL に変換
    def _translate_for(self, node: ForLoop) -> str:
        """FOR ループを LMQL に変換"""
        if isinstance(node.iterations, int):
            iter_desc = f"{node.iterations}回"
        else:
            iter_desc = f"各要素 {node.iterations}"
        
        return f'''
@lmql.query
def for_loop_execution(context: str):
    """CCL FOR ループ: {iter_desc}"""
    argmax
        "コンテキスト: {{context}}"
        # 反復実行
        for i in range({node.iterations if isinstance(node.iterations, int) else len(node.iterations)}):
            "反復 {{i+1}}: "[ITER_RESULT]"
            where len(ITER_RESULT) > 50
        
        "全反復完了。統合結果: [FINAL_RESULT]"
    from
        "{self.model}"
'''
    
    # PURPOSE: IF 条件分岐を LMQL に変換
    def _translate_if(self, node: IfCondition) -> str:
        """IF 条件分岐を LMQL に変換"""
        cond = node.condition
        
        return f'''
@lmql.query
def if_condition_execution(context: str, {cond.var.replace("[]", "")}: float):
    """CCL IF 条件分岐: {cond.var} {cond.op} {cond.value}"""
    argmax
        "コンテキスト: {{context}}"
        
        if {cond.var.replace("[]", "")} {cond.op} {cond.value}:
            "条件成立: THEN ブランチを実行"
            "[THEN_RESULT]"
        else:
            "条件不成立: ELSE ブランチを実行"
            "[ELSE_RESULT]"
    from
        "{self.model}"
'''
    
    # PURPOSE: WHILE ループを LMQL に変換
    def _translate_while(self, node: WhileLoop) -> str:
        """WHILE ループを LMQL に変換"""
        cond = node.condition
        
        return f'''
@lmql.query
def while_loop_execution(context: str):
    """CCL WHILE ループ: {cond.var} {cond.op} {cond.value}"""
    argmax
        "コンテキスト: {{context}}"
        {cond.var.replace("[]", "")} = 1.0
        iteration = 0
        MAX_ITER = 10
        
        while {cond.var.replace("[]", "")} {cond.op} {cond.value} and iteration < MAX_ITER:
            "反復 {{iteration}}: "[ITER_RESULT]"
            "現在値: [{cond.var.replace("[]", "")}_EST]"
            where {cond.var.replace("[]", "")}_EST in ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9"]
            {cond.var.replace("[]", "")} = float({cond.var.replace("[]", "")}_EST)
            iteration += 1
        
        "ループ完了。最終結果: [FINAL_RESULT]"
    from
        "{self.model}"
'''


# =============================================================================
# Convenience Function
# =============================================================================

# PURPOSE: AST を LMQL に変換 (便利関数)
def translate_to_lmql(ast: Any, model: str = "openai/gpt-4o") -> str:
    """AST を LMQL に変換 (便利関数)"""
    translator = LMQLTranslator(model=model)
    return translator.translate(ast)
