# KPI Dictionary

```yaml
doc_id: kpi_dictionary
filename: KPI_DICTIONARY.md
version: 1.0.0
status: draft
depends_on: []
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

## หลักการสำคัญ (plan.md §20, §21)

ตัวเลขขั้นต่ำ (`total_actions`, `completed_actions`, `open_actions`, `overdue_actions`, `days_overdue`; รวม metric เสริม `owners_with_overdue_actions`, `open_not_overdue_actions`) **ยังไม่ใช่ organizational KPI ที่อนุมัติแล้ว** เพราะยังไม่มี KPI owner, target และ business definition ที่อนุมัติ ดังนั้นเอกสารนี้นิยามเป็น **Candidate KPI** (`approval_status: candidate`) โดย `owner` ใช้ role placeholder และ `target = null` ทุกตัว ไม่มีการเดาค่าเป้าหมาย

KPI คือผลลัพธ์ที่มีคนรับผิดชอบ; metric (METRIC_SPEC.md) คือตัวเลขที่คำนวณ; dimension (`project_name`, `owner`, `status`, `due_date` — DATA_MODEL_SPEC.md) คือสิ่งที่ใช้ซอย การซอย KPI ด้วย `project_name` (dimension parameter ที่ทุก query รับ) **ไม่ทำให้เกิด KPI ใหม่**

## KPI Catalog

| KPI ID | Name | Definition (plain language) | Owner | Target | Frequency | Business Impact | OKR / iKPI |
|---|---|---|---|---|---|---|---|
| KPI-01 | Action Completion | สัดส่วน/จำนวน action ที่ปิดแล้ว (Completed Action) เทียบกับ action ทั้งหมดใน scope | `{{KPI_OWNER_ROLE}}` (candidate: Weekly meeting chair, STK-01 — `[ASSUMPTION]`) | `null` (calibration source: การอนุมัติของ `{{PROJECT_SPONSOR}}`) | weekly `[ASSUMPTION: ตามรอบประชุม]` | ดีขึ้น = งานตามประชุมถูกปิดมากขึ้น; แย่ลง = งานสะสมไม่ปิด | `null` — ไม่มี OKR/iKPI ระบุ `{{OKR_REFERENCE}}` |
| KPI-02 | Overdue Action Backlog | จำนวน open action ที่เลยกำหนด ณ reference date และระยะเวลาที่เลย | `{{KPI_OWNER_ROLE}}` (candidate: Security team lead, STK-03 — `[ASSUMPTION]`) | `null` (source: `{{PROJECT_SPONSOR}}`) | weekly | ลดลง = ภาระ follow-up ลดลง; เพิ่มขึ้น = ต้องติดตามเพิ่ม (ไม่ระบุ severity/impact เพราะ source ไม่มีข้อมูล) | `null` |
| KPI-03 | Owner Overdue Follow-up Load | จำนวน overdue action ที่แต่ละ owner ถือ ใช้กำหนดผู้ที่ต้องติดตาม — **ไม่ใช่คะแนนผลงาน** (ห้ามสร้าง owner performance score) | `{{KPI_OWNER_ROLE}}` (candidate: Security team lead, STK-03) | `null` | weekly | ช่วยจัดลำดับการติดตามรายบุคคล | `null` |

ทุก KPI: `approval_status = candidate` (ค่าที่ควรอนุมัติ: owner + target + definition). `Target — numeric` ของ template = **null จนกว่าอนุมัติ**

### Metric ที่สนับสนุน (ดูสูตรใน METRIC_SPEC.md)

| KPI | Metrics (ID ใน METRIC_SPEC.md) |
|---|---|
| KPI-01 | `total_actions` (MET-01), `completed_actions` (MET-02), `completion_rate` (MET-06, optional) |
| KPI-02 | `open_actions` (MET-03), `overdue_actions` (MET-04), `days_overdue` (MET-05), `open_not_overdue_actions` (MET-08) |
| KPI-03 | `owners_with_overdue_actions` (MET-07); และ `overdue_actions` (MET-04), `days_overdue` (MET-05) ซอยด้วย dimension `owner` |

### ความสามารถในการคำนวณ (coverage check)

ทุก KPI คำนวณได้จาก `stg_actions` ซึ่งได้จาก CSV ที่ลงจริง (`status`, `due_date`, `project_name`, `owner`) — ไม่ต้องใช้ข้อมูลที่ไม่มี pipeline ผลิต

### สิ่งที่ไม่นิยามเป็น KPI (Do-Not-Build)

risk/health/severity score, owner performance score, SLA compliance, on-time completion rate, cycle time, forecast — source ไม่มีข้อมูลเพียงพอ

## KPI Hierarchy (CEO to Team Level)

| ระดับ | KPI | หมายเหตุ |
|---|---|---|
| Company-level (portfolio, ผู้บริหาร/ประธานประชุม) | KPI-01, KPI-02 | ภาพรวมทุกโครงการ (12 projects ใน sample) |
| Department-level | ไม่มี KPI แยก | การดู KPI-01/KPI-02 รายโครงการ `project_name` เป็น slice ของ KPI เดียวกัน ไม่ใช่ KPI ใหม่; ตำแหน่ง department owner = `{{PROJECT_MANAGER}}` ยังไม่กำหนด |
| Team-level | KPI-03 | driver ของ KPI-02 |

Parent-child mapping:
- KPI-03 -> contributes to KPI-02 (ผลรวม overdue ของทุก owner = overdue ของ portfolio)
- KPI-01 และ KPI-02 เป็นอิสระต่อกัน (ผลรวม open = total − completed; overdue เป็นส่วนย่อยของ open)

## Measurement Frequency

| KPI | Frequency | Reporting Deadline | Data Availability |
|---|---|---|---|
| KPI-01 | weekly `[ASSUMPTION]` | `null` — calibration source: `{{MEETING_CHAIR}}`; owner `{{DATA_STEWARD}}` | หลัง CSV ประจำสัปดาห์ถูก ingest สำเร็จ (run ใหม่เป็น latest successful run) |
| KPI-02 | weekly | `null` | เช่นเดียวกัน; ตัวเลขขึ้นกับ `REFERENCE_DATE` ที่เก็บต่อ run |
| KPI-03 | weekly | `null` | เช่นเดียวกัน |

หมายเหตุ: ไม่มี timestamp ของ source; ความถี่ที่แท้จริงของ CSV ที่ส่งเข้ามา = ต้องยืนยัน

## KPI Owners

| KPI | KPI Owner | Review Cadence | Escalation Path |
|---|---|---|---|
| KPI-01 | `{{KPI_OWNER_ROLE}}` (null จนอนุมัติ) | ทุกการประชุมประจำสัปดาห์ `[ASSUMPTION]` | `null` — `{{PROJECT_SPONSOR}}` ต้องกำหนด; ไม่มี threshold ที่อนุมัติจึงยังไม่มีเงื่อนไข escalate |
| KPI-02 | `{{KPI_OWNER_ROLE}}` | ทุกการประชุมประจำสัปดาห์ | `null` |
| KPI-03 | `{{KPI_OWNER_ROLE}}` | ทุกการประชุมประจำสัปดาห์ | `null` |

Data steward ของ KPI (ผู้รับผิดชอบความถูกต้องของข้อมูล): `{{DATA_STEWARD}}` (STK-06)

## ข้อมูล informational ที่ REFERENCE_DATE = 2026-10-02 (fixed constant for iteration 1)

ค่าที่สังเกตจาก sample ไม่ใช่ target: total 14,013; completed 8,597; open 5,416; overdue 3,531; max days_overdue 46 — ใช้ตรวจ reconcile เท่านั้น ห้าม hardcode ใน dashboard

## Open Questions

1. ใครคือ KPI owner และ target ที่อนุมัติของ KPI-01..03? (จนกว่าตอบ ทั้งสามเป็น candidate)
2. มี OKR/iKPI ที่ KPI เหล่านี้สนับสนุนหรือไม่?
