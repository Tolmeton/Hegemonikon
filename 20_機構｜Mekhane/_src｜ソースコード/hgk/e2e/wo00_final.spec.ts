import { test, expect } from '@playwright/test';

async function navigateTo(page: any, route: string) {
  // Blur any focused element first
  await page.evaluate(() => (document.activeElement as HTMLElement)?.blur());
  await page.waitForTimeout(200);

  // Use exposed navigate function
  const result = await page.evaluate((r: string) => {
    const nav = (window as any).__hgk_navigate;
    if (typeof nav === 'function') {
      nav(r);
      return 'navigate_called';
    }
    return 'navigate_not_found';
  }, route);

  // Wait for setTimeout(120ms) + render
  await page.waitForTimeout(2500);
  return result;
}

test('WO-00 FINAL: navigate to Dashboard via __hgk_navigate', async ({ page }) => {
  await page.goto('http://localhost:1420/');
  await page.waitForTimeout(2500);

  // Confirm on Chat
  const chatBefore = await page.evaluate(() =>
    document.getElementById('view-content')?.querySelector('.cw-layout') !== null
  );
  console.log(`Starting on Chat: ${chatBefore}`);

  const result = await navigateTo(page, 'dashboard');
  console.log(`Navigation: ${result}`);

  const after = await page.evaluate(() => {
    const vc = document.getElementById('view-content');
    return {
      has_cwlayout: vc?.querySelector('.cw-layout') !== null,
      has_skeleton: vc?.innerHTML.includes('skeleton') ?? false,
      has_error: vc?.innerHTML.includes('error-boundary') ?? false,
      first_class: vc?.firstElementChild?.className ?? 'none',
      html_len: vc?.innerHTML.length ?? 0,
      text: vc?.textContent?.trim().substring(0, 150) ?? '',
    };
  });

  console.log('Dashboard state:', JSON.stringify(after, null, 2));
  await page.screenshot({ path: '/tmp/wo00_v2_dashboard.png', fullPage: false });

  // Chat's cw-layout must be gone
  expect(after.has_cwlayout).toBe(false);
});

const VIEWS = ['dashboard', 'search', 'devtools', 'gnosis', 'agents', 'notifications', 'fep', 'settings'];

for (const route of VIEWS) {
  test(`WO-00: ${route} renders without cw-layout`, async ({ page }) => {
    await page.goto('http://localhost:1420/');
    await page.waitForTimeout(2500);

    const result = await navigateTo(page, route);
    expect(result).toBe('navigate_called');

    const state = await page.evaluate(() => {
      const vc = document.getElementById('view-content');
      return {
        has_cwlayout: vc?.querySelector('.cw-layout') !== null,
        first_class: vc?.firstElementChild?.className ?? 'none',
        html_len: vc?.innerHTML.length ?? 0,
        has_error: vc?.innerHTML.includes('error-boundary') ?? false,
        error_msg: vc?.querySelector('.error-boundary-detail')?.textContent ?? '',
      };
    });

    console.log(`${route}: cwlayout=${state.has_cwlayout}, class="${state.first_class}", html=${state.html_len}, error=${state.has_error} ${state.error_msg}`);
    await page.screenshot({ path: `/tmp/wo00_v2_${route}.png`, fullPage: false });

    expect(state.has_cwlayout).toBe(false);
  });
}
