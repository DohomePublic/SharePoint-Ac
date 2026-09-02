# คู่มือการนำแดชบอร์ดไปวาง (ฉบับละเอียด)

แดชบอร์ด: **PO Approval Dashboard**
แหล่งข้อมูล: SharePoint List `AC-Data Request for approval of PO`
`https://dohomegroup.sharepoint.com/sites/AC-Accounting/Lists/ACData%20Request%20for%20approval%20of%20PO/AllItems.aspx`

---

## สารบัญ

- [ส่วนที่ 0 — เตรียมไฟล์](#ส่วนที่-0--เตรียมไฟล์)
- [ส่วนที่ 1 — เลือกวิธีวาง](#ส่วนที่-1--เลือกวิธีวาง)
- [วิธี A — วางบน SharePoint SiteAssets (แนะนำที่สุด)](#วิธี-a--วางบน-sharepoint-siteassets-แนะนำที่สุด)
- [วิธี B — ฝังเป็นหน้าใน SharePoint ด้วย Embed web part](#วิธี-b--ฝังเป็นหน้าใน-sharepoint-ด้วย-embed-web-part)
- [วิธี C — วางบน GitHub Pages](#วิธี-c--วางบน-github-pages)
- [วิธี D — แชร์เป็นไฟล์เดี่ยว (ไม่ต้องติดตั้งอะไร)](#วิธี-d--แชร์เป็นไฟล์เดี่ยว-ไม่ต้องติดตั้งอะไร)
- [ส่วนที่ 2 — ตั้งค่าอัปเดตอัตโนมัติ (CI/CD)](#ส่วนที่-2--ตั้งค่าอัปเดตอัตโนมัติ-cicd)
- [ส่วนที่ 3 — ตรวจรับหลังวาง (Checklist)](#ส่วนที่-3--ตรวจรับหลังวาง-checklist)
- [ส่วนที่ 4 — แก้ปัญหาที่พบบ่อย](#ส่วนที่-4--แก้ปัญหาที่พบบ่อย)

---

## ส่วนที่ 0 — เตรียมไฟล์

แตกไฟล์ `SharePoint-Ac-dashboard.zip` (677 KB) จะได้โครงสร้างนี้

```
SharePoint-Ac-dashboard/
├── dashboard/
│   ├── index.html        1,744,570 B   ← ไฟล์แดชบอร์ดตัวจริง (ฝังข้อมูล 5,760 รายการ)
│   ├── data.json         1,701,471 B   ← ข้อมูลแยกไฟล์ สำหรับปุ่ม 🔄 รีเฟรช
│   ├── template.html        43,209 B   ← ต้นฉบับ (มี placeholder __SNAPSHOT_JSON__)
│   └── README.md             7,325 B
├── scripts/
│   └── build-snapshot.mjs    8,993 B   ← ตัว build ดึงข้อมูล → สร้าง index.html + data.json
├── .github/workflows/
│   ├── dashboard-build-deploy.yml       3,713 B
│   └── dashboard-upload-sharepoint.yml  2,685 B
├── push.sh / push.ps1                   ← สคริปต์ push อัตโนมัติ (ถ้าใช้ command line)
├── PUSH-INSTRUCTIONS.md
└── .gitignore.dashboard
```

> ไฟล์ `po-approval-dashboard.html` ที่ส่งแยกมา = ไฟล์เดียวกับ `dashboard/index.html`
> ใช้กับวิธี A / B / D ได้เลยโดยไม่ต้องแตะ GitHub

---

## ส่วนที่ 1 — เลือกวิธีวาง

| วิธี | เหมาะกับ | ข้อมูลเป็นความลับ? | ความยาก |
|---|---|---|---|
| **A. SharePoint SiteAssets** | ใช้งานจริงในองค์กร | ✅ ปลอดภัย ใช้ permission ของ List | ⭐ ง่าย |
| **B. Embed web part** | ทำเป็นหน้าในเว็บไซต์ทีม | ✅ ปลอดภัย | ⭐ ง่าย |
| **C. GitHub Pages** | เข้าถึงจากภายนอกองค์กร | ❌ **เปิดสาธารณะ** | ⭐⭐ ปานกลาง |
| **D. ไฟล์เดี่ยว** | ทดลอง/ส่งให้ดูชั่วคราว | ⚠️ ขึ้นกับผู้รับ | ⭐ ง่ายที่สุด |

> ⚠️ **ข้อมูลใน `index.html` มีชื่อผู้ขอ รหัสพนักงาน PR Number ผู้อนุมัติ และสาขา 5,760 รายการ**
> ถ้าเป็นข้อมูลภายใน ให้เลือก **วิธี A หรือ B** เท่านั้น

---

## วิธี A — วางบน SharePoint SiteAssets (แนะนำที่สุด)

ข้อดี: เมื่อเปิดจาก URL ของ SharePoint แดชบอร์ดจะสลับเป็น **โหมด LIVE ดึงข้อมูลสดเอง**
และสิทธิ์เข้าถึงเป็นไปตาม permission ของ List เดิม ไม่ต้องตั้งค่าอะไรเพิ่ม

### A.1 อัปโหลดไฟล์

1. เปิด `https://dohomegroup.sharepoint.com/sites/AC-Accounting`
2. เมนูซ้าย → **Site contents** (เนื้อหาไซต์)
3. เปิดคลัง **Site Assets** (ถ้าไม่เห็น ให้เข้า URL ตรง: `https://dohomegroup.sharepoint.com/sites/AC-Accounting/SiteAssets`)
4. กด **Upload → Files** แล้วเลือกไฟล์ `index.html`
5. **เปลี่ยนชื่อไฟล์** เป็น `po-approval-dashboard.html`
   (คลิกขวาที่ไฟล์ → **Rename**) เพื่อไม่ให้ชนกับไฟล์อื่น
6. (ตัวเลือก) อัป `data.json` ไว้ด้วย ถ้าอยากให้ปุ่มรีเฟรชมีแหล่งสำรองในไซต์เดียวกัน

### A.2 เปิดใช้งาน

URL ที่ได้:
```
https://dohomegroup.sharepoint.com/sites/AC-Accounting/SiteAssets/po-approval-dashboard.html
```

เปิดแล้วต้องเห็นป้ายบนหัวเว็บเป็น **`LIVE · SharePoint REST · N รายการ`**
ถ้าเห็น `SNAPSHOT` แสดงว่าดึงสดไม่ผ่าน → ดู[ส่วนที่ 4](#ส่วนที่-4--แก้ปัญหาที่พบบ่อย)

### A.3 ทำให้เข้าถึงง่าย

- **ปักหมุดเมนูซ้าย**: Site contents → **Edit** เมนูนำทาง → **+** → วาง URL ข้างบน → ตั้งชื่อ `แดชบอร์ดอนุมัติ PO`
- **สร้าง Shortcut ใน Teams**: แท็บในทีม → **+** → **Website** → วาง URL

### A.4 อัปเดตไฟล์ในอนาคต

อัปโหลดไฟล์ชื่อเดิมทับได้เลย SharePoint จะเก็บเวอร์ชันเดิมไว้ให้ (Version history)
หรือให้ workflow `dashboard-upload-sharepoint.yml` ทำอัตโนมัติ (ดูส่วนที่ 2)

---

## วิธี B — ฝังเป็นหน้าใน SharePoint ด้วย Embed web part

ทำ **หลังจาก** อัปไฟล์ตามวิธี A แล้ว

1. ไปที่ **Pages** ในไซต์ → **+ New → Site Page**
2. ตั้งชื่อหน้า เช่น `Dashboard อนุมัติ PO`
3. กด **+** ในพื้นที่เนื้อหา → เลือก web part **Embed**
4. เลือก **Website address** แล้ววาง:
   ```
   https://dohomegroup.sharepoint.com/sites/AC-Accounting/SiteAssets/po-approval-dashboard.html
   ```
5. ปรับ **ความสูง** ของ web part ให้สูงสุด (ลากขอบล่าง) เพื่อให้ตารางแสดงได้เต็ม
6. กด **Publish**

> ถ้า Embed ขึ้นข้อความว่าโดเมนไม่ได้รับอนุญาต ให้ผู้ดูแลไซต์เพิ่มโดเมน
> `dohomegroup.sharepoint.com` ใน **Site settings → HTML Field Security**

---

## วิธี C — วางบน GitHub Pages

### C.1 อัปไฟล์ขึ้น repo (ผ่านหน้าเว็บ)

1. เปิด `https://github.com/DohomePublic/SharePoint-Ac`
2. **ตรวจก่อน**: ต้องไม่มีโฟลเดอร์ `dashboard/`, ไฟล์ `scripts/build-snapshot.mjs`
   หรือ workflow ชื่อซ้ำอยู่เดิม ถ้ามีให้หยุดแล้วเปลี่ยนชื่อพาธก่อน
3. **Add file ▾ → Upload files** → ลากโฟลเดอร์ `dashboard` และ `scripts` เข้าไป
4. commit message: `feat(dashboard): PO approval dashboard`
5. เลือก **Create a new branch for this commit** → ตั้งชื่อ `feature/po-approval-dashboard` → **Propose changes**

### C.2 อัปไฟล์ workflow (โฟลเดอร์ `.github` ลากไม่ได้ ต้องพิมพ์พาธเอง)

1. สลับไป branch `feature/po-approval-dashboard`
2. **Add file ▾ → Create new file**
3. ช่องชื่อไฟล์พิมพ์: `.github/workflows/dashboard-build-deploy.yml`
   (พิมพ์ `/` แล้วระบบสร้างโฟลเดอร์ให้อัตโนมัติ)
4. เปิดไฟล์จริงด้วย Notepad → **Ctrl+A → Ctrl+C** → วางลงกล่องแก้ไข → **Commit changes**
5. ทำซ้ำกับ `.github/workflows/dashboard-upload-sharepoint.yml`
6. ไปแท็บ **Pull requests** → เปิด PR → ตรวจ **Files changed** ว่ามีแค่ไฟล์ใหม่ → **Merge**

### C.3 เปิด GitHub Pages

1. **Settings → Pages** → Source = **GitHub Actions**
2. **Settings → Actions → General → Workflow permissions** = **Read and write permissions**
3. **Actions → Dashboard - Build & Deploy → Run workflow**
   - ถ้ายังไม่มี Azure secrets: ติ๊ก **`skip_refresh` = true**
4. รอ workflow เขียว → เปิด `https://dohomepublic.github.io/SharePoint-Ac/`

---

## วิธี D — แชร์เป็นไฟล์เดี่ยว (ไม่ต้องติดตั้งอะไร)

`index.html` เป็นไฟล์เดียวจบ ไม่พึ่ง CDN ใด ๆ

- **ดับเบิลคลิกเปิดได้เลย** → ทำงานในโหมด SNAPSHOT (ข้อมูลที่ฝังมา 5,760 รายการ)
- ส่งทาง Teams / OneDrive / อีเมลได้ (1.74 MB)
- ถ้าเครื่องต่อเน็ตได้ กด **🔄 รีเฟรช** จะดึง `data.json` จาก GitHub ให้ข้อมูลใหม่กว่า
- วางบน File Server / IIS / Nginx ก็ได้ แค่ก๊อปไฟล์ไปวางในโฟลเดอร์เว็บ

---

## ส่วนที่ 2 — ตั้งค่าอัปเดตอัตโนมัติ (CI/CD)

### 2.1 สร้าง App Registration (ทำครั้งเดียว)

1. เปิด **Azure Portal → Microsoft Entra ID → App registrations → New registration**
2. Name: `SharePoint-Ac Dashboard Build` → Register
3. จดค่า **Application (client) ID** และ **Directory (tenant) ID**
4. **Certificates & secrets → New client secret** → จดค่า **Value** (เห็นครั้งเดียว)
5. **API permissions → Add a permission → Microsoft Graph → Application permissions**
   → เลือก **`Sites.Selected`** (แนะนำ จำกัดเฉพาะไซต์) หรือ `Sites.ReadWrite.All`
   → **Grant admin consent**
6. ถ้าใช้ `Sites.Selected` ให้ผู้ดูแลรันคำสั่งให้สิทธิ์เฉพาะไซต์ AC-Accounting เพิ่ม

### 2.2 ใส่ Secrets ใน GitHub

**Settings → Secrets and variables → Actions → New repository secret**

| ชื่อ Secret | ค่า |
|---|---|
| `AZURE_TENANT_ID` | Directory (tenant) ID |
| `AZURE_CLIENT_ID` | Application (client) ID |
| `AZURE_CLIENT_SECRET` | Client secret Value |

### 2.3 สิ่งที่ workflow ทำให้อัตโนมัติ

**`dashboard-build-deploy.yml`** — รันเมื่อ push แก้ template/script, **ทุกวัน 01:00 UTC (08:00 น. ไทย)**, หรือกดรันเอง
1. ดึงข้อมูลจาก SharePoint ผ่าน Graph (map Display Name → internal name ตอนรันไทม์)
2. สร้าง `dashboard/index.html` + `dashboard/data.json`
3. ตรวจสอบ: ต้องมีบล็อก `#snap`, ต้องอยู่ก่อนสคริปต์หลัก, `data.json` ต้องมี rows > 0
4. commit ถ้ามีการเปลี่ยนแปลง → deploy GitHub Pages

**`dashboard-upload-sharepoint.yml`** — ทำงานต่อเมื่อ build สำเร็จ
→ PUT ไฟล์ขึ้น `SiteAssets/po-approval-dashboard.html` ผ่าน Graph โดยอัตโนมัติ

### 2.4 อยาก build เองบนเครื่อง

```bash
# ดึงสดจาก SharePoint
AZURE_TENANT_ID=... AZURE_CLIENT_ID=... AZURE_CLIENT_SECRET=... \
  node scripts/build-snapshot.mjs

# หรือจากไฟล์ CSV ที่ export จาก List
node scripts/build-snapshot.mjs --from-csv ./export.csv
```
ต้องมี Node.js 18 ขึ้นไป

---

## ส่วนที่ 3 — ตรวจรับหลังวาง (Checklist)

เปิดแดชบอร์ดแล้วไล่เช็คตามนี้

- [ ] ป้ายบนหัวเว็บแสดงแหล่งข้อมูลและจำนวนรายการ (เช่น `LIVE · SharePoint REST · 5,760 รายการ`)
- [ ] ไม่มีแถบแดงแจ้ง error
- [ ] KPI 7 ใบมีตัวเลข และกดแล้วกรองข้อมูลได้
- [ ] กราฟ 3 ชุดขึ้น (สถานะ / Top 8 สาขา / คำขอต่อเดือน)
- [ ] ตารางมีข้อมูล และคลิกหัวคอลัมน์แล้วเรียงลำดับได้
- [ ] พิมพ์ `มหาชัย` ในช่องค้นหา → ต้องได้ผลลัพธ์
- [ ] เลือกตัวกรอง `Status = ยกเลิก` → ได้ **234 รายการ**
- [ ] กด **ดู** ที่แถวใดแถวหนึ่ง → เห็น timeline อนุมัติ 3 ขั้น และปุ่มเปิดใน SharePoint ใช้ได้
- [ ] กด **⬇ Export CSV** → เปิดใน Excel แล้วภาษาไทยไม่เพี้ยน
- [ ] กด **🔄 รีเฟรช** → ปุ่มเปลี่ยนเป็น `⏳ กำลังดึง…` แล้วขึ้น toast แจ้งผล
- [ ] เปิดบนมือถือ → ตารางเลื่อนแนวนอนได้ ตัวกรองเรียงเป็นแถวเดียว

ค่าอ้างอิงจากข้อมูลจริง ณ วันที่ build: รวม **5,760 รายการ** ·
ดำเนินการเรียบร้อย **4,883** · รอดำเนินการ **631** · ยกเลิก **234** · ไม่ระบุ **12** ·
แผนก **23** ค่า · สาขา **30** ค่า · ผู้อนุมัติสายงาน **68** คน ·
ช่วงข้อมูล **30/06/2025 – 01/09/2026**

---

## ส่วนที่ 4 — แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุ | วิธีแก้ |
|---|---|---|
| เปิดแล้วหน้าว่าง ไม่มีอะไรเลย | ไฟล์ไม่สมบูรณ์ / ดาวน์โหลดไม่ครบ | เช็คขนาดไฟล์ต้องได้ **1,744,570 B** ถ้าไม่ตรงให้ดาวน์โหลดใหม่ |
| ขึ้นแถบแดง `โหลดข้อมูลไม่สำเร็จทุกแหล่ง` | ทั้ง SharePoint, GitHub และ snapshot อ่านไม่ได้ | เปิด F12 → Console ดูข้อความ แล้วแจ้งข้อความนั้นมา |
| อยู่บน SharePoint แต่ขึ้น `SNAPSHOT` ไม่ใช่ `LIVE` | ผู้ใช้ไม่มีสิทธิ์อ่าน List หรือชื่อ List ถูกเปลี่ยน | ตรวจ permission ของ List และตรวจว่าชื่อยังเป็น `AC-Data Request for approval of PO` |
| กดรีเฟรชแล้วขึ้น `ดึงจาก GitHub ไม่สำเร็จ` | ยังไม่ได้อัป `data.json` ขึ้น GitHub หรือ branch ไม่ใช่ `main` | อัป `dashboard/data.json` ให้ครบ หรือแก้ค่า `GH` ในหัวสคริปต์ของ `template.html` |
| Export CSV แล้วภาษาไทยเพี้ยนใน Excel | เปิดผิดวิธี | ไฟล์มี UTF-8 BOM อยู่แล้ว — ดับเบิลคลิกเปิดตรง ๆ อย่าใช้ Import Text |
| workflow แดงที่ขั้น commit | สิทธิ์ workflow เป็น read-only | Settings → Actions → General → **Read and write permissions** |
| workflow แดงที่ขั้น build | Azure secrets ผิด/หมดอายุ หรือยังไม่ grant consent | สร้าง client secret ใหม่ แล้วอัปเดต secret ใน GitHub |
| ข้อมูลไม่อัปเดตแม้กดรีเฟรช | เบราว์เซอร์แคช | ระบบใส่ `?v=timestamp` ให้แล้ว ถ้ายังไม่หายให้กด **Ctrl+F5** |

---

## สรุปสั้นที่สุด

**ถ้าอยากใช้งานเลยวันนี้:** อัป `index.html` ไปที่ SharePoint SiteAssets
เปลี่ยนชื่อเป็น `po-approval-dashboard.html` แล้วเปิดจาก URL นั้น — จบ
ระบบจะดึงข้อมูลสดเองและใช้สิทธิ์ตาม List เดิม ไม่ต้องตั้งค่าอะไรเพิ่ม
