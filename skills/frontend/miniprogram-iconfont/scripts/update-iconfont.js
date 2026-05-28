#!/usr/bin/env node
/**
 * update-iconfont.js
 *
 * 将 iconfont.ttf 转为 Base64 并写入 iconfont.wxss。
 * 参数化版本，适用于技能调用。
 *
 * 用法：
 *   node update-iconfont.js --ttf <ttf路径> --wxss <wxss路径>
 *
 * 参数：
 *   --ttf   iconfont.ttf 文件路径（默认: ./images/font_icon/iconfont.ttf）
 *   --wxss  iconfont.wxss 文件路径（默认: ./styles/iconfont.wxss）
 */

const fs = require('fs');
const path = require('path');

// ─── 参数解析 ─────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const get = (flag) => { const i = args.indexOf(flag); return i >= 0 ? args[i + 1] : null; };

const TTF_PATH = get('--ttf') || './images/font_icon/iconfont.ttf';
const WXSS_PATH = get('--wxss') || './styles/iconfont.wxss';

// ─── 执行 ─────────────────────────────────────────────────────────────────────
console.log('🔄 开始更新 IconFont...\n');

const ttfPath = path.resolve(TTF_PATH);
const wxssPath = path.resolve(WXSS_PATH);

if (!fs.existsSync(ttfPath)) {
  console.error(`❌ 找不到字体文件: ${ttfPath}`);
  process.exit(1);
}
console.log(`✅ 字体文件: ${ttfPath}`);

if (!fs.existsSync(wxssPath)) {
  console.error(`❌ 找不到 wxss 文件: ${wxssPath}`);
  process.exit(1);
}
console.log(`✅ 样式文件: ${wxssPath}`);

try {
  const ttfBuffer = fs.readFileSync(ttfPath);
  const base64 = ttfBuffer.toString('base64');
  const dataUrl = `data:font/truetype;charset=utf-8;base64,${base64}`;
  console.log(`✅ Base64 转换完成 (${(base64.length / 1024).toFixed(1)} KB)`);

  let wxssContent = fs.readFileSync(wxssPath, 'utf-8');
  const oldPattern = /src: url\('data:font\/truetype;charset=utf-8;base64,[^']+'\)/;
  const newSrc = `src: url('${dataUrl}')`;

  if (!oldPattern.test(wxssContent)) {
    console.error('❌ 在 wxss 中找不到 @font-face 的 src 字段');
    process.exit(1);
  }

  wxssContent = wxssContent.replace(oldPattern, newSrc);
  fs.writeFileSync(wxssPath, wxssContent, 'utf-8');
  console.log(`✅ 已更新: ${wxssPath}`);
  console.log('\n🎉 IconFont 更新完成！请重新编译小程序查看效果。');

} catch (err) {
  console.error('❌ 更新失败:', err.message);
  process.exit(1);
}
