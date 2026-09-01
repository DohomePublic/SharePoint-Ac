# วิธีนำเข้า GitHub — DohomePublic/SharePoint-Ac

ไฟล์ที่ต้องอัปโหลด (4 ไฟล์ อยู่ในโฟลเดอร์ `SharePoint-Ac` ที่ได้รับมา)

```
index.html          ← ตัวแดชบอร์ด (live-only build, 36 KB, ไม่มีข้อมูลจริงฝังอยู่)
docs/index.html     ← สำเนาสำหรับ GitHub Pages
README.md           ← คู่มือโครงการ
.gitignore          ← กันไฟล์ที่มีข้อมูลจริงหลุดขึ้น repo
```

> ⚠️ **ห้ามอัปโหลด** `PO_Approval_Dashboard.html` (ไฟล์ 5.2 MB) ขึ้น repo นี้เด็ดขาด
> เพราะฝังข้อมูลพนักงาน/PR/PO จริง 5,757 รายการ และ repo นี้เป็น **Public**
> ไฟล์นั้นให้ใช้ภายในหรือวางบน SharePoint เท่านั้น

---

## วิธีที่ 1 — อัปโหลดผ่านหน้าเว็บ GitHub (ง่ายสุด ไม่ต้องติดตั้งอะไร)

1. เปิด https://github.com/DohomePublic/SharePoint-Ac
2. ถ้า repo ยังว่าง กด **uploading an existing file**
   ถ้ามีไฟล์อยู่แล้ว กด **Add file → Upload files**
3. ลาก `index.html` และ `README.md` เข้าไปวาง
4. ช่อง commit message พิมพ์: `PO Approval Dashboard (live-only, no data embedded)`
   เลือก **Commit directly to the main branch** → กด **Commit changes**
5. อัปโหลดโฟลเดอร์ `docs`: กด **Add file → Upload files** อีกครั้ง แล้วลาก
   **ทั้งโฟลเดอร์ `docs`** เข้าไป (GitHub จะสร้างโฟลเดอร์ให้เอง) → Commit changes
6. เพิ่ม `.gitignore`: กด **Add file → Create new file** ตั้งชื่อไฟล์ว่า `.gitignore`
   แล้ววางเนื้อหานี้ลงไป → Commit changes

```
PO_Approval_Dashboard.html
*snapshot*.html
*.csv
*.xls
*.xlsx
sharepoint_list_*.csv
.DS_Store
```

> เบราว์เซอร์บางตัวซ่อนไฟล์ที่ขึ้นต้นด้วยจุด ทำให้ลาก `.gitignore` ไม่ได้ — ใช้วิธี Create new file ตามข้อ 6

---

## วิธีที่ 2 — ใช้ Git command line

```bash
# 1) โคลน repo
git clone https://github.com/DohomePublic/SharePoint-Ac.git
cd SharePoint-Ac

# 2) คัดลอกไฟล์ทั้งหมดจากโฟลเดอร์ที่ได้รับมาลงในนี้ (รวมโฟลเดอร์ docs และ .gitignore)
#    Windows PowerShell:  Copy-Item -Recurse -Force ..\SharePoint-Ac\* .
#    macOS / Linux:       cp -r ../SharePoint-Ac/. .

# 3) ตรวจก่อน commit ว่าไม่มีไฟล์ข้อมูลจริงติดไปด้วย
git status
grep -c '"pr":"11' index.html || echo "OK: ไม่มีข้อมูลฝังในไฟล์"

# 4) commit และ push
git add index.html docs/index.html README.md DEPLOY-GITHUB.md .gitignore
git commit -m "PO Approval Dashboard (live-only, no data embedded)"
git branch -M main
git push origin main
```

ถ้า push แล้วถูกถาม username/password ให้ใช้ **Personal Access Token** แทนรหัสผ่าน
(GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens →
เลือก repo `SharePoint-Ac` → สิทธิ์ `Contents: Read and write`)

---

## วิธีที่ 3 — GitHub Desktop

1. ติดตั้ง GitHub Desktop แล้วล็อกอิน
2. **File → Clone repository → URL** วาง `https://github.com/DohomePublic/SharePoint-Ac`
3. เปิดโฟลเดอร์ที่โคลนมา แล้วก๊อปไฟล์ทั้ง 4 (รวมโฟลเดอร์ `docs`) วางลงไป
4. กลับมาที่ GitHub Desktop → ใส่ Summary → **Commit to main** → **Push origin**

---

## เปิด GitHub Pages (หน้าตัวอย่าง ไม่มีข้อมูล)

1. ไปที่ repo → **Settings** → เมนูซ้าย **Pages**
2. Source: `Deploy from a branch`
3. Branch: `main` · Folder: **`/docs`** → **Save**
4. รอ 1–2 นาที จะได้ URL: `https://dohomepublic.github.io/SharePoint-Ac/`

หน้านี้จะขึ้นสถานะ 🟡 **Snapshot 0 รายการ** พร้อมหน้าจอวิธีติดตั้ง — เป็นพฤติกรรมที่ถูกต้อง
เพราะ SharePoint ไม่อนุญาต CORS ให้โดเมน `github.io` และเบราว์เซอร์ไม่ส่ง cookie ข้ามไซต์
**GitHub Pages ใช้ดูดีไซน์และรีวิวโค้ดเท่านั้น ไม่ใช่ที่ใช้งานจริง**

---

## ใช้งานจริง — ต้องวางบน SharePoint

1. ดาวน์โหลด `index.html` จาก repo (ปุ่ม **Download raw file**)
2. อัปโหลดขึ้นไลบรารี **Site Assets** ของ
   https://dohomegroup.sharepoint.com/sites/AC-Accounting
3. เปิดด้วย URL นี้
   `https://dohomegroup.sharepoint.com/sites/AC-Accounting/SiteAssets/index.html`
4. หน้าเว็บจะขึ้น 🟢 **Live** และซิงก์ข้อมูลใหม่อัตโนมัติทุก 5 นาที (ปรับรอบได้มุมขวาบน)

ทางเลือกอื่น: ฝังด้วย Web Part **Embed** ในหน้า SharePoint, วางบน Web Server ภายในที่ใช้ SSO เดียวกัน,
หรือแพ็กเป็น SPFx web part

---

## รอบการอัปเดตในอนาคต

แก้โค้ดใน repo → `git pull` / แก้ผ่านเว็บ → แล้วอัปโหลด `index.html` ตัวใหม่ทับใน Site Assets
(ผู้ใช้กด Ctrl+F5 หนึ่งครั้งเพื่อล้างแคชเบราว์เซอร์)
