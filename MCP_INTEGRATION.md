# MCP 接入说明（MCP_INTEGRATION.md）

本文件说明「麦门积分玩家 / McPoints Arcade」实际使用的麦当劳官方 MCP 工具、调用流程与业务价值，作为赛事必交材料。

---

## 接入概要

| 项目 | 内容 |
|---|---|
| 服务地址 | `https://mcp.mcd.cn` |
| 协议 | MCP Streamable HTTP |
| 鉴权方式 | `Authorization: Bearer <MCP_TOKEN>`（Token 经 `https://open.mcd.cn/mcp` 申请） |
| 工具总数 | 35（本作品覆盖其中 **11 个积分生态工具**） |
| 写操作 | **3 个**：`draw-lottery` / `mall-create-order` / `auto-bind-coupons` |
| 客户端 | `mcd_arcade.py`（零依赖 Python 标准库）+ `mcd_mcp.py`（传输层） |

---

## 工具映射：11 个积分生态接口

| 工具 | 读/写 | 业务模块 | 真实入参（已核验） |
|---|---|---|---|
| `query-my-account` | 读 | 账户体检官 | 无参 → `data.availablePoint / nextMouthExpirePoint` 等 |
| `query-lottery-info` | 读 | 奖池情报站 | 无参 → `data.drawPoint / drawDecision.chances / prizes[]` |
| `query-my-prizes` | 读 | 奖品战绩 | `{pageNum, pageSize}` |
| `mall-points-products` | 读 | 商城淘金侠 | `{catRuleIds:"1>4"}` → `data[].spuName/spuId/point/selling` |
| `mall-product-detail` | 读 | 兑换详情 | `{spuId}` |
| `query-my-coupons` | 读 | 卡券收纳师 | `{page, pageSize}`（返回 markdown，正则解析） |
| `available-coupons` | 读 | 可领券 | 无参（返回 markdown） |
| `campaign-calendar` | 读 | 活动日历 | 可选 `{specifiedDate}` |
| `now-time-info` | 读 | 时间基准 | 无参（临期计算用） |
| **`draw-lottery`** ⭐ | **写** | 抽奖参谋 | 无参；服务端原子扣积分 + 出奖 |
| **`mall-create-order`** ⭐ | **写** | 商城兑换 | `{skuId, count, spuCategory, addressId?}` |
| **`auto-bind-coupons`** ⭐ | **写** | 一键领券 | 无参；领取当前可领全部券 |

> 其余 24 个工具（门店/点餐/订单/派对/团餐/营养等）未在本作品主链路使用，但同属官方 MCP 能力，可按扩展需求接入。

---

## 强耦合证据

1. **数据零本地造假**：账户余额、奖池、商城商品、卡包券全部来自实时接口。无 Token 时仅进入清晰标注的演示模式，不存在"离线也能跑"的影子实现。
2. **真实写入**：抽奖 / 兑换 / 领券三个写操作直接作用于用户真实积分账户与卡包，是品牌最希望被开发者用到的能力。
3. **已真实验证**：全部 11 个工具均对真实 MCP 调通（样例见 `examples/`）。

---

## 调用流程（以战报为例）

```
now-time-info（探活+时间基准）
   └─ query-my-account         → 账户体检
   └─ query-lottery-info       → 奖池情报
   └─ mall-points-products     → 商城性价比排序（解析 selling 中"X元"算每元积分成本）
   └─ query-my-coupons         → 卡包盘点（markdown 正则解析 + 临期计算）
   └─ 汇总 → 真实战报
```

写操作额外步骤（consent-gated）：

```
draw   : query-lottery-info 校验可抽次数 → 展示策略 → 用户确认 --yes → draw-lottery
redeem : mall-product-detail 取积分价   → 展示成本 → 用户确认 --yes → mall-create-order
autobind: available-coupons 统计可领数  → 展示清单 → 用户确认 --yes → auto-bind-coupons
```

---

## 返回格式说明

官方 MCP 返回为 `markdown 说明 + ## Original Response 内嵌业务 JSON`。`mcd_mcp.py` 的 `extract_payload` 负责钻取 `result.content[].text` 并定位首个非空业务 JSON（`_first_json` 跳过空容器 `{}` / `[]` / `{"data":[]}`）。卡券类接口（`query-my-coupons` / `available-coupons`）返回纯 markdown，由 `parse_coupons_md` 正则解析。
