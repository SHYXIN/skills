# Interview Coach

> 面试备战教练，帮你系统准备面试，最终拿到 offer。

通过知识梳理、问答练习和全真模拟三种模式，覆盖技术面试（算法、系统设计、编码）和行为面试（STAR、文化匹配）。

## 功能

- **知识梳理** — 根据目标岗位和公司，生成考点清单和学习路线图
- **问答练习** — 扮演面试官出题，逐点评分反馈，自动记录错题
- **全真模拟**（V2）— 完整面试流程演练，生成综合报告
- **进度追踪** — 能力图谱 + 错题本 + 艾宾浩斯复习计划
- **公司情报** — 内置 5 家公司面试风格（字节/阿里/Google/Amazon/腾讯）

## 使用方式

在 Claude Code 中：

```
帮我准备面试，目标公司是字节跳动，后端二面
```

```
考考我，动态规划
```

```
来一轮模拟面试
```

```
帮我梳理考点，明天面试腾讯前端
```

## 文件结构

```
interview-coach/
├── SKILL.md                          — 主流程
├── PROGRESS.md                       — 进度文件格式说明
├── README.md                         — 本文件
├── progress/
│   └── .gitkeep
└── REFERENCES/
    ├── question-bank/                — 内置题库
    │   ├── algorithms/               — 算法题
    │   ├── system-design/            — 系统设计题
    │   ├── coding/                   — 编码题
    │   ├── behavioral/               — 行为面试题
    │   └── domain/                   — 领域知识题
    └── company-intel/                — 公司面试情报
        ├── bytedance.md
        ├── alibaba.md
        ├── google.md
        ├── amazon.md
        └── tencent.md
```

## 进度文件

进度独立存储在用户主目录下，与 skill 安装位置无关：

```
~/.interview-coach/progress.md
```

更新或重装 skill 不会丢失进度。

## 面试风格

- **温和模式** — 答不出来给提示，像教练
- **真实模式（默认）** — 模拟真实面试压力，追问到底
- **压力面模式** — 连续追问，挑战答案

## License

MIT
