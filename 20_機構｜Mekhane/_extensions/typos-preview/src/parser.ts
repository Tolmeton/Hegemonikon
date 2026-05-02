/**
 * Typos v8 Parser — Lightweight JS port of v8_tokenizer.py
 *
 * Line-based stack parser for the Typos DSL.
 * Produces an AST (TyposDocument) for the renderer.
 */

// ── AST Types ──

export interface TyposNode {
  kind: string;
  value: string;
  children: TyposNode[];
  textLines: string[];
  line: number;
  condition?: string;
  prefix?: string;
  address?: string;
}

export interface TyposDocument {
  meta: Record<string, string>;
  rootNodes: TyposNode[];
}

// ── Regex Patterns ──

const META_PATTERN = /^#(\w+)\s*:\s*(.+)$/;
const PROMPT_PATTERN = /^#prompt\s+(.+)$/;
const MIXIN_HEADER = /^#mixin\s+(.+)$/;

// v8.4 identifier: S-01a, S[01a], S-[01a]
const ID_NAME_RE = /^([A-Z])(?:-?\[([^\]]+)\]|-(\d[\w.]*))$/;

// Name = word-name | identifier-name
const NAME_PAT = '(?:\\w[\\w-]*|[A-Z](?:-?\\[[^\\]]+\\]|-\\d[\\w.]*))';

const V8_INLINE = new RegExp(`^<:(${NAME_PAT}):\\s*(.*?)\\s*:>$`);
const V8_BLOCK_OPEN = new RegExp(`^<:(${NAME_PAT}):$`);
const V8_IF_OPEN = /^<:if\s+(.+):$/;
const V8_ELIF_OPEN = /^<:elif\s+(.+):$/;
const V8_ELSE_OPEN = /^<:else:$/;
const V8_NAMED_CLOSE = new RegExp(`^/(${NAME_PAT}):>$`);
const V8_ANON_CLOSE = /^:>$/;
const CODE_FENCE = /^```/;

// ── Parser ──

function parseIdName(name: string): { prefix?: string; address?: string } {
  const m = name.match(ID_NAME_RE);
  if (!m) { return {}; }
  return {
    prefix: m[1],
    address: m[2] !== undefined ? m[2] : m[3],
  };
}

function createNode(kind: string, line: number, extra?: Partial<TyposNode>): TyposNode {
  return {
    kind,
    value: '',
    children: [],
    textLines: [],
    line,
    ...extra,
  };
}

interface StackFrame {
  node: TyposNode;
  expectsName: string;
}

export function parse(text: string): TyposDocument {
  const lines = text.split('\n');
  let pos = 0;
  const doc: TyposDocument = { meta: {}, rootNodes: [] };
  const stack: StackFrame[] = [];
  let inCodeBlock = false;

  // ── Helpers ──

  function addNode(node: TyposNode): void {
    if (stack.length > 0) {
      stack[stack.length - 1].node.children.push(node);
    } else {
      doc.rootNodes.push(node);
    }
  }

  function addTextLine(line: string): void {
    if (stack.length > 0) {
      stack[stack.length - 1].node.textLines.push(line);
    }
  }

  function push(node: TyposNode, name: string): void {
    stack.push({ node, expectsName: name });
  }

  function pop(closeTag: string, lineNum: number): TyposNode {
    if (stack.length === 0) {
      throw new Error(`Line ${lineNum}: Unexpected close tag with no open block`);
    }
    const frame = stack.pop()!;
    return frame.node;
  }

  function closeNamed(name: string, lineNum: number): void {
    if (name === 'if') {
      closeIfGroup(lineNum);
      return;
    }
    if (stack.length === 0) { return; }

    const top = stack[stack.length - 1];
    if (top.expectsName === name) {
      const node = pop(`/${name}:>`, lineNum);
      addNode(node);
    } else {
      // Search stack for matching name
      for (let i = stack.length - 1; i >= 0; i--) {
        if (stack[i].expectsName === name) {
          while (stack.length > i + 1) {
            const inner = pop(':>', lineNum);
            stack[stack.length - 1].node.children.push(inner);
          }
          const node = pop(`/${name}:>`, lineNum);
          addNode(node);
          return;
        }
      }
    }
  }

  function closeAnon(lineNum: number): void {
    const node = pop(':>', lineNum);
    addNode(node);
  }

  function closeIfGroup(lineNum: number): void {
    if (stack.length === 0) { return; }
    const collected: TyposNode[] = [];
    while (stack.length > 0 && ['else', 'elif'].includes(stack[stack.length - 1].expectsName)) {
      collected.unshift(pop(':>', lineNum));
    }
    if (stack.length === 0 || stack[stack.length - 1].expectsName !== 'if') { return; }
    const ifNode = pop('/if:>', lineNum);
    ifNode.children.push(...collected);
    addNode(ifNode);
  }

  // ── Phase 1: Meta headers ──

  while (pos < lines.length) {
    const line = lines[pos].trim();
    if (!line) { pos++; continue; }

    let m = line.match(PROMPT_PATTERN);
    if (m) { doc.meta['prompt'] = m[1].trim(); pos++; continue; }

    m = line.match(MIXIN_HEADER);
    if (m) { doc.meta['mixin'] = m[1].trim(); pos++; continue; }

    m = line.match(META_PATTERN);
    if (m) {
      if (m[1] !== 'prompt') { doc.meta[m[1]] = m[2].trim(); }
      pos++;
      continue;
    }

    break; // Not a meta line
  }

  // ── Phase 2: Directives ──

  while (pos < lines.length) {
    const line = lines[pos];
    const stripped = line.trim();
    const lineNum = pos + 1;

    if (!stripped) { pos++; continue; }

    // Comments
    if (stripped.startsWith('#') && !stripped.startsWith('#prompt') && !stripped.startsWith('#syntax')) {
      pos++;
      continue;
    }

    // Code fence
    if (CODE_FENCE.test(stripped)) {
      inCodeBlock = !inCodeBlock;
      addTextLine(line);
      pos++;
      continue;
    }

    // Inside code block
    if (inCodeBlock) {
      addTextLine(line);
      pos++;
      continue;
    }

    // Named close: /name:>
    let m = stripped.match(V8_NAMED_CLOSE);
    if (m) {
      closeNamed(m[1], lineNum);
      pos++;
      continue;
    }

    // Anon close: :>
    if (V8_ANON_CLOSE.test(stripped)) {
      closeAnon(lineNum);
      pos++;
      continue;
    }

    // Inline: <:name: value :>
    m = stripped.match(V8_INLINE);
    if (m) {
      const id = parseIdName(m[1]);
      addNode(createNode(m[1], lineNum, { value: m[2], ...id }));
      pos++;
      continue;
    }

    // if/elif/else
    m = stripped.match(V8_IF_OPEN);
    if (m) {
      push(createNode('if', lineNum, { condition: m[1].trim() }), 'if');
      pos++;
      continue;
    }
    m = stripped.match(V8_ELIF_OPEN);
    if (m) {
      push(createNode('elif', lineNum, { condition: m[1].trim() }), 'elif');
      pos++;
      continue;
    }
    if (V8_ELSE_OPEN.test(stripped)) {
      push(createNode('else', lineNum), 'else');
      pos++;
      continue;
    }

    // Block open: <:name:
    m = stripped.match(V8_BLOCK_OPEN);
    if (m) {
      const id = parseIdName(m[1]);
      push(createNode(m[1], lineNum, { ...id }), m[1]);
      pos++;
      continue;
    }

    // Text line
    addTextLine(line);
    pos++;
  }

  // Close any remaining open blocks gracefully (no throw for preview)
  while (stack.length > 0) {
    const node = stack.pop()!.node;
    addNode(node);
  }

  return doc;
}
