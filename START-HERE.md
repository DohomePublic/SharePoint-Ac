# เริ่มตรงนี้ — PO Approval Dashboard

ในไฟล์ zip นี้มีอะไรบ้าง

| ไฟล์ | ใช้ทำอะไร |
|---|---|
| `index.html` | **ตัวแดชบอร์ด** (36 KB) อัปโหลดไฟล์นี้ไฟล์เดียวขึ้น SharePoint ก็ใช้งานได้เลย |
| `docs/index.html` | สำเนาสำหรับ GitHub Pages (หน้าตัวอย่าง ไม่มีข้อมูล) |
| `README.md` | คู่มือโครงการ ฟีเจอร์ และตาราง mapping คอลัมน์ |
| `DEPLOY-GITHUB.md` | วิธีนำเข้า GitHub 4 วิธี + วิธีเปิด GitHub Pages |
| `push-to-github.sh` | สคริปต์ push ขึ้น GitHub อัตโนมัติ พร้อมด่านตรวจความปลอดภัย |
| `.gitignore` | กันไฟล์ที่มีข้อมูลจริงหลุดขึ้น repo สาธารณะ |
| `START-HERE.bat` | เมนูลัดสำหรับ Windows (ดับเบิลคลิก) |

---

## ใช้งานจริงใน 3 ขั้น (ใช้เวลา 2 นาที)

1. แตกไฟล์ zip นี้
2. เปิด https://dohomegroup.sharepoint.com/sites/AC-Accounting/SiteAssets/Forms/AllItems.aspx
   แล้วอัปโหลด **`index.html`** ขึ้นไป
3. เปิดลิงก์นี้ในเบราว์เซอร์
   `https://dohomegroup.sharepoint.com/sites/AC-Accounting/SiteAssets/index.html`

เสร็จ — แดชบอร์ดจะขึ้นสถานะ 🟢 **Live** ดึงข้อมูลจากลิสต์เอง และซิงก์อัตโนมัติทุก 5 นาที
(ปรับรอบเป็น 1 / 10 / 30 / 60 นาที หรือปิดได้ที่มุมขวาบน)

> ถ้าดับเบิลคลิก `index.html` จากเครื่องตัวเอง จะขึ้น 🟡 Snapshot 0 รายการ — ถูกต้องแล้ว
> เพราะเบราว์เซอร์บล็อกการเรียก API ข้ามโดเมน ต้องเปิดผ่าน URL ของ SharePoint เท่านั้น

---

## นำเข้า GitHub

อ่าน `DEPLOY-GITHUB.md` — สรุปสั้น: อัปโหลด `index.html`, `docs/`, `README.md`, `.gitignore`
ขึ้น https://github.com/DohomePublic/SharePoint-Ac แล้วเปิด Pages จาก branch `main` folder `/docs`

---

## ความปลอดภัย

ไฟล์ zip นี้ **ไม่มีข้อมูลพนักงาน คำขอ PR/PO หรือรหัสผ่านใด ๆ อยู่ภายใน** — ตรวจสอบแล้วด้วยสคริปต์อัตโนมัติ
แดชบอร์ดดึงข้อมูลตอนเปิดใช้งานด้วยสิทธิ์ของผู้ที่ล็อกอินอยู่ (`credentials: include`)
ผู้ที่ไม่มีสิทธิ์อ่านลิสต์จะไม่เห็นข้อมูล จึงปลอดภัยที่จะวางบน GitHub สาธารณะ

**อย่าใส่** ไฟล์ `PO_Approval_Dashboard.html` (5.2 MB ที่ฝังข้อมูลจริง 5,757 รายการ) ลงใน zip นี้
หรืออัปโหลดขึ้น GitHub เด็ดขาด — ใช้ภายในหรือวางบน SharePoint เท่านั้น
