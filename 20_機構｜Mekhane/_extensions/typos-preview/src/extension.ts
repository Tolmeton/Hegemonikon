/**
 * Typos Preview — VS Code Extension Entry Point
 *
 * Registers the preview command and manages the webview lifecycle.
 */

import * as vscode from 'vscode';
import { parse } from './parser';
import { render } from './renderer';

let currentPanel: vscode.WebviewPanel | undefined;

export function activate(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('typos.preview', () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.languageId !== 'typos') {
      vscode.window.showWarningMessage('Open a .typos file to preview');
      return;
    }

    if (currentPanel) {
      currentPanel.reveal(vscode.ViewColumn.Beside);
      updatePreview(currentPanel, editor.document, context);
    } else {
      currentPanel = vscode.window.createWebviewPanel(
        'typosPreview',
        'Týpos Preview',
        vscode.ViewColumn.Beside,
        {
          enableScripts: false,
          localResourceRoots: [
            vscode.Uri.joinPath(context.extensionUri, 'media')
          ],
        }
      );

      currentPanel.onDidDispose(() => {
        currentPanel = undefined;
      }, null, context.subscriptions);

      updatePreview(currentPanel, editor.document, context);
    }
  });

  // Live update on text change
  const changeDisposable = vscode.workspace.onDidChangeTextDocument((e) => {
    if (currentPanel && vscode.window.activeTextEditor &&
        e.document === vscode.window.activeTextEditor.document &&
        e.document.languageId === 'typos') {
      updatePreview(currentPanel, e.document, context);
    }
  });

  // Update when switching editors
  const editorDisposable = vscode.window.onDidChangeActiveTextEditor((editor) => {
    if (currentPanel && editor && editor.document.languageId === 'typos') {
      updatePreview(currentPanel, editor.document, context);
    }
  });

  context.subscriptions.push(disposable, changeDisposable, editorDisposable);
}

function updatePreview(
  panel: vscode.WebviewPanel,
  document: vscode.TextDocument,
  context: vscode.ExtensionContext
) {
  const text = document.getText();
  const fileName = document.fileName.split('/').pop() || 'untitled.typos';

  let bodyHtml: string;
  let errorHtml = '';

  try {
    const doc = parse(text);
    bodyHtml = render(doc);
  } catch (e: any) {
    bodyHtml = '';
    errorHtml = `<div class="parse-error">⚠ Parse Error: ${escapeHtml(e.message || String(e))}</div>`;
  }

  const cssUri = panel.webview.asWebviewUri(
    vscode.Uri.joinPath(context.extensionUri, 'media', 'preview.css')
  );

  panel.webview.html = getWebviewContent(cssUri.toString(), fileName, bodyHtml, errorHtml);
}

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function getWebviewContent(
  cssUri: string,
  fileName: string,
  bodyHtml: string,
  errorHtml: string
): string {
  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="${cssUri}">
  <title>Týpos Preview</title>
</head>
<body>
  <header class="preview-header">
    <span class="preview-icon">◉</span>
    <span class="preview-title">${escapeHtml(fileName)}</span>
  </header>
  ${errorHtml}
  <main class="preview-body">
    ${bodyHtml}
  </main>
</body>
</html>`;
}

export function deactivate() {
  if (currentPanel) {
    currentPanel.dispose();
  }
}
