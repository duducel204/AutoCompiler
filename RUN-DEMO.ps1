$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "AutoCompiler - prova rapida" -ForegroundColor Cyan
python .\demo.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host ""
Write-Host "Arquivo de prova:" -ForegroundColor Green
Get-Content .\.autocompiler\DEMO_OK.txt
