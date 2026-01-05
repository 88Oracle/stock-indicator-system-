@echo off
chcp 65001 >nul
echo ======================================================================
echo   Git 仓库初始化和发布脚本
echo ======================================================================
echo.

REM 检查是否在项目根目录
if not exist "src" (
    echo [错误] 请在项目根目录运行此脚本！
    echo 当前目录: %CD%
    pause
    exit /b 1
)

echo [步骤 1/6] 检查Git是否已安装...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Git未安装！请先安装Git: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo [OK] Git已安装
echo.

echo [步骤 2/6] 检查是否已是Git仓库...
if exist ".git" (
    echo [提示] 已是Git仓库，跳过初始化
) else (
    echo [执行] git init
    git init
    if %errorlevel% neq 0 (
        echo [错误] Git初始化失败！
        pause
        exit /b 1
    )
    echo [OK] Git仓库初始化成功
)
echo.

echo [步骤 3/6] 添加所有文件到暂存区...
echo [执行] git add .
git add .
if %errorlevel% neq 0 (
    echo [错误] 添加文件失败！
    pause
    exit /b 1
)
echo [OK] 文件添加成功
echo.

echo [步骤 4/6] 查看要提交的文件...
git status --short
echo.

echo [步骤 5/6] 提交到本地仓库...
set commit_msg=初始提交: 高性能股票指标计算系统，支持110+指标，性能提升52%%
echo [执行] git commit -m "%commit_msg%"
git commit -m "%commit_msg%"
if %errorlevel% neq 0 (
    echo [警告] 提交失败或无文件需要提交
    git status
    pause
)
echo [OK] 提交成功
echo.

echo [步骤 6/6] 重命名主分支为main...
echo [执行] git branch -M main
git branch -M main
echo [OK] 分支重命名成功
echo.

echo ======================================================================
echo   本地Git仓库初始化完成！
echo ======================================================================
echo.
echo 接下来的步骤：
echo.
echo 1. 在Gitee或GitHub上创建远程仓库
echo    - Gitee: https://gitee.com/ (推荐国内用户)
echo    - GitHub: https://github.com/
echo.
echo 2. 复制仓库地址，例如：
echo    https://gitee.com/你的用户名/stock-indicator-system.git
echo.
echo 3. 在命令行执行以下命令：
echo.
echo    git remote add origin 你的仓库地址
echo    git push -u origin main
echo.
echo 详细说明请查看: docs\Git发布指南.md
echo.
pause
