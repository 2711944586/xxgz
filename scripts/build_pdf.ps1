# Compile the monograph to build/ACTS-MCDT.pdf.
# Two passes are required: the first fills the .toc/.aux, the second resolves
# the table of contents and every \ref / \eqref.
#
# Usage:  powershell -ExecutionPolicy Bypass -File scripts/build_pdf.ps1
$ErrorActionPreference = 'Stop'

$root  = Split-Path -Parent $PSScriptRoot
$book  = Join-Path $root 'monograph'
$build = Join-Path $root 'build'

New-Item -ItemType Directory -Force -Path $build | Out-Null

# MiKTeX is expected on PATH; fall back to the per-user install location.
if (-not (Get-Command xelatex -ErrorAction SilentlyContinue)) {
    $candidate = Join-Path $env:LOCALAPPDATA 'Programs\MiKTeX\miktex\bin\x64'
    if (Test-Path (Join-Path $candidate 'xelatex.exe')) { $env:PATH = "$candidate;$env:PATH" }
}
if (-not (Get-Command xelatex -ErrorAction SilentlyContinue)) { throw 'xelatex not found on PATH.' }

# The chapters are pulled in with relative \input, so compilation has to happen
# inside monograph/. Intermediate files are moved to build/ afterwards.
Push-Location $book
try {
    foreach ($pass in 1, 2) {
        Write-Host "=== xelatex pass $pass ==="
        & xelatex -interaction=nonstopmode -jobname=ACTS-MCDT book.tex | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "xelatex pass $pass failed; see build/ACTS-MCDT.log" }
    }
} finally {
    Pop-Location
}

$pdf = Join-Path $book 'ACTS-MCDT.pdf'
if (-not (Test-Path $pdf)) { throw 'PDF was not produced.' }

# Keep only the PDF as a durable artifact; .aux/.log/.toc stay in build/ as diagnostics.
Get-ChildItem $book -Filter 'ACTS-MCDT.*' | Where-Object { $_.Extension -in '.aux', '.log', '.out', '.toc' } |
    Move-Item -Destination $build -Force
Move-Item $pdf (Join-Path $build 'ACTS-MCDT.pdf') -Force

$final = Join-Path $build 'ACTS-MCDT.pdf'
$size = [math]::Round((Get-Item $final).Length / 1MB, 1)
Write-Host "wrote $final ($size MB)"

# Surface any remaining LaTeX problems instead of hiding them.
$log = Join-Path $build 'ACTS-MCDT.log'
if (Test-Path $log) {
    $bad = Select-String -Path $log -Pattern 'multiply defined|Reference .* undefined|Missing character' -Encoding UTF8
    if ($bad) {
        Write-Warning ("LaTeX reported $($bad.Count) unresolved issue(s):")
        $bad | Select-Object -First 10 | ForEach-Object { Write-Warning $_.Line }
    } else {
        Write-Host 'LaTeX log clean: no duplicate labels, undefined refs, or missing glyphs.'
    }
}
