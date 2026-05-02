# PROOF: [L2/インフラ] <- mekhane/ochema/scripts/vault_setup.py A0→マルチアカウント OAuth 登録 CLI
# PURPOSE: TokenVault にアカウントを登録するための CLI ツール。
#   DX-010 §H.10 の OAuth フローを自動化する。
from __future__ import annotations
from typing import Optional
"""vault_setup — TokenVault アカウント登録 CLI.

Google OAuth localhost リダイレクト方式で refresh_token を取得し、
TokenVault に登録する。

Usage:
    # アカウント追加 (ブラウザで Google ログイン)
    python -m mekhane.ochema.scripts.vault_setup add movement

    # アカウント一覧
    python -m mekhane.ochema.scripts.vault_setup list

    # アカウント削除
    python -m mekhane.ochema.scripts.vault_setup remove movement

    # 全アカウントの健全性チェック
    python -m mekhane.ochema.scripts.vault_setup check
"""

import argparse
import json
import logging
import sys
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

logger = logging.getLogger(__name__)

# OAuth 定数 (DX-010 §H.10)
_OAUTH_CONFIG = Path.home() / ".config" / "cortex" / "oauth.json"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_SCOPES = "https://www.googleapis.com/auth/cloud-platform https://www.googleapis.com/auth/userinfo.email"
_REDIRECT_URI = "http://localhost"
_TOKENS_DIR = Path.home() / ".config" / "ochema" / "tokens"


# PURPOSE: oauth.json から Client ID/Secret を読み込む
def _load_oauth_config() -> tuple[str, str]:
    """OAuth 設定の読み込み。~/.config/cortex/oauth.json から。"""
    if not _OAUTH_CONFIG.exists():
        print(f"❌ OAuth 設定が見つかりません: {_OAUTH_CONFIG}")
        print("作成方法:")
        print(f'  mkdir -p {_OAUTH_CONFIG.parent}')
        print(f'  echo \'{{"client_id":"...","client_secret":"..."}}\' > {_OAUTH_CONFIG}')
        sys.exit(1)

    data = json.loads(_OAUTH_CONFIG.read_text())
    return data["client_id"], data["client_secret"]


# PURPOSE: Google OAuth 認証 URL を生成してブラウザを開く
def _start_oauth_flow(client_id: str) -> str:
    """OAuth 認証フローを開始し、認証コードを取得する。"""
    params = {
        "client_id": client_id,
        "redirect_uri": _REDIRECT_URI,
        "response_type": "code",
        "scope": _SCOPES,
        "access_type": "offline",
        "prompt": "consent",  # refresh_token を確実に取得
    }
    auth_url = f"{_AUTH_URL}?{urllib.parse.urlencode(params)}"

    print()
    print("=" * 60)
    print("🔑 Google OAuth ログイン")
    print("=" * 60)
    print()
    print("ブラウザが開きます。対象の Google アカウントでログインしてください。")
    print()
    print("ログイン後、アドレスバーに以下の形式の URL が表示されます:")
    print("  http://localhost/?code=4/0A... (ページ自体は表示されません)")
    print()
    print("その URL の ?code= 以降の値をコピーしてここに貼り付けてください。")
    print()

    webbrowser.open(auth_url)

    print("認証 URL (手動でブラウザを開く場合):")
    print(f"  {auth_url}")
    print()

    code = input("認証コード (?code= の値): ").strip()

    # URL 全体が貼り付けられた場合のパース
    if code.startswith("http"):
        parsed = urllib.parse.urlparse(code)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            code = params["code"][0]

    return code


# PURPOSE: 認証コードを refresh_token に交換する
def _exchange_code(
    code: str,
    client_id: str,
    client_secret: str,
) -> dict:
    """認証コード → refresh_token + access_token を取得。"""
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": _REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode("utf-8")

    req = urllib.request.Request(_TOKEN_URL, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    if "refresh_token" not in result:
        print("❌ refresh_token が取得できませんでした。")
        print("   prompt=consent で再試行してください。")
        print(f"   レスポンス: {json.dumps(result, indent=2)}")
        sys.exit(1)

    return result


# PURPOSE: ユーザーのメールアドレスを取得する
def _get_user_email(access_token: str) -> Optional[str]:
    """access_token でユーザー情報を取得してメールアドレスを返す。"""
    try:
        req = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("email")
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("メールアドレス取得失敗: %s", e)
        return None


# PURPOSE: アカウントを TokenVault に登録する
def cmd_add(args: argparse.Namespace) -> None:
    """アカウントを追加する。"""
    from mekhane.ochema.token_vault import TokenVault, VaultError

    name = args.name
    vault = TokenVault()

    # 既存チェック
    existing = vault.list_accounts()
    for acct in existing:
        if acct["name"] == name:
            print(f"⚠️ アカウント '{name}' は既に登録されています。")
            confirm = input("上書きしますか？ (y/N): ").strip().lower()
            if confirm != "y":
                print("中断しました。")
                return
            # 上書きのために削除 (default でなければ)
            try:
                vault.remove_account(name)
            except VaultError:
                # default の場合は削除できないが、credentials は上書きする
                pass
            break

    # OAuth フロー
    client_id, client_secret = _load_oauth_config()
    code = _start_oauth_flow(client_id)
    result = _exchange_code(code, client_id, client_secret)

    # メールアドレス取得
    email = _get_user_email(result.get("access_token", ""))
    if email:
        print(f"✅ ログイン成功: {email}")

    # credentials ファイル作成
    creds = {
        "refresh_token": result["refresh_token"],
        "client_id": client_id,
        "client_secret": client_secret,
    }
    if email:
        creds["email"] = email

    _TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    creds_path = _TOKENS_DIR / f"{name}.json"
    creds_path.write_text(json.dumps(creds, indent=2))
    creds_path.chmod(0o600)

    # TokenVault に登録
    vault.add_account(name, creds_path, email=email or "")
    print(f"✅ アカウント '{name}' を TokenVault に登録しました。")
    print(f"   認証ファイル: {creds_path}")

    # テスト: トークン取得
    try:
        token = vault.get_token(name)
        print(f"✅ トークン取得成功 (ya29...{token[-6:]})")
    except (OSError, KeyError) as e:
        logger.debug("Ignored exception: %s", e)
        print(f"⚠️ トークン取得テスト失敗: {e}")


# PURPOSE: 全アカウントを一覧表示する
def cmd_list(args: argparse.Namespace) -> None:
    """登録済みアカウントを一覧表示。"""
    from mekhane.ochema.token_vault import TokenVault

    vault = TokenVault()
    accounts = vault.list_accounts()

    if not accounts:
        print("アカウントが登録されていません。")
        return

    print(f"\n{'名前':<20} {'メール':<30} {'ソース':<25} {'デフォルト':<10}")
    print("-" * 85)
    for acct in accounts:
        default_mark = "★" if acct["is_default"] else ""
        print(f"{acct['name']:<20} {acct['email']:<30} {acct['source']:<25} {default_mark:<10}")


# PURPOSE: アカウントを削除する
def cmd_remove(args: argparse.Namespace) -> None:
    """アカウントを削除。"""
    from mekhane.ochema.token_vault import TokenVault

    vault = TokenVault()
    try:
        vault.remove_account(args.name)
        print(f"✅ アカウント '{args.name}' を削除しました。")
    except (OSError, KeyError) as e:
        logger.debug("Ignored exception: %s", e)
        print(f"❌ 削除失敗: {e}")


# PURPOSE: 全アカウントの健全性をチェックする
def cmd_check(args: argparse.Namespace) -> None:
    """全アカウントのトークン健全性をチェック。"""
    from mekhane.ochema.token_vault import TokenVault

    vault = TokenVault()
    accounts = vault.list_accounts()

    if not accounts:
        print("アカウントが登録されていません。")
        return

    # account_router の定義と照合
    try:
        from mekhane.ochema.account_router import PIPELINE_ACCOUNTS
        all_needed = set()
        for accts in PIPELINE_ACCOUNTS.values():
            all_needed.update(accts)
    except ImportError:
        all_needed = set()

    registered = {acct["name"] for acct in accounts}

    print("\n=== TokenVault ヘルスチェック ===\n")

    # 登録済みアカウントのトークンテスト
    for acct in accounts:
        name = acct["name"]
        try:
            token = vault.get_token(name)
            print(f"  ✅ {name:<20} トークン取得成功 (ya29...{token[-6:]})")
        except (OSError, KeyError) as e:
            logger.debug("Ignored exception: %s", e)
            print(f"  ❌ {name:<20} トークン取得失敗: {e}")

    # account_router で必要だが未登録のアカウント
    missing = all_needed - registered
    if missing:
        print(f"\n⚠️ account_router で必要だが未登録: {', '.join(sorted(missing))}")
        print("  登録方法: python -m mekhane.ochema.scripts.vault_setup add <name>")

    print()


# PURPOSE: メインエントリポイント
def main() -> None:
    """CLI エントリポイント。"""
    parser = argparse.ArgumentParser(
        description="TokenVault アカウント管理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # add
    add_p = sub.add_parser("add", help="アカウントを追加")
    add_p.add_argument("name", help="アカウント名 (例: movement)")
    add_p.set_defaults(func=cmd_add)

    # list
    list_p = sub.add_parser("list", help="アカウント一覧")
    list_p.set_defaults(func=cmd_list)

    # remove
    rm_p = sub.add_parser("remove", help="アカウントを削除")
    rm_p.add_argument("name", help="削除するアカウント名")
    rm_p.set_defaults(func=cmd_remove)

    # check
    check_p = sub.add_parser("check", help="全アカウントの健全性チェック")
    check_p.set_defaults(func=cmd_check)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
