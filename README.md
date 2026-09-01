# SharePoint-Ac — PO Approval Dashboard

แดชบอร์ดติดตามคำขออนุมัติ PO จาก SharePoint List **AC-Data Request for approval of PO**
(ไซต์ `https://dohomegroup.sharepoint.com/sites/AC-Accounting`)

ไฟล์เดียวจบ ไม่มี build step ไม่มี dependency ไม่ใช้ CDN ใด ๆ — เปิดแล้วดึงข้อมูลสดจาก SharePoint REST API
ด้วยสิทธิ์ของผู้ใช้ที่ล็อกอินอยู่

> ⚠️ **repo นี้ไม่มีข้อมูลจริงอยู่เลย** `index.html` เป็น *live-only build*: ข้อมูลทั้งหมดถูกดึงตอนรันไทม์จาก
> SharePoint ของบริษัท ไม่มีการฝัง record, ชื่อพนักงาน, รหัสพนักงาน, PR/PO หรือ credential ใด ๆ ลงในซอร์ส
> **ห้าม commit ไฟล์ที่ฝังข้อมูลจริง (snapshot build) ขึ้น repo สาธารณะ** — ดู `.gitignore`

## ฟีเจอร์

- **KPI**: Total Request / Approved / Pending / Rejected-Cancelled / Total PO Amount (คลิกการ์ดเพื่อกรอง)
- **Search & Filter**: Request No, PR/PO Number, Vendor–Site, Requester, Department, Approval Status, Request Date (from–to), ค้นหาอิสระทุกคอลัมน์
- **Visual**: Monthly Trend (stacked), Approval Status donut, Department Summary Top 12, Vendor/Site Summary Top 12
- **Detail Table**: ค้นหา/เรียงลำดับ/แบ่งหน้า + Drill through รายคำขอ พร้อม Approval Flow 3 ขั้น และลิงก์เปิดรายการจริงใน SharePoint
- **Export**: CSV (UTF-8 BOM รองรับภาษาไทย), Excel (.xls), PDF ผ่าน Print stylesheet
- **Auto-update**: ดึงข้อมูลใหม่อัตโนมัติทุก 1/5/10/30/60 นาที + รีเฟรชเมื่อกลับมาที่แท็บ + แจ้งเตือน "มีคำขอใหม่ N รายการ" + ไฮไลต์แถวใหม่
- **Cache**: เก็บชุดข้อมูลล่าสุดไว้ใน localStorage ของเครื่องผู้ใช้ ให้เปิดครั้งถัดไปเห็นข้อมูลทันที
- Responsive layout + corporate theme

## การ deploy (สำคัญ)

**GitHub Pages ใช้แสดงผลได้ แต่จะดึงข้อมูลสดไม่ได้** เพราะ SharePoint ไม่ส่ง CORS header ให้โดเมน
`*.github.io` และเบราว์เซอร์ไม่ส่ง cookie ข้ามไซต์ → หน้าเว็บจะขึ้นสถานะ 🟡 Snapshot พร้อมคำแนะนำติดตั้ง

**วิธีที่ใช้งานได้จริง — โฮสต์บนโดเมนเดียวกับ SharePoint:**

1. ดาวน์โหลด `index.html` จาก repo นี้ (หรือ `git clone`)
2. อัปโหลดขึ้นไลบรารี `Site Assets` ของไซต์ `AC-Accounting`
3. เปิดด้วย URL: `https://dohomegroup.sharepoint.com/sites/AC-Accounting/SiteAssets/index.html`
4. หน้าเว็บจะขึ้น 🟢 **Live** และเริ่มซิงก์อัตโนมัติ

ทางเลือกอื่นที่ทำงานได้: วางบน Web Server ภายในที่ใช้ SSO เดียวกัน, ฝังผ่าน Web Part *Embed*,
หรือ deploy เป็น SPFx web part

### เผยแพร่หน้าตัวอย่าง (ไม่มีข้อมูล) บน GitHub Pages

Settings → Pages → Source: `Deploy from a branch` → Branch: `main` / folder: `/docs` → Save
จะได้ `https://dohomepublic.github.io/SharePoint-Ac/` สำหรับดูหน้าตา/รีวิวโค้ดเท่านั้น

## สิทธิ์ที่ต้องใช้

ผู้เปิดดูต้องมีสิทธิ์อ่านลิสต์อยู่แล้ว — แดชบอร์ดเรียก API ด้วย session ของผู้ใช้เอง (`credentials: include`)
ไม่มี service account, ไม่มี token, ไม่มี secret ในโค้ด

## หมายเหตุเรื่องคอลัมน์

ลิสต์ต้นทางไม่มีคอลัมน์ Vendor และ PO Amount โดยตรง จึงแมปดังนี้

| ช่องบนแดชบอร์ด | ที่มา |
|---|---|
| Vendor / Site | คอลัมน์ `Site` |
| PO Number | ดึงด้วย regex จากคอมเมนต์ผู้อนุมัติ / Additional Notes |
| PO Amount | ดึงด้วย regex จากข้อความเดียวกัน |
| Request No | คอลัมน์ `Title` |
| Approval Status | คำนวณจาก `Status` + สถานะ 3 ขั้นอนุมัติ |

ถ้าเพิ่มคอลัมน์ `Vendor` และ `PO Amount` ในลิสต์ ให้เพิ่ม mapping ในตัวแปร `MAP` ใน `index.html`

## โครงสร้าง

```
index.html        live-only build (ตัวจริงสำหรับ deploy)
docs/index.html   สำเนาสำหรับ GitHub Pages
.gitignore        กัน snapshot ที่มีข้อมูลจริงหลุดขึ้น repo
```
