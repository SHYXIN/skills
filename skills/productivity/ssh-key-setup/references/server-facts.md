# ssh-key-setup —— 参考数据

技能启动时（前置条件阶段）读一次本文件。

---

## 默认远端清单

Step 2 让用户确认这份清单：

| 远端域名 | 上传页面 | 验证命令 | 期望的成功输出 |
|---|---|---|---|
| `gitlab.deepexi.com` | `https://gitlab.deepexi.com/-/profile/keys` | `ssh -T -o StrictHostKeyChecking=accept-new git@gitlab.deepexi.com` | `Welcome to GitLab, @<用户名>!` |
| `github.com` | `https://github.com/settings/keys` | `ssh -T -o StrictHostKeyChecking=accept-new git@github.com` | `Hi <用户名>! You've successfully authenticated...` |
| `gitee.com` | `https://gitee.com/profile/sshkeys` | `ssh -T -o StrictHostKeyChecking=accept-new git@gitee.com` | `Welcome to Gitee, @<用户名>!` |

### 清单之外的远端

用户指名了清单外的远端时：
1. 上传页面用用户给的（或猜 `https://<host>/settings/keys` / `/-/profile/keys`）
2. 验证命令用 `ssh -T git@<host>`
3. 远端返回的任何成功响应都当作身份字符串

---

## 文件约定

| 条目 | 路径 | 备注 |
|---|---|---|
| 私钥 | `~/.ssh/id_ed25519` | 600 |
| 公钥 | `~/.ssh/id_ed25519.pub` | 644 |
| 已知 host | `~/.ssh/known_hosts` | ssh 自动维护 |
| 待清理的旧凭据 | `~/.git-credentials`, `~/.netrc` | 置空或删 PAT 条目 |

---

## 上传前自检

在生成密钥的那台机器上打公钥（这遍是干净的，避免跨系统复制）：

```bash
cat ~/.ssh/id_ed25519.pub
```

打指纹（让用户在上传确认 UI 中对一下是不是同一把）：

```bash
ssh-keygen -lf ~/.ssh/id_ed25519.pub
```
