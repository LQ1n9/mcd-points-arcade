@echo off
chcp 65001 >nul
cd /d "%~dp0"

where gh >nul 2>&1 || (echo [错误] 未检测到 gh，请先安装 GitHub CLI & pause & exit /b 1)
gh auth status >nul 2>&1 || (echo [错误] 未登录 GitHub，请先运行：gh auth login & pause & exit /b 1)

git branch -M main
set REPO=mcd-points-arcade
set REMOTE=https://github.com/LQ1n9/%REPO%.git

gh repo view LQ1n9/%REPO% >nul 2>&1
if %errorlevel%==0 (
  echo [信息] 远程仓库已存在，直接推送
  git remote add origin %REMOTE% 2>nul
  git push -u origin main
) else (
  echo [信息] 创建公开仓库并推送
  gh repo create %REPO% --public --source=. --remote=origin --push --description "麦门积分玩家 McPoints Arcade - 麦当劳官方 MCP 强耦合积分运营台"
)

echo.
echo [完成] 仓库地址： https://github.com/LQ1n9/%REPO%
echo 后续：1) 按 issue_body.md 去官方仓库提报名 Issue  2) 10/16 前按 comment_post.md 发评论区
pause
