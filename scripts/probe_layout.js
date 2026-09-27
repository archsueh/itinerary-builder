#!/usr/bin/env node
/**
 * probe_layout.js — 路书 HTML 的布局体检（横向溢出 / 视口宽度）
 *
 * 为什么需要它：`check_quality.py` 只能看文本（emoji / 外链 / 图表 / slop / 注入噪声），
 * **看不到布局**。路书是要在手机上打开的，一个 `nowrap` 或没加 `min-width:0` 的 grid
 * 就会让整页横向滚动——在手机上表现为「右边被切掉」，而 HTML 本身完全合法。
 *
 * 为什么不用 Chrome 无头截图目测：
 *   chrome --headless --window-size=430,1400 --force-device-scale-factor=2 --screenshot=...
 * 会**假性裁切**（右侧内容看似被切、还出现一条红色竖线），但页面其实没有溢出。
 * 实测过的坑：差点把截图口径问题误报成布局 bug。所以这里直接量 DOM。
 *
 * 用法：
 *   NODE_PATH=/Users/mac/.workbuddy-ai/binaries/node/workspace/node_modules \
 *   /Users/mac/.workbuddy-ai/binaries/node/versions/22.22.2-3/bin/node \
 *   scripts/probe_layout.js <输出.html> [视口宽度...]
 *
 * 退出码：0 = 全部视口无溢出；1 = 有溢出（列出越界元素）
 */
const path = require('path');
const { chromium } = require('playwright');

const WIDTHS = process.argv.slice(3).map(Number).filter(Boolean);
const VIEWPORTS = WIDTHS.length ? WIDTHS : [320, 375, 430, 768];

async function main() {
  const file = process.argv[2];
  if (!file) {
    console.error('用法: probe_layout.js <输出.html> [视口宽度...]');
    process.exit(2);
  }
  const url = 'file://' + path.resolve(file);

  const browser = await chromium.launch();
  let bad = 0;

  for (const width of VIEWPORTS) {
    const page = await browser.newPage({
      viewport: { width, height: 900 },
      deviceScaleFactor: 2,
    });
    await page.goto(url, { waitUntil: 'load' });

    const r = await page.evaluate(() => {
      const doc = document.documentElement;
      const offenders = [];
      document.querySelectorAll('*').forEach((el) => {
        const rect = el.getBoundingClientRect();
        if (rect.right > doc.clientWidth + 1) {
          offenders.push({
            tag: el.tagName.toLowerCase(),
            cls: String(el.className || '').slice(0, 46),
            right: Math.round(rect.right),
            w: Math.round(rect.width),
            text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 34),
          });
        }
      });
      // 去重：同一个越界块常带一串同坐标子元素
      const seen = new Set();
      const uniq = offenders.filter((o) => {
        const k = `${o.cls}|${o.right}|${o.w}`;
        if (seen.has(k)) return false;
        seen.add(k);
        return true;
      });
      return {
        scrollW: doc.scrollWidth,
        clientW: doc.clientWidth,
        offenders: uniq.slice(0, 12),
        total: uniq.length,
      };
    });

    const overflow = r.scrollW > r.clientW;
    if (overflow || r.total) bad++;
    console.log(
      '[%s] %dpx  scrollWidth=%d clientWidth=%d  越界元素=%d%s',
      overflow || r.total ? 'FAIL' : 'OK',
      width, r.scrollW, r.clientW, r.total,
      overflow && !r.total ? '（有横向滚动但未定位到单一元素，检查 body/wrap 的 padding 与 100vw 用法）' : ''
    );
    r.offenders.forEach((o) => {
      console.log('        <%s class="%s"> right=%d w=%d  %s', o.tag, o.cls, o.right, o.w, o.text);
    });

    await page.close();
  }

  await browser.close();
  console.log();
  if (bad) {
    console.log('FAIL — %d/%d 个视口有横向溢出', bad, VIEWPORTS.length);
    process.exit(1);
  }
  console.log('PASS — %d 个视口均无横向溢出', VIEWPORTS.length);
}

main().catch((e) => {
  console.error(e);
  process.exit(2);
});
