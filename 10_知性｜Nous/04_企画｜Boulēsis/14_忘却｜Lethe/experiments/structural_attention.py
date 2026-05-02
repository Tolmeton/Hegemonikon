#!/usr/bin/env python3
"""Phase C-mini: Structural Attention PoC.

PROOF: CCL 構造空間でアテンションすることで、LLM の構造的コード検索が改善される。

PURPOSE: VISION.md §12.2 の 3 層パイプラインを実装し、
  TinyLlama 1.1B (凍結) + 追加層で構造検索 recall@1 +10pp を検証する。

アーキテクチャ (§12.2 + §13.3 ハイブリッド v2):
  Code → [Frozen LLM] → hidden_states (L×S×D)
       → [Layer 1: CCL Encoder (U_ccl)] → CCL 構造ベクトル (M 個)
       → [Layer 2: Structural Attention] → 変換された構造
       → [Layer 3: CCL Decoder (N_ccl)] → 構造強化表現 (D)
       → [Contrastive Head] → similarity score

3 条件アブレーション (§13.3):
  C1: 明示化のみ (frozen LLM + AttentivePooling)
  C2: 注入のみ   (CCL エンコーダ → Structural Attn, LLM なし)
  C3: ハイブリッド (明示化 + 注入)
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

# 遅延 import (GPU/TPU 環境依存)
torch = None  # type: ignore
nn = None  # type: ignore
F_torch = None  # type: ignore


def _ensure_torch():
    """PyTorch の遅延インポート。"""
    global torch, nn, F_torch
    if torch is None:
        import torch as _torch
        import torch.nn as _nn
        import torch.nn.functional as _F
        torch = _torch
        nn = _nn
        F_torch = _F


# ============================================================
# 設定
# ============================================================

@dataclass
class StructuralAttentionConfig:
    """Structural Attention 層の設定。"""
    # LLM の hidden dimension
    hidden_dim: int = 768  # CodeBERT: 768, TinyLlama: 2048
    # CCL 構造空間の次元 (隠れ → 構造への圧縮)
    ccl_dim: int = 256
    # 構造アテンションのヘッド数
    n_heads: int = 4
    # Layer 1 の学習可能クエリ数 (構造トークン数)
    n_structure_queries: int = 8
    # Structural Attention の層数
    n_sa_layers: int = 2
    # ドロップアウト率
    dropout: float = 0.1
    # Contrastive Head の中間次元
    head_intermediate_dim: int = 128
    # CCL トークン注入 (Layer 2 で利用)
    use_ccl_injection: bool = True
    # CCL 最大トークン数 (注入用)
    max_ccl_tokens: int = 64
    # CCL 語彙サイズ (構造トークン)
    ccl_vocab_size: int = 128


# ============================================================
# Layer 1: CCL Encoder (U_ccl) — 忘却関手
# ============================================================

def _build_ccl_encoder(config: StructuralAttentionConfig):
    """CCL Encoder モジュールを動的生成。"""
    _ensure_torch()

    class CCLEncoder(nn.Module):
        """LLM hidden states → CCL 構造ベクトルへの射影。

        §13.3 ハイブリッド v2:
          - LLM の分散的構造表現を集約 (明示化)
          - CCL ground truth からの注入パスも持つ (注入)

        数学的: Im(U_existing) の集約 + Im(U_existing)^c からの注入
        """

        def __init__(self):
            super().__init__()
            hidden_dim = config.hidden_dim
            ccl_dim = config.ccl_dim
            n_queries = config.n_structure_queries

            # --- 明示化パス: LLM hidden → CCL 構造空間 ---
            # 学習可能クエリ (構造的トークン位置を選択)
            self.structure_queries = nn.Parameter(
                torch.randn(1, n_queries, hidden_dim) * 0.02
            )
            # Cross-attention: クエリ × LLM hidden
            self.cross_attn = nn.MultiheadAttention(
                hidden_dim, num_heads=config.n_heads, batch_first=True,
                dropout=config.dropout,
            )
            self.norm1 = nn.LayerNorm(hidden_dim)

            # hidden_dim → ccl_dim 線形射影
            self.project = nn.Linear(hidden_dim, ccl_dim)
            self.norm2 = nn.LayerNorm(ccl_dim)

            # --- 注入パス: CCL トークン → CCL 構造空間 ---
            if config.use_ccl_injection:
                self.ccl_embedding = nn.Embedding(
                    config.ccl_vocab_size, ccl_dim
                )
                self.ccl_positional = nn.Embedding(
                    config.max_ccl_tokens, ccl_dim
                )

        def forward(
            self,
            hidden_states: "torch.Tensor",
            ccl_token_ids: Optional["torch.Tensor"] = None,
            ccl_mask: Optional["torch.Tensor"] = None,
        ) -> tuple["torch.Tensor", "torch.Tensor"]:
            """
            Args:
                hidden_states: (batch, seq_len, hidden_dim) — LLM の出力
                ccl_token_ids: (batch, ccl_len) — CCL トークン ID (注入用、任意)
                ccl_mask: (batch, ccl_len) — CCL パディングマスク (任意)

            Returns:
                structure_repr: (batch, n_queries, ccl_dim) — 明示化された構造表現
                attn_weights: (batch, n_queries, seq_len) — 注意重み (可視化用)
            """
            batch_size = hidden_states.size(0)

            # --- 明示化パス ---
            queries = self.structure_queries.expand(batch_size, -1, -1)
            # cross-attention: 学習可能クエリが LLM hidden の構造的位置に注目
            attn_out, attn_weights = self.cross_attn(
                queries, hidden_states, hidden_states
            )
            attn_out = self.norm1(attn_out + queries)  # 残差接続

            # hidden_dim → ccl_dim に射影
            structure_repr = self.norm2(self.project(attn_out))
            # structure_repr: (batch, n_queries, ccl_dim)

            # --- 注入パス ---
            if config.use_ccl_injection and ccl_token_ids is not None:
                ccl_len = ccl_token_ids.size(1)
                positions = torch.arange(ccl_len, device=ccl_token_ids.device)
                ccl_repr = self.ccl_embedding(ccl_token_ids) + \
                    self.ccl_positional(positions)
                # ccl_repr: (batch, ccl_len, ccl_dim)

                # 明示化 + 注入 を連結
                structure_repr = torch.cat([structure_repr, ccl_repr], dim=1)
                # structure_repr: (batch, n_queries + ccl_len, ccl_dim)

            return structure_repr, attn_weights

    return CCLEncoder()


# ============================================================
# Layer 2: Structural Attention — 構造空間での自己アテンション
# ============================================================

def _build_structural_attention_layer(config: StructuralAttentionConfig):
    """Structural Attention の1層を動的生成。"""
    _ensure_torch()

    class StructuralAttentionLayer(nn.Module):
        """CCL 構造ベクトル間の self-attention。

        §12.2: トークンではなく射の合成パターンに対してアテンションを計算。
        将来的に CCL 演算子ベースのアテンションマスクを注入する拡張点あり。
        """

        def __init__(self):
            super().__init__()
            ccl_dim = config.ccl_dim

            # Self-attention (構造空間)
            self.self_attn = nn.MultiheadAttention(
                ccl_dim, num_heads=config.n_heads, batch_first=True,
                dropout=config.dropout,
            )
            self.norm1 = nn.LayerNorm(ccl_dim)

            # FFN (構造空間)
            self.ffn = nn.Sequential(
                nn.Linear(ccl_dim, ccl_dim * 4),
                nn.GELU(),
                nn.Dropout(config.dropout),
                nn.Linear(ccl_dim * 4, ccl_dim),
                nn.Dropout(config.dropout),
            )
            self.norm2 = nn.LayerNorm(ccl_dim)

        def forward(
            self,
            x: "torch.Tensor",
            attn_mask: Optional["torch.Tensor"] = None,
        ) -> "torch.Tensor":
            """
            Args:
                x: (batch, n_tokens, ccl_dim) — 構造トークン列
                attn_mask: (n_tokens, n_tokens) — CCL 演算子ベースのマスク (任意)

            Returns:
                x: (batch, n_tokens, ccl_dim) — 変換された構造表現
            """
            # Self-attention + 残差
            attn_out, _ = self.self_attn(x, x, x, attn_mask=attn_mask)
            x = self.norm1(x + attn_out)

            # FFN + 残差
            ffn_out = self.ffn(x)
            x = self.norm2(x + ffn_out)

            return x

    return StructuralAttentionLayer()


def _build_structural_attention_stack(config: StructuralAttentionConfig):
    """Structural Attention の複数層スタックを動的生成。"""
    _ensure_torch()

    class StructuralAttentionStack(nn.Module):
        """Structural Attention 層のスタック。"""

        def __init__(self):
            super().__init__()
            self.layers = nn.ModuleList([
                _build_structural_attention_layer(config)
                for _ in range(config.n_sa_layers)
            ])

        def forward(
            self,
            x: "torch.Tensor",
            attn_mask: Optional["torch.Tensor"] = None,
        ) -> "torch.Tensor":
            for layer in self.layers:
                x = layer(x, attn_mask)
            return x

    return StructuralAttentionStack()


# ============================================================
# Layer 3: CCL Decoder (N_ccl) — 回復関手
# ============================================================

def _build_ccl_decoder(config: StructuralAttentionConfig):
    """CCL Decoder モジュールを動的生成。"""
    _ensure_torch()

    class CCLDecoder(nn.Module):
        """CCL 構造ベクトル → LLM hidden 空間への逆射影。

        §12.2: 構造空間で処理された情報を元のトークン空間と再結合する。
        数学的: N_ccl (回復関手 = U_ccl の左随伴)
        """

        def __init__(self):
            super().__init__()
            ccl_dim = config.ccl_dim
            hidden_dim = config.hidden_dim

            # ccl_dim → hidden_dim 逆射影
            self.project_back = nn.Linear(ccl_dim, hidden_dim)
            self.norm1 = nn.LayerNorm(hidden_dim)

            # Cross-attention: 元の hidden + 構造表現
            self.cross_attn = nn.MultiheadAttention(
                hidden_dim, num_heads=config.n_heads, batch_first=True,
                dropout=config.dropout,
            )
            self.norm2 = nn.LayerNorm(hidden_dim)

            # 最終集約
            self.final_pool = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim),
                nn.Tanh(),
            )

        def forward(
            self,
            structure_repr: "torch.Tensor",
            original_hidden: "torch.Tensor",
        ) -> "torch.Tensor":
            """
            Args:
                structure_repr: (batch, n_tokens, ccl_dim) — Layer 2 出力
                original_hidden: (batch, seq_len, hidden_dim) — 元の LLM hidden

            Returns:
                output: (batch, hidden_dim) — 構造強化された表現 (1 ベクトル)
            """
            # ccl_dim → hidden_dim に戻す
            projected = self.norm1(self.project_back(structure_repr))
            # projected: (batch, n_tokens, hidden_dim)

            # Cross-attention: 構造表現 → 元の hidden から情報を引く
            cross_out, _ = self.cross_attn(
                projected, original_hidden, original_hidden
            )
            fused = self.norm2(projected + cross_out)
            # fused: (batch, n_tokens, hidden_dim)

            # Mean pooling → 最終表現
            pooled = fused.mean(dim=1)  # (batch, hidden_dim)
            output = self.final_pool(pooled)

            return output

    return CCLDecoder()


# ============================================================
# Contrastive Head — ペア類似度予測
# ============================================================

def _build_contrastive_head(config: StructuralAttentionConfig):
    """Contrastive Head を動的生成。nonlinear_probe.py StructuralHead の拡張。"""
    _ensure_torch()

    class ContrastiveHead(nn.Module):
        """2 つの構造強化表現の類似度を予測する。

        nonlinear_probe.py の StructuralHead (|a-b|, a*b → MLP → score) を拡張。
        """

        def __init__(self):
            super().__init__()
            hidden_dim = config.hidden_dim
            intermediate = config.head_intermediate_dim

            self.mlp = nn.Sequential(
                nn.Linear(hidden_dim * 3, intermediate),
                nn.GELU(),
                nn.Dropout(config.dropout),
                nn.Linear(intermediate, intermediate // 2),
                nn.GELU(),
                nn.Dropout(config.dropout),
                nn.Linear(intermediate // 2, 1),
                nn.Sigmoid(),  # 出力 [0, 1]
            )

        def forward(
            self,
            repr_a: "torch.Tensor",
            repr_b: "torch.Tensor",
        ) -> "torch.Tensor":
            """
            Args:
                repr_a: (batch, hidden_dim) — 関数 A の構造表現
                repr_b: (batch, hidden_dim) — 関数 B の構造表現

            Returns:
                similarity: (batch,) — 予測類似度
            """
            diff = torch.abs(repr_a - repr_b)
            product = repr_a * repr_b
            cosine = F_torch.cosine_similarity(repr_a, repr_b, dim=-1).unsqueeze(-1)
            combined = torch.cat([diff, product, cosine], dim=-1)
            return self.mlp(combined).squeeze(-1)

    return ContrastiveHead()


# ============================================================
# 統合モデル: StructuralAttentionModel
# ============================================================

class StructuralAttentionModel:
    """Phase C-mini 統合モデル。

    3層パイプライン (Layer 1 + Layer 2 + Layer 3) + Contrastive Head を統合。
    3条件アブレーション (C1/C2/C3) をモード切替で対応。
    """

    def __init__(
        self,
        config: StructuralAttentionConfig,
        mode: str = "hybrid",  # "explicit_only" | "injection_only" | "hybrid"
    ):
        _ensure_torch()
        self.config = config
        self.mode = mode

        # Layer 1: CCL Encoder
        self.encoder = _build_ccl_encoder(config)

        # Layer 2: Structural Attention
        self.attention = _build_structural_attention_stack(config)

        # Layer 3: CCL Decoder
        self.decoder = _build_ccl_decoder(config)

        # Contrastive Head
        self.head = _build_contrastive_head(config)

        self._device = "cpu"

    def parameters(self):
        """全訓練パラメータ。"""
        params = []
        params.extend(self.encoder.parameters())
        params.extend(self.attention.parameters())
        params.extend(self.decoder.parameters())
        params.extend(self.head.parameters())
        return params

    def n_parameters(self) -> int:
        """訓練パラメータ数。"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def to(self, device):
        """デバイスに転送。"""
        self._device = device
        self.encoder.to(device)
        self.attention.to(device)
        self.decoder.to(device)
        self.head.to(device)
        return self

    def train(self):
        """訓練モード。"""
        self.encoder.train()
        self.attention.train()
        self.decoder.train()
        self.head.train()

    def eval(self):
        """評価モード。"""
        self.encoder.eval()
        self.attention.eval()
        self.decoder.eval()
        self.head.eval()

    def encode_function(
        self,
        hidden_states: "torch.Tensor",
        ccl_token_ids: Optional["torch.Tensor"] = None,
        ccl_mask: Optional["torch.Tensor"] = None,
    ) -> "torch.Tensor":
        """1つの関数の構造強化表現を生成。

        Args:
            hidden_states: (1, seq_len, hidden_dim) — LLM の hidden state
            ccl_token_ids: (1, ccl_len) — CCL トークン ID (任意)
            ccl_mask: (1, ccl_len) — CCL マスク (任意)

        Returns:
            output: (1, hidden_dim) — 構造強化表現
        """
        # モードに応じて入力を制御
        if self.mode == "explicit_only":
            ccl_token_ids = None
            ccl_mask = None
        elif self.mode == "injection_only":
            # 注入のみの場合、hidden_states は mean-pool でダミー化
            hidden_states = hidden_states.mean(dim=1, keepdim=True).expand_as(
                hidden_states[:, :1, :]
            )

        # Layer 1: CCL Encoder
        structure_repr, attn_weights = self.encoder(
            hidden_states, ccl_token_ids, ccl_mask
        )

        # Layer 2: Structural Attention
        structure_repr = self.attention(structure_repr)

        # Layer 3: CCL Decoder
        output = self.decoder(structure_repr, hidden_states)

        return output

    def forward(
        self,
        hidden_a: "torch.Tensor",
        hidden_b: "torch.Tensor",
        ccl_ids_a: Optional["torch.Tensor"] = None,
        ccl_ids_b: Optional["torch.Tensor"] = None,
        ccl_mask_a: Optional["torch.Tensor"] = None,
        ccl_mask_b: Optional["torch.Tensor"] = None,
    ) -> "torch.Tensor":
        """ペアの類似度を予測。

        Args:
            hidden_a: (1, seq_a, hidden_dim) — 関数 A の LLM hidden
            hidden_b: (1, seq_b, hidden_dim) — 関数 B の LLM hidden
            ccl_ids_a/b: CCL トークン ID (任意)
            ccl_mask_a/b: CCL マスク (任意)

        Returns:
            similarity: (1,) — 予測類似度
        """
        repr_a = self.encode_function(hidden_a, ccl_ids_a, ccl_mask_a)
        repr_b = self.encode_function(hidden_b, ccl_ids_b, ccl_mask_b)
        return self.head(repr_a, repr_b)


# ============================================================
# CCL トークナイザ (簡易版 — 構造トークンのみ)
# ============================================================

# CCL 構造トークンの語彙
CCL_VOCAB = {
    "<pad>": 0, "<unk>": 1, "<bos>": 2, "<eos>": 3,
    # CCL 演算子
    ">>": 4, "_": 5, "~": 6, "*": 7, "%": 8,
    "<<": 9, "<*": 10, "||": 11,
    # 制御構造
    "F:": 12, "I:": 13, "C:": 14, "V:": 15, "E:": 16, "R:": 17,
    "[": 18, "]": 19, "{": 20, "}": 21,
    # 修飾子
    "+": 22, "-": 23, "^": 24,
    # 座標
    "[Va:": 25, "[Fn:": 26, "[Pr:": 27,
    "[Sc:": 28, "[Vl:": 29, "[Te:": 30,
    "I]": 31, "A]": 32, "E]": 33, "P]": 34,
    "Ex]": 35, "Ep]": 36, "C]": 37, "U]": 38,
    "Mi]": 39, "Ma]": 40, "+]": 41, "-]": 42,
    "Pa]": 43, "Fu]": 44,
    # 構造パターン
    "fn": 45, ".method": 46, ".attr": 47, "pred": 48,
    "return": 49, "yield": 50, "raise": 51,
    "×": 52, "each": 53, "map": 54,
    # 動詞ラベル (主要な 24 動詞の接頭辞)
    "/noe": 55, "/bou": 56, "/zet": 57, "/ene": 58,
    "/the": 59, "/ant": 60, "/ske": 61, "/sag": 62,
}
# 逆引き辞書
CCL_ID_TO_TOKEN = {v: k for k, v in CCL_VOCAB.items()}


def tokenize_ccl(ccl_expr: str, max_length: int = 64) -> list[int]:
    """CCL 式をトークン ID 列に変換する簡易トークナイザ。

    Args:
        ccl_expr: CCL 式の文字列 (例: "_ >> fn >> .method")
        max_length: 最大長 (パディング込み)

    Returns:
        token_ids: パディング済みトークン ID 列
    """
    tokens = [CCL_VOCAB["<bos>"]]

    # 簡易トークン化: スペースで分割 + 既知トークンにマッチ
    parts = ccl_expr.split()
    for part in parts:
        if part in CCL_VOCAB:
            tokens.append(CCL_VOCAB[part])
        else:
            # 未知トークンをさらに分解
            found = False
            for known in sorted(CCL_VOCAB.keys(), key=len, reverse=True):
                if known in part and known not in ("<pad>", "<unk>", "<bos>", "<eos>"):
                    tokens.append(CCL_VOCAB[known])
                    found = True
                    break
            if not found:
                tokens.append(CCL_VOCAB["<unk>"])

    tokens.append(CCL_VOCAB["<eos>"])

    # パディング / 切り詰め
    if len(tokens) > max_length:
        tokens = tokens[:max_length - 1] + [CCL_VOCAB["<eos>"]]
    while len(tokens) < max_length:
        tokens.append(CCL_VOCAB["<pad>"])

    return tokens


# ============================================================
# テスト
# ============================================================

def test_forward_pass():
    """最小限のフォワードパス疎通テスト。"""
    _ensure_torch()

    print("=== Structural Attention PoC — 疎通テスト ===\n")

    # --- 設定 ---
    config = StructuralAttentionConfig(
        hidden_dim=768,  # CodeBERT 互換
        ccl_dim=256,
        n_structure_queries=8,
        n_sa_layers=2,
        use_ccl_injection=True,
    )

    # --- 3 条件テスト ---
    for mode in ["explicit_only", "injection_only", "hybrid"]:
        print(f"\n--- Mode: {mode} ---")
        model = StructuralAttentionModel(config, mode=mode)
        print(f"  パラメータ数: {model.n_parameters():,}")

        # ダミー入力
        batch = 1
        seq_a, seq_b = 32, 48
        hidden_a = torch.randn(batch, seq_a, config.hidden_dim)
        hidden_b = torch.randn(batch, seq_b, config.hidden_dim)

        # CCL トークン
        ccl_expr_a = "_ >> fn >> .method"
        ccl_expr_b = "_ >> .method >> fn"
        ccl_ids_a = torch.tensor([tokenize_ccl(ccl_expr_a)])
        ccl_ids_b = torch.tensor([tokenize_ccl(ccl_expr_b)])

        # フォワードパス
        similarity = model.forward(
            hidden_a, hidden_b,
            ccl_ids_a if mode != "explicit_only" else None,
            ccl_ids_b if mode != "explicit_only" else None,
        )

        print(f"  similarity: {similarity.item():.4f}")
        assert similarity.shape == (1,), f"出力形状エラー: {similarity.shape}"
        assert 0 <= similarity.item() <= 1, f"出力範囲エラー: {similarity.item()}"
        print(f"  ✅ PASS")

    # --- CCL トークナイザテスト ---
    print(f"\n--- CCL トークナイザ ---")
    test_exprs = [
        "_ >> fn",
        "_ >> .method >> _ >> .method",
        "F: [ × 3 ] { _ >> fn }",
        "I: [ ] { _ >> fn }",
    ]
    for expr in test_exprs:
        ids = tokenize_ccl(expr)
        n_non_pad = sum(1 for x in ids if x != CCL_VOCAB["<pad>"])
        print(f"  '{expr}' → {n_non_pad} トークン (+ {len(ids) - n_non_pad} pad)")

    print(f"\n=== 全テスト PASS ===")


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        test_forward_pass()
    else:
        print("Usage: python structural_attention.py --test")
        print("  → フォワードパス疎通テストを実行")
