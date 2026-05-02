#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/anamnesis/
"""
PROOF: [L3/ユーティリティ]

P3 → チャット履歴の保存が必要
   → CDP + websockets による履歴抽出
   → export_chats が担う

Q.E.D.

---

Antigravity IDE チャット履歴エクスポートツール v4
=================================================

websockets + CDP (Chrome DevTools Protocol) を使用して
Antigravity の Agent Manager からチャット履歴を DOM 経由で抽出し、
Markdown / JSON 形式で保存する。

v4 変更点:
  - Playwright 依存を除去: websockets + CDP 直接接続に統一
  - v3 品質改善を統合: UI ノイズ除去、テーブル変換、正規化ハッシュ重複検出
  - ロール判定: DOM data 属性優先 + section_idx + ヒューリスティック

使用方法:
    python export_chats.py                    # 全会話をエクスポート
    python export_chats.py --output sessions/ # 出力先指定
    python export_chats.py --format json      # JSON 形式で出力
    python export_chats.py --limit 5          # 最初の5件のみ
    python export_chats.py --list             # 会話リストのみ表示
    python export_chats.py --single "title"   # 現在の会話のみ
    python export_chats.py --watch            # 待機モード
    python export_chats.py --filter "Boot"    # タイトルフィルタ
    python export_chats.py --no-scroll        # スクロール無効（高速・部分取得）

必要条件:
    pip install websockets
"""

import asyncio
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import argparse
from mekhane.paths import HANDOFF_DIR

# ============================================================================
# 設定
# ============================================================================

# GCP/Linux 環境に対応
DEFAULT_OUTPUT_DIR = HANDOFF_DIR
CDP_PORT = 9334  # Chrome DevTools Protocol ポート (Electron IDE)

# メッセージ抽出の閾値
MIN_MESSAGE_LENGTH = 1  # 短い User 入力（y, /boot）も抽出
MAX_MESSAGE_CONTENT = 10000  # 保存するメッセージの最大長

# プリコンパイル正規表現
RE_THOUGHT_FOR = re.compile(r"^Thought for <?(\d+)s\s*")
RE_MULTI_NEWLINE = re.compile(r"\n{3,}")
RE_MULTI_SPACE = re.compile(r" {2,}")
RE_UNSAFE_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RE_MULTI_UNDERSCORE = re.compile(r"_+")

# UI ノイズパターン（Python 側フィルタ）
UI_NOISE_PATTERNS = [
    re.compile(r"^Analyzed\s+\S+#L\d+.*$", re.MULTILINE),
    re.compile(r"^Searched\s+\S+\d+\s+results?$", re.MULTILINE),
    re.compile(r"^Files Edited$", re.MULTILINE),
    re.compile(r"^Progress Updates\s*(Expand all|Collapse all)?\s*$", re.MULTILINE),
    re.compile(r"^Recent actions$", re.MULTILINE),
    re.compile(r"^(Open|Always run|Always Proceed|GoodBad|OpenProceed)\s*$", re.MULTILINE),
    re.compile(r"^MCP Tool:\s+.+$", re.MULTILINE),
    re.compile(r"^Show Details$", re.MULTILINE),
    re.compile(r"^Ran with these arguments:.*$", re.MULTILINE),
    re.compile(r"^Full output written to\s*$", re.MULTILINE),
    re.compile(r"^Ran command\s*(Open)?\s*(Always run)?\s*Exit code \d+$", re.MULTILINE),
    re.compile(r"^Generating\.{0,3}$", re.MULTILINE),
    re.compile(r"^Exit code:?\s*\d+$", re.MULTILINE),
]

# 完全にスキップすべき行パターン（行単位）
SKIP_LINE_PATTERNS = [
    re.compile(r"^Expand all\s*\d*$"),
    re.compile(r"^Collapse all\s*\d*$"),
    re.compile(r"^Manually proceeded\.$"),
    re.compile(r"^Asks for Review$"),
    re.compile(r"^Proceeded with.*$"),
    re.compile(r"^RunningOpen$"),
    re.compile(r"^\d+$"),  # 単独の数字行（Progress の番号）
    re.compile(r"^-\s*$"),  # 空リスト項目
    re.compile(r"^Task\s*$"),  # タスク UI ラベル
    re.compile(r"^Task[A-Z]\w{2,}.*$"),  # TaskXxx UI ラベル
    re.compile(r"^Error\s*$"),  # エラーラベル
    re.compile(r"^Agent execution terminated due to error\.\s*$"),
]

# コードブロック内の IDE CSS ノイズ
RE_CODE_BLOCK_CSS = re.compile(
    r"\t+\.code-block[^`]*?(?=```|$)",
    re.DOTALL
)


# ============================================================================
# CDP Page Proxy — websockets による直接 CDP 接続
# ============================================================================

class CDPPageProxy:
    """websockets + CDP で Electron ページに直接接続するプロキシ。
    Playwright の page.evaluate() 相当の機能を提供する。
    """

    def __init__(self, ws_url: str, page_url: str = ""):
        self.ws_url = ws_url
        self.url = page_url
        self.ws = None
        self._msg_id = 0

    async def connect(self):
        import websockets
        self.ws = await websockets.connect(
            self.ws_url,
            max_size=50 * 1024 * 1024,
            open_timeout=10,
            close_timeout=5,
        )

    async def _send(self, method: str, params: dict = None) -> dict:
        self._msg_id += 1
        msg = {"id": self._msg_id, "method": method}
        if params:
            msg["params"] = params
        await self.ws.send(json.dumps(msg))
        while True:
            raw = await asyncio.wait_for(self.ws.recv(), timeout=30)
            resp = json.loads(raw)
            if resp.get("id") == self._msg_id:
                if "error" in resp:
                    raise RuntimeError(f"CDP Error: {resp['error']}")
                return resp.get("result", {})

    async def evaluate(self, expression: str):
        """JS 式を評価して結果を返す。Playwright の page.evaluate() と同等。"""
        result = await self._send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
        })
        exc = result.get("exceptionDetails")
        if exc:
            raise RuntimeError(f"JS Error: {json.dumps(exc, ensure_ascii=False)[:500]}")
        return result.get("result", {}).get("value")

    async def close(self):
        if self.ws:
            await self.ws.close()


# ============================================================================
# CDP ユーティリティ
# ============================================================================

def cdp_get_json(endpoint: str, port: int, timeout: int = 30) -> list:
    """CDP HTTP エンドポイントから JSON を取得"""
    url = f"http://localhost:{port}{endpoint}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


async def find_best_jetski_page(pages: list) -> Optional[dict]:
    """全 jetski-agent ページの会話数をチェックし、最大のものを返す。
    複数ワークスペースが開いている場合でも正しいページを選択する。
    """
    import websockets

    candidates = [p for p in pages if "jetski-agent" in p.get("url", "")]
    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    # 各ページの会話数をチェック
    best = None
    best_count = -1

    for c in candidates:
        ws_url = c.get("webSocketDebuggerUrl")
        if not ws_url:
            continue
        try:
            async with websockets.connect(ws_url, max_size=10*1024*1024, open_timeout=5, close_timeout=3) as ws:
                msg = {"id": 1, "method": "Runtime.evaluate", "params": {
                    "expression": "document.querySelectorAll('button.select-none').length",
                    "returnByValue": True
                }}
                await ws.send(json.dumps(msg))
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                resp = json.loads(raw)
                count = resp.get("result", {}).get("result", {}).get("value", 0)
                print(f"    [{c.get('title', '?')}] {count} conversations")
                if count > best_count:
                    best_count = count
                    best = c
        except Exception as e:  # noqa: BLE001
            print(f"    [{c.get('title', '?')}] check failed: {e}")
            # フォールバック: Manager タイトルを優先
            if best is None and c.get("title", "").strip() == "Manager":
                best = c

    return best or candidates[0]


# ============================================================================
# JS テンプレート — メッセージ抽出・会話リスト・スクロール
# ============================================================================

JS_SCROLL_TOP = """
(() => {
    const c = document.querySelector('.flex.flex-col.gap-y-3.px-4.relative')
        || document.querySelector('.flex.flex-col.gap-y-3');
    if (!c) return;
    let el = c.parentElement;
    while (el) {
        const s = window.getComputedStyle(el);
        if (s.overflowY === 'auto' || s.overflowY === 'scroll') {
            el.scrollTop = 0;
            return;
        }
        el = el.parentElement;
    }
})()
"""

JS_SCROLL_DOWN = """
(() => {
    const c = document.querySelector('.flex.flex-col.gap-y-3.px-4.relative')
        || document.querySelector('.flex.flex-col.gap-y-3');
    if (!c) return -1;
    let el = c.parentElement;
    while (el) {
        const s = window.getComputedStyle(el);
        if (s.overflowY === 'auto' || s.overflowY === 'scroll') {
            el.scrollTop += 500;
            return el.scrollTop;
        }
        el = el.parentElement;
    }
    return -1;
})()
"""

JS_GET_CONVERSATIONS = """
(() => {
    const buttons = document.querySelectorAll('button.select-none');
    const convs = [];
    buttons.forEach((btn, idx) => {
        const span = btn.querySelector('span[data-testid], span.truncate');
        const title = span?.textContent?.trim();
        if (title && title.length > 2) {
            convs.push({idx, title: title.substring(0, 100)});
        }
    });
    return JSON.stringify(convs);
})()
"""

# v4: DOM 属性でロール検出 + UI ノイズ除外 + テーブル→Markdown 変換
JS_EXTRACT_MESSAGES = """
(() => {
    const selectors = [
        '.flex.flex-col.gap-y-3.px-4.relative',
        '.flex.flex-col.gap-y-3'
    ];
    let container = null;
    for (const sel of selectors) {
        container = document.querySelector(sel);
        if (container) break;
    }
    if (!container) return JSON.stringify({error: 'no container'});

    const noiseSelectors = [
        '[data-testid="progress-updates"]',
        '[data-testid="files-edited"]',
        '[data-testid="terminal-output"]',
        '.bg-ide-sidebar',
        '.bg-ide-panel',
        'button',
        '[role="toolbar"]',
        '[role="tablist"]',
        '.code-actions',
        '.inline-actions',
    ];

    const excludeTags = new Set(['STYLE', 'SCRIPT', 'SVG', 'IMG', 'VIDEO', 'CANVAS', 'IFRAME']);

    function tableToMarkdown(table) {
        const rows = table.querySelectorAll('tr');
        if (rows.length === 0) return '';
        let md = '\\n';
        rows.forEach((row, ri) => {
            const cells = row.querySelectorAll('th, td');
            const vals = Array.from(cells).map(c => c.textContent.trim().replace(/\\|/g, '\\\\|'));
            md += '| ' + vals.join(' | ') + ' |\\n';
            if (ri === 0) {
                md += '| ' + vals.map(() => '---').join(' | ') + ' |\\n';
            }
        });
        return md + '\\n';
    }

    function getCleanText(node, root) {
        let text = '';
        for (const child of node.childNodes) {
            if (child.nodeType === 3) {
                let parent = child.parentElement;
                let skip = false;
                while (parent && parent !== root) {
                    if (excludeTags.has(parent.tagName)) { skip = true; break; }
                    for (const ns of noiseSelectors) {
                        try { if (parent.matches(ns)) { skip = true; break; } } catch(e) {}
                    }
                    if (skip) break;
                    parent = parent.parentElement;
                }
                if (!skip) text += child.textContent;
            } else if (child.nodeType === 1) {
                const tag = child.tagName;
                if (excludeTags.has(tag)) continue;
                if (tag === 'BUTTON') continue;
                if (tag === 'TABLE') {
                    text += tableToMarkdown(child);
                    continue;
                }
                if (tag === 'PRE') {
                    const code = child.querySelector('code');
                    const lang = code ? (code.className.match(/language-(\\w+)/)?.[1] || '') : '';
                    const codeText = (code || child).textContent;
                    text += '\\n```' + lang + '\\n' + codeText + '\\n```\\n';
                    continue;
                }
                if (tag === 'CODE' && child.parentElement.tagName !== 'PRE') {
                    text += '`' + child.textContent + '`';
                    continue;
                }
                if (/^H[1-6]$/.test(tag)) {
                    const level = parseInt(tag[1]);
                    text += '\\n' + '#'.repeat(level) + ' ' + child.textContent.trim() + '\\n';
                    continue;
                }
                if (tag === 'LI') {
                    text += '\\n- ' + getCleanText(child, root);
                    continue;
                }
                const blockTags = new Set(['P', 'DIV', 'BLOCKQUOTE', 'UL', 'OL', 'SECTION', 'ARTICLE']);
                if (blockTags.has(tag)) {
                    text += '\\n' + getCleanText(child, root) + '\\n';
                    continue;
                }
                text += getCleanText(child, root);
            }
        }
        return text;
    }

    function detectRole(el) {
        let node = el;
        for (let i = 0; i < 5; i++) {
            if (!node) break;
            const role = node.getAttribute('data-turn-role')
                || node.getAttribute('data-role')
                || node.dataset?.turnRole
                || node.dataset?.role;
            if (role) {
                if (role === 'user' || role === 'human') return 'user';
                if (role === 'assistant' || role === 'model' || role === 'ai') return 'assistant';
            }
            if (node.getAttribute('data-is-user') === 'true') return 'user';
            if (node.getAttribute('data-is-user') === 'false') return 'assistant';
            node = node.parentElement;
        }
        const cls = el.className || '';
        if (cls.includes('user-message') || cls.includes('human-turn')) return 'user';
        if (cls.includes('assistant-message') || cls.includes('ai-turn')) return 'assistant';
        return null;
    }

    const results = [];
    const children = container.querySelectorAll(':scope > div');

    for (const child of children) {
        const text = getCleanText(child, child).trim();
        if (!text || text.length === 0) continue;

        const domRole = detectRole(child);
        const sectionIdx = child.getAttribute('data-section-index');

        results.push({
            clean_text: text,
            dom_role: domRole,
            section_idx: sectionIdx,
            raw_text: child.textContent || ""
        });
    }
    return JSON.stringify({count: results.length, messages: results});
})()
"""


def js_click_conversation(idx: int) -> str:
    return f"""
    (() => {{
        const buttons = document.querySelectorAll('button.select-none');
        if (buttons[{idx}]) {{
            buttons[{idx}].click();
            return true;
        }}
        return false;
    }})()
    """


# ============================================================================
# ロール判定（v4: DOM 属性優先 + section_idx + ヒューリスティック）
# ============================================================================

def classify_role(msg: dict) -> str:
    """メッセージのロールを判定"""
    dom_role = msg.get("dom_role")
    text = msg.get("clean_text", "")
    raw_text = msg.get("raw_text", "")
    section_idx = msg.get("section_idx")

    # 1. DOM 属性が最も信頼性が高い
    if dom_role:
        return dom_role

    # 2. section_idx による交互判定
    if section_idx is not None:
        try:
            return "user" if int(section_idx) % 2 == 0 else "assistant"
        except ValueError:
            pass

    # 3. Claude 検出パターン
    claude_patterns = [
        "Thought for", "Files Edited", "Progress Updates",
        "Background Steps", "Ran terminal command", "Open Terminal",
        "Exit code", "Always Proceed", "RunningOpen",
        "Analyzed", "Edited", "Generating", "GoodBad", "OpenProceed",
    ]
    if any(p in raw_text for p in claude_patterns):
        return "assistant"

    # 4. テキスト内容によるヒューリスティック
    first_line = text.split("\n")[0].strip() if text else ""

    if first_line.startswith("Thought for "):
        return "assistant"

    user_patterns = [
        r"^/\w",          # /boot, /bye 等
        r"^@\w",          # @plan, @next 等
        r"^Continue\s*$",
        r"^続けて\s*$",
        r"^はい\s*$",
        r"^いいえ\s*$",
        r"^(y|Y|ok|OK)\s*$",
        r"^再開\s*$",
        r"^GO\s*$",
    ]
    if len(text) < 500:
        for pat in user_patterns:
            if re.match(pat, first_line):
                return "user"

    return "assistant"


# ============================================================================
# テキストクリーニング（v4: UIノイズ除去、Thinking 保存）
# ============================================================================

def clean_message_text(text: str) -> str:
    """メッセージテキストのクリーニング。
    Thinking リークは保存する（Creator 方針）。UIノイズのみ除去。
    """
    text = RE_CODE_BLOCK_CSS.sub("", text)

    for pat in UI_NOISE_PATTERNS:
        text = pat.sub("", text)

    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if any(p.match(stripped) for p in SKIP_LINE_PATTERNS):
            continue
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    text = RE_MULTI_NEWLINE.sub("\n\n", text)
    text = RE_MULTI_SPACE.sub(" ", text)

    return text.strip()


def normalize_for_dedup(text: str) -> str:
    """重複検出用にテキストを正規化"""
    return re.sub(r"\s+", "", text)


# ============================================================================
# エクスポータークラス
# ============================================================================


class AntigravityChatExporter:
    """Antigravity IDE のチャット履歴をエクスポート (v4: websockets CDP)"""

    def __init__(self, output_dir: Path = DEFAULT_OUTPUT_DIR, limit: int = None, cdp_port: int = CDP_PORT):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chats: List[Dict] = []
        self.cdp: Optional[CDPPageProxy] = None
        self.limit = limit
        self.cdp_port = cdp_port
        self.filter_keyword = None
        self.no_scroll = False
        self.force_reexport = False

        print(f"[DEBUG] Output directory: {self.output_dir}")
        if limit:
            print(f"[DEBUG] Limit: {limit} conversations")

    # PURPOSE: CDP 経由で Antigravity のブラウザに接続
    async def connect(self) -> bool:
        """CDP 経由で jetski-agent ページに websockets で直接接続

        /json エンドポイントからページ一覧を取得し、
        jetski-agent の WebSocket URL に直接接続する。
        Playwright は使用しない（ハング問題の回避）。
        """
        try:
            cdp_url = f"http://localhost:{self.cdp_port}"
            print(f"[*] Connecting to CDP: {cdp_url}")

            # /json からページリストを取得
            try:
                pages = cdp_get_json("/json", port=self.cdp_port, timeout=30)
            except Exception as e:  # noqa: BLE001
                print(f"[✗] /json 取得失敗: {e}")
                print("    → Antigravity IDE が起動していることを確認してください")
                return False

            jetski = await find_best_jetski_page(pages)
            if not jetski:
                print(f"[✗] jetski-agent ページが見つかりません (全 {len(pages)} ページ)")
                return False

            ws_url = jetski.get("webSocketDebuggerUrl")
            if not ws_url:
                print("[✗] WebSocket URL が見つかりません")
                return False

            print(f"[✓] jetski-agent 検出: {jetski.get('title', 'unknown')}")
            print(f"    WS: {ws_url}")

            self.cdp = CDPPageProxy(ws_url, jetski.get("url", ""))
            await self.cdp.connect()
            print("[✓] WebSocket 接続成功")
            return True

        except Exception as e:  # noqa: BLE001
            print(f"[✗] Connection failed: {e}")
            print("    → Antigravity IDE が起動していることを確認してください")
            return False

    # PURPOSE: 会話リストを抽出
    async def extract_conversation_list(self) -> List[Dict]:
        """会話リストを抽出"""
        try:
            raw = await self.cdp.evaluate(JS_GET_CONVERSATIONS)
            convs = json.loads(raw)
            print(f"[*] Found {len(convs)} conversations")
            return convs
        except Exception as e:  # noqa: BLE001
            print(f"[!] Error finding conversations: {e}")
            return []

    # PURPOSE: スクロールしながらメッセージを収集する
    async def scroll_and_collect_messages(self) -> List[Dict]:
        """スクロールしながらメッセージを収集する

        仮想スクロールにより DOM からメッセージが消えるため、
        スクロールしながら逐次メッセージを収集し蓄積する。
        """
        all_messages = []
        seen_hashes = set()

        try:
            await self.cdp.evaluate(JS_SCROLL_TOP)
            await asyncio.sleep(1.0)

            max_iterations = 500
            same_scroll_count = 0
            prev_scroll_pos = -1

            print("    [*] Scrolling and collecting messages...")

            for i in range(max_iterations):
                raw = await self.cdp.evaluate(JS_EXTRACT_MESSAGES)
                data = json.loads(raw)

                if "error" in data:
                    if i == 0:
                        print(f"    [!] {data['error']} — retrying...")
                        for retry in range(20):
                            await asyncio.sleep(0.5)
                            raw = await self.cdp.evaluate(JS_EXTRACT_MESSAGES)
                            data = json.loads(raw)
                            if "error" not in data:
                                break
                        if "error" in data:
                            print("    [!] Container not found after retry")
                            return []
                    else:
                        break

                new_count = 0
                for msg in data.get("messages", []):
                    content = msg["clean_text"]
                    normalized = normalize_for_dedup(content)
                    content_hash = hash(normalized)
                    if content_hash not in seen_hashes:
                        seen_hashes.add(content_hash)
                        all_messages.append(msg)
                        new_count += 1

                if i % 20 == 0:
                    print(f"    [*] Scroll {i}: collected {len(all_messages)} (+{new_count})")

                scroll_pos = await self.cdp.evaluate(JS_SCROLL_DOWN)

                if scroll_pos == prev_scroll_pos:
                    same_scroll_count += 1
                    if same_scroll_count >= 3:
                        break
                else:
                    same_scroll_count = 0
                    prev_scroll_pos = scroll_pos

                await asyncio.sleep(0.15)

            print(f"    [✓] Collected {len(all_messages)} total messages")
            return all_messages

        except Exception as e:  # noqa: BLE001
            print(f"    [!] Scroll/collect error: {e}")
            import traceback
            traceback.print_exc()
            return all_messages

    # PURPOSE: 現在表示されている会話のメッセージを抽出（非スクロール版）
    async def extract_messages(self) -> List[Dict]:
        """現在表示されている会話のメッセージを抽出（スクロールなし）"""
        try:
            raw = await self.cdp.evaluate(JS_EXTRACT_MESSAGES)
            data = json.loads(raw)

            if "error" in data:
                print(f"    [!] {data['error']}")
                return []

            return data.get("messages", [])
        except Exception as e:  # noqa: BLE001
            print(f"    [!] Error extracting messages: {e}")
            return []

    # PURPOSE: 収集したメッセージをロール判定してフォーマット
    def _process_raw_messages(self, raw_messages: List[Dict]) -> List[Dict]:
        """収集したメッセージをロール判定・クリーニングしてフォーマット"""
        messages = []

        for msg in raw_messages:
            role = classify_role(msg)
            content = clean_message_text(msg.get("clean_text", ""))
            if content and len(content) >= MIN_MESSAGE_LENGTH:
                messages.append({
                    "role": role,
                    "content": content[:MAX_MESSAGE_CONTENT],
                    "section_index": msg.get("section_idx"),
                })

        # 隣接する同一ロールの完全重複を除去
        deduped = []
        for msg in messages:
            if deduped and deduped[-1]["role"] == msg["role"]:
                prev_norm = normalize_for_dedup(deduped[-1]["content"])
                cur_norm = normalize_for_dedup(msg["content"])
                if prev_norm == cur_norm:
                    continue
            deduped.append(msg)

        return deduped

    # PURPOSE: 全会話をエクスポート
    async def export_all(self):
        """全会話をエクスポート"""
        if not await self.connect():
            return

        try:
            conversations = await self.extract_conversation_list()

            if self.limit:
                conversations = conversations[:self.limit]
                print(f"[*] Limiting to {self.limit} conversations")

            if self.filter_keyword:
                print(f"[*] Filtering by keyword: '{self.filter_keyword}'")
                original_count = len(conversations)
                conversations = [
                    c for c in conversations
                    if self.filter_keyword.lower() in c["title"].lower()
                ]
                print(f"[*] Filtered: {original_count} -> {len(conversations)} conversations")

            # 差分チェック: 既存ファイルのタイトルを読み取り、スキップ対象を特定
            existing_titles = set()
            if not self.force_reexport:
                for md_file in self.output_dir.glob("*.md"):
                    try:
                        with open(md_file, "r", encoding="utf-8") as f:
                            first_line = f.readline().strip()
                            if first_line.startswith("# "):
                                existing_titles.add(first_line[2:].strip())
                    except Exception:  # noqa: BLE001
                        continue
                if existing_titles:
                    before = len(conversations)
                    conversations = [
                        c for c in conversations
                        if c["title"] not in existing_titles
                    ]
                    skipped = before - len(conversations)
                    print(f"[*] 差分チェック: {skipped} 件スキップ (既存 {len(existing_titles)} ファイル)")
                    print(f"[*] 残り {len(conversations)} 件をエクスポート")

            if not conversations:
                print("[✓] 全会話がエクスポート済みです")
                return

            exported = 0
            prev_first_msg = None

            for idx, conv in enumerate(conversations, 1):
                print(f"[{idx}/{len(conversations)}] {conv['title']}", flush=True)

                try:
                    # 会話をクリック
                    await self.cdp.evaluate(js_click_conversation(conv["idx"]))
                    await asyncio.sleep(1.5)  # UI 切替待機

                    # コンテナ出現を待機（最大15秒）
                    container_found = False
                    content_changed = False
                    for wait_i in range(30):
                        raw = await self.cdp.evaluate(JS_EXTRACT_MESSAGES)
                        data = json.loads(raw)
                        if "error" not in data:
                            container_found = True
                            if data.get("count", 0) > 0:
                                first = data["messages"][0]["clean_text"][:100]
                                if first != prev_first_msg:
                                    content_changed = True
                                    break
                        await asyncio.sleep(0.5)

                    if not container_found:
                        print("    [!] Container not found after 15s wait")

                    if not content_changed:
                        print("    [!] Content did not change, may be duplicate")

                    # メッセージ収集
                    if self.no_scroll:
                        raw = await self.cdp.evaluate(JS_EXTRACT_MESSAGES)
                        data = json.loads(raw)
                        if "error" in data:
                            print(f"    [!] {data['error']}")
                            continue
                        raw_messages = data.get("messages", [])
                    else:
                        raw_messages = await self.scroll_and_collect_messages()

                    if not raw_messages:
                        print("    [!] メッセージなし")
                        continue

                    messages = self._process_raw_messages(raw_messages)

                    # 会話間の重複チェック
                    if messages and prev_first_msg:
                        if messages[0]["content"][:100] == prev_first_msg:
                            print("    [!] Duplicate content detected, skipping...")
                            continue

                    prev_first_msg = messages[0]["content"][:100] if messages else None

                    # 記録を保存
                    chat_record = {
                        "id": f"conv_{conv['idx']}",
                        "title": conv["title"],
                        "exported_at": datetime.now().isoformat(),
                        "message_count": len(messages),
                        "messages": messages,
                    }
                    self.chats.append(chat_record)
                    self.save_single_chat(chat_record)
                    exported += 1
                    print(f"    → {len(messages)} messages extracted")

                except Exception as e:  # noqa: BLE001
                    print(f"    → Error: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            print(f"\n[✓] Export: {exported}/{len(conversations)} conversations")
        finally:
            await self.close()

    # PURPOSE: Markdown 形式で保存
    def save_markdown(self, filename: Optional[str] = None):
        """Markdown 形式で保存"""
        if not filename:
            filename = f"antigravity_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# Antigravity IDE チャット履歴\n\n")
            f.write(f"- **エクスポート日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **会話数**: {len(self.chats)}\n")
            f.write(f"- **総メッセージ数**: {sum(c['message_count'] for c in self.chats)}\n\n")
            f.write("---\n\n")

            for chat in self.chats:
                f.write(f"## {chat['title']}\n\n")
                f.write(f"- **ID**: `{chat['id']}`\n")
                f.write(f"- **メッセージ数**: {chat['message_count']}\n\n")

                for msg in chat["messages"]:
                    role_label = "👤 **User**" if msg["role"] == "user" else "🤖 **Claude**"
                    f.write(f"### {role_label}\n\n")
                    f.write(f"{msg['content']}\n\n")

                f.write("---\n\n")

        print(f"[✓] Saved: {filepath}")
        return filepath

    # PURPOSE: JSON 形式で保存
    def save_json(self, filename: Optional[str] = None):
        """JSON 形式で保存"""
        if not filename:
            filename = f"antigravity_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.chats, f, ensure_ascii=False, indent=2)

        print(f"[✓] Saved: {filepath}")
        return filepath

    # PURPOSE: 1つの会話を保存
    def save_single_chat(self, chat: Dict):
        """1つの会話を Markdown で保存"""
        title = chat["title"]
        safe_title = RE_UNSAFE_FILENAME.sub("", title)
        safe_title = "".join(c if ord(c) < 128 else "_" for c in safe_title)
        safe_title = RE_MULTI_UNDERSCORE.sub("_", safe_title).strip("_")[:60]

        if not safe_title:
            safe_title = "untitled"

        date_prefix = datetime.now().strftime("%Y-%m-%d")
        id_prefix = chat["id"][:8] if chat["id"] else "noname"

        filename = f"{date_prefix}_{id_prefix}_{safe_title}.md"
        filepath = self.output_dir / filename

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {chat['title']}\n\n")
                f.write(f"- **ID**: `{chat['id']}`\n")
                f.write(f"- **エクスポート日時**: {chat['exported_at']}\n")
                f.write(f"- **メッセージ数**: {chat['message_count']}\n\n")
                f.write("---\n\n")

                for msg in chat["messages"]:
                    role_label = "## 👤 User" if msg["role"] == "user" else "## 🤖 Claude"
                    f.write(f"{role_label}\n\n")
                    content = RE_MULTI_NEWLINE.sub("\n\n", msg["content"])
                    f.write(f"{content}\n\n")

            print(f"  [✓] Saved: {filename}")
        except Exception as e:  # noqa: BLE001
            print(f"  [!] Error saving file {filename}: {e}")
            import traceback
            traceback.print_exc()

    # PURPOSE: （非推奨：逐次保存を使用）各会話を個別ファイルとして保存
    def save_individual(self):
        """（非推奨：逐次保存を使用）各会話を個別ファイルとして保存"""
        print("[*] Re-saving all chats...")
        for chat in self.chats:
            self.save_single_chat(chat)

    # PURPOSE: リソースを解放
    async def close(self):
        """リソースを解放"""
        if self.cdp:
            await self.cdp.close()

    # PURPOSE: 現在表示されている会話のみをエクスポート（手動モード）
    async def export_single(self, title: str = "current_chat"):
        """現在表示されている会話のみをエクスポート（手動モード）"""
        if not await self.connect():
            return

        try:
            print(f"[*] Exporting current conversation: {title}")

            if self.no_scroll:
                raw_messages = await self.extract_messages()
            else:
                raw_messages = await self.scroll_and_collect_messages()

            if not raw_messages:
                print("[!] No messages found in current view")
                return

            messages = self._process_raw_messages(raw_messages)

            chat_record = {
                "id": f"manual_{datetime.now().strftime('%H%M%S')}",
                "title": title,
                "exported_at": datetime.now().isoformat(),
                "message_count": len(messages),
                "messages": messages,
            }
            self.chats.append(chat_record)
            self.save_single_chat(chat_record)

            print(f"    → {len(messages)} messages extracted")

        finally:
            await self.close()

    # PURPOSE: 待機モード: コンテンツ変化を検出して自動エクスポート
    async def export_watch(self):
        """待機モード: コンテンツ変化を検出して自動エクスポート"""
        if not await self.connect():
            return

        print("[*] 待機モード開始！")
        print("[*] Agent Manager で会話を切り替えると自動でエクスポートします")
        print("[*] 終了するには Ctrl+C を押してください")
        print()

        exported_hashes = set()
        last_content_hash = None
        export_count = 0

        try:
            while True:
                try:
                    messages = await self.extract_messages()

                    if messages:
                        content = "".join(
                            m.get("clean_text", "")[:200] for m in messages[:3]
                        )
                        content_hash = hash(content)

                        if (
                            content_hash != last_content_hash
                            and content_hash not in exported_hashes
                        ):
                            export_count += 1

                            title = (
                                messages[0]
                                .get("clean_text", "unknown")[:50]
                                .replace("\n", " ")
                            )

                            print(f"[{export_count}] 新しい会話を検出: {title[:30]}...")

                            processed = self._process_raw_messages(messages)

                            chat_record = {
                                "id": f"watch_{datetime.now().strftime('%H%M%S')}",
                                "title": title,
                                "exported_at": datetime.now().isoformat(),
                                "message_count": len(processed),
                                "messages": processed,
                            }
                            self.chats.append(chat_record)
                            self.save_single_chat(chat_record)

                            print(f"    → {len(processed)} messages extracted")

                            last_content_hash = content_hash
                            exported_hashes.add(content_hash)

                    await asyncio.sleep(1.0)

                except KeyboardInterrupt:
                    break
                except Exception as e:  # noqa: BLE001
                    print(f"[!] Error: {e}")
                    await asyncio.sleep(2.0)

        finally:
            print(f"\n[*] 待機モード終了。{export_count} 件の会話をエクスポートしました")
            await self.close()


# ============================================================================
# メイン
# ============================================================================


async def main():
    parser = argparse.ArgumentParser(
        description="Antigravity IDE チャット履歴エクスポート (v4: websockets CDP)"
    )
    parser.add_argument(
        "--output", "-o", type=Path, default=DEFAULT_OUTPUT_DIR,
        help=f"出力ディレクトリ (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--format", "-f", choices=["md", "json", "both", "individual"],
        default="individual", help="出力形式 (default: individual)",
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=None,
        help="エクスポートする会話数の上限 (テスト用)",
    )
    parser.add_argument(
        "--single", "-s", type=str, default=None, metavar="TITLE",
        help="手動モード: 現在表示されている会話だけをエクスポート",
    )
    parser.add_argument(
        "--watch", "-w", action="store_true",
        help="待機モード: 会話の切り替えを検出して自動エクスポート（Ctrl+C で終了）",
    )
    parser.add_argument(
        "--filter", type=str, default=None,
        help="指定した文字列をタイトルに含む会話のみエクスポート",
    )
    parser.add_argument(
        "--port", "-p", type=int, default=CDP_PORT,
        help=f"CDP (Chrome DevTools Protocol) ポート (default: {CDP_PORT})",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="会話リストのみ表示",
    )
    parser.add_argument(
        "--no-scroll", action="store_true",
        help="スクロール収集を無効化（高速・部分取得）",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="既にエクスポート済みの会話も再エクスポートする",
    )

    args = parser.parse_args()

    exporter = AntigravityChatExporter(output_dir=args.output, limit=args.limit, cdp_port=args.port)
    exporter.filter_keyword = args.filter
    exporter.no_scroll = args.no_scroll
    exporter.force_reexport = args.force

    try:
        if args.list:
            if not await exporter.connect():
                return 1
            try:
                convs = await exporter.extract_conversation_list()
                for i, c in enumerate(convs):
                    print(f"  [{i+1}] {c['title']}")
                return 0
            finally:
                await exporter.close()

        elif args.watch:
            await exporter.export_watch()
        elif args.single:
            await exporter.export_single(title=args.single)
        else:
            await exporter.export_all()

        if not exporter.chats:
            print("[!] No chats exported")
            return 1

        if args.format == "md":
            exporter.save_markdown()
        elif args.format == "json":
            exporter.save_json()
        elif args.format == "both":
            exporter.save_markdown()
            exporter.save_json()
        elif args.format == "individual":
            exporter.save_individual()

        print(f"\n[✓] Export complete: {len(exporter.chats)} conversations")
        return 0

    except Exception as e:  # noqa: BLE001
        print(f"[✗] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
