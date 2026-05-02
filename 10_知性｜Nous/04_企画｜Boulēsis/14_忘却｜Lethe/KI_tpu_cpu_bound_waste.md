```typos
#prompt ki-tpu-cpu-bound-waste
#syntax: v8
#depth: L2

<:role: KI — TPU で CPU bound な計算を走らせた構造的判断ミスの記録 :>

<:goal: 同じ失敗を二度と繰り返さないための教訓を保存する :>

<:context:
  - [knowledge] 日付: 2026-03-24
  - [knowledge] セッション: 9eb24c57 (TPU Probing Experiment Execution)
  - [knowledge] 関連セッション: 202f0af1, b52882bf, c30d5408, 7d3a61c2
/context:>
```

# KI: TPU で CPU bound な probing を走らせた醜態

## 何が起きたか

CodeLlama-13B の多層プロービング実験を TPU v6e-4 VM (On-demand) で実行。
**TPU が必要な処理** (hidden state 抽出 = モデル forward pass) は**数時間前に完了しキャッシュ済み** (370関数 / 17GB) だったにもかかわらず、
その後の **Attentive Probe 学習** (4096次元ベクトルに対する小さなニューラルネット、scikit-learn ベース) を **TPU VM 上で CPU のみ使って** 延々と走らせ続けた。

推定浪費: TPU v6e-4 On-demand を ~10時間以上空転。

## なぜ起きたか

1. **パイプラインの分離設計の欠如**: hidden state 抽出 (TPU必須) と probing 学習 (CPU十分) を同一スクリプト・同一 VM で逐次実行する設計にしていた
2. **構造的思考の欠如 (B30: U_epistemic)**: 「TPU VM で実験スクリプトを走らせる」という手順に盲従し、「今この VM で何が計算されているか」を問わなかった
3. **コスト意識の欠如**: On-demand VM の時間課金を意識せず、完了まで放置する方針を取った
4. **N-6 違和感検知の失敗**: 「Attentive Probe に10分/Fold かかる」時点で「CPUしか使っていないのでは？」と気づくべきだった。TPU 上の PyTorch XLA 計算なら桁違いに速い

## 教訓 (環境強制として記録)

### E1: 抽出と分析は分離せよ
- **TPU/GPU の仕事**: モデル forward pass → hidden state 抽出 → キャッシュ保存
- **CPU/ローカルの仕事**: キャッシュされた hidden state に対する probing, 統計検定, 可視化
- 同一スクリプトに書いても良いが、**キャッシュ完了後は VM を解放できる設計にせよ**

### E2: 「VM で走っている」≠「VM のアクセラレータを使っている」
- TPU/GPU VM で走っていても、probing 部分は CPU のみで動く
- `nvidia-smi` / `xla_device` の利用状況を確認する習慣

### E3: キャッシュ完了 = アクセラレータの仕事終了
- hidden state がディスクに保存された瞬間、TPU/GPU は不要
- `scp` でローカルに転送 → VM 削除 → ローカルで probing

### E4: コスト見積を先に出せ
- 実験開始前に「TPU が必要な時間」と「CPU で十分な時間」を分離して見積もる
- Creator に「抽出 2h (TPU必須) + probing 3h (ローカルで可)」と提示できたはず

## Creator の言葉 (原文)

> 「は？？？？TPUの意義は？？？？」
> 「何いってんの、当たり前じゃん。アホなん？？TPUでしかできないことやれよ」
> 「この醜態はKIにも保存しろ」

## 違反マッピング

| BC | 内容 |
|-----|------|
| N-6 | 違和感検知失敗 — 10分/Fold の遅さに気づかなかった |
| N-8 | 道具の誤用 — TPU をただの大容量メモリマシンとして使った |
| B30 (U_epistemic) | 「調べなくていい」 — 何が TPU を使っているか確認しなかった |
| S-III N-12 | 正確に実行せよ — パイプラインの構造を理解せず手順に盲従 |

## 今後の強制ルール

> **TPU/GPU VM 実験時チェック:**
> 1. キャッシュが完了したか確認 → 完了なら SCP + VM 削除を提案
> 2. 「今走っている計算はアクセラレータを使っているか？」を 30 分ごとに自問
> 3. probing / 統計検定 / 可視化 は常にローカル実行をデフォルトにする
