"""
HGK Perception-Action PoC — windows_agent.py
=============================================
PURPOSE: HGK に「目と手」を与える最小の知覚-運動ループ。
  Perceive (画面キャプチャ + accessibility tree)
  → Decide (Florence-2 Vision API で UI 要素検出)
  → Act (マウスクリック)

実行方法 (WSL2 から):
  cmd.exe /c "python C:\\path\\to\\windows_agent.py"
  
  または
  cmd.exe /c "python \\\\wsl.localhost\\Debian\\home\\makaron8426\\Sync\\oikos\\01_ヘゲモニコン｜Hegemonikon\\60_実験｜Peira\\perception_poc\\windows_agent.py"

依存: pip install mss uiautomation requests
"""

import sys
import time
import json
import base64
import io
import argparse
from typing import Optional

try:
    import mss
    import mss.tools
    import requests
    import uiautomation as auto
    from PIL import Image
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("Install: python -m pip install mss uiautomation requests Pillow")
    sys.exit(1)


# --- Configuration ---
FLORENCE2_API = "http://100.83.204.102:8780"
DEFAULT_TASK = "<OD>"  # Object Detection
DEFAULT_PROMPT = ""
MAX_WIDTH = 1024  # Florence-2 (GTX 1050 Ti) 用リサイズ


def perceive_screen(monitor_index: int = 1, max_width: int = MAX_WIDTH) -> tuple[bytes, dict]:
    """L1 Perception: スクリーンキャプチャ + リサイズ"""
    with mss.mss() as sct:
        monitor = sct.monitors[monitor_index]
        screenshot = sct.grab(monitor)
        
        orig_w = screenshot.size.width
        orig_h = screenshot.size.height
        
        # PIL Image に変換
        img = Image.frombytes("RGB", (orig_w, orig_h), screenshot.rgb)
        
        # リサイズ (アスペクト比維持)
        scale = 1.0
        if orig_w > max_width:
            scale = max_width / orig_w
            new_w = max_width
            new_h = int(orig_h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            print(f"[PERCEIVE/Screen] Captured {orig_w}x{orig_h}, resized to {new_w}x{new_h} (scale={scale:.3f})")
        else:
            print(f"[PERCEIVE/Screen] Captured {orig_w}x{orig_h} (no resize needed)")
        
        # PNG bytes に変換
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        
        return png_bytes, {
            "orig_width": orig_w,
            "orig_height": orig_h,
            "width": img.size[0],
            "height": img.size[1],
            "scale": scale,
            "monitor": monitor,
        }


def perceive_accessibility() -> dict:
    """L1 Perception: accessibility tree (アクティブウィンドウ)"""
    try:
        # GetForegroundWindow() は int (ハンドル) を返す
        hwnd = auto.GetForegroundWindow()
        window = auto.ControlFromHandle(hwnd) if hwnd else None
        
        result = {
            "window_name": window.Name if window else "Unknown",
            "window_class": window.ClassName if window else "Unknown",
            "window_handle": hwnd,
            "children_summary": [],
        }
        
        # アクティブウィンドウの直下の子要素を取得 (最大 20 個)
        if window:
            children = window.GetChildren()
            for i, child in enumerate(children[:20]):
                try:
                    cr = child.BoundingRectangle
                    result["children_summary"].append({
                        "name": child.Name or "(unnamed)",
                        "type": child.ControlTypeName,
                        "rect": {
                            "left": cr.left,
                            "top": cr.top,
                            "right": cr.right,
                            "bottom": cr.bottom,
                        } if cr else None,
                    })
                except Exception:
                    result["children_summary"].append({
                        "name": "(error)",
                        "type": "Unknown",
                        "rect": None,
                    })
        
        print(f"[PERCEIVE/A11y] Window: '{result['window_name']}' | "
              f"Children: {len(result['children_summary'])}")
        return result
    except Exception as e:
        print(f"[PERCEIVE/A11y] Error: {e}")
        return {"error": str(e)}


def decide_detect(png_bytes: bytes, task: str = DEFAULT_TASK, 
                   text_input: str = DEFAULT_PROMPT) -> list[dict]:
    """Decide: Florence-2 API で UI 要素を検出"""
    try:
        # API は multipart/form-data で file フィールドを要求、task は query param
        files = {"file": ("screenshot.png", png_bytes, "image/png")}
        params = {"task": task}
        
        t0 = time.time()
        resp = requests.post(
            f"{FLORENCE2_API}/detect",
            files=files,
            params=params,
            timeout=30,
        )
        elapsed = time.time() - t0
        
        if resp.status_code != 200:
            print(f"[DECIDE] API error: {resp.status_code} {resp.text[:200]}")
            return []
        
        result = resp.json()
        detections = result.get("results", [])
        print(f"[DECIDE] {len(detections)} detections in {elapsed:.2f}s (task={task})")
        
        for det in detections[:10]:
            label = det.get("label", "?")
            bbox = det.get("bbox", [])
            print(f"  → {label}: bbox={bbox}")
        
        return detections
    except Exception as e:
        print(f"[DECIDE] Error: {e}")
        return []


def decide_ocr(png_bytes: bytes) -> list[dict]:
    """Decide: Florence-2 API で OCR (テキスト + 座標)"""
    return decide_detect(png_bytes, task="<OCR_WITH_REGION>")


def act_click(x: int, y: int, delay: float = 0.5):
    """L2 Action: 指定座標をクリック"""
    print(f"[ACT] Clicking at ({x}, {y}) ...")
    time.sleep(delay)  # 安全のための遅延
    auto.Click(x, y)
    print(f"[ACT] Clicked at ({x}, {y})")


def act_move(x: int, y: int):
    """L2 Action: マウスを移動 (クリックなし)"""
    print(f"[ACT] Moving to ({x}, {y}) ...")
    auto.MoveTo(x, y)


# --- Main Loop ---

def run_perceive_only():
    """知覚のみ実行 (操作なし) — デモ・デバッグ用"""
    print("=" * 60)
    print("[HGK Perception-Action PoC] Perceive-Only Mode")
    print("=" * 60)
    
    # Perceive: Screen
    png_bytes, screen_info = perceive_screen()
    
    # Perceive: Accessibility
    a11y = perceive_accessibility()
    
    # Decide: Object Detection
    detections = decide_detect(png_bytes)
    
    # Decide: OCR
    ocr_results = decide_ocr(png_bytes)
    
    # Summary
    print("\n" + "=" * 60)
    print("[SUMMARY]")
    print(f"  Screen: {screen_info['width']}x{screen_info['height']}")
    print(f"  Window: {a11y.get('window_name', 'Unknown')}")
    print(f"  OD detections: {len(detections)}")
    print(f"  OCR regions: {len(ocr_results)}")
    print("=" * 60)
    
    return {
        "screen_info": screen_info,
        "a11y": a11y,
        "detections": detections,
        "ocr_results": ocr_results,
    }


def run_perception_action_loop(target_text: str, action: str = "move"):
    """知覚-運動ループ (UIA 構造探索版): 指定テキスト名を持つコントロールを探して操作する
    Florence-2 の OCR が重いため、Windows UIA を Perceive と Decide の両方に使う。
    """
    print("=" * 60)
    print(f"[HGK Perception-Action PoC] UIA Loop Mode")
    print(f"  Target Name: '{target_text}'")
    print(f"  Action: {action}")
    print("=" * 60)
    
    # Perceive: Accessibility Tree の探索
    print("[PERCEIVE] Searching in Desktop Accessibility Tree...")
    try:
        # デスクトップ全体から指定した名前に部分一致するコントロールを探す
        target_control = auto.Control(searchDepth=5, Name=target_text, RegexName=f".*{target_text}.*")
        
        if not target_control.Exists(3, 1):
            print(f"\n[RESULT] Target '{target_text}' not found in UIA tree (depth=5).")
            return {"found": False, "target": target_text}
            
        name = target_control.Name
        ctype = target_control.ControlTypeName
        rect = target_control.BoundingRectangle
        
        print(f"\n[MATCH] Found {ctype}: '{name}' at {rect}")
        
        if not rect:
            print("[ACT] Cannot act: No BoundingRectangle available.")
            return {"found": True, "target": target_text, "error": "No rect"}
            
        cx = int((rect.left + rect.right) / 2)
        cy = int((rect.top + rect.bottom) / 2)
        print(f"  Center: ({cx}, {cy})")
        
        # Act
        if action == "click":
            act_click(cx, cy)
        elif action == "move":
            act_move(cx, cy)
        else:
            print(f"[ACT] Unknown action: {action}")
        
        return {
            "found": True,
            "target": target_text,
            "match": {
                "name": name,
                "type": ctype,
                "rect": (rect.left, rect.top, rect.right, rect.bottom)
            },
            "center": (cx, cy),
            "action": action,
        }
        
    except Exception as e:
        print(f"[ERROR] UIA Loop failed: {e}")
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="HGK Perception-Action PoC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python windows_agent.py perceive          # 知覚のみ (操作なし)
  python windows_agent.py find "スタート"   # テキストを見つけてマウスを移動
  python windows_agent.py click "OK"        # テキストを見つけてクリック
  python windows_agent.py a11y              # accessibility tree のみ表示
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # perceive
    subparsers.add_parser("perceive", help="Perceive only (no action)")
    
    # find
    find_parser = subparsers.add_parser("find", help="Find text and move mouse")
    find_parser.add_argument("target", help="Text to find on screen")
    
    # click
    click_parser = subparsers.add_parser("click", help="Find text and click")
    click_parser.add_argument("target", help="Text to click on screen")
    
    # a11y
    subparsers.add_parser("a11y", help="Show accessibility tree only")
    
    args = parser.parse_args()
    
    if args.command == "perceive":
        result = run_perceive_only()
        print(f"\n[OUTPUT] {json.dumps(result, indent=2, ensure_ascii=False, default=str)[:2000]}")
        
    elif args.command == "find":
        result = run_perception_action_loop(args.target, action="move")
        print(f"\n[OUTPUT] {json.dumps(result, indent=2, ensure_ascii=False, default=str)}")
        
    elif args.command == "click":
        result = run_perception_action_loop(args.target, action="click")
        print(f"\n[OUTPUT] {json.dumps(result, indent=2, ensure_ascii=False, default=str)}")
        
    elif args.command == "a11y":
        a11y = perceive_accessibility()
        print(f"\n[OUTPUT] {json.dumps(a11y, indent=2, ensure_ascii=False, default=str)}")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
