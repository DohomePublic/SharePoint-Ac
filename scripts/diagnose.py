#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnose.py — ตรวจว่าทำไมข้อมูลไม่อัปเดตจาก SharePoint

รัน:  python scripts/diagnose.py
ต้องมี env: AZURE_TENANT_ID / AZURE_CLIENT_ID / AZURE_CLIENT_SECRET

จะบอกทีละขั้นว่า ตรงไหนผ่าน ตรงไหนพัง พร้อมวิธีแก้
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_dashboard import (COLS, HOSTNAME, LIST_TITLE, SITE_PATH, g,  # noqa: E402
                             get_token)

BKK = timezone(timedelta(hours=7))
OK, NG, WARN = "✅", "❌", "⚠️ "


def main():
    print("=" * 66)
    print(" ตรวจสอบการเชื่อมต่อ SharePoint")
    print("=" * 66)

    # 1) secrets
    have = {k: bool(os.environ.get(k)) for k in
            ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET")}
    for k, v in have.items():
        print(f"{OK if v else NG} {k}: {'มี' if v else 'ไม่มี'}")
    if not all(have.values()):
        print(f"\n{NG} ขาด secrets → ดึงข้อมูลไม่ได้")
        print("   แก้: Settings → Secrets and variables → Actions → New repository secret")
        return 1

    # 2) token
    try:
        tk = get_token()
        print(f"{OK} ขอ access token สำเร็จ")
    except Exception as e:
        print(f"{NG} ขอ token ไม่สำเร็จ: {e}")
        print("   แก้: ตรวจว่า client secret หมดอายุหรือยัง (Azure Portal → App registrations")
        print("        → Certificates & secrets — secret มีอายุสูงสุด 24 เดือน)")
        return 1

    # 3) site
    try:
        site = g(f"https://graph.microsoft.com/v1.0/sites/{HOSTNAME}:{SITE_PATH}", tk)
        print(f"{OK} เข้าถึงไซต์ได้: {site.get('displayName')} ({site['id'][:40]}…)")
    except Exception as e:
        print(f"{NG} เข้าถึงไซต์ไม่ได้: {str(e)[:250]}")
        print("   แก้: App Registration ต้องมีสิทธิ์ Sites.Selected (Application)")
        print("        แล้วให้แอดมินอนุมัติ + grant สิทธิ์ read บนไซต์ AC-Accounting โดยเฉพาะ")
        return 1

    # 4) list
    lists = g(f"https://graph.microsoft.com/v1.0/sites/{site['id']}/lists?$select=id,displayName", tk)
    names = [l.get("displayName") for l in lists.get("value", [])]
    lst = next((l for l in lists.get("value", []) if l.get("displayName") == LIST_TITLE), None)
    if not lst:
        print(f"{NG} ไม่พบ List ชื่อ '{LIST_TITLE}'")
        print(f"   List ที่มองเห็น ({len(names)}): {names}")
        print("   แก้: แก้ค่า SP_LIST_TITLE ใน workflow ให้ตรงกับชื่อจริง")
        return 1
    print(f"{OK} พบ List: {LIST_TITLE}")

    # 5) columns
    cols = g(f"https://graph.microsoft.com/v1.0/sites/{site['id']}/lists/{lst['id']}"
             f"/columns?$select=name,displayName", tk)
    by_display = {}
    for c in cols.get("value", []):
        by_display.setdefault(c.get("displayName"), c.get("name"))
    auto = ("_ID", "Created", "Modified", "_HasAttachments")
    missing = [c for c in COLS if c not in by_display and c not in auto]
    if missing:
        print(f"{WARN}คอลัมน์ที่หาไม่เจอ (จะเว้นว่าง): {missing}")
        print(f"   Display Name ที่ List มีจริง: {sorted(by_display)}")
    else:
        print(f"{OK} คอลัมน์ครบทั้ง {len(COLS)} คอลัมน์")

    # 6) นับรายการจริง + ดูรายการใหม่สุด
    print("\nกำลังนับรายการทั้งหมด…")
    total, newest, page = 0, [], 0
    url = (f"https://graph.microsoft.com/v1.0/sites/{site['id']}/lists/{lst['id']}"
           f"/items?expand=fields&$top=500")
    while url and page < 400:
        j = g(url, tk)
        page += 1
        for it in j.get("value", []):
            total += 1
            newest.append((it.get("createdDateTime"), it.get("id"),
                           (it.get("fields") or {}).get("Title")))
        url = j.get("@odata.nextLink")
    newest.sort(key=lambda x: x[0] or "")
    print(f"{OK} ดึงได้ {total:,} รายการ ({page} หน้า)")

    print("\n5 รายการใหม่สุดที่ App มองเห็น:")
    for c, i, t in newest[-5:][::-1]:
        bkk = datetime.fromisoformat(c.replace("Z", "+00:00")).astimezone(BKK)
        print(f"   {bkk:%d/%m/%Y %H:%M} น. · เลขที่คำขอ {t} · ID {i}")

    # 7) เทียบกับ data.json ใน repo
    dj = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "dashboard", "data.json")
    if os.path.exists(dj):
        with open(dj, encoding="utf-8") as fh:
            d = json.load(fh)
        print(f"\nไฟล์ data.json ใน repo มี {d['data']['n']:,} รายการ (build {d.get('builtAt')})")
        if d["data"]["n"] == total:
            print(f"{WARN}จำนวนเท่ากับที่ดึงมาได้ → ไม่มีรายการใหม่จริง ๆ "
                  "หรือ App มองเห็นข้อมูลไม่ครบ")
        else:
            print(f"{OK} ต่างกัน {total - d['data']['n']:+,} รายการ → รัน build_dashboard.py "
                  "เพื่ออัปเดตได้เลย")

    print("\n" + "=" * 66)
    print(f" สรุป: เชื่อมต่อได้ปกติ · SharePoint มี {total:,} รายการ")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())
