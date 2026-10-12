"""麦当劳 MCP Streamable-HTTP 客户端（可复用模块）。

协议：Streamable HTTP + Bearer 鉴权。
真实返回：markdown 说明 + `## Original Response` 内嵌业务 JSON。
"""
import json
import sys
import urllib.request
import urllib.error


class McdMCP:
    BASE = "https://mcp.mcd.cn"

    def __init__(self, token: str):
        self.token = token
        self.session = ""
        self._id = 0

    def _next_id(self):
        self._id += 1
        return self._id

    def _post(self, method, params=None, is_notification=False):
        body = {"jsonrpc": "2.0", "method": method}
        if not is_notification:
            body["id"] = self._next_id()
        if params is not None:
            body["params"] = params
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(self.BASE, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        try:
            resp = urllib.request.urlopen(req, timeout=30)
        except urllib.error.HTTPError as e:
            txt = e.read().decode("utf-8", "replace")
            raise RuntimeError(f"HTTP {e.code}: {txt[:500]}")
        if "Mcp-Session-Id" in resp.headers:
            self.session = resp.headers["Mcp-Session-Id"]
        raw = resp.read().decode("utf-8", "replace")
        # 可能返回 SSE 流 或 纯 JSON
        if raw.strip().startswith("event:") or "data:" in raw:
            return self._parse_sse(raw)
        try:
            return json.loads(raw)
        except Exception:
            return {"_raw": raw}

    @staticmethod
    def _parse_sse(raw):
        out = None
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                payload = line[len("data:"):].strip()
                if payload:
                    try:
                        out = json.loads(payload)
                    except Exception:
                        pass
        return out or {"_raw": raw}

    def initialize(self):
        r = self._post("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcd-arcade", "version": "1.0.0"},
        })
        # 发送 initialized 通知
        self._post("notifications/initialized", is_notification=True)
        return r

    def list_tools(self):
        return self._post("tools/list", {})

    def call(self, name, arguments):
        return self._post("tools/call", {"name": name, "arguments": arguments})


def extract_payload(result):
    """从 tools/call 的 result 中抽取业务 JSON。
    入参可能是 JSON-RPC 信封 {jsonrpc,id,result:{content:[...]}}，
    也可能是已拆开的 {content:[...]}。
    """
    if not isinstance(result, dict):
        return result
    res = result.get("result", result)
    content = res.get("content") if isinstance(res, dict) else None
    if not content:
        return result
    text = ""
    for blk in content:
        if isinstance(blk, dict) and blk.get("type") == "text":
            text += blk.get("text", "")
    if not text:
        return result
    return _first_json(text, fallback_text=text)


def _first_json(text, fallback_text=""):
    """找第一个非空业务 JSON 对象。跳过空容器。"""
    marker = "## Original Response"
    seg = text
    if marker in text:
        seg = text.split(marker, 1)[1]
    # 逐字符扫描找 JSON
    start = -1
    for i, ch in enumerate(seg):
        if ch in "{[":
            start = i
            break
    if start < 0:
        return {"_text": fallback_text or text}
    depth = 0
    instr = False
    esc = False
    for i in range(start, len(seg)):
        c = seg[i]
        if esc:
            esc = False
            continue
        if c == "\\":
            esc = True
            continue
        if c == '"':
            instr = not instr
            continue
        if instr:
            continue
        if c in "{[":
            depth += 1
        elif c in "}":
            depth -= 1
            if depth == 0:
                cand = seg[start:i + 1]
                try:
                    obj = json.loads(cand)
                except Exception:
                    return {"_text": fallback_text or text}
                # 跳过空容器，继续找真正的业务 JSON
                if obj in ({}, [], {"data": []}, {"data": {}}):
                    # 重新从 i+1 找
                    rest = seg[i + 1:]
                    nxt = _first_json(rest, fallback_text)
                    if isinstance(nxt, dict) and "_text" not in nxt:
                        return nxt
                    return nxt
                return obj
        elif c in "]":
            depth -= 1
            if depth == 0:
                cand = seg[start:i + 1]
                try:
                    obj = json.loads(cand)
                except Exception:
                    return {"_text": fallback_text or text}
                if obj in ([], {}):
                    rest = seg[i + 1:]
                    return _first_json(rest, fallback_text)
                return obj
    return {"_text": fallback_text or text}


if __name__ == "__main__":
    tok = sys.argv[1] if len(sys.argv) > 1 else ""
    if not tok:
        print("用法: python mcd_mcp.py <TOKEN>", file=sys.stderr)
        sys.exit(1)
    m = McdMCP(tok)
    m.initialize()
    t = m.list_tools()
    tools = (t or {}).get("result", {}).get("tools", [])
    print(f"共 {len(tools)} 个工具")
    for tl in tools:
        nm = tl.get("name")
        desc = (tl.get("description") or "")[:60]
        print(f"\n### {nm}\n{desc}")
        sch = tl.get("inputSchema", {})
        props = sch.get("properties", {})
        req = sch.get("required", [])
        for p, info in props.items():
            flag = "必填" if p in req else "可选"
            t_ = info.get("type", "?")
            print(f"  - {p} ({flag}, {t_}): {info.get('description','')[:50]}")
