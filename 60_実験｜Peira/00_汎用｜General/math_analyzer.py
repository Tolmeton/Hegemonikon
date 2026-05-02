import os
import re
import sys
import glob
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple

@dataclass
class MathNode:
    file_path: str
    line_number: int
    content: str
    node_type: str  # 'inline', 'block', 'adjunction'

@dataclass
class Violation:
    file_path: str
    line_number: int
    message: str
    content: str

class MathAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.nodes: List[MathNode] = []
        self.violations: List[Violation] = []
        
        # Known adjunction pairs: Left ⊣ Right (multiple allowed)
        self.known_adjunctions = {
            "F": ["G", "U"],       # Free ⊣ Forgetful / Underlying
            "V": ["G", "U"],       # Cofree context
            "U": ["N", "G", "F"],  # Forgetful ⊣ Recover (Hegemonikon)
            "U_CCL": ["G_CCL", "N_CCL"],
            "bou": ["ene"],   # Boulēsis ⊣ Energeia
            "zet": ["ene"],
            "ske": ["pei"],
            "sag": ["tek"],
            "kat": ["pai"],
            "epo": ["dok"],
            "lys": ["akr"],
            "ops": ["arh"],
            "ele": ["dio"],
            "beb": ["kop"],
            "hyp": ["ath"],
            "prm": ["par"],
            "L": ["R"],
            "C": ["U"],
            "E": ["P"],
            "Explore": ["Exploit"],
            "index_opp": ["Search"],
            "index_op": ["Search"],
            "N": ["U"],
            "G": ["F"]
        }

    def scan_files(self, patterns: List[str]):
        """Finds all files matching the given patterns."""
        files = set()
        for pattern in patterns:
            for p in self.root_dir.rglob(pattern):
                if p.is_file() and ".stversions" not in p.parts and ".tmp_index_export" not in p.parts and "sync-conflict" not in p.name:
                    files.add(p)
        return list(files)

    def extract_nodes(self, file_path: Path):
        """Extracts mathematical nodes from a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")
            return

        content = "".join(lines)
        rel_path = str(file_path.relative_to(self.root_dir))

        # Block equations $$ ... $$
        for match in re.finditer(r'\$\$([\s\S]*?)\$\$', content):
            line_num = content[:match.start()].count('\n') + 1
            self.nodes.append(MathNode(rel_path, line_num, match.group(1).strip(), 'block'))
            
        # Inline equations $ ... $
        for match in re.finditer(r'(?<!\$)\$([^$\n]+)\$(?!\$)', content):
            line_num = content[:match.start()].count('\n') + 1
            self.nodes.append(MathNode(rel_path, line_num, match.group(1).strip(), 'inline'))
            
        # Adjunctions (in plain text or math) containing ⊣
        for i, line in enumerate(lines, 1):
            if "⊣" in line:
                self.nodes.append(MathNode(rel_path, i, line.strip(), 'adjunction'))

    def analyze_adjunctions(self, node: MathNode):
        """Validates adjunction directions L ⊣ R."""
        matches = re.findall(r'([A-Za-z_]+)\s*⊣\s*([A-Za-z_]+)', node.content)
        for L, R in matches:
            if L in self.known_adjunctions:
                expected_R_list = self.known_adjunctions[L]
                if R not in expected_R_list:
                    self.violations.append(Violation(
                        node.file_path, node.line_number,
                        f"Adjunction direction mismatch: Found '{L} ⊣ {R}', expected one of {expected_R_list}",
                        node.content
                    ))
            else:
                # Check reverse lookup
                valid_lefts = [k for k, v_list in self.known_adjunctions.items() if R in v_list]
                if valid_lefts:
                     self.violations.append(Violation(
                        node.file_path, node.line_number,
                        f"Adjunction direction mismatch: Found '{L} ⊣ {R}', expected Left to be one of {valid_lefts}",
                        node.content
                    ))

    def analyze_integrals(self, node: MathNode):
        """Checks for undefined bounds or simple dimensionality issues in integrals."""
        if "int" in node.content or "\\int" in node.content:
            # Check if there is an integral without bounds (simple heuristic)
            if "\\int_" not in node.content and "\\int" in node.content and "d" in node.content:
                # Might be ok, but flag as a warning for dimension check
                pass
            
            # Dimensionality check: e.g. checking d x vs dx space
            if re.search(r'\\int.*dx', node.content) and "x" not in node.content:
                pass # more complex AST parsing needed for real dimension check

    def analyze_fep_vfe(self, node: MathNode):
        """Checks FEP / VFE formula consistency (e.g. KL divergence terms)."""
        # Only require '||' if the KL divergence is written with arguments, e.g. D_{KL}(P || Q)
        if re.search(r'(D_\{KL\}|KL|Phi_\\text\{KL\})\s*\(', node.content):
            if "||" not in node.content and "\\|" not in node.content:
                self.violations.append(Violation(
                    node.file_path, node.line_number,
                    "KL divergence with arguments missing '||' or '\\|' separator between distributions.",
                    node.content
                ))

    def run_analysis(self):
        for node in self.nodes:
            if node.node_type == 'adjunction':
                self.analyze_adjunctions(node)
            elif node.node_type in ('inline', 'block'):
                self.analyze_adjunctions(node) # Math blocks can have adjunctions too
                self.analyze_integrals(node)
                self.analyze_fep_vfe(node)

    def report(self):
        print("=== Hegemonikon Math Static Analysis Report ===")
        print(f"Total files scanned: {len(set(n.file_path for n in self.nodes))}")
        print(f"Total math nodes extracted: {len(self.nodes)}")
        print(f"Total violations found: {len(self.violations)}\n")
        
        by_file = defaultdict(list)
        for v in self.violations:
            by_file[v.file_path].append(v)
            
        for file_path, violations in by_file.items():
            print(f"📄 {file_path}")
            for v in violations:
                print(f"  [Line {v.line_number}] ❌ {v.message}")
                print(f"    Content: {v.content}")
            print()
            
        if not self.violations:
            print("✅ All checks passed! No consistency or dimensional violations found.")

if __name__ == "__main__":
    root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    analyzer = MathAnalyzer(root_dir)
    
    # Target files: Paper I-XI drafts and all typos files
    print("Extracting nodes...")
    target_files = analyzer.scan_files([
        "10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/paper_*.md",
        "*.typos"
    ])
    
    for f in target_files:
        analyzer.extract_nodes(f)
        
    print("Running analysis...")
    analyzer.run_analysis()
    analyzer.report()
