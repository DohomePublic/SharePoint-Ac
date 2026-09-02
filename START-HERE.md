# START HERE — PO Approval Dashboard

แพ็กเกจนี้พร้อมใช้งานทันที ไม่ต้อง `npm install` ไม่ต้อง build ก่อน

---

## ⚡ ใช้งานเร็วสุด (30 วินาที)

แตกไฟล์ zip → ดับเบิลคลิก **`dashboard/index.html`**

เปิดได้เลยในเบราว์เซอร์ ไม่ต้องมีอินเทอร์เน็ต เพราะมีข้อมูล 5,760 รายการฝังอยู่ในไฟล์
(มุมขวาบนจะขึ้นป้าย `SNAPSHOT` สีเทา)

---

## 📁 มีอะไรในแพ็กเกจนี้

```
START-HERE.md                  ← ไฟล์นี้
DEPLOY-GUIDE.md                คู่มือนำไปวางแบบละเอียด 4 วิธี
PUSH-INSTRUCTIONS.md           วิธี push ขึ้น GitHub (คำสั่ง + ผ่านหน้าเว็บ)
push.sh / push.ps1             สคริปต์ push อัตโนมัติ (Linux-macOS / Windows)
.gitignore.dashboard           ตัวอย่าง .gitignore (เปลี่ยนชื่อเป็น .gitignore หากยังไม่มี)

dashboard/
  index.html                   ⭐ แดชบอร์ดพร้อมใช้ (ไฟล์เดียวจบ ฝังข้อมูลแล้ว)
  data.json                    ข้อมูลแยกไฟล์ สำหรับปุ่ม 🔄 รีเฟรช
  template.html                ต้นฉบับ — แก้หน้าตา/กราฟที่ไฟล์นี้
  build-report.json            สรุปผล build ล่าสุด
  README.md                    เอกสารเทคนิคฉบับเต็ม

scripts/
  build-snapshot.mjs           ดึงข้อมูลจาก SharePoint (Graph) หรือ CSV แล้ว build
  rebuild-from-data.mjs        build ใหม่จาก data.json เดิม (ไม่ต้องต่อ SharePoint)

.github/workflows/
  dashboard-build-deploy.yml       ดึงข้อมูลอัตโนมัติ + commit + deploy Pages
  dashboard-upload-sharepoint.yml  อัปโหลดไฟล์ขึ้น SharePoint SiteAssets
```

---

## 🎯 เลือกวิธีใช้งานตามสถานการณ์

| สถานการณ์ | ทำอย่างไร | ผลลัพธ์ |
|---|---|---|
| อยากดูเดี๋ยวนี้คนเดียว | ดับเบิลคลิก `dashboard/index.html` | โหมด SNAPSHOT |
| อยากให้ทีมใช้ + ข้อมูลสดเสมอ | อัป `index.html` ขึ้น SharePoint **Site Assets** | โหมด **LIVE** ⭐ แนะนำ |
| อยากให้อัปเดตเองทุกวัน | push ขึ้น GitHub + ตั้ง 3 secrets | Workflow ดึงให้อัตโนมัติ |
| อยากได้ลิงก์เปิดจากที่ไหนก็ได้ | เปิด GitHub Pages | ⚠️ repo public = ข้อมูลเปิดสาธารณะ |

รายละเอียดทุกวิธีอยู่ใน **`DEPLOY-GUIDE.md`**

---

## 🚀 วิธีที่แนะนำที่สุด (ได้ข้อมูลสด)

1. เปิด `https://dohomegroup.sharepoint.com/sites/AC-Accounting/SiteAssets`
2. **Upload → Files** เลือก `dashboard/index.html`
3. เปลี่ยนชื่อไฟล์เป็น `po-approval-dashboard.html`
4. เปิด URL:
   `https://dohomegroup.sharepoint.com/sites/AC-Accounting/SiteAssets/po-approval-dashboard.html`
5. มุมขวาบนต้องขึ้นป้าย **LIVE** สีเขียว = ดึงข้อมูลสดจาก List สำเร็จ

> ผู้ใช้จะเห็นเฉพาะข้อมูลที่ตัวเองมีสิทธิ์อ่านใน List อยู่แล้ว ไม่ต้องตั้ง permission เพิ่ม

---

## 🔄 ตั้งให้อัปเดตอัตโนมัติผ่าน GitHub Actions

1. push แพ็กเกจนี้ขึ้น repo (ดู `PUSH-INSTRUCTIONS.md`)
2. **Settings → Secrets and variables → Actions** เพิ่ม 3 ตัว:
   `AZURE_TENANT_ID` · `AZURE_CLIENT_ID` · `AZURE_CLIENT_SECRET`
3. **Settings → Actions → General → Workflow permissions** = **Read and write permissions**
4. **Settings → Pages → Source** = **GitHub Actions** (เฉพาะถ้าจะใช้ Pages)
5. Entra ID App → API permissions → Microsoft Graph **Application** →
   `Sites.Selected` → **Grant admin consent**
   แล้วให้สิทธิ์ระดับไซต์: `PATCH /sites/{site-id}/permissions` role `write`
6. ไปแท็บ **Actions** → เลือก *Dashboard - ดึงข้อมูล & Deploy* → **Run workflow** เพื่อทดสอบ

ตารางเวลา: ทุก 30 นาที ช่วง 08:00–20:30 น. ไทย จันทร์–เสาร์ + 00:00 น. ทุกวัน

---

## ✅ Checklist ตรวจรับ

เปิดแดชบอร์ดแล้วตรวจตามนี้ ถ้าตรงทุกข้อ = ใช้งานได้สมบูรณ์

- [ ] `dashboard/index.html` ขนาด **1,766,013 bytes**
- [ ] เปิดแล้วขึ้น **5,760 รายการ**
- [ ] แถบฟ้าใต้หัวเว็บขึ้น *ข้อมูลล่าสุดในชุดนี้: 01/09/2026 12:44 น. (เวลาไทย)*
- [ ] กรอง Status = `ยกเลิก` → ได้ **234** รายการ
- [ ] ค้นหา `มหาชัย` → ได้ **76** รายการ
- [ ] กรองวันที่ 01/08/2026–31/08/2026 → **387** รายการ
- [ ] กดปุ่ม **ดูเฉพาะวันล่าสุด** → ได้ **6** รายการ (วันที่ 01/09/2026)
- [ ] เห็นกราฟครบ: รายวัน · โดนัท · ขั้นอนุมัติ · ระยะเวลา · รายเดือน · รายชั่วโมง · Top 10 ×4
- [ ] กดโดนัทส่วน "ยกเลิก" แล้วตารางกรองตาม
- [ ] กด **Export CSV** เปิดใน Excel ภาษาไทยไม่เพี้ยน

---

## 🩺 แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| หน้าว่างเปล่า | JavaScript ถูกบล็อก (SharePoint Custom Script) → ใช้ Embed web part หรือเปิดไฟล์ตรง |
| ขึ้น SNAPSHOT แทน LIVE | ไม่ได้เปิดจากโดเมน `*.sharepoint.com` หรือไม่มีสิทธิ์อ่าน List → เลือก *แหล่งข้อมูล = SharePoint สด* เพื่อดูข้อความ error |
| ไม่เห็นข้อมูลของวันนี้ | snapshot ในไฟล์หยุดที่วัน build → ใช้โหมด LIVE หรือกด Run workflow ให้ build ใหม่ |
| เวลาไม่ตรงกับ SharePoint | แดชบอร์ดใช้เวลาไทย (UTC+7) เสมอ — ถ้ายังเพี้ยนแปลว่าค่าใน List ผิดรูปแบบ |
| กดรีเฟรชแล้วไม่สำเร็จ | ยังไม่ได้ push `dashboard/data.json` ขึ้น GitHub |
| Workflow ขึ้นสีแดง | ตรวจ 3 secrets · admin consent · ชื่อ List ต้องตรงเป๊ะ |
| Workflow commit ไม่ได้ | Settings → Actions → General → Workflow permissions ยังเป็น Read-only |

---

## ⚠️ ข้อควรระวังเรื่องความลับข้อมูล

repo `DohomePublic/SharePoint-Ac` เป็น **public** — ถ้า push `dashboard/index.html`
และ `dashboard/data.json` ขึ้นไป ข้อมูลคำขอ PO ทั้ง 5,760 รายการ (ชื่อผู้ขอ อีเมล แผนก สาขา)
จะเปิดสาธารณะ

ถ้าไม่ต้องการ ให้เลือกอย่างใดอย่างหนึ่ง:
1. เปลี่ยน repo เป็น **private**
2. หรือ **ไม่ commit** `index.html` / `data.json` (ใส่ใน `.gitignore`) แล้วให้ workflow
   build เองแล้วอัปโหลดเข้า SharePoint SiteAssets อย่างเดียว
   (`dashboard-upload-sharepoint.yml`)
