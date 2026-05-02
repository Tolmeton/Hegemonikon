# Git マルチマシン運用手順

> `.stignore` に `.git` が含まれているため、Syncthing は `.git/` を同期しない。
> これは設計判断（git objects の大量バイナリデータが Syncthing と相性が悪い）。

## 新マシンでの初期設定

```bash
cd /path/to/oikos/01_ヘゲモニコン｜Hegemonikon

# .git がなければ、GitHub からクローンして .git だけ取り出す
git clone --bare https://github.com/Tolmeton/Hegemonikon.git /tmp/hgk-bare
cp -r /tmp/hgk-bare/objects .git/
rm -rf /tmp/hgk-bare

# refs を GitHub 最新に合わせる
git fetch origin
git reset origin/master

# index を再構築
git checkout -- .
```

## 日常操作

```bash
# 日本語パスの場合、GIT_DIR を明示する必要がある場合がある
export GIT_DIR="/path/to/01_ヘゲモニコン｜Hegemonikon/.git"
export GIT_WORK_TREE="/path/to/01_ヘゲモニコン｜Hegemonikon"

git status
git add -A
git commit -m "message"
git push origin master
```

## 注意事項

- `.git/objects/` は各マシンで独立。push/pull で同期する
- Syncthing はワーキングツリーのみを同期する
- コンフリクト時は Syncthing 側が `.sync-conflict` ファイルを作る
