# Metric Specification

```yaml
doc_id: metric_spec
filename: METRIC_SPEC.md
version: 1.0.0
status: draft
depends_on: [kpi_dictionary, business_glossary, stakeholders]
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

เอกสารนี้เป็นแหล่งนิยาม metric เดียว (single source of truth) เอกสารอื่นอ้างด้วย Metric ID ชื่อ metric และ label ยึดตาม BUSINESS_GLOSSARY.md; parent KPI ยึดตาม KPI_DICTIONARY.md; consumer ยึดตาม STAKEHOLDERS.md ทุกตัวเลขคำนวณด้วย `REFERENCE_DATE` ที่เก็บต่อ run (ค่า `2026-10-02` = fixed constant for iteration 1; เปลี่ยนได้ผ่าน ANALYTICS_CHANGELOG เท่านั้น — breaking สำหรับ MET-04/MET-05/MET-07/MET-08) สูตรอยู่ใน SQL layer เท่านั้น (ห้ามเขียนซ้ำใน Dash callback)

## Enum ที่เอกสารนี้เป็นเจ้าของ

### metric_status (owner: METRIC_SPEC.md)

| value | ความหมาย |
|---|---|
| `draft` | นิยามเสนอแล้ว แต่ parent KPI ยังไม่มี owner/target อนุมัติ หรือยังไม่ผ่านการรับรอง |
| `certified` | KPI owner อนุมัติ + นิยาม version ถูกรับรอง; เปลี่ยนนิยามหลังจากนี้ = breaking change |
| `deprecated` | เลิกใช้ ต้องมี deprecation path ไปยัง metric ทดแทน |

Metric ทั้งหมดด้านล่างเป็น `draft` เพราะ parent KPI เป็น candidate (ไม่มี owner/target อนุมัติ)

## Metric Profiles

KPI ≠ Metric ≠ Dimension: dimension ที่ใช้ซอย = `project_name`, `owner`, `status`, `due_date` (นิยามใน DATA_MODEL_SPEC) — ไม่ถูกยกขึ้นเป็น metric

| Metric ID | name | Business definition | Parent KPI | Owner (team) | Refresh cadence | Primary consumer (data_literacy_level) | metric_status / version |
|---|---|---|---|---|---|---|---|
| MET-01 | `total_actions` | จำนวน action record ทั้งหมดใน scope ที่เลือก | KPI-01 | `{{DATA_STEWARD}}` / Analytics team (STK-06) `[ASSUMPTION]` | ทุก ingest run สำเร็จ (weekly `[ASSUMPTION]`) | STK-01 (basic), STK-02 (intermediate) | `draft` / 1.0.0 |
| MET-02 | `completed_actions` | จำนวน Completed Action | KPI-01 | เช่นเดียวกัน | เช่นเดียวกัน | STK-01 (basic), STK-02 (intermediate) | `draft` / 1.0.0 |
| MET-03 | `open_actions` | จำนวน Open Action | KPI-02 | เช่นเดียวกัน | เช่นเดียวกัน | STK-02 (intermediate), STK-03 (intermediate) | `draft` / 1.0.0 |
| MET-04 | `overdue_actions` | จำนวน Overdue Action | KPI-02; รอง KPI-03 เมื่อซอยด้วย `owner` | เช่นเดียวกัน | เช่นเดียวกัน | STK-01 (basic), STK-03 (intermediate), STK-04 (basic) | `draft` / 1.0.0 |
| MET-05 | `days_overdue` | จำนวนวันปฏิทินจาก due_date ถึง reference_date ของ overdue action หนึ่งรายการ | KPI-02; รอง KPI-03 | เช่นเดียวกัน | เช่นเดียวกัน | STK-02, STK-03 (intermediate), STK-04 (basic) | `draft` / 1.0.0 |
| MET-06 | `completion_rate` (optional) | สัดส่วน Completed Action ต่อ action ทั้งหมดใน scope | KPI-01 | เช่นเดียวกัน | เช่นเดียวกัน | STK-01 (basic), STK-02 (intermediate) | `draft` / 1.0.0 |
| MET-07 | `owners_with_overdue_actions` | จำนวน owner ที่ไม่ซ้ำกันซึ่งถือ overdue action อย่างน้อยหนึ่งรายการใน scope (ใช้ติดตามภาระ follow-up; ไม่ใช่คะแนนผลงาน) | KPI-03 | เช่นเดียวกัน | เช่นเดียวกัน | STK-03 (intermediate), STK-02 (intermediate) | `draft` / 1.0.0 |
| MET-08 | `open_not_overdue_actions` | จำนวน Open Action ที่ยังไม่ overdue (`open_actions − overdue_actions`) | KPI-02 | เช่นเดียวกัน | เช่นเดียวกัน | STK-02 (intermediate), STK-03 (intermediate) | `draft` / 1.0.0 |

ทุก metric มี parent KPI (ไม่มี metric ที่ไม่มีเจ้าของ); ทุก KPI-01..03 มี metric รองรับ (MET-07 -> KPI-03, MET-08 -> KPI-02; ทั้งสองเป็นนับจำนวน ไม่มี threshold) ผู้ใช้หลักทั้งหมดมี literacy ระดับ `basic` ขึ้นไป — การแสดงผลต้องเหมาะกับ `basic` (KPI card, bar chart, ตาราง)

การเปลี่ยนนิยาม metric ที่ certified แล้ว = breaking change -> บันทึกใน ANALYTICS_CHANGELOG (ANALYTICS_CHANGELOG.md) พร้อม effective date และการตัดสินว่าจะ restate history หรือเก็บนิยามเก่าคู่กัน

## Formula Reference

ฐานข้อมูล: `stg_actions` กรองด้วย `run_id = <latest successful run>` (flag `is_completed`, `is_open`, `is_overdue` นิยามที่ BUSINESS_GLOSSARY; ค่า status ที่ใช้อ้าง enum `action_status` ใน DATA_MODEL_SPEC)

| Metric | Formula (plain language) | Formula (notation) | Numerator | Denominator |
|---|---|---|---|---|
| `total_actions` | นับทุกแถวใน scope | `COUNT(*)` | - | - |
| `completed_actions` | นับแถวที่ status เป็น 'done' | `COUNT(*) FILTER (WHERE is_completed)` โดย `is_completed = (status = 'done')` | - | - |
| `open_actions` | นับแถวที่ status ไม่ใช่ 'done' | `COUNT(*) FILTER (WHERE is_open)` โดย `is_open = (status != 'done')` | - | - |
| `overdue_actions` | นับ open action ที่ due_date เร็วกว่า reference_date (วันเท่ากัน ไม่นับ) | `COUNT(*) FILTER (WHERE is_overdue)` โดย `is_overdue = status != 'done' AND due_date < reference_date` | - | - |
| `days_overdue` | ต่อ overdue action: reference_date ลบ due_date เป็นวัน | `date_diff('day', due_date, reference_date)` เมื่อ `is_overdue`; ค่าที่เก็บสำหรับ non-overdue = 0 (placeholder ไม่ใช่ metric value) | - | - |
| `completion_rate` | completed หารด้วย total; scope ว่างให้ 0 (ตาม plan SQL) | `completed_actions / total_actions` (0 ถ้า total = 0) | `completed_actions` (scope เดียวกัน) | `total_actions` (scope เดียวกัน, ไม่กรอง status) |
| `owners_with_overdue_actions` | นับ owner ที่ไม่ซ้ำ จากแถวที่ overdue ใน scope (0 ถ้าไม่มี overdue) | `COUNT(DISTINCT owner) FILTER (WHERE is_overdue)` | - | - |
| `open_not_overdue_actions` | นับ open action ที่ไม่ overdue (due_date >= reference_date) | `COUNT(*) FILTER (WHERE is_open AND NOT is_overdue)` เท่ากับ `open_actions − overdue_actions` | - | - |

ความสัมพันธ์ที่ต้องเป็นจริง (invariant): `open_actions = total_actions − completed_actions`; `overdue_actions <= open_actions`; `open_not_overdue_actions = open_actions − overdue_actions` (และ `open_not_overdue_actions + overdue_actions = open_actions`); `owners_with_overdue_actions <= overdue_actions`; `days_overdue > 0` สำหรับทุก overdue action

ค่าอ้างอิงที่ reference_date 2026-10-02 (informational, ใช้ตรวจ reconcile; ไม่ใช่ target): total 14,013; completed 8,597; open 5,416; overdue 3,531; max days_overdue 46; completion_rate ≈ 0.6135; open_not_overdue = 5,416 − 3,531 = 1,885; owners_with_overdue_actions = ค่าจาก query จริง (ยังไม่ได้ verify ในเอกสารนี้) — ห้าม hardcode ใน app

## Grain and Filter Matrix

Filter = dimension parameter: ทุก metric รับพารามิเตอร์ `project_name` (NULL / `All Projects` = ทุกโครงการ; ระบุค่า = **จำกัดแถว** ไม่ใช่ highlight) เหมือนกันทุก query; `reference_date` อ่านจาก run ที่เก็บไว้ ไม่มาจาก filter

| Metric | Grain | Required Filters | Optional Filters (dimension parameter) | Segment Breakdowns |
|---|---|---|---|---|
| `total_actions` | 1 action (`action_id`) ต่อ run | `run_id` = latest successful run | `project_name` | `project_name`, `owner`, `status`, `due_date` |
| `completed_actions` | เช่นเดียวกัน | เช่นเดียวกัน | `project_name` | `project_name`, `owner`, `due_date` |
| `open_actions` | เช่นเดียวกัน | เช่นเดียวกัน | `project_name` | `project_name`, `owner`, `status`, `due_date` |
| `overdue_actions` | เช่นเดียวกัน | `run_id`; `reference_date` ของ run นั้น | `project_name` | `project_name`, `owner`, `due_date` |
| `days_overdue` | 1 overdue action | `run_id`; `is_overdue = true` | `project_name` | `project_name`, `owner` (ดูทีละ action; ไม่นิยามค่า aggregate เช่น average ในเวอร์ชันนี้) |
| `completion_rate` | 1 scope (portfolio หรือ project) | `run_id` | `project_name` | `project_name` |
| `owners_with_overdue_actions` | 1 scope (portfolio หรือ project) | `run_id`; `reference_date` ของ run นั้น | `project_name` | `project_name` (ซอยด้วย `owner` ไม่มีความหมาย — ตัวนับ owner เอง) |
| `open_not_overdue_actions` | 1 action (`action_id`) ต่อ run | `run_id`; `reference_date` ของ run นั้น | `project_name` | `project_name`, `owner`, `status`, `due_date` |

Dimension `status` ใน matrix อ้างค่าจาก enum `action_status` ไม่ประกาศซ้ำที่นี่

## Action Thresholds

ไม่มี threshold ที่อนุมัติหรือ calibrate แล้ว ทุกค่า = `null` (ห้ามเดา) — calibration source: การอนุมัติ KPI target โดย KPI owner; calibration owner: `{{KPI_OWNER_ROLE}}`

| Metric | Warning | Critical | Required Action | Responsible Team |
|---|---|---|---|---|
| `total_actions` | `null` | `null` | ไม่กำหนด (informational; ใช้เป็นตัวส่วน/ตัวตรวจ reconcile กับ `source_row_count`) | `{{DATA_STEWARD}}` |
| `completed_actions` | `null` | `null` | ไม่กำหนด | `null` |
| `open_actions` | `null` | `null` | `null` | `{{RESPONSIBLE_TEAM}}` |
| `overdue_actions` | `null` | `null` | `null` — เบื้องต้นได้เฉพาะ practice ตาม plan: ทบทวนรายการ overdue, ยืนยัน blocker, อัปเดต due date/status ในการประชุม (ไม่ใช่ threshold) | `{{RESPONSIBLE_TEAM}}` (ผู้ติดตาม: STK-03) |
| `days_overdue` | `null` | `null` | `null` | `{{RESPONSIBLE_TEAM}}` |
| `completion_rate` | `null` | `null` | `null` | `{{RESPONSIBLE_TEAM}}` |
| `owners_with_overdue_actions` | `null` | `null` | `null` | `{{RESPONSIBLE_TEAM}}` (ผู้ติดตาม: STK-03) |
| `open_not_overdue_actions` | `null` | `null` | `null` | `{{RESPONSIBLE_TEAM}}` |

## Open Questions

1. ผู้อนุมัติ KPI-01..03 (owner/target) เพื่อเลื่อน metric เป็น `certified`
2. `REFERENCE_DATE` = 2026-10-02 ยืนยันแล้วสำหรับ iteration 1 (fixed constant); เปลี่ยนได้เฉพาะผ่าน ANALYTICS_CHANGELOG (breaking สำหรับ MET-04/MET-05)
3. ต้องการ aggregate ของ `days_overdue` (เช่น max) เป็น metric แยกหรือไม่ — ถ้าต้องการ ต้องเพิ่ม metric ใหม่พร้อม parent KPI
