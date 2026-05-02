# 3画面マルチモニター修正 (2026-04-05)

## 環境
- GPU: NVIDIA RTX 2070 SUPER / Driver 550.163.01
- DE: GNOME Wayland / Debian 13 (kernel 6.12.74)
- DP-3: XEC MFG27F4Q 2560x1440@200Hz (上下逆, HDR bt2100)
- DP-2: ASUS VG27AQ5A 2560x1440@200Hz (primary)
- DP-1: GIGABYTE AORUS KD25F 1920x1080@240Hz (右90°縦置き)

## 問題と原因
1. ホワイトアウト + 操作不能 → Page flip failed (drmModeAtomicCommit) = NVIDIA DRM の atomic commit 失敗
2. カーソル非表示 → ハードウェアカーソルプレーンが page flip 失敗に巻き込まれた
3. 設定変更で再発 → HDR 切替が atomic commit 再構成を引き起こす
4. 定期的な3秒黒画面 → DP ポートの接触不良 (ポート変更で解決)

## 適用した修正
1. `/etc/default/grub`: `nvidia_drm.fbdev=1` 追加 → Wayland マルチモニター安定性向上
2. `/etc/environment`: `MUTTER_DEBUG_DISABLE_HW_CURSORS=1` 追加 → ソフトウェアカーソル強制
3. `~/.config/monitors.xml`: 10構成 → 1構成にクリーンアップ (バックアップ: monitors.xml.bak.20260405)
4. DP-3 のモニター側 DP ポート変更 → 3秒黒画面解消

## 知見
- GIGABYTE AORUS KD25F / XEC MFG27F4Q は Hz 固定 (240Hz/200Hz のみ)。Linux 側でカスタムモード不可 (Wayland)。OSD か カスタム EDID が必要
- RTX 2070 SUPER + 3画面 + 高Hz + 回転 = atomic commit の負荷が高い。設定変更時に崩れやすい
- monitors.xml に古い構成が蓄積すると GNOME が間違った構成を拾う
- `sudo` は Claude Code の settings.json に `Bash(sudo *)` パターンを追加しても、セッション中は反映されない。次セッションから有効
