#!/usr/bin/env bash
# ------------------------------------------------------------------
# push.sh — อัปโหลดแดชบอร์ดขึ้น GitHub: DohomePublic/SharePoint-Ac
# รันบนเครื่องที่ล็อกอิน GitHub แล้ว (มี git + สิทธิ์ push)
#
#   bash push.sh                     -> สร้าง branch feature/po-approval-dashboard
#   bash push.sh main                -> push เข้า main โดยตรง (ไม่แนะนำ)
# ------------------------------------------------------------------
set -euo pipefail

REPO_URL="https://github.com/DohomePublic/SharePoint-Ac.git"
BRANCH="${1:-feature/po-approval-dashboard}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="$(mktemp -d)"

echo "▶ 1/6 clone repo …"
git clone "$REPO_URL" "$WORK/repo"
cd "$WORK/repo"

echo "▶ 2/6 ตรวจสอบระบบเดิมใน repo (ไม่ทับของเดิม)"
echo "  branches:"; git branch -a | sed 's/^/    /'
echo "  root files:"; ls -1 | sed 's/^/    /'
[ -f package.json ] && { echo "  package.json:"; sed -n '1,25p' package.json | sed 's/^/    /'; }
CONFLICT=0
for p in dashboard scripts/build-snapshot.mjs \
         .github/workflows/dashboard-build-deploy.yml \
         .github/workflows/dashboard-upload-sharepoint.yml; do
  if [ -e "$p" ]; then echo "  ⚠ พบไฟล์/โฟลเดอร์เดิมซ้ำ: $p"; CONFLICT=1; fi
done
if [ "$CONFLICT" = "1" ]; then
  echo
  echo "✖ หยุด: มีไฟล์เดิมชื่อซ้ำ อาจถูกเขียนทับ"
  echo "  ตรวจสอบก่อน หรือรันใหม่ด้วย FORCE=1 bash push.sh"
  [ "${FORCE:-0}" != "1" ] && exit 1
  echo "  FORCE=1 → ดำเนินการต่อ"
fi

echo "▶ 3/6 คัดลอกไฟล์แดชบอร์ด …"
mkdir -p dashboard scripts .github/workflows
cp "$SRC/dashboard/index.html"        dashboard/
cp "$SRC/dashboard/data.json"         dashboard/
cp "$SRC/dashboard/template.html"     dashboard/
cp "$SRC/dashboard/build-report.json" dashboard/
cp "$SRC/dashboard/README.md"         dashboard/
cp "$SRC/scripts/build-snapshot.mjs"     scripts/
cp "$SRC/scripts/rebuild-from-data.mjs"  scripts/
cp "$SRC/START-HERE.md" "$SRC/DEPLOY-GUIDE.md" "$SRC/PUSH-INSTRUCTIONS.md" .
cp "$SRC/.github/workflows/dashboard-build-deploy.yml"      .github/workflows/
cp "$SRC/.github/workflows/dashboard-upload-sharepoint.yml" .github/workflows/

echo "▶ 4/6 ตรวจสอบไฟล์ที่ build ไว้ …"
node -e "
  const fs=require('fs');
  const h=fs.readFileSync('dashboard/index.html','utf8');
  const iData=h.indexOf('id=\"snap\"'), iUse=h.indexOf('function loadSnapshot');
  if(iData<0)      throw new Error('ไม่พบบล็อกข้อมูล #snap');
  if(iData>iUse)   throw new Error('บล็อกข้อมูลอยู่หลังสคริปต์หลัก');
  const j=JSON.parse(h.match(/id=\"snap\">([\s\S]*?)<\/script>/)[1]);
  if(!j.n) throw new Error('snapshot ว่าง');
  console.log('  OK: '+j.n.toLocaleString()+' รายการ, '+(h.length/1e6).toFixed(2)+' MB');
"

echo "▶ 5/6 commit …"
git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"
git add dashboard scripts/build-snapshot.mjs scripts/rebuild-from-data.mjs \
        .github/workflows/dashboard-*.yml \
        START-HERE.md DEPLOY-GUIDE.md PUSH-INSTRUCTIONS.md
git status --short | sed 's/^/    /'
git -c user.name="${GIT_NAME:-$(git config user.name || echo dohome-bi)}" \
    -c user.email="${GIT_EMAIL:-$(git config user.email || echo bi@dohome.co.th)}" \
    commit -m "feat(dashboard): PO approval dashboard + build/deploy workflows"

echo "▶ 6/6 push …"
git push -u origin "$BRANCH"

echo
echo "✔ เสร็จสิ้น — เปิด Pull Request ที่:"
echo "   https://github.com/DohomePublic/SharePoint-Ac/compare/$BRANCH?expand=1"
echo "workdir: $WORK/repo"
