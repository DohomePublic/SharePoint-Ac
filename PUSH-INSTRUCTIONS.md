# วิธีนำเข้า GitHub — `DohomePublic/SharePoint-Ac`

มี 3 วิธี เลือกวิธีเดียวก็พอ

| วิธี | เหมาะกับ | ต้องติดตั้งอะไร | เวลา |
|---|---|---|---|
| **A. หน้าเว็บ GitHub** | ไม่อยากติดตั้งโปรแกรม ทำครั้งเดียว | ไม่ต้อง | ~10 นาที |
| **B. GitHub Desktop** | ใช้งานประจำ อยากเห็นภาพ | GitHub Desktop | ~15 นาที |
| **C. คำสั่ง git** | มี git อยู่แล้ว เร็วสุด | git | ~3 นาที |

> ⚠️ **อ่านก่อนเริ่มทุกวิธี** — repo นี้เป็น **public** ถ้าอัป `dashboard/index.html`
> และ `dashboard/data.json` ขึ้นไป ข้อมูลคำขอ PO 5,760 รายการ (ชื่อผู้ขอ อีเมล แผนก สาขา)
> จะเปิดให้คนทั้งโลกเห็น หากไม่ต้องการ ให้เปลี่ยน repo เป็น **private** ก่อน
> (Settings → General → เลื่อนล่างสุด → Change repository visibility)
> หรือข้ามไม่อัป 2 ไฟล์นั้น แล้วให้ workflow build เอง

---

## ขั้นที่ 0 — ตรวจของเดิมก่อน (ทำทุกวิธี)

เปิด `https://github.com/DohomePublic/SharePoint-Ac` แล้วดูว่า **มีโฟลเดอร์/ไฟล์ชื่อซ้ำหรือไม่**

- มีโฟลเดอร์ `dashboard/` อยู่แล้วหรือเปล่า
- มีโฟลเดอร์ `scripts/` อยู่แล้วหรือเปล่า
- มี `.github/workflows/` และมีไฟล์ชื่อ `dashboard-*.yml` หรือเปล่า
- มี `package.json` หรือเปล่า (ถ้ามี ดูว่า `"type"` เป็นอะไร)

**ถ้าไม่มีชื่อซ้ำเลย** → ปลอดภัย ทำต่อได้ทันที
**ถ้ามีชื่อซ้ำ** → หยุดก่อน แจ้งผมพร้อมภาพหน้าจอ จะเปลี่ยนพาธให้ใหม่ก่อนรวมไฟล์

ไฟล์ทั้งหมดที่แพ็กเกจนี้จะเพิ่ม (เป็นพาธใหม่ทั้งหมด ไม่ทับของเดิม):

```
START-HERE.md
DEPLOY-GUIDE.md
PUSH-INSTRUCTIONS.md
push.sh
push.ps1
.gitignore.dashboard
dashboard/index.html
dashboard/data.json
dashboard/template.html
dashboard/build-report.json
dashboard/README.md
scripts/build-snapshot.mjs
scripts/rebuild-from-data.mjs
.github/workflows/dashboard-build-deploy.yml
.github/workflows/dashboard-upload-sharepoint.yml
```

---

# วิธี A — อัปผ่านหน้าเว็บ GitHub (ไม่ต้องติดตั้งอะไร)

### A1. แตกไฟล์ zip

แตก `SharePoint-Ac-dashboard.zip` ลงเดสก์ท็อป จะได้โฟลเดอร์ที่มี `dashboard`, `scripts`,
`.github` และไฟล์ `.md` ต่าง ๆ

> 💡 **Windows ซ่อนโฟลเดอร์ `.github`** — ถ้ามองไม่เห็น ให้เปิด File Explorer →
> แท็บ **View** → ติ๊ก **Hidden items**

### A2. อัปโฟลเดอร์ `dashboard` และ `scripts` (ลากวางได้)

1. เปิด `https://github.com/DohomePublic/SharePoint-Ac`
2. กดปุ่ม **Add file** (มุมขวาบน) → **Upload files**
3. **ลากโฟลเดอร์ `dashboard` ทั้งโฟลเดอร์** จาก File Explorer มาวางในกรอบ
   (GitHub จะเก็บโครงสร้างโฟลเดอร์ให้เอง)
4. ลากโฟลเดอร์ `scripts` มาวางเพิ่ม
5. ลากไฟล์ `START-HERE.md`, `DEPLOY-GUIDE.md`, `PUSH-INSTRUCTIONS.md`,
   `push.sh`, `push.ps1` มาวางเพิ่ม
6. เลื่อนลงล่าง ช่อง **Commit changes**:
   - บรรทัดบน: `feat(dashboard): PO approval dashboard + กราฟสรุป`
   - เลือก **Commit directly to the main branch**
7. กด **Commit changes** สีเขียว → รอสักครู่ (ไฟล์รวม ~3.5 MB)

> ⏳ ถ้าอัปแล้วค้างนาน ลองอัปทีละโฟลเดอร์ เพราะ `index.html` + `data.json`
> รวมกันประมาณ 3.4 MB

### A3. สร้าง workflow — **ลากวางไม่ได้ ต้องพิมพ์พาธเอง**

โฟลเดอร์ที่ขึ้นต้นด้วยจุด (`.github`) ลากวางบนเว็บ GitHub **ไม่ได้**
ต้องสร้างไฟล์ใหม่แล้วพิมพ์พาธเอง ทำ 2 รอบ (ไฟล์ละรอบ)

**รอบที่ 1:**

1. กลับหน้าแรกของ repo → **Add file** → **Create new file**
2. ในช่องชื่อไฟล์ พิมพ์ทีละตัวอักษร:
   ```
   .github/workflows/dashboard-build-deploy.yml
   ```
   > พอพิมพ์ `/` ตัวแรก GitHub จะสร้างโฟลเดอร์ `.github` ให้เอง
   > แล้วพิมพ์ `workflows/` ต่อ จะเห็นแถบโฟลเดอร์ขึ้นด้านบนเรื่อย ๆ
3. เปิดไฟล์ `.github/workflows/dashboard-build-deploy.yml` บนเครื่อง
   ด้วย **Notepad** หรือ **VS Code** → กด `Ctrl+A` แล้ว `Ctrl+C`
4. คลิกในกรอบเขียนโค้ดของ GitHub → `Ctrl+V`
5. เลื่อนลงล่าง → **Commit changes**

**รอบที่ 2:** ทำซ้ำข้อ 1–5 แต่ใช้ชื่อ

```
.github/workflows/dashboard-upload-sharepoint.yml
```

> ❗ **อย่าเปิดไฟล์ .yml ด้วย Word หรือ WordPad** เพราะจะแทรกอักขระพิเศษทำให้ YAML พัง
> ใช้ Notepad หรือ VS Code เท่านั้น

### A4. ตรวจผล

กลับหน้าแรก repo ต้องเห็นครบ: `dashboard/`, `scripts/`, `.github/`
และแท็บ **Actions** ต้องมี workflow ชื่อ **Dashboard - ดึงข้อมูล & Deploy** ขึ้นมา

ข้ามไปทำ **ขั้นตอนหลังอัปเสร็จ** ด้านล่าง

---

# วิธี B — GitHub Desktop

1. ดาวน์โหลดติดตั้ง `https://desktop.github.com` → Sign in ด้วยบัญชี GitHub
2. **File → Clone repository → URL** ใส่
   `https://github.com/DohomePublic/SharePoint-Ac` เลือกที่เก็บบนเครื่อง → **Clone**
3. เปิดโฟลเดอร์ที่ clone มา (ปุ่ม **Show in Explorer** ใน GitHub Desktop)
4. **คัดลอกทุกอย่างจาก zip** ไปวางทับในโฟลเดอร์นั้น (รวมโฟลเดอร์ `.github` ที่ซ่อนอยู่)
5. กลับมาที่ GitHub Desktop จะเห็นรายการไฟล์ใหม่ทางซ้าย — **ตรวจว่าไม่มีไฟล์เดิมถูกแก้**
   (ไฟล์ที่เพิ่มใหม่จะขึ้นสีเขียวมีเครื่องหมาย `+`)
6. ช่อง **Summary** ล่างซ้าย พิมพ์
   `feat(dashboard): PO approval dashboard + กราฟสรุป`
7. กด **Commit to main** → แล้วกด **Push origin** ด้านบน

---

# วิธี C — คำสั่ง git (เร็วที่สุด)

### C1. อัตโนมัติด้วยสคริปต์ที่แถมมา

ในแพ็กเกจมีสคริปต์ที่ทำให้ครบทุกขั้นตอน พร้อมตรวจสอบไม่ให้ทับไฟล์เดิม

**Windows (PowerShell):**
```powershell
cd C:\path\to\SharePoint-Ac-dashboard
.\push.ps1
```

**macOS / Linux:**
```bash
cd ~/SharePoint-Ac-dashboard
chmod +x push.sh
./push.sh
```

### C2. ทำเองทีละขั้น

```bash
# 1) clone repo เดิมลงมา
git clone https://github.com/DohomePublic/SharePoint-Ac.git
cd SharePoint-Ac

# 2) ดูของเดิมก่อน
git branch -a
ls -la
ls .github/workflows 2>/dev/null

# 3) แตกไฟล์แพ็กเกจทับลงไป
unzip -o ../SharePoint-Ac-dashboard.zip -d .

# 4) แยก branch ไว้ก่อน (แนะนำ ปลอดภัยกว่า push ตรงเข้า main)
git checkout -b feature/po-approval-dashboard

# 5) ตรวจว่ามีเฉพาะไฟล์ใหม่จริง — ต้องไม่มีบรรทัดขึ้นต้นด้วย M (modified)
git status --short

# 6) commit + push
git add dashboard scripts .github/workflows/dashboard-*.yml \
        START-HERE.md DEPLOY-GUIDE.md PUSH-INSTRUCTIONS.md push.sh push.ps1
git commit -m "feat(dashboard): PO approval dashboard + กราฟสรุป + CI/CD"
git push -u origin feature/po-approval-dashboard
```

จากนั้นเปิด Pull Request เข้า `main` แล้ว merge

> 🔑 ถ้า push แล้วถามรหัสผ่าน — GitHub ไม่รับรหัสผ่านบัญชีแล้ว
> ต้องใช้ **Personal Access Token**: GitHub → รูปโปรไฟล์ → Settings →
> Developer settings → Personal access tokens → **Tokens (classic)** →
> Generate new token → ติ๊ก **repo** และ **workflow** → Generate →
> คัดลอก token มาใส่แทนรหัสผ่าน
>
> ❗ ต้องติ๊ก **workflow** ด้วย ไม่งั้นจะ push ไฟล์ใน `.github/workflows/` ไม่ได้
> (ขึ้น error `refusing to allow a Personal Access Token to create or update workflow`)

---

# ขั้นตอนหลังอัปเสร็จ (ทำทุกวิธี)

### 1. เปิดสิทธิ์ให้ workflow เขียนไฟล์กลับได้

**Settings → Actions → General** → เลื่อนลงหัวข้อ **Workflow permissions**
→ เลือก **Read and write permissions** → **Save**

> ถ้าไม่ทำขั้นนี้ workflow จะรันได้แต่ commit ข้อมูลใหม่กลับเข้า repo ไม่ได้

### 2. ใส่ Secrets สำหรับดึงข้อมูลจาก SharePoint

**Settings → Secrets and variables → Actions → New repository secret**
เพิ่มทีละตัว รวม 3 ตัว:

| ชื่อ Secret | ค่าที่ใส่ |
|---|---|
| `AZURE_TENANT_ID` | Directory (tenant) ID ของ DOHOME |
| `AZURE_CLIENT_ID` | Application (client) ID ของ App Registration |
| `AZURE_CLIENT_SECRET` | Client secret value (ไม่ใช่ Secret ID) |

ยังไม่มี App Registration? ขอจากทีม IT/Azure Admin โดยระบุว่าต้องการ:
- Microsoft Graph สิทธิ์แบบ **Application**: `Sites.Selected`
- **Grant admin consent** ให้เรียบร้อย
- ให้สิทธิ์ระดับไซต์เฉพาะ `/sites/AC-Accounting` แบบ `write`
  (`PATCH https://graph.microsoft.com/v1.0/sites/{site-id}/permissions`)

> ยังไม่พร้อมก็ใช้งานได้ — workflow จะขึ้น warning แล้ว build จากข้อมูลเดิมแทน ไม่พัง

### 3. เปิด GitHub Pages (ถ้าต้องการลิงก์เปิดจากที่ไหนก็ได้)

**Settings → Pages → Build and deployment → Source** = **GitHub Actions**

จะได้ลิงก์ `https://dohomepublic.github.io/SharePoint-Ac/`

> ⚠️ ข้ามขั้นนี้ได้ถ้าจะใช้บน SharePoint อย่างเดียว (ปลอดภัยกว่า)

### 4. ทดสอบรัน

แท็บ **Actions** → เลือก **Dashboard - ดึงข้อมูล & Deploy** ทางซ้าย
→ ปุ่ม **Run workflow** ทางขวา → **Run workflow** สีเขียว

รอ 1–3 นาที ถ้าขึ้น ✅ สีเขียว ให้กดเข้าไปดู **Summary** จะเห็นตารางสรุปแบบนี้:

| รายการ | ค่า |
|---|---|
| จำนวนรายการ | 5,760 |
| รายการใหม่สุด | 2026-09-01 11:15 น. (เวลาไทย) · เลขที่คำขอ 6108 |
| แยกตามสถานะ | ดำเนินการเรียบร้อย 4,883 · รอดำเนินการ 631 · ยกเลิก 234 |

---

# ตารางแก้ปัญหา

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| ไม่เห็นโฟลเดอร์ `.github` ในเครื่อง | Windows ซ่อนโฟลเดอร์ที่ขึ้นต้นด้วยจุด → File Explorer → View → ติ๊ก Hidden items |
| ลากโฟลเดอร์ `.github` ขึ้นเว็บไม่ได้ | เป็นข้อจำกัดของ GitHub → ใช้ **Add file → Create new file** แล้วพิมพ์พาธเอง (วิธี A3) |
| `refusing to allow a Personal Access Token to create or update workflow` | Token ไม่ได้ติ๊กสิทธิ์ **workflow** → สร้าง token ใหม่ติ๊กทั้ง `repo` และ `workflow` |
| อัปแล้วไม่เห็นแท็บ Actions มี workflow | ไฟล์ `.yml` อาจอยู่ผิดพาธ ต้องเป็น `.github/workflows/` เป๊ะ (มีจุดนำหน้า, workflows มี s) |
| Workflow รันแล้วขึ้นแดงทันที | YAML พังเพราะ copy ผ่าน Word → เปิดไฟล์ใหม่ด้วย Notepad แล้ว copy ใหม่ |
| Workflow commit ไม่ได้ `Permission denied` | ยังไม่ได้ตั้ง Workflow permissions = Read and write (ขั้นตอนที่ 1) |
| Workflow ขึ้น warning เรื่อง secrets | ยังไม่ได้ใส่ `AZURE_*` — ไม่เป็นไร ระบบจะ build จากข้อมูลเดิมให้ |
| อัปไฟล์ไม่ขึ้น ค้างนาน | ไฟล์รวม ~3.5 MB → อัปทีละโฟลเดอร์ หรือใช้วิธี B/C |
| ไฟล์ใหญ่เกิน | GitHub จำกัด 25 MB ต่อไฟล์ผ่านเว็บ / 100 MB ผ่าน git — ไฟล์เราใหญ่สุด 1.77 MB ผ่านสบาย |

---

# ถ้าไม่อยากอัปขึ้น GitHub เลย

ใช้ `dashboard/index.html` ไฟล์เดียวได้เลย:

- **เปิดบนเครื่อง**: ดับเบิลคลิก → ใช้ได้ทันที (โหมด SNAPSHOT)
- **ให้ทีมใช้ + ข้อมูลสด**: อัปขึ้น
  `https://dohomegroup.sharepoint.com/sites/AC-Accounting/SiteAssets/`
  เปลี่ยนชื่อเป็น `po-approval-dashboard.html` แล้วเปิดจาก URL นั้น → ได้โหมด **LIVE**
  ดึงข้อมูลสดเอง และสิทธิ์เข้าถึงเป็นไปตาม permission ของ List เดิม

รายละเอียดอยู่ใน `DEPLOY-GUIDE.md`
