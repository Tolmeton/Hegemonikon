# ClawX デザインリファレンス

> HGK の CSS 改善時に参考にする ClawX の値。直接コピーではなく参考値。

## Dark Mode カラーパレット (HSL)

| 変数 | ClawX 値 | HGK 用途 |
|:-----|:---------|:---------|
| `--background` | `222.2 84% 4.9%` | 深い紺 — 背景 |
| `--foreground` | `210 40% 98%` | ほぼ白 — テキスト |
| `--primary` | `217.2 91.2% 59.8%` | 鮮やかな青 — CTA |
| `--secondary` | `217.2 32.6% 17.5%` | 暗い青灰 — セカンダリ |
| `--muted-foreground` | `215 20.2% 65.1%` | 中間グレー — 補助テキスト |
| `--destructive` | `0 62.8% 30.6%` | 暗い赤 — エラー |
| `--border` | `217.2 32.6% 17.5%` | ボーダー (secondary と同値) |
| `--ring` | `224.3 76.3% 48%` | フォーカスリング |

## タイポグラフィ

- `line-height: 1.6` (prose)
- paragraph margin: `0.75em`
- `font-feature-settings: "rlig" 1, "calt" 1`

## トランジション

- 標準: `200ms` (テーマ切替など)
- タイピングインジケーター: `bounce` animation (30% で -4px 上昇)

## スクロールバー

- 幅/高さ: `8px`
- thumb: `rounded-full`, border 色
- hover: `muted-foreground/30`

## デザイン思想の差異

ClawX は React + shadcn/ui + Tailwind → トークン化が徹底。
HGK は手書き CSS → 上記の値を CSS custom properties として定義し、共通言語にする。
