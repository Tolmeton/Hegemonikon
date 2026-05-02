# pyre-ignore-all-errors
# PROOF: [L3/インフラ] <- hermeneus/src/parser.py Hermēneus CCL パーサー
"""
Hermēneus CCL Parser

CCL (Cognitive Control Language) 式を AST に変換するパーサー。
再帰下降法 + 演算子優先度パース。

Origin: 2026-01-31 CCL Execution Guarantee Architecture
"""

import warnings

import re
from typing import Any, List
from .ast import (
    OpType, Workflow, PreVerb, Condition, MacroRef,
    ConvergenceLoop, Sequence, Fusion, Oscillation, ColimitExpansion,
    Adjunction, Pipeline, Parallel, Morphism, OpenEnd,
    ForLoop, IfCondition, WhileLoop, Lambda, TaggedBlock, ModifierPeras, LetBinding,
    Group,
    PartialDiff, Integral, Summation,
    ErrorNode,
)


# PURPOSE: [L2-auto] CCL パーサー
class CCLParser:
    """CCL パーサー"""
    
    # 認識するワークフロー ID
    WORKFLOWS = {
        # Telos 族 (V01-V04: I/A極, V25-V26: S極)
        "noe", "bou", "zet", "ene", "o", "o1", "o2", "o3", "o4",
        "the", "ant",  # S極: Theōria (S×E), Antilepsis (S×P)
        # Methodos 族 (V05-V08: I/A極, V27-V28: S極) + 旧エイリアス
        "ske", "sag", "pei", "tek",
        "ere", "agn",  # S極: Ereuna (S×Ex), Anagnōsis (S×Ep)
        "s", "met", "mek", "sta", "pra", "s1", "s2", "s3", "s4",  # 後方互換
        # Krisis 族 (V09-V12: I/A極, V29-V30: S極) + 旧エイリアス
        "kat", "epo", "pai", "dok",
        "sap", "ski",  # S極: Saphēneia (S×C), Skiagraphia (S×U)
        "h", "pro", "pis", "ore", "dox", "h1", "h2", "h3", "h4",  # 後方互換
        # Diástasis 族 (V13-V16: I/A極, V31-V32: S極) + 旧エイリアス
        "lys", "ops", "akr", "arc",
        "prs", "per",  # S極: Prosochē (S×Mi), Perioptē (S×Ma)
        "p", "kho", "hod", "tro", "p1", "p2", "p3", "p4",  # 後方互換
        # Orexis 族 (V17-V20: I/A極, V33-V34: S極) + 旧エイリアス
        "beb", "ele", "kop", "dio",
        "apo", "exe",  # S極: Apodochē (S×+), Exetasis (S×-)
        "k", "euk", "chr", "tel", "sop", "k1", "k2", "k3", "k4",  # 後方互換
        # Chronos 族 (V21-V24: I/A極, V35-V36: S極) + 旧エイリアス
        "hyp", "prm", "ath", "par",
        "his", "prg",  # S極: Historiā (S×Pa), Prognōsis (S×Fu)
        "a", "pat", "dia", "gno", "epi", "a1", "a2", "a3", "a4",  # 後方互換
        # Meta
        "boot", "bye", "ax", "u", "syn", "pan", "pre", "poc", "why",
        "vet", "tak", "eat", "fit", "flag", "lex",
    }
    
    # H-series 前動詞（中動態）の略記 — `[xx]` 記法で使用
    PREVERBS = {
        "tr", "sy", "pa", "he", "ek", "th",
        "eu", "sh", "ho", "ph", "an", "pl",
    }
    
    # 略記 → 正式名のマッピング
    PREVERB_NAMES = {
        "tr": "Tropē",          # H1: S∩A×E — 向変
        "sy": "Synaisthēsis",   # H2: S∩A×P — 体感
        "pa": "Paidia",         # H3: S∩A×Explore — 遊戯
        "he": "Hexis",          # H4: S∩A×Exploit — 習態
        "ek": "Ekplēxis",       # H5: S∩A×C — 驚愕
        "th": "Thambos",        # H6: S∩A×U — 戸惑い
        "eu": "Euarmostia",     # H7: S∩A×Mi — 微調和
        "sh": "Synhorasis",     # H8: S∩A×Ma — 一望
        "ho": "Hormē",          # H9: S∩A×+ — 衝動
        "ph": "Phobos",         # H10: S∩A×- — 恐怖
        "an": "Anamnēsis",      # H11: S∩A×Past — 想起再現
        "pl": "Prolepsis",      # H12: S∩A×Future — 予期反射
    }
    
    # 単項演算子マッピング
    UNARY_OPS = {
        '+': OpType.DEEPEN,
        '-': OpType.CONDENSE,
        '^': OpType.ASCEND,
        '?': OpType.QUERY,
        '\\': OpType.INVERT,
        "'": OpType.DIFF,
        '!': OpType.EXPAND,
    }
    
    # 二項演算子優先順位 (低い方が先に処理)
    # v7.6: || = 随伴宣言, |>/&> 区別, <| = 左随伴
    # ~* と ~! は ~ より先にマッチさせる（長いトークン優先）
    # *% は * より先にマッチさせる（長いトークン優先）
    # 2文字演算子を1文字演算子の前に配置 (長いトークン優先)
    # <* と >% は * と % より前に、<< >> >* は > より前にマッチさせる
    BINARY_OPS_PRIORITY = ['&&', '&>', '||', '|>', '<|', '_', '~*', '~!', '~', '*^', '*%', '*>', '<*', '<<', '>%', '>*', '>>', '*', '%']
    
    # PURPOSE: Initialize instance
    def __init__(self):
        self.errors: List[str] = []
    
    # PURPOSE: Parse a CCL expression and return an AST node
    def parse(self, ccl: str) -> Any:
        """CCL 式をパース"""
        ccl = ccl.strip()
        self.errors = []
        
        try:
            return self._parse_expression(ccl)
        except Exception as e:
            self.errors.append(str(e))
            raise ValueError(f"Parse error: {e}")
    
    # PURPOSE: Parse tolerantly — return ErrorNode instead of raising
    def parse_tolerant(self, ccl: str, line: int = 0) -> Any:
        """CCL 式をパース。失敗時は例外を投げず ErrorNode を返す (LSP 用)

        Args:
            ccl:  パース対象の CCL 式
            line: ソースファイル内の行番号 (0-indexed, エラー報告用)

        Returns:
            正常時: AST ノード / 失敗時: ErrorNode
        """
        ccl = ccl.strip()
        self.errors = []
        try:
            return self._parse_expression(ccl)
        except Exception as e:
            msg = str(e)
            self.errors.append(msg)
            return ErrorNode(source=ccl, message=msg, line=line, col=0)

    # PURPOSE: Parse a multi-line .ccl file, never raises (LSP 用)
    def parse_file(self, source: str) -> List[Any]:
        """複数行 .ccl ソースをパースし、各文の AST ノードリストを返す

        行番号を保持し、エラーがあっても残りの行のパースを継続する。
        LSP の diagnostics 生成に使用する。

        Args:
            source: .ccl ファイルの全テキスト

        Returns:
            List of (line_number, ASTNode | ErrorNode)
            line_number は 1-indexed
        """
        results = []
        for lineno, raw in enumerate(source.split("\n"), start=1):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                continue
            node = self.parse_tolerant(stripped, line=lineno - 1)
            results.append((lineno, node))
        return results

    # PURPOSE: Dispatch expression to appropriate parser
    def _parse_expression(self, expr: str) -> Any:
        """式をパース (優先順位に従う)"""
        expr = expr.strip()
        
        # 式が空の場合、末尾の開放などを表す OpenEnd ノードを返す
        if not expr:
            return OpenEnd()
            
        # 括弧グループの剤離: (...) や {...} の外側が式全体を囲んでいる場合に剥がす
        if (expr.startswith('(') and expr.endswith(')') and
                self._is_balanced_group(expr, '(', ')')):
            return self._parse_expression(expr[1:-1])
        if (expr.startswith('{') and expr.endswith('}') and
                self._is_balanced_group(expr, '{', '}')):
            return self._parse_expression(expr[1:-1])
            
        # グループ修飾子: (...)+ や (...)- 形式 → Group ノードを返す
        group_mod_match = re.search(r'^\((.*)\)([\+\-\^\?\'\\!]+)$', expr)
        if group_mod_match and self._is_balanced_group(f"({group_mod_match.group(1)})", '(', ')'):
            inner = group_mod_match.group(1)
            modifiers_str = group_mod_match.group(2)
            
            body = self._parse_expression(inner)
            operators = [self.UNARY_OPS[op] for op in modifiers_str if op in self.UNARY_OPS]
            return Group(body=body, operators=operators)
        
        # Colimit 前置演算子: \WF
        if expr.startswith('\\'):
            inner = expr[1:]
            body = self._parse_expression(inner)
            operators = []
            if isinstance(body, Workflow):
                operators = body.operators
            return ColimitExpansion(body=body, operators=operators)
        
        # FEP 前置演算子: ∂coord/verb, ∫/verb, Σ[items]
        if expr.startswith('∂'):
            return self._parse_partial_diff(expr)
        if expr.startswith('∫'):
            return self._parse_integral(expr)
        if expr.startswith('Σ'):
            return self._parse_summation(expr)
        
        # let マクロ定義: let @name = CCL
        if expr.startswith('let '):
            return self._parse_let(expr)
        
        # fn 関数定義: fn name(args) { body }
        if expr.startswith('fn '):
            return self._parse_fn(expr)
        
        # use モジュール宣言: use hgk.telos
        if expr.startswith('use '):
            return self._parse_use(expr)
        
        # adjoint 宣言: adjoint F <=> G
        if expr.startswith('adjoint '):
            return self._parse_adjoint_decl(expr)
        
        # 関数呼出: name(args) — CCL 演算子より先にチェック
        fn_call_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$', expr)
        if fn_call_match and self._is_balanced_group(expr[len(fn_call_match.group(1)):], '(', ')'):
            fn_name = fn_call_match.group(1)
            # CCL 制御構文 (F:, I:, W:, L:, V:, C:, R:, M:, E:) は除外
            if fn_name not in ('F', 'I', 'W', 'L', 'V', 'C', 'R', 'M', 'E', 'EI'):
                return self._parse_fn_call(expr)
        
        # CPL 制御構文チェック
        if expr.startswith('F:'):
            return self._parse_for(expr)
        if expr.startswith('I:'):
            return self._parse_if(expr)
        if expr.startswith('EI:'):
            # EI: がトップレベルで出現した場合も IF チェインとして処理
            return self._parse_if('I:' + expr[3:])
        if expr.startswith('W:'):
            return self._parse_while(expr)
        if expr.startswith('L:'):
            return self._parse_lambda(expr)
        if expr.startswith('lim['):
            return self._parse_lim(expr)
        
        # CPL v2.0 意味タグ: V:{}, C:{}, R:{}, M:{}
        if len(expr) >= 3 and expr[0] in 'VCRM' and expr[1] == ':' and expr[2] == '{':
            return self._parse_tagged_block(expr)
        # E:{} は I: のコンテキスト外では TaggedBlock として処理
        if expr.startswith('E:{'):
            return self._parse_tagged_block(expr)
        
        # H-series 前動詞（中動態）: [xx] 記法
        # 例: [th], [ph], [ho]
        preverb_match = re.match(r'^\[([a-z]{2})\]$', expr)
        if preverb_match:
            pv_id = preverb_match.group(1)
            if pv_id in self.PREVERBS:
                return PreVerb(id=pv_id, full_name=self.PREVERB_NAMES.get(pv_id, ""))
        
        # グループ振動: ~(...) — シーケンス全体を振動（反復実行）
        # 例: ~(/sop_/noe_/ene_/dia-) = 4WFシーケンスを反復
        # 二項演算子より先にチェック（括弧内の _ で分割されるのを防ぐ）
        if expr.startswith('~(') and expr.endswith(')') and self._is_balanced_group(expr[1:], '(', ')'):
            inner = expr[2:-1]  # ~( と ) を除去
            body = self._parse_expression(inner)
            return Oscillation(left=body, right=body)
        
        # 二項演算子を優先順位順にチェック
        for op in self.BINARY_OPS_PRIORITY:
            if op in expr:
                # 最も外側の演算子を見つける
                parts = self._split_binary(expr, op)
                if len(parts) > 1:
                    return self._handle_binary(op, parts)
        
        # マクロ参照
        if expr.startswith('@'):
            return self._parse_macro(expr)
        
        # ワークフロー
        return self._parse_workflow(expr)
    
    # PURPOSE: 式全体がバランスしたグループかを判定する。
    def _is_balanced_group(self, expr: str, open_ch: str, close_ch: str) -> bool:
        """式全体がバランスしたグループかを判定する。
        例: (A~*B) -> True, (A)~*(B) -> False
        """
        if not (expr.startswith(open_ch) and expr.endswith(close_ch)):
            return False
        depth = 0
        for i, c in enumerate(expr):
            if c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
            if depth == 0 and i < len(expr) - 1:
                return False  # 途中で閉じた = 全体を囲んでいない
        return True
    
    # PURPOSE: 二項演算子で分割 (ネストを考慮)
    def _split_binary(self, expr: str, op: str) -> List[str]:
        """二項演算子で分割 (ネストを考慮)"""
        parts = []
        current = ""
        depth = 0
        i = 0
        
        while i < len(expr):
            c = expr[i]
            
            if c in '[{(':
                depth += 1
                current += c
            elif c in ']})':
                depth -= 1
                current += c
            elif depth == 0 and expr[i:i+len(op)] == op:
                parts.append(current.strip())
                current = ""
                i += len(op) - 1
            else:
                current += c
            
            i += 1
        
        # 最後の要素を追加 (空文字列でも追加して OpenEnd を表現できるようにする)
        parts.append(current.strip())
        
        return parts
    
    # PURPOSE: 二項演算子を処理
    def _handle_binary(self, op: str, parts: List[str]) -> Any:
        """二項演算子を処理"""
        if op == '_':
            # シーケンス — I:/EI: + E:/EI: チェインの再結合
            # `_` 分割で I:[cond]{then}_E:{else} が分離されるのを防ぐ
            merged_parts = []
            i = 0
            while i < len(parts):
                p = parts[i].strip()
                if not p:
                    i += 1
                    continue
                
                # I: または EI: で始まるパーツの場合、後続の E:/EI: を結合
                if p.startswith('I:') or p.startswith('EI:'):
                    combined = p
                    j = i + 1
                    while j < len(parts):
                        next_p = parts[j].strip()
                        if next_p.startswith('E:{') or next_p.startswith('EI:'):
                            combined += '_' + next_p
                            j += 1
                        else:
                            break
                    merged_parts.append(combined)
                    i = j
                else:
                    merged_parts.append(p)
                    i += 1
            
            steps = [self._parse_expression(p) for p in merged_parts if p]
            return Sequence(steps=steps)
        elif op == '~*':
            # 収束振動
            left = self._parse_expression(parts[0])
            right = self._parse_expression('~*'.join(parts[1:]))
            return Oscillation(left=left, right=right, convergent=True)
        elif op == '~!':
            # 発散振動
            left = self._parse_expression(parts[0])
            right = self._parse_expression('~!'.join(parts[1:]))
            return Oscillation(left=left, right=right, divergent=True)
        elif op == '~':
            # 通常の振動
            left = self._parse_expression(parts[0])
            right = self._parse_expression('~'.join(parts[1:]))
            return Oscillation(left=left, right=right)
        elif op == '*^':
            # 融合 + メタ表示 (fusion with meta display)
            # 空左辺の場合（_ 分割の結果 *^/u+ が独立パーツになったケース）
            if not parts[0]:
                right = self._parse_expression('*^'.join(parts[1:]))
                return Fusion(left=right, right=right, meta_display=True)
            left = self._parse_expression(parts[0])
            right = self._parse_expression('*^'.join(parts[1:]))
            return Fusion(left=left, right=right, meta_display=True)
        elif op == '*%':
            # 内積+外積 (fuse_outer)
            left = self._parse_expression(parts[0])
            right = self._parse_expression('*%'.join(parts[1:]))
            return Fusion(left=left, right=right, fuse_outer=True)
        elif op == '*':
            # 融合 (内積)
            left = self._parse_expression(parts[0])
            right = self._parse_expression('*'.join(parts[1:]))
            return Fusion(left=left, right=right, meta_display=False)
        elif op == '%':
            # 外積 (テンソル展開)
            left = self._parse_expression(parts[0])
            right = self._parse_expression('%'.join(parts[1:]))
            return Fusion(left=left, right=right, outer_product=True)
        elif op == '<*':
            # 逆射融合 (Oplax v7.7): A <* B = A が B の構造を取り込んで変容
            source = self._parse_expression(parts[0])
            target = self._parse_expression('<*'.join(parts[1:]))
            return Morphism(source=source, target=target, direction='oplax')
        elif op == '<<':
            # 逆射 (pullback): A << B = A が B を逆算する
            source = self._parse_expression(parts[0])
            target = self._parse_expression('<<'.join(parts[1:]))
            return Morphism(source=source, target=target, direction='reverse')
        elif op == '*>':
            # 方向付き融合 (v7.7): A *> B = A の融合結果が B 方向に流れる
            source = self._parse_expression(parts[0])
            target = self._parse_expression('*>'.join(parts[1:]))
            return Morphism(source=source, target=target, direction='directed_fusion')
        elif op == '>%':
            # 射的展開 (Pushforward v7.7): A >% B = A の射を B の全次元に展開
            source = self._parse_expression(parts[0])
            target = self._parse_expression('>%'.join(parts[1:]))
            return Morphism(source=source, target=target, direction='pushforward')
        elif op == '>*':
            # 射的融合 (Lax Actegory): A >* B = A が B の視点で変容
            source = self._parse_expression(parts[0])
            target = self._parse_expression('>*'.join(parts[1:]))
            return Morphism(source=source, target=target, direction='lax')
        elif op == '>>':
            # 収束ループ
            body = self._parse_expression(parts[0])
            condition = self._parse_condition(parts[1])
            return ConvergenceLoop(body=body, condition=condition)
        elif op == '|>':
            # 右随伴 (v7.6): 単項後置 — 右辺は空 (OpenEnd)
            left = self._parse_expression(parts[0])
            return Adjunction(left=left, right=OpenEnd())
        elif op == '<|':
            # 左随伴 (v7.6): 単項後置 — 右辺は空 (OpenEnd)
            left = self._parse_expression(parts[0])
            return Adjunction(left=OpenEnd(), right=left)
        elif op == '||':
            # 随伴宣言 (v7.6): F ⊣ G
            if len(parts) != 2 or not parts[0] or not parts[1]:
                raise ValueError(f"随伴宣言 || は二項演算子: 左辺と右辺が必要")
            left = self._parse_expression(parts[0])
            right = self._parse_expression(parts[1])
            return Adjunction(left=left, right=right)
        elif op == '&>':
            # 分散パイプライン (v7.6: 旧 |>)
            steps = [self._parse_expression(p) for p in parts]
            return Pipeline(steps=steps)
        elif op == '&&':
            # 分散並列 (v7.6: 旧 ||)
            branches = [self._parse_expression(p) for p in parts]
            return Parallel(branches=branches)
        
        # 未知の演算子
        return self._parse_workflow(parts[0])
    
    # Relation suffix partner table (v7.2)
    # Generated from nous/workflows/*.md category_theory: YAML
    RELATION_PARTNERS = {
        # .d = adjunction (diagonal), .h = natural transformation (horizontal), .x = duality (anti-diagonal)
        # Telos (I/A極)
        "noe": {"d": "zet", "h": "bou", "x": ("ene", "transition")},
        "bou": {"d": "ene", "h": "noe", "x": ("zet", "tension")},
        "zet": {"d": "noe", "h": "ene", "x": ("bou", "tension")},
        "ene": {"d": "bou", "h": "zet", "x": ("noe", "transition")},
        # Telos S極 (v5.0): .d=族内S極ペア, .h=同座標I極, .x=同座標A極
        "the": {"d": "ant", "h": "noe", "x": ("zet", "transition")},
        "ant": {"d": "the", "h": "bou", "x": ("ene", "transition")},
        # Methodos (I/A極)
        "ske": {"d": "sag", "h": "pei", "x": ("tek", "transition")},
        "sag": {"d": "ske", "h": "tek", "x": ("pei", "tension")},
        "pei": {"d": "tek", "h": "ske", "x": ("sag", "tension")},
        "tek": {"d": "pei", "h": "sag", "x": ("ske", "transition")},
        # Methodos S極 (v5.0)
        "ere": {"d": "agn", "h": "ske", "x": ("pei", "transition")},
        "agn": {"d": "ere", "h": "sag", "x": ("tek", "transition")},
        # Krisis / Orexis (I/A極, 旧体系 legacy)
        "pro": {"d": "ore", "h": "pis", "x": ("dox", "transition")},
        "pis": {"d": "dox", "h": "pro", "x": ("ore", "tension")},
        "ore": {"d": "pro", "h": "dox", "x": ("pis", "tension")},
        "dox": {"d": "pis", "h": "ore", "x": ("pro", "transition")},
        # Krisis (v5.0 I/A極)
        "kat": {"d": "epo", "h": "pai", "x": ("dok", "transition")},
        "epo": {"d": "kat", "h": "dok", "x": ("pai", "tension")},
        "pai": {"d": "dok", "h": "kat", "x": ("epo", "tension")},
        "dok": {"d": "pai", "h": "epo", "x": ("kat", "transition")},
        # Krisis S極 (v5.0)
        "sap": {"d": "ski", "h": "kat", "x": ("pai", "transition")},
        "ski": {"d": "sap", "h": "epo", "x": ("dok", "transition")},
        # Diástasis (v5.0 I/A極)
        "lys": {"d": "ops", "h": "akr", "x": ("arc", "transition")},
        "ops": {"d": "lys", "h": "arc", "x": ("akr", "tension")},
        "akr": {"d": "arc", "h": "lys", "x": ("ops", "tension")},
        "arc": {"d": "akr", "h": "ops", "x": ("lys", "transition")},
        # Diástasis S極 (v5.0)
        "prs": {"d": "per", "h": "lys", "x": ("akr", "transition")},
        "per": {"d": "prs", "h": "ops", "x": ("arc", "transition")},
        # Orexis (v5.0 I/A極)
        "beb": {"d": "ele", "h": "kop", "x": ("dio", "transition")},
        "ele": {"d": "beb", "h": "dio", "x": ("kop", "tension")},
        "kop": {"d": "dio", "h": "beb", "x": ("ele", "tension")},
        "dio": {"d": "kop", "h": "ele", "x": ("beb", "transition")},
        # Orexis S極 (v5.0)
        "apo": {"d": "exe", "h": "beb", "x": ("kop", "transition")},
        "exe": {"d": "apo", "h": "ele", "x": ("dio", "transition")},
        # Chronos (v5.0 I/A極)
        "hyp": {"d": "prm", "h": "ath", "x": ("par", "transition")},
        "prm": {"d": "hyp", "h": "par", "x": ("ath", "tension")},
        "ath": {"d": "par", "h": "hyp", "x": ("prm", "tension")},
        "par": {"d": "ath", "h": "prm", "x": ("hyp", "transition")},
        # Chronos S極 (v5.0)
        "his": {"d": "prg", "h": "hyp", "x": ("ath", "transition")},
        "prg": {"d": "his", "h": "prm", "x": ("par", "transition")},
        # Megethos (legacy)
        "kho": {"d": "tro", "h": "hod", "x": ("tek", "transition")},
        "hod": {"d": "tek", "h": "kho", "x": ("tro", "tension")},
        "tro": {"d": "kho", "h": "tek", "x": ("hod", "tension")},
        # Akribeia (legacy)
        "pat": {"d": "gno", "h": "dia", "x": ("epi", "transition")},
        "dia": {"d": "epi", "h": "pat", "x": ("gno", "tension")},
        "gno": {"d": "pat", "h": "epi", "x": ("dia", "tension")},
        "epi": {"d": "dia", "h": "gno", "x": ("pat", "transition")},
        # 旧 Chronos legacy
        "euk": {"d": "tel", "h": "chr", "x": ("sop", "transition")},
        "chr": {"d": "sop", "h": "euk", "x": ("tel", "tension")},
        "tel": {"d": "chr", "h": "sop", "x": ("euk", "tension")},
        "sop": {"d": "tel", "h": "chr", "x": ("euk", "transition")},
    }

    # 有効な修飾座標キー (v4.1 Dokimasia parameters)
    MODIFIER_COORDINATES = {
        "Va": {"E", "P"},             # Value: Epistemic / Pragmatic
        "Fu": {"Explore", "Exploit"}, # Function: Explore / Exploit
        "Pr": {"C", "U"},             # Precision: Confident / Uncertain
        "Sc": {"Mi", "Ma"},           # Scale: Micro / Macro
        "Vl": {"+", "-"},             # Valence: Approach / Avoid
        "Te": {"Past", "Future"},     # Temporality: Past / Future
    }

    # X-series 15辺の .XY ドット記法マッピング (taxis.md 準拠)
    # キー: 2文字ドット記法, 値: (座標1略記, 座標2略記, X-series 辺番号)
    XSERIES_DOT = {
        # 群 I: d2 内結合 (3本)
        "VF": ("Va", "Fu", 1),   # Value × Function
        "VP": ("Va", "Pr", 2),   # Value × Precision
        "FP": ("Fu", "Pr", 3),   # Function × Precision
        # 群 II: d2×d3 結合 (9本)
        "VS": ("Va", "Sc", 4),   # Value × Scale
        "VV": ("Va", "Vl", 5),   # Value × Valence
        "VT": ("Va", "Te", 6),   # Value × Temporality
        "FS": ("Fu", "Sc", 7),   # Function × Scale
        "FV": ("Fu", "Vl", 8),   # Function × Valence
        "FT": ("Fu", "Te", 9),   # Function × Temporality
        "PS": ("Pr", "Sc", 10),  # Precision × Scale
        "PV": ("Pr", "Vl", 11),  # Precision × Valence
        "PT": ("Pr", "Te", 12),  # Precision × Temporality
        # 群 III: d3 内結合 (3本)
        "SV": ("Sc", "Vl", 13),  # Scale × Valence
        "ST": ("Sc", "Te", 14),  # Scale × Temporality
        "VlTe": ("Vl", "Te", 15),  # Valence × Temporality (VT は Va×Te と衝突のため)
    }

    # PURPOSE: ワークフロー式をパース (例: /noe+, /noe[Va:E], /noe Q[Va→Pr], /noe.VF)
    def _parse_workflow(self, expr: str) -> Workflow:
        """ワークフロー式をパース"""
        # v5.0 Q[X→Y] 循環修飾子を先に抽出 (ブラケット修飾子より優先)
        q_modifiers = {}
        q_match = re.search(r'Q\[(\w+)→(\w+)\]', expr)
        if q_match:
            src_coord = q_match.group(1)
            dst_coord = q_match.group(2)
            valid_coords = set(self.MODIFIER_COORDINATES.keys())
            if src_coord in valid_coords and dst_coord in valid_coords:
                if src_coord == dst_coord:
                    self.errors.append(
                        f"Q-series の始点と終点が同一: Q[{src_coord}→{dst_coord}]"
                    )
                else:
                    q_modifiers["_q_src"] = src_coord
                    q_modifiers["_q_dst"] = dst_coord
                    q_modifiers["_q_edge"] = f"{src_coord}→{dst_coord}"
            else:
                invalid = [c for c in [src_coord, dst_coord] if c not in valid_coords]
                self.errors.append(
                    f"Q-series の無効な座標: {', '.join(invalid)}。"
                    f"有効: {sorted(valid_coords)}"
                )
            # Q[...] 部分を式から除去
            expr = expr[:q_match.start()] + expr[q_match.end():]
            expr = expr.strip()

        # v4.1 修飾子ブラケット [Va:E, Fu:Explore] or [critical] or [Va % Fu] を抽出
        bracket_modifiers = {}
        outer_product_coords = [] # [Va % Fu] のような外積展開用
        bracket_match = re.search(r'\[([^\]]+)\]', expr)
        if bracket_match:
            bracket_str = bracket_match.group(1).strip()
            
            # 外積展開: [Va % Fu] 
            if '%' in bracket_str:
                outer_product_coords = [c.strip() for c in bracket_str.split('%')]
                # 無効な座標キーの検証
                for c in outer_product_coords:
                    if c not in self.MODIFIER_COORDINATES and c != '*':
                        self.errors.append(
                            f"Invalid coordinate '{c}' for outer product. "
                            f"Valid: {list(self.MODIFIER_COORDINATES.keys())} or '*'"
                        )
            # プリセット展開: [critical] のようにコロンを含まない単一単語の場合
            elif ',' not in bracket_str and ':' not in bracket_str:
                preset_name = bracket_str.lower()
                # CCL-PL: modifier_presets は将来の実装。現在はパススルー
                self.errors.append(
                    f"Modifier preset '{preset_name}' は未実装 (Phase 2 で追加予定)"
                )
            else:
                # カンマ区切りで分割 → コロン区切りで key:value に分解
                for pair in bracket_str.split(','):
                    pair = pair.strip()
                    if ':' in pair:
                        key, value = pair.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        # 座標キーの検証
                        if key in self.MODIFIER_COORDINATES:
                            if value in self.MODIFIER_COORDINATES[key]:
                                bracket_modifiers[key] = value
                            else:
                                self.errors.append(
                                    f"Invalid modifier value '{value}' for {key}. "
                                    f"Valid: {self.MODIFIER_COORDINATES[key]}"
                                )
                        else:
                            # 不明なキーでもそのまま格納 (拡張性)
                            bracket_modifiers[key] = value
            # ブラケット部分を式から除去
            expr = expr[:bracket_match.start()] + expr[bracket_match.end():]
            expr = expr.strip()
        
        # Q 修飾子をブラケット修飾子にマージ
        bracket_modifiers.update(q_modifiers)
        
        # /wf.h+- 形式: relation suffix (.d/.h/.x) + X-series (.VF 等) を認識
        # ドット記法は演算子の前後どちらにも出現しうる:
        #   /noe.VF+ (ドット → 演算子)
        #   /noe+.VF (演算子 → ドット)
        # 両方のパターンを認識するため、2段階抽出とする
        
        # パターン1: /wf.suffix+ops (ドット → 演算子の順)
        pattern = r"^/?([a-z][a-z0-9]*)(?:\.([a-zA-Z]{1,4}))?([+\-\^\?\!\'\\\\]*)(.*)$"
        match = re.match(pattern, expr)
        
        if not match:
            raise ValueError(f"Invalid workflow: {expr}")
        
        wf_id = match.group(1)
        relation = match.group(2)  # None or "d"/"h"/"x" or "VF" 等
        ops_str = match.group(3) or ''
        rest = (match.group(4) or '').strip()
        
        # パターン2: /wf+.suffix (演算子 → ドットの順、rest に .suffix が残っている場合)
        if not relation and rest.startswith('.'):
            dot_match = re.match(r'^\.([a-zA-Z]{1,4})(.*)', rest)
            if dot_match:
                relation = dot_match.group(1)
                rest = (dot_match.group(2) or '').strip()
        
        # 演算子を変換
        operators = [self.UNARY_OPS[op] for op in ops_str if op in self.UNARY_OPS]
        
        # 修飾子パース (旧形式: a1:2, --mode=nous)
        modifiers = dict(bracket_modifiers)  # v4.1 ブラケット修飾子をベースに
        mode = None
        
        # operators → mode 自動導出 (AP-2: operators と mode の橋渡し)
        # /noe+ の + は operators [DEEPEN] に格納されるが、
        # LLMStepHandler は params["mode"] で深度を判定するため変換が必要
        _OP_TO_MODE = {
            OpType.DEEPEN: "+",
            OpType.CONDENSE: "-",
            OpType.ASCEND: "^",
        }
        for op in operators:
            if op in _OP_TO_MODE:
                mode = _OP_TO_MODE[op]
                break  # 最初にマッチした深度演算子を採用
        
        # --mode=xxx (明示指定は operators 導出を上書き)
        mode_match = re.search(r'--mode=(\w+)', rest)
        if mode_match:
            mode = mode_match.group(1)
        
        # 旧修飾子 (例: +a1:2) — 後方互換
        mod_pattern = r'([a-z]\d):(\d+)'
        for mod_match in re.finditer(mod_pattern, rest):
            modifiers[mod_match.group(1)] = int(mod_match.group(2))
            
        # ブラケット外積 [Va % Fu] → ModifierPeras
        if outer_product_coords:
            base_wf = Workflow(
                id=wf_id, operators=[], modifiers=modifiers, mode=mode, relation=None
            )
            coords = []
            if '*' not in outer_product_coords:
                coords = outer_product_coords
            return ModifierPeras(
                base_wf=base_wf,
                coordinates=coords,
                preset_name="",
                operators=operators
            )
        
        # .XY X-series ドット記法: 2文字以上のサフィックスを X-series 辺として解決
        if relation and len(relation) >= 2 and relation in self.XSERIES_DOT:
            coord1, coord2, edge_num = self.XSERIES_DOT[relation]
            modifiers["_x_edge"] = f"X{edge_num}"
            modifiers["_x_coords"] = f"{coord1}×{coord2}"
            modifiers["_x_dot"] = relation
            relation = None  # .XY は AST の relation フィールドには入れない

        # .d/.h/.x 展開: パートナーに自動展開 (1文字のみ)
        if relation and len(relation) == 1 and wf_id in self.RELATION_PARTNERS:
            partner_info = self.RELATION_PARTNERS[wf_id].get(relation)
            if partner_info:
                source = Workflow(
                    id=wf_id, operators=[], modifiers={}, mode=None
                )
                if relation == "x" and isinstance(partner_info, tuple):
                    partner_id, duality_type = partner_info
                    target = Workflow(
                        id=partner_id, operators=operators,
                        modifiers=modifiers, mode=mode, relation=relation
                    )
                    if duality_type == "tension":
                        # tension → ~ (oscillation)
                        result = Oscillation(left=source, right=target)
                        result.source_notation = f"/{wf_id}.{relation}"  # 元記法を保持
                        return result
                    else:
                        # transition → >> (sequence)
                        result = Sequence(steps=[source, target])
                        result.source_notation = f"/{wf_id}.{relation}"  # 元記法を保持
                        return result
                else:
                    # .d or .h → >> (sequence)
                    partner_id = partner_info
                    target = Workflow(
                        id=partner_id, operators=operators,
                        modifiers=modifiers, mode=mode, relation=relation
                    )
                    result = Sequence(steps=[source, target])
                    result.source_notation = f"/{wf_id}.{relation}"  # 元記法を保持
                    return result
        
        # 不明な2文字以上のサフィックスは警告
        if relation and len(relation) >= 2 and relation not in self.XSERIES_DOT:
            self.errors.append(
                f"未知のドット記法 '.{relation}'。"
                f"有効な X-series: {sorted(self.XSERIES_DOT.keys())}、"
                f"有効な relation: d, h, x"
            )
            relation = None

        return Workflow(
            id=wf_id,
            operators=operators,
            modifiers=modifiers,
            mode=mode,
            relation=relation
        )

    
    # PURPOSE: Parse a comparison condition
    def _parse_condition(self, expr: str) -> Condition:
        """条件式をパース"""
        expr = expr.strip()
        
        # 拡張パターン: V[] < 0.3, E[] > 0.5, E[/growth] > 0.8
        # 関数呼び出し形式を許容: VAR[任意の中身] OP VALUE
        pattern = r'(V\[[^\]]*\]|E\[[^\]]*\]|\w+)\s*(<|>|<=|>=|=)\s*([\d.]+)'
        match = re.match(pattern, expr)
        
        if match:
            return Condition(
                var=match.group(1),
                op=match.group(2),
                value=float(match.group(3))
            )
        
        # デフォルト — サイレントフォールバックではなく警告を出す
        warnings.warn(
            f"条件式のパースに失敗: '{expr}' → デフォルト V[] < 0.5 にフォールバック。"
            f"有効な形式: 'V[] < 0.3', 'E[] > 0.5', 'E[/growth] > 0.8'",
            stacklevel=2,
        )
        return Condition(var="V[]", op="<", value=0.5)
    
    # PURPOSE: マクロ参照をパース
    def _parse_macro(self, expr: str) -> MacroRef:
        """マクロ参照をパース"""
        # 拡張パターン: @name[·×+-]? または @name{...} または @name(...)
        # 1. @syn· @syn× など演算子付き
        # 2. @S{O,A,K} などセレクタ付き
        # 3. @think(param) など引数付き
        match = re.match(r'@(\w+)([·×\+\-]?)(?:\{([^}]*)\}|\(([^)]*)\))?', expr)
        if match:
            name = match.group(1)
            operator = match.group(2)
            selector = match.group(3)  # {} 内
            args_str = match.group(4)  # () 内
            
            # 演算子があれば名前に付加
            if operator:
                name = name + operator
            
            # 引数解析
            args = []
            if selector:
                args = [selector]  # セレクタは1つの引数として扱う
            elif args_str:
                args = [a.strip() for a in args_str.split(',')]
            
            return MacroRef(name=name, args=args)
        raise ValueError(f"Invalid macro: {expr}")
    
    # PURPOSE: Parse a FOR loop expression
    def _parse_for(self, expr: str) -> ForLoop:
        """FOR ループをパース: F:[×N]{body} or F:[A,B]{body} or F:N{body}"""
        # Pattern 1: F:[...]{body} (角括弧あり、ネスト対応)
        bracket_match = re.match(r'F:\[([^\]]+)\]', expr)
        if bracket_match:
            iter_spec = bracket_match.group(1).strip()
            rest_after_bracket = expr[bracket_match.end():]
            body_str, rest = self._extract_braced_body(rest_after_bracket)
            if body_str is not None:
                # ×N 形式
                if iter_spec.startswith('×'):
                    iterations = int(iter_spec[1:])
                else:
                    # リスト形式
                    iterations = [i.strip() for i in iter_spec.split(',')]
                
                body = self._parse_expression(body_str)
                
                # body 後に続く式がある場合 (例: F:[...]{...}, ~(...))
                if rest:
                    for_node = ForLoop(iterations=iterations, body=body)
                    if rest.startswith(','):
                        rest = rest[1:].strip()
                    if rest.startswith('_'):
                        rest = rest[1:].strip()
                    if rest:
                        rest_node = self._parse_expression(rest)
                        return Sequence(steps=[for_node, rest_node])
                    return for_node
                
                return ForLoop(iterations=iterations, body=body)

        # Pattern 2: F:N{body} (角括弧なし、数値直接指定)
        num_match = re.match(r'F:(\d+)', expr)
        if num_match:
            iterations = int(num_match.group(1))
            rest_after_num = expr[num_match.end():]
            body_str, _ = self._extract_braced_body(rest_after_num)
            if body_str is not None:
                body = self._parse_expression(body_str)
                return ForLoop(iterations=iterations, body=body)

        raise ValueError(f"Invalid FOR loop: {expr}")
    
    # PURPOSE: Parse an IF conditional expression
    def _parse_if(self, expr: str) -> IfCondition:
        """IF 条件分岐をパース: I:[cond]{then} EI:[cond]{elif} E:{else}"""
        # Pattern 1: I:[cond]{then} — ネストした [] と {} に対応
        if expr.startswith('I:['):
            # I:[ の後から対応する ] を見つける（]{の並びを閉じ判定に使用）
            depth = 0
            cond_end = -1
            for i in range(3, len(expr)):
                if expr[i] == '[':
                    depth += 1
                elif expr[i] == ']':
                    if depth > 0:
                        depth -= 1
                    else:
                        # 次の文字が { なら正しい閉じ括弧
                        if i + 1 < len(expr) and expr[i + 1] == '{':
                            cond_end = i
                            break
                        # V[] のような内部 [] はスキップ
            
            if cond_end > 0:
                cond_str = expr[3:cond_end]
                condition = self._parse_condition(cond_str)
                rest_after_cond = expr[cond_end + 1:]
                body_str, rest = self._extract_braced_body(rest_after_cond)
                if body_str is not None:
                    then_branch = self._parse_expression(body_str)
                    else_branch = self._parse_else_chain(rest) if rest else None
                    return IfCondition(
                        condition=condition,
                        then_branch=then_branch,
                        else_branch=else_branch
                    )

        # Pattern 2: I:cond{then} (角括弧なし、シンプル条件)
        match2 = re.match(r'I:(\w+)', expr)
        if match2:
            condition = Condition(var=match2.group(1), op=">", value=0)
            rest_after_cond = expr[match2.end():]
            body_str, rest = self._extract_braced_body(rest_after_cond)
            if body_str is not None:
                then_branch = self._parse_expression(body_str)
                else_branch = self._parse_else_chain(rest) if rest else None
                return IfCondition(
                    condition=condition,
                    then_branch=then_branch,
                    else_branch=else_branch
                )

        raise ValueError(f"Invalid IF: {expr}")

    # PURPOSE: Parse EI:/E: chain after IF body
    def _parse_else_chain(self, rest: str) -> Any:
        """EI:/E: チェインをパース → ネストされた IfCondition に変換"""
        rest = rest.strip()
        if not rest:
            return None
        
        # シーケンス結合後の `_` プレフィクスを除去
        # (例: _E:{...} → E:{...}, _EI:{...} → EI:{...})
        if rest.startswith('_'):
            rest = rest[1:].strip()
        
        # EI:[cond]{body}... → 再帰的に IfCondition をネスト
        if rest.startswith('EI:'):
            # EI: を I: に置換して再帰パース
            return self._parse_if('I:' + rest[3:])
        
        # E:{body} → else ブランチ (ネスト対応)
        if rest.startswith('E:'):
            body_str, _ = self._extract_braced_body(rest[2:])
            if body_str is not None:
                return self._parse_expression(body_str)
        
        return None
    
    # PURPOSE: Extract content from balanced braces
    def _extract_braced_body(self, s: str) -> tuple:
        """先頭の {body} を抽出 (ネスト対応)。
        
        Returns:
            (body_str, rest) — body_str は {} 内の文字列、rest は残りの文字列。
            body_str が None の場合は抽出失敗。
        """
        s = s.strip()
        if not s or s[0] != '{':
            return (None, s)
        
        depth = 0
        for i, c in enumerate(s):
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    body = s[1:i].strip()
                    rest = s[i+1:].strip()
                    return (body, rest)
        
        return (None, s)
    
    # PURPOSE: Parse a WHILE loop expression
    def _parse_while(self, expr: str) -> WhileLoop:
        """WHILE ループをパース: W:[cond]{body}"""
        # V[] を含む条件式を許容するパターン
        match = re.match(r'W:\[([^\]]*(?:\[\][^\]]*)*)\]\{(.+)\}$', expr)
        if not match:
            raise ValueError(f"Invalid WHILE: {expr}")
        
        condition = self._parse_condition(match.group(1))
        body = self._parse_expression(match.group(2))
        
        return WhileLoop(condition=condition, body=body)
    
    # PURPOSE: Parse a lambda expression
    def _parse_lambda(self, expr: str) -> Lambda:
        """Lambda をパース: L:[x]{body}
        
        body 内に CCL パターン (/verb) がなければ RawExpr として保持。
        算術式 (x * 2 等) が CCL 融合と誤認されるのを防ぐ。
        """
        match = re.match(r'L:\[([^\]]+)\]\{(.+)\}$', expr)
        if not match:
            raise ValueError(f"Invalid Lambda: {expr}")
        
        params = [p.strip() for p in match.group(1).split(',')]
        body_str = match.group(2).strip()
        
        # body に CCL パターンがあるか判定
        if self._is_ccl_expression(body_str):
            body = self._parse_expression(body_str)
        else:
            # Python 式としてそのまま保持
            from .ast import RawExpr
            body = RawExpr(code=body_str)
        
        return Lambda(params=params, body=body)
    
    def _is_ccl_expression(self, expr: str) -> bool:
        """式が CCL 構文を含むか判定する
        
        /verb パターン、CCL 制御構文 (F:, I:, W: 等)、
        @macro 参照が含まれていれば CCL 式として扱う。
        含まれなければ Python 式 (算術等) として扱う。
        """
        # /verb パターン
        if re.search(r'/[a-z]{2,}', expr):
            return True
        # CCL 制御構文
        if re.match(r'^[FIWL]:\[', expr):
            return True
        # @macro
        if expr.startswith('@'):
            return True
        # CCL 二項演算子 (~, >>, <<, &>, ||) — ただし Python にもある * % は除外
        # ⚠️ `_` は除外: 変数名 (my_var, sub_func) に含まれるため無条件マッチは誤判定
        for op in ['~', '&>', '||', '|>', '<|']:
            if op in expr:
                return True
        # >> と << は Python にもあるが、CCL コンテキスト (/verb>>/verb) のみ発火
        if re.search(r'>>|<<', expr) and re.search(r'/[a-z]', expr):
            return True
        # _ は CCL Sequence 演算子だが、トークン境界チェックが必要
        # `/verb_/verb` パターンのみマッチ。`my_var` や `sub_func` は除外
        if re.search(r'(?<=[+\-\])}])_(?=[/{(])', expr):
            return True
        return False
    
    def _parse_use(self, expr: str) -> 'UseDecl':
        """use 構文をパース: use module.path"""
        from .ast import UseDecl
        match = re.match(r'^use\s+([\w.]+)$', expr)
        if not match:
            raise ValueError(f"Invalid use: {expr}. 構文: use module.path")
        return UseDecl(module_path=match.group(1))
    
    def _parse_adjoint_decl(self, expr: str) -> 'AdjointDecl':
        """adjoint 宣言をパース: adjoint F <=> G"""
        from .ast import AdjointDecl
        match = re.match(r'^adjoint\s+(\w+)\s*<=>\s*(\w+)$', expr)
        if not match:
            raise ValueError(f"Invalid adjoint: {expr}. 構文: adjoint left <=> right")
        return AdjointDecl(left=match.group(1), right=match.group(2))
    
    def _parse_fn(self, expr: str) -> 'FnDef':
        """fn 構文をパース: fn name(params) { body }"""
        from .ast import FnDef, RawExpr
        match = re.match(r'fn\s+([a-zA-Z_][a-zA-Z0-9_]*)\(([^)]*)\)\s*\{(.+)\}$', expr)
        if not match:
            raise ValueError(f"Invalid fn: {expr}. 構文: fn name(args) {{ body }}")
        
        name = match.group(1)
        params = [p.strip() for p in match.group(2).split(',') if p.strip()]
        body_str = match.group(3).strip()
        
        if self._is_ccl_expression(body_str):
            body = self._parse_expression(body_str)
        else:
            body = RawExpr(code=body_str)
        
        return FnDef(name=name, params=params, body=body)
    
    def _parse_fn_call(self, expr: str) -> 'FnCall':
        """関数呼出をパース: name(args)"""
        from .ast import FnCall, RawExpr
        match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$', expr)
        if not match:
            raise ValueError(f"Invalid function call: {expr}")
        
        name = match.group(1)
        args_str = match.group(2).strip()
        
        if not args_str:
            return FnCall(name=name, args=[])
        
        # 引数をカンマ分割 (ネスト考慮)
        args = []
        for arg_str in self._split_args(args_str):
            arg_str = arg_str.strip()
            if self._is_ccl_expression(arg_str):
                args.append(self._parse_expression(arg_str))
            else:
                args.append(RawExpr(code=arg_str))
        
        return FnCall(name=name, args=args)
    
    def _split_args(self, args_str: str) -> list:
        """引数をカンマで分割 (ネスト考慮)"""
        parts = []
        current = ""
        depth = 0
        for c in args_str:
            if c in '([{':
                depth += 1
                current += c
            elif c in ')]}':
                depth -= 1
                current += c
            elif c == ',' and depth == 0:
                parts.append(current)
                current = ""
            else:
                current += c
        if current:
            parts.append(current)
        return parts
    
    # PURPOSE: Parse a lim convergence expression
    def _parse_lim(self, expr: str) -> ConvergenceLoop:
        """lim 正式形をパース: lim[cond]{body}"""
        # E[/growth] 等の角括弧内に内容がある関数呼び出しにも対応
        match = re.match(r'lim\[([^\]]*(?:\[[^\]]*\][^\]]*)*)\]\{(.+)\}$', expr)
        if not match:
            raise ValueError(f"Invalid lim: {expr}")
        
        condition = self._parse_condition(match.group(1))
        body = self._parse_expression(match.group(2))
        
        return ConvergenceLoop(body=body, condition=condition)

    # PURPOSE: 偏微分をパース: ∂Coord/WF
    def _parse_partial_diff(self, expr: str) -> 'PartialDiff':
        """偏微分をパース: ∂Coord/verb

        例: ∂Pr/noe+ — Precision 座標の変化率のみ観測
        構文: ∂ + 座標名(2文字) + / + WF式
        """
        # ∂ は UTF-8 で1文字
        rest = expr[1:]  # ∂ を除去
        # 座標名は 2文字 (Va, Fu, Pr, Sc, Vl, Te) で / が続く
        match = re.match(r'^(\w+)(/.+)$', rest)
        if not match:
            raise ValueError(f"Invalid partial diff: {expr}. 構文: ∂Coord/verb (例: ∂Pr/noe)")
        coord = match.group(1)
        body = self._parse_expression(match.group(2))
        return PartialDiff(coordinate=coord, body=body)

    # PURPOSE: 積分をパース: ∫/WF
    def _parse_integral(self, expr: str) -> 'Integral':
        """積分をパース: ∫/verb

        例: ∫/ath+ — 過去の省察を累積統合
        構文: ∫ + WF式
        """
        rest = expr[1:]  # ∫ を除去 (UTF-8 1文字)
        body = self._parse_expression(rest)
        return Integral(body=body)

    # PURPOSE: 総和をパース: Σ[items] or Σ[items]{body}
    def _parse_summation(self, expr: str) -> 'Summation':
        """総和をパース: Σ[items] or Σ[items]{body}

        例: Σ[results], Σ[findings]{/noe+}
        構文: Σ + [items] + オプショナル{body}
        """
        rest = expr[1:]  # Σ を除去 (UTF-8 1文字)
        match = re.match(r'^\[([^\]]+)\](?:\{(.+)\})?$', rest)
        if not match:
            raise ValueError(f"Invalid summation: {expr}. 構文: Σ[items] or Σ[items]{{body}}")
        items = match.group(1)
        body = self._parse_expression(match.group(2)) if match.group(2) else None
        return Summation(items=items, body=body)

    # PURPOSE: Parse a let binding (macro or variable)
    def _parse_let(self, expr: str) -> LetBinding:
        """let マクロ定義をパース: let @name = CCL or let name = CCL"""
        # Pattern 1: let @name = CCL (マクロ定義)
        match = re.match(r'let\s+@(\w+)\s*=\s*(.+)$', expr)
        if not match:
            # Pattern 2: let name = CCL (変数束縛)
            match = re.match(r'let\s+(\w+)\s*=\s*(.+)$', expr)
        if not match:
            raise ValueError(f"Invalid let: {expr}")
        
        name = match.group(1)
        body = self._parse_expression(match.group(2))
        
        return LetBinding(name=name, body=body)

    # PURPOSE: Parse tagged block (V:/C:/R:/M:/E:)
    def _parse_tagged_block(self, expr: str) -> 'TaggedBlock':
        """意味タグ付きブロックをパース: V:{body}, C:{body}, R:{body}, M:{body}, E:{body}"""
        tag = expr[0]  # V, C, R, M, or E
        # tag:{ の後の body を抽出 (ネストしたブラケットを考慮)
        if not expr[2] == '{':
            raise ValueError(f"Invalid tagged block: {expr}")
        
        # ネストした {} を考慮して body を抽出
        depth = 0
        body_start = 2  # ':' の次の '{'
        body_end = -1
        for i in range(body_start, len(expr)):
            if expr[i] == '{':
                depth += 1
            elif expr[i] == '}':
                depth -= 1
                if depth == 0:
                    body_end = i
                    break
        
        if body_end == -1:
            raise ValueError(f"Unmatched braces in tagged block: {expr}")
        
        body_str = expr[body_start + 1:body_end].strip()
        body = self._parse_expression(body_str)
        
        # タグブロック後に続く式がある場合（例: V:{/dia}_I:[pass]{...}）
        rest = expr[body_end + 1:].strip()
        if rest:
            # 残りの部分（通常は _ で接続されている）を処理
            if rest.startswith('_'):
                rest = rest[1:].strip()
            rest_node = self._parse_expression(rest)
            tagged = TaggedBlock(tag=tag, body=body)
            return Sequence(steps=[tagged, rest_node])
        
        return TaggedBlock(tag=tag, body=body)




# =============================================================================
# Convenience Function
# =============================================================================

# PURPOSE: Parse a CCL expression string into an AST
def parse_ccl(ccl: str) -> Any:
    """CCL 式をパース (便利関数)"""
    parser = CCLParser()
    return parser.parse(ccl)


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    test_cases = [
        "/noe+",
        "/bou-",
        "/s+_/ene",
        "/noe+ ~> V[] < 0.3",
        "/u+ ~ /noe!",
        "/noe * /dia",
        "F:[×3]{/dia}",
        "I:[V[] > 0.5]{/noe+} E:{/noe-}",
        "I:[V[]<0.3]{/ene+} EI:[V[]>0.7]{/pra+} E:{/zet}",  # EI: チェイン
        "W:[E[] > 0.3]{/dia}",
        "L:[wf]{wf+}",
        "lim[V[] < 0.3]{/noe+}",
        "lim[E[/growth]>0.8]{/noe+ _ /dia}",  # E[/growth] 拡張条件
        "let @think = /noe+ _ /dia",  # let マクロ定義
        "/noe+ |> /dia+",
        "/noe+ |> /dia+ |> /ene",
        "/noe+ || /dia+",
        "/noe+ || /dia+ || /ene",
        # % / *% 演算子
        "/noe+*%/dia+",
        "/noe % /dia",
        "/noe+*%/dia+_/ene",
        "(/noe+ || /dia+) |> /ene",
    ]
    
    parser = CCLParser()
    
    for ccl in test_cases:
        print(f"\n{'='*60}")
        print(f"CCL: {ccl}")
        try:
            ast = parser.parse(ccl)
            print(f"AST: {ast}")
        except Exception as e:
            print(f"Error: {e}")
