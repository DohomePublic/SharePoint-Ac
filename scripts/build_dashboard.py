#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_dashboard.py
ดึงข้อมูลจาก SharePoint List "AC-Data Request for approval of PO"
ผ่าน Microsoft Graph API แล้วสร้างไฟล์ index.html (Dashboard)

Run บน GitHub Actions:
    python scripts/build_dashboard.py

Preview ด้วยไฟล์ CSV (ไม่ต้องต่อ Graph):
    python scripts/build_dashboard.py --csv data.csv
"""

import argparse
import html
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

TZ = timezone(timedelta(hours=7))  # Asia/Bangkok

SITE_HOST = "dohomegroup.sharepoint.com"
SITE_PATH = "/sites/AC-Accounting"
LIST_NAME = "AC-Data Request for approval of PO"

# ---- mapping: key ที่ใช้ใน dashboard -> ชื่อ internal field ที่เป็นไปได้ ----
FIELDS = {
    "id":           ["ID", "id", "_ID"],
    "title":        ["Title", "LinkTitle"],
    "idno":         ["id_x0020_number", "idnumber", "id number", "id_number"],
    "user":         ["user_x0020_name", "username", "user name", "user_name"],
    "dept":         ["Department", "Department0", "Dept", "หน่วยงาน"],
    "pr":           ["PR_x0020_Number", "PRNumber"],
    "note":         ["Additional_x0020_Notes", "AdditionalNotes"],
    "head_name":    ["Name_x0020_Department_x0020_Head", "NameDepartmentHead"],
    "head_time":    ["Time_x0020_Department_x0020_Head", "TimeDepartmentHead"],
    "head_status":  ["Status_x0020_Department_x0020_Head", "StatusDepartmentHead"],
    "head_cmt":     ["Comment_x0020_Department_x0020_Head", "CommentDepartmentHead"],
    "proc_name":    ["Name_x0020_Head_x0020_of_x0020_Procurement_x0020_Center",
                     "NameHeadofProcurementCenter"],
    "proc_time":    ["Time_x0020_Head_x0020_of_x0020_Procurement_x0020_Center",
                     "TimeHeadofProcurementCenter"],
    "proc_status":  ["Status_x0020_Head_x0020_of_x0020_Procurement_x0020_Center",
                     "StatusHeadofProcurementCenter"],
    "proc_cmt":     ["Comment_x0020_Head_x0020_Procurement_x0020_Center",
                     "CommentHeadProcurementCenter"],
    "asset_name":   ["Name_x0020_Asset_x0020_Register", "NameAssetRegister"],
    "asset_time":   ["Time_x0020_Asset_x0020_Register", "TimeAssetRegister"],
    "asset_status": ["Status_x0020_Asset_x0020_Register", "StatusAssetRegister"],
    "asset_cmt":    ["Comment_x0020_Asset_x0020_", "Comment_x0020_Asset", "CommentAsset"],
    "status":       ["Status"],
    "site":         ["Site"],
    "email":        ["Email_x0020_User", "EmailUser"],
    "created":      ["Created"],
    "modified":     ["Modified"],
    "cby":          ["Author", "Created_x0020_By", "CreatedBy"],
    "mby":          ["Editor", "Modified_x0020_By", "ModifiedBy"],
    "att":          ["Attachments"],
    "ctype":        ["ContentType", "Content_x0020_Type"],
}

STATUS_DONE = "ดำเนินการเรียบร้อย"
STATUS_WAIT = "รอดำเนินการ"
STATUS_CANCEL = "ยกเลิก"


# --------------------------------------------------------------------------
# 1) ดึงข้อมูลจาก Microsoft Graph
# --------------------------------------------------------------------------
def get_token(tenant_id, client_id, client_secret):
    import requests
    r = requests.post(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        },
        timeout=60,
    )
    if r.status_code != 200:
        print(f"❌ ขอ token ไม่สำเร็จ ({r.status_code}): {r.text[:400]}", file=sys.stderr)
        r.raise_for_status()
    return r.json()["access_token"]


def graph_get(url, token):
    import requests
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=120)
    if r.status_code != 200:
        print(f"❌ Graph API error ({r.status_code}): {r.text[:400]}", file=sys.stderr)
        r.raise_for_status()
    return r.json()


def norm_key(s):
    """ทำให้ชื่อคอลัมน์เทียบกันได้: ตัด _x0020_ / ช่องว่าง / _ / ตัวพิมพ์"""
    s = str(s or "").replace("_x0020_", " ")
    return "".join(ch for ch in s.lower() if ch.isalnum())


def fetch_columns(site_id, list_id, token):
    """คืน dict: normalize(displayName หรือ internal name) -> internal name จริง"""
    try:
        data = graph_get(
            f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}"
            f"/columns?$top=300", token)
    except Exception as e:
        print(f"   ⚠ อ่าน /columns ไม่ได้ ({e}) — จะใช้การเดาชื่อคอลัมน์แทน",
              file=sys.stderr)
        return {}
    m = {}
    for c in data.get("value", []):
        internal = c.get("name") or ""
        if not internal:
            continue
        for label in (c.get("displayName"), internal):
            k = norm_key(label)
            if k and k not in m:
                m[k] = internal
    print(f"   อ่านชื่อคอลัมน์จากลิสต์ได้ {len(m):,} รายการ")
    return m


def fetch_items(token):
    site = graph_get(
        f"https://graph.microsoft.com/v1.0/sites/{SITE_HOST}:{SITE_PATH}", token)
    site_id = site["id"]

    lists = graph_get(
        f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists?$top=200", token)
    list_id = None
    for l in lists.get("value", []):
        if l.get("displayName", "").strip().lower() == LIST_NAME.lower():
            list_id = l["id"]
            break
    if not list_id:
        raise SystemExit(f"❌ ไม่พบ List ชื่อ '{LIST_NAME}' ใน site {SITE_PATH}")

    colmap = fetch_columns(site_id, list_id, token)

    url = (f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}"
           f"/items?expand=fields&$top=1000")
    rows, page = [], 0
    while url:
        data = graph_get(url, token)
        for it in data.get("value", []):
            f = dict(it.get("fields", {}) or {})
            # Graph คืนเลขที่รายการที่ระดับ item ด้วย — ใช้เป็น fallback ของ ID
            if not f.get("ID") and not f.get("id"):
                f["ID"] = it.get("id", "")
            rows.append(f)
        page += 1
        print(f"   ดึงข้อมูลหน้า {page} — สะสม {len(rows):,} รายการ")
        url = data.get("@odata.nextLink")
    return rows, colmap


def flat(v):
    if isinstance(v, dict):
        return (v.get("DisplayName") or v.get("displayName") or v.get("Email")
                or v.get("email") or v.get("LookupValue") or v.get("Label") or "")
    if isinstance(v, list):
        return ", ".join(str(flat(x)) for x in v if flat(x) != "")
    return v


def pick(f, names, colmap=None, nf=None):
    """หาค่าจาก field ตามชื่อที่เป็นไปได้หลายแบบ
    1) เทียบชื่อตรงตัว  2) เทียบผ่าน map displayName->internal  3) เทียบแบบ normalize"""
    for n in names:
        if n in f and f[n] not in (None, ""):
            v = f[n]
            if isinstance(v, dict):
                return v.get("DisplayName") or v.get("Email") or v.get("LookupValue") or ""
            if isinstance(v, list):
                return ", ".join(
                    (x.get("DisplayName") or x.get("Email") or "") if isinstance(x, dict)
                    else str(x) for x in v)
            return flat(v)
    if colmap:
        for n in names:
            real = colmap.get(norm_key(n))
            if real and f.get(real) not in (None, ""):
                return flat(f[real])
    if nf is None:
        nf = {norm_key(k): k for k in f}
    for n in names:
        real = nf.get(norm_key(n))
        if real and f.get(real) not in (None, ""):
            return flat(f[real])
    return ""


def normalize(fields_rows, colmap=None):
    out = []
    for f in fields_rows:
        nf = {norm_key(k): k for k in f}
        out.append({k: pick(f, names, colmap, nf) for k, names in FIELDS.items()})
    return out


def report_fields(recs, sample_keys=None):
    """เตือนถ้าคอลัมน์ไหนดึงมาแล้วว่างเกือบทั้งหมด"""
    if not recs:
        return
    n = len(recs)
    empty = [(k, sum(1 for r in recs if not str(r.get(k) or "").strip()))
             for k in FIELDS]
    bad = [(k, c) for k, c in empty if c >= n * 0.9]
    if not bad:
        print("   ✅ ดึงข้อมูลได้ครบทุกคอลัมน์")
        return
    print("\n   ⚠ คอลัมน์ต่อไปนี้ว่างเกือบทั้งหมด (อาจตั้งชื่อ internal name ไม่ตรง):",
          file=sys.stderr)
    for k, c in bad:
        print(f"      - {k:12s} ว่าง {c:,}/{n:,} แถว  (ลองชื่อ: {', '.join(FIELDS[k])})",
              file=sys.stderr)
    if sample_keys:
        print(f"\n   ชื่อคอลัมน์จริงที่ Graph ส่งกลับมา ({len(sample_keys)} คอลัมน์):",
              file=sys.stderr)
        print("      " + ", ".join(sorted(sample_keys)), file=sys.stderr)
        print("   👉 นำชื่อที่ถูกต้องไปใส่ใน FIELDS ด้านบนของสคริปต์นี้", file=sys.stderr)


# --------------------------------------------------------------------------
# 2) โหมด preview จาก CSV
# --------------------------------------------------------------------------
CSV_MAP = {
    "id": "_ID", "title": "Title", "idno": "id number", "user": "user name",
    "dept": "Department", "pr": "PR Number", "note": "Additional Notes",
    "head_name": "Name Department Head", "head_time": "Time Department Head",
    "head_status": "Status Department Head", "head_cmt": "Comment Department Head",
    "proc_name": "Name Head of Procurement Center",
    "proc_time": "Time Head of Procurement Center",
    "proc_status": "Status Head of Procurement Center",
    "proc_cmt": "Comment Head Procurement Center",
    "asset_name": "Name Asset Register", "asset_time": "Time Asset Register",
    "asset_status": "Status Asset Register", "asset_cmt": "Comment Asset ",
    "status": "Status", "site": "Site", "email": "Email User",
    "created": "Created", "modified": "Modified",
    "cby": "Created By", "mby": "Modified By",
    "att": "_HasAttachments", "ctype": "Content Type",
}


def load_csv(path):
    import csv as _csv
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for r in _csv.DictReader(fh):
            rows.append({k: (r.get(v) or "").strip() for k, v in CSV_MAP.items()})
    return rows


# --------------------------------------------------------------------------
# 3) helper
# --------------------------------------------------------------------------
def fmt_dt(s):
    if not s:
        return ""
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(TZ)
        return d.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(s)


def iso_date(s):
    """คืนค่า YYYY-MM-DD (เวลาไทย) สำหรับใช้กรองช่วงวันที่"""
    if not s:
        return ""
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(TZ)
        return d.strftime("%Y-%m-%d")
    except Exception:
        return str(s)[:10]


def sort_key(r):
    try:
        return datetime.fromisoformat(str(r.get("created")).replace("Z", "+00:00"))
    except Exception:
        return datetime(1900, 1, 1, tzinfo=timezone.utc)


def clean(v):
    v = str(v if v is not None else "").strip()
    if v.lower() in ("nan", "none", "nat"):
        return ""
    return v


def clean_pr(v):
    v = clean(v)
    if v.endswith(".0"):
        v = v[:-2]
    try:
        if "e+" in v.lower():
            return str(int(float(v)))
    except Exception:
        pass
    return v


# --------------------------------------------------------------------------
# 4) สร้าง HTML
# --------------------------------------------------------------------------
NO_DEPT = "(ไม่ระบุหน่วยงาน)"


def backfill_dept(rows):
    """คอลัมน์ Department ในลิสต์ต้นทางว่างอยู่จำนวนมาก
    -> เติมจากคำขออื่นของพนักงานคนเดียวกัน (รหัสพนักงาน > อีเมล > ชื่อ)
    คืนค่า (จำนวนที่เติมได้, จำนวนที่ยังว่าง)"""
    from collections import defaultdict
    maps = [defaultdict(Counter) for _ in range(3)]
    keys = ("idno", "email", "user")
    for r in rows:
        d = clean(r.get("dept"))
        if not d:
            continue
        for m, k in zip(maps, keys):
            kv = clean(r.get(k))
            if kv:
                m[kv][d] += 1

    filled = blank = 0
    for r in rows:
        if clean(r.get("dept")):
            r["dept_guess"] = ""
            continue
        got = ""
        for m, k in zip(maps, keys):
            kv = clean(r.get(k))
            if kv and m.get(kv):
                got = m[kv].most_common(1)[0][0]
                break
        if got:
            r["dept"] = got
            r["dept_guess"] = "1"
            filled += 1
        else:
            r["dept"] = NO_DEPT
            r["dept_guess"] = "?"
            blank += 1
    return filled, blank


def build_html(rows):
    now = datetime.now(TZ)
    rows = sorted(rows, key=sort_key, reverse=True)

    n_fill, n_blank = backfill_dept(rows)
    if n_fill or n_blank:
        print(f"   หน่วยงาน: เติมให้อัตโนมัติ {n_fill:,} รายการ · "
              f"ยังไม่ทราบ {n_blank:,} รายการ (แสดงเป็น '{NO_DEPT}')")

    recs = []
    for r in rows:
        recs.append({
            "id": clean(r.get("id")),
            "title": clean(r.get("title")),
            "idno": clean_pr(r.get("idno")),
            "user": clean(r.get("user")),
            "dept": clean(r.get("dept")),
            "dg": r.get("dept_guess", ""),
            "pr": clean_pr(r.get("pr")),
            "note": clean(r.get("note")),
            "status": clean(r.get("status")) or "-",
            "site": clean(r.get("site")),
            "email": clean(r.get("email")),
            "cby": clean(r.get("cby")), "mby": clean(r.get("mby")),
            "att": "มีไฟล์แนบ" if str(r.get("att")).strip().lower() in ("true", "1", "yes")
                   else "ไม่มีไฟล์แนบ",
            "ctype": clean(r.get("ctype")) or "Item",
            "created": fmt_dt(r.get("created")),
            "modified": fmt_dt(r.get("modified")),
            "cd": iso_date(r.get("created")),
            "hn": clean(r.get("head_name")), "ht": clean(r.get("head_time")),
            "hs": clean(r.get("head_status")), "hc": clean(r.get("head_cmt")),
            "pn": clean(r.get("proc_name")), "pt": clean(r.get("proc_time")),
            "ps": clean(r.get("proc_status")), "pc": clean(r.get("proc_cmt")),
            "an": clean(r.get("asset_name")), "at": clean(r.get("asset_time")),
            "as": clean(r.get("asset_status")), "ac": clean(r.get("asset_cmt")),
        })

    STAGES = [
        ("hs", "hn", "หัวหน้าสายงาน"),
        ("ps", "pn", "ศูนย์จัดซื้อทรัพย์สิน"),
        ("as", "an", "บัญชีทรัพย์สิน"),
    ]
    NO_OWNER = "(ยังไม่ระบุผู้รับผิดชอบ)"
    today = now.date()
    for r in recs:
        r["stg"] = ""
        r["own"] = ""
        r["age"] = 0
        if r["status"] == STATUS_WAIT:
            for sk, nk, label in STAGES:
                if (r.get(sk) or "").startswith("รอ"):
                    r["stg"] = label
                    r["own"] = (r.get(nk) or "").strip() or NO_OWNER
                    break
            if not r["stg"]:
                r["stg"] = "รอดำเนินการ"
                r["own"] = (r.get("hn") or "").strip() or NO_OWNER
            try:
                d = datetime.strptime(r["cd"], "%Y-%m-%d").date()
                r["age"] = max(0, (today - d).days)
            except Exception:
                r["age"] = 0

    total = len(recs)
    c_status = Counter(r["status"] for r in recs)
    done = c_status.get(STATUS_DONE, 0)
    wait = c_status.get(STATUS_WAIT, 0)
    cancel = c_status.get(STATUS_CANCEL, 0)

    dept = Counter(r["dept"] for r in recs if r["dept"])
    site = Counter(r["site"] for r in recs if r["site"])

    month = Counter()
    for r in recs:
        k = r["cd"][:7]
        if len(k) == 7:
            month[k] += 1
    months = sorted(month)[-12:]
    month_values = [month[m] for m in months]

    all_dates = sorted(r["cd"] for r in recs if len(r["cd"]) == 10)
    date_min = all_dates[0] if all_dates else ""
    date_max = all_dates[-1] if all_dates else ""

    data_json = json.dumps(recs, ensure_ascii=False)

    def bars(pairs):
        if not pairs:
            return ""
        mx = max(v for _, v in pairs) or 1
        return "".join(
            f'<div class="bar-row"><span class="bar-lb">{html.escape(k)}</span>'
            f'<span class="bar-track"><span class="bar-fill" style="width:{v/mx*100:.1f}%"></span></span>'
            f'<span class="bar-val">{v:,}</span></div>' for k, v in pairs)

    return f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PO Approval Dashboard | DOHOME</title>
<link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{{
  --o50:#fff7ed; --o100:#ffedd5; --o200:#fed7aa; --o300:#fdba74;
  --o400:#fb923c; --o500:#f97316; --o600:#ea580c; --o700:#c2410c; --o800:#9a3412;
  --ink:#431407; --muted:#9a6a4a; --line:#fde3c7;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Sarabun',sans-serif;background:var(--o50);color:var(--ink)}}
header{{background:linear-gradient(135deg,var(--o500),var(--o700));color:#fff;padding:24px 28px;
  box-shadow:0 4px 18px rgba(234,88,12,.25)}}
header h1{{font-size:22px;font-weight:700}}
header p{{opacity:.92;font-size:13px;margin-top:5px}}
.wrap{{max-width:1400px;margin:0 auto;padding:22px 28px 60px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px}}
.card{{background:#fff;border-radius:16px;padding:18px 20px;border:1px solid var(--line);
  box-shadow:0 2px 12px rgba(234,88,12,.08);border-top:4px solid var(--o400)}}
.card .lb{{font-size:13px;color:var(--muted)}}
.card .val{{font-size:31px;font-weight:700;margin-top:6px}}
.c-all{{border-top-color:var(--o600)}} .c-all .val{{color:var(--o700)}}
.c-done{{border-top-color:#16a34a}} .c-done .val{{color:#15803d}}
.c-wait{{border-top-color:var(--o400)}} .c-wait .val{{color:var(--o600)}}
.c-cancel{{border-top-color:#dc2626}} .c-cancel .val{{color:#b91c1c}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:18px}}
@media(max-width:960px){{.grid2{{grid-template-columns:1fr}}}}
.panel{{background:#fff;border-radius:16px;padding:18px 20px;border:1px solid var(--line);
  box-shadow:0 2px 12px rgba(234,88,12,.08)}}
.panel h2{{font-size:15px;font-weight:600;margin-bottom:14px;color:var(--o800)}}
.sub{{font-weight:400;color:var(--muted);font-size:12px}}
.bar-row{{display:flex;align-items:center;gap:10px;margin-bottom:8px;font-size:13px}}
.bar-lb{{width:230px;flex:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.bar-track{{flex:1;height:10px;background:var(--o100);border-radius:6px;overflow:hidden}}
.bar-fill{{display:block;height:100%;background:linear-gradient(90deg,var(--o400),var(--o600))}}
.bar-val{{width:60px;text-align:right;color:var(--o700);font-weight:600}}
.tools{{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 10px;align-items:center}}
input,select{{font-family:inherit;font-size:14px;padding:9px 12px;border:1px solid var(--o200);
  border-radius:10px;background:#fff;color:var(--ink)}}
input:focus,select:focus{{outline:2px solid var(--o300);border-color:var(--o400)}}
#q{{flex:1;min-width:240px}}
.daterow{{margin-top:0}}
.daterow input[type=date]{{min-width:150px}}
.dl{{font-size:13px;color:var(--muted);font-weight:600}}
.qb{{font-family:inherit;font-size:13px;padding:8px 14px;border:1px solid var(--o200);
  border-radius:10px;background:#fff;color:var(--o700);cursor:pointer}}
.qb:hover{{background:var(--o100)}}
.qb.on{{background:var(--o600);border-color:var(--o600);color:#fff}}
.qb.clr{{color:#b91c1c;border-color:#fecaca}}
table{{width:100%;border-collapse:collapse;background:#fff;font-size:13px}}
th{{background:var(--o100);text-align:left;padding:11px 10px;color:var(--o800);
  border-bottom:2px solid var(--o200);position:sticky;top:0;z-index:1}}
td{{padding:10px;border-bottom:1px solid var(--line);vertical-align:top}}
tbody tr:hover{{background:var(--o50)}}
.tabs{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}}
.tab{{border:1px solid var(--line);background:#fff;color:var(--o800);border-radius:999px;
  padding:6px 14px;font-family:inherit;font-size:13px;cursor:pointer}}
.tab.on{{background:var(--o600);color:#fff;border-color:var(--o600)}}
.otbl{{width:100%;border-collapse:collapse;font-size:13px}}
.otbl th{{text-align:left;padding:8px 10px;color:var(--muted);font-weight:600;
  border-bottom:1px solid var(--line);position:sticky;top:0;background:#fff;z-index:1}}
.otbl td{{padding:8px 10px;border-bottom:1px solid var(--o50)}}
.otbl tr[data-o]{{cursor:pointer}}
.otbl tr[data-o]:hover{{background:var(--o50)}}
.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
.mini{{height:8px;border-radius:6px;background:var(--o50);overflow:hidden;min-width:80px}}
.mini>i{{display:block;height:100%;background:var(--o500);border-radius:6px}}
.mini-r>i{{background:#dc2626}}
.mini-g>i{{background:#16a34a}}
.hint{{font-size:12px;color:var(--muted);margin-top:10px}}
.gs{{display:inline-block;font-size:10px;padding:0 5px;border-radius:5px;
  background:var(--o100);color:var(--o700);margin-left:5px;vertical-align:middle;cursor:help}}
.gq{{color:#c9b0a0;font-style:italic}}
.stg{{display:inline-block;font-size:11px;padding:1px 8px;border-radius:999px;
  background:var(--o50);color:var(--o800);margin-left:4px;white-space:nowrap}}
.old{{color:#dc2626;font-weight:700}}
.owner-wrap{{max-height:430px;overflow:auto;border-radius:12px}}
.osum{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px}}
.ochip{{background:var(--o50);border:1px solid var(--line);border-radius:12px;
  padding:8px 14px;font-size:13px;color:var(--o800)}}
.ochip b{{font-size:17px;color:var(--o700);margin-left:6px}}
.tools{{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:0 0 10px}}
.tbtn{{font-family:inherit;font-size:13px;padding:7px 14px;border:1px solid var(--o200);
  background:#fff;color:var(--o700);border-radius:10px;cursor:pointer;white-space:nowrap}}
.tbtn:hover{{background:var(--o50)}}
.tbtn.on{{background:var(--o600);color:#fff;border-color:var(--o600)}}
#tb tr{{cursor:pointer}}
#tb tr:hover{{background:var(--o50)}}
.rawt{{width:100%;border-collapse:collapse;font-size:13px}}
.rawt th{{text-align:left;width:270px;padding:7px 10px;color:var(--muted);font-weight:600;
  background:var(--o50);border:1px solid var(--line);vertical-align:top;word-break:break-word}}
.rawt td{{padding:7px 10px;border:1px solid var(--line);word-break:break-word;
  white-space:pre-wrap;color:var(--ink)}}
.mnav{{display:flex;gap:8px;align-items:center}}
.mnav button{{background:rgba(255,255,255,.2);border:0;color:#fff;font-size:13px;
  padding:6px 12px;border-radius:9px;cursor:pointer;font-family:inherit}}
.mnav button:hover:not(:disabled){{background:rgba(255,255,255,.35)}}
.mnav button:disabled{{opacity:.35;cursor:default}}
.mnav .pos{{font-size:12px;opacity:.9;white-space:nowrap}}
.cellwrap{{max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.tbl-wrap{{max-height:640px;overflow:auto;border-radius:16px;border:1px solid var(--line);
  box-shadow:0 2px 12px rgba(234,88,12,.08)}}
.pill{{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;white-space:nowrap}}
.p-done{{background:#dcfce7;color:#15803d}} .p-wait{{background:var(--o100);color:var(--o700)}}
.p-cancel{{background:#fee2e2;color:#b91c1c}} .p-na{{background:#f1f5f9;color:#64748b}}
.p-ok{{background:#dcfce7;color:#15803d}} .p-no{{background:#fee2e2;color:#b91c1c}}
.p-pend{{background:var(--o100);color:var(--o700)}}
.btn-view{{font-family:inherit;font-size:12px;font-weight:600;padding:5px 14px;border:0;
  border-radius:8px;background:var(--o500);color:#fff;cursor:pointer;white-space:nowrap}}
.btn-view:hover{{background:var(--o700)}}
footer{{text-align:center;color:var(--muted);font-size:12px;margin-top:26px}}

/* ---------- Modal รายละเอียด ---------- */
.ov{{position:fixed;inset:0;background:rgba(67,20,7,.55);display:none;
  align-items:center;justify-content:center;padding:20px;z-index:50}}
.ov.show{{display:flex}}
.modal{{background:#fff;border-radius:18px;max-width:900px;width:100%;max-height:90vh;
  overflow:auto;box-shadow:0 20px 60px rgba(67,20,7,.35)}}
.mh{{background:linear-gradient(135deg,var(--o500),var(--o700));color:#fff;padding:18px 24px;
  display:flex;justify-content:space-between;align-items:flex-start;gap:16px;
  position:sticky;top:0;z-index:2}}
.mh h3{{font-size:18px;font-weight:700}}
.mh .mid{{font-size:12px;opacity:.9;margin-top:3px}}
.mx{{background:rgba(255,255,255,.2);border:0;color:#fff;font-size:20px;line-height:1;
  width:34px;height:34px;border-radius:9px;cursor:pointer;flex:none}}
.mx:hover{{background:rgba(255,255,255,.35)}}
.mb{{padding:22px 24px}}
.mb h4{{font-size:14px;color:var(--o800);margin:20px 0 10px;padding-bottom:7px;
  border-bottom:2px solid var(--o100)}}
.mb h4:first-child{{margin-top:0}}
.kv{{display:grid;grid-template-columns:150px 1fr;gap:8px 14px;font-size:14px}}
.kv dt{{color:var(--muted);font-weight:600}}
.kv dd{{color:var(--ink);word-break:break-word}}
@media(max-width:640px){{.kv{{grid-template-columns:1fr}}.kv dt{{margin-top:8px}}}}
.step{{display:flex;gap:14px;padding:14px;border:1px solid var(--line);border-radius:12px;
  margin-bottom:10px;background:var(--o50)}}
.step .no{{flex:none;width:30px;height:30px;border-radius:50%;background:var(--o500);color:#fff;
  display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px}}
.step .bd{{flex:1;font-size:13px}}
.step .rl{{font-weight:600;color:var(--o800);margin-bottom:4px}}
.step .mt{{color:var(--muted);margin-top:3px}}
.step .cm{{margin-top:7px;padding:8px 11px;background:#fff;border-left:3px solid var(--o300);
  border-radius:0 8px 8px 0;color:var(--ink)}}
.note-box{{background:var(--o50);border:1px solid var(--line);border-radius:12px;
  padding:12px 14px;font-size:14px;white-space:pre-wrap}}
</style>
</head>
<body>
<header>
  <h1>📋 Dashboard คำขออนุมัติ PO</h1>
  <p>อัปเดตล่าสุด: {now.strftime('%d/%m/%Y %H:%M')} น. (เวลาไทย) · ข้อมูลทั้งหมด {total:,} รายการ</p>
</header>
<div class="wrap">
  <div class="cards">
    <div class="card c-all"><div class="lb">รายการทั้งหมด</div><div class="val" id="k-all">{total:,}</div></div>
    <div class="card c-done"><div class="lb">ดำเนินการเรียบร้อย</div><div class="val" id="k-done">{done:,}</div></div>
    <div class="card c-wait"><div class="lb">รอดำเนินการ</div><div class="val" id="k-wait">{wait:,}</div></div>
    <div class="card c-cancel"><div class="lb">ยกเลิก</div><div class="val" id="k-cancel">{cancel:,}</div></div>
  </div>

  <div class="tools">
    <input id="q" placeholder="🔍 ค้นหา: ชื่อผู้ขอ / เลข PR / รหัสพนักงาน / หน่วยงาน / สาขา / หมายเหตุ">
    <select id="fs"><option value="">สถานะทั้งหมด</option>
      <option>{STATUS_DONE}</option><option>{STATUS_WAIT}</option><option>{STATUS_CANCEL}</option></select>
    <select id="fd"><option value="">หน่วยงานทั้งหมด</option>
      {''.join(f'<option>{html.escape(k)}</option>' for k, _ in dept.most_common())}</select>
    <select id="fsite"><option value="">สาขาทั้งหมด</option>
      {''.join(f'<option>{html.escape(k)}</option>' for k, _ in site.most_common())}</select>
  </div>

  <div class="tools daterow">
    <span class="dl">📅 วันที่สร้าง</span>
    <input type="date" id="d1" min="{date_min}" max="{date_max}" title="ตั้งแต่วันที่">
    <span class="dl">ถึง</span>
    <input type="date" id="d2" min="{date_min}" max="{date_max}" title="ถึงวันที่">
    <button class="qb" data-r="7">7 วัน</button>
    <button class="qb" data-r="30">30 วัน</button>
    <button class="qb" data-r="90">90 วัน</button>
    <button class="qb" data-r="tm">เดือนนี้</button>
    <button class="qb" data-r="lm">เดือนที่แล้ว</button>
    <button class="qb" data-r="ty">ปีนี้</button>
    <button class="qb clr" data-r="all">ล้างตัวกรอง</button>
  </div>
  <div id="cnt" style="font-size:13px;color:var(--muted);margin:4px 0 12px"></div>

  <div class="grid2">
    <div class="panel"><h2>สัดส่วนสถานะ <span class="sub">(ตามตัวกรอง)</span></h2><canvas id="pie" height="190"></canvas></div>
    <div class="panel"><h2>จำนวนคำขอรายเดือน <span class="sub">(ตามตัวกรอง, 12 เดือนล่าสุด)</span></h2><canvas id="line" height="190"></canvas></div>
  </div>

  <div class="grid2">
    <div class="panel"><h2>Top 10 หน่วยงาน</h2><div id="bd">{bars(dept.most_common(10))}</div></div>
    <div class="panel"><h2>Top 10 สาขา / Site</h2><div id="bs">{bars(site.most_common(10))}</div></div>
  </div>
  <div style="height:18px"></div>

  <div class="panel">
    <h2>👥 ภาระงานผู้อนุมัติ / เจ้าหน้าที่จัดซื้อ <span class="sub">(ตามตัวกรอง)</span></h2>
    <div class="tabs">
      <button class="tab on" data-t="pend">⏳ ใครค้างงาน</button>
      <button class="tab" data-t="work">✅ ใครรับงานแล้ว</button>
      <button class="tab" data-t="age">⏱ อายุงานค้าง</button>
    </div>
    <div id="osum" class="osum"></div>
    <div class="owner-wrap"><div id="ownerbox"></div></div>
    <div class="hint" id="ownerhint"></div>
  </div>
  <div style="height:18px"></div>

  <div class="tools">
    <button class="tbtn" id="btn-all">📄 แสดงทุกรายการ</button>
    <button class="tbtn" id="btn-col">🔳 แสดงทุกคอลัมน์</button>
    <button class="tbtn" id="btn-csv">⬇ ดาวน์โหลด CSV (ตามตัวกรอง)</button>
    <span style="font-size:12px;color:var(--muted)">💡 คลิกที่แถวใดก็ได้เพื่อดูรายละเอียดทั้งหมด</span>
  </div>
  <div class="tbl-wrap">
    <table>
      <thead id="th"></thead>
      <tbody id="tb"></tbody>
    </table>
  </div>
  <footer>Auto-generated by GitHub Actions · build_dashboard.py · DOHOME BI HQ</footer>
</div>

<div class="ov" id="ov">
  <div class="modal" role="dialog" aria-modal="true">
    <div class="mh">
      <div><h3 id="m-title">รายละเอียดคำขอ</h3><div class="mid" id="m-sub"></div></div>
      <div class="mnav">
        <button id="m-prev" title="ก่อนหน้า (←)">◀</button>
        <span class="pos" id="m-pos"></span>
        <button id="m-next" title="ถัดไป (→)">▶</button>
        <button class="mx" id="m-close" title="ปิด (Esc)">✕</button>
      </div>
    </div>
    <div class="mb" id="m-body"></div>
  </div>
</div>

<script>
const DATA = {data_json};
const DMIN = "{date_min}", DMAX = "{date_max}";
const S_DONE="{STATUS_DONE}", S_WAIT="{STATUS_WAIT}", S_CANCEL="{STATUS_CANCEL}";
const PAGE = 300; let shown = PAGE, cur = DATA, pie, line;

const esc = s => (s??"").toString().replace(/[&<>"]/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]));
const iso = d => new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10);
const pill = s => s===S_DONE ? "p-done" : s===S_WAIT ? "p-wait" : s===S_CANCEL ? "p-cancel" : "p-na";
const apr  = s => !s ? "p-na" : s.indexOf("ไม่อนุมัติ")>=0 ? "p-no"
                 : s.indexOf("อนุมัติ")>=0 ? "p-ok" : "p-pend";
const dash = v => (v && v.toString().trim()) ? esc(v) : '<span style="color:#c9b0a0">—</span>';
const NO_DEPT = {json.dumps(NO_DEPT, ensure_ascii=False)};
const deptCell = r => r.dg==='?' ? `<span class="gq">${{NO_DEPT}}</span>`
  : r.dg==='1' ? `${{esc(r.dept)}}<span class="gs" title="ต้นทางไม่ได้ระบุหน่วยงาน — อนุมานจากคำขออื่นของพนักงานคนเดียวกัน">≈</span>`
  : dash(r.dept);

/* ---------- ตาราง ---------- */
let ALLCOL = false;
const MORE = [
  ['เลขที่อ้างอิง', r=>dash(r.title)],
  ['รหัสพนักงาน',  r=>dash(r.idno)],
  ['อีเมล',        r=>dash(r.email)],
  ['หมายเหตุ',     r=>`<div class="cellwrap" title="${{esc(r.note)}}">${{dash(r.note)}}</div>`],
  ['หัวหน้าสายงาน', r=>dash(r.hn)],
  ['สถานะขั้น 1',  r=>`<span class="pill ${{apr(r.hs)}}">${{esc(r.hs||'-')}}</span>`],
  ['ศูนย์จัดซื้อ',  r=>dash(r.pn)],
  ['สถานะขั้น 2',  r=>`<span class="pill ${{apr(r.ps)}}">${{esc(r.ps||'-')}}</span>`],
  ['บัญชีทรัพย์สิน', r=>dash(r.an)],
  ['สถานะขั้น 3',  r=>`<span class="pill ${{apr(r['as'])}}">${{esc(r['as']||'-')}}</span>`],
  ['แก้ไขล่าสุด',   r=>dash(r.modified)],
  ['ผู้สร้างรายการ', r=>dash(r.cby)],
  ['ไฟล์แนบ',      r=>dash(r.att)],
];
function render(){{
  document.getElementById('th').innerHTML = '<tr><th>เลขที่</th><th>วันที่สร้าง</th>' +
    '<th>ผู้ขอ</th><th>หน่วยงาน</th><th>PR Number</th><th>สาขา</th><th>สถานะ</th>' +
    (ALLCOL ? MORE.map(c=>`<th>${{c[0]}}</th>`).join('') : '') +
    '<th style="width:80px">รายละเอียด</th></tr>';
  document.getElementById('tb').innerHTML = cur.slice(0,shown).map((r,i)=>`<tr data-i="${{i}}">
    <td>${{dash(r.id)}}</td><td>${{dash(r.created)}}</td><td>${{dash(r.user)}}</td>
    <td>${{deptCell(r)}}</td><td>${{dash(r.pr)}}</td><td>${{dash(r.site)}}</td>
    <td><span class="pill ${{pill(r.status)}}">${{esc(r.status)}}</span>${{r.stg?`<br><span class="stg">⏳ ${{esc(r.own)}} · ${{r.age}} วัน</span>`:''}}</td>
    ${{ALLCOL ? MORE.map(c=>`<td>${{c[1](r)}}</td>`).join('') : ''}}
    <td><button class="btn-view" data-i="${{i}}">👁 ดู</button></td></tr>`).join('');
  const d1=document.getElementById('d1').value, d2=document.getElementById('d2').value;
  const rng = (d1||d2) ? ` · ช่วงวันที่ ${{d1||DMIN}} ถึง ${{d2||DMAX}}` : '';
  document.getElementById('cnt').textContent =
    `แสดง ${{Math.min(shown,cur.length).toLocaleString()}} จาก ${{cur.length.toLocaleString()}} รายการ${{rng}}`;
  const ba = document.getElementById('btn-all');
  ba.textContent = shown >= cur.length
    ? `📄 แสดงครบทุกรายการแล้ว (${{cur.length.toLocaleString()}})`
    : `📄 แสดงทุกรายการ (${{cur.length.toLocaleString()}})`;
  ba.disabled = shown >= cur.length;
  ba.classList.toggle('on', shown >= cur.length && cur.length > 0);
}}

/* ---------- Modal รายละเอียด ---------- */

/* ---------- ข้อมูลดิบครบทุกคอลัมน์ ---------- */
const RAWF = [
  ['_ID (เลขที่รายการ)','id'], ['Title (เลขที่อ้างอิง)','title'],
  ['id number (รหัสพนักงาน)','idno'], ['user name (ผู้ขออนุมัติ)','user'],
  ['Department (หน่วยงาน)','dept'], ['PR Number','pr'],
  ['Additional Notes (หมายเหตุ)','note'], ['Status (สถานะรวม)','status'],
  ['Site (สาขา)','site'], ['Email User (อีเมล)','email'],
  ['Name Department Head','hn'], ['Time Department Head','ht'],
  ['Status Department Head','hs'], ['Comment Department Head','hc'],
  ['Name Head of Procurement Center','pn'], ['Time Head of Procurement Center','pt'],
  ['Status Head of Procurement Center','ps'], ['Comment Head Procurement Center','pc'],
  ['Name Asset Register','an'], ['Time Asset Register','at'],
  ['Status Asset Register','as'], ['Comment Asset','ac'],
  ['Created (วันที่สร้าง)','created'], ['Created By (ผู้สร้าง)','cby'],
  ['Modified (แก้ไขล่าสุด)','modified'], ['Modified By (ผู้แก้ไข)','mby'],
  ['Content Type','ctype'], ['Attachments (ไฟล์แนบ)','att'],
];
function rawTable(r){{
  return '<table class="rawt"><tbody>' + RAWF.map(f=>
    `<tr><th>${{esc(f[0])}}</th><td>${{dash(r[f[1]])}}</td></tr>`).join('') + '</tbody></table>';
}}

function step(no, role, name, time, status, comment){{
  if(!name && !time && !status) return '';
  return `<div class="step"><div class="no">${{no}}</div><div class="bd">
    <div class="rl">${{esc(role)}}</div>
    <div>ผู้พิจารณา: <b>${{dash(name)}}</b>
      <span class="pill ${{apr(status)}}" style="margin-left:6px">${{esc(status||'-')}}</span></div>
    <div class="mt">⏱ ${{dash(time)}}</div>
    ${{comment ? `<div class="cm">💬 ${{esc(comment)}}</div>` : ''}}
  </div></div>`;
}}
let MIDX = -1;
function openDetail(r, i){{
  if(typeof i === 'number') MIDX = i; else MIDX = cur.indexOf(r);
  const P = document.getElementById('m-prev'), N = document.getElementById('m-next');
  document.getElementById('m-pos').textContent =
    (MIDX>=0) ? `${{(MIDX+1).toLocaleString()}} / ${{cur.length.toLocaleString()}}` : '';
  P.disabled = !(MIDX>0); N.disabled = !(MIDX>=0 && MIDX<cur.length-1);
  document.getElementById('m-title').textContent = 'คำขออนุมัติ PO เลขที่ ' + (r.id||'-');
  document.getElementById('m-sub').textContent =
    (r.user||'-') + ' · ' + (r.dept||'-') + ' · สร้างเมื่อ ' + (r.created||'-');
  document.getElementById('m-body').innerHTML = `
    <h4>ข้อมูลคำขอ</h4>
    <dl class="kv">
      <dt>สถานะ</dt><dd><span class="pill ${{pill(r.status)}}">${{esc(r.status)}}</span></dd>
      ${{r.stg?`<dt>ค้างที่</dt><dd><b>${{esc(r.stg)}}</b> · ผู้รับผิดชอบ <b>${{esc(r.own)}}</b> · ค้างมาแล้ว <span class="old">${{r.age}}</span> วัน</dd>`:''}}
      <dt>เลขที่รายการ</dt><dd>${{dash(r.id)}}</dd>
      <dt>เลขที่อ้างอิง</dt><dd>${{dash(r.title)}}</dd>
      <dt>PR Number</dt><dd><b>${{dash(r.pr)}}</b></dd>
      <dt>ผู้ขออนุมัติ</dt><dd>${{dash(r.user)}}</dd>
      <dt>รหัสพนักงาน</dt><dd>${{dash(r.idno)}}</dd>
      <dt>อีเมล</dt><dd>${{dash(r.email)}}</dd>
      <dt>หน่วยงาน</dt><dd>${{deptCell(r)}}${{r.dg==='1'
        ? '<div style="font-size:12px;color:var(--muted);margin-top:3px">'
          + '≈ ต้นทางไม่ได้ระบุหน่วยงาน ระบบอนุมานจากคำขออื่นของพนักงานคนนี้</div>'
        : r.dg==='?'
        ? '<div style="font-size:12px;color:var(--muted);margin-top:3px">'
          + 'ไม่พบข้อมูลหน่วยงานของพนักงานคนนี้ในลิสต์</div>' : ''}}</dd>
      <dt>สาขา / Site</dt><dd>${{dash(r.site)}}</dd>
      <dt>วันที่สร้าง</dt><dd>${{dash(r.created)}}</dd>
      <dt>แก้ไขล่าสุด</dt><dd>${{dash(r.modified)}}</dd>
    </dl>
    <h4>รายละเอียด / หมายเหตุเพิ่มเติม</h4>
    <div class="note-box">${{r.note ? esc(r.note) : 'ไม่มีข้อมูล'}}</div>
    <h4>ลำดับการอนุมัติ</h4>
    ${{ step(1,'หัวหน้าสายงาน / ผู้จัดการแผนก', r.hn, r.ht, r.hs, r.hc)
      + step(2,'ศูนย์จัดซื้อทรัพย์สิน', r.pn, r.pt, r.ps, r.pc)
      + step(3,'บัญชีทรัพย์สิน (Asset Register)', r.an, r.at, r['as'], r.ac)
      || '<div class="note-box">ยังไม่มีข้อมูลการอนุมัติ</div>' }}
    <h4>📋 ข้อมูลทั้งหมดของรายการนี้ (ทุกคอลัมน์ในลิสต์)</h4>
    ${{rawTable(r)}}
    <h4>🖥 ข้อมูลระบบ</h4>
    <dl class="kv">
      <dt>ประเภทเนื้อหา</dt><dd>${{dash(r.ctype)}}</dd>
      <dt>ผู้สร้างรายการ</dt><dd>${{dash(r.cby)}}</dd>
      <dt>ผู้แก้ไขล่าสุด</dt><dd>${{dash(r.mby)}}</dd>
      <dt>ไฟล์แนบ</dt><dd>${{dash(r.att)}}</dd>
    </dl>`;
  document.getElementById('ov').classList.add('show');
  document.body.style.overflow='hidden';
}}
function closeDetail(){{
  document.getElementById('ov').classList.remove('show');
  document.body.style.overflow='';
}}
document.getElementById('tb').addEventListener('click',e=>{{
  const tr = e.target.closest('tr[data-i]');
  if(tr) openDetail(cur[+tr.dataset.i], +tr.dataset.i);
}});
document.getElementById('m-prev').addEventListener('click',()=>{{
  if(MIDX>0) openDetail(cur[MIDX-1], MIDX-1);
}});
document.getElementById('m-next').addEventListener('click',()=>{{
  if(MIDX>=0 && MIDX<cur.length-1) openDetail(cur[MIDX+1], MIDX+1);
}});
document.addEventListener('keydown',e=>{{
  if(!document.getElementById('ov').classList.contains('show')) return;
  if(e.key==='ArrowLeft'  && MIDX>0) openDetail(cur[MIDX-1], MIDX-1);
  if(e.key==='ArrowRight' && MIDX>=0 && MIDX<cur.length-1) openDetail(cur[MIDX+1], MIDX+1);
}});

/* ---------- ปุ่มเครื่องมือ ---------- */
document.getElementById('btn-all').addEventListener('click',()=>{{
  shown = cur.length; render();
}});
document.getElementById('btn-col').addEventListener('click',e=>{{
  ALLCOL = !ALLCOL;
  e.target.classList.toggle('on', ALLCOL);
  e.target.textContent = ALLCOL ? '🔳 แสดงคอลัมน์ย่อ' : '🔳 แสดงทุกคอลัมน์';
  render();
}});
document.getElementById('btn-csv').addEventListener('click',()=>{{
  const q = v => '"' + (v==null?'':String(v)).replace(/"/g,'""') + '"';
  const head = RAWF.map(f=>f[0]);
  const body = cur.map(r=>RAWF.map(f=>q(r[f[1]])).join(','));
  const csv = '\\uFEFF' + head.map(q).join(',') + '\\r\\n' + body.join('\\r\\n');
  const url = URL.createObjectURL(new Blob([csv], {{type:'text/csv;charset=utf-8;'}}));
  const el = document.createElement('a');
  el.href = url; el.download = 'PO-approval-' + new Date().toISOString().slice(0,10) + '.csv';
  document.body.appendChild(el); el.click(); document.body.removeChild(el);
  URL.revokeObjectURL(url);
}});
document.getElementById('m-close').addEventListener('click',closeDetail);
document.getElementById('ov').addEventListener('click',e=>{{
  if(e.target.id==='ov') closeDetail();
}});
document.addEventListener('keydown',e=>{{ if(e.key==='Escape') closeDetail(); }});

/* ---------- สถิติ + กราฟ ---------- */
function mkbars(pairs){{
  if(!pairs.length) return '<div style="color:#c9b0a0;font-size:13px">ไม่มีข้อมูลในช่วงที่เลือก</div>';
  const mx = Math.max(...pairs.map(p=>p[1])) || 1;
  return pairs.map(([k,v])=>`<div class="bar-row"><span class="bar-lb" title="${{esc(k)}}">${{esc(k)}}</span>`
    +`<span class="bar-track"><span class="bar-fill" style="width:${{(v/mx*100).toFixed(1)}}%"></span></span>`
    +`<span class="bar-val">${{v.toLocaleString()}}</span></div>`).join('');
}}
const topN = (arr,key,n=10) => {{
  const m={{}}; arr.forEach(r=>{{const k=((r[key])||'').toString().trim(); if(k) m[k]=(m[k]||0)+1;}});
  return Object.entries(m).sort((a,b)=>b[1]-a[1]).slice(0,n);
}};
function stats(){{
  const c = s => cur.filter(r=>r.status===s).length;
  document.getElementById('k-all').textContent = cur.length.toLocaleString();
  document.getElementById('k-done').textContent = c(S_DONE).toLocaleString();
  document.getElementById('k-wait').textContent = c(S_WAIT).toLocaleString();
  document.getElementById('k-cancel').textContent = c(S_CANCEL).toLocaleString();
  document.getElementById('bd').innerHTML = mkbars(topN(cur,'dept'));
  document.getElementById('bs').innerHTML = mkbars(topN(cur,'site'));
  pie.data.datasets[0].data = [c(S_DONE), c(S_WAIT), c(S_CANCEL)]; pie.update();
  const m={{}}; cur.forEach(r=>{{const k=(r.cd||'').slice(0,7); if(k.length===7) m[k]=(m[k]||0)+1;}});
  const ks = Object.keys(m).sort().slice(-12);
  line.data.labels = ks; line.data.datasets[0].data = ks.map(k=>m[k]); line.update();
}}

/* ---------- แผงภาระงานผู้อนุมัติ / เจ้าหน้าที่จัดซื้อ ---------- */
let OTAB = 'pend', FOWN = '', FOWNMODE = '';
const STAGE_LIST = ['หัวหน้าสายงาน','ศูนย์จัดซื้อทรัพย์สิน','บัญชีทรัพย์สิน','รอดำเนินการ'];
const bar = (v,mx,cls) => `<div class="mini ${{cls||''}}"><i style="width:${{
  mx? Math.max(4, Math.round(v*100/mx)) : 0}}%"></i></div>`;

function ownerPending(rows){{
  const m = new Map();
  rows.forEach(r=>{{
    if(!r.stg) return;
    const k = r.own + '|' + r.stg;
    let o = m.get(k);
    if(!o){{ o = {{own:r.own, stg:r.stg, n:0, sum:0, mx:0, old:0}}; m.set(k,o); }}
    o.n++; o.sum += r.age; if(r.age>o.mx) o.mx = r.age; if(r.age>90) o.old++;
  }});
  return [...m.values()].sort((a,b)=>b.n-a.n);
}}

function ownerWorked(rows){{
  const m = new Map();
  const add = (name, stg, st) => {{
    name = (name||'').trim(); if(!name || !st) return;
    if(st.indexOf('รอ')===0) return;
    const k = name + '|' + stg;
    let o = m.get(k);
    if(!o){{ o = {{own:name, stg:stg, n:0, ok:0, no:0}}; m.set(k,o); }}
    o.n++;
    if(st.indexOf('ไม่อนุมัติ')>=0) o.no++; else if(st.indexOf('อนุมัติ')>=0) o.ok++;
  }};
  rows.forEach(r=>{{
    add(r.hn,'หัวหน้าสายงาน',r.hs);
    add(r.pn,'ศูนย์จัดซื้อทรัพย์สิน',r.ps);
    add(r.an,'บัญชีทรัพย์สิน',r['as']);
  }});
  return [...m.values()].sort((a,b)=>b.n-a.n);
}}

function renderOwner(){{
  const box = document.getElementById('ownerbox');
  const sum = document.getElementById('osum');
  const hint = document.getElementById('ownerhint');
  const pend = cur.filter(r=>r.stg);
  const fchip = FOWN ? `<div class="ochip fclr" style="cursor:pointer;background:var(--o600);
      color:#fff;border-color:var(--o600)">🔎 กำลังกรอง: ${{esc(FOWN)}} &nbsp;✕</div>` : '';

  if(OTAB==='pend'){{
    const L = ownerPending(cur);
    const byStage = {{}};
    pend.forEach(r=> byStage[r.stg] = (byStage[r.stg]||0)+1);
    sum.innerHTML = fchip + `<div class="ochip">ค้างทั้งหมด<b>${{pend.length.toLocaleString()}}</b></div>` +
      STAGE_LIST.filter(k=>byStage[k]).map(k=>
        `<div class="ochip">${{esc(k)}}<b>${{byStage[k].toLocaleString()}}</b></div>`).join('') +
      `<div class="ochip">ผู้รับผิดชอบ<b>${{L.length.toLocaleString()}}</b> คน</div>`;
    if(!L.length){{ box.innerHTML='<div class="hint">ไม่มีงานค้างในช่วงที่เลือก 🎉</div>';
                   hint.textContent=''; return; }}
    const mx = L[0].n;
    box.innerHTML = `<table class="otbl"><thead><tr>
      <th style="width:34px">#</th><th>ผู้รับผิดชอบ</th><th>ขั้นตอนที่ค้าง</th>
      <th class="num">ค้าง</th><th style="width:110px"></th>
      <th class="num">เฉลี่ย (วัน)</th><th class="num">นานสุด</th><th class="num">เกิน 90 วัน</th>
      </tr></thead><tbody>` + L.map((o,i)=>`<tr data-o="${{esc(o.own)}}">
      <td>${{i+1}}</td><td><b>${{esc(o.own)}}</b></td><td>${{esc(o.stg)}}</td>
      <td class="num"><b>${{o.n.toLocaleString()}}</b></td>
      <td>${{bar(o.n,mx,'mini-r')}}</td>
      <td class="num">${{Math.round(o.sum/o.n)}}</td>
      <td class="num">${{o.mx}}</td>
      <td class="num ${{o.old?'old':''}}">${{o.old.toLocaleString()}}</td></tr>`).join('') +
      '</tbody></table>';
    hint.textContent = '💡 คลิกที่แถวเพื่อกรองดูเฉพาะงานค้างของคนนั้น';

  }} else if(OTAB==='work'){{
    const L = ownerWorked(cur);
    sum.innerHTML = fchip + `<div class="ochip">ผู้พิจารณาที่รับงานแล้ว<b>${{L.length.toLocaleString()}}</b> คน</div>` +
      `<div class="ochip">รายการที่พิจารณาแล้ว<b>${{L.reduce((a,b)=>a+b.n,0).toLocaleString()}}</b></div>`;
    if(!L.length){{ box.innerHTML='<div class="hint">ไม่มีข้อมูลการพิจารณาในช่วงที่เลือก</div>';
                   hint.textContent=''; return; }}
    const mx = L[0].n;
    box.innerHTML = `<table class="otbl"><thead><tr>
      <th style="width:34px">#</th><th>ผู้พิจารณา</th><th>ขั้นตอน</th>
      <th class="num">พิจารณาแล้ว</th><th style="width:110px"></th>
      <th class="num">อนุมัติ</th><th class="num">ไม่อนุมัติ</th>
      </tr></thead><tbody>` + L.map((o,i)=>`<tr data-o="${{esc(o.own)}}">
      <td>${{i+1}}</td><td><b>${{esc(o.own)}}</b></td><td>${{esc(o.stg)}}</td>
      <td class="num"><b>${{o.n.toLocaleString()}}</b></td>
      <td>${{bar(o.n,mx,'mini-g')}}</td>
      <td class="num">${{o.ok.toLocaleString()}}</td>
      <td class="num ${{o.no?'old':''}}">${{o.no.toLocaleString()}}</td></tr>`).join('') +
      '</tbody></table>';
    hint.textContent = '💡 คลิกที่แถวเพื่อค้นหารายการที่ผู้พิจารณาคนนั้นเกี่ยวข้อง';

  }} else {{
    const B = [['0–7 วัน',0,7],['8–30 วัน',8,30],['31–90 วัน',31,90],['เกิน 90 วัน',91,1e9]];
    const cnt = B.map(b=>pend.filter(r=>r.age>=b[1]&&r.age<=b[2]).length);
    const tot = pend.length;
    const avg = tot? Math.round(pend.reduce((a,r)=>a+r.age,0)/tot) : 0;
    const mxd = tot? Math.max(...pend.map(r=>r.age)) : 0;
    sum.innerHTML = fchip + `<div class="ochip">งานค้าง<b>${{tot.toLocaleString()}}</b></div>
      <div class="ochip">อายุเฉลี่ย<b>${{avg}}</b> วัน</div>
      <div class="ochip">ค้างนานสุด<b>${{mxd}}</b> วัน</div>`;
    if(!tot){{ box.innerHTML='<div class="hint">ไม่มีงานค้างในช่วงที่เลือก 🎉</div>';
              hint.textContent=''; return; }}
    const mx = Math.max(...cnt);
    box.innerHTML = `<table class="otbl"><thead><tr>
      <th>ช่วงอายุงานค้าง</th><th class="num">จำนวน</th><th style="width:180px"></th>
      <th class="num">สัดส่วน</th></tr></thead><tbody>` +
      B.map((b,i)=>`<tr><td>${{b[0]}}</td><td class="num"><b>${{cnt[i].toLocaleString()}}</b></td>
      <td>${{bar(cnt[i],mx, i===3?'mini-r':'')}}</td>
      <td class="num">${{(cnt[i]*100/tot).toFixed(1)}}%</td></tr>`).join('') +
      '</tbody></table>';
    const top = [...pend].sort((a,b)=>b.age-a.age).slice(0,10);
    box.innerHTML += `<h4 style="margin:16px 0 8px;color:var(--o700);font-size:14px">
      🔥 10 รายการที่ค้างนานที่สุด</h4>
      <table class="otbl"><thead><tr><th>เลขที่</th><th>วันที่สร้าง</th><th>ผู้ขอ</th>
      <th>ค้างที่</th><th>ผู้รับผิดชอบ</th><th class="num">ค้าง (วัน)</th></tr></thead><tbody>` +
      top.map(r=>`<tr><td>${{dash(r.id)}}</td><td>${{dash(r.created)}}</td><td>${{dash(r.user)}}</td>
      <td>${{esc(r.stg)}}</td><td>${{esc(r.own)}}</td>
      <td class="num old">${{r.age}}</td></tr>`).join('') + '</tbody></table>';
    hint.textContent = 'นับจากวันที่สร้างคำขอถึงวันที่อัปเดตข้อมูลล่าสุด';
  }}
}}

document.querySelectorAll('.tab').forEach(t=>t.addEventListener('click',()=>{{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));
  t.classList.add('on'); OTAB = t.dataset.t; renderOwner();
}}));
document.getElementById('ownerbox').addEventListener('click',e=>{{
  const tr = e.target.closest('tr[data-o]'); if(!tr) return;
  FOWN = tr.dataset.o; FOWNMODE = OTAB;
  document.getElementById('fs').value = (OTAB==='pend') ? S_WAIT : '';
  apply();
  document.querySelector('.tbl-wrap').scrollIntoView({{behavior:'smooth',block:'start'}});
}});
document.getElementById('osum').addEventListener('click',e=>{{
  if(!e.target.closest('.fclr')) return;
  FOWN = ''; FOWNMODE = ''; document.getElementById('fs').value = ''; apply();
}});

/* ---------- ตัวกรอง ---------- */
function apply(){{
  const q=document.getElementById('q').value.trim().toLowerCase();
  const s=document.getElementById('fs').value, d=document.getElementById('fd').value,
        st=document.getElementById('fsite').value,
        d1=document.getElementById('d1').value, d2=document.getElementById('d2').value;
  cur = DATA.filter(r =>
    (!s || r.status===s) && (!d || r.dept===d) && (!st || r.site===st) &&
    (!FOWN || (FOWNMODE==='pend' ? r.own===FOWN
               : (r.hn===FOWN||r.pn===FOWN||r.an===FOWN))) &&
    (!d1 || (r.cd && r.cd >= d1)) && (!d2 || (r.cd && r.cd <= d2)) &&
    (!q || [r.user,r.pr,r.idno,r.dept,r.site,r.title,r.hn,r.pn,r.an,r.note,r.id]
            .join(' ').toLowerCase().includes(q)));
  shown = PAGE; render(); stats(); renderOwner();
}}
function preset(r, btn){{
  const d1=document.getElementById('d1'), d2=document.getElementById('d2');
  const now=new Date(); let a=null, b=null;
  if(r==='all'){{
    document.getElementById('q').value=''; FOWN=''; FOWNMODE='';
    ['fs','fd','fsite'].forEach(i=>document.getElementById(i).value='');
  }} else if(r==='tm'){{ a=new Date(now.getFullYear(),now.getMonth(),1); b=now; }}
  else if(r==='lm'){{ a=new Date(now.getFullYear(),now.getMonth()-1,1);
                      b=new Date(now.getFullYear(),now.getMonth(),0); }}
  else if(r==='ty'){{ a=new Date(now.getFullYear(),0,1); b=now; }}
  else {{ b=now; a=new Date(now.getTime()-(Number(r)-1)*86400000); }}
  d1.value = a?iso(a):''; d2.value = b?iso(b):'';
  document.querySelectorAll('.qb').forEach(x=>x.classList.remove('on'));
  if(btn && r!=='all') btn.classList.add('on');
  apply();
}}
['q','fs','fd','fsite','d1','d2'].forEach(id=>document.getElementById(id)
  .addEventListener('change',apply));
document.getElementById('q').addEventListener('input',apply);
['d1','d2'].forEach(id=>document.getElementById(id).addEventListener('input',()=>{{
  document.querySelectorAll('.qb').forEach(x=>x.classList.remove('on'));
}}));
document.querySelectorAll('.qb').forEach(b=>
  b.addEventListener('click',()=>preset(b.dataset.r,b)));
document.querySelector('.tbl-wrap').addEventListener('scroll',e=>{{
  const el=e.target;
  if(el.scrollTop+el.clientHeight>=el.scrollHeight-60 && shown<cur.length){{shown+=PAGE;render();}}
}});

pie = new Chart(document.getElementById('pie'),{{type:'doughnut',
  data:{{labels:[S_DONE,S_WAIT,S_CANCEL],
    datasets:[{{data:[{done},{wait},{cancel}],
      backgroundColor:['#16a34a','#fb923c','#dc2626'],borderWidth:2,borderColor:'#fff'}}]}},
  options:{{plugins:{{legend:{{position:'bottom',labels:{{padding:14,font:{{family:'Sarabun'}}}}}}}}}}}});
line = new Chart(document.getElementById('line'),{{type:'bar',
  data:{{labels:{json.dumps(months)},
    datasets:[{{label:'จำนวนคำขอ',data:{json.dumps(month_values)},
      backgroundColor:'#f97316',hoverBackgroundColor:'#c2410c',borderRadius:6}}]}},
  options:{{plugins:{{legend:{{display:false}}}},
    scales:{{y:{{beginAtZero:true,grid:{{color:'#ffedd5'}}}},x:{{grid:{{display:false}}}}}}}}}});
apply();
</script>
</body>
</html>"""


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="สร้าง dashboard จากไฟล์ CSV แทน Graph API")
    ap.add_argument("-o", "--out", default="index.html")
    ap.add_argument("--dump-fields", action="store_true",
                    help="แสดงชื่อคอลัมน์จริงทั้งหมดจาก SharePoint แล้วจบการทำงาน")
    a = ap.parse_args()

    if a.csv:
        rows = load_csv(a.csv)
    else:
        env = {k: (os.environ.get(k) or "").strip()
               for k in ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET")}
        if not all(env.values()):
            print("❌ ไม่พบค่า environment variable ต่อไปนี้ (ยังไม่ได้ตั้ง GitHub Secrets):",
                  file=sys.stderr)
            for k in ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"):
                v = env[k]
                mark = f"✅ มีค่า (ยาว {len(v)} ตัวอักษร)" if v else "❌ ว่าง/ไม่ได้ตั้ง"
                print(f"   - {k}: {mark}", file=sys.stderr)
            print("\n👉 วิธีแก้: Settings > Secrets and variables > Actions > "
                  "New repository secret\n"
                  "   ต้องเป็น *Repository secrets* (ไม่ใช่ Variables / ไม่ใช่ Environment secrets)\n"
                  "   และชื่อต้องสะกดตรงเป๊ะ ตัวพิมพ์ใหญ่ทั้งหมด", file=sys.stderr)
            sys.exit(78)
        raw, colmap = fetch_items(
            get_token(env["AZURE_TENANT_ID"], env["AZURE_CLIENT_ID"],
                      env["AZURE_CLIENT_SECRET"]))
        if a.dump_fields:
            keys = sorted({k for f in raw[:200] for k in f})
            print(f"\n📋 ชื่อคอลัมน์จริงใน SharePoint ({len(keys)} คอลัมน์):")
            for k in keys:
                sample = ""
                for f in raw[:200]:
                    if str(f.get(k) or "").strip():
                        sample = str(flat(f[k]))[:60]
                        break
                print(f"   {k:55s} | ตัวอย่าง: {sample}")
            print(f"\n📋 map displayName -> internal name ({len(colmap)}):")
            for k, v in sorted(colmap.items()):
                print(f"   {k:40s} -> {v}")
            return
        rows = normalize(raw, colmap)
        report_fields(rows, {k for f in raw[:200] for k in f})

    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(build_html(rows))
    print(f"✅ สร้าง {a.out} สำเร็จ ({len(rows):,} รายการ)")


if __name__ == "__main__":
    main()
