```typos
#prompt symphysis-readme
#syntax: v8
#depth: L1

<:role: Symphysis (σύμφυσις) — PJ 間融合ディレクトリ :>
<:goal: HGK 内部の独立 PJ 同士が有機的に融合する構想を格納する :>

<:context:
  - [knowledge] Symphysis = 「癒合」。別々に育った骨が一体化する医学用語
  - [knowledge] 対象: 独立 PJ 間の融合構想・VISION・PoC 実装計画
  - [knowledge] 非対象: 外部 OSS 調査 (→ 04_随伴/research/)、単独 PJ の VISION (→ 各 PJ 内)
/context:>
```

# 13_融合｜Symphysis

> **σύμφυσις** (symphysis) = 癒合。別々に育ったものが有機的に一体化すること。

## 目的

HGK 内部の独立 PJ 同士の融合構想を格納するディレクトリ。

各融合プロジェクトはサブディレクトリとして配置:

```
13_融合｜Symphysis/
  ├── README.md
  └── ccl-ir_dendron/        ← CCL-IR × Dendron 融合
       └── ビジョン.md
```

## なぜ `research/` ではないか

`04_随伴/research/` は外部 OSS・フレームワークの調査を格納する。
内部 PJ 間の融合は「外部調査」ではなく「内部統合」であり、質的に異なる。

## 命名規則

サブディレクトリ名: `{PJ-A}_{PJ-B}/` (アルファベット順)
