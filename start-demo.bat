@echo off
setlocal
cd /d "%~dp0demo"
if not exist "package.json" (
  echo 未找到 demo\package.json
  exit /b 1
)
where node >nul 2>&1
if errorlevel 1 (
  echo 需要先安装 Node.js
  exit /b 1
)
if not exist "node_modules\" (
  echo 正在安装依赖...
  call npm install
  if errorlevel 1 exit /b 1
)
echo 启动演示：浏览器打开终端里打印的本地地址
call npm run dev
endlocal
