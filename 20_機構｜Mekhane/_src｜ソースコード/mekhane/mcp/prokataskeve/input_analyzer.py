from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/prokataskeve/input_analyzer.py
"""
InputAnalyzer — L0 rule-based input analysis.

Contains:
  - normalize (Akribeia, A×Mi) — L0
  - extract_entities (Analysis, I×Mi) — L0
  - extract_certain (Katalēpsis, I×C) — L0
  - detect_ambiguity (Epochē, I×U) — L2
"""

import re
import unicodedata

from mekhane.mcp.prokataskeve.models import (
    AmbiguitySpan,
    CertainSpan,
    Entity,
    EntityType,
)


# =============================================================================
# Compiled patterns (module-level singletons)
# =============================================================================

_PATH_PATTERN = re.compile(
    r'(?:^|[\s"\'(])(/(?:[a-zA-Z0-9_\-\.]+/)*[a-zA-Z0-9_\-\.]+)',
    re.MULTILINE,
)
_URL_PATTERN = re.compile(
    r'https?://[^\s<>\"\')\]]+',
)
_NUMBER_PATTERN = re.compile(
    r'\b\d+(?:\.\d+)?(?:%|ms|s|KB|MB|GB|件|個|回|日|時間|分|秒)?\b',
)
_CCL_PATTERN = re.compile(
    r'(?:^|\s)(/[a-z]{2,4}[+\-]*(?:\s*>>\s*/[a-z]{2,4}[+\-]*)*)',
    re.MULTILINE,
)
_CODE_BLOCK_PATTERN = re.compile(
    r'```[\s\S]*?```|`[^`\n]+`',
)
_QUOTED_PATTERN = re.compile(
    r'「[^」]+」|"[^"]+"|\'[^\']+\'',
)
_FULLWIDTH_MAP = str.maketrans(
    'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ'
    '０１２３４５６７８９（）［］｛｝',
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    '0123456789()[]{}',
)
_BLOCKQUOTE_PATTERN = re.compile(r'(?:^>[^\n]*(?:\n|$))+', re.MULTILINE)

# Ambiguity detection patterns (L2 Epochē)
_AMBIGUITY_PATTERNS = [
    (re.compile(r'さっき(?:の)?|先ほど(?:の)?|前(?:の)?|上(?:の)?'), "unresolved_ref", "具体的な対象を指定してください"),
    (re.compile(r'これ|この|それ|その|あれ|あの'), "unresolved_ref", "具体的な対象が必要です"),
    (re.compile(r'あたり|くらい|ぐらい|程度|ほど'), "vague_scope", "具体的な数値や範囲を指定してください"),
    (re.compile(r'(?:^|[。、\s])(?:直して|変えて|修正して|更新して)'), "omitted_subject", "何を修正するか明示してください"),
    (re.compile(r'(?:いい感じ|適当|うまく|なんとか)(?:に|して)'), "vague_scope", "具体的な要件を指定してください"),
]


# =============================================================================
# L0: normalize (Akribeia)
# =============================================================================


# PURPOSE: L0 正規化 (Akribeia, A×Mi — 局所的に正確に行動する)
def normalize(text: str) -> str:
    """L0 Normalize input text.

    - Full-width → half-width conversion
    - Unicode NFKC normalization
    - Collapse multiple whitespace
    - Strip leading/trailing whitespace
    """
    result = unicodedata.normalize("NFKC", text)
    result = result.translate(_FULLWIDTH_MAP)
    result = re.sub(r'[^\S\n]+', ' ', result)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


# =============================================================================
# L0: extract_entities (Analysis)
# =============================================================================


# PURPOSE: L0 エンティティ抽出 (Analysis, I×Mi — 局所的に深く推論する)
def extract_entities(text: str) -> list[Entity]:
    """L0 Extract entities from text using regex patterns.

    Detects: file paths, URLs, numbers with units, CCL expressions,
    code blocks, quoted strings, language.
    """
    entities: list[Entity] = []

    # Code blocks (extract first to avoid false positives inside code)
    for m in _CODE_BLOCK_PATTERN.finditer(text):
        entities.append(Entity(
            type=EntityType.CODE_BLOCK, value=m.group(),
            start=m.start(), end=m.end(),
        ))

    # Quoted strings
    for m in _QUOTED_PATTERN.finditer(text):
        entities.append(Entity(
            type=EntityType.QUOTED, value=m.group(),
            start=m.start(), end=m.end(),
        ))

    # URLs (before paths to avoid URL-path confusion)
    for m in _URL_PATTERN.finditer(text):
        entities.append(Entity(
            type=EntityType.URL, value=m.group(),
            start=m.start(), end=m.end(),
        ))

    # CCL expressions (before paths — /noe+ would match PATH as /noe otherwise)
    for m in _CCL_PATTERN.finditer(text):
        ccl_val = m.group(1).strip()
        if any(e.start <= m.start(1) < e.end for e in entities):
            continue
        end_pos = m.end(1)
        if end_pos < len(text) and text[end_pos] in ('/', '.'):
            continue
        entities.append(Entity(
            type=EntityType.CCL, value=ccl_val,
            start=m.start(1), end=m.end(1),
        ))

    # File paths
    for m in _PATH_PATTERN.finditer(text):
        path_val = m.group(1)
        if any(e.start <= m.start(1) < e.end for e in entities):
            continue
        entities.append(Entity(
            type=EntityType.PATH, value=path_val,
            start=m.start(1), end=m.end(1),
        ))

    # Numbers with units
    for m in _NUMBER_PATTERN.finditer(text):
        if any(e.start <= m.start() < e.end for e in entities):
            continue
        entities.append(Entity(
            type=EntityType.NUMBER, value=m.group(),
            start=m.start(), end=m.end(),
        ))

    # Detect language
    has_jp = bool(re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]', text))
    has_en = bool(re.search(r'[a-zA-Z]{3,}', text))
    if has_jp and has_en:
        lang = "mixed"
    elif has_jp:
        lang = "ja"
    elif has_en:
        lang = "en"
    else:
        lang = "unknown"
    entities.append(Entity(
        type=EntityType.LANGUAGE, value=lang,
        start=0, end=len(text),
    ))

    entities.sort(key=lambda e: e.start)
    return entities


# =============================================================================
# L0: extract_certain (Katalēpsis)
# =============================================================================


# PURPOSE: L0 確定情報抽出 (Katalēpsis, I×C — 信念を固定しコミットする)
def extract_certain(text: str, entities: list[Entity]) -> list[CertainSpan]:
    """L0 Extract spans of text that are SOURCE (certain information).

    SOURCE = information that comes directly from the input and should be
    treated as ground truth (not to be hallucinated or modified).

    Covers: quoted strings, code blocks, file paths, numbers, blockquotes.
    """
    spans: list[CertainSpan] = []
    for entity in entities:
        if entity.type == EntityType.QUOTED:
            spans.append(CertainSpan(
                text=entity.value, source_type="quoted",
                start=entity.start, end=entity.end,
            ))
        elif entity.type == EntityType.CODE_BLOCK:
            spans.append(CertainSpan(
                text=entity.value, source_type="code_block",
                start=entity.start, end=entity.end,
            ))
        elif entity.type == EntityType.PATH:
            spans.append(CertainSpan(
                text=entity.value, source_type="path",
                start=entity.start, end=entity.end,
            ))
        elif entity.type == EntityType.NUMBER:
            spans.append(CertainSpan(
                text=entity.value, source_type="number",
                start=entity.start, end=entity.end,
            ))

    # Independent detection: Markdown blockquotes
    for m in _BLOCKQUOTE_PATTERN.finditer(text):
        if any(s.start <= m.start() and m.end() <= s.end
               for s in spans if s.source_type == "code_block"):
            continue
        spans.append(CertainSpan(
            text=m.group().strip(), source_type="blockquote",
            start=m.start(), end=m.end(),
        ))

    spans.sort(key=lambda s: s.start)
    return spans


# =============================================================================
# L2: detect_ambiguity (Epochē)
# =============================================================================


# PURPOSE: L2 曖昧性検出 (Epochē, I×U — 信念の確定を保留する)
def detect_ambiguity(
    text: str,
    entities: list[Entity],
    resolved_refs: dict[str, str] | None = None,
) -> list[AmbiguitySpan]:
    """L2 Detect ambiguous spans in the input text.

    Detects:
      - Unresolved references ("さっきの", "これ" etc.)
      - Vague scope ("あたり", "くらい", "適当に")
      - Omitted subjects (verb without explicit object)
      - Implicit context dependencies

    Already-resolved references (from resolve_references) are excluded.
    """
    ambiguities: list[AmbiguitySpan] = []
    resolved_refs = resolved_refs or {}

    for pattern, amb_type, suggestion in _AMBIGUITY_PATTERNS:
        for m in pattern.finditer(text):
            ref_text = m.group()

            # Skip if this reference was already resolved
            if ref_text in resolved_refs and not resolved_refs[ref_text].startswith("[unresolved:"):
                continue

            # Skip if inside a certain span (quoted, code block, etc.)
            if any(e.start <= m.start() < e.end
                   for e in entities
                   if e.type in (EntityType.QUOTED, EntityType.CODE_BLOCK)):
                continue

            ambiguities.append(AmbiguitySpan(
                text=ref_text,
                ambiguity_type=amb_type,
                start=m.start(),
                end=m.end(),
                suggestion=suggestion,
            ))

    ambiguities.sort(key=lambda a: a.start)
    return ambiguities
