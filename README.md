# 📋 PO Approval Dashboard (SharePoint → GitHub Pages)

Dashboard สรุปข้อมูล SharePoint List **AC-Data Request for approval of PO**
(site `AC-Accounting`) อัปเดตอัตโนมัติทุกวันด้วย GitHub Actions

🔗 List ต้นทาง: https://dohomegroup.sharepoint.com/sites/AC-Accounting/Lists/ACData%20Request%20for%20approval%20of%20PO

---

## 🔄 วิธีทำงาน

1. GitHub Actions รันทุกวัน **07:00 น. เวลาไทย** (`cron: 0 0 * * *` = 00:00 UTC) — กดรันเองได้จากแท็บ Actions
2. ดึงข้อมูลจาก SharePoint List `AC-Data Request for approval of PO` ผ่าน Microsoft Graph API
3. สร้าง `index.html` ใหม่พร้อมข้อมูลล่าสุด (การ์ดสรุป + กราฟ + ตารางค้นหา)
4. Commit + Push → GitHub Pages อัปเดตอัตโนมัติ

## ⚙️ การตั้งค่า GitHub Secrets

ไปที่ **Settings > Secrets and variables > Actions** แล้วเพิ่ม:

| Secret | Value |
|---|---|
| `AZURE_CLIENT_ID` | `012ac5e6-9487-4436-9e0e-246c19ab2a67` |
| `AZURE_TENANT_ID` | `7f8918d9-718a-495b-ac9a-17cba381c4a0` |
| `AZURE_CLIENT_SECRET` | (ค่า Client Secret จาก Azure AD) |

> ⚠️ อย่า commit ค่า Client Secret ลงในโค้ด — ใส่ใน GitHub Secrets เท่านั้น

## 🔑 การตั้งค่า Azure AD (IT Admin ทำครั้งเดียว)

1. เปิด Azure Portal → **Azure Active Directory > App registrations**
2. เปิด App ID: `012ac5e6-9487-4436-9e0e-246c19ab2a67`
3. **Certificates & secrets → New client secret → Copy value**
4. **API permissions → Add permission → Microsoft Graph → Application permissions**
5. เพิ่ม `Sites.Read.All`
6. กด **Grant admin consent**

## 🌐 เปิดใช้งาน GitHub Pages

**Settings > Pages** → Source: `Deploy from a branch` → Branch: `main` / `(root)` → Save

## 📁 โครงสร้างไฟล์

```
sharepoint-web/
├── .github/
│   └── workflows/
│       └── update-dashboard.yml   ← GitHub Actions workflow
├── scripts/
│   └── build_dashboard.py         ← Python script ดึงข้อมูล + สร้าง HTML
├── index.html                     ← Dashboard (auto-generated)
└── README.md
```

## ⏰ ตารางเวลารันอัตโนมัติ

Workflow ตั้งไว้ที่ `cron: "0 0 * * *"` = **00:00 UTC ทุกวัน = 07:00 น. เวลาไทย**

| ต้องการให้รันตอน (เวลาไทย) | ใส่ cron |
|---|---|
| 07:00 น. (ค่าปัจจุบัน) | `0 0 * * *` |
| 08:00 น. | `0 1 * * *` |
| 09:00 น. | `0 2 * * *` |
| 07:00 น. เฉพาะ จ.–ศ. | `0 0 * * 1-5` |
| 07:00 น. และ 13:00 น. | `0 0,6 * * *` |
| ทุก 1 ชั่วโมง | `0 * * * *` |

สูตรแปลง: **ชั่วโมง UTC = ชั่วโมงไทย − 7** (ถ้าติดลบให้ +24 แล้วเลื่อนไปวันก่อนหน้า)

แก้ได้ที่บรรทัด `- cron:` ใน `.github/workflows/update-dashboard.yml`

> ⚠️ **ข้อควรทราบของ GitHub Actions**: schedule เป็น *best effort* อาจดีเลย์ 5–15 นาที
> ในช่วงที่ระบบมีงานเยอะ และ GitHub จะ **ปิด schedule อัตโนมัติถ้า repo ไม่มี activity นาน 60 วัน**
> (กด Run workflow เองหรือ push ใหม่เพื่อเปิดกลับ)

## 🖱️ รันด้วยตนเอง

ไปที่แท็บ **Actions** → เลือก **"Update PO Approval Dashboard"** → กด **Run workflow**

## 💻 รันบนเครื่อง (ทดสอบ)

```bash
pip install requests

# ดึงจาก Graph API จริง
export AZURE_TENANT_ID=7f8918d9-718a-495b-ac9a-17cba381c4a0
export AZURE_CLIENT_ID=012ac5e6-9487-4436-9e0e-246c19ab2a67
export AZURE_CLIENT_SECRET=xxxxx
python scripts/build_dashboard.py -o index.html

# หรือ preview จากไฟล์ CSV ที่ export มาจาก SharePoint
python scripts/build_dashboard.py --csv data.csv -o index.html
```

## 📊 สิ่งที่แสดงบน Dashboard

- **การ์ดสรุป**: รายการทั้งหมด / ดำเนินการเรียบร้อย / รอดำเนินการ / ยกเลิก
- **กราฟโดนัท**: สัดส่วนสถานะ
- **กราฟแท่ง**: จำนวนคำขอรายเดือน 12 เดือนล่าสุด
- **Top 10 หน่วยงาน** และ **Top 10 สาขา/Site**
- **ตัวกรองช่วงวันที่** (ตามคอลัมน์ `Created`): เลือก "ตั้งแต่วันที่ – ถึงวันที่" ด้วย date picker
  หรือกดปุ่มลัด **7 วัน / 30 วัน / 90 วัน / เดือนนี้ / เดือนที่แล้ว / ปีนี้ / ล้างตัวกรอง**
- **ตารางรายการ** ค้นหาได้ (ชื่อผู้ขอ / PR Number / หน่วยงาน / สาขา) + ตัวกรองสถานะ/หน่วยงาน/สาขา
  พร้อมลิงก์เปิด `DispForm.aspx?ID=` กลับไปยังรายการจริงใน SharePoint

> ตัวกรองทุกตัว **ทำงานร่วมกัน** และการ์ดสรุป กราฟ และ Top 10 จะคำนวณใหม่ตามผลลัพธ์ที่กรองทันที
> (เช่น เลือก 01/07/2025–31/07/2025 → 398 รายการ: เรียบร้อย 349 / รอดำเนินการ 18 / ยกเลิก 23)

## 🗂️ คอลัมน์ที่ดึงมาใช้

`ID`, `Title`, `user name`, `Department`, `PR Number`, `Status`, `Site`, `Created`, `Modified`,
`Name Department Head`, `Status Department Head`, `Status Head of Procurement Center`,
`Status Asset Register`, `Additional Notes`

หากชื่อ internal field ใน Graph ไม่ตรง ให้แก้ที่ dict `FIELDS` ใน `scripts/build_dashboard.py`
ตรวจชื่อจริงได้จาก:
`GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/columns`
