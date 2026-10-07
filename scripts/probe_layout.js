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
 * 用法（本机手动跑）：
 *   NODE=$(cat /Users/mac/.workbuddy-ai/binaries/node/versions/current)
 *   NODE_PATH=/Users/mac/.workbuddy-ai/binaries/node/workspace/node_modules \
 *   /Users/mac/.workbuddy-ai/binaries/node/versions/$NODE/bin/node \
 *   scripts/probe_layout.js <输出.html> [视口宽度...]
 *
 *   ⚠️ node 版本目录名会变（托管运行时重装时会升后缀，实测 22.22.2-3 → 22.22.2-6），
 *   **不要写死版本号**，一律经 `versions/current` 解析，否则会报
 *   `no such file or directory: .../bin/node`，看起来像脚本坏了、其实是路径过期。
 *   CI 里不需要这些：workflow 用 actions/setup-node 提供裸 `node`。
 *
 * 退出码：0 = 全部视口无溢出
 *         1 = 有溢出（列出越界元素）
 *         2 = 环境缺 playwright（NODE_PATH 未设，或本机未安装）—— **不是脚本坏了**
 *         3 = 用法错误 / 未预期错误（崩溃）
 */
const path = require('path');

let chromium;
try {
  ({ chromium } = require('playwright'));
} catch (e) {
  if (e && e.code === 'MODULE_NOT_FOUND') {
    console.error('[环境错误] 加载不到 playwright —— 不是脚本坏了，是 NODE_PATH 没设。');
    console.error('');
    console.error('  本机跑法（注意 node 版本目录要经 versions/current 解析，别写死）：');
    console.error('    NODE=$(cat /Users/mac/.workbuddy-ai/binaries/node/versions/current)');
    console.error('    NODE_PATH=/Users/mac/.workbuddy-ai/binaries/node/workspace/node_modules \\');
    console.error('      /Users/mac/.workbuddy-ai/binaries/node/versions/$NODE/bin/node \\');
    console.error('      scripts/probe_layout.js examples/01-selfdrive-chengdu-daocheng.html');
    console.error('');
    console.error('  未安装 playwright 时：');
    console.error('    cd /Users/mac/.workbuddy-ai/binaries/node/workspace && npm install playwright');
    process.exit(2);
  }
  throw e;
}

const WIDTHS = process.argv.slice(3).map(Number).filter(Boolean);
const VIEWPORTS = WIDTHS.length ? WIDTHS : [320, 375, 430, 768];

async function main() {
  const file = process.argv[2];
  if (!file) {
    console.error('用法: probe_layout.js <输出.html> [视口宽度...]');
    process.exit(3);
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
            // 必须用 getAttribute：SVG 元素的 `className` 是 SVGAnimatedString 对象，
            // `String(el.className)` 会打印成 `[object SVGAnimatedString]`，
            // 而本 skill 的图表全是 inline SVG —— 越界元素多半正是它们，诊断信息会全废。
            cls: (el.getAttribute('class') || '').slice(0, 46),
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
  // 3 而非 2：2 已被「缺 playwright」占用，崩溃与环境缺依赖必须能分辨，
  // 否则 CI 日志会把脚本 bug 读成「环境没配好」。
  process.exit(3);
});
