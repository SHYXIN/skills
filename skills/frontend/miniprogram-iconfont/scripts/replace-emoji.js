#!/usr/bin/env node
/**
 * replace-emoji.js
 *
 * 扫描小程序项目中的 emoji 并替换为 iconfont 类名。
 *
 * 用法：
 *   node replace-emoji.js <project-root> [--emoji ⚙️] [--dry-run] [--yes]
 *
 * 参数：
 *   project-root   小程序项目根目录
 *   --emoji        只处理指定 emoji（可重复）
 *   --dry-run      只输出变更清单，不实际替换
 *   --yes          跳过确认直接替换
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ─── emoji → iconfont 类名映射 ───────────────────────────────────────────────
// 按 emoji-icon-mapping.md 维护，格式：[emoji, className, description]
const EMOJI_MAP = [
  // 功能导航类
  ['🔍',    'icon-search',                         '搜索'],
  ['👤',    'icon-user',                           '用户/个人中心'],
  ['⚙️',    'icon-settings',                       '设置'],
  ['💰',    'icon-wallet',                         '钱包/收入'],
  ['📋',    'icon-clipboard1',                     '订单/清单'],
  ['📞',    'icon-phone1',                         '联系电话'],
  ['🎟️',    'icon-coupon',                         '优惠券'],
  ['📍',    'icon-location-fill',                  '地址/位置'],
  ['🎓',    'icon-education',                      '学历/教育'],
  ['❓',    'icon-help',                           '帮助/疑问'],
  ['❤️',    'icon-tubiaozhizuomoban-',              '收藏/喜欢（实心）'],
  ['🤍',    'icon-tubiaozhizuomoban-',              '未收藏（空心，同上）'],
  ['💼',    'icon-briefcase',                      '工作台/职业'],
  ['📊',    'icon-charts-bar',                     '数据统计'],
  ['📅',    'icon-calendar',                       '日程/日期'],
  ['📝',    'icon-edit-pencil',                    '文章/编辑/表单'],
  ['👥',    'icon-users',                          '用户管理/客户'],
  ['⭐',    'icon-star',                           '评分星标（实心）'],

  // 操作按钮类
  ['✏️',    'icon-edit-pencil',                    '编辑'],
  ['🗑️',    'icon-delete',                         '删除'],
  ['✓',     'icon-icon_success_done',              '成功/勾选'],
  ['✕',     'icon-close',                          '关闭/错误'],
  ['⚠️',    'icon-warning',                        '警告/提示'],
  ['💬',    'icon-chat',                           '微信/聊天'],
  ['🚫',    'icon-Ban',                            '禁止/已撤回'],
  ['↩️',    'icon-money-quick-refund-plan',         '退款'],

  // 状态标识类
  ['✅',    'icon-icon_success_done',              '已通过/已完成'],
  ['⏰',    'icon-clock-timeout',                  '时间/时长'],
  ['⏱️',    'icon-uj_icon_stopwatch',               '咨询时长'],
  ['🎯',    'icon-a-targetbullseye-negative',      '目标/匹配'],
  ['💻',    'icon-computer-laptop',                '线上咨询'],
  ['🏅',    'icon-trophy-fill',                    '资质证书'],
  ['🏆',    'icon-trophy-fill',                    '成就/荣誉'],
  ['📭',    'icon-Envelope',                       '无数据空态'],
  ['📌',    'icon-Marker',                         '重要提示/定位'],
  ['🎫',    'icon-coupon',                         '票券'],

  // 人物角色类
  ['👨‍⚕️',  'icon-jingli2x',                        '咨询师'],
  ['👩‍💼',  'icon-manager-o',                       '管理员'],
  ['👨',    'icon-msnui-male',                     '性别-男'],
  ['👩',    'icon-female',                         '性别-女'],
  ['🤐',    'icon-secret',                         '性别-保密'],
  ['🤝',    'icon-Handshake',                      '合作共赢'],

  // 其他辅助类
  ['💡',    'icon-lightbulb',                      '提示/说明'],
  ['🔒',    'icon-lock',                           '密码安全'],
  ['📱',    'icon-mobile-phone',                   '手机号'],
  ['📷',    'icon-camera_upload_loding',            '上传照片'],
  ['🎉',    'icon-celebrate',                      '成功庆祝'],
  ['☆',     'icon-star',                           '评分星星（空心）'],
  ['🏷️',    'icon-Taglabel',                       '标签/类型'],
  ['✗',     'icon-close',                          '密码不一致'],
  ['💝',    'icon-tubiaozhizuomoban-',              '爱心（同收藏）'],
  ['⚡',    'icon-uj_icon_stopwatch',               '快速/秒表'],
];

// ─── 参数解析 ─────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
  console.log(`用法: node replace-emoji.js <project-root> [options]
  --emoji <emoji>  只处理指定 emoji（可重复）
  --dry-run        只输出变更清单，不实际替换
  --yes            跳过确认直接替换
  --help, -h       显示帮助`);
  process.exit(0);
}

const projectRoot = path.resolve(args[0]);
const dryRun = args.includes('--dry-run');
const skipConfirm = args.includes('--yes');

const emojiFilter = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--emoji' && args[i + 1]) {
    emojiFilter.push(args[++i]);
  }
}

if (!fs.existsSync(projectRoot)) {
  console.error(`❌ 项目目录不存在: ${projectRoot}`);
  process.exit(1);
}

// ─── 构建查找表 ───────────────────────────────────────────────────────────────
const emojiToClass = new Map();
for (const [emoji, className, desc] of EMOJI_MAP) {
  if (emojiFilter.length > 0 && !emojiFilter.includes(emoji)) continue;
  // 相同 emoji 只保留第一个映射
  if (!emojiToClass.has(emoji)) {
    emojiToClass.set(emoji, { className, desc });
  }
}

// ─── 扫描文件 ─────────────────────────────────────────────────────────────────
const SCAN_EXTENSIONS = ['.wxml', '.js'];
const EXCLUDE_DIRS = ['node_modules', '.git', 'images'];

function scanFiles(dir) {
  const results = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!EXCLUDE_DIRS.includes(entry.name)) {
        results.push(...scanFiles(fullPath));
      }
    } else if (entry.isFile() && SCAN_EXTENSIONS.includes(path.extname(entry.name))) {
      results.push(fullPath);
    }
  }
  return results;
}

const files = scanFiles(projectRoot);
console.log(`📂 扫描目录: ${projectRoot}`);
console.log(`📄 找到 ${files.length} 个文件（.wxml / .js）\n`);

// ─── 匹配 emoji ───────────────────────────────────────────────────────────────
const changes = []; // [{ file, line, emoji, className, desc, original, replaced }]

for (const filePath of files) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    for (const [emoji, { className, desc }] of emojiToClass) {
      if (line.includes(emoji)) {
        const relativePath = path.relative(projectRoot, filePath);
        // 生成替换后的行（替换所有出现的该 emoji）
        const replacedLine = line.split(emoji).join(`<text class="iconfont ${className}"></text>`);
        changes.push({
          file: relativePath,
          line: i + 1,
          emoji,
          className,
          desc,
          original: line.trim(),
          replaced: replacedLine.trim(),
        });
      }
    }
  }
}

// ─── 输出变更清单 ─────────────────────────────────────────────────────────────
if (changes.length === 0) {
  console.log('✅ 没有找到需要替换的 emoji！');
  process.exit(0);
}

console.log(`🔍 找到 ${changes.length} 处需要替换的 emoji：\n`);

// 按文件分组输出
const grouped = new Map();
for (const c of changes) {
  if (!grouped.has(c.file)) grouped.set(c.file, []);
  grouped.get(c.file).push(c);
}

for (const [file, items] of grouped) {
  console.log(`  📄 ${file} (${items.length} 处)`);
  for (const item of items) {
    console.log(`     第 ${item.line} 行  ${item.emoji} → .${item.className}  (${item.desc})`);
    console.log(`     - ${item.original}`);
    console.log(`     + ${item.replaced}`);
  }
  console.log('');
}

// 统计
const emojiCount = new Map();
for (const c of changes) {
  emojiCount.set(c.emoji, (emojiCount.get(c.emoji) || 0) + 1);
}
console.log('─── 统计 ───');
for (const [emoji, count] of emojiCount) {
  const { className, desc } = emojiToClass.get(emoji);
  console.log(`  ${emoji} → .${className}  ${desc}  × ${count}`);
}
console.log(`  共 ${changes.length} 处，涉及 ${grouped.size} 个文件\n`);

if (dryRun) {
  console.log('🔍 dry-run 模式，未执行替换。去掉 --dry-run 执行实际替换。');
  process.exit(0);
}

// ─── 确认 & 执行替换 ──────────────────────────────────────────────────────────
if (!skipConfirm) {
  const readline = require('readline');
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  rl.question('确认执行替换？(y/N) ', (answer) => {
    rl.close();
    if (answer.trim().toLowerCase() !== 'y') {
      console.log('已取消。');
      process.exit(0);
    }
    doReplace();
  });
} else {
  doReplace();
}

function doReplace() {
  // 按文件去重，每个文件只读写一次
  const fileChanges = new Map();
  for (const c of changes) {
    if (!fileChanges.has(c.file)) fileChanges.set(c.file, []);
    fileChanges.get(c.file).push(c);
  }

  let replacedCount = 0;
  for (const [relativePath, items] of fileChanges) {
    const absPath = path.join(projectRoot, relativePath);
    let content = fs.readFileSync(absPath, 'utf-8');

    // 按 emoji 去重替换（同一文件同一 emoji 只替换一次模式）
    const seenEmojis = new Set();
    for (const item of items) {
      if (seenEmojis.has(item.emoji)) continue;
      seenEmojis.add(item.emoji);

      const replacement = `<text class="iconfont ${item.className}"></text>`;
      const count = (content.split(item.emoji).length - 1);
      content = content.split(item.emoji).join(replacement);
      replacedCount += count;
    }

    fs.writeFileSync(absPath, content, 'utf-8');
    console.log(`  ✅ ${relativePath}`);
  }

  console.log(`\n🎉 替换完成！共替换 ${replacedCount} 处 emoji，涉及 ${fileChanges.size} 个文件。`);
  console.log('   请在微信开发者工具中重新编译查看效果。');
}
