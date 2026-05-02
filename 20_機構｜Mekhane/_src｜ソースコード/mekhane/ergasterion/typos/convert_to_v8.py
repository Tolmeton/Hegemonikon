# PROOF: mekhane/ergasterion/typos/convert_to_v8.py
# PURPOSE: ergasterion モジュールの convert_to_v8
import sys
from pathlib import Path
from mekhane.ergasterion.typos.typos import PromptLangParser

def format_prompt(input_path: Path, output_path: Path):
    content = input_path.read_text(encoding="utf-8")
    parser = PromptLangParser(content)
    prompt = parser.parse()
    # to_v8 outputs the modern v8 syntax representation
    v8_content = prompt.to_v8()
    output_path.write_text(v8_content, encoding="utf-8")
    print(f"Converted {input_path.name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_to_v8.py <file_or_dir>")
        sys.exit(1)
        
    target = Path(sys.argv[1])
    if target.is_file():
        format_prompt(target, target)
    elif target.is_dir():
        for file in target.rglob("*.typos"):
            format_prompt(file, file)
