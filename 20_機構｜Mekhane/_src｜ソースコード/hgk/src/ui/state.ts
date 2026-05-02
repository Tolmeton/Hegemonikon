/**
 * UI State — 共有状態管理
 *
 * icon-rail, tab-nav, navigate が共有するグローバル状態。
 * 各モジュールは state を import して読み書きする。
 */

export let activeGroup = 'dialogue';
export let expandedGroup: string | null = 'dialogue';
export let isTabNavOpen = localStorage.getItem('hgk-tabnav') === 'true';

export function setActiveGroup(g: string): void { activeGroup = g; }
export function setExpandedGroup(g: string | null): void { expandedGroup = g; }
export function setTabNavOpen(open: boolean): void {
    isTabNavOpen = open;
    localStorage.setItem('hgk-tabnav', String(open));
}
export function toggleTabNav(): void { setTabNavOpen(!isTabNavOpen); }
