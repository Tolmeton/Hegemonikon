/**
 * Typos v8 Renderer — AST → HTML conversion
 *
 * Renders a TyposDocument into styled HTML for the preview webview.
 * Each directive type gets a visually distinct treatment.
 */

import { TyposDocument, TyposNode } from './parser';

// ── Directive categories for styling ──

const CATEGORY: Record<string, string> = {
  // d=0 生成子
  role: 'endpoint',
  goal: 'why',
  // Why族
  context: 'why', intent: 'why', rationale: 'why',
  // How族
  detail: 'how', summary: 'how', spec: 'how', outline: 'how',
  constraints: 'how',  // legacy
  // How-much族
  focus: 'howmuch', scope: 'howmuch', highlight: 'howmuch', breadth: 'howmuch',
  // Where族
  case: 'where', principle: 'where', step: 'where', policy: 'where',
  examples: 'where',  // legacy
  // Which族
  data: 'which', schema: 'which', content: 'which', format: 'which',
  tools: 'which', resources: 'which', rubric: 'which',  // legacy
  // When族
  fact: 'when', assume: 'when', assert: 'when', option: 'when',
  // Control
  if: 'control', elif: 'control', else: 'control',
  // Structure
  table: 'structure', flow: 'structure',
  // Meta
  mixin: 'meta', extends: 'meta', activation: 'meta',
  include: 'meta',
};

const CATEGORY_LABELS: Record<string, string> = {
  endpoint: '⊚ Endpoint',
  why: 'Why',
  how: 'How',
  howmuch: 'How-much',
  where: 'Where',
  which: 'Which',
  when: 'When',
  control: '⎇ Control',
  structure: '⊞ Structure',
  meta: '⚙ Meta',
};

const DEPTH_BADGE: Record<string, string> = {
  why: 'L1+',
  how: 'L1+',
  howmuch: 'L2+',
  where: 'L2+',
  which: 'L3',
  when: 'L3',
};

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function getCategory(kind: string): string {
  if (kind.match(/^[A-Z](?:-?\[|-.)/)) { return 'identifier'; }
  return CATEGORY[kind] || 'generic';
}

// ── Render functions ──

function renderMeta(doc: TyposDocument): string {
  const entries = Object.entries(doc.meta);
  if (entries.length === 0) { return ''; }

  const badges = entries.map(([k, v]) => {
    const cls = k === 'prompt' ? 'meta-badge meta-prompt' : 'meta-badge';
    return `<span class="${cls}"><span class="meta-key">#${escapeHtml(k)}</span> <span class="meta-value">${escapeHtml(v)}</span></span>`;
  }).join('\n');

  return `<div class="meta-header">${badges}</div>`;
}

function renderTableContent(textLines: string[]): string {
  const rows = textLines.filter(l => l.trim()).map(l => l.trim());
  if (rows.length === 0) { return ''; }

  const parseRow = (line: string) => line.split('::').map(c => c.trim());
  const headers = parseRow(rows[0]);
  const dataRows = rows.slice(1).map(parseRow);

  let html = '<table class="typos-table"><thead><tr>';
  for (const h of headers) {
    html += `<th>${escapeHtml(h)}</th>`;
  }
  html += '</tr></thead><tbody>';
  for (const row of dataRows) {
    html += '<tr>';
    for (let i = 0; i < headers.length; i++) {
      html += `<td>${escapeHtml(row[i] || '')}</td>`;
    }
    html += '</tr>';
  }
  html += '</tbody></table>';
  return html;
}

function renderTextContent(textLines: string[], value: string): string {
  if (value) { return `<p class="inline-value">${escapeHtml(value)}</p>`; }
  if (textLines.length === 0) { return ''; }

  const content = textLines.join('\n');
  // Check if content looks like a list
  const listItems = textLines.filter(l => l.trim().startsWith('- '));
  if (listItems.length > textLines.filter(l => l.trim()).length * 0.5) {
    // Render as list
    let html = '<ul class="typos-list">';
    for (const line of textLines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('- ')) {
        html += `<li>${formatInlineText(trimmed.slice(2))}</li>`;
      }
    }
    html += '</ul>';
    return html;
  }

  // Check for :: table content
  if (textLines.some(l => l.includes('::'))) {
    const tableLines = textLines.filter(l => l.includes('::'));
    if (tableLines.length > 1) {
      return renderTableContent(tableLines);
    }
  }

  // Render as pre-formatted text
  return `<div class="text-content">${formatBlockText(content)}</div>`;
}

function formatInlineText(text: string): string {
  let html = escapeHtml(text);
  // Bold: **text**
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Code: `text`
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  // ✅ ❌ ⚠️ indicators
  html = html.replace(/(✅|❌|⚠️)/g, '<span class="indicator">$1</span>');
  // [SOURCE] [TAINT] labels
  html = html.replace(/\[(SOURCE|TAINT|確信|推定|仮説)\]/g, '<span class="label label-$1">[$1]</span>');
  return html;
}

function formatBlockText(text: string): string {
  const lines = text.split('\n');
  let html = '';
  let inCode = false;
  let codeContent = '';
  let codeLang = '';

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('```')) {
      if (inCode) {
        html += `<pre class="code-block"><code class="lang-${escapeHtml(codeLang)}">${escapeHtml(codeContent.trim())}</code></pre>`;
        inCode = false;
        codeContent = '';
      } else {
        inCode = true;
        codeLang = trimmed.slice(3).trim();
      }
      continue;
    }
    if (inCode) {
      codeContent += line + '\n';
      continue;
    }
    if (trimmed === '') {
      html += '<br>';
    } else {
      html += `<p>${formatInlineText(trimmed)}</p>`;
    }
  }

  if (inCode && codeContent) {
    html += `<pre class="code-block"><code>${escapeHtml(codeContent.trim())}</code></pre>`;
  }

  return html;
}

function renderNode(node: TyposNode, depth: number = 0): string {
  const cat = getCategory(node.kind);
  const catLabel = CATEGORY_LABELS[cat] || cat;
  const depthBadge = DEPTH_BADGE[cat] || '';
  const indent = depth > 0 ? ` style="margin-left: ${Math.min(depth * 12, 48)}px"` : '';

  let html = `<div class="directive directive-${cat}"${indent}>`;

  // Header bar
  html += '<div class="directive-header">';
  html += `<span class="directive-name">${escapeHtml(node.kind)}</span>`;
  if (catLabel && cat !== 'generic') {
    html += `<span class="category-badge cat-${cat}">${escapeHtml(catLabel)}</span>`;
  }
  if (depthBadge) {
    html += `<span class="depth-badge">${depthBadge}</span>`;
  }
  if (node.condition) {
    html += `<span class="condition-badge">if ${escapeHtml(node.condition)}</span>`;
  }
  if (node.line) {
    html += `<span class="line-number">L${node.line}</span>`;
  }
  html += '</div>';

  // Content
  html += '<div class="directive-body">';

  // Special rendering for specific directive types
  if (node.kind === 'table') {
    html += renderTableContent(node.textLines);
  } else if (node.kind === 'case' || node.kind === 'examples') {
    html += renderExamples(node);
  } else if (node.kind === 'schema' || node.kind === 'rubric') {
    html += renderSchema(node);
  } else if (node.kind === 'scope') {
    html += renderScope(node);
  } else if (node.kind === 'flow') {
    html += renderFlow(node);
  } else {
    html += renderTextContent(node.textLines, node.value);
  }

  // Children
  for (const child of node.children) {
    html += renderNode(child, depth + 1);
  }

  html += '</div></div>';
  return html;
}

function renderExamples(node: TyposNode): string {
  let html = '';
  const examples = node.children.filter(c => c.kind === 'example');
  if (examples.length > 0) {
    for (const ex of examples) {
      html += '<div class="example-pair">';
      const input = ex.children.find(c => c.kind === 'input');
      const output = ex.children.find(c => c.kind === 'output');
      if (input) {
        html += `<div class="example-input"><span class="example-label">INPUT</span>${renderTextContent(input.textLines, input.value)}</div>`;
      }
      if (output) {
        html += `<div class="example-output"><span class="example-label">OUTPUT</span>${renderTextContent(output.textLines, output.value)}</div>`;
      }
      html += '</div>';
    }
  } else {
    html += renderTextContent(node.textLines, node.value);
  }
  return html;
}

function renderSchema(node: TyposNode): string {
  let html = '';
  const dims = node.children.filter(c => c.kind === 'dimension');
  if (dims.length > 0) {
    for (const dim of dims) {
      html += '<div class="schema-dimension">';
      // Extract name, description, scale from text lines
      for (const line of dim.textLines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('name:')) {
          html += `<h4 class="dim-name">${escapeHtml(trimmed.slice(5).trim())}</h4>`;
        } else if (trimmed.startsWith('description:')) {
          html += `<p class="dim-desc">${escapeHtml(trimmed.slice(12).trim())}</p>`;
        } else if (trimmed.startsWith('scale:')) {
          html += `<span class="dim-scale">Scale: ${escapeHtml(trimmed.slice(6).trim())}</span>`;
        }
      }
      // Criteria
      const criteria = dim.children.find(c => c.kind === 'criteria');
      if (criteria) {
        html += '<div class="criteria-list">';
        for (const line of criteria.textLines) {
          const trimmed = line.trim();
          if (trimmed.includes(':')) {
            const [score, desc] = trimmed.split(':', 2);
            html += `<div class="criteria-item"><span class="criteria-score">${escapeHtml(score.trim())}</span> ${escapeHtml(desc.trim())}</div>`;
          }
        }
        html += '</div>';
      }
      html += '</div>';
    }
  } else {
    html += renderTextContent(node.textLines, node.value);
  }
  return html;
}

function renderScope(node: TyposNode): string {
  let html = '<div class="scope-container">';
  let section = 'triggered';

  const sections: Record<string, string[]> = {
    triggered: [],
    not_triggered: [],
    gray_zone: [],
  };

  for (const line of node.textLines) {
    const trimmed = line.trim();
    if (!trimmed) { continue; }
    const lower = trimmed.toLowerCase().replace(/:$/, '');
    if (trimmed.includes('非発動') || lower === 'not_triggered') {
      section = 'not_triggered'; continue;
    }
    if (trimmed.includes('グレーゾーン') || lower === 'gray_zone') {
      section = 'gray_zone'; continue;
    }
    if ((trimmed.includes('発動') && !trimmed.includes('非')) || lower === 'triggered') {
      section = 'triggered'; continue;
    }
    sections[section].push(trimmed);
  }

  const labels: Record<string, string> = {
    triggered: '🟢 発動条件',
    not_triggered: '🔴 非発動条件',
    gray_zone: '🟡 グレーゾーン',
  };

  for (const [key, items] of Object.entries(sections)) {
    if (items.length === 0) { continue; }
    html += `<div class="scope-section scope-${key}">`;
    html += `<div class="scope-label">${labels[key]}</div>`;
    html += '<ul>';
    for (const item of items) {
      const text = item.startsWith('- ') ? item.slice(2) : item;
      html += `<li>${formatInlineText(text)}</li>`;
    }
    html += '</ul></div>';
  }

  html += '</div>';
  return html;
}

function renderFlow(node: TyposNode): string {
  const expr = node.value || node.textLines.join(' ').trim();
  if (!expr) { return ''; }

  // Split by >> and render as pipeline
  const stages = expr.split('>>').map(s => s.trim()).filter(Boolean);
  let html = '<div class="flow-pipeline">';
  for (let i = 0; i < stages.length; i++) {
    if (i > 0) {
      html += '<span class="flow-arrow">▸▸</span>';
    }
    const stage = stages[i];
    // Check for [A, B] group
    if (stage.startsWith('[') && stage.endsWith(']')) {
      const nodes = stage.slice(1, -1).split(',').map(n => n.trim());
      html += '<div class="flow-group">';
      for (const n of nodes) {
        html += `<span class="flow-node">${escapeHtml(n)}</span>`;
      }
      html += '</div>';
    } else if (stage.includes('*')) {
      const nodes = stage.split('*').map(n => n.trim());
      html += '<div class="flow-group">';
      for (const n of nodes) {
        html += `<span class="flow-node">${escapeHtml(n)}</span>`;
      }
      html += '</div>';
    } else {
      html += `<span class="flow-node">${escapeHtml(stage)}</span>`;
    }
  }
  html += '</div>';
  return html;
}

// ── Main render function ──

export function render(doc: TyposDocument): string {
  let html = renderMeta(doc);

  for (const node of doc.rootNodes) {
    html += renderNode(node);
  }

  return html;
}
