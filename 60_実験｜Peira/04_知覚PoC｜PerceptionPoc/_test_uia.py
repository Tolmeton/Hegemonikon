"""uiautomation API 調査 v2 — WindowControl(Handle=h) パターン"""
import uiautomation as auto

# 1. ハンドルから WindowControl を取得
h = auto.GetForegroundWindow()
print(f"Handle: {h}")

# 2. ControlFromHandle で取得
try:
    ctrl = auto.ControlFromHandle(h)
    print(f"Name: {ctrl.Name}")
    print(f"ClassName: {ctrl.ClassName}")
    print(f"ControlType: {ctrl.ControlTypeName}")
    r = ctrl.BoundingRectangle
    if r:
        print(f"Rect: ({r.left}, {r.top}, {r.right}, {r.bottom})")
    
    # 直下の子要素を列挙
    children = ctrl.GetChildren()
    print(f"\nChildren: {len(children)}")
    for i, child in enumerate(children[:15]):
        try:
            name = child.Name or "(unnamed)"
            ctype = child.ControlTypeName
            cr = child.BoundingRectangle
            rect_str = f"({cr.left},{cr.top},{cr.right},{cr.bottom})" if cr else "None"
            print(f"  [{i}] {ctype}: '{name}' {rect_str}")
        except Exception as e:
            print(f"  [{i}] Error: {e}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
