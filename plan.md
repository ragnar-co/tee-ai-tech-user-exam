# Cybersecurity Project Action Dashboard — Claude Code Implementation Plan

## 0. Decision Summary

### Selected DDD

ใช้ **`ddd-data-analytics` เพียงตัวเดียว**

เหตุผล:
- source เป็น CSV จากหลาย cybersecurity projects ที่มีอยู่แล้ว
- งานหลักคือ validation, storage, metric computation, dashboard และ executive reporting
- ไม่ได้ออกแบบ operational workflow/application domain ใหม่
- analytics layer ต้องตอบว่าโครงการใดมีงานค้าง งานใด overdue และใครเป็น owner

ห้ามเพิ่ม `ddd-web-app` หรือ `ddd-ai-workflow` เป็น DDD track เพิ่ม แม้จะทำ bonus AI summary

### Technology Choice

- Database: **DuckDB**
- Backend/runtime: Python
- Dashboard shell: **Plotly Dash**
- Core charts: Plotly
- Optional declarative visualization: Vega/Altair เฉพาะจุดที่เหมาะสม
- Detail table: Dash AG Grid
- Tests: pytest

---

# 1. Assignment Goal

สร้างแอป:

> **Cybersecurity Project Action Dashboard**

สำหรับ workflow หลังประชุมประจำสัปดาห์:

1. ทีมส่ง Action Items เป็น CSV
2. แอปรับไฟล์ CSV
3. ตรวจสอบข้อมูลก่อน ingest
4. จัดเก็บข้อมูลใน DuckDB
5. คำนวณสถานะ action ด้วย **reference date เดียวกันทั้งระบบ**
6. แสดง:
   - จำนวนงานทั้งหมด
   - จำนวนงานเสร็จ
   - จำนวนงานเลยกำหนด
   - แยกตามโครงการ
7. แสดงรายการ overdue actions พร้อม:
   - project
   - action
   - owner
   - due date
   - days overdue
8. ผู้ใช้เลือกดูเฉพาะ project ได้

Bonus:

9. สร้าง AI workflow สำหรับ draft Executive Summary จากข้อมูลใน database
10. บันทึก summary ลง database
11. แสดง summary บน Dash app

---

# 2. Critical Rule — Reference Date

โจทย์กำหนดให้ใช้ **วันที่อ้างอิงตามโจทย์** เพื่อให้ผลตรวจตรงกัน

ห้ามใช้:

```python
date.today()
datetime.now().date()
```

โดยตรงใน metric logic

ให้มี source of truth เดียว:

```text
REFERENCE_DATE
```

## Current Status

ไฟล์ `src/tee_cybersecurity_actions_mock.csv` **ไม่มี** ค่า reference date ระบุไว้ตรง ๆ

การตัดสินใจ (ผู้ใช้ยืนยัน, iteration แรก): **`REFERENCE_DATE = 2026-10-02`** ล็อกเป็นค่าคงที่ (= วันที่ทำงาน) ไม่ใช่ `date.today()` แบบเปลี่ยนทุกวัน — ถ้าโจทย์ต้นฉบับระบุวันอื่น ให้เปลี่ยนค่าเดียวนี้

ผลที่ได้ที่ 2026-10-02 (ตรวจจากไฟล์จริง): overdue = 3,531 งาน, days_overdue สูงสุด = 46

(ค่าที่ใช้ก่อนหน้านี้ 2026-10-01 → overdue 3,145 ถูกยกเลิกแล้ว)

ห้ามเรียก `date.today()` ใน metric logic; ค่านี้ถูกส่งผ่าน `--reference-date` และเก็บใน DuckDB:

```bash
python -m src.ingest \
  --input src/tee_cybersecurity_actions_mock.csv \
  --reference-date 2026-10-02
```

---

# 3. Confirmed Source Schema

Input sample:

```text
tee_cybersecurity_actions_mock.csv
```

Columns:

```text
action_id
project_name
action_name
owner
due_date
status
```

ตำแหน่งไฟล์จริง: `src/tee_cybersecurity_actions_mock.csv` (UTF-8, ภาษาไทยปนอังกฤษ)

Profile ที่ตรวจจากไฟล์จริง (ไม่ใช่ค่า hardcode ใน app):

```text
rows                = 14,013 (บรรทัดรวม header = 14,014)
status.done         = 8,597
status.in_progress  = 3,326
status.todo         = 2,090
projects            = 12 (P01..P12; P01-P09 = 1,168 แถว, P10-P12 = 1,167 แถว)
owners (distinct)   = 96 (Owner-001..)
due_date range      = 2026-07-18 .. 2026-11-05 (ISO YYYY-MM-DD, parse ได้ทุกแถว)
duplicate action_id = 0
empty / whitespace  = 0 ในทุกคอลัมน์
```

ข้อสังเกต: ไฟล์ตัวอย่างสะอาด ดังนั้น validation test ที่ต้องพิสูจน์กรณี invalid ต้องใช้ fixture ที่สร้างขึ้นเอง (`tests/fixtures/`)

Project name เป็นรูปแบบ `Pxx - ชื่อโครงการ` ให้ใช้เป็น key ตามที่ปรากฏใน source

ห้าม hardcode counts เหล่านี้ใน dashboard

dashboard ต้อง query จาก DuckDB เท่านั้น

---

# 4. Functional Requirements

## FR-01 CSV Input

ระบบต้องรับ CSV ตัวอย่างได้

MVP รองรับอย่างน้อย:

```text
src/tee_cybersecurity_actions_mock.csv
```

Bonus UX:

- upload CSV ผ่าน Dash
- preview validation result ก่อน ingest

แต่ command-line ingest ต้องทำงานได้เสมอเพื่อ reproducibility

---

## FR-02 Validate CSV

ตรวจอย่างน้อย:

### Required columns

```text
action_id
project_name
action_name
owner
due_date
status
```

### Required validations

- file readable
- required columns ครบ
- `action_id` ไม่ว่าง
- duplicate `action_id`
- `project_name` ไม่ว่าง
- `action_name` ไม่ว่าง
- `owner` ไม่ว่าง
- `due_date` parse เป็น DATE ได้
- `status` ไม่ว่าง
- invalid rows ต้องถูก report
- ห้าม silently drop invalid records

### Status Handling

อย่า invent business enum นอก source

อ่าน distinct status จาก source

สำหรับ sample ปัจจุบันพบ:

```text
done
in_progress
todo
```

Metric logic สำหรับ "completed" ใช้ `status = 'done'` ตาม sample data

ถ้าพบ status ใหม่:
- แสดงเป็น data-quality finding
- อย่า map ไป status อื่นโดยเดา

---

## FR-03 Store in DuckDB

Database:

```text
data/cybersecurity.duckdb
```

ต้องสามารถ rebuild จาก CSV ได้

---

## FR-04 Metrics by Project

แสดงต่อ project:

```text
total_actions
completed_actions
open_actions
overdue_actions
completion_rate
```

โจทย์ขั้นต่ำบังคับอย่างน้อย:

```text
total_actions
completed_actions
overdue_actions
```

---

## FR-05 Overdue Definition

Action เป็น overdue เมื่อ:

```text
status != 'done'
AND due_date < reference_date
```

Action ที่:

```text
due_date == reference_date
```

ยังไม่ถือว่า overdue

---

## FR-06 Days Overdue

นิยาม:

```text
days_overdue = reference_date - due_date
```

เฉพาะ record ที่ overdue

DuckDB logic:

```sql
date_diff('day', due_date, reference_date)
```

Expected:

```text
days_overdue > 0
```

---

## FR-07 Project Filter

ผู้ใช้ต้องเลือก:

```text
All Projects
หรือ
single project
```

Filter ต้อง update:

- KPI cards
- charts
- overdue table

---

## FR-08 Overdue Detail

แสดงอย่างน้อย:

```text
project_name
action_name
owner
due_date
days_overdue
```

แนะนำเพิ่ม:

```text
action_id
status
```

Sort default:

```text
days_overdue DESC
```

---

# 5. Bonus Functional Requirements — AI Executive Summary

Bonus ต้องอยู่ใน project เดียวกัน และยังใช้ `ddd-data-analytics` track เดียว

## AI-01 Source

AI summary ต้องสร้างจาก **ข้อมูล query จาก DuckDB**

ห้ามส่ง raw CSV ทั้งไฟล์ให้ model ถ้าไม่จำเป็น

สร้าง structured context เช่น:

```json
{
  "reference_date": "...",
  "portfolio": {
    "total_actions": 0,
    "completed_actions": 0,
    "open_actions": 0,
    "overdue_actions": 0
  },
  "projects": [],
  "top_overdue_actions": []
}
```

`top_overdue_actions` ส่งเป็นแถวจำกัดจำนวน top-N เรียงตาม `days_overdue` มาก→น้อย โดยมี field เฉพาะ `action_id`, `project_name`, `action_name`, `owner`, `due_date`, `days_overdue` (N = `null` ใน plan นี้ — ตั้งค่าใน config ตอน calibration; ห้ามส่ง raw CSV, ห้ามส่งตารางเต็ม, ห้ามส่ง API key)

---

## AI-02 Output

Executive Summary draft ควรมี:

1. Portfolio status
2. Projects that require attention
3. Most overdue / important follow-up actions based on overdue days and open counts
4. Responsible owners for follow-up (ส่ง `owner` แบบ pseudonymous `Owner-NNN` ให้ model ได้ตามการตัดสินใจของผู้ใช้ สำหรับ iteration 1 — ไม่มีเงื่อนไข)
5. Proposed next steps

ห้าม model invent:

- risk severity
- impact
- project priority
- SLA
- business consequence
- security criticality

ถ้า source ไม่มี field เหล่านี้

หมายเหตุการตัดสินใจ (ผู้ใช้ตัดสิน iteration 1): การส่ง `owner` ให้ model เป็น user decision ไม่ใช่การอนุมัติจาก DPO/Legal — คำถามการจัดชั้น PDPA ของ `owner`/`action_name` (GOV-OPEN-01) และ data residency/third-party processing (OpenRouter -> Anthropic) ยังเปิดอยู่สำหรับ `{{DPO_OR_LEGAL}}`

---

## AI-03 Persistence

สร้าง table:

```text
executive_summaries
```

Fields:

```text
summary_id
created_at
reference_date
project_filter
source_run_id
summary_text
provider
model_name
prompt_version
```

ชื่อ field ตาม `DATA_MODEL_SPEC.md` (เท่ากับ §9.5); `provider` = `'openrouter'` (constant), `model_name` = `'anthropic/claude-sonnet-5'`

ห้ามเก็บ API key ใน database

---

## AI-04 UI

เพิ่ม page/section:

```text
Executive Summary
```

รองรับ:

- Generate Draft
- Save generated summary
- Display latest saved summary
- Display generated timestamp
- Display reference date
- optional history list

---

## AI-05 AI Failure

ถ้า AI provider ใช้งานไม่ได้ (ไม่มี `OPENAI_API_KEY`/`OPENAI_BASE_URL`, timeout, rate-limit, HTTP error):

- dashboard core ต้องยังทำงาน
- แสดง error ที่อ่านเข้าใจได้
- ห้าม crash app
- ห้ามสร้าง fake summary

---

# 6. Non-Functional Requirements

## NFR-01 Reproducibility

ตัวเลขต้อง reproducible จาก:

```text
source CSV
+
reference date
+
SQL definitions
```

---

## NFR-02 Read Only Analytics

MVP dashboard:

- ไม่แก้ owner
- ไม่แก้ due_date
- ไม่เปลี่ยน status

---

## NFR-03 No Hidden Business Logic

ห้ามเขียน metric formula ซ้ำใน Dash callbacks

business metric logic ต้องอยู่ใน SQL / data access layer

---

## NFR-04 Idempotent Load

load input เดิมซ้ำต้องไม่เพิ่ม duplicate actions

---

## NFR-05 Traceability

ทุก dashboard metric ต้อง trace กลับไปยัง SQL/query ได้

---

# 7. Architecture

```text
CSV files
   |
   v
Validation
   |
   +---- invalid records/report
   |
   v
DuckDB
   |
   +----------------------+
   |                      |
   v                      v
raw layer             app_config
   |                 reference_date
   v
staging layer
   |
   v
semantic/action layer
   |
   +----------------------------+
   |                            |
   v                            v
project metrics             overdue details
   |                            |
   +-------------+--------------+
                 |
                 v
            Plotly Dash
          /      |       \
         /       |        \
 Overview   Overdue    Executive Summary
                          (bonus)
```

---

# 8. Repository Layout

```text
cybersecurity-action-dashboard/          # layout ตามจริง ณ 2026-10-02
├── plan.md
├── ddd/                    # DDD JSON templates (อ่านอย่างเดียว)
├── README.md
├── pyproject.toml          # dependency, pytest markers (sample/unit/integration), ruff
├── .env.example
├── .gitignore
├── Dockerfile, docker-compose.yml, .dockerignore   # image 2-stage, gunicorn (extra `prod`)
├── docker/
│   └── entrypoint.sh       # รัน ingest (idempotent) ทุก start แล้วเปิด gunicorn
├── data/
│   └── cybersecurity.duckdb      # สร้างตอน ingest (ไม่ commit)
├── sql/
│   ├── 00_schema/create_tables.sql
│   ├── 10_staging/load_raw.sql, stg_actions.sql
│   ├── 20_metrics/latest_run.sql, q_portfolio.sql, q_by_project.sql,
│   │              q_overdue_detail.sql, q_by_owner.sql
│   └── 30_quality/quality_checks.sql
├── src/
│   ├── tee_cybersecurity_actions_mock.csv   # source ตามที่มีอยู่จริง
│   ├── __init__.py, settings.py, db.py
│   ├── validation.py, ingest.py, metrics.py
│   └── ai/
│       ├── __init__.py, context_builder.py, prompt.py
│       ├── provider.py, summary_service.py
├── dashboard/
│   ├── app.py              # app + 3 หน้า (/, /overdue, /executive-summary) อยู่ในไฟล์นี้
│   ├── viz_theme.py
│   ├── components/         # cards.py, charts.py, filters.py, tables.py
│   ├── pages/              # ว่าง (มีแต่ __init__.py) — ไม่ใช้ Dash multi-page
│   └── assets/app.css
├── tests/
│   ├── fixtures/actions_small.csv
│   ├── conftest.py, reference_calc.py, reference_validation.py
│   ├── test_validation.py, test_ingest.py, test_idempotency.py
│   ├── test_hardening_ingest.py, test_metrics.py, test_reference_date.py
│   ├── test_reconciliation.py
│   ├── test_ai_provider.py, test_ai_summary_service.py
│   ├── test_ai_context_builder.py, test_ai_prompt_hardening.py
│   └── test_dashboard_app.py, test_dashboard_components.py
└── docs/
    └── data-analytics/
```


---

# 9. DuckDB Schema

## 9.1 `ingestion_runs`

ใช้เก็บ metadata ของแต่ละ load

```text
run_id
source_file
source_hash
reference_date
started_at
completed_at
source_row_count
valid_row_count
invalid_row_count
status
```

---

## 9.2 `raw_actions`

```text
run_id
action_id
project_name
action_name
owner
due_date_raw
status
source_row_number
loaded_at
```

Raw layer เก็บ source semantics ให้มากที่สุด

---

## 9.3 `stg_actions`

```text
run_id
action_id
project_name
action_name
owner
due_date
status
is_completed
is_open
is_overdue
days_overdue
loaded_at
```

### Definitions

```text
is_completed = status = 'done'

is_open = status != 'done'

is_overdue =
    status != 'done'
    AND due_date < reference_date

days_overdue =
    CASE
      WHEN is_overdue
      THEN date_diff('day', due_date, reference_date)
      ELSE 0
    END
```

---

## 9.4 `data_quality_results`

```text
quality_result_id
run_id
check_name
record_key
severity_class
message
created_at
```

ใน code ใช้ classification:

```text
blocking
warning
investigation
```

นี่เป็น implementation classification ภายใน app
อย่าอ้างว่าเป็น DDD `rule_severity` enum อย่างเป็นทางการจนกว่าจะสร้าง DATA_QUALITY.md ตาม ownership rule

---

## 9.5 `executive_summaries` — Bonus

```text
summary_id
created_at
reference_date
project_filter
source_run_id
summary_text
provider
model_name
prompt_version
```

`provider` = `'openrouter'`, `model_name` = `'anthropic/claude-sonnet-5'`; `project_filter` NULL = All Projects; ชื่อเดียวกับ §5 AI-03 และ `DATA_MODEL_SPEC.md`

---

# 10. Core SQL Queries

ทุก query รับ `project_name` เลือกได้ (`NULL` = All Projects; data layer แปลง label `All Projects` เป็น `NULL`) ตาม `METRIC_LOGIC.md` (ซึ่งเป็น authority ของ SQL; ด้านล่างใช้ named parameter `$run_id`, `$project_name`)

## 10.1 Portfolio Metrics

```sql
SELECT
    COUNT(*) AS total_actions,
    COUNT(*) FILTER (WHERE is_completed) AS completed_actions,
    COUNT(*) FILTER (WHERE is_open) AS open_actions,
    COUNT(*) FILTER (WHERE is_overdue) AS overdue_actions,
    COUNT(*) FILTER (WHERE is_open AND NOT is_overdue) AS open_not_overdue_actions,   -- MET-08
    COUNT(DISTINCT owner) FILTER (WHERE is_overdue) AS owners_with_overdue_actions,   -- MET-07
    CASE
        WHEN COUNT(*) = 0 THEN 0
        ELSE COUNT(*) FILTER (WHERE is_completed)::DOUBLE / COUNT(*)
    END AS completion_rate
FROM stg_actions
WHERE run_id = $run_id
  AND ($project_name IS NULL OR project_name = $project_name);
```

---

## 10.2 Metrics by Project

```sql
SELECT
    project_name,
    COUNT(*) AS total_actions,
    COUNT(*) FILTER (WHERE is_completed) AS completed_actions,
    COUNT(*) FILTER (WHERE is_open) AS open_actions,
    COUNT(*) FILTER (WHERE is_overdue) AS overdue_actions,
    COUNT(*) FILTER (WHERE is_open AND NOT is_overdue) AS open_not_overdue_actions,   -- MET-08
    CASE
        WHEN COUNT(*) = 0 THEN 0
        ELSE
            COUNT(*) FILTER (WHERE is_completed)::DOUBLE
            / COUNT(*)
    END AS completion_rate
FROM stg_actions
WHERE run_id = $run_id
  AND ($project_name IS NULL OR project_name = $project_name)
GROUP BY project_name
ORDER BY project_name;
```

---

## 10.3 Overdue Detail

```sql
SELECT
    action_id,
    project_name,
    action_name,
    owner,
    due_date,
    status,
    days_overdue
FROM stg_actions
WHERE run_id = $run_id
  AND is_overdue
  AND ($project_name IS NULL OR project_name = $project_name)
ORDER BY days_overdue DESC, due_date ASC, action_id ASC;  -- action_id = tie-break ให้ผลคงที่
```

MET-07 (`owners_with_overdue_actions`) ไม่ additive ข้าม project จึงอยู่ใน 10.1 เท่านั้น ไม่อยู่ใน 10.2

---

# 11. Dashboard Design

> **ตามที่ implement (2026-10-02):** Dash app เดียวใน `dashboard/app.py` (ไม่ใช้ multi-page; `dashboard/pages/` ว่าง) 3 route สลับด้วย `dcc.Location` + callback: `/` = Portfolio Overview (Page 1), `/overdue` = Overdue Actions (Page 2), `/executive-summary` = Executive Summary (Page 3, bonus) ตัวกรองโครงการ/theme/colorblind อยู่ใน filter bar ที่ใช้ร่วมทุกหน้า รันด้วย `python dashboard/app.py` (default `127.0.0.1:8050`; env `DASH_DB_PATH`, `DASH_HOST`, `DASH_PORT`, `DASH_DEBUG`) CH-14 (Owners with Overdue Actions = MET-07) อ่านจาก Q-PORTFOLIO

## Page 1 — Portfolio Overview

### Header

```text
Cybersecurity Project Action Dashboard
Reference date: <fixed assignment date>
Source: <filename>
Loaded: <timestamp>
```

### Global filter

```text
Project
```

values:

```text
All Projects
<distinct projects>
```

### KPI cards

```text
Total Actions
Completed
Open
Overdue
```

Completion Rate (MET-06, Q-PORTFOLIO `completion_rate`) เพิ่มได้แต่ไม่จำเป็นต่อโจทย์ขั้นต่ำ; แสดงเฉพาะเมื่อ `total_actions > 0`

### Main chart

ค่าเริ่มต้น = bar แยก (basic) ตาม `DASHBOARD_SPEC.md`; stacked bar เป็น view ระดับ intermediate ที่ผู้ใช้เปิดเอง (CH-09):

```text
x = project
y = action count
series =
    completed
    open non-overdue
    overdue
```

ค่าเริ่มต้น chart แยก:

```text
Total / Completed / Overdue by Project
```

"open non-overdue" = MET-08 `open_not_overdue_actions` (Q-BY-PROJECT) — ไม่คำนวณใน Dash

### Project table

Columns:

```text
Project
Total
Completed
Open
Overdue
Completion Rate
```

---

# 12. Page 2 — Overdue Actions

## Objective

ตอบทันทีว่า:

> งานใดเลยกำหนด ใครเป็นผู้รับผิดชอบ และล่าช้ากี่วัน

### KPI

```text
Overdue Actions
Owners with Overdue Actions   (MET-07 owners_with_overdue_actions, จาก Q-PORTFOLIO)
```

### AG Grid

Columns:

```text
Project
Action
Owner
Due Date
Days Overdue
Status
```

Default sort:

```text
Days Overdue DESC
```

### Optional visualization

Plotly:

```text
Overdue Actions by Owner
```

หรือ:

```text
Overdue Actions by Project
```

อย่าสร้าง owner performance score

---

# 13. Page 3 — Executive Summary (Bonus)

### Components

```text
Reference Date
Project Filter
Generate Draft button
Latest Saved Summary
Generated At   (= created_at)
Model          (= model_name)
```

### Generation flow

```text
project filter
      |
      v
query DuckDB
      |
      v
build structured summary context
      |
      v
OpenRouter (OpenAI-compatible HTTPS)
      |
      v
draft summary
      |
      v
save to executive_summaries
      |
      v
display in Dash
```

### Prompt principles

Prompt ต้องบอก model:

- use only supplied data
- do not invent risk severity
- do not invent business impact
- name projects requiring follow-up based on observed overdue/open counts
- mention owners (`Owner-NNN`) only when present in supplied data
- propose operational next steps เช่น review overdue items, confirm blockers, update due dates/status
- label output as draft

---

# 14. CSV Validation UX

CLI validation ต้องเสร็จก่อน dashboard

Bonus upload UI อาจทำ:

```text
Upload CSV
   |
   v
Validate
   |
   +--> blocking errors -> reject ingest
   |
   +--> warnings -> show user
   |
   v
Ingest
```

ห้าม ingest แล้ว silently discard invalid rows

---

# 15. Data Quality Checks

Minimum:

```text
DQ-01 required columns exist
DQ-02 action_id not null
DQ-03 action_id unique within input
DQ-04 project_name not null
DQ-05 action_name not null
DQ-06 owner not null
DQ-07 due_date parseable
DQ-08 status not null
DQ-09 distinct status discovery
DQ-10 source row count reconciles
```

ถ้า status ใหม่ปรากฏ:

```text
investigation
```

จนกว่าจะมี business rule

---

# 16. Reference Date Tests

ต้องมี test โดยตรง

Fixture:

```text
reference_date = 2026-09-15   # fixture ต้องต่างจาก REFERENCE_DATE จริง (2026-10-02) เพื่อจับ date.today() แอบแฝง
```

นี่เป็น **test fixture เท่านั้น**

Cases:

```text
due_date = 2026-09-14, status=todo
=> overdue = true
=> days_overdue = 1

due_date = 2026-09-15, status=todo
=> overdue = false

due_date = 2026-09-16, status=todo
=> overdue = false

due_date = 2026-08-01, status=done
=> overdue = false
```

เมื่อทราบ reference date จริงของ assignment ให้เพิ่ม integration test ด้วย date จริงนั้น

---

# 17. Testing

## Validation

- missing required column fails
- invalid date reported
- duplicate action ID reported
- null required field reported

## Metrics

ใช้ golden fixture ที่คำนวณมือได้

Assert:

```text
total
completed
open
overdue
days_overdue
project grouping
```

## Idempotency

Load file เดิมสองครั้ง

เลือก implementation strategy อย่างใดอย่างหนึ่ง:

### Strategy A — Snapshot Replace

source เดิม:

```text
replace current snapshot
```

หรือ

### Strategy B — Run Versioning

แต่ละ ingest มี `run_id`
dashboard ใช้ latest successful run

แนะนำ **Strategy B**
เพราะ audit/reproducibility ชัดกว่า

## Dashboard Smoke

- app starts
- project selector loads
- All Projects works
- project filter works
- overdue table loads
- no-data project state does not crash

---

# 18. DDD Scope for This Assignment

Track: **`ddd-data-analytics` v2.8.0** (`ddd/ddd-data-analytics-v2.8.0.json`) เท่านั้น
Output dir ตาม template: `docs/data-analytics/`

## เอกสารและ dependency (อ่านจาก JSON จริง)

Generation order (23 เอกสาร):

```text
stakeholders, constraints, kpi_dictionary, business_glossary, metric_spec,
data_model_spec, metric_logic, data_contract, pipeline_spec, data_quality,
sla_freshness, testing_strategy, viz_design_spec, dashboard_spec, report_spec,
data_governance, agents_md, tasks, lineage, ai_model_spec, runbook,
analytics_changelog, readme
```

| Doc | depends_on |
|---|---|
| stakeholders, constraints, kpi_dictionary, business_glossary | - |
| metric_spec | kpi_dictionary, business_glossary, stakeholders |
| data_model_spec | metric_spec |
| metric_logic | metric_spec, data_model_spec |
| data_contract | data_model_spec |
| pipeline_spec | data_model_spec, metric_logic |
| data_quality | data_model_spec, pipeline_spec |
| sla_freshness | pipeline_spec |
| testing_strategy | pipeline_spec, data_quality, metric_logic |
| viz_design_spec | stakeholders, metric_spec |
| dashboard_spec | metric_spec, kpi_dictionary, data_model_spec, stakeholders, testing_strategy, viz_design_spec |
| report_spec | dashboard_spec, kpi_dictionary, metric_spec, stakeholders, sla_freshness |
| data_governance | data_model_spec, data_contract, kpi_dictionary |
| agents_md | pipeline_spec, data_governance, constraints, data_model_spec |
| tasks | kpi_dictionary, pipeline_spec |
| lineage | metric_logic, pipeline_spec, data_model_spec, dashboard_spec |
| ai_model_spec | data_model_spec, metric_spec, data_quality, lineage |
| runbook | pipeline_spec, sla_freshness, data_quality |
| analytics_changelog | metric_spec, kpi_dictionary, pipeline_spec, data_contract |
| readme | stakeholders, pipeline_spec, runbook, testing_strategy |

## สถานะเอกสาร (ตัดสินแล้ว)

ผู้ใช้ตัดสินให้สร้าง **ครบทั้ง 23 เอกสาร** ของ `ddd-data-analytics` v2.8.0 และเอกสารทั้งหมดมีอยู่แล้วใน `docs/data-analytics/` (reconciled กับ plan นี้) — ประเด็น "รายการเอกสารขั้นต่ำตามเงื่อนไขกลาง" จึงเลิกใช้

**Implementation authority:** เอกสาร DDD ใน `docs/data-analytics/` เป็นแหล่งอ้างอิงสำหรับการ implement — code ต้องทำตามเอกสารเหล่านั้น; plan.md เป็นสรุป หากขัดกันให้แก้ให้ตรงกัน (ห้ามเดาเงียบ ๆ)

# 19. Working DDD Artifacts for Development

เอกสาร formal DDD ครบ 23 ฉบับมีแล้ว (§18) working notes ด้านล่างเป็นทางเลือก ใช้เมื่อยังมีประโยชน์เท่านั้น และไม่อ้างว่าเป็น formal DDD document:

```text
docs/requirements.md
docs/data-profile.md
docs/metric-notes.md
docs/dashboard-wireframe.md
```

ถ้า working notes ขัดกับ `docs/data-analytics/` ให้ถือเอกสาร DDD เป็นหลัก ห้าม invent upstream content

---

# 20. Metric Definitions for Assignment

## `total_actions`

ประเภท:

```text
metric
```

Definition:

> จำนวน action records ทั้งหมดใน scope ที่เลือก

---

## `completed_actions`

Definition:

> จำนวน action records ที่ `status = 'done'`

---

## `open_actions`

Definition:

> จำนวน action records ที่ `status != 'done'`

---

## `overdue_actions`

Definition:

> จำนวน open actions ที่ `due_date < reference_date`

---

## `days_overdue`

Definition:

> จำนวน calendar days จาก due date ถึง reference date สำหรับ overdue action

---

## `completion_rate` (MET-06, optional)

Definition:

> `completed_actions / total_actions` (0 เมื่อ scope ว่าง — UI ต้องแสดง no-data แทน 0%)

---

## `owners_with_overdue_actions` (MET-07, draft; KPI-03)

Definition:

> `COUNT(DISTINCT owner)` ของ actions ที่ `is_overdue` ใน scope ที่เลือก — ไม่ additive ข้าม project; จำนวนนับล้วน ไม่ใช่ owner performance score

---

## `open_not_overdue_actions` (MET-08, draft; KPI-02)

Definition:

> จำนวน actions ที่ `is_open AND NOT is_overdue` (= `open_actions - overdue_actions`) — ใช้เป็นส่วนของ stacked view CH-09

---

## Important

Metric เหล่านี้ยังไม่ควรถูกเรียกว่า organizational KPI
จนกว่าจะมี KPI owner/target และ business definition ที่อนุมัติ

---

# 21. Do Not Build

MVP ห้ามทำสิ่งต่อไปนี้โดยไม่มีข้อมูล:

```text
risk score
project health score
severity score
owner performance score
SLA compliance score
on-time completion rate
average completion time
cycle time
forecast completion date
AI-generated security risk rating
```

Source ไม่มีข้อมูลเพียงพอ

---

# 22. AI Provider Design — Bonus

Provider = **OpenRouter** (OpenAI-compatible chat-completions API) เรียกตรงผ่าน HTTPS จาก Python (ไม่ใช้ `aix` CLI ไม่มี subprocess) — ไลบรารี (`httpx` หรือ `openai` SDK) เป็น implementation detail ที่ยังเปิดอยู่

ทำ abstraction:

```python
class ExecutiveSummaryProvider:
    def generate(self, context: dict) -> str:
        ...
```

provider implementation อ่าน config จาก environment — ตัวแปรมีเพียง:

```text
OPENAI_API_KEY=        # secret
OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

Model = `anthropic/claude-sonnet-5` เป็น constant/ค่า default ใน code หรือ config (ไม่ใช่ secret; ไม่ใช้ env `AI_PROVIDER`/`AI_MODEL`/`AI_API_KEY`)

`.env.example` (ค่าว่างเท่านั้น):

```text
OPENAI_API_KEY=
OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

Env ทางเลือก (ไม่ใช่ secret; ไม่อยู่ใน `.env.example` ที่ active — อยู่เป็นบรรทัดคอมเมนต์ใช้ default ของโค้ด): `AI_TIMEOUT_SECONDS` (default 60), `AI_TOP_N` (default 10, จำนวนแถว `top_overdue_actions` ที่ส่งให้โมเดล) ฝั่ง ingest: `INGEST_MAX_BYTES` (default 256 MiB) ฝั่ง dashboard: `DASH_DB_PATH`, `DASH_HOST`, `DASH_PORT`, `DASH_DEBUG` — ค่าทั้งหมดนี้เป็นค่าที่โค้ดเลือกเอง ไม่ได้มาจาก requirement/การ calibrate

บันทึกลง `executive_summaries`: `provider = 'openrouter'`, `model_name = 'anthropic/claude-sonnet-5'`

ห้าม commit credential; ห้ามเก็บ key ใน DB/repo/log

ถ้าไม่มี `OPENAI_API_KEY` หรือ `OPENAI_BASE_URL`:
- ปิด Generate Draft button พร้อม configuration message
- core dashboard ต้องทำงานปกติ

Timeout / rate-limit / HTTP error: แสดง error ที่อ่านเข้าใจได้ ไม่สร้าง fake summary ไม่ crash

Model risk: `model_status = experimental`; threshold/cost ceiling ยังเป็น `null`; guardrail GR-xx เดิม (ห้าม invent severity/impact/SLA/priority)

Operational dependency / open items:
- OpenRouter workspace guardrail อาจอนุญาตเฉพาะ `anthropic/claude-sonnet-5` — ยังไม่ยืนยันกับ key ของโปรเจกต์นี้
- PDPA ของ `owner`/`action_name` (GOV-OPEN-01) และ data residency/third-party processing (OpenRouter -> Anthropic) ยังเปิดสำหรับ `{{DPO_OR_LEGAL}}` — การส่ง `owner` เป็น user decision iteration 1 ไม่ใช่การอนุมัติจาก DPO/Legal

---

> **สถานะ (2026-10-02):** ติ๊กเฉพาะรายการที่มี code และผ่าน `pytest` หรือการรัน app จริง; รายการที่ยังไม่ทำ/ไม่ได้ยืนยันคงเป็น `[ ]` พร้อมหมายเหตุ ตัวเลข test ล่าสุดดู README.md

# 23. Claude Code Phase Plan

## Phase 1 — Bootstrap

- [x] create repo structure
- [x] create `pyproject.toml`
- [x] add duckdb
- [ ] add pandas or pyarrow only if necessary  _(ไม่จำเป็น — ไม่ได้เพิ่ม)_
- [x] add dash
- [x] add plotly
- [x] add dash-ag-grid
- [ ] add altair only if actually used  _(ไม่ได้ใช้ — ไม่ได้เพิ่ม)_
- [x] add pytest
- [x] add `.env.example`
- [x] add sample CSV

Exit:

```bash
python -c "import duckdb, dash, plotly"
```

works

---

## Phase 2 — Validation

- [x] required column validator
- [x] duplicate action validator
- [x] null validator
- [x] due date parser
- [x] status discovery
- [x] validation result model
- [x] tests

Exit:
invalid file cannot silently ingest

---

## Phase 3 — DuckDB Ingestion

- [x] create DB
- [x] create ingestion_runs
- [x] load raw_actions
- [x] build stg_actions
- [x] persist reference_date
- [x] calculate flags
- [x] calculate days_overdue
- [x] row reconciliation
- [x] tests

Exit:
one command builds a valid DB snapshot

---

## Phase 4 — Metric Queries

- [x] portfolio query
- [x] project metrics query
- [x] overdue detail query
- [x] project-filtered variants
- [x] metric golden tests
- [x] reference-date tests

Exit:
all assignment metrics independently verifiable from SQL

---

## Phase 5 — Dash Overview

- [x] app shell
- [x] project dropdown
- [x] reference date display
- [x] KPI cards
- [x] by-project chart
- [x] project metrics table
- [x] filter callbacks

Exit:
user selects project and all overview numbers update consistently

---

## Phase 6 — Overdue Detail

- [x] overdue AG Grid
- [x] owner field
- [x] due date
- [x] days overdue
- [x] sorting
- [x] project filter integration
- [x] optional overdue-by-owner chart

Exit:
every displayed overdue record reconciles with SQL

---

## Phase 7 — Data Quality Display

- [ ] display validation summary — ถอดแผง CH-12 ออกจากหน้าตามคำสั่งผู้ใช้ (2026-10-02); component `cards.dq_panel` ยังอยู่แต่ไม่ได้ต่อกับหน้า
- [ ] display row counts — ถอดแผง CH-12 ออกจากหน้าตามคำสั่งผู้ใช้ (2026-10-02); component `cards.dq_panel` ยังอยู่แต่ไม่ได้ต่อกับหน้า
- [ ] display duplicate/invalid findings — ถอดแผง CH-12 ออกจากหน้าตามคำสั่งผู้ใช้ (2026-10-02); component `cards.dq_panel` ยังอยู่แต่ไม่ได้ต่อกับหน้า
- [x] display source file/run info

Exit:
user knows which source snapshot drives dashboard

---

## Phase 8 — AI Executive Summary (Bonus)

- [x] build DB context
- [x] define provider interface
- [x] add provider implementation (OpenRouter, OpenAI-compatible HTTPS, `anthropic/claude-sonnet-5`, env `OPENAI_API_KEY`/`OPENAI_BASE_URL`)
- [x] add prompt version
- [x] generate draft  _(pytest ใช้ mocked HTTP; เรียก OpenRouter จริงสำเร็จ 2 ครั้ง 2026-10-02)_
- [x] save summary
- [x] retrieve latest summary
- [x] add Dash page
- [x] failure handling
- [x] tests with mocked provider
- [x] เรียก OpenRouter จริงด้วย key จริงสำเร็จ  _(2026-10-02, 2 ครั้งผ่านปุ่ม Generate; ยังไม่ได้ประเมิน EV-01..EV-05)_

Exit:
AI summary can be generated, persisted and displayed

---

## Phase 9 — Hardening

- [x] idempotency
- [x] latest successful run handling
- [x] empty state
- [x] bad project filter
- [x] DB errors
- [x] AI provider errors
- [x] dashboard smoke tests  _(Flask test client + server จริงที่ 127.0.0.1:8050; ไม่มี browser e2e)_
- [ ] lint/format  _(ruff: ตรวจสถานะจริงด้วย `ruff check .` — ไม่ติ๊กจนกว่าสะอาดตอนส่งมอบ)_

---

## Phase 10 — Submission Docs

- [x] README
- [x] setup instructions
- [x] run instructions
- [ ] architecture  _(README มี layout/เหตุผลการเลือก แต่ไม่มี architecture diagram — ไม่ติ๊ก)_
- [x] reference date declaration
- [x] metric definitions
- [x] known limitations
- [x] DDD selection rationale
- [ ] ตรวจว่า README/code ตรงกับ 23 DDD docs ใน `docs/data-analytics/` (docs เป็น implementation authority)  _(reconcile รอบ 2026-10-02 ทำแล้วด้วยมือ ยังไม่มีการตรวจอัตโนมัติ/ทบทวนอิสระ — ไม่ติ๊ก)_

---

# 24. README Must Include

## Run

Example:

```bash
python -m src.ingest \
  --input src/tee_cybersecurity_actions_mock.csv \
  --reference-date 2026-10-02

pytest

python dashboard/app.py
```

## Explain

README ต้องบอก:

- why DuckDB
- why ddd-data-analytics
- exact reference date used
- overdue definition
- days overdue definition
- database location
- how to rebuild data
- how to run dashboard
- AI bonus setup if implemented: OpenRouter, ตั้ง `OPENAI_API_KEY` และ `OPENAI_BASE_URL` (ดู `.env.example`), model `anthropic/claude-sonnet-5`, เรียกตรงผ่าน HTTPS (ไม่มี `aix`), ไม่มี key ⇒ ปุ่ม Generate Draft ถูกปิด; ระบุว่า owner (`Owner-NNN`) และ top overdue rows ถูกส่งให้ third-party model และ PDPA/data residency ยังเปิดอยู่

---

# 25. Acceptance Criteria — Core

ถือว่า core assignment ผ่านเมื่อ:

- [ ] sample CSV ผ่าน ingestion
- [ ] CSV validation ทำงาน
- [ ] data ถูกเก็บใน DuckDB
- [ ] reference date ถูกกำหนด explicit
- [ ] ไม่มี metric ใช้ system current date
- [ ] total actions แสดงได้
- [ ] completed actions แสดงได้
- [ ] overdue actions แสดงได้
- [ ] metrics แยก project ได้
- [ ] user filter project ได้
- [ ] overdue detail แสดง project
- [ ] overdue detail แสดง action
- [ ] overdue detail แสดง owner
- [ ] overdue detail แสดง due date
- [ ] overdue detail แสดง days overdue
- [ ] dashboard numbers reconcile กับ DuckDB SQL
- [ ] invalid input ไม่ถูก silently ignored
- [ ] tests ผ่าน
- [ ] README รันตามได้

---

# 26. Acceptance Criteria — Bonus

- [ ] summary context มาจาก DuckDB
- [ ] OpenRouter (`anthropic/claude-sonnet-5`) ถูกเรียกจริงเมื่อ `OPENAI_API_KEY`/`OPENAI_BASE_URL` configured
- [ ] ไม่มี config ⇒ Generate Draft ถูกปิดพร้อม config message
- [ ] summary ถูก label เป็น draft
- [ ] summary ถูก save ลง `executive_summaries`
- [ ] summary เปิดดูใน Dash ได้
- [ ] มี generated timestamp (`created_at`)
- [ ] มี reference date
- [ ] มี source run reference (`source_run_id`)
- [ ] AI failure ไม่ทำให้ dashboard core crash
- [ ] model ไม่ได้รับ instruction ให้ invent risk/severity

---

# 27. Definition of Done

Core DoD:

```bash
python -m src.ingest \
  --input src/tee_cybersecurity_actions_mock.csv \
  --reference-date 2026-10-02

pytest

python dashboard/app.py
```

แล้วสามารถตรวจได้ว่า:

1. DuckDB ถูกสร้าง
2. source row count reconcile
3. validation result มีให้ตรวจ
4. reference date แสดงบน app
5. total/completed/overdue ตรงกับ SQL
6. metrics แยก project ได้
7. project filter ทำงาน
8. overdue list แสดง owner และ days late
9. reload ไม่สร้างข้อมูลซ้ำแบบไร้การควบคุม
10. ไม่มี threshold/KPI/risk score ที่แต่งขึ้นเอง

Bonus DoD:

11. Generate Draft ทำงานเมื่อ AI configured
12. generated summary ถูกบันทึก
13. latest summary แสดงใน app
14. provenance ของ summary ตรวจย้อนกลับถึง source run/reference date ได้

---

# 28. Implementation Priority

Claude Code ให้ทำตามลำดับนี้:

```text
1. Confirm/set assignment reference date
2. Bootstrap
3. Validation
4. DuckDB ingestion
5. Metric SQL
6. Metric tests
7. Dash overview
8. Project filter
9. Overdue detail
10. Data quality display
11. Hardening
12. README
13. Bonus AI workflow
14. ตรวจ code/README ให้ตรงกับ DDD docs ทั้ง 23 ฉบับ (มีแล้วใน docs/data-analytics/; docs คือ implementation authority)
```

อย่าเริ่มจาก AI หรือ visual polish ก่อน core metrics ถูก test แล้ว

---

# 29. Important Unknowns

ยังต้องได้รับข้อมูลภายนอก plan นี้:

```text
ASSIGNMENT_REFERENCE_DATE (iteration แรกล็อก 2026-10-02 ตามผู้ใช้ — เปลี่ยนได้ถ้าโจทย์ต้นฉบับระบุต่าง)
```

ตัดสินแล้ว (ไม่ใช่ unknown อีก): เอกสาร DDD ครบ 23 ฉบับมีใน `docs/data-analytics/` (ผู้ใช้ตัดสิน; docs เป็น implementation authority); AI provider = OpenRouter, model `anthropic/claude-sonnet-5`, env `OPENAI_API_KEY`/`OPENAI_BASE_URL`

ยังเปิดอยู่ (เฉพาะ bonus): PDPA ของ `owner`/`action_name` และ data residency/third-party processing สำหรับ `{{DPO_OR_LEGAL}}`; guardrail ของ OpenRouter workspace; ค่า top-N ของ `top_overdue_actions`; ไลบรารี HTTP (`httpx`/`openai`)

Claude Code ห้ามเดาค่าเหล่านี้

ทุกอย่างอื่นใน core MVP สามารถเริ่ม implement ได้ทันที
