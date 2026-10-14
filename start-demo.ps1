Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $root "demo")
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "需要先安装 Node.js"
}
if (-not (Test-Path "node_modules")) {
    Write-Host "正在安装依赖..."
    npm install
}
Write-Host "启动演示：浏览器打开终端里打印的本地地址"
npm run dev
