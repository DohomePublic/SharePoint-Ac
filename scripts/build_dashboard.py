#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_dashboard.py — ดึงข้อมูลจาก SharePoint List แล้ว build แดชบอร์ดอนุมัติ PO

ใช้แพทเทิร์นเดียวกับ Update KYC Dashboard: Python + requests อย่างเดียว
ไม่ต้องติดตั้ง Node หรือ dependency อื่น

  List : AC-Data Request for approval of PO
  Site : https://dohomegroup.sharepoint.com/sites/AC-Accounting

ผลลัพธ์
  index.html                  แดชบอร์ดเต็ม (หน้าแรกของ GitHub Pages)
  dashboard/index.html        สำเนา สำหรับอัปขึ้น SharePoint SiteAssets
  dashboard/data.json         ข้อมูลอย่างเดียว สำหรับปุ่มรีเฟรชในแดชบอร์ด
  dashboard/build-report.json รายงานผลการ build

รันเอง (ไม่มี secrets ก็ได้ จะ build จาก data.json เดิม)
  python scripts/build_dashboard.py
  python scripts/build_dashboard.py --from-csv ข้อมูล.csv
  python scripts/build_dashboard.py --force        ข้ามการตรวจข้อมูลหด
"""

import csv
import io
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "dashboard", "template.html")
OUT_ROOT = os.path.join(ROOT, "index.html")
OUT_DASH = os.path.join(ROOT, "dashboard", "index.html")
DATA_JSON = os.path.join(ROOT, "dashboard", "data.json")
REPORT = os.path.join(ROOT, "dashboard", "build-report.json")

BKK = timezone(timedelta(hours=7))

# ลำดับคอลัมน์ต้องตรงกับที่แดชบอร์ดใช้ (Display Name จริงของ List — ห้ามเดา)
COLS = [
    "_ID", "Title", "id number", "user name", "Department", "PR Number", "Additional Notes",
    "Name Department Head", "Time Department Head", "Status Department Head",
    "Name Head of Procurement Center", "Time Head of Procurement Center",
    "Status Head of Procurement Center",
    "Status", "Name Asset Register", "Time Asset Register", "Status Asset Register",
    "Email User", "Site", "Comment Department Head", "Comment Head Procurement Center",
    "Comment Asset ", "Created", "Modified", "_HasAttachments",
]

HOSTNAME = os.environ.get("SP_HOSTNAME", "dohomegroup.sharepoint.com")
SITE_PATH = os.environ.get("SP_SITE_PATH", "/sites/AC-Accounting")
LIST_TITLE = os.environ.get("SP_LIST_TITLE", "AC-Data Request for approval of PO")


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------- Graph API
def get_token():
    tid = os.environ.get("AZURE_TENANT_ID")
    cid = os.environ.get("AZURE_CLIENT_ID")
    sec = os.environ.get("AZURE_CLIENT_SECRET")
    if not (tid and cid and sec):
        raise RuntimeError("ขาด AZURE_TENANT_ID / AZURE_CLIENT_ID / AZURE_CLIENT_SECRET")
    r = requests.post(
        f"https://login.microsoftonline.com/{tid}/oauth2/v2.0/token",
        data={
            "client_id": cid,
            "client_secret": sec,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        },
        timeout=60,
    )
    if not r.ok:
        raise RuntimeError(f"ขอ token ไม่สำเร็จ: {r.status_code} {r.text[:300]}")
    return r.json()["access_token"]


def g(url, token, tries=5):
    """เรียก Graph พร้อม retry อัตโนมัติ (429 throttle / 5xx / network error)"""
    last = None
    for n in range(1, tries + 1):
        try:
            r = requests.get(
                url,
                headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
                timeout=120,
            )
            if r.ok:
                return r.json()
            if r.status_code in (401, 403, 404):  # ไม่ต้อง retry
                raise RuntimeError(f"Graph {r.status_code} {url}\n{r.text[:500]}")
            if r.status_code == 429 or r.status_code >= 500:
                ra = r.headers.get("Retry-After")
                wait = int(ra) if (ra and ra.isdigit()) else min(30, 1.5 * 2 ** (n - 1))
                log(f"  ↻ Graph {r.status_code} — รอ {wait:.1f}s แล้วลองใหม่ ({n}/{tries})")
                time.sleep(wait)
                last = RuntimeError(f"Graph {r.status_code}: {r.text[:300]}")
                continue
            raise RuntimeError(f"Graph {r.status_code} {url}\n{r.text[:500]}")
        except requests.RequestException as e:
            last = e
            if n == tries:
                break
            wait = min(30, 1.5 * 2 ** (n - 1))
            log(f"  ↻ ผิดพลาด: {str(e)[:120]} — ลองใหม่ใน {wait:.1f}s ({n}/{tries})")
            time.sleep(wait)
    raise last if last else RuntimeError("เรียก Graph ไม่สำเร็จ")


def fetch_from_graph():
    token = get_token()
    log(f"→ เชื่อมต่อ {HOSTNAME}{SITE_PATH}")
    site = g(f"https://graph.microsoft.com/v1.0/sites/{HOSTNAME}:{SITE_PATH}", token)

    lists = g(f"https://graph.microsoft.com/v1.0/sites/{site['id']}/lists?$select=id,displayName", token)
    lst = next((l for l in lists.get("value", []) if l.get("displayName") == LIST_TITLE), None)
    if not lst:
        names = ", ".join(l.get("displayName", "") for l in lists.get("value", [])[:20])
        raise RuntimeError(f'ไม่พบ List "{LIST_TITLE}" ในไซต์ {SITE_PATH}\nList ที่มี: {names}')

    # map Display Name -> internal name (อ่านจาก List จริง ไม่เดาชื่อคอลัมน์)
    cols = g(
        f"https://graph.microsoft.com/v1.0/sites/{site['id']}/lists/{lst['id']}/columns?$select=name,displayName",
        token,
    )
    by_display = {}
    for c in cols.get("value", []):
        by_display.setdefault(c.get("displayName"), c.get("name"))

    missing = [c for c in COLS if c not in by_display
               and c not in ("_ID", "Created", "Modified", "_HasAttachments")]
    if missing:
        log(f"  ⚠ คอลัมน์ที่หาไม่เจอใน List (จะเว้นว่าง): {missing}")

    rows = []
    url = (f"https://graph.microsoft.com/v1.0/sites/{site['id']}/lists/{lst['id']}"
           f"/items?expand=fields&$top=500")
    page = 0
    while url and page < 400:
        j = g(url, token)
        page += 1
        for it in j.get("value", []):
            f = it.get("fields", {}) or {}
            o = {}
            for disp in COLS:
                if disp == "_ID":
                    o["_ID"] = it.get("id")
                    continue
                if disp == "Created":
                    o["Created"] = it.get("createdDateTime")
                    continue
                if disp == "Modified":
                    o["Modified"] = it.get("lastModifiedDateTime")
                    continue
                if disp == "_HasAttachments":
                    o["_HasAttachments"] = str(bool(f.get("Attachments"))).lower()
                    continue
                key = by_display.get(disp)
                v = f.get(key) if key else None
                if isinstance(v, dict):
                    v = (v.get("Title") or v.get("LookupValue") or v.get("Email")
                         or v.get("DisplayName") or json.dumps(v, ensure_ascii=False))
                o[disp] = None if v is None else str(v)
            rows.append(o)
        if page % 5 == 0:
            log(f"  … ดึงแล้ว {len(rows):,} รายการ")
        url = j.get("@odata.nextLink")
    log(f"✔ ดึงจาก SharePoint สำเร็จ {len(rows):,} รายการ")
    return rows


# ------------------------------------------------------------------- ทางเลือกอื่น
def rows_from_csv(path):
    with io.open(path, "r", encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        rows = []
        for r in rd:
            rows.append({c: (r.get(c) if r.get(c) not in ("", None) else None) for c in COLS})
    log(f"✔ อ่านจาก CSV {len(rows):,} รายการ")
    return rows


def rows_from_data_json():
    """คลาย data.json เดิมกลับเป็น rows (ใช้เมื่อไม่มี secrets)"""
    if not os.path.exists(DATA_JSON):
        raise RuntimeError("ไม่มี dashboard/data.json ให้ใช้ และไม่มี AZURE_* secrets")
    with io.open(DATA_JSON, "r", encoding="utf-8") as fh:
        d = json.load(fh)["data"]
    cols, dicts, vals, n = d["c"], d["d"], d["v"], d["n"]
    rows = []
    for i in range(n):
        o = {}
        for ci, c in enumerate(cols):
            k = vals[ci][i]
            o[c] = None if k < 0 else dicts[ci][k]
        rows.append(o)
    log(f"✔ ใช้ข้อมูลเดิมจาก data.json {len(rows):,} รายการ")
    return rows


# ------------------------------------------------------------------- pack/render
def pack(rows):
    """dictionary encoding — ลดขนาด ~4 เท่า โดยไม่ต้องพึ่ง gzip ในเบราว์เซอร์"""
    dicts, vals = [], []
    for c in COLS:
        lst, idx, col = [], {}, []
        for r in rows:
            v = r.get(c)
            if v is None or v == "":
                col.append(-1)
                continue
            s = str(v)
            if s not in idx:
                idx[s] = len(lst)
                lst.append(s)
            col.append(idx[s])
        dicts.append(lst)
        vals.append(col)
    return {"c": COLS, "d": dicts, "v": vals, "n": len(rows)}


def render(rows):
    with io.open(TEMPLATE, "r", encoding="utf-8") as fh:
        tpl = fh.read()
    if "__SNAPSHOT_JSON__" not in tpl:
        raise RuntimeError("dashboard/template.html ไม่มี placeholder __SNAPSHOT_JSON__")

    packed = pack(rows)
    payload = json.dumps(packed, ensure_ascii=False, separators=(",", ":"))
    if "</script" in payload.lower():
        raise RuntimeError("ข้อมูลมี </script> ซึ่งจะทำให้ HTML พัง")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M") + " UTC"
    html = tpl.replace("__SNAPSHOT_JSON__", payload).replace("SNAPDATE", stamp)

    # กันบั๊กเดิม: บล็อกข้อมูลต้องอยู่ก่อนสคริปต์หลักเสมอ ไม่งั้นข้อมูลไม่แสดง
    i_data, i_use = html.find('id="snap"'), html.find("function loadSnapshot")
    if i_data < 0 or i_use < 0 or i_data > i_use:
        raise RuntimeError("บล็อกข้อมูล #snap ต้องอยู่ก่อนสคริปต์หลัก")

    for p in (OUT_ROOT, OUT_DASH):
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(html)

    with io.open(DATA_JSON, "w", encoding="utf-8") as fh:
        json.dump({
            "builtAt": stamp,
            "rows": len(rows),
            "source": f"SharePoint List: {LIST_TITLE}",
            "data": packed,
        }, fh, ensure_ascii=False, separators=(",", ":"))

    return {"htmlBytes": os.path.getsize(OUT_ROOT),
            "dataBytes": os.path.getsize(DATA_JSON),
            "builtAt": stamp}


# ------------------------------------------------------------------- สรุปผล
def to_bkk(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(BKK)
    except Exception:
        return None


def summarize(rows):
    stamps = [(to_bkk(r.get("Created")), r) for r in rows]
    stamps = [(d, r) for d, r in stamps if d]
    stamps.sort(key=lambda x: x[0])
    latest_dt, latest = stamps[-1] if stamps else (None, {})
    last_day = latest_dt.strftime("%Y-%m-%d") if latest_dt else None
    today = datetime.now(BKK).strftime("%Y-%m-%d")
    by_status = {}
    for r in rows:
        by_status[r.get("Status") or "(ไม่ระบุ)"] = by_status.get(r.get("Status") or "(ไม่ระบุ)", 0) + 1
    return {
        "latestCreatedBkk": latest_dt.strftime("%Y-%m-%d %H:%M") if latest_dt else None,
        "latestId": latest.get("_ID"),
        "latestTitle": latest.get("Title"),
        "lastDay": last_day,
        "lastDayCount": sum(1 for d, _ in stamps if d.strftime("%Y-%m-%d") == last_day),
        "todayBkk": today,
        "todayCount": sum(1 for d, _ in stamps if d.strftime("%Y-%m-%d") == today),
        "byStatus": sorted(by_status.items(), key=lambda x: -x[1]),
    }


def previous_rows():
    try:
        with io.open(DATA_JSON, "r", encoding="utf-8") as fh:
            return int(json.load(fh)["data"]["n"])
    except Exception:
        return 0


# ------------------------------------------------------------------- main
def main():
    args = sys.argv[1:]
    force = "--force" in args or os.environ.get("FORCE_BUILD", "").lower() == "true"
    started = time.time()

    if "--from-csv" in args:
        src, rows = "csv", rows_from_csv(args[args.index("--from-csv") + 1])
    elif os.environ.get("AZURE_TENANT_ID") and os.environ.get("AZURE_CLIENT_ID") \
            and os.environ.get("AZURE_CLIENT_SECRET") and "--offline" not in args:
        src, rows = "graph", fetch_from_graph()
    else:
        log("⚠ ไม่มี AZURE_* secrets — จะ build ใหม่จากข้อมูลเดิมแทน")
        src, rows = "data.json", rows_from_data_json()

    if not rows:
        raise RuntimeError("ไม่ได้ข้อมูลเลย — หยุดเพื่อไม่ให้เขียนทับแดชบอร์ดเดิมด้วยไฟล์ว่าง")

    prev = previous_rows()
    if prev and len(rows) < prev * 0.9 and not force:
        raise RuntimeError(
            f"ข้อมูลหดผิดปกติ {prev:,} → {len(rows):,} "
            f"(หายไป {(1 - len(rows) / prev) * 100:.1f}%) — หยุดไว้ก่อน\n"
            f"ถ้าถูกต้องจริงให้รันใหม่ด้วย --force หรือตั้ง FORCE_BUILD=true"
        )

    info = render(rows)
    summary = summarize(rows)
    report = {
        "builtAt": info["builtAt"], "source": src,
        "tookSec": round(time.time() - started, 1),
        "rows": len(rows), "previousRows": prev, "delta": len(rows) - prev,
        "htmlBytes": info["htmlBytes"], "dataBytes": info["dataBytes"],
        **summary,
    }
    with io.open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    log("")
    log(f"✔ index.html / dashboard/index.html : {len(rows):,} รายการ, "
        f"{info['htmlBytes'] / 1048576:.2f} MB")
    log(f"✔ dashboard/data.json              : {info['dataBytes'] / 1048576:.2f} MB")
    log(f"✔ เทียบครั้งก่อน                     : {prev:,} → {len(rows):,} "
        f"({len(rows) - prev:+,})")
    log(f"✔ รายการใหม่สุด                     : {summary['latestCreatedBkk']} น. (เวลาไทย) · "
        f"เลขที่คำขอ {summary['latestTitle']} · ID {summary['latestId']}")
    log(f"✔ วันนี้ ({summary['todayBkk']})            : {summary['todayCount']:,} รายการ")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"::error::{e}", file=sys.stderr)
        print(f"\n❌ {e}", file=sys.stderr)
        sys.exit(1)
