# Starts Huso on Windows (PowerShell). The first time it also creates .env with a fresh secret key.
Set-Location $PSScriptRoot
if (-not (Test-Path .env)) {
  Copy-Item env.example .env
  $bytes = New-Object byte[] 32
  [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
  $key = "base64:" + [Convert]::ToBase64String($bytes)
  (Get-Content .env) -replace '^APP_KEY=.*', "APP_KEY=$key" | Set-Content .env
  Write-Host "Created .env with a new APP_KEY."
}
New-Item -ItemType Directory -Force storage | Out-Null
& .\huso.exe serve
