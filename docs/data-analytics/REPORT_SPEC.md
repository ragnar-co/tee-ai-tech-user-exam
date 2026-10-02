# Report Spec

```yaml
doc_id: report_spec
filename: REPORT_SPEC.md
version: 1.0.0
status: draft
depends_on: [dashboard_spec, kpi_dictionary, metric_spec, stakeholders, sla_freshness]
also_references: [viz_design_spec, data_governance, pipeline_spec]
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

## ขอบเขตและความซื่อตรงของเอกสาร

ผลิตภัณฑ์นี้คือ **dashboard** (DASH-01..03) ไม่ใช่ระบบ scheduled reporting plan.md ไม่มีข้อกำหนด export/รายงานตามรอบ และ pipeline (PL-01, PL-02) ไม่มี step ผลิตรายงาน เอกสารนี้จึงกำหนด **รายงานขั้นต่ำ 2 ฉบับ** ที่ผลิตจากข้อมูลและ query ที่มีอยู่แล้วเท่านั้น โดยทุกฉบับมีสถานะ `proposed` (ยังไม่อนุมัติ) ค่า format / ช่องทางส่ง / schedule / deadline / distribution list ที่ไม่มีหลักฐานเป็น `null` พร้อม calibration source และ owner ไม่มีการสร้างรายชื่อผู้รับหรือตารางเวลาเอง และ **ไม่นิยาม metric/KPI ใหม่** (ใช้ MET-xx, KPI-xx เดิม)

เครื่องมือ Zoho / Slack ที่ DDD template กล่าวถึง **ไม่อยู่ใน stack ของโครงการ** (stack = Python, DuckDB, Plotly Dash — AGENTS.md) จึงไม่ถูกกำหนดเป็นช่องทางส่ง

## Report Profiles

### RPT-01 Weekly Overdue Summary Export

| หัวข้อ | รายละเอียด |
|---|---|
| Name / Purpose | Weekly Overdue Summary — สรุปสถานะ action หลังประชุมประจำสัปดาห์ (portfolio + รายโครงการ + รายการ overdue) ให้ใช้ติดตามงานนอก dashboard; ผลิตจาก latest successful run |
| Status | `proposed` (ไม่มีใน plan.md; ต้องได้รับการอนุมัติจาก `{{PROJECT_SPONSOR}}`) |
| Format | `null` — ตัวเลือกที่สอดคล้อง stack: CSV (ผ่าน Dash AG Grid export ของ CH-11/CH-15 ตาม DATA_GOVERNANCE "Column Masking") หรือ PDF/HTML ที่ render จาก Dash; ผู้ตัดสิน `{{PROJECT_SPONSOR}}` ร่วม `{{DATA_STEWARD}}`. email HTML / Zoho Analytics = ไม่มีหลักฐานว่าใช้ได้ |
| Frequency | `weekly` ผูกกับรอบ ingest (FR-01) — ความถี่จริงของ CSV = ต้องยืนยัน (KPI_DICTIONARY "Measurement Frequency"); ไม่มี cron (PIPELINE_SPEC Schedule = `null`) |
| Target Audience | STK-01 (basic), STK-02 (intermediate), STK-03 (intermediate); STK-04 เฉพาะขอบเขตที่ DATA_GOVERNANCE ตัดสิน (row-level = `null`) |
| Owner | `{{REPORT_OWNER}}` (role ยังไม่กำหนด; candidate: `{{DATA_STEWARD}}`, STK-06 `[ASSUMPTION]`) |
| Source | Q-PORTFOLIO, Q-BY-PROJECT, Q-OVERDUE-DETAIL, Q-BY-OWNER (METRIC_LOGIC) จาก `run_id` เดียวกัน; ทุก Q รับพารามิเตอร์ `project_name` (NULL = All Projects) และ **จำกัดแถวตาม project ที่เลือก** (ไม่ใช่ highlight) — รายงานต้องพิมพ์ขอบเขต (`All Projects` / ชื่อ project) ทุกหน้า และใช้ค่าเดียวกันทั้งฉบับ; ต้องพิมพ์ `run_id`, `reference_date`, source file ทุกหน้า |

### RPT-02 Executive Summary Draft (report artifact)

| หัวข้อ | รายละเอียด |
|---|---|
| Name / Purpose | Executive Summary Draft — ข้อความร่างที่บันทึกใน `executive_summaries` (DASH-03, PL-02) ส่งต่อเป็นเอกสารให้ผู้ตรวจทาน ติด label "Draft" ไม่ใช่รายงานที่อนุมัติ |
| Status | `proposed`, bonus (ตามสถานะ DASH-03; provider = `openrouter`, model = `anthropic/claude-sonnet-5`; draft) |
| Format | `null` — ผู้ตัดสิน `{{PROJECT_SPONSOR}}`; ข้อความล้วนจาก `summary_text` + header (`source_run_id`, `provider`, `model_name`, `prompt_version`, `created_at`) |
| Frequency | `on-demand` (FR-05 ไม่มี cron; ไม่สร้างอัตโนมัติ) — ความถี่ตามรอบ = `null` ผู้กำหนด `{{AUDIT_OWNER}}` (STAKEHOLDERS STK-05) |
| Target Audience | STK-05 (intermediate), STK-03 (intermediate) |
| Owner | `{{REPORT_OWNER}}` + ผู้ตรวจทานข้อความ `{{AUDITOR_OR_EXEC}}` |
| ข้อจำกัด | ห้ามระบุ severity / business impact / SLA ที่ไม่มีในข้อมูล; ตัวเลขใน summary ยังไม่ผ่านการรับรอง — ต้องเทียบกับ DASH-01 ก่อนเผยแพร่ |

## KPI Coverage

### KPIs Included

| Report | KPIs (KPI_DICTIONARY) | Metrics (METRIC_SPEC) | ที่มาของตัวเลข |
|---|---|---|---|
| RPT-01 | KPI-01, KPI-02, KPI-03 (ทั้งหมดสถานะ candidate) | MET-01..MET-05; MET-06 (optional); MET-07, MET-08 (draft) | ตรงกับ chart เดียวกับ DASH-01: CH-01..CH-04, CH-05, CH-09, CH-11; DASH-02: CH-13, CH-14, CH-15, CH-16 |
| RPT-02 | KPI-01, KPI-02, KPI-03 แบบ **context เท่านั้น** | MET-01..MET-05 (+ MET-07/MET-08 ถ้ารวมใน context — ตาม PL-02) ส่งให้โมเดล (OpenRouter) | ตาม DASHBOARD_SPEC Metric-to-Dashboard (DASH-03 = "context เท่านั้น"); ไม่มีการคำนวณใหม่ในรายงาน |

### Coverage Matrix

| KPI | RPT-01 | RPT-02 |
|---|---|---|
| KPI-01 Action Completion | ครอบคลุม | context |
| KPI-02 Overdue Action Backlog | ครอบคลุม | context |
| KPI-03 Owner Overdue Follow-up Load | ครอบคลุม (ขึ้นกับ masking `owner`) | context |

### Missing Coverage

ไม่มี KPI ที่ไม่ถูกครอบคลุม (3/3 โดย RPT-01) ข้อควรระวัง: KPI-03 ใน RPT-01 แสดง `owner` ซึ่งเป็น `confidential` — ถ้า `{{DPO_OR_LEGAL}}` ตัดสินให้ mask ROLE-01/02/05 KPI-03 จะอ่านได้เฉพาะ ROLE-03 (DATA_GOVERNANCE Column Masking) ห้ามสร้าง KPI/score ใหม่ (risk, health, owner performance) เพื่อเติมรายงาน

## Distribution Schedule

| หัวข้อ | RPT-01 | RPT-02 |
|---|---|---|
| Distribution Channel | `null` — ไม่มีหลักฐานช่องทางที่อนุมัติ; ทางเลือกต่ำสุด = ผู้ใช้ดาวน์โหลดเองจาก dashboard (ไม่มีการส่งอัตโนมัติ); ผู้ตัดสิน `{{PROJECT_SPONSOR}}` | `null` — ผู้ตัดสินเช่นเดียวกัน |
| Schedule | `null` (ไม่มี cron) — ผู้ผลิตเปิดรายงานด้วยมือหลัง run `succeeded` | on-demand |
| Deadline (วันหลัง period close) | `null` — period close = เวลาประชุมจบ/CSV พร้อม; calibration source: ข้อตกลง `{{MEETING_CHAIR}}` + delay tolerance FR-01 (SLA_FRESHNESS = `null`); owner `{{DATA_STEWARD}}` | `null` (ตาม FR-05 tolerance = `null`) |
| Distribution List | `null` — ไม่สร้างรายชื่อ; ผู้รับระดับ role = STK-01/02/03 ตาม Profile; รายชื่อจริงกำหนดโดย `{{PROJECT_SPONSOR}}` | `null` — role = STK-05/STK-03 |
| Freshness precondition | ผลิตได้ต่อเมื่อมี run `succeeded` ที่เป็น latest (AL-03) และ AL-01/AL-02 ไม่ active | `source_run_id` = latest successful run (AL-04) |

### Missed Deadline Handling

ค่า deadline เป็น `null` จึงยังตรวจ "ส่งไม่ทัน" เชิงตัวเลขไม่ได้ ที่นี่กำหนด **กติกา** ที่ใช้ทันทีเมื่อ deadline ถูกอนุมัติ (`DESIGN PROPOSAL`):

| ประเด็น | กติกา |
|---|---|
| ใครถูกแจ้ง | `{{REPORT_OWNER}}` และ L1 `{{DATA_STEWARD}}`; เลย tolerance ต่อเนื่อง -> L2 `{{MEETING_CHAIR}}` ตาม Escalation Procedures (SLA_FRESHNESS) เวลา escalate = `null` |
| ฉบับบางส่วนหรือรอครบ | **รอครบ ไม่ส่งฉบับบางส่วน** — รายงานที่ตัวเลขไม่ครบ/มาจาก run เก่าทำให้เข้าใจผิดว่าเป็นสถานะล่าสุด; ถ้าจำเป็นต้องส่ง ต้องพิมพ์ banner ว่า "ข้อมูลจาก run `{run_id}` ณ `{reference_date}` — ไม่ใช่ล่าสุด" และห้ามเรียก "final" |
| บันทึกที่ไหน | บันทึกเหตุการณ์ในรายการ report log `null` (ที่เก็บยังไม่กำหนด; ตัวเลือก: ANALYTICS_CHANGELOG หรือตารางใน DuckDB — ต้องเพิ่มใน DATA_MODEL_SPEC ก่อน); owner `{{DATA_STEWARD}}` |
| ผลตามมา | การส่งช้าซ้ำถูกนำเข้า review ของ `{{MEETING_CHAIR}}` ในที่ประชุมถัดไป; จำนวนครั้งที่ยอมรับได้ = `null` (calibration: `{{PROJECT_SPONSOR}}`) เพื่อไม่ให้ส่งช้ากลายเป็นเรื่องปกติ |
| สาเหตุจาก pipeline | run `failed` / ไม่มี CSV -> ดำเนินตาม AL-02/AL-03 และ RUNBOOK; ไม่ re-run ด้วย `reference_date` อื่นเพื่อเร่งให้ทัน |

## Template Definitions

### RPT-01 Template Layout

| ลำดับ | Section | เนื้อหา | อ้างอิง |
|---|---|---|---|
| 1 | Header | ชื่อรายงาน, `run_id`, `reference_date` (อ่านจาก run; fixed constant `2026-10-02` สำหรับ iteration 1 — ห้ามฝังในเทมเพลต), ขอบเขต project filter, source file, generated at | CH-12 |
| 2 | Portfolio Summary | Total / Completed / Open / Overdue | CH-01..CH-04 (CT-01) |
| 3 | By Project | ตารางและ bar ราย `project_name` (เมื่อเลือก 1 project = 1 แถว) | CH-11 (CT-09), CH-08 (CT-02) |
| 4 | Overdue Detail | ตารางเรียง Days Overdue DESC | CH-15 (CT-04) |
| 5 | Overdue by Owner | นับต่อ owner (ไม่ใช่คะแนนผลงาน) | CH-16 (CT-04) |
| 6 | Data Notes | ผลตรวจ quality ของ run, คำเตือนถ้า run ไม่ใช่ล่าสุด | CH-12, DATA_QUALITY |

### RPT-02 Template Layout

Header (CP-01, CP-05, CP-06) -> label "Draft" -> `summary_text` -> ข้อความกำกับ "ร่างโดย AI ต้องตรวจทาน; ตัวเลขยังไม่รับรอง" ไม่มี chart

### Chart Types

ทุก chart มาจาก `chart_type_matrix` (VIZ_DESIGN_SPEC) ไม่เลือกใหม่ที่นี่: CT-01 `kpi_card`, CT-02 `bar`, CT-04 `table`/`bar`, CT-09 `table` (project summary) — ทั้งหมดเป็นระดับ `basic` จึงผ่าน Gate Rule สำหรับ STK-01..03 ห้ามใช้ heatmap/scatter/multi-axis (CT-07/CT-08) ใน RPT-01 และ RPT-02 ไม่มี chart

### Branding

| รายการ | ค่า |
|---|---|
| Logo | `{{ORG_LOGO}}` (ไม่ระบุชื่อองค์กรในเอกสาร) |
| Color scheme | ใช้ token `series_1..series_6` ของ VIZ_DESIGN_SPEC "Color & Theme Spec" (โหมด light สำหรับพิมพ์) |
| Header / Footer | header ตาม section 1; footer = เลขหน้า + "Draft/proposed — ไม่ใช่ organizational KPI จนกว่าอนุมัติ" + `{{CONFIDENTIALITY_LABEL}}` (ค่า `null`, owner `{{DPO_OR_LEGAL}}`) |

### ข้อกำกับ PDPA ของรายงาน

รายงานที่มี `owner` / `action_name` เป็นข้อมูล `confidential` — ต้องผ่าน masking เดียวกับ dashboard (DATA_GOVERNANCE) และทุกการ export ถูก log (GOV-AUD-01) การจัดเก็บ/ระยะเก็บไฟล์รายงาน = `null` (GOV-RET) ต้องอยู่ในขอบเขต erasure

## Open Questions

1. ต้องมีรายงานตามรอบจริงหรือไม่ หรือ dashboard เพียงพอ? (`{{PROJECT_SPONSOR}}`)
2. format, ช่องทางส่ง, deadline หลังประชุม และรายชื่อผู้รับของ RPT-01/RPT-02 คืออะไร? (ทั้งหมด `null`)
3. ใครเป็น `{{REPORT_OWNER}}` และ report log เก็บที่ใด?
4. (ปิดแล้ว) `reference_date` ใน RPT = ค่าที่เก็บใน run (fixed constant `2026-10-02` สำหรับ iteration 1; เปลี่ยนได้ผ่าน ANALYTICS_CHANGELOG เท่านั้น) — ห้ามฝังค่าในเทมเพลต
5. `owner` ในรายงานต้อง mask สำหรับ role ใด? (`{{DPO_OR_LEGAL}}`)
