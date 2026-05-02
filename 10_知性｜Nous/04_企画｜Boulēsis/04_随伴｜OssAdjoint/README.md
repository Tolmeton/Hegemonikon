# OSS 随伴 PJ (OSS Adjoint Project)

> **目的**: HGK 各サブPJ に対する OSS 同等品を随伴対象として管理し、
> Build/Leverage/Replace の戦略判断を継続的に更新する
>
> **圏論的意味**: G: HGK → OSS (忘却関手 = HGK固有性を落とすと何が残るか)
> この G の左随伴 F: OSS → HGK が「既存OSSをHGKに持ち上げる」操作。
> η: Id → G∘F = "OSS を取り込んで HGK 化した結果、元の HGK とどれだけ一致するか"
> ε: F∘G → Id = "HGK の固有性を落として OSS に写像し、再び持ち上げた結果"

## 方針

1. **Replace (🟢)**: OSS で十分。薄いラッパーのみ
2. **Leverage+Extend (🟡)**: OSS 基盤 + HGK 固有レイヤー
3. **Build (🔴)**: 代替不能。自前実装を継続

## ディレクトリ構造

```
oss_adjoint/
├── README.md           # 本ファイル
├── adjoint_map.yaml    # 随伴対象マップ (正本)
└── research/           # 深掘り調査単位
    └── (future)
```

---

*Created: 2026-02-28*
