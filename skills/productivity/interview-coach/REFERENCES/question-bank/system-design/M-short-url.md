---
title: "设计短链接服务（TinyURL）"
tags: [system-design, 哈希, 分布式ID, 缓存, 数据库设计]
difficulty: M
companies: [字节, 腾讯, Amazon]
round: 技术二面
estimated_time: 35min
---

# 设计短链接服务

## 问题

设计一个类似 TinyURL 的短链接服务，能够将长 URL 转换为短 URL，并能从短 URL 重定向到原始 URL。

## 考察点

- API 设计
- 哈希/编码方案选择
- 数据库 schema 设计
- 分布式 ID 生成
- 缓存策略
- 高并发处理

## 推荐分析框架

### 1. 需求分析
- **功能需求：** 长 URL → 短 URL（编码），短 URL → 长 URL（解码）
- **非功能需求：** 高可用、低延迟、短 URL 不可预测
- **规模估算：** 每天 1 亿次写入，10 亿次读取，存储 5 年

### 2. 高层设计
```
客户端 → API Gateway → 编码服务 / 解码服务 → 缓存(Redis) → 数据库(MySQL/NoSQL)
```

### 3. 核心设计决策

**短 URL 生成方案：**

| 方案 | 优点 | 缺点 |
|------|------|------|
| MD5 取前8位 | 简单 | 可能冲突 |
| 自增ID + Base62 | 无冲突、短 | ID 可预测 |
| 随机字符串 + 查重 | 不可预测 | 需要查重 |

推荐：**自增ID + Base62 编码**（或分布式 ID 如 Snowflake）

### 4. 数据库 Schema
```sql
CREATE TABLE url_mapping (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    short_code VARCHAR(10) UNIQUE,
    long_url TEXT NOT NULL,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    user_id BIGINT,
    INDEX(short_code)
);
```

### 5. 缓存策略
- Redis 缓存热点映射，TTL 24h
- 读写比 10:1，缓存命中率预计 > 90%

## 追问方向

1. "如果短 URL 过期了怎么办？" → TTL + 定期清理
2. "怎么防止恶意刷短链？" → 限流 + CAPTCHA
3. "数据量太大放不下怎么办？" → 分库分表（按 short_code 哈希）
4. "怎么保证高可用？" → 主从复制 + 多机房部署
5. "短链被微信封了怎么办？" → 多域名 + 域名池轮换

## 评分维度

| 维度 | 优秀 | 及格 | 需改进 |
|------|------|------|--------|
| 框架 | 有清晰的分析框架 | 能回答但缺乏条理 | 不知道从哪开始 |
| 深度 | 主动讨论 trade-off | 被问到能回答 | 只停留在表面 |
| 广度 | 覆盖性能/可用/扩展 | 覆盖核心功能 | 遗漏关键点 |
| 沟通 | 主动确认需求 | 能回答问题 | 被动等追问 |
