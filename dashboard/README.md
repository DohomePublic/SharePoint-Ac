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
| `dashboard/template.html` | ต้นฉบับ มี placeholder `__SNAPSHOT_JSON__` |
| `scripts/build-snapshot.mjs` | ดึงข้อมูลจาก Graph / CSV แล้ว build เป็น `index.html` |
| `.github/workflows/dashboard-build-deploy.yml` | build + commit + deploy GitHub Pages |
| `.github/workflows/dashboard-upload-sharepoint.yml` | อัปโหลดไฟล์ขึ้น SharePoint SiteAssets |

## โหมดข้อมูล 2 แบบ (สลับอัตโนมัติ)

1. **LIVE** — เมื่อเปิดไฟล์จากโดเมน `*.sharepoint.com` จะดึงข้อมูลสดผ่าน SharePoint REST API
   (`/_api/web/lists/getByTitle(...)`) โดย map *Display Name → Internal Name* จาก `/fields`
   ตอนรันไทม์ จึงไม่มีการฮาร์ดโค้ดชื่อ internal ที่เป็น `_x0e01_...`
2. **SNAPSHOT** — เมื่อเปิดจาก GitHub Pages หรือ `file://` จะใช้ข้อมูลที่ฝังไว้ในไฟล์
   (dictionary-encoded JSON ~1.7 MB สำหรับ 5,760 รายการ)

หาก LIVE ล้มเหลว ระบบจะ fallback เป็น SNAPSHOT พร้อมแสดงเหตุผลบนแถบแจ้งเตือน

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
- KPI 7 ใบ (กดเพื่อกรอง) และกราฟ 3 ชุด: สถานะ / Top 8 Site / คำขอต่อเดือน
- หน้ารายละเอียดแสดง timeline การอนุมัติ 3 ขั้น + ลิงก์ไป `DispForm.aspx`
- Export CSV (UTF-8 BOM) / Excel / JSON / พิมพ์เป็น PDF ตามผลลัพธ์ที่กรองอยู่
- Auto-refresh: ปิด / 1 / 5 (ค่าเริ่มต้น) / 15 นาที
- โหมดสว่าง–มืด จำค่าไว้ใน localStorage

## Build เอง

```bash
# จาก SharePoint ผ่าน Graph
AZURE_TENANT_ID=... AZURE_CLIENT_ID=... AZURE_CLIENT_SECRET=... \
  node scripts/build-snapshot.mjs

# หรือจากไฟล์ CSV ที่ export จาก List
node scripts/build-snapshot.mjs --from-csv ./export.csv
```

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
