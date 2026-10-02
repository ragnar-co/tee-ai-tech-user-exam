# Dashboard Spec

```yaml
doc_id: dashboard_spec
filename: DASHBOARD_SPEC.md
version: 1.0.0
status: draft
depends_on: [metric_spec, kpi_dictionary, data_model_spec, stakeholders, testing_strategy, viz_design_spec]
also_references: [metric_logic, business_glossary, pipeline_spec, sla_freshness, data_governance]
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

เอกสารนี้เป็นแหล่งนิยาม dashboard เดียว (canonical) ของ analytics stack: dashboard ID, chart ID, filter, drill-down และ acceptance criteria เอกสารนี้ **ไม่นิยามสูตร metric ใหม่** — ตัวเลขทุกตัวอ้าง Metric ID (MET-xx, METRIC_SPEC.md) และ Query ID (Q-*, METRIC_LOGIC.md) เท่านั้น; label ยึด BUSINESS_GLOSSARY.md "Label บน dashboard"; chart type ยึด `chart_type_matrix` (CT-xx) ของ VIZ_DESIGN_SPEC.md; literacy ยึด enum `data_literacy_level` (STAKEHOLDERS.md) และ Gate Rule ใน VIZ_DESIGN_SPEC.md

> **สถานะการ implement/ยืนยัน (2026-10-02):** ทั้งสามหน้า implement แล้ว; ยืนยันผ่าน Flask test client และ server จริง (page load, callbacks, project filter, no-data states) และ headless Chrome screenshot ครั้งเดียว **ไม่ได้ตรวจด้วยตา:** dark theme, colorblind mode, AG Grid; AI: pytest ใช้ mocked HTTP แต่เรียก OpenRouter จริงสำเร็จ 2 ครั้งผ่านปุ่ม Generate (All Projects และ `P01 - Network VA`, 2026-10-02; ยังไม่ได้ประเมินคุณภาพ EV-01..EV-05); CH-10 แกน 0–100%

เอกสารนี้ **resolve placeholder** ที่เอกสารอื่นเคยทิ้งไว้ (D6: VIZ_DESIGN_SPEC ใช้ `DASH-01/02/03` แล้ว; เอกสารอื่นที่ยังมี `{{DASH_*}}` ต้องแทนที่ตามตาราง):

| Placeholder | ID ที่กำหนดที่นี่ | ชื่อหน้า | ใช้อยู่ใน |
|---|---|---|---|
| `{{DASH_PORTFOLIO}}` | `DASH-01` | Portfolio Overview | SLA_FRESHNESS (FR-01, FR-02, FR-04), VIZ_DESIGN_SPEC (Interaction Spec) |
| `{{DASH_OVERDUE}}` | `DASH-02` | Overdue Actions | SLA_FRESHNESS (FR-01, FR-02), VIZ_DESIGN_SPEC |
| `{{DASH_EXEC_SUMMARY}}` | `DASH-03` | Executive Summary (bonus, **draft**) | SLA_FRESHNESS (FR-05) |

## Dashboard Inventory

| Dashboard ID | Dashboard Name (version) | Tool / Platform | URL / Access Path | Owner |
|---|---|---|---|---|
| `DASH-01` | Portfolio Overview (1.0.0, draft) | Plotly Dash app เดียว (`dashboard/app.py`; 3 หน้าสลับด้วย `dcc.Location` ไม่ใช่ Dash multi-page; `dashboard/pages/` ว่าง) + Dash AG Grid + Plotly charts | route `/` (implement); host/port = env `DASH_HOST`/`DASH_PORT` default `127.0.0.1:8050`, DB = `DASH_DB_PATH`, `DASH_DEBUG`; production deployment = `null` (ไม่มี production tier — TESTING_STRATEGY "Environment promotion"; owner `{{PROJECT_SPONSOR}}`) | Analytics team `{{ANALYTICS_TEAM}}`; maintainer `{{DASHBOARD_DEVELOPER}}`; data steward `{{DATA_STEWARD}}` |
| `DASH-02` | Overdue Actions (1.0.0, draft) | เช่นเดียวกัน | route `/overdue` (implement) | เช่นเดียวกัน |
| `DASH-03` | Executive Summary (1.0.0, **draft — bonus**) | เช่นเดียวกัน + OpenRouter (env `OPENAI_API_KEY` / `OPENAI_BASE_URL`; model `anthropic/claude-sonnet-5`) | route `/executive-summary` (implement) | เช่นเดียวกัน; ผู้ตรวจ summary = `{{SECURITY_TEAM_LEAD}}` (STK-03) `[ASSUMPTION]` |

กฎร่วมทุกหน้า (ที่มา plan.md §11-13, CON-07/CON-08/CON-09):
- **Read-only:** ไม่มี control แก้ `owner` / `due_date` / `status`; ข้อยกเว้นเดียวคือ `DASH-03` เขียน `executive_summaries` (PL-02)
- **ไม่มี hidden logic:** callback เรียก Q-* ผ่าน data access layer (`src/metrics.py`) เท่านั้น ห้ามคำนวณ `date_diff` / `due_date <` / `status != 'done'` ใน Dash
- **Do-Not-Build:** ไม่มี risk/health/severity score, owner performance score, SLA compliance, on-time rate, cycle time, forecast; ไม่มีสีเขียว/แดงหรือลูกศร trend เพราะ target/threshold ทุกตัว = `null` (KPI_DICTIONARY, METRIC_SPEC Action Thresholds)
- **Provenance header (ทุกหน้า):** `Reference date` (`ingestion_runs.reference_date` ของ latest successful run; ค่าปัจจุบัน `2026-10-02` = fixed constant ที่ผู้ใช้ยืนยันสำหรับ iteration 1 อ่านจาก run ไม่ hardcode ใน app), `Source` (`source_file`), `Loaded` (`completed_at`), `run_id` — รองรับ T-D08 และ SLA_FRESHNESS "Staleness ของ dashboard"
- **Run ที่ใช้:** latest successful run ตาม `latest_run.sql` (METRIC_LOGIC) ทุก query; ไม่เคยอ่าน run `failed`

## Dashboard Profiles

### DASH-01 Portfolio Overview

| หัวข้อ | รายละเอียด |
|---|---|
| Name | Portfolio Overview |
| Purpose | ตอบ "โครงการใดมีงานค้าง และภาพรวม portfolio เป็นอย่างไร" ก่อนเข้าประชุม (plan.md §11; STK-01 critical questions) |
| Target User | STK-01 Weekly meeting chair (primary, `basic`), STK-02 Project manager (`intermediate`); ตาม METRIC_SPEC primary consumer ⇒ ทุก chart ต้อง `complexity_level = basic` (Gate Rule) |
| Data Source | `stg_actions` (+ `ingestion_runs` สำหรับ header; `data_quality_results` สำหรับแผง CH-12) ผ่าน Q-PORTFOLIO, Q-BY-PROJECT (DATA_MODEL_SPEC); ทุก Q รับพารามิเตอร์ `project_name` (NULL = All Projects) |
| Acceptance Criteria | T-D01, T-D02, T-D03, T-D04, T-D06, T-D07, T-D08, T-D09, T-D10, T-D11 (TESTING_STRATEGY) ครบ; เพิ่ม: (a) ผลรวมแถวใน CH-11 = ค่าบน CH-01..CH-04 ในทุก scope (All Projects และ single project: เลือก 1 project ⇒ CH-11/CH-06..08 เหลือ 1 แถว/แท่ง ค่าเท่า KPI card; invariant Q-BY-PROJECT = Q-PORTFOLIO); (b) ทุก chart ตรงแถว CT-xx ที่ระบุด้านล่าง; (c) KPI card ไม่มีสี alert/ลูกศร trend |

**Chart Inventory — DASH-01**

| Chart ID | ชื่อบน dashboard | chart_type | Metric | Query | chart_type_matrix | complexity / min literacy | หมายเหตุ |
|---|---|---|---|---|---|---|---|
| CH-01 | Total Actions | `kpi_card` | MET-01 | Q-PORTFOLIO | CT-01 | basic | แสดง reference_date + run_id ใกล้การ์ด |
| CH-02 | Completed | `kpi_card` | MET-02 | Q-PORTFOLIO | CT-01 | basic | |
| CH-03 | Open | `kpi_card` | MET-03 | Q-PORTFOLIO | CT-01 | basic | |
| CH-04 | Overdue | `kpi_card` | MET-04 | Q-PORTFOLIO | CT-01 | basic | คลิก = ไป `DASH-02` (Interaction Spec) |
| CH-05 | Completion Rate (optional) | `kpi_card` | MET-06 | Q-PORTFOLIO (`completion_rate`) | CT-01 | basic | แสดงเฉพาะเมื่อ `total_actions > 0`; ห้ามแสดง 0% ตอน scope ว่าง |
| CH-06 | Total Actions by Project | `bar` แนวนอน เรียงมาก→น้อย | MET-01 | Q-BY-PROJECT | CT-02 | basic | แกนเริ่มที่ 0 |
| CH-07 | Completed by Project | `bar` แนวนอน | MET-02 | Q-BY-PROJECT | CT-02 | basic | |
| CH-08 | Overdue by Project | `bar` แนวนอน | MET-04 | Q-BY-PROJECT | CT-02 | basic | สี role `overdue` + label ตัวเลขกำกับ |
| CH-09 | Composition by Project (completed / open non-overdue / overdue) | `stacked_bar` | MET-02, MET-08, MET-04 | Q-BY-PROJECT | CT-02 (stacked) | intermediate | **อยู่ใน v1 (un-deferred, D4)** เป็น view ที่ผู้ใช้เปิดเอง (ไม่ใช่ค่าเริ่มต้น) ระบุ min literacy `intermediate` ที่หัว chart; "open non-overdue" = MET-08 `open_not_overdue_actions` (draft) ที่ SQL layer ไม่คำนวณใน Dash |
| CH-10 | Completion Rate by Project (optional) | `bar` แกน 0–100% | MET-06 | Q-BY-PROJECT | CT-03 | basic | |
| CH-11 | Project summary table | `table` (Dash AG Grid) | MET-01, MET-02, MET-03, MET-04, MET-06 | Q-BY-PROJECT | CT-09 (project summary table) | basic | คอลัมน์: Project, Total Actions, Completed, Open, Overdue, Completion Rate |
| CH-12 | Run & validation summary (**ถอดออกจากหน้า — ผู้ใช้ตัดสินใจ 2026-10-02**; component `cards.dq_panel` และ `metrics.data_quality_summary` ยังอยู่ ไม่ได้ต่อกับหน้า) | `table` | — (ไม่ใช่ metric; count จาก `ingestion_runs`, `data_quality_results`) | อ่านตรงผ่าน data access layer | `table` (basic) | basic | แสดง source file, run_id, `source_row_count` / `valid_row_count` / `invalid_row_count`, finding ต่อ `check_name` และ `rule_severity` (DATA_QUALITY "Quality Dashboards"; plan.md Phase 7); ไม่มี quality score (`null`) |

หมายเหตุ Gate: plan.md §11 อนุญาต grouped/stacked bar แต่เป็น `intermediate` ขณะที่ primary = `basic` ⇒ ค่าเริ่มต้นเป็นชุด `bar` (CH-06..08) ตามที่ VIZ_DESIGN_SPEC ตัดสินไว้ และ CH-09 เป็น view ที่ผู้ใช้เปิดเองพร้อมระบุ min literacy (ซ่อนจาก STK-01 โดยค่าเริ่มต้น)

### DASH-02 Overdue Actions

| หัวข้อ | รายละเอียด |
|---|---|
| Name | Overdue Actions |
| Purpose | ตอบทันทีว่า "งานใดเลยกำหนด ใครเป็นผู้รับผิดชอบ และล่าช้ากี่วัน" (plan.md §12) |
| Target User | STK-03 Security team lead (`intermediate`), STK-02 Project manager (`intermediate`), STK-04 Action owner (`basic`; ขอบเขต row-level = `null`) ⇒ primary รวมมี `basic` ⇒ ทุก chart `basic` |
| Data Source | `stg_actions` ผ่าน Q-PORTFOLIO (MET-04), Q-OVERDUE-DETAIL (MET-05), Q-BY-OWNER (MET-04 ต่อ owner), MET-07 (CH-14) จาก Q-PORTFOLIO, Q-BY-PROJECT (CH-17) — ทุก Q รับ `project_name` |
| Acceptance Criteria | T-D03 (CH-13), T-D04, T-D05, T-D07, T-D08, T-D09, T-D10, T-D11; เพิ่ม: (a) จำนวนแถว CH-15 = ค่า CH-13 ในทุก scope; (b) ผลรวม CH-16 = ค่า CH-13; (c) ไม่มีคอลัมน์/ป้ายที่ implied คะแนนหรืออันดับผลงานบุคคล (CON-09); (d) แถวเรียง `days_overdue` DESC โดยค่าเริ่มต้น |

**Chart Inventory — DASH-02**

| Chart ID | ชื่อบน dashboard | chart_type | Metric | Query | chart_type_matrix | complexity / min literacy | หมายเหตุ |
|---|---|---|---|---|---|---|---|
| CH-13 | Overdue Actions | `kpi_card` | MET-04 | Q-PORTFOLIO | CT-01 | basic | |
| CH-14 | Owners with Overdue Actions | `kpi_card` | MET-07 `owners_with_overdue_actions` (draft; KPI-03) | Q-PORTFOLIO (MET-07 คืนจาก Q-PORTFOLIO; implement ตามนี้) | CT-01 | basic | นับ `COUNT(DISTINCT owner)` ของแถว overdue ตามนิยาม METRIC_SPEC/METRIC_LOGIC (ไม่นับใน Dash); เป็นจำนวน ไม่ใช่คะแนน/อันดับผลงานบุคคล |
| CH-15 | Overdue Actions table | `table` (Dash AG Grid) | MET-05 (+ แถวของ MET-04) | Q-OVERDUE-DETAIL | CT-04 | basic | คอลัมน์ด้านล่าง |
| CH-16 | Overdue Actions by Owner | `bar` แนวนอน top-N | MET-04 ซอย `owner` (KPI-03) | Q-BY-OWNER | CT-04 (ranking ต่อ owner → `bar`) | basic | N = `null` (owner `{{DASHBOARD_DEVELOPER}}`; VIZ_DESIGN_SPEC Open Question 3); series เดียว สี neutral; ไม่มี rank number/leaderboard; ใช้ `owner` เป็น pseudonymous ID |
| CH-17 | Overdue Actions by Project | `bar` แนวนอน | MET-04 | Q-BY-PROJECT | CT-02 | basic | optional; แสดงเฉพาะโหมด All Projects (single project = 1 แท่ง จึงซ่อน) |

**CH-15 คอลัมน์ (AG Grid)** — sort ค่าเริ่มต้น `Days Overdue` DESC (tie-break `due_date` ASC ตาม Q-OVERDUE-DETAIL):

| ลำดับ | Header บน grid | Field ใน Q-OVERDUE-DETAIL | ที่มาของค่า |
|---|---|---|---|
| 1 | Project | `project_name` | dimension |
| 2 | Action | `action_name` | dimension (`confidential` — ดู Access) |
| 3 | Owner | `owner` | dimension (`confidential`, pseudonymous `Owner-NNN`) |
| 4 | Due Date | `due_date` | dimension (ISO `YYYY-MM-DD`) |
| 5 | Days Overdue | `days_overdue` | MET-05 |
| 6 | Status | `status` | ค่าตาม enum `action_status` (DATA_MODEL_SPEC; แสดงค่าตามที่เก็บ ไม่ map ใหม่) |

`action_id` เป็น row id ภายใน (ซ่อน) ไม่เป็นคอลัมน์ที่แสดง; sort/filter ราย column ได้ด้วย AG Grid; ขนาดหน้า = `null` (owner `{{DASHBOARD_DEVELOPER}}`; ตัดสินจากประสิทธิภาพจริง) Export (ถ้าเปิด) ต้องผ่าน masking เดียวกับที่แสดง (DATA_GOVERNANCE Column Masking)

### DASH-03 Executive Summary — **DRAFT (bonus)**

> สถานะ **draft / bonus**: ไม่อยู่ใน minimum scope; provider = OpenRouter, model = `anthropic/claude-sonnet-5` (ผู้ใช้ตัดสินใจ iteration 1; `model_status` = `experimental`); ทุก summary ที่แสดงต้องติด label "Draft" และห้ามระบุ severity / business impact / SLA ที่ไม่มีในข้อมูล (plan.md §13; T-A01, T-A04)

| หัวข้อ | รายละเอียด |
|---|---|
| Name | Executive Summary |
| Purpose | สรุปสถานะจาก DuckDB เป็นข้อความร่างให้ผู้ตรวจทาน — ไม่ใช่รายงานที่อนุมัติ (REPORT_SPEC.md เป็นเจ้าของรูปแบบรายงาน RPT-02) |
| Target User | STK-03 (`intermediate`), STK-05 Auditor/exec reviewer (`intermediate`); ไม่มี chart จึงไม่ติด Gate Rule |
| Data Source | `executive_summaries` (อ่าน/เขียน); context ที่ส่ง OpenRouter มาจากผลของ Q-PORTFOLIO, Q-BY-PROJECT, Q-OVERDUE-DETAIL เท่านั้น (PIPELINE_SPEC PL-02) โดยใช้ `project_filter` เป็นพารามิเตอร์ `project_name`; ข้อกำหนด prompt/guardrail = AI_MODEL_SPEC.md |
| Acceptance Criteria | T-A01..T-A05 (TESTING_STRATEGY), T-D08, T-D10 (ยกเว้นการเขียน `executive_summaries`); เพิ่ม: ปุ่ม Generate Draft ปิดพร้อมข้อความตั้งค่าเมื่อไม่มี env (T-A03); ถ้า `source_run_id` ≠ latest successful run ต้องแสดงคำเตือน (AL-04) |

**Component Inventory — DASH-03** (ไม่มี chart; ไม่มีตัวเลข metric ที่คำนวณในหน้านี้ — ตัวเลขใน `summary_text` สร้างโดยโมเดลจาก context และยังไม่ผ่านการรับรอง)

| Component ID | Component | ที่มา |
|---|---|---|
| CP-01 | Reference Date | `ingestion_runs.reference_date` |
| CP-02 | Project Filter (`All Projects` / project) | เช่น DASH-01; เก็บเป็น `executive_summaries.project_filter` (NULL = All Projects) |
| CP-03 | ปุ่ม Generate Draft | เรียก PL-02; ไม่มี retry อัตโนมัติ; ล้มเหลว = ข้อความอ่านเข้าใจได้ ไม่ insert ไม่แสดง summary ปลอม |
| CP-04 | Latest Saved Summary (+ label Draft) | `summary_text` ล่าสุดของ project_filter ที่เลือก |
| CP-05 | Generated At | `created_at` |
| CP-06 | Model | `provider` (= `openrouter`) / `model_name` (= `anthropic/claude-sonnet-5`) (+ `prompt_version`, `source_run_id`) + label "Draft" — ห้ามแสดง/เก็บ `OPENAI_API_KEY` |

## Metric Coverage Matrix

**GIST:** KPI ที่ไม่ปรากฏบน dashboard ใดคือ KPI ที่ไม่มีใครดู แม้ pipeline คำนวณทุกสัปดาห์ — ตารางนี้ทำให้ช่องว่างระหว่าง "วัดได้" กับ "มีคนดู" มองเห็นได้

### Metric-to-Dashboard

| Metric ID | name | label | DASH-01 | DASH-02 | DASH-03 |
|---|---|---|---|---|---|
| MET-01 | `total_actions` | Total Actions | CH-01, CH-06, CH-11 | - | context เท่านั้น |
| MET-02 | `completed_actions` | Completed | CH-02, CH-07, CH-11 | - | context เท่านั้น |
| MET-03 | `open_actions` | Open | CH-03, CH-11 | - | context เท่านั้น |
| MET-04 | `overdue_actions` | Overdue | CH-04, CH-08, CH-11 | CH-13, CH-16, CH-17 | context เท่านั้น |
| MET-05 | `days_overdue` | Days Overdue | - | CH-15 | context เท่านั้น |
| MET-06 | `completion_rate` (optional) | Completion Rate | CH-05, CH-10, CH-11 | - | - |
| MET-07 | `owners_with_overdue_actions` (draft) | Owners with Overdue Actions | - | CH-14 | context เท่านั้น |
| MET-08 | `open_not_overdue_actions` (draft) | Open (not overdue) | CH-09 | - | context เท่านั้น |

"context เท่านั้น" = ตัวเลขถูกส่งให้ provider แต่หน้า DASH-03 ไม่แสดง metric เป็น chart/card

### KPI coverage (KPI_DICTIONARY)

| KPI | สถานะ | Metric ที่รองรับ | Dashboard / Chart |
|---|---|---|---|
| KPI-01 Action Completion | candidate | MET-01, MET-02, MET-06 | DASH-01: CH-01, CH-02, CH-05, CH-10, CH-11 |
| KPI-02 Overdue Action Backlog | candidate | MET-03, MET-04, MET-05, MET-08 | DASH-01: CH-03, CH-04, CH-08, CH-09; DASH-02: CH-13, CH-15 |
| KPI-03 Owner Overdue Follow-up Load | candidate | MET-04, MET-05 ซอย `owner`, MET-07 | DASH-02: CH-14, CH-16 (นับต่อ owner), CH-15 (รายแถวต่อ owner) |

ครบทุก KPI (3/3) และทุก metric (8/8; MET-07/08 สถานะ draft) อย่างน้อยหนึ่ง dashboard การที่ CH-16 อยู่ใน v1 ทั้งที่ plan.md §12 เรียก "optional visualization" เป็นการตัดสินเพื่อให้ KPI-03 ไม่ขาด coverage — ถ้า CH-16 ถูกตัดออก KPI-03 เหลือเพียง CH-15 (ดู Open Question 3)

### Missing coverage

- ไม่มี metric ที่ไม่มี dashboard
- ไม่มีค่าแสดงผลที่ไม่มี Metric ID: CH-14 = MET-07, CH-09 = MET-08 (นิยามที่ METRIC_SPEC; SQL ที่ METRIC_LOGIC) — เอกสารนี้ไม่นิยามสูตร
- ข้อสังเกต: ตัวเลขอ้างอิงด้านล่างเป็นค่าที่ **All Projects** เท่านั้น
- ค่าอ้างอิงที่ reference date 2026-10-02 (informational ตรวจ reconcile เท่านั้น ห้าม hardcode ใน app): total 14,013; completed 8,597; open 5,416; overdue 3,531; max days_overdue 46

## Drill-down Logic

### Available Filters

| Filter | ค่า | ใช้กับ | พฤติกรรม |
|---|---|---|---|
| Project (global) | `All Projects` (ค่าเริ่มต้น) + `project_name` ทุกค่าที่ปรากฏในผล Q-BY-PROJECT (ไม่กรอง) ของ latest successful run | DASH-01, DASH-02, DASH-03 | เก็บค่าร่วมระหว่างหน้า (URL query `?project=` `[DESIGN PROPOSAL]`); ส่งเป็นพารามิเตอร์ `project_name` ให้ **ทุก Q** เพื่อจำกัดแถว ไม่กรองด้วย logic ใน Dash; ค่าที่ไม่มีอยู่จริง = ผลว่าง ไม่ error |
| Column filter/sort | AG Grid ของ CH-11, CH-15 | DASH-01, DASH-02 | client-side บนผลที่ query มาแล้ว; ไม่เปลี่ยนค่า KPI card |
| Reference date | **ไม่ใช่ filter** | - | แสดงอย่างเดียว; เปลี่ยนได้โดยสร้าง run ใหม่เท่านั้น (METRIC_LOGIC กฎ Reference Date) |

**หลักการ (D3):** Project filter **จำกัดแถว (restrict)** ในทุก chart/ตารางของทุกหน้า ไม่ใช่การ highlight — ทุก query ที่ CH-xx/CP-xx ใช้ (Q-PORTFOLIO, Q-BY-PROJECT, Q-OVERDUE-DETAIL, Q-BY-OWNER) รับพารามิเตอร์ `project_name` (NULL / `All Projects` = ทุกโครงการ) `reference_date` อ่านจาก run ที่เก็บไว้ ไม่เคยมาจาก filter

**โหมด All Projects:** KPI card = Q-PORTFOLIO ไม่ใส่ `project_name`; CH-06..09, CH-10, CH-11, CH-17 แสดงครบทุกโครงการ; CH-15 แสดง overdue ทุกโครงการ

**โหมด single project:** ทุก chart ส่ง `project_name` ให้ Q — KPI card (CH-01..05, CH-13, CH-14), CH-15, CH-16 จำกัดเฉพาะโครงการนั้น; Q-BY-PROJECT คืน **1 แถว** ⇒ CH-06..CH-11 เหลือ 1 แท่ง/1 แถว (ค่าตรงกับ KPI card); CH-17 ซ่อน (แท่งเดียวไม่ให้ข้อมูล) ไม่มีการคงโครงการอื่นไว้บนจอเพื่อเทียบ — การเทียบข้ามโครงการทำที่โหมด All Projects

### Empty / no-data state

| สถานการณ์ | พฤติกรรม | อ้างอิง |
|---|---|---|
| ยังไม่มี run `succeeded` (`:run_id` = NULL) | ทุกหน้าแสดงข้อความ "ยังไม่มีข้อมูล — ยังไม่เคยโหลด CSV สำเร็จ" ไม่ crash; ไม่แสดงตัวเลข 0 | AL-03, T-D07 |
| project ที่เลือกมี `total_actions = 0` | แสดง "ไม่มีข้อมูลสำหรับ project นี้" และ **ไม่แสดง Completion Rate เป็น 0%** (Q คืน 0 ซึ่งกำกวมกับ 0% จริง) | METRIC_LOGIC Edge Case, T-D07 |
| scope มีข้อมูลแต่ `overdue_actions = 0` | KPI Overdue = 0 และ CH-15 แสดง "ไม่มี overdue action ณ reference date {date}" — แยกจาก no-data | plan §12 |
| query/DB error | ข้อความ error ที่อ่านเข้าใจได้ ไม่ใช้ค่าเก่าเงียบ ๆ | plan Phase 9 |

### Drill-down Path (summary → detail)

ทิศทางเดียวตาม interaction_spec (VIZ_DESIGN_SPEC): ไม่มี external link; table row click = เลือกแถวเท่านั้น

| จาก | การกระทำ | ไปที่ | scope ที่ส่งต่อ |
|---|---|---|---|
| `DASH-01` CH-01..CH-03, CH-05 (`kpi_card`) | คลิก | เลื่อนไป CH-11 (project table) | Project filter เดิม |
| `DASH-01` CH-04 Overdue (`kpi_card`) | คลิก | `DASH-02` | Project filter เดิม |
| `DASH-01` CH-06..CH-08, CH-10 (`bar`) | คลิกแท่ง | ตั้ง Project filter = โครงการนั้น (อยู่หน้าเดิม; ทุก chart จำกัดเหลือโครงการนั้น — เลือกกลับ All Projects เพื่อเทียบ) | `project_name` ของแท่ง |
| `DASH-01` CH-08 (แท่ง overdue) | คลิกแท่ง + ปุ่ม "ดูรายการ" | `DASH-02` | `project_name` ของแท่ง |
| `DASH-02` CH-16 (`bar` owner) | คลิกแท่ง | กรอง CH-15 ด้วย `owner` (filter ฝั่ง grid ของค่าที่ query แล้ว) | `owner` |
| `DASH-02` CH-17 (`bar` project) | คลิกแท่ง | ตั้ง Project filter | `project_name` |

Keyboard: Tab เข้า chart/ตาราง, Enter = drill-down, Esc = ปิด tooltip (Accessibility, VIZ_DESIGN_SPEC) Tooltip ใช้รูปแบบ `{metric label} : {value} {unit}` + `Reference date`; ไม่มี `% change`/trend ข้าม run ใน v1

### Cross-dashboard Links

| จาก | ถึง | เงื่อนไข |
|---|---|---|
| DASH-01 ↔ DASH-02 | nav bar + CH-04 | ส่ง Project filter ตามไป |
| DASH-01 / DASH-02 → DASH-03 | nav bar (bonus) | แสดงเฉพาะเมื่อเปิดใช้ DASH-03 |
| DASH-03 → DASH-01 / DASH-02 | nav bar | ส่ง Project filter ตามไป |

## Refresh Schedule

| Dashboard | Refresh Frequency | Data Source Pipeline | Last Refresh Indicator | SLA (SLA_FRESHNESS) |
|---|---|---|---|---|
| DASH-01 | weekly หลังประชุม — ผู้รัน `src.ingest` ด้วยมือ (cron = `null` ตาม PIPELINE_SPEC Schedule); dashboard อ่าน latest successful run **ตอนโหลดหน้า/รีเฟรช** ไม่มี auto-polling `[DESIGN PROPOSAL]` | PL-01 `csv_ingest` | header: `completed_at`, `run_id`, `reference_date` ของ run ที่ใช้ | FR-01, FR-02, FR-04 (`P0`/`P1`) |
| DASH-02 | เช่นเดียวกัน | PL-01 | เช่นเดียวกัน | FR-01, FR-02 (`P0`) |
| DASH-03 | on-demand (ปุ่ม Generate Draft; ไม่มี cron) | PL-02 `executive_summary_generate` (ต้องมี run `succeeded` จาก PL-01) | `created_at` + `source_run_id` ของ summary | FR-05 (`P2`) |

- Delay tolerance / threshold แจ้งเตือนอายุข้อมูล = `null` (calibration source: ข้อตกลงเวลาส่ง CSV กับ `{{MEETING_CHAIR}}`; owner `{{DATA_STEWARD}}` — SLA_FRESHNESS) ดังนั้น dashboard **แสดงเวลา `completed_at` เท่านั้น ไม่ตัดสินว่า "stale"**
- Freshness ≠ completeness ≠ correctness: indicator ข้างบนบอกเฉพาะความสด; ความครบอยู่ที่ CH-12 / DATA_QUALITY; ความถูกต้องอยู่ที่ T-D03/T-D04
- **Performance Budget:** p95 load time = `null` (calibration source: วัดบนข้อมูลจริงและเครื่องที่ใช้ประชุม; owner `{{DASHBOARD_DEVELOPER}}` ร่วม `{{DATA_STEWARD}}`) — ยังไม่เคยวัด วิธีที่ออกแบบ: query สด read-only บน DuckDB (sample = 14,013 แถว, 12 projects; Q เป็น aggregate/ตารางเดียว) โดยไม่มี pre-aggregated extract `[DESIGN PROPOSAL — ยังไม่พิสูจน์]` ถ้าวัดแล้วเกินงบ จึงพิจารณา cache ผลต่อ `run_id` (ผลของ run ไม่เปลี่ยน — run immutable) และต้องบันทึกใน ANALYTICS_CHANGELOG

## Access and Governance (อ้างอิง DATA_GOVERNANCE.md)

- `Owner` และ `Action` (CH-15) เป็น `confidential` — การแสดงดิบ/mask ต่อ role (ROLE-01..05) ตาม Column Masking; ยังเป็น `null` สำหรับ ROLE-01/02/05 (ผู้ตัดสิน `{{DPO_OR_LEGAL}}`); export จาก AG Grid ต้องผ่าน masking เดียวกัน
- ขอบเขต row-level ของ STK-04 (ROLE-04) และ ROLE-02 = `null`; ยังไม่มี authentication ใน plan — จนกว่าตัดสิน ทุกผู้ใช้ที่เข้าถึงแอปเห็นเท่ากัน (ความเสี่ยงที่รับรู้ ไม่ใช่การรับรอง)
- ห้ามพิมพ์ค่า `owner` / `action_name` ลง log เกินจำเป็น; chart alt text สร้างจากข้อมูลโดยไม่ฝังตัวเลขตายตัว (VIZ_DESIGN_SPEC Accessibility)

## Open Questions

1. (ปิดแล้ว, D4) CH-14 = MET-07 `owners_with_overdue_actions` (draft; KPI-03) — สถานะ draft จนกว่า `{{KPI_OWNER_ROLE}}` อนุมัติ MET-07/MET-08
2. (ปิดแล้ว, D4) CH-09 un-defer แล้ว: ใช้ MET-08 `open_not_overdue_actions` ผ่าน Q-BY-PROJECT; เป็น view `intermediate` ที่ผู้ใช้เปิดเอง
3. CH-16 (overdue by owner) ถือเป็น required เพื่อ coverage ของ KPI-03 หรือคงเป็น optional ตาม plan.md §12? (ตอนนี้ KPI-03 ยังมี CH-14 และ CH-15 รองรับ) และค่า top-N = `null` (`{{DASHBOARD_DEVELOPER}}`)
4. (ปิดแล้ว, D4) CH-05 ใช้ Q-PORTFOLIO ที่คืน `completion_rate` (MET-06) — การเพิ่มคอลัมน์นี้อยู่ใน METRIC_LOGIC (เจ้าของ SQL)
5. (ปิดแล้ว, D3) Project filter จำกัดแถวทุก chart/ตาราง; TESTING_STRATEGY T-D04 ต้องตรวจว่า chart ทุกตัวเปลี่ยนตาม project (เจ้าของ TESTING_STRATEGY)
6. (ปิดแล้ว, D7) VIZ_DESIGN_SPEC มี CT-09 สำหรับ project summary table (CH-11)
7. Dashboard host/URL, authentication และ p95 budget = `null` (owner `{{PROJECT_SPONSOR}}` / `{{DASHBOARD_DEVELOPER}}`); `REFERENCE_DATE` = 2026-10-02 (fixed constant สำหรับ iteration 1; เปลี่ยนผ่าน ANALYTICS_CHANGELOG เท่านั้น); test fixture ใช้วันที่ต่างจาก REFERENCE_DATE (2026-09-15) จึงห้ามเทียบตัวเลข fixture กับค่าอ้างอิงนี้
8. Optional integration (ai-chatbot EVALUATION.md) — **ไม่ใช้**: โปรเจกต์นี้ไม่มี conversational metric; inventory ข้างบนครบโดยไม่พึ่ง source นั้น
