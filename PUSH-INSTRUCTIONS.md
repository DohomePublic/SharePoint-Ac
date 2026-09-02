# วิธีอัปขึ้น GitHub (DohomePublic/SharePoint-Ac)

สภาพแวดล้อมที่ผมรันอยู่ **ออกอินเทอร์เน็ตไปยัง github.com ไม่ได้**
(DNS resolve ได้ = 20.205.243.166 แต่ HTTPS ถูกบล็อก คืนค่า `000` และไม่มี `git` ติดตั้ง)
จึง push ให้โดยตรงไม่ได้ — ไฟล์ทั้งหมดเตรียมพร้อม push แล้วในแพ็กเกจนี้

## ก่อนแตกไฟล์ — ตรวจสอบไม่ให้ทับของเดิม

```bash
git clone https://github.com/DohomePublic/SharePoint-Ac.git
cd SharePoint-Ac
git branch -a
ls -la
cat README.md 2>/dev/null | head -40
cat package.json 2>/dev/null
ls .github/workflows 2>/dev/null
```

ไฟล์ที่แพ็กเกจนี้จะเพิ่ม (ทั้งหมดเป็นพาธใหม่ ไม่ทับไฟล์เดิม):

```
dashboard/index.html
dashboard/template.html
dashboard/README.md
scripts/build-snapshot.mjs
.github/workflows/dashboard-build-deploy.yml
.github/workflows/dashboard-upload-sharepoint.yml
```

ถ้ามี `dashboard/` หรือชื่อ workflow ซ้ำอยู่แล้ว **หยุดก่อน** แล้วแจ้งผม
จะปรับพาธ/ชื่อไฟล์ให้ใหม่ก่อน merge

## ขั้นตอน push

```bash
# 1) แตกไฟล์แพ็กเกจลงใน repo ที่ clone มา
unzip -o SharePoint-Ac-dashboard.zip -d .

# 2) แยก branch ไว้ก่อน (แนะนำ ไม่ push ตรงเข้า main)
git checkout -b feature/po-approval-dashboard

# 3) ตรวจว่ามีเฉพาะไฟล์ที่เพิ่มใหม่จริง
git status --short

# 4) commit + push
git add dashboard scripts .github/workflows/dashboard-*.yml
git commit -m "feat(dashboard): PO approval dashboard + build/deploy workflows"
git push -u origin feature/po-approval-dashboard
```

แล้วเปิด Pull Request เข้า `main`

> ⚠️ `dashboard/index.html` มีขนาด ~1.74 MB (ต่ำกว่าลิมิต 100 MB ของ GitHub มาก)
> ถ้าไม่ต้องการเก็บ snapshot ใน git ให้ลบ `dashboard/index.html` แล้วให้ workflow
> build ขึ้นมาเองทุกครั้ง (แต่ GitHub Pages จะต้องรอ workflow รันรอบแรกก่อน)

## ตั้งค่าหลัง merge

1. **Settings → Pages** → Source = **GitHub Actions**
2. **Settings → Secrets and variables → Actions** → เพิ่ม
   `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`
3. **Settings → Actions → General → Workflow permissions** → **Read and write permissions**
   (workflow ต้อง commit ไฟล์ `index.html` ที่ build ใหม่)
4. ทดสอบ: **Actions → Dashboard - Build & Deploy → Run workflow**

## ถ้ายังไม่มี App Registration (ข้ามการดึงข้อมูลอัตโนมัติ)

รัน workflow ด้วย `skip_refresh = true` — ระบบจะ deploy `index.html`
ที่ build ไว้แล้ว (snapshot 5,760 รายการ) โดยไม่ต้องใช้ Azure secrets

หรือ build เองจากไฟล์ CSV ที่ export จาก List:

```bash
node scripts/build-snapshot.mjs --from-csv ./export.csv
```

## ทางเลือกถ้าไม่อยากใช้ GitHub Pages

อัปโหลด `dashboard/index.html` ไปที่
`https://dohomegroup.sharepoint.com/sites/AC-Accounting/SiteAssets/`
แล้วเปิดจาก URL นั้น — แดชบอร์ดจะสลับเป็นโหมด **LIVE** ดึงข้อมูลสดเอง
และสิทธิ์การเข้าถึงจะเป็นไปตาม permission ของ List เดิม
(workflow `dashboard-upload-sharepoint.yml` ทำขั้นตอนนี้ให้อัตโนมัติ)
