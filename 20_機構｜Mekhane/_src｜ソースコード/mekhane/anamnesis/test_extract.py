#!/usr/bin/env python3
# PROOF: [L3/テスト] <- mekhane/anamnesis/
"""
PROOF: [L3/テスト] export_chats が存在→その検証が必要→test_extract が担う

---

メッセージ抽出テスト

1 つの会話をクリック
メッセージを抽出
ファイルに保存
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path

CDP_PORT = 9222
OUTPUT_DIR = Path(r"M:\Brain\05_状態｜State\sessions")


# PURPOSE: メッセージを抽出
async def extract_messages(page):
    """メッセージを抽出"""
    messages = []

    try:
        # メッセージコンテナを探す
        container = await page.query_selector(".flex.flex-col.gap-y-3.px-4.relative")

        if not container:
            container = await page.query_selector(".flex.flex-col.gap-y-3")

        if not container:
            print("    [!] Message container not found")
            return []

        # 直接の子要素を取得
        children = await container.query_selector_all(":scope > div")
        print(f"    Found {len(children)} child elements")

        for child in children:
            try:
                classes = await child.get_attribute("class") or ""
                if "bg-gray-500" in classes:
                    continue

                content = await child.text_content()
                if not content or len(content.strip()) < 10:
                    continue

                # CSS ノイズを除去
                clean = content.strip()
                if clean.startswith("/*"):
                    end = clean.find("*/")
                    if end > 0:
                        clean = clean[end + 2 :].strip()

                # @media ルールを除去
                while clean.startswith("@media") or clean.startswith(".markdown"):
                    brace_count = 0
                    for i, c in enumerate(clean):
                        if c == "{":
                            brace_count += 1
                        elif c == "}":
                            brace_count -= 1
                            if brace_count == 0:
                                clean = clean[i + 1 :].strip()
                                break
                    else:
                        break

                if len(clean) < 10:
                    continue

                # ロール判定
                role = "assistant"
                if any(
                    clean.startswith(p)
                    for p in ["@", "/", "Continue", "y", "ok", "続けて"]
                ):
                    if len(clean) < 500:
                        role = "user"

                messages.append({"role": role, "content": clean[:3000]})
                print(f"    Extracted: {role} ({len(clean)} chars)")

            except Exception:  # noqa: BLE001
                continue

        return messages

    except Exception as e:  # noqa: BLE001
        print(f"    [!] Error: {e}")
        return []


# PURPOSE: main の処理
async def main():
    from playwright.async_api import async_playwright

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")

        # 正しいページを選択
        agent_pages = []
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "jetski-agent" in pg.url:
                    try:
                        buttons = await pg.query_selector_all("button.select-none")
                        agent_pages.append((pg, len(buttons)))
                    except Exception:  # noqa: BLE001
                        pass  # TODO: Add proper error handling

        if not agent_pages:
            print("[!] Agent Manager not found")
            return

        agent_pages.sort(key=lambda x: x[1], reverse=True)
        page = agent_pages[0][0]
        print(f"[✓] Selected: {agent_pages[0][1]} buttons")

        # 会話をクリック（force=True）
        buttons = await page.query_selector_all("button.select-none")
        conv_title = None

        for btn in buttons:
            try:
                title_el = await btn.query_selector("span[data-testid], span.truncate")
                if title_el:
                    title = await title_el.text_content()
                    if title and len(title.strip()) > 5 and "Inbox" not in title:
                        conv_title = title.strip()
                        print(f"[*] Clicking: {conv_title[:50]}")
                        await btn.click(force=True)
                        await asyncio.sleep(3)
                        break
            except Exception:  # noqa: BLE001
                continue

        if not conv_title:
            print("[!] No conversation clicked")
            return

        # メッセージを抽出
        print("[*] Extracting messages...")
        messages = await extract_messages(page)
        print(f"[*] Extracted {len(messages)} messages")

        # ファイルに保存
        if messages:
            safe_title = "".join(
                c if (ord(c) < 128 and ord(c) >= 32) else "_" for c in conv_title
            )
            safe_title = re.sub(r'[<>:"/|?*\n\r]', "", safe_title)
            safe_title = (
                re.sub(r"[\s_]+", "_", safe_title).strip("_")[:50] or "untitled"
            )

            filename = (
                f"test_extract_{datetime.now().strftime('%H%M%S')}_{safe_title}.md"
            )
            filepath = OUTPUT_DIR / filename

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {conv_title}\n\n")
                f.write(f"- **Exported**: {datetime.now().isoformat()}\n")
                f.write(f"- **Messages**: {len(messages)}\n\n")
                f.write("---\n\n")

                for msg in messages:
                    role_label = (
                        "## 👤 User" if msg["role"] == "user" else "## 🤖 Claude"
                    )
                    f.write(f"{role_label}\n\n")
                    f.write(f"{msg['content']}\n\n")

            print(f"[✓] Saved: {filepath}")
        else:
            print("[!] No messages extracted")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
