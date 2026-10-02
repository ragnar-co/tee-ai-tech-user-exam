# Data Stakeholders

```yaml
doc_id: stakeholders
filename: STAKEHOLDERS.md
version: 1.0.0
status: draft
depends_on: []
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

เอกสารนี้ระบุกลุ่มผู้ใช้ข้อมูล (data consumers) ของ dashboard ที่วิเคราะห์ Action Item CSV หลังประชุมประจำสัปดาห์ ใช้ **role placeholder** เท่านั้น ไม่มีชื่อบุคคล ข้อมูลทุกจุดที่ **ไม่ได้มาจาก plan.md โดยตรง** ถูกทำเครื่องหมาย `[ASSUMPTION]` และต้องได้รับการยืนยันจากผู้รับผิดชอบก่อนเปลี่ยนสถานะเป็น approved

> สถานะการยืนยัน: ทั้งรายชื่อ stakeholder, literacy level, pain points และ cadence เป็น **inferred assumptions** (plan.md ระบุเพียง workflow "ประชุมประจำสัปดาห์ -> ส่ง CSV" และคำถามหลัก "โครงการใดมีงานค้าง งานใด overdue ใครเป็น owner") — รอยืนยันโดย `{{PROJECT_SPONSOR}}`

## Enum ที่เอกสารนี้เป็นเจ้าของ

### data_literacy_level (owner: STAKEHOLDERS.md)

| value | ความหมาย |
|---|---|
| `basic` | อ่าน KPI card, bar chart และตารางที่กรองด้วย dropdown ได้; ไม่เขียน query เอง |
| `intermediate` | เปรียบเทียบหลาย dimension, ตีความ stacked/grouped chart, heatmap/scatter/crosshair ได้ |
| `advanced` | อ่านและตรวจ SQL/metric definition ได้, ใช้ multi-axis/custom visualization ได้ |

เอกสารอื่น (METRIC_SPEC, VIZ_DESIGN_SPEC, DASHBOARD_SPEC) อ้างอิงชื่อ enum นี้ ห้ามประกาศค่าซ้ำ

### data_need_priority (owner: STAKEHOLDERS.md)

| value | ความหมาย |
|---|---|
| `P0` | ขาดไม่ได้ (cannot operate without) |
| `P1` | สำคัญ (important) |
| `P2` | มีก็ดี (nice to have) |

## Stakeholder Profiles

| ID | Role (placeholder) | Team (`{{...}}` = ต้องระบุ) | data_literacy_level | preferred_format |
|---|---|---|---|---|
| STK-01 | Weekly meeting chair — `{{MEETING_CHAIR}}` | `{{CYBERSECURITY_PROGRAM_OFFICE}}` | basic `[ASSUMPTION]` | dashboard (หน้า Portfolio Overview) |
| STK-02 | Project manager — `{{PROJECT_MANAGER}}` (หนึ่งคนต่อโครงการ P01..P12) | `{{PROJECT_TEAM}}` | intermediate `[ASSUMPTION]` | dashboard (project filter + Overdue Actions) |
| STK-03 | Security team lead — `{{SECURITY_TEAM_LEAD}}` | `{{SECURITY_TEAM}}` | intermediate `[ASSUMPTION]` | dashboard + Executive Summary draft (bonus) |
| STK-04 | Action owner — `{{ACTION_OWNER}}` (ตัวตนใน data = pseudonymous `Owner-NNN`; mapping กับบุคคลจริง = unknown) | `{{OWNER_TEAM}}` | basic `[ASSUMPTION]` | dashboard (ตาราง overdue ที่ filter ตนเอง) |
| STK-05 | Auditor / exec reviewer — `{{AUDITOR_OR_EXEC}}` | `{{AUDIT_OR_EXEC_OFFICE}}` | intermediate `[ASSUMPTION]` | report / Executive Summary + ตรวจย้อนรอยถึง run_id |
| STK-06 | Data steward / dashboard maintainer — `{{DATA_STEWARD}}` (ผู้รัน `src.ingest`) | `{{ANALYTICS_TEAM}}` | advanced `[ASSUMPTION]` | self-service query (DuckDB SQL) + CLI |

### รายละเอียดรายกลุ่ม

**STK-01 Weekly meeting chair** — cadence: ทุกสัปดาห์ หลังประชุม (ผูกกับรอบ ingest)
- Critical questions: ภาพรวม portfolio ตอนนี้เป็นอย่างไร (total/completed/open/overdue)? โครงการใดมี overdue มากที่สุด?
- Pain points `[ASSUMPTION]`: ต้องรวมงานจากหลายไฟล์ CSV ด้วยมือ; ตัวเลขต่างกันเมื่อคำนวณคนละวันที่อ้างอิง

**STK-02 Project manager** — cadence: ทุกสัปดาห์ และก่อนประชุมถัดไป
- Critical questions: ในโครงการของฉันมีงานใดเลยกำหนด ใครเป็น owner ช้ากี่วัน?
- Pain points `[ASSUMPTION]`: ไม่มีมุมมองเฉพาะโครงการที่ตัวเลขตรงกับ portfolio

**STK-03 Security team lead** — cadence: ทุกสัปดาห์
- Critical questions: owner ใดมีงานเลยกำหนดค้างอยู่ (นับจำนวนเท่านั้น ไม่ใช่คะแนนผลงาน); ต้อง follow-up ข้อใดก่อน (เรียงตาม days_overdue)?
- Pain points `[ASSUMPTION]`: ไม่มีรายการ overdue เรียงลำดับที่ตรวจสอบได้

**STK-04 Action owner** — cadence: ทุกสัปดาห์
- Critical questions: งานของฉันอันใดเลยกำหนดแล้วและช้ากี่วัน?
- Pain points `[ASSUMPTION]`: ไม่ทราบว่าตัวเลขคำนวณจากวันที่อ้างอิงใด
- หมายเหตุ: ขอบเขตการมองเห็นระดับแถว (row-level) เป็นหน้าที่ DATA_GOVERNANCE.md — ที่นี่บันทึกเป็นความคาดหวัง: `null` จนกว่าจะตัดสิน

**STK-05 Auditor / exec reviewer** — cadence: ตามรอบรายงาน/ตรวจสอบ `[ASSUMPTION]` (ความถี่ = null, ผู้กำหนด `{{AUDIT_OWNER}}`)
- Critical questions: ตัวเลขนี้มาจาก source file/run ใด และ reference date ใด? Executive Summary ถูกสร้างจากข้อมูลใด?
- Pain points `[ASSUMPTION]`: ตรวจย้อนรอยตัวเลขไม่ได้

**STK-06 Data steward** — cadence: ทุกครั้งที่รับ CSV ใหม่ (ทุกสัปดาห์)
- Critical questions: ไฟล์ผ่าน validation หรือไม่? row count reconcile หรือไม่? พบ status ใหม่ที่ไม่รู้จักหรือไม่?
- Pain points `[ASSUMPTION]`: แถวไม่ถูกต้องอาจถูกทิ้งเงียบ ๆ (plan ห้ามกรณีนี้)

## Data Needs Matrix

ตาราง Stakeholder × KPI (KPI ID จาก KPI_DICTIONARY.md) — ค่า = `data_need_priority`; `-` = ไม่เกี่ยวข้อง

| Stakeholder | KPI-01 Action Completion | KPI-02 Overdue Action Backlog | KPI-03 Owner Overdue Follow-up Load |
|---|---|---|---|
| STK-01 Meeting chair | P0 | P0 | P2 |
| STK-02 Project manager | P0 | P0 | P1 |
| STK-03 Security team lead | P1 | P0 | P0 |
| STK-04 Action owner | P2 | P1 | P0 |
| STK-05 Auditor / exec | P1 | P1 | P2 |
| STK-06 Data steward | P1 | P1 | P1 |

(ระดับ priority ทั้งหมดเป็น `[ASSUMPTION]` รอ `{{PROJECT_SPONSOR}}` ยืนยัน)

### Freshness requirement

| Stakeholder | ความสดของข้อมูลที่ต้องการ |
|---|---|
| STK-01..STK-06 | ข้อมูลจาก **latest successful run** ที่โหลดหลังการประชุมประจำสัปดาห์ (weekly) |

ค่า freshness tolerance เชิงตัวเลข (เช่น ชั่วโมงหลังประชุม) = `null` — calibration source: ข้อตกลงกับ `{{MEETING_CHAIR}}` ว่า CSV ส่งมาเมื่อใด; owner: `{{DATA_STEWARD}}`; เอกสารเจ้าของ: SLA_FRESHNESS.md

## ความคาดหวังต่อเอกสารปลายน้ำ (เอกสารมีครบแล้ว; ใช้ตรวจ consistency)

| เอกสาร | ความคาดหวัง |
|---|---|
| DASHBOARD_SPEC.md | หน้า Portfolio Overview DASH-01 (STK-01/02), Overdue Actions DASH-02 (STK-02/03/04), Executive Summary DASH-03 [bonus] (STK-03/05) — ID กำหนดที่ DASHBOARD_SPEC; project filter (`project_name`) รับโดยทุก query |
| REPORT_SPEC.md | Executive Summary draft สำหรับ STK-05; ความถี่/ช่องทางส่ง = null จนกว่าตัดสิน |
| DATA_GOVERNANCE.md | role-to-team mapping และ row-level scope ของ STK-04 = null; `{{DATA_STEWARD}}` เป็นผู้ถือสิทธิ์ ingest |

## Role Placeholder Registry (นิยามครั้งเดียวที่นี่)

placeholder ที่ไม่ใช่ STK-01..06 ด้านบน — เอกสารอื่นอ้างชื่อ ไม่นิยามซ้ำ ตัวบุคคล/ทีมจริงทุกตัว = `null` จนกว่า `{{PROJECT_SPONSOR}}` กำหนด

| Placeholder | นิยามบทบาท |
|---|---|
| `{{PROJECT_SPONSOR}}` | ผู้อนุมัติ scope, stakeholder list, KPI owner/target, งบ/วัน go-live |
| `{{KPI_OWNER_ROLE}}` | บทบาทเจ้าของ KPI หนึ่งตัว (candidate ใน KPI_DICTIONARY; ยังไม่อนุมัติ) |
| `{{DATA_ENGINEER}}` | ผู้พัฒนา pipeline: `src/ingest.py`, `sql/`, DuckDB schema, data quality checks (ผู้ลงมือ TSK ฝั่ง ingest/SQL ใน TASKS.md) |
| `{{DASHBOARD_DEVELOPER}}` | ผู้พัฒนา/ดูแล Plotly Dash app (DASH-01..03), AG Grid, charts ตาม DASHBOARD_SPEC / VIZ_DESIGN_SPEC (`{{DASHBOARD_BUILDER}}` ที่พบในเอกสารอื่น = ชื่อเดียวกัน ให้แก้เป็น `{{DASHBOARD_DEVELOPER}}`) |
| `{{DPO_OR_LEGAL}}` | ผู้รับผิดชอบ PDPA / legal basis / data residency |
| `{{AUDIT_OWNER}}` | ผู้กำหนดรอบรายงาน/ตรวจสอบของ STK-05 |
| `{{CONTRACT_OWNER}}` / `{{PRODUCER_TEAMS}}` | ผู้ดูแลสัญญาข้อมูล CSV / ทีมผู้ผลิต CSV ฝั่ง source (DATA_CONTRACT.md) |
| `{{REPORT_OWNER}}` | ผู้รับผิดชอบรายงาน Executive Summary (REPORT_SPEC.md) |
| `{{RESPONSIBLE_TEAM}}` | ทีมผู้ติดตามผล metric (ใน METRIC_SPEC Action Thresholds); ยังไม่กำหนด = `null` |

## Open Questions

1. ใครคือ `{{PROJECT_SPONSOR}}` ผู้อนุมัติรายชื่อ stakeholder และ KPI owner?
2. STK-04 ต้องเห็นเฉพาะงานของตนเองหรือทั้ง portfolio (PDPA: `owner` เป็น pseudonymous ID)?
3. มี stakeholder กลุ่มอื่น (เช่น หัวหน้าโครงการระดับ executive) ที่ต้องเพิ่มหรือไม่?
