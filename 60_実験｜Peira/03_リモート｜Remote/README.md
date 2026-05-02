# 03_リモート｜Remote — リモート環境実験

GPU サーバー・Language Server 等のリモート環境に特化した実験群。

## 内容

| ディレクトリ / ファイル | 概要 |
|:------------------------|:-----|
| `benchmarks/` | リモート環境ベンチマーク |
| `ls-test-workspace/` | Language Server テストワークスペース |
| `unleash/` | 制約解放テスト (リモート版) |
| `vertex_claude/` | Vertex Claude API 検証 (リモート版) |
| `gpu_embed_bench.py` | GPU 埋め込みベンチマーク |
| `extract_grpc2.py` | gRPC プロトコル抽出 |
| `f0_ccl_test.py` | CCL テスト (リモート) |
| `h2c_proxy.py` | HTTP/2 cleartext プロキシ |
| `ls_capability_test.sh` | LS 能力テスト |
| `run_ls_mitm.py` | LS MITM (中間者) 検証 |

## 備考

- 00_汎用 の特殊ケース: ローカルでは実行できない / GPU が必要な実験
