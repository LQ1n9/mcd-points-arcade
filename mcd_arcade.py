#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦门积分玩家 / McPoints Arcade —— 麦当劳中国官方 MCP 强耦合积分运营台。

定位：把你在麦当劳真实积分生态里的「查—抽—兑—领」做成一套玩家化运营台。
强耦合：核心数据全部来自麦当劳官方 MCP 实时接口，离开 MCP 概不成立。

覆盖工具（11 个积分生态接口，含 3 个写操作）：
  读：query-my-account / query-lottery-info / query-my-prizes /
      mall-points-products / mall-product-detail / query-my-coupons /
      available-coupons / campaign-calendar / now-time-info
  写：draw-lottery ⭐ / mall-create-order ⭐ / auto-bind-coupons ⭐
      （写操作均为 consent-gated，未获明确授权绝不调用）

合规边界：
  - 不提供任何"算命/命运/天意"类输出，全部基于真实账户数据做策略与预警。
  - 不贬低品牌、不宣扬不健康饮食 / 拜金 / 娱乐至上；定位为"把手里的积分用足、别浪费"。
  - 写操作消耗真实积分 / 生成真实订单，必须经过用户明确确认。

仅使用 Python 标准库，直连 https://mcp.mcd.cn（Streamable HTTP + Bearer 鉴权）。
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

import mcd_mcp as M

PROFILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arcade_profile.json")


# ---------------------------------------------------------------------------
# 本地玩家档案（数据全来自 MCP，这里只存"动作战绩"用于玩家等级与战报）
# ---------------------------------------------------------------------------
def load_profile():
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"draws": 0, "wins": 0, "redeems": 0, "redeem_items": [],
            "autobinds": 0, "first_scan": None, "last_scan": None}


def save_profile(p):
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)


def player_tier(p):
    """玩家等级：按真实动作累计。轻量趣味化，非宣扬拜金。"""
    score = p["draws"] + p["redeems"] * 2 + p["autobinds"]
    if score == 0:
        return "新晋麦门学徒", "攒够积分，开启你的第一抽"
    if score < 5:
        return "麦门见习生", "动作熟练中，积分开始为你打工"
    if score < 15:
        return "积分操盘手", "查抽兑领已成肌肉记忆"
    if score < 40:
        return "麦门策展人", "你的积分生态被你打理得井井有条"
    return "麦门宗师", "把每一分积分都用在刀刃上"


# ---------------------------------------------------------------------------
# 演示数据（无 Token 时清晰标注，绝不冒充真实）
# ---------------------------------------------------------------------------
DEMO = {
    "query-my-account": {
        "success": True, "code": 200, "message": "请求成功",
        "data": {
            "availablePoint": "1280", "accountId": "DEMO",
            "accumulativePoint": "5320", "currency": "麦享会积分",
            "currentMouthExpirePoint": "0", "expiredPoint": "0",
            "frozenPoint": "0", "lastMouthExpirePoint": "0",
            "nextMouthExpirePoint": "300", "usedPoint": "4040",
        },
    },
    "query-lottery-info": {
        "success": True, "code": 200, "message": "请求成功",
        "data": {
            "status": {"code": "SUCCESS", "message": "成功"},
            "activityCode": "dtx2", "activityStatusText": "进行中",
            "activityName": "麦麦积分抽奖", "beginTime": "2025-01-26 00:00:00",
            "endTime": "2030-12-31 23:59:59", "drawPoint": "24",
            "drawTypeText": "消耗积分抽奖", "availablePoint": "1280",
            "drawDecision": {
                "resourceEligible": True, "reason": "",
                "nextConsumption": {"type": "POINTS", "points": "24",
                                    "chances": 53, "text": "本次将消耗 24 积分"},
            },
            "prizes": [
                {"name": "下单立减3元券", "typeText": "优惠券"},
                {"name": "下单立减2元券", "typeText": "优惠券"},
                {"name": "下单立减1元券", "typeText": "优惠券"},
                {"name": "麦辣三件套5折券", "typeText": "优惠券"},
                {"name": "板烧三件套5折券", "typeText": "优惠券"},
                {"name": "甜辣小食组合5折券", "typeText": "优惠券"},
                {"name": "谢谢参与", "typeText": "未中奖"},
                {"name": "谢谢参与", "typeText": "未中奖"},
            ],
        },
    },
    "mall-points-products": {
        "success": True, "code": 200, "message": "请求成功",
        "data": [
            {"spuName": "18.8元2份麦辣鸡翅", "spuId": 6113, "point": "200",
             "selling": "18.8元2份麦辣鸡翅", "catName": "到店专用", "status": 2},
            {"spuName": "10.9元指定小食任选", "spuId": 17077, "point": "200",
             "selling": "10.9元指定小食任选1份", "catName": "到店专用", "status": 2},
            {"spuName": "16.9元麦辣可乐组合", "spuId": 17079, "point": "500",
             "selling": "16.9元麦辣可乐组合", "catName": "到店专用", "status": 2},
            {"spuName": "21.9元巨无霸可乐组合", "spuId": 17081, "point": "800",
             "selling": "21.9元巨无霸可乐组合", "catName": "到店专用", "status": 2},
        ],
    },
    "query-my-prizes": {
        "success": True, "code": 200, "message": "请求成功",
        "data": {"status": {"code": "SUCCESS", "message": "成功"},
                 "prizes": [{"name": "下单立减2元券", "statusText": "已领取"}],
                 "pageNum": 1, "pageSize": 5, "hasMore": False},
    },
    "query-my-coupons": {
        "_text": "# 您的优惠券列表\n\n共 3 张可用优惠券 | 第 1/1 页\n\n"
                 "## 新人专享-中杯美式7折\n- **优惠**: ¥13.3\n"
                 "- **有效期**: 2026-10-12 00:00-2026-11-10 23:59\n- **标签**: 到店专用\n\n"
                 "## 麦辣三件套5折券\n- **优惠**: 5折\n"
                 "- **有效期**: 2026-10-12 00:00-2026-10-20 23:59\n- **标签**: 到店专用\n\n"
                 "## 下单立减2元券\n- **优惠**: 立减2元\n"
                 "- **有效期**: 2026-10-12 00:00-2026-11-15 23:59\n- **标签**: 到店专用\n",
    },
    "campaign-calendar": {
        "_text": "### 当前时间：2026-10-12\n\n#### 今日\n- **活动标题**：9.9元早餐两件套\n"
                 "  **活动内容介绍**：早八的快乐，一堡一咖已就位\n\n"
                 "#### 即将\n- **活动标题**：麦麦积分抽奖进行中\n  **活动内容介绍**：消耗积分抽券，别让积分睡大觉\n",
    },
}


# ---------------------------------------------------------------------------
# 工具：解析器
# ---------------------------------------------------------------------------
def _num(s):
    try:
        return int(float(s))
    except Exception:
        return 0


def parse_cash(text):
    """从文案里解析现金价值（元）。"""
    if not text:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*元", text)
    return float(m.group(1)) if m else None


def parse_coupons_md(text):
    """把 query-my-coupons / available-coupons 返回的 markdown 解析成结构化列表。"""
    out = []
    blocks = re.split(r"\n##\s+", text)
    for b in blocks[1:]:
        lines = b.splitlines()
        name = lines[0].strip()
        item = {"name": name}
        for ln in lines[1:]:
            if "**优惠**" in ln:
                item["discount"] = ln.split("**优惠**:", 1)[-1].strip()
            elif "**有效期**" in ln:
                seg = ln.split("**有效期**:", 1)[-1].strip()
                item["valid"] = seg
                m = re.search(r"(\d{4}-\d{2}-\d{2})[ \d:]*?-(\d{4}-\d{2}-\d{2})", seg)
                if m:
                    item["expire"] = m.group(2)
            elif "**标签**" in ln:
                item["tag"] = ln.split("**标签**:", 1)[-1].strip()
        out.append(item)
    return out


def days_left(expire_str, now):
    if not expire_str:
        return None
    try:
        ed = datetime.strptime(expire_str, "%Y-%m-%d")
        return (ed.date() - now.date()).days
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 客户端
# ---------------------------------------------------------------------------
class Arcade:
    def __init__(self, token=None):
        self.token = token
        self.mcp = M.McdMCP(token) if token else None
        self.demo = token is None
        if not self.demo:
            self.mcp.initialize()

    def _call(self, name, args):
        if self.demo:
            if name in DEMO:
                return DEMO[name]
            # 写操作演示：不执行，返回占位
            return {"_demo_write": name, "args": args}
        return M.extract_payload(self.mcp.call(name, args))

    def now(self):
        if self.demo:
            return datetime(2026, 10, 12)
        try:
            r = M.extract_payload(self.mcp.call("now-time-info", {}))
            ds = (r.get("data") or {}).get("dateTime") or (r.get("data") or {}).get("date") or ""
            return datetime.strptime(ds[:19], "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.now()

    # ---- 模块 1：账户体检官 ----
    def account(self):
        d = (self._call("query-my-account", {}) or {}).get("data", {}) or {}
        avail = _num(d.get("availablePoint"))
        lines = []
        lines.append(f"💳 积分账户体检（{d.get('currency','麦享会积分')}）")
        lines.append(f"  可用积分：{avail}")
        lines.append(f"  累计获得：{_num(d.get('accumulativePoint'))}")
        lines.append(f"  累计已用：{_num(d.get('usedPoint'))}")
        lines.append(f"  累计过期：{_num(d.get('expiredPoint'))}")
        nxt = _num(d.get("nextMouthExpirePoint"))
        cur = _num(d.get("currentMouthExpirePoint"))
        if cur > 0:
            lines.append(f"  ⚠️ 本月将过期：{cur} 分，建议近期用掉")
        if nxt > 0:
            lines.append(f"  ⚠️ 下月将过期：{nxt} 分，月底前安排掉别浪费")
        if avail == 0:
            lines.append("  📌 当前 0 积分：先去门店消费攒积分，再来玩抽奖/兑换")
        return "\n".join(lines)

    # ---- 模块 2：奖池情报站 ----
    def lottery(self):
        d = (self._call("query-lottery-info", {}) or {}).get("data", {}) or {}
        dec = d.get("drawDecision", {}) or {}
        chances = _num((dec.get("nextConsumption") or {}).get("chances"))
        cost = _num(d.get("drawPoint"))
        lines = []
        lines.append(f"🎯 奖池情报站：{d.get('activityName','麦麦积分抽奖')}（{d.get('activityStatusText','')}）")
        lines.append(f"  单次消耗：{cost} 积分")
        if dec.get("resourceEligible"):
            lines.append(f"  剩余可抽：{chances} 发")
            lines.append(f"  按当前积分可抽满，建议别让次数睡大觉")
        else:
            lines.append(f"  ⛔ {dec.get('reason','积分不足')}（需 {cost} 分/发）")
        pool = d.get("prizes", []) or []
        if pool:
            real = [p for p in pool if (p.get("typeText") != "未中奖")]
            lines.append(f"  奖池（{len(real)} 种奖品）：" + "、".join(p.get("name", "") for p in real[:6]))
        return "\n".join(lines)

    # ---- 模块 3：抽奖参谋 + 真抽（写） ----
    def draw(self, times, yes):
        d = (self._call("query-lottery-info", {}) or {}).get("data", {}) or {}
        dec = d.get("drawDecision", {}) or {}
        cost = _num(d.get("drawPoint"))
        chances = _num((dec.get("nextConsumption") or {}).get("chances"))
        if not dec.get("resourceEligible") or chances <= 0:
            return (f"⛔ 当前积分不足或无可抽次数（{dec.get('reason','积分不足')}），"
                    f"无法抽奖。先攒积分再来。")
        times = min(times or 1, chances)
        # 策略建议
        plan = (f"🎯 抽奖参谋：可抽 {chances} 发，单次 {cost} 分。\n"
                f"   策略：奖池为各类下单券，建议一次抽完把次数用足，"
                f"中奖券自动进卡包。本次将抽 {times} 发，消耗 {times*cost} 分。")
        if not self._consent(f"确认消耗 {times*cost} 积分抽奖 {times} 发？", yes):
            return plan + "\n❌ 已取消，未消耗任何积分。"
        if self.demo:
            return plan + "\n[演示模式] 未真实调用 draw-lottery。"
        # 真实调用
        out = [plan]
        p = load_profile()
        for i in range(times):
            r = M.extract_payload(self.mcp.call("draw-lottery", {}))
            p["draws"] += 1
            res = (r.get("data") or {})
            prize = res.get("prize") or res.get("name") or r
            won = "谢谢参与" not in json.dumps(prize, ensure_ascii=False)
            if won:
                p["wins"] += 1
                out.append(f"  第{i+1}发：🎁 中 {prize}")
            else:
                out.append(f"  第{i+1}发：🌀 谢谢参与")
        save_profile(p)
        out.append(f"✅ 共抽 {times} 发，赢 {p['wins']} 次（累计）。战绩已记入玩家档案。")
        return "\n".join(out)

    # ---- 模块 4：商城淘金侠（读）+ 兑换（写） ----
    def mall(self):
        arr = (self._call("mall-points-products", {"catRuleIds": "1>4"}) or {}).get("data", []) or []
        if isinstance(arr, dict):
            arr = arr.get("data", []) or []
        rows = []
        for it in arr:
            if not isinstance(it, dict):
                continue
            cash = parse_cash(it.get("spuName") or it.get("selling") or "")
            pt = _num(it.get("point"))
            eff = round(pt / cash, 1) if cash else None
            rows.append({
                "name": it.get("spuName", ""),
                "spu": it.get("spuId"),
                "point": pt,
                "cash": cash,
                "eff": eff,
                "cat": it.get("catName", ""),
                "down": it.get("downTime", ""),
            })
        rows.sort(key=lambda x: (x["eff"] is None, x["eff"] if x["eff"] is not None else 1e9))
        lines = ["🛒 商城淘金侠：积分兑换餐品券（按「每元积分成本」升序，越靠前越值）"]
        for i, r in enumerate(rows[:12], 1):
            eff_s = f"{r['eff']}分/元" if r["eff"] is not None else "—"
            cash_s = f"¥{r['cash']}" if r["cash"] else "—"
            lines.append(f"  {i}. {r['name']} ｜ {r['point']}分 ≈ {cash_s} ｜ {eff_s} ｜ {r['cat']}")
        lines.append("  💡 想兑换：mcd_arcade.py redeem --spu <ID> [--count N] --yes")
        return "\n".join(lines)

    def redeem(self, spu, count, address, yes):
        prod = None
        if self.demo:
            for it in (DEMO.get("mall-points-products", {}).get("data", []) or []):
                if it.get("spuId") == spu:
                    prod = it
                    break
            if prod is None:
                prod = {"spuName": f"spu {spu}", "point": "0", "spuCategory": "1"}
        else:
            info = self._call("mall-product-detail", {"spuId": spu})
            if isinstance(info, dict) and "data" in info:
                prod = info["data"]
        name = (prod or {}).get("spuName") or f"spu {spu}"
        pt = _num((prod or {}).get("point"))
        cat = str((prod or {}).get("spuCategory") or "1")
        summary = (f"🛒 兑换参谋：{name}（{pt}分/份 × {count}）"
                   + (f" 配送地址 {address}" if address else " 到店券"))
        if not self._consent(f"确认消耗 {pt*count} 积分兑换 {count} 份 {name}？", yes):
            return summary + "\n❌ 已取消，未生成订单。"
        if self.demo:
            return summary + "\n[演示模式] 未真实调用 mall-create-order。"
        args = {"skuId": spu, "count": count, "spuCategory": cat}
        if cat == "2" and address:
            args["addressId"] = address
        r = M.extract_payload(self.mcp.call("mall-create-order", args))
        p = load_profile()
        p["redeems"] += 1
        p["redeem_items"].append({"name": name, "count": count, "at": str(self.now())})
        save_profile(p)
        return summary + f"\n✅ 兑换订单已提交：{json.dumps(r, ensure_ascii=False)[:200]}"

    # ---- 模块 5：卡券收纳师（读）+ 自动领（写） ----
    def coupons(self):
        now = self.now()
        mine = parse_coupons_md((self._call("query-my-coupons", {"page": "1", "pageSize": "200"}) or {}).get("_text", ""))
        avail = parse_coupons_md((self._call("available-coupons", {}) or {}).get("_text", ""))
        lines = [f"🎫 卡券收纳师：卡包 {len(mine)} 张"]
        soon = []
        for c in mine:
            dl = days_left(c.get("expire"), now)
            tag = f"（{dl}天后到期）" if dl is not None else ""
            if dl is not None and dl <= 7:
                soon.append(c["name"])
            lines.append(f"  - {c['name']} ｜ {c.get('discount','')} ｜ 有效至 {c.get('expire','')} {tag}")
        if soon:
            lines.append(f"  ⚠️ 临期请优先用：{'、'.join(soon)}")
        if avail:
            lines.append(f"📥 还可领 {len(avail)} 张：{'、'.join(c['name'] for c in avail[:5])}")
            lines.append("  💡 一键领取：mcd_arcade.py autobind --yes")
        return "\n".join(lines)

    def autobind(self, yes):
        n = len(parse_coupons_md((self._call("available-coupons", {}) or {}).get("_text", "")))
        summary = f"📥 自动领券：将领取当前可领的 {n} 张麦麦省优惠券。"
        if not self._consent("确认一键领取所有可领优惠券？", yes):
            return summary + "\n❌ 已取消。"
        if self.demo:
            return summary + "\n[演示模式] 未真实调用 auto-bind-coupons。"
        r = M.extract_payload(self.mcp.call("auto-bind-coupons", {}))
        p = load_profile()
        p["autobinds"] += 1
        save_profile(p)
        return summary + f"\n✅ 领取结果：{json.dumps(r, ensure_ascii=False)[:200]}"

    # ---- 模块 6：活动日历 ----
    def calendar(self):
        t = (self._call("campaign-calendar", {}) or {}).get("_text", "")
        return "📅 活动日历（真实）\n" + (t[:600] if t else "（暂无）")

    # ---- 玩家档案 ----
    def profile(self):
        p = load_profile()
        tier, motto = player_tier(p)
        now = str(self.now())
        p["last_scan"] = now
        if not p["first_scan"]:
            p["first_scan"] = now
        save_profile(p)
        lines = ["🏅 麦门玩家档案"]
        lines.append(f"  等级：{tier}")
        lines.append(f"  格言：{motto}")
        lines.append(f"  累计抽奖 {p['draws']} 发 / 中奖 {p['wins']} 次")
        lines.append(f"  累计兑换 {p['redeems']} 次")
        lines.append(f"  累计自动领券 {p['autobinds']} 次")
        return "\n".join(lines)

    # ---- 战报 ----
    def report(self):
        now = self.now()
        p = load_profile()
        tier, _ = player_tier(p)
        acc = self.account()
        lot = self.lottery()
        mal = self.mall()
        cp = self.coupons()
        bar = "=" * 30
        return (
            f"{bar}\n  麦门积分玩家 · 我的真实积分战报\n  生成于 {now}\n{bar}\n"
            f"{acc}\n\n{lot}\n\n{mal}\n\n{cp}\n\n"
            f"🏅 玩家等级：{tier}\n{bar}\n"
            f"本战报由麦当劳官方 MCP 实时数据生成 · McPoints Arcade\n{bar}"
        )

    # ---- 同意闸门 ----
    @staticmethod
    def _consent(prompt, yes):
        if yes:
            return True
        if not sys.stdin.isatty():
            return False
        try:
            return input(f"{prompt} [y/N] ").strip().lower() in ("y", "yes")
        except Exception:
            return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(prog="mcd_arcade.py",
                                 description="麦门积分玩家 McPoints Arcade —— 麦当劳官方 MCP 强耦合积分运营台")
    ap.add_argument("cmd", nargs="?", default="report",
                    help="account/lottery/draw/mall/redeem/coupons/autobind/calendar/profile/report/tools")
    ap.add_argument("--times", type=int, default=1)
    ap.add_argument("--spu", type=int)
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--address", default=None)
    ap.add_argument("--yes", action="store_true", help="写操作明确授权（非交互环境必带）")
    ap.add_argument("--token", default=None, help="麦当劳 MCP Token（或设 MCD_MCP_TOKEN 环境变量）")
    args = ap.parse_args()

    token = args.token or os.environ.get("MCD_MCP_TOKEN")
    a = Arcade(token)
    if a.demo:
        print("【演示模式】未检测到 MCD_MCP_TOKEN，使用清晰标注的演示数据。"
              "配置真实 Token 后即为实时真实数据。\n")

    cmd = args.cmd
    try:
        if cmd == "account":
            print(a.account())
        elif cmd == "lottery":
            print(a.lottery())
        elif cmd == "draw":
            print(a.draw(args.times, args.yes))
        elif cmd == "prizes":
            print(json.dumps(a._call("query-my-prizes", {"pageNum": "1", "pageSize": "10"}),
                              ensure_ascii=False, indent=1))
        elif cmd == "mall":
            print(a.mall())
        elif cmd == "redeem":
            if not args.spu:
                print("redeem 需要 --spu <ID>")
            else:
                print(a.redeem(args.spu, args.count, args.address, args.yes))
        elif cmd == "coupons":
            print(a.coupons())
        elif cmd == "autobind":
            print(a.autobind(args.yes))
        elif cmd == "calendar":
            print(a.calendar())
        elif cmd == "profile":
            print(a.profile())
        elif cmd == "report":
            print(a.report())
        elif cmd == "tools":
            print("积分生态工具：query-my-account, query-lottery-info, draw-lottery(写), "
                  "query-my-prizes, mall-points-products, mall-product-detail, mall-create-order(写), "
                  "query-my-coupons, available-coupons, auto-bind-coupons(写), campaign-calendar")
        else:
            print(f"未知命令：{cmd}")
            ap.print_help()
    except Exception as e:
        print(f"执行出错：{e}")


if __name__ == "__main__":
    main()
