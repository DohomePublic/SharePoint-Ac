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
LIST_URL = ("https://dohomegroup.sharepoint.com/sites/AC-Accounting/Lists/"
            "ACData%20Request%20for%20approval%20of%20PO")
ITEM_URL = LIST_URL + "/DispForm.aspx?ID={id}"

# ---- mapping: internal field name (Graph) -> key ที่ใช้ใน dashboard ----
FIELDS = {
    "id": "ID",
    "title": "Title",
    "user": "user_x0020_name",
    "dept": "Department",
    "pr": "PR_x0020_Number",
    "status": "Status",
    "site": "Site",
    "created": "Created",
    "modified": "Modified",
    "head_name": "Name_x0020_Department_x0020_Head",
    "head_status": "Status_x0020_Department_x0020_Head",
    "proc_status": "Status_x0020_Head_x0020_of_x0020_Procurement_x0020_Center",
    "asset_status": "Status_x0020_Asset_x0020_Register",
    "note": "Additional_x0020_Notes",
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
    r.raise_for_status()
    return r.json()["access_token"]


def graph_get(url, token):
    import requests
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=120)
    r.raise_for_status()
    return r.json()


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
        raise SystemExit(f"ไม่พบ List ชื่อ '{LIST_NAME}' ใน site {SITE_PATH}")

    url = (f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}"
           f"/items?expand=fields&$top=1000")
    rows = []
    while url:
        data = graph_get(url, token)
        for it in data.get("value", []):
            rows.append(it.get("fields", {}))
        url = data.get("@odata.nextLink")
    return rows


def normalize(fields_rows):
    out = []
    for f in fields_rows:
        out.append({k: f.get(v) for k, v in FIELDS.items()})
    return out


# --------------------------------------------------------------------------
# 2) โหมด preview จาก CSV
# --------------------------------------------------------------------------
CSV_MAP = {
    "id": "_ID", "title": "Title", "user": "user name", "dept": "Department",
    "pr": "PR Number", "status": "Status", "site": "Site",
    "created": "Created", "modified": "Modified",
    "head_name": "Name Department Head",
    "head_status": "Status Department Head",
    "proc_status": "Status Head of Procurement Center",
    "asset_status": "Status Asset Register",
    "note": "Additional Notes",
}


def load_csv(path):
    import csv as _csv
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for r in _csv.DictReader(fh):
            rows.append({k: (r.get(v) or "").strip() for k, v in CSV_MAP.items()})
    return rows


# --------------------------------------------------------------------------
# 3) สร้าง HTML
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


def clean_pr(v):
    v = str(v or "").strip()
    if v.endswith(".0"):
        v = v[:-2]
    if v.lower() in ("nan", "none"):
        return ""
    try:  # 1.100453e+09 -> 1100453000
        if "e+" in v.lower():
            return str(int(float(v)))
    except Exception:
        pass
    return v


def build_html(rows):
    now = datetime.now(TZ)
    rows = sorted(rows, key=sort_key, reverse=True)
    for r in rows:
        r["pr"] = clean_pr(r.get("pr"))
        r["status"] = (str(r.get("status") or "").strip()
                       .replace("nan", "") or "-")

    total = len(rows)
    c_status = Counter(r["status"] for r in rows)
    done = c_status.get(STATUS_DONE, 0)
    wait = c_status.get(STATUS_WAIT, 0)
    cancel = c_status.get(STATUS_CANCEL, 0)

    dept = Counter(str(r.get("dept") or "").strip() for r in rows if r.get("dept"))
    site = Counter(str(r.get("site") or "").strip() for r in rows if r.get("site"))

    # กราฟรายเดือน 12 เดือนล่าสุด
    month = Counter()
    for r in rows:
        k = str(r.get("created") or "")[:7]
        if len(k) == 7:
            month[k] += 1
    months = sorted(month)[-12:]
    month_labels = months
    month_values = [month[m] for m in months]

    all_dates = sorted(d for d in (iso_date(r.get("created")) for r in rows) if len(d) == 10)
    date_min = all_dates[0] if all_dates else ""
    date_max = all_dates[-1] if all_dates else ""

    data_json = json.dumps(
        [{"id": r.get("id"), "title": r.get("title"), "user": r.get("user"),
          "dept": r.get("dept"), "pr": r.get("pr"), "status": r.get("status"),
          "site": r.get("site"), "created": fmt_dt(r.get("created")),
          "cd": iso_date(r.get("created")),
          "head": r.get("head_name"), "hs": r.get("head_status"),
          "ps": r.get("proc_status"), "as": r.get("asset_status"),
          "note": r.get("note")} for r in rows],
        ensure_ascii=False)

    top_dept = dept.most_common(10)
    top_site = site.most_common(10)

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
<link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Sarabun',sans-serif;background:#f2f5f9;color:#1e293b}}
header{{background:linear-gradient(135deg,#e2231a,#a3120c);color:#fff;padding:22px 28px}}
header h1{{font-size:22px;font-weight:700}}
header p{{opacity:.85;font-size:13px;margin-top:4px}}
.wrap{{max-width:1400px;margin:0 auto;padding:22px 28px 60px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px}}
.card{{background:#fff;border-radius:14px;padding:18px 20px;box-shadow:0 2px 10px rgba(15,23,42,.07)}}
.card .lb{{font-size:13px;color:#64748b}}
.card .val{{font-size:30px;font-weight:700;margin-top:6px}}
.c-all .val{{color:#0f172a}} .c-done .val{{color:#16a34a}}
.c-wait .val{{color:#f59e0b}} .c-cancel .val{{color:#dc2626}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:18px}}
@media(max-width:960px){{.grid2{{grid-template-columns:1fr}}}}
.panel{{background:#fff;border-radius:14px;padding:18px 20px;box-shadow:0 2px 10px rgba(15,23,42,.07)}}
.panel h2{{font-size:15px;font-weight:600;margin-bottom:14px}}
.bar-row{{display:flex;align-items:center;gap:10px;margin-bottom:8px;font-size:13px}}
.bar-lb{{width:230px;flex:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.bar-track{{flex:1;height:10px;background:#eef2f7;border-radius:6px;overflow:hidden}}
.bar-fill{{display:block;height:100%;background:linear-gradient(90deg,#e2231a,#f97316)}}
.bar-val{{width:60px;text-align:right;color:#475569}}
.tools{{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 12px}}
input,select{{font-family:inherit;font-size:14px;padding:9px 12px;border:1px solid #d7dee8;border-radius:9px;background:#fff}}
#q{{flex:1;min-width:240px}}
.daterow{{align-items:center;margin-top:0}}
.daterow input[type=date]{{min-width:150px}}
.dl{{font-size:13px;color:#64748b}}
.qb{{font-family:inherit;font-size:13px;padding:8px 14px;border:1px solid #d7dee8;border-radius:9px;
   background:#fff;color:#334155;cursor:pointer}}
.qb:hover{{background:#f1f5f9}}
.qb.on{{background:#e2231a;border-color:#e2231a;color:#fff}}
.qb.clr{{color:#dc2626}}
.sub{{font-weight:400;color:#94a3b8;font-size:12px}}
table{{width:100%;border-collapse:collapse;background:#fff;font-size:13px}}
th{{background:#f8fafc;text-align:left;padding:11px 10px;border-bottom:2px solid #e2e8f0;position:sticky;top:0}}
td{{padding:10px;border-bottom:1px solid #eef2f7;vertical-align:top}}
tbody tr:hover{{background:#fafcff}}
.tbl-wrap{{max-height:640px;overflow:auto;border-radius:14px;box-shadow:0 2px 10px rgba(15,23,42,.07)}}
.pill{{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;white-space:nowrap}}
.p-done{{background:#dcfce7;color:#15803d}} .p-wait{{background:#fef3c7;color:#b45309}}
.p-cancel{{background:#fee2e2;color:#b91c1c}} .p-na{{background:#e2e8f0;color:#475569}}
a{{color:#e2231a;text-decoration:none}} a:hover{{text-decoration:underline}}
footer{{text-align:center;color:#94a3b8;font-size:12px;margin-top:26px}}
</style>
</head>
<body>
<header>
  <h1>📋 Dashboard คำขออนุมัติ PO (AC-Data Request for approval of PO)</h1>
  <p>อัปเดตล่าสุด: {now.strftime('%d/%m/%Y %H:%M')} น. (เวลาไทย) · ข้อมูล {total:,} รายการ ·
     <a href="{LIST_URL}" style="color:#fff;text-decoration:underline">เปิด SharePoint List</a></p>
</header>
<div class="wrap">
  <div class="cards">
    <div class="card c-all"><div class="lb">รายการทั้งหมด</div><div class="val" id="k-all">{total:,}</div></div>
    <div class="card c-done"><div class="lb">ดำเนินการเรียบร้อย</div><div class="val" id="k-done">{done:,}</div></div>
    <div class="card c-wait"><div class="lb">รอดำเนินการ</div><div class="val" id="k-wait">{wait:,}</div></div>
    <div class="card c-cancel"><div class="lb">ยกเลิก</div><div class="val" id="k-cancel">{cancel:,}</div></div>
  </div>

  <div class="tools">
    <input id="q" placeholder="🔍 ค้นหา: ชื่อผู้ขอ / เลข PR / หน่วยงาน / สาขา">
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
  <div id="cnt" style="font-size:13px;color:#64748b;margin:4px 0 12px"></div>

  <div class="grid2">
    <div class="panel"><h2>สัดส่วนสถานะ <span class="sub">(ตามตัวกรอง)</span></h2><canvas id="pie" height="190"></canvas></div>
    <div class="panel"><h2>จำนวนคำขอรายเดือน <span class="sub">(ตามตัวกรอง, 12 เดือนล่าสุด)</span></h2><canvas id="line" height="190"></canvas></div>
  </div>

  <div class="grid2">
    <div class="panel"><h2>Top 10 หน่วยงาน</h2><div id="bd">{bars(top_dept)}</div></div>
    <div class="panel"><h2>Top 10 สาขา / Site</h2><div id="bs">{bars(top_site)}</div></div>
  </div>
  <div style="height:18px"></div>

  <div class="tbl-wrap">
    <table>
      <thead><tr><th>ID</th><th>วันที่สร้าง</th><th>ผู้ขอ</th><th>หน่วยงาน</th>
      <th>PR Number</th><th>สาขา</th><th>สถานะ</th><th>ผู้อนุมัติ (หน.แผนก)</th><th>ลิงก์</th></tr></thead>
      <tbody id="tb"></tbody>
    </table>
  </div>
  <footer>Auto-generated by GitHub Actions · build_dashboard.py · DOHOME BI HQ</footer>
</div>
<script>
const DATA = {data_json};
const ITEM = "{ITEM_URL}";
const DMIN = "{date_min}", DMAX = "{date_max}";
const S_DONE="{STATUS_DONE}", S_WAIT="{STATUS_WAIT}", S_CANCEL="{STATUS_CANCEL}";
const PAGE = 300; let shown = PAGE, cur = DATA, pie, line;
const pill = s => s===S_DONE ? "p-done" : s===S_WAIT ? "p-wait"
                : s===S_CANCEL ? "p-cancel" : "p-na";
const esc = s => (s??"").toString().replace(/[&<>]/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;"}}[c]));
const iso = d => new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10);

function render(){{
  const tb=document.getElementById('tb');
  tb.innerHTML = cur.slice(0,shown).map(r=>`<tr>
    <td>${{esc(r.id)}}</td><td>${{esc(r.created)}}</td><td>${{esc(r.user)}}</td>
    <td>${{esc(r.dept)}}</td><td>${{esc(r.pr)}}</td><td>${{esc(r.site)}}</td>
    <td><span class="pill ${{pill(r.status)}}">${{esc(r.status)}}</span></td>
    <td>${{esc(r.head)}}</td>
    <td><a href="${{ITEM.replace('{{id}}', r.id)}}" target="_blank">เปิด ↗</a></td></tr>`).join('');
  const d1=document.getElementById('d1').value, d2=document.getElementById('d2').value;
  const rng = (d1||d2) ? ` · ช่วงวันที่ ${{d1||DMIN}} ถึง ${{d2||DMAX}}` : '';
  document.getElementById('cnt').textContent =
    `แสดง ${{Math.min(shown,cur.length).toLocaleString()}} จาก ${{cur.length.toLocaleString()}} รายการ${{rng}}`;
}}

function mkbars(pairs){{
  if(!pairs.length) return '<div style="color:#94a3b8;font-size:13px">ไม่มีข้อมูลในช่วงที่เลือก</div>';
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
  pie.data.datasets[0].data = [c(S_DONE), c(S_WAIT), c(S_CANCEL)];
  pie.update();
  const m={{}}; cur.forEach(r=>{{const k=(r.cd||'').slice(0,7); if(k.length===7) m[k]=(m[k]||0)+1;}});
  const ks = Object.keys(m).sort().slice(-12);
  line.data.labels = ks; line.data.datasets[0].data = ks.map(k=>m[k]); line.update();
}}

function apply(){{
  const q=document.getElementById('q').value.trim().toLowerCase();
  const s=document.getElementById('fs').value, d=document.getElementById('fd').value,
        st=document.getElementById('fsite').value,
        d1=document.getElementById('d1').value, d2=document.getElementById('d2').value;
  cur = DATA.filter(r =>
    (!s || r.status===s) && (!d || r.dept===d) && (!st || r.site===st) &&
    (!d1 || (r.cd && r.cd >= d1)) && (!d2 || (r.cd && r.cd <= d2)) &&
    (!q || [r.user,r.pr,r.dept,r.site,r.title,r.head,r.note].join(' ').toLowerCase().includes(q)));
  shown = PAGE; render(); stats();
}}

function preset(r, btn){{
  const d1=document.getElementById('d1'), d2=document.getElementById('d2');
  const now=new Date(); let a=null, b=null;
  if(r==='all'){{
    document.getElementById('q').value='';
    ['fs','fd','fsite'].forEach(i=>document.getElementById(i).value='');
  }} else if(r==='tm'){{
    a=new Date(now.getFullYear(),now.getMonth(),1); b=now;
  }} else if(r==='lm'){{
    a=new Date(now.getFullYear(),now.getMonth()-1,1);
    b=new Date(now.getFullYear(),now.getMonth(),0);
  }} else if(r==='ty'){{
    a=new Date(now.getFullYear(),0,1); b=now;
  }} else {{
    b=now; a=new Date(now.getTime()-(Number(r)-1)*86400000);
  }}
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
    datasets:[{{data:[{done},{wait},{cancel}],backgroundColor:['#16a34a','#f59e0b','#dc2626']}}]}},
  options:{{plugins:{{legend:{{position:'bottom'}}}}}}}});
line = new Chart(document.getElementById('line'),{{type:'bar',
  data:{{labels:{json.dumps(month_labels)},
    datasets:[{{label:'จำนวนคำขอ',data:{json.dumps(month_values)},
      backgroundColor:'#e2231a',borderRadius:6}}]}},
  options:{{plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true}}}}}}}});
apply();
</script>
</body>
</html>"""


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="สร้าง dashboard จากไฟล์ CSV แทน Graph API")
    ap.add_argument("-o", "--out", default="index.html")
    a = ap.parse_args()

    if a.csv:
        rows = load_csv(a.csv)
    else:
        tid = os.environ.get("AZURE_TENANT_ID")
        cid = os.environ.get("AZURE_CLIENT_ID")
        sec = os.environ.get("AZURE_CLIENT_SECRET")
        if not all([tid, cid, sec]):
            sys.exit("❌ ต้องตั้งค่า AZURE_TENANT_ID / AZURE_CLIENT_ID / AZURE_CLIENT_SECRET")
        rows = normalize(fetch_items(get_token(tid, cid, sec)))

    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(build_html(rows))
    print(f"✅ สร้าง {a.out} สำเร็จ ({len(rows):,} รายการ)")


if __name__ == "__main__":
    main()
