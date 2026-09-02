#!/usr/bin/env node
/**
 * build-snapshot.mjs
 * ------------------------------------------------------------------
 * ดึงข้อมูลจาก SharePoint List "AC-Data Request for approval of PO"
 * ผ่าน Microsoft Graph (client credentials) แล้วสร้าง dashboard/index.html
 * โดยฝัง snapshot แบบ dictionary-encoded JSON ลงใน template.html
 *
 * ใช้ได้ 2 โหมด:
 *   node scripts/build-snapshot.mjs            -> ดึงสดจาก Graph (ต้องมี env)
 *   node scripts/build-snapshot.mjs --from-csv path.csv
 *                                              -> สร้างจากไฟล์ CSV ที่ export ไว้
 *
 * ENV ที่ต้องใช้ในโหมด Graph (ตั้งเป็น GitHub Secrets):
 *   AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET
 *   SP_HOSTNAME (default: dohomegroup.sharepoint.com)
 *   SP_SITE_PATH (default: /sites/AC-Accounting)
 *   SP_LIST_TITLE (default: AC-Data Request for approval of PO)
 * สิทธิ์ Graph ที่ต้องให้ (Application): Sites.Selected หรือ Sites.Read.All
 * ------------------------------------------------------------------
 */
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const TEMPLATE = path.join(ROOT, "dashboard", "template.html");
const OUTPUT = path.join(ROOT, "dashboard", "index.html");

/** ลำดับคอลัมน์ต้องตรงกับที่ dashboard ใช้งาน (Display Name จริงของ List) */
export const COLS = [
  "_ID", "Title", "id number", "user name", "Department", "PR Number", "Additional Notes",
  "Name Department Head", "Time Department Head", "Status Department Head",
  "Name Head of Procurement Center", "Time Head of Procurement Center", "Status Head of Procurement Center",
  "Status", "Name Asset Register", "Time Asset Register", "Status Asset Register",
  "Email User", "Site", "Comment Department Head", "Comment Head Procurement Center",
  "Comment Asset ", "Created", "Modified", "_HasAttachments"
];

/** dictionary encoding: ลดขนาดไฟล์ ~4 เท่า และไม่ต้องพึ่ง gzip ในเบราว์เซอร์ */
export function pack(rows) {
  const dicts = [], vals = [];
  for (const c of COLS) {
    const list = [], idx = new Map(), col = [];
    for (const r of rows) {
      const v = r[c];
      if (v === null || v === undefined || v === "") { col.push(-1); continue; }
      const s = String(v);
      if (!idx.has(s)) { idx.set(s, list.length); list.push(s); }
      col.push(idx.get(s));
    }
    dicts.push(list); vals.push(col);
  }
  return { c: COLS, d: dicts, v: vals, n: rows.length };
}

export function render(rows) {
  const tpl = fs.readFileSync(TEMPLATE, "utf8");
  if (!tpl.includes("__SNAPSHOT_JSON__")) throw new Error("template.html ไม่มี placeholder __SNAPSHOT_JSON__");
  const json = JSON.stringify(pack(rows));
  if (/<\/script/i.test(json)) throw new Error("ข้อมูลมี </script> ซึ่งจะทำให้ HTML พัง");
  const stamp = new Date().toISOString().replace("T", " ").slice(0, 16) + " UTC";
  const html = tpl.replace("__SNAPSHOT_JSON__", json).replace(/SNAPDATE/g, stamp);
  const iData = html.indexOf('id="snap"');
  const iUse = html.indexOf("function loadSnapshot");
  if (iData < 0 || iUse < 0 || iData > iUse) throw new Error("บล็อกข้อมูลต้องอยู่ก่อนสคริปต์หลักเสมอ");
  fs.writeFileSync(OUTPUT, html, "utf8");
  return { bytes: Buffer.byteLength(html), rows: rows.length };
}

/* ---------------- Microsoft Graph ---------------- */
async function token() {
  const t = process.env.AZURE_TENANT_ID, c = process.env.AZURE_CLIENT_ID, s = process.env.AZURE_CLIENT_SECRET;
  if (!t || !c || !s) throw new Error("ขาด AZURE_TENANT_ID / AZURE_CLIENT_ID / AZURE_CLIENT_SECRET");
  const body = new URLSearchParams({
    client_id: c, client_secret: s, scope: "https://graph.microsoft.com/.default", grant_type: "client_credentials"
  });
  const r = await fetch(`https://login.microsoftonline.com/${t}/oauth2/v2.0/token`, { method: "POST", body });
  if (!r.ok) throw new Error("ขอ token ไม่สำเร็จ: " + r.status + " " + await r.text());
  return (await r.json()).access_token;
}
async function g(url, tk) {
  const r = await fetch(url, { headers: { Authorization: "Bearer " + tk, Accept: "application/json" } });
  if (!r.ok) throw new Error(`Graph ${r.status} ${url}\n${await r.text()}`);
  return r.json();
}
async function fetchFromGraph() {
  const host = process.env.SP_HOSTNAME || "dohomegroup.sharepoint.com";
  const sitePath = process.env.SP_SITE_PATH || "/sites/AC-Accounting";
  const listTitle = process.env.SP_LIST_TITLE || "AC-Data Request for approval of PO";
  const tk = await token();
  const site = await g(`https://graph.microsoft.com/v1.0/sites/${host}:${sitePath}`, tk);
  const lists = await g(`https://graph.microsoft.com/v1.0/sites/${site.id}/lists?$select=id,displayName`, tk);
  const list = (lists.value || []).find(l => l.displayName === listTitle);
  if (!list) throw new Error(`ไม่พบ List "${listTitle}" ในไซต์ ${sitePath}`);

  // map Display Name -> internal column name (ห้ามเดาชื่อคอลัมน์)
  const cols = await g(`https://graph.microsoft.com/v1.0/sites/${site.id}/lists/${list.id}/columns?$select=name,displayName`, tk);
  const byDisplay = new Map();
  for (const c of cols.value || []) if (!byDisplay.has(c.displayName)) byDisplay.set(c.displayName, c.name);

  const rows = [];
  let url = `https://graph.microsoft.com/v1.0/sites/${site.id}/lists/${list.id}/items?expand=fields&$top=500`;
  let guard = 0;
  while (url && guard++ < 200) {
    const j = await g(url, tk);
    for (const it of j.value || []) {
      const f = it.fields || {}, o = {};
      for (const disp of COLS) {
        if (disp === "_ID") { o._ID = it.id; continue; }
        if (disp === "Created") { o.Created = it.createdDateTime; continue; }
        if (disp === "Modified") { o.Modified = it.lastModifiedDateTime; continue; }
        if (disp === "_HasAttachments") { o._HasAttachments = String(!!f.Attachments); continue; }
        const key = byDisplay.get(disp);
        let v = key ? f[key] : undefined;
        if (v && typeof v === "object") v = v.Title || v.LookupValue || v.Email || v.DisplayName || JSON.stringify(v);
        o[disp] = v === undefined || v === null ? null : String(v);
      }
      rows.push(o);
    }
    url = j["@odata.nextLink"] || null;
  }
  return rows;
}

/* ---------------- CSV fallback ---------------- */
function parseCsv(text) {
  const rows = []; let cur = [""], i = 0, q = false;
  if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
  while (i < text.length) {
    const ch = text[i];
    if (q) {
      if (ch === '"' && text[i + 1] === '"') { cur[cur.length - 1] += '"'; i += 2; continue; }
      if (ch === '"') { q = false; i++; continue; }
      cur[cur.length - 1] += ch; i++; continue;
    }
    if (ch === '"') { q = true; i++; continue; }
    if (ch === ",") { cur.push(""); i++; continue; }
    if (ch === "\r") { i++; continue; }
    if (ch === "\n") { rows.push(cur); cur = [""]; i++; continue; }
    cur[cur.length - 1] += ch; i++;
  }
  if (cur.length > 1 || cur[0] !== "") rows.push(cur);
  const head = rows.shift();
  return rows.map(r => Object.fromEntries(head.map((h, k) => [h, r[k] ?? ""])));
}

/* ---------------- main ---------------- */
const args = process.argv.slice(2);
const csvIdx = args.indexOf("--from-csv");
try {
  const rows = csvIdx >= 0
    ? parseCsv(fs.readFileSync(args[csvIdx + 1], "utf8"))
    : await fetchFromGraph();
  if (!rows.length) throw new Error("ไม่ได้ข้อมูลจากแหล่งข้อมูล (0 แถว) — ยกเลิกการเขียนไฟล์");
  const res = render(rows);
  console.log(`✔ สร้าง dashboard/index.html สำเร็จ: ${res.rows.toLocaleString()} รายการ, ${(res.bytes / 1e6).toFixed(2)} MB`);
} catch (e) {
  console.error("✖ build ล้มเหลว:", e.message);
  process.exit(1);
}
