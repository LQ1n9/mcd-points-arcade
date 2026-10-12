# WorkBuddy 联动开发上下文（workbuddy.md）

> 本文件用于核验本项目「真实使用腾讯 WorkBuddy 智能体」开发，作为 WorkBuddy 专项奖励（前 100 名 + 提交本文件 = 3000 积分）的凭证。
> 以下为使用 WorkBuddy 开发「麦门积分玩家 McPoints Arcade」的对话上下文节选（已脱敏，不含任何 Token / 个人信息）。

---

## 一、作品概览

- **作品名**：麦门积分玩家 / McPoints Arcade
- **定位**：麦当劳中国官方 MCP 驱动的「积分运营台」，覆盖 11 个积分生态工具（含 3 个写操作）
- **交付形态**：① WorkBuddy 原生 Skill（`SKILL.md`）② 零依赖 Python 客户端（`mcd_arcade.py`）
- **强耦合证据**：账户 / 奖池 / 商城 / 卡券全部来自官方 MCP 实时接口；抽奖 / 兑换 / 领券为真实写操作

## 二、WorkBuddy 在开发中的真实角色

| 阶段 | WorkBuddy 做了什么 |
|---|---|
| 需求与定位 | 从「产品定位 / 贴合活动 / 趣味设计 / 热门内容」四维度收敛，并据赛事博弈（排名看 Star、仓库要"活"）把作品从弱耦合 demo 重做成强耦合 Skill |
| MCP 接入 | 直连 `https://mcp.mcd.cn`，拉取 35 工具清单、核验写操作真实入参 |
| 代码 | 生成 `mcd_mcp.py`（Streamable HTTP 传输层）与 `mcd_arcade.py`（积分运营台客户端） |
| 合规 | 把关"不迷信 / 不贬品牌 / 不拜金 / 写操作 consent-gated"红线 |
| 文档 | 同步生成 README / SKILL / MCP_INTEGRATION / 本文件 |

## 三、关键对话上下文（脱敏节选）

```
用户：重新思考做什么样的 skill 参加比赛
WorkBuddy：复盘发现旧版仅用了 8 个 GET 工具、13 个写操作能力浪费，作品弱耦合（demo 能跑证明离开 MCP 也能活）。
           建议方向 A「麦门积分玩家」——用 draw-lottery / mall-create-order / auto-bind-coupons 做强耦合积分玩法。

用户：a（确认方向 A）
WorkBuddy：拉取真实 35 工具清单，核验 query-my-account / query-lottery-info / mall-points-products /
           query-my-coupons / campaign-calendar 真实返回结构，写出精准解析器；写操作 consent-gated，未擅自调用。

用户：按要求设计啊 / ？活动是这么写的吗
WorkBuddy：核对官方赛事规则（排名只看 GitHub 公开 Star、2026-10-26 定榜、用 WorkBuddy 交 workbuddy.md 加 3000 积分等），
           并将强耦合与真实战报作为传播/留存抓手。
```

## 四、如何复现

1. WorkBuddy「连接器」配置麦当劳 MCP（`https://mcp.mcd.cn`，Bearer）。
2. 安装 `SKILL.md` → 对话"查我的麦当劳积分战报"即触发全链路。
3. 或运行 `python mcd_arcade.py report`（需 `MCD_MCP_TOKEN`）。

---

© 本文件随作品公开，不含任何敏感信息。
