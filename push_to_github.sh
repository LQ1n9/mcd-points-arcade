#!/usr/bin/env bash
# 麦门积分玩家 · 一键推送到 GitHub
# 前置：本机已安装 gh 且执行过 `gh auth login`（OAuth 浏览器授权，账号 LQ1n9）
# 用法：在 Git Bash 中 `bash push_to_github.sh`
set -e
cd "$(dirname "$0")"

echo "== 检查 gh 是否已登录 =="
if ! gh auth status >/dev/null 2>&1; then
  echo "✗ 尚未登录 GitHub。请先运行：gh auth login"
  echo "  登录后用 LQ1n9 账号，勾选 repo 权限，完成后重跑本脚本。"
  exit 1
fi

echo "== 统一分支名为 main =="
git branch -M main

REPO="mcd-points-arcade"
REMOTE="https://github.com/LQ1n9/${REPO}.git"

if gh repo view "LQ1n9/${REPO}" >/dev/null 2>&1; then
  echo "== 远程仓库已存在，直接推送 =="
  git remote add origin "$REMOTE" 2>/dev/null || git remote set-url origin "$REMOTE"
  git push -u origin main
else
  echo "== 创建公开仓库并推送 =="
  gh repo create "$REPO" --public --source=. --remote=origin --push \
    --description "麦门积分玩家 McPoints Arcade · 麦当劳官方 MCP 强耦合积分运营台（覆盖 11 个积分接口含 3 写操作）"
fi

echo ""
echo "✓ 完成。仓库地址："
echo "  https://github.com/LQ1n9/${REPO}"
echo ""
echo "后续两步（不依赖本脚本）："
echo "  1) 按 issue_body.md 去官方仓库 M-China/mcd-developer-innovation-challenge 提报名 Issue"
echo "  2) 10/16 11:00 前按 comment_post.md 在 WorkBuddy 微信推文评论区发战报截图"
