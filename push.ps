# ------------------------------------------------------------------
# push.ps1 — อัปโหลดแดชบอร์ดขึ้น GitHub: DohomePublic/SharePoint-Ac (Windows)
# เปิด PowerShell ในโฟลเดอร์ที่แตกไฟล์ไว้ แล้วรัน:  .\push.ps1
# ------------------------------------------------------------------
param([string]$Branch = "feature/po-approval-dashboard")
$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/DohomePublic/SharePoint-Ac.git"
$Src  = $PSScriptRoot
$Work = Join-Path $env:TEMP ("sp-ac-" + [guid]::NewGuid().ToString("N").Substring(0,8))

Write-Host "1/6 clone repo ..." -ForegroundColor Cyan
git clone $RepoUrl "$Work\repo"
Set-Location "$Work\repo"

Write-Host "2/6 ตรวจสอบระบบเดิมใน repo" -ForegroundColor Cyan
git branch -a
Get-ChildItem | Select-Object -ExpandProperty Name
$conflict = $false
foreach ($p in @("dashboard","scripts\build-snapshot.mjs",
                 ".github\workflows\dashboard-build-deploy.yml",
                 ".github\workflows\dashboard-upload-sharepoint.yml")) {
  if (Test-Path $p) { Write-Host "  พบไฟล์เดิมซ้ำ: $p" -ForegroundColor Yellow; $conflict = $true }
}
if ($conflict -and -not $env:FORCE) { throw "หยุด: มีไฟล์เดิมชื่อซ้ำ ตรวจสอบก่อน หรือตั้ง `$env:FORCE=1" }

Write-Host "3/6 คัดลอกไฟล์ ..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path dashboard,scripts,".github\workflows" | Out-Null
Copy-Item "$Src\dashboard\index.html"        dashboard\ -Force
Copy-Item "$Src\dashboard\data.json"         dashboard\ -Force
Copy-Item "$Src\dashboard\template.html"     dashboard\ -Force
Copy-Item "$Src\dashboard\build-report.json" dashboard\ -Force
Copy-Item "$Src\dashboard\README.md"         dashboard\ -Force
Copy-Item "$Src\scripts\build-snapshot.mjs"    scripts\ -Force
Copy-Item "$Src\scripts\rebuild-from-data.mjs" scripts\ -Force
Copy-Item "$Src\START-HERE.md","$Src\DEPLOY-GUIDE.md","$Src\PUSH-INSTRUCTIONS.md" . -Force
Copy-Item "$Src\.github\workflows\dashboard-build-deploy.yml"      ".github\workflows\" -Force
Copy-Item "$Src\.github\workflows\dashboard-upload-sharepoint.yml" ".github\workflows\" -Force

Write-Host "4/6 ตรวจสอบไฟล์ที่ build ไว้ ..." -ForegroundColor Cyan
$h = Get-Content dashboard\index.html -Raw
if ($h.IndexOf('id="snap"') -lt 0) { throw "ไม่พบบล็อกข้อมูล #snap" }
if ($h.IndexOf('id="snap"') -gt $h.IndexOf('function loadSnapshot')) { throw "บล็อกข้อมูลอยู่หลังสคริปต์หลัก" }
Write-Host ("  OK: {0:N2} MB" -f ($h.Length/1MB))

Write-Host "5/6 commit ..." -ForegroundColor Cyan
git checkout -b $Branch 2>$null; if ($LASTEXITCODE -ne 0) { git checkout $Branch }
git add dashboard scripts/build-snapshot.mjs scripts/rebuild-from-data.mjs .github/workflows/dashboard-build-deploy.yml .github/workflows/dashboard-upload-sharepoint.yml START-HERE.md DEPLOY-GUIDE.md PUSH-INSTRUCTIONS.md
git status --short
git commit -m "feat(dashboard): PO approval dashboard + build/deploy workflows"

Write-Host "6/6 push ..." -ForegroundColor Cyan
git push -u origin $Branch

Write-Host "`nเสร็จสิ้น เปิด Pull Request ที่:" -ForegroundColor Green
Write-Host "https://github.com/DohomePublic/SharePoint-Ac/compare/$Branch`?expand=1"
