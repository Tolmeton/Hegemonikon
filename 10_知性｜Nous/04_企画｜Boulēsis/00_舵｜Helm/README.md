# 00_舵｜Helm

> **PURPOSE**: HGK 全体のビジョン・方向性・プロジェクトレジストリを管理する司令塔。

## SCOPE

- **hgk_vision_v4.typos** (32KB): HGK の全体ビジョン定義 (Týpos 形式)
- **AMBITION.typos**: HGK OS 野望要件定義書。`hgk_vision_v4.typos` と並ぶ canonical ancestor
- **HGK_NATIVE_SPEC_PROTOCOL_v1.md**: Vision Packet → State Packet → `IMPL_SPEC` → `WORK_ORDER` の current canonical transform rule
- **registry.yaml** (18KB): 全 PJ のレジストリ (メタデータ管理)
- **knowledge.yaml**: 知識体系のメタデータ
- **north_star.typos**: 北極星 (最上位の目的)
- **core.typos / concepts.typos / modules.typos**: 核心・概念・モジュール定義
- **engines.typos / infra.typos**: エンジン・インフラ定義
- **products.typos / applied.typos / incubator.typos**: 製品・応用・インキュベーター
- **vision/index.md**: ビジョン.md 横断索引 (14件)
- **templates/**: protocol 用の最小 template pack

## MAP

### 内部ファイル
- [hgk_vision_v4.typos](./hgk_vision_v4.typos) — HGK 全体ビジョン (32KB, Týpos v8 形式)
- [AMBITION.typos](./AMBITION.typos) — HGK OS 野望要件定義書。canonical ancestor
- [HGK_NATIVE_SPEC_PROTOCOL_v1.md](./HGK_NATIVE_SPEC_PROTOCOL_v1.md) — current canonical transform rule
- [templates/](./templates/) — Vision / State / IMPL_SPEC / WORK_ORDER template pack
- [registry.yaml](./registry.yaml) — 全 PJ レジストリ (18KB)
- [north_star.typos](./north_star.typos) — 最上位目的
- [vision/index.md](./vision/index.md) — ビジョン.md 横断索引

### ROM
- [rom_2026-02-14_helm_direction.md](../../../30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_2026-02-14_helm_direction.md) — 舵の方向性
- [rom_2026-03-07_vision_kalon.md](../../../30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_2026-03-07_vision_kalon.md) — ビジョンの Kalon 判定

### Artifact
- [helm_2026-02-14.md](../../../30_記憶｜Mneme/01_記録｜Records/d_成果物｜artifacts/helm_2026-02-14.md)
- [helm_direction_2026-02-14.md](../../../30_記憶｜Mneme/01_記録｜Records/d_成果物｜artifacts/helm_direction_2026-02-14.md)

### Handoff
- [handoff_dendron_helm_2026-02-13](../../../30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff/archive/2026-02/handoff_dendron_helm_2026-02-13_2105.md)

### 関連 PJ
- [03_市場｜Agora](../03_市場｜Agora/) — 製品化戦略の実行面
- [08_形式導出｜FormalDerivation](../08_形式導出｜FormalDerivation/) — 理論的基盤の厳密化

## STATUS

- **現状**: `hgk_vision_v4.typos` と `AMBITION.typos` が canonical ancestors、`HGK_NATIVE_SPEC_PROTOCOL_v1.md` が現行の変換規則
- **実装面**: `Helm/specs/` の `IMPL_SPEC` 群と `WORK_ORDERS` 群が reader-facing artifact
- **gate**: 新規 Medium+ change は protocol に従って State Packet と IMPL_SPEC を要求
- **未踏**: vision/index.md を拡張し、PJ 間の依存関係グラフを可視化する

---
*Created: 2026-03-13 / Updated: 2026-04-17*
