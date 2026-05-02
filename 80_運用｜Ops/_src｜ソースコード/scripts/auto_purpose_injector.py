import ast
import os
import sys
from pathlib import Path

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except Exception:
        return

    insertions = []
    
    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            self._handle_node(node, "関数", node.name)
            self.generic_visit(node)
            
        def visit_AsyncFunctionDef(self, node):
            self._handle_node(node, "非同期処理", node.name)
            self.generic_visit(node)
            
        def visit_ClassDef(self, node):
            self._handle_node(node, "クラス", node.name)
            self.generic_visit(node)
            
        def _handle_node(self, node, type_name, name):
            # node.lineno is 1-based
            line_idx = node.lineno - 1
            
            # Decorators handling
            if node.decorator_list:
                line_idx = node.decorator_list[0].lineno - 1
                
            # Check if there's already a PURPOSE comment
            if line_idx > 0 and lines[line_idx - 1].strip().startswith('# PURPOSE:'):
                return
                
            # Check if it's a test file or test function
            if name.startswith('test_') or 'test' in filepath.name:
                return
                
            # Insert PURPOSE
            human_name = name.replace('_', ' ')
            comment = f"{' ' * lines[line_idx].find(lines[line_idx].lstrip())}# PURPOSE: [L2-auto] {name} の{type_name}定義\n"
            insertions.append((line_idx, comment))

    Visitor().visit(tree)
    
    if not insertions:
        return
        
    # Apply insertions from bottom to top
    insertions.sort(key=lambda x: x[0], reverse=True)
    for line_idx, comment in insertions:
        lines.insert(line_idx, comment)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"Added {len(insertions)} PURPOSE comments to {filepath}")

if __name__ == "__main__":
    target_dir = Path("mekhane")
    for root, dirs, files in os.walk(target_dir):
        # Exclude tests
        if 'tests' in dirs:
            dirs.remove('tests')
        if 'tests_root' in dirs:
            dirs.remove('tests_root')
            
        for file in files:
            if file.endswith('.py') and not file.startswith('test_'):
                process_file(Path(root) / file)
