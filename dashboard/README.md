# PO Approval Dashboard

แดชบอร์ดตรวจสอบข้อมูลการอนุมัติ PO อ่านข้อมูลจาก SharePoint List
**AC-Data Request for approval of PO**
(`https://dohomegroup.sharepoint.com/sites/AC-Accounting/Lists/ACData%20Request%20for%20approval%20of%20PO/AllItems.aspx`)

> ⚠️ ไฟล์ทั้งหมดของแดชบอร์ดถูกแยกไว้ใน `dashboard/` และ `scripts/` เท่านั้น
> ไม่มีการแก้ไขหรือทับไฟล์เดิมของ repository

## โครงสร้างไฟล์

| ไฟล์ | หน้าที่ |
|---|---|
| `dashboard/index.html` | ไฟล์แดชบอร์ดที่ build แล้ว (ฝัง snapshot) — ไฟล์เดียวจบ ไม่พึ่ง CDN |
| `dashboard/data.json` | ข้อมูลแยกไฟล์ สำหรับปุ่ม 🔄 รีเฟรช ดึงจาก GitHub |
| `dashboard/template.html` | ต้นฉบับ มี placeholder `__SNAPSHOT_JSON__` — **แก้หน้าตา/กราฟที่ไฟล์นี้** |
| `dashboard/build-report.json` | สรุปผล build ล่าสุด (จำนวนแถว, รายการใหม่สุด, แยกตามสถานะ) |
| `scripts/build-snapshot.mjs` | ดึงข้อมูลจาก Graph / CSV แล้ว build เป็น `index.html` + `data.json` |
| `scripts/rebuild-from-data.mjs` | build `index.html` ใหม่จาก `data.json` เดิม (ไม่ต้องต่อ SharePoint) |
| `.github/workflows/dashboard-build-deploy.yml` | ดึงข้อมูลอัตโนมัติ + commit + deploy GitHub Pages |
| `.github/workflows/dashboard-upload-sharepoint.yml` | อัปโหลดไฟล์ขึ้น SharePoint SiteAssets |

## โหมดข้อมูล 3 แบบ (เลือกได้จากดรอปดาวน์ "แหล่งข้อมูล" บนหัวเว็บ)

| โหมด | ที่มาของข้อมูล |
|---|---|
| **LIVE** | SharePoint REST API — ใช้เมื่อเปิดไฟล์จากโดเมน `*.sharepoint.com` map *Display Name → Internal Name* จาก `/fields` ตอนรันไทม์ ไม่ฮาร์ดโค้ดชื่อ internal ที่เป็น `_x0e01_...` |
| **GITHUB** | ดึง `dashboard/data.json` ที่ workflow build ไว้ (มี cache-bust `?v=timestamp`) |
| **SNAPSHOT** | ข้อมูลที่ฝังในไฟล์ `index.html` เอง ใช้ได้แม้ออฟไลน์ |

ค่าเริ่มต้นคือ **อัตโนมัติ**: บน SharePoint → `LIVE → GITHUB → SNAPSHOT`,
ที่อื่น → `GITHUB → SNAPSHOT` และตัวเลือกที่ผู้ใช้เลือกจะถูกจำไว้ใน localStorage

### ปุ่ม 🔄 รีเฟรช

กดแล้วจะ **ดึงข้อมูลใหม่ตามแหล่งที่เลือก** ทันที (ไม่ต้องโหลดหน้าใหม่)
ระหว่างดึงปุ่มจะเปลี่ยนเป็น "⏳ กำลังดึง…" และล็อกไว้กันกดซ้ำ
เสร็จแล้วแจ้งผลเป็น toast พร้อมบอกแหล่งและจำนวนรายการ

ลำดับ endpoint ของโหมด GitHub (ลองไล่ลงจนกว่าจะสำเร็จ):
1. `data.json` (ไฟล์ข้าง ๆ — ใช้เมื่อ deploy บน GitHub Pages, เร็วที่สุด)
2. `https://raw.githubusercontent.com/DohomePublic/SharePoint-Ac/main/dashboard/data.json`
3. `https://cdn.jsdelivr.net/gh/DohomePublic/SharePoint-Ac@main/dashboard/data.json`

หากต้องการเปลี่ยน owner/repo/branch แก้ที่ค่า `GH` ในหัวสคริปต์ของ `template.html`

## คอลัมน์ที่ใช้ (Display Name จริงจาก List)

`Title` (เลขที่คำขอ) · `id number` · `user name` · `Department` · `PR Number` ·
`Additional Notes` · `Name/Time/Status/Comment Department Head` ·
`Name/Time/Status/Comment Head of Procurement Center` ·
`Name/Time/Status/Comment Asset ` (มีช่องว่างท้ายชื่อจริง) ·
`Status` (Choice) · `Email User` (Person) · `Site` · `Created` · `Modified` · `Attachments`

ค่าที่ปรากฏจริง:
- `Status`: ดำเนินการเรียบร้อย · ยกเลิก · รอดำเนินการ
- `Status Department Head`: อนุมัติ · รอหัวหน้าสายงานอนุมัติ · ไม่อนุมัติ
- `Status Head of Procurement Center`: อนุมัติ · รอศูนย์จัดซื้อทรัพย์สินพิจารณา · ไม่อนุมัติ
- `Status Asset Register`: อนุมัติ · รอบัญชีทรัพย์สินพิจารณา · ไม่อนุมัติ

## ความสามารถ

- ตาราง responsive 16 คอลัมน์ เรียงลำดับได้ทุกคอลัมน์ (รู้ชนิดตัวเลข/วันที่/ข้อความ)
- ค้นหาบางส่วนหลายคำพร้อมกัน ครอบคลุม 19 คอลัมน์
- ตัวกรอง 12 ตัว + chip ถอดตัวกรองรายตัว
- KPI 7 ใบ (กดเพื่อกรอง)
- หน้ารายละเอียดแสดง timeline การอนุมัติ 3 ขั้น + ลิงก์ไป `DispForm.aspx`
- Export CSV (UTF-8 BOM) / Excel / JSON / พิมพ์เป็น PDF ตามผลลัพธ์ที่กรองอยู่
- Auto-refresh: ปิด / 1 / 5 (ค่าเริ่มต้น) / 15 นาที
- โหมดสว่าง–มืด จำค่าไว้ใน localStorage

### แถบ "ข้อมูลล่าสุด"

อยู่ใต้หัวเว็บ บอกว่าข้อมูลชุดที่กำลังดูสดถึงเมื่อไหร่ (เวลาไทย), วันล่าสุดที่มีคำขอและจำนวน,
จำนวนคำขอของวันนี้ พร้อมปุ่ม **ดูเฉพาะวันล่าสุด** / **ไปรายการใหม่สุด**
ถ้าข้อมูลเก่ากว่า 24 ชม. แถบจะเปลี่ยนเป็นสีส้มเตือน

### กราฟสรุป (SVG ล้วน ไม่พึ่ง CDN — คลิกทุกกราฟเพื่อกรองต่อได้)

| กราฟ | รายละเอียด |
|---|---|
| 📅 คำขอรายวัน | เลือก 14/30/60/90 วัน · แท่งขวาสุด = วันล่าสุด ไฮไลต์สีแบรนด์ |
| 🍩 โดนัทสถานะรวม | สัดส่วน + จำนวน + % ในคำอธิบาย |
| 🪜 ผลพิจารณาแต่ละขั้น | แท่งซ้อน 3 ขั้น พร้อม % อนุมัติของแต่ละขั้น |
| ⏱ ระยะเวลาอนุมัติ | มัธยฐาน / เฉลี่ย / P90 ของแต่ละขั้น (ชม. หรือ วัน) |
| 📈 คำขอต่อเดือน | กราฟเส้น+พื้นที่ 12 เดือนล่าสุด คลิกจุด = กรองทั้งเดือน |
| 🕒 ตามช่วงเวลาของวัน | 24 ชั่วโมง เวลาไทย |
| 🏢🏷👤✅ Top 10 | สาขา/Site · แผนก · ผู้ขอ · ผู้อนุมัติศูนย์จัดซื้อ |

มีปุ่ม **ซ่อน/แสดงกราฟ** จำค่าไว้ใน localStorage (`po_charts`)

### การจัดการเวลา (สำคัญ)

แดชบอร์ดแสดงและจัดกลุ่มวันที่ด้วย **เวลาไทย (Asia/Bangkok, UTC+7) เสมอ**
ไม่ว่าเครื่องผู้ใช้จะตั้งโซนเวลาใด เพื่อให้ตรงกับที่เห็นใน SharePoint

- `Created` / `Modified` : ISO UTC (`…Z`) → แปลงเป็นเวลาไทยก่อนแสดง
- `Time Department Head` / `Time Head of Procurement Center` / `Time Asset Register` :
  ข้อความรูปแบบ `d/M/yyyy HH:mm` ซึ่งเป็นเวลาไทยอยู่แล้ว (บางแถวมีวินาที) —
  `new Date()` ของเบราว์เซอร์อ่านรูปแบบนี้ไม่ได้ จึงมี parser เฉพาะใน `dOnly()`
- การกรองช่วงวันที่เทียบด้วยคีย์ `YYYY-MM-DD` แบบเวลาไทย จึงไม่มีปัญหาคาบเกี่ยวข้ามวัน

## Build เอง

```bash
# จาก SharePoint ผ่าน Graph
AZURE_TENANT_ID=... AZURE_CLIENT_ID=... AZURE_CLIENT_SECRET=... \
  node scripts/build-snapshot.mjs

# หรือจากไฟล์ CSV ที่ export จาก List
node scripts/build-snapshot.mjs --from-csv ./export.csv

# ข้าม safety guard (ใช้เมื่อจำนวนแถวลดลงจริง เช่น มีการล้างข้อมูล)
node scripts/build-snapshot.mjs --force

# แก้แค่ template.html แล้ว build ใหม่โดยไม่ต้องต่อ SharePoint
node scripts/rebuild-from-data.mjs
```

ต้องใช้ Node.js 18 ขึ้นไป (ใช้ `fetch` ในตัว) — ไม่มี dependency ภายนอก ไม่ต้อง `npm install`

### Safety guard

ถ้าดึงข้อมูลได้น้อยกว่าครั้งก่อนเกิน 10% สคริปต์จะ **หยุดและไม่เขียนทับไฟล์เดิม**
เพื่อกันกรณี API คืนข้อมูลไม่ครบแล้วทำให้ข้อมูลหาย ต้องยืนยันด้วย `--force`
หรือ `FORCE_BUILD=true` จึงจะเขียนทับ

### Retry อัตโนมัติ

การเรียก Microsoft Graph มี retry สูงสุด 5 ครั้ง สำหรับ HTTP `429` (throttle) และ `5xx`
โดยเคารพ header `Retry-After` และใช้ exponential backoff (สูงสุด 30 วินาที)
ส่วน `401` / `403` / `404` จะ fail ทันที เพราะ retry ไปก็ไม่ช่วย

## ตารางเวลาดึงข้อมูลอัตโนมัติ

`.github/workflows/dashboard-build-deploy.yml`

| cron (UTC) | เวลาไทย |
|---|---|
| `0,30 1-13 * * 1-6` | ทุก 30 นาที 08:00–20:30 น. จันทร์–เสาร์ |
| `0 17 * * *` | 00:00 น. ทุกวัน (รอบปิดวัน) |

รันเองได้ที่แท็บ **Actions → Dashboard - ดึงข้อมูล & Deploy → Run workflow**
มีตัวเลือก `skip_refresh` (ไม่ดึงใหม่) · `force` (ข้าม guard) · `deploy_pages`

หลังรันเสร็จ ดูสรุปได้ที่ **Job Summary** ของ run นั้น (จำนวนรายการ, รายการใหม่สุด,
เทียบกับครั้งก่อน, แยกตามสถานะ) และดาวน์โหลดไฟล์ได้จาก **Artifacts** (เก็บ 30 วัน)

ถ้ารอบ schedule ล้มเหลว workflow จะ **เปิด GitHub Issue อัตโนมัติ** (label `dashboard-refresh`)
ถ้ามี issue เปิดค้างอยู่แล้วจะ comment ต่อในอันเดิม ไม่สร้างซ้ำ

> ⚠️ GitHub จะ **ปิด schedule อัตโนมัติหาก repo ไม่มี commit ใน 60 วัน**
> workflow นี้ commit ทุกครั้งที่ข้อมูลเปลี่ยน จึงไม่ถูกปิดในทางปฏิบัติ
> และรอบ schedule มักดีเลย์ 5–20 นาทีตามคิว runner ของ GitHub

## Secrets ที่ต้องตั้งใน GitHub

`Settings → Secrets and variables → Actions`

| Secret | ค่า |
|---|---|
| `AZURE_TENANT_ID` | Tenant ID ของ DOHOME |
| `AZURE_CLIENT_ID` | Application (client) ID ของ App Registration |
| `AZURE_CLIENT_SECRET` | Client secret |

สิทธิ์ Microsoft Graph แบบ **Application** ที่ต้อง grant admin consent:
`Sites.Selected` (แนะนำ — จำกัดเฉพาะไซต์ AC-Accounting) หรือ `Sites.ReadWrite.All`

> repository นี้เป็น public — ข้อมูลใน `dashboard/index.html` จะเปิดสาธารณะด้วย
> หากข้อมูลเป็นความลับ ให้เปลี่ยน repo เป็น private หรือ build เฉพาะโหมด LIVE
> (ลบบล็อก `id="snap"` ออก) แล้ว deploy ผ่าน SiteAssets เท่านั้น
