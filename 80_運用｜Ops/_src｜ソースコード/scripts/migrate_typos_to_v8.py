import sys
import re
from pathlib import Path

def convert_to_v8(filepath: Path):
    content = filepath.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    name = filepath.stem
    depth = "L2"
    
    # Check for yaml frontmatter
    start_idx = 0
    if lines[0].strip() == "---":
        start_idx = 1
        while start_idx < len(lines) and lines[start_idx].strip() != "---":
            line = lines[start_idx].strip()
            if line.startswith("name:"):
                # name: "ccl-plan" or name: ccl-plan
                name = line.replace("name:", "").strip().strip('"\'')
            start_idx += 1
        if start_idx < len(lines) and lines[start_idx].strip() == "---":
            start_idx += 1
            
    # Also find if #depth is already defined
    for line in lines:
        if line.startswith("#depth:"):
            depth = line.replace("#depth:", "").strip()
            
    # Extract blocks
    blocks = {}
    current_block = None
    current_content = []
    
    # Pattern to match `@directive` or `@directive:`
    block_pattern = re.compile(r"^@(\w+):?\s*$")
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        
        # Skip legacy `#prompt` or `#depth` or `#syntax` headers if present
        if line.startswith("#prompt ") or line.startswith("#syntax:") or line.startswith("#depth:"):
            continue
            
        match = block_pattern.match(line)
        if match:
            if current_block:
                blocks[current_block] = "\n".join(current_content).strip()
            current_block = match.group(1)
            current_content = []
        else:
            if current_block:
                current_content.append(line)
            else:
                # Store content before any block as 'preamble' if it's not empty
                if line.strip():
                    if "preamble" not in blocks:
                        blocks["preamble"] = []
                    blocks["preamble"].append(line)
                    
    if current_block:
        blocks[current_block] = "\n".join(current_content).strip()
        
    # Reconstruct v8 format
    v8_lines = []
    v8_lines.append(f"#prompt {name}")
    v8_lines.append("#syntax: v8")
    v8_lines.append(f"#depth: {depth}")
    v8_lines.append("")
    
    if "preamble" in blocks:
        preamble = "\n".join(blocks["preamble"]).strip()
        if preamble:
            v8_lines.append(preamble)
            v8_lines.append("")
            
    for directive, value in blocks.items():
        if directive == "preamble":
            continue
        
        # Special formatting rules (optional, just raw for now)
        v8_lines.append(f"<:{directive}:")
        
        # indent value
        val_lines = value.split('\n')
        indented = []
        for vl in val_lines:
            if vl.strip():
                indented.append(f"  {vl}")
            else:
                indented.append("")
                
        v8_lines.extend(indented)
        v8_lines.append(":>")
        v8_lines.append("")
        
    output = "\n".join(v8_lines).strip() + "\n"
    filepath.write_text(output, encoding='utf-8')
    print(f"Converted {filepath.name} to v8 syntax.")

if __name__ == '__main__':
    target = Path(sys.argv[1])
    if target.is_file() and target.suffix == '.typos':
        convert_to_v8(target)
    elif target.is_dir():
        for file in target.rglob("*.typos"):
            convert_to_v8(file)
