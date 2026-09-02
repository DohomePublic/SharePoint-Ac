#!/usr/bin/env node
/**
 * rebuild-from-data.mjs
 * ------------------------------------------------------------------
 * สร้าง dashboard/index.html ใหม่จาก dashboard/data.json ที่มีอยู่แล้ว
 * โดยไม่ต้องเชื่อมต่อ SharePoint
 *
 * ใช้เมื่อ:
 *   - แก้ template.html (หน้าตา/กราฟ) แต่ยังไม่ต้องการดึงข้อมูลใหม่
 *   - ยังไม่ได้ตั้ง AZURE_* secrets
 *   - กด Run workflow แล้วติ๊ก skip_refresh
 *
 * รัน: node scripts/rebuild-from-data.mjs
 * ------------------------------------------------------------------
 */
import fs from "node:fs";
import path from "node:path";
import { COLS, render } from "./build-snapshot.mjs";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const DATA_JSON = path.join(ROOT, "dashboard", "data.json");

if (!fs.existsSync(DATA_JSON)) {
  console.error("✖ ไม่พบ dashboard/data.json — ต้องรัน build-snapshot.mjs อย่างน้อยหนึ่งครั้งก่อน");
  process.exit(1);
}

/** คลาย dictionary-encoded payload กลับเป็น array ของ object */
function unpack(p) {
  if (Array.isArray(p)) return p;
  if (!p || !p.c || !p.v) throw new Error("รูปแบบ data.json ไม่ถูกต้อง");
  const out = new Array(p.n);
  for (let i = 0; i < p.n; i++) {
    const o = {};
    for (let j = 0; j < p.c.length; j++) { const ix = p.v[j][i]; o[p.c[j]] = ix < 0 ? null : p.d[j][ix]; }
    out[i] = o;
  }
  return out;
}

try {
  const j = JSON.parse(fs.readFileSync(DATA_JSON, "utf8"));
  const rows = unpack(j.data || j);
  if (!rows.length) throw new Error("data.json มี 0 แถว");

  // ตรวจว่าคอลัมน์ยังตรงกับที่ dashboard ต้องการ
  const missing = COLS.filter(c => !(c in rows[0]));
  if (missing.length) throw new Error("data.json ขาดคอลัมน์: " + missing.join(", "));

  const res = render(rows);
  console.log(`✔ rebuild จาก data.json (build เดิมเมื่อ ${j.builtAt || "-"})`);
  console.log(`✔ dashboard/index.html : ${res.rows.toLocaleString()} รายการ, ${(res.bytes / 1e6).toFixed(2)} MB`);
} catch (e) {
  console.error("✖ rebuild ล้มเหลว:", e.message);
  process.exit(1);
}
