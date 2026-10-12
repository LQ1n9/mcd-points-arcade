# 提交指南（SUBMIT_GUIDE.md）

> 本文件为**本地操作指南**（非参赛必交件）：汇总推送、报名、评论文案的操作步骤。可随仓库公开，也可在推送前删除，不影响参赛资格。

---

## 一、仓库与文件清单（必交）

建议 GitHub 仓库名：**`mcd-points-arcade`**（本地文件夹 `mcd-mcdaily-pick` 可整体推送，仓库名在 GitHub 侧指定）。

| 文件 | 是否必交 | 说明 |
|---|---|---|
| `README.md` | 必交 | 作品首页，含真实战报钩子 |
| `SKILL.md` | 必交 | WorkBuddy 原生 Skill（如用 WorkBuddy 开发需交） |
| `workbuddy.md` | 必交（若用 WorkBuddy） | WorkBuddy 专项奖励凭证，前 100 名 + 本文件 = +3000 积分 |
| `CONTEST_DECLARATION.md` | 必交 | 参赛声明（官方原文，未改动） |
| `MCP_INTEGRATION.md` | 建议 | 工具映射与强耦合证据 |
| `mcd_arcade.py` / `mcd_mcp.py` | 建议 | 零依赖客户端与传输层 |
| `examples/` | 建议 | 真实样例输出 |
| `mcp-config.example.json` | 建议 | MCP 连接器配置样例 |

---

## 二、时间线与硬条件（官方规则核对）

- **定榜时间**：2026-10-26 00:00（排名只看 GitHub 公开 Star；Star=0 不进榜）。
- **仓库创建窗口**：2025-12-25 ~ 2026-10-25。
- **资格**：中国大陆居民，年满 18 周岁。
- **WorkBuddy 奖励**：使用 WorkBuddy 并在仓库提交 `workbuddy.md` → 前 100 名 +3000 积分。
- **评论区活动**：在 WorkBuddy 微信推文评论区（注意：是**推文评论区**，非 GitHub Issue）2026-10-16 11:00 前 Top5 送贴纸。
- **奖项**：前 100 = 汉堡回车键 + 徽章；前 3 = 巨无霸券 50/30/20 次 + 10240 积分。

---

## 三、本地 Git 推送步骤（LQ1n9 账号）

```bash
cd E:/workbuddy/ai/mcd-mcdaily-pick
git init -q
git add -A
git commit -q -m "feat: 麦门积分玩家 McPoints Arcade — 麦当劳官方 MCP 强耦合积分运营台"
# 在 GitHub 新建仓库 mcd-points-arcade（不要勾 README）
git remote add origin https://github.com/LQ1n9/mcd-points-arcade.git
git branch -M main
git push -u origin main
```

> Token 安全：MCD_MCP_TOKEN 仅运行时通过环境变量传入，**绝不写入仓库任何文件**。旧 Token 已多次暴露在对话中，建议去 `https://open.mcd.cn/mcp` 重新生成。

---

## 四、传播 / 留存抓手（冲 Star）

1. **首屏真实战报**：每个用户跑出来都是"我的真实积分战报"，天然可截图分享。
2. **强耦合叙事**：README 明确"离开 MCP 概不成立"，展示对 3 个写操作的真实使用。
3. **评论区**（推文，10-16 11:00 前）：用"麦门积分玩家"战报截图 + 一句话定位参与。

---

## 五、评论文案（推文评论区，仅供参考）

> 参加了 2026 麦当劳程序员创意开发大赛，做了个「麦门积分玩家」：直连官方 MCP，把积分抽奖/商城兑换/卡券收纳做成实时运营台，离开 MCP 跑不起来。已真实验证 11 个积分接口，抽奖/兑换/领券都是真实写操作（需用户确认）。欢迎来 Star 一起玩～

---

⚠️ 合规提醒：作品不提供算命/命运/天意类内容，不贬低品牌，不宣扬不健康/拜金/娱乐至上；写操作均 consent-gated。
