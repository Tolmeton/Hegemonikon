#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ochema/scripts/ A0→外部LLM接続→LS単独稼働のためのOAuth認証
# PURPOSE: LS 固有の client_id で OAuth 認証を行い TokenVault に登録する
"""LS OAuth Authentication Script.

Language Server 固有の client_id で OAuth 認証を行い、
TokenVault にアカウントとして登録します。
これにより、バックエンド環境 (IDE 未起動) でも LS が単独で
Claude などの LLM にアクセスできるようになります。
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from mekhane.ochema.token_vault import TokenVault

# Antigravity Language Server credentials. Keep real values out of Git.
CLIENT_ID = os.environ.get("LS_OAUTH_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("LS_OAUTH_CLIENT_SECRET", "")
SCOPES = "https://www.googleapis.com/auth/cloud-platform https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"
REDIRECT_URI = "http://localhost"


def main():
    parser = argparse.ArgumentParser(description="Authenticate LS and register to TokenVault")
    parser.add_argument(
        "--account", "-a", 
        default="default", 
        help="TokenVault account name to register (default: 'default')"
    )
    args = parser.parse_args()

    account_name = args.account

    if not CLIENT_ID or not CLIENT_SECRET:
        print("LS_OAUTH_CLIENT_ID and LS_OAUTH_CLIENT_SECRET must be set in the environment.")
        sys.exit(1)

    print("=" * 60)
    print("LS 固有の OAuth 認証を開始します。")
    print(f"登録アカウント名: '{account_name}'")
    print()
    print("1. 以下の URL をブラウザで開いてログインしてください:")
    
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        + urllib.parse.urlencode({
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
        })
    )
    print(auth_url)
    print()
    print("2. ログイン後、ブラウザが http://localhost?code=... に")
    print("   リダイレクトされます。ページは表示されませんが、")
    print("   アドレスバーの URL 全体をコピーして以下に貼り付けてください。")
    print("=" * 60)
    print()

    raw_input = input("リダイレクト先の URL (または code) を貼り付けてください: ").strip()

    if not raw_input:
        print("入力が空です。終了します。")
        sys.exit(1)

    if "code=" in raw_input:
        parsed = urllib.parse.urlparse(raw_input)
        params = urllib.parse.parse_qs(parsed.query)
        auth_code = params.get("code", [None])[0]
    else:
        auth_code = raw_input

    if not auth_code:
        print("認証コードを抽出できませんでした。")
        sys.exit(1)

    print(f"\n認証コード: {auth_code[:20]}...")
    print("トークンを取得中...")

    data = urllib.parse.urlencode({
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"❌ エラー: {e.code}")
        print(e.read().decode())
        sys.exit(1)

    refresh_token = result.get("refresh_token")
    access_token = result.get("access_token")

    if not refresh_token:
        print("❌ refresh_token が取得できませんでした。")
        print("既に承認済みの場合は prompt=consent が効いていない可能性があります。")
        sys.exit(1)

    # get email via userinfo
    email = "unknown"
    try:
        req_req = urllib.request.Request("https://www.googleapis.com/oauth2/v1/userinfo?alt=json")
        req_req.add_header("Authorization", f"Bearer {access_token}")
        with urllib.request.urlopen(req_req) as u_resp:
            u_info = json.loads(u_resp.read())
            email = u_info.get("email", "unknown")
    except (OSError, json.JSONDecodeError) as _e:
        print(f"Ignored exception: {_e}")

    creds = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
        "access_token": access_token,
        "type": "authorized_user",
        "email": email,
    }

    # 一時ファイルに保存して TokenVault に登録
    vault = TokenVault()
    
    # default または指定アカウントを上書きするために削除を試みる
    target_account = vault.get_default_account() if account_name == "default" else account_name
    
    try:
        # If the target is default_account, we just override its json file but TokenVault API
        # might throw an error if we try to remove the default account.
        vault.remove_account(target_account)
        print(f"既存のアカウント '{target_account}' を一旦削除・上書きします。")
    except OSError as _e:
        print(f"Ignored exception: {_e}")

    fd, path = tempfile.mkstemp(suffix=".json")
    with open(fd, "w") as f:
        json.dump(creds, f)

    try:
        vault.add_account(target_account, Path(path), email=email)
        # default 指定時は default にセットする
        if account_name == "default":
            vault.set_default(target_account)
            
        print()
        print("=" * 60)
        print(f"✅ 成功! アカウント '{target_account}' を TokenVault に登録しました。")
        print(f"  email:         {email}")
        print(f"  refresh_token: {refresh_token[:15]}...")
        print("=" * 60)
    except OSError as e:
        print(f"Ignored exception: {e}")
        print(f"❌ TokenVault への登録に失敗しました: {e}")
    finally:
        Path(path).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
