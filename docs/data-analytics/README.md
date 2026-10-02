# Cybersecurity Project Action Dashboard — Data Analytics Docs (README)

doc_id: readme
version: 1.0.0
status: draft
depends_on: [stakeholders, pipeline_spec, runbook, testing_strategy]
generated_from: ddd-data-analytics v2.8.0

> **สถานะการยืนยัน (2026-10-02):** โค้ดมีและทำงานแล้ว — `src/` (ingest, validation, metrics, ai), `sql/`, `dashboard/app.py`, `pyproject.toml`, `tests/` **ยืนยันแล้ว:** `.venv/bin/pytest -q` ผ่านทั้งชุด (277 test ณ เวลาที่เขียน; ตัวเลขเปลี่ยนได้); ingest sample จริง 14,013 แถวที่ `2026-10-02` ได้ total 14,013 / completed 8,597 / open 5,416 / overdue 3,531 / max `days_overdue` 46; dashboard เปิดได้ที่ `127.0.0.1:8050` และตรวจผ่าน Flask test client + server จริง (page load, callback, project filter) **ยืนยันเพิ่ม:** เรียก OpenRouter จริงสำเร็จ 2 ครั้งผ่านปุ่ม Generate (2026-10-02; pytest ยังใช้ mocked HTTP เท่านั้น) **ยังไม่ยืนยัน:** การประเมินคุณภาพ EV-01..EV-05, guardrail ของโมเดลอื่น; การตรวจด้วยตา — headless Chrome screenshot ครั้งเดียว ไม่ได้ตรวจ dark theme / colorblind / AG Grid; ไม่มี browser e2e, scheduler/monitoring/on-call, production environment; ไม่มี CI

## Project Name and Description

**Cybersecurity Project Action Dashboard** — analytics layer ครอบ CSV Action Item รายสัปดาห์หลังประชุม (6 คอลัมน์: `action_id, project_name, action_name, owner, due_date, status`) ตอบคำถามว่าโครงการใดมีงานค้าง งานใด overdue และ `owner` ใดเกี่ยวข้อง ผู้ใช้และคำถามหลักอยู่ที่ [STAKEHOLDERS.md](STAKEHOLDERS.md)

**Key Design Decisions** (ไม่ซ้ำรายละเอียด — ดูเอกสารเจ้าของ)
- Warehouse = **DuckDB** (ไฟล์เดียว `data/cybersecurity.duckdb`); BI = **Plotly Dash + Dash AG Grid**; transformation = **SQL files** ใต้ `sql/` ที่รันโดย `src/ingest.py`; test = **pytest**. **ไม่ใช้ dbt** (CON-05, [CONSTRAINTS.md](CONSTRAINTS.md)) — ดังนั้นขั้นตอน "dbt run / dbt test" ในแม่แบบ DDD แทนด้วย `python -m src.ingest` และ `pytest` ([PIPELINE_SPEC.md](PIPELINE_SPEC.md), [TESTING_STRATEGY.md](TESTING_STRATEGY.md))
- Run versioning: ทุก CSV = หนึ่ง run; dashboard อ่านเฉพาะ latest successful run
- `REFERENCE_DATE` ส่งผ่าน `--reference-date` เสมอ ไม่ใช้ `date.today()` ใน metric logic (CON-06) ค่า iteration 1 = **2026-10-02** (ค่าคงที่ที่ผู้ใช้ยืนยัน); test fixture ใช้ 2026-09-15
- ไม่สร้าง risk/health/owner-performance score, SLA compliance, on-time rate, cycle time, forecast (Do-Not-Build — [METRIC_SPEC.md](METRIC_SPEC.md))
- Bonus: AI Executive Summary ([AI_MODEL_SPEC.md](AI_MODEL_SPEC.md))

**Audience:** analytics engineer คนใหม่ (อ่านต่อจากหัวข้อนี้) — ผู้ใช้ธุรกิจดู "Reading Order" ด้านล่าง

## Quick Start

ลำดับคำสั่งรันจาก repo root — step 2-7 รันและยืนยันแล้วในเครื่องพัฒนา (Linux/WSL, Python 3.12 ใน `.venv`); step ที่เกี่ยวกับ AI ไม่อยู่ในรายการนี้ (ต้องมี key)

| # | คำสั่ง | Expected observable result |
|---|---|---|
| 1 | `python -m venv .venv && source .venv/bin/activate` | prompt แสดง `.venv` |
| 2 | `pip install -e ".[dev]"` (extras `dev` ใน `pyproject.toml`: pytest, ruff) | ติดตั้ง duckdb, dash, dash-ag-grid, plotly, pytest ได้ไม่มี error |
| 3 | `python -c "import duckdb, dash, plotly"` | ไม่มี output / exit 0 (PIPELINE_SPEC) |
| 4 | `pytest` | ทุก test ใน suite ที่ [TESTING_STRATEGY.md](TESTING_STRATEGY.md) กำหนดผ่าน (รวม T-R07 สแกนห้ามใช้ `date.today()`) — ไม่ใช่แค่ "ผ่าน" ลอย ๆ; ใช้ DuckDB ชั่วคราวใน `tmp_path` ไม่แตะ DB จริง |
| 5 | `python -m src.ingest --input src/tee_cybersecurity_actions_mock.csv --reference-date 2026-10-02` | exit 0; พิมพ์สรุป `run_id`, `status=succeeded`, row counts (sample: 14,013 แถว; done 8,597 / in_progress 3,326 / todo 2,090); สร้าง `data/cybersecurity.duckdb` |
| 6 | query ตรวจใน [Usage](#usage) | `overdue_actions` ของ sample ที่ 2026-10-02 = **3,531**, max `days_overdue` = **46** (ค่าอ้างอิง ต้อง verify เมื่อรันจริง — informational ไม่ใช่ acceptance threshold) |
| 7 | `python dashboard/app.py` | Dash เปิดได้ และหน้า Portfolio Overview (`DASH-01`) render ตัวเลขตรง step 6 |
| 7b | (ทางเลือก Docker, ยืนยันแล้ว) `docker compose up --build` | เปิด `http://localhost:8050`; entrypoint รัน ingest ทุก start (start แรก `succeeded` 14,013 แถว, restart = `noop`); ข้อมูลอยู่ใน volume `duckdb-data` (`docker compose down -v` เพื่อล้าง); `OPENAI_API_KEY` ว่าง = AI ปิด; `REFERENCE_DATE` default 2026-10-02 |

เมื่อ step 5 ล้ม ดู exit code และ RB-01..RB-06 ใน [RUNBOOK.md](RUNBOOK.md) (`1` blocking/DQ-10, `2` argument/ไฟล์/เกิน `INGEST_MAX_BYTES`/header-only, `3` DB/ระบบ — implement แล้ว ดู PIPELINE_SPEC)

## Prerequisites

**Accounts/Access:** ไม่ต้องมี warehouse server หรือ BI server (DuckDB ไฟล์ในเครื่อง, Dash รันในเครื่อง) สิทธิ์ที่ต้องมี: อ่านไฟล์ CSV จาก producer (`{{PRODUCER_TEAMS}}`), สิทธิ์เขียนโฟลเดอร์ `data/`; สิทธิ์ ingest ถือโดย `{{DATA_STEWARD}}` (DATA_GOVERNANCE.md); bonus (AI Executive Summary): ผู้ใช้เลือก OpenRouter (OpenAI-compatible API) model `anthropic/claude-sonnet-5` (constant ในโค้ด ไม่ใช่ secret) ตั้งค่าด้วย env `OPENAI_API_KEY` (secret) และ `OPENAI_BASE_URL` (เช่น `https://openrouter.ai/api/v1`) เก็บใน env/`.env` ไม่ commit ไม่เก็บใน DB; เรียก HTTPS ตรงจาก Python ไม่ใช้ `aix`; ถ้าไม่ตั้งค่า ปุ่ม Generate Draft ปิดพร้อมข้อความตั้งค่า และ dashboard หลักทำงานปกติ; DPO/residency ของการส่ง context (รวม `owner`) ยัง open ที่ `{{DPO_OR_LEGAL}}`

**Tooling versions:** ไม่มีการ pin เวอร์ชันแน่นอน — `pyproject.toml` กำหนดเฉพาะ lower bound (duckdb>=1.1, dash>=3.0, plotly>=6.0, dash-ag-grid>=31.0, httpx>=0.27; dev: pytest>=8, ruff>=0.5; Python >=3.11); เวอร์ชันที่ต้อง pin = `null` (calibration: ทดสอบกับ sample + `pytest`; owner `{{DATA_STEWARD}}`) ข้อมูลประกอบเท่านั้น: เครื่องที่ใช้เขียนเอกสารมี Python 3.12.3 และ duckdb 1.4.4 (ตรวจเมื่อ 2026-10-02, **ไม่ใช่ค่าที่ตัดสินใจเป็น requirement**) ห้ามเดาเวอร์ชันของ dash/plotly/pytest

## Installation

1. **Warehouse:** ไม่ต้องตั้งค่า connection — `src/ingest.py` สร้าง/เปิด `data/cybersecurity.duckdb` และรัน `sql/00_schema/create_tables.sql` (ST-01, `IF NOT EXISTS`) ingest เป็น single writer; dashboard เปิด `read_only=True` (CON-07, CON-15)
2. **dbt / profiles.yml:** **ไม่เกี่ยวข้อง** (CON-05) — ไม่มี `profiles.yml` หรือ target
3. **BI connection:** Dash อ่าน DuckDB ไฟล์เดียวกันโดยตรงผ่าน data access layer (ไม่มี connector แยก); env: `DASH_DB_PATH` (default `data/cybersecurity.duckdb`), `DASH_HOST` (127.0.0.1), `DASH_PORT` (8050), `DASH_DEBUG` (ปิด) — ค่า default ที่โค้ดเลือก
4. **Secrets:** คัดลอก `.env.example` -> `.env` (`.env.example` มีอยู่ และมีเฉพาะ placeholder ว่าง + บรรทัดคอมเมนต์ `AI_TIMEOUT_SECONDS`/`AI_TOP_N`; env อื่น: `INGEST_MAX_BYTES` (default 256 MiB), `DASH_*`) ดู PIPELINE_SPEC "Credentials and Secret Management"

## Usage

```bash
# ingest (CLI; ต้องส่ง --reference-date เสมอ — ไม่ส่ง = exit 2)
python -m src.ingest --input <csv> --reference-date 2026-10-02
# ดู run ล่าสุด
duckdb -readonly data/cybersecurity.duckdb \
  "SELECT run_id, status, reference_date, source_row_count FROM ingestion_runs ORDER BY started_at DESC LIMIT 1"
# dashboard
python dashboard/app.py
```

- **Query metric:** ไม่มี dbt semantic layer — metric query เป็น `Q-PORTFOLIO`, `Q-BY-PROJECT`, `Q-OVERDUE-DETAIL`, `Q-BY-OWNER` (ทุกตัวรับ `project_name` optional) ใน [METRIC_LOGIC.md](METRIC_LOGIC.md) บน `stg_actions` ของ latest successful run (นิยาม metric ที่ [METRIC_SPEC.md](METRIC_SPEC.md), ตาราง/คอลัมน์ที่ [DATA_MODEL_SPEC.md](DATA_MODEL_SPEC.md)) ห้ามเขียนสูตรใหม่ในที่อื่น
- **Dashboard:** routes ใน `dashboard/app.py`: `/` = `DASH-01` Portfolio Overview, `/overdue` = `DASH-02`, `/executive-summary` = `DASH-03` (ตาม [DASHBOARD_SPEC.md](DASHBOARD_SPEC.md) (`DASH-01` Portfolio, `DASH-02` Overdue, `DASH-03` Executive Summary); Dash ใช้ `Dash 4.x` ตาม corpus ภายใน แต่เวอร์ชัน pin = `null`
- **ไฟล์รายสัปดาห์ถัดไป:** ใช้ `--reference-date` ของรอบนั้น; ไฟล์เดิม + date เดิม = no-op (RUNBOOK "Pipeline Rerun")

## Architecture Overview

รายละเอียดทั้งหมดอยู่ที่ [PIPELINE_SPEC.md](PIPELINE_SPEC.md) (PL-01 `csv_ingest`, PL-02 `executive_summary_generate`); การปฏิบัติการที่ [RUNBOOK.md](RUNBOOK.md)

```
Weekly CSV --(CLI --input, --reference-date)--> src.ingest
   validate (DQ-*) -> raw_actions -> stg_actions (flags via sql/10_staging) -> reconcile (DQ-10)
   => data/cybersecurity.duckdb (ingestion_runs, raw_actions, stg_actions, data_quality_results, executive_summaries)
   --(read-only, latest successful run)--> Dash + AG Grid
```

Lineage ระดับ metric -> table -> source: [LINEAGE.md](LINEAGE.md)

## Contributing

- Coding conventions, ข้อห้าม และกติกาสำหรับ agent: [AGENTS.md](AGENTS.md)
- **PR review สำหรับ metric/pipeline ใหม่** (ข้อเสนอ `[DESIGN PROPOSAL]` ไม่มีกระบวนการที่อนุมัติแล้ว; ผู้ review = `{{DATA_STEWARD}}`, KPI/metric = `{{KPI_OWNER_ROLE}}`):
  1. แก้นิยามที่เอกสารเจ้าของเพียงที่เดียว (ดูตาราง Doc Index) อ้างที่อื่นด้วย ID ไม่คัดลอก
  2. เพิ่ม/แก้ test ใน TESTING_STRATEGY (rule/metric ใหม่ต้องมี test คู่)
  3. `pytest` ผ่าน; ไม่มี `date.today()` ใน metric logic
  4. เปลี่ยนที่กระทบตัวเลข -> บันทึกใน [ANALYTICS_CHANGELOG.md](ANALYTICS_CHANGELOG.md)
  5. ห้ามเพิ่ม metric ใน Do-Not-Build; ค่าที่ต้อง calibrate เป็น `null` พร้อม owner ห้ามเดา

## License

License Type: `null` — repo ไม่มีไฟล์ LICENSE และ plan.md ไม่ระบุ; Copyright Holder: `{{ORG_NAME}}` (ไม่ใส่ชื่อจริง); ผู้ตัดสิน `{{PROJECT_SPONSOR}}`. กรอบ compliance = PDPA (ประเทศไทย) — `owner` เป็น pseudonymous ID (`Owner-NNN`) ดู [DATA_GOVERNANCE.md](DATA_GOVERNANCE.md)

---

## Doc Index (23 docs)

เจ้าของ = role placeholder (ยังไม่มีบุคคลได้รับแต่งตั้ง) ลำดับ = topological ตาม `depends_on` (อ้างเฉพาะ upstream ตามหน้า front-matter ของแต่ละไฟล์) สถานะทุกฉบับ `draft` v1.0.0 ยกเว้นที่ระบุ

| # | Doc ID / ไฟล์ | Owner (role) | Purpose | depends_on |
|---|---|---|---|---|
| 1 | `business_glossary` [BUSINESS_GLOSSARY.md](BUSINESS_GLOSSARY.md) | `{{DATA_STEWARD}}` | ศัพท์ธุรกิจ + Enumeration Registry (index เท่านั้น) | — |
| 2 | `constraints` [CONSTRAINTS.md](CONSTRAINTS.md) | `{{PROJECT_SPONSOR}}` | CON-* ข้อจำกัดของ stack/โครงการ | — |
| 3 | `kpi_dictionary` [KPI_DICTIONARY.md](KPI_DICTIONARY.md) | `{{KPI_OWNER_ROLE}}` | KPI-01..03 (ผลลัพธ์ที่มีผู้รับผิดชอบ) | — |
| 4 | `stakeholders` [STAKEHOLDERS.md](STAKEHOLDERS.md) | `{{PROJECT_SPONSOR}}` | STK-*, literacy, คำถามหลัก | — |
| 5 | `metric_spec` [METRIC_SPEC.md](METRIC_SPEC.md) | `{{KPI_OWNER_ROLE}}` | MET-* นิยามและสูตร | kpi_dictionary, business_glossary, stakeholders |
| 6 | `data_model_spec` [DATA_MODEL_SPEC.md](DATA_MODEL_SPEC.md) | `{{DATA_STEWARD}}` | ตาราง/คอลัมน์/dimension | metric_spec |
| 7 | `data_contract` [DATA_CONTRACT.md](DATA_CONTRACT.md) | `{{DATA_STEWARD}}` + `{{PRODUCER_TEAMS}}` | สัญญากับผู้ส่ง CSV | data_model_spec |
| 8 | `viz_design_spec` [VIZ_DESIGN_SPEC.md](VIZ_DESIGN_SPEC.md) | `{{DASHBOARD_DEVELOPER}}` | chart_type_matrix, complexity gate | stakeholders, metric_spec |
| 9 | `metric_logic` [METRIC_LOGIC.md](METRIC_LOGIC.md) | `{{DATA_STEWARD}}` | SQL / Q-* queries | metric_spec, data_model_spec |
| 10 | `pipeline_spec` [PIPELINE_SPEC.md](PIPELINE_SPEC.md) | `{{DATA_STEWARD}}` | PL-01/02, ST-*, exit codes | data_model_spec, metric_logic |
| 11 | `data_quality` [DATA_QUALITY.md](DATA_QUALITY.md) | `{{DATA_STEWARD}}` | DQ-*/AN-* rules (threshold = `null`) | data_model_spec, pipeline_spec |
| 12 | `sla_freshness` [SLA_FRESHNESS.md](SLA_FRESHNESS.md) | `{{DATA_STEWARD}}` | FR-*/AL-* (tolerance = `null`) | pipeline_spec |
| 13 | `data_governance` [DATA_GOVERNANCE.md](DATA_GOVERNANCE.md) | `{{DPO_OR_LEGAL}}` | PDPA, access, retention (`null`) | data_model_spec, data_contract, kpi_dictionary |
| 14 | `testing_strategy` [TESTING_STRATEGY.md](TESTING_STRATEGY.md) | `{{DATA_STEWARD}}` | pytest suite T-* | pipeline_spec, data_quality, metric_logic |
| 15 | `runbook` [RUNBOOK.md](RUNBOOK.md) | `{{DATA_STEWARD}}` | RB-* incident/rerun/backup | pipeline_spec, sla_freshness, data_quality |
| 16 | `dashboard_spec` [DASHBOARD_SPEC.md](DASHBOARD_SPEC.md) | `{{DASHBOARD_DEVELOPER}}` | DASH-* หน้า/chart | metric_spec, kpi_dictionary, data_model_spec, stakeholders, testing_strategy, viz_design_spec |
| 17 | `report_spec` [REPORT_SPEC.md](REPORT_SPEC.md) | `{{ANALYTICS_TEAM}}` | รายงานตามรอบ (format/channel) | dashboard_spec, kpi_dictionary, metric_spec, stakeholders, sla_freshness |
| 18 | `lineage` [LINEAGE.md](LINEAGE.md) | `{{DATA_STEWARD}}` | metric -> table -> source, impact analysis | metric_logic, pipeline_spec, data_model_spec, dashboard_spec — สร้างแล้ว |
| 19 | `ai_model_spec` [AI_MODEL_SPEC.md](AI_MODEL_SPEC.md) | `{{DATA_STEWARD}}` | AI Executive Summary (bonus) | data_model_spec, metric_spec, data_quality, lineage — สร้างแล้ว |
| 20 | `tasks` [TASKS.md](TASKS.md) | `{{DATA_STEWARD}}` | task breakdown | kpi_dictionary, pipeline_spec |
| 21 | `analytics_changelog` [ANALYTICS_CHANGELOG.md](ANALYTICS_CHANGELOG.md) | `{{KPI_OWNER_ROLE}}` | บันทึกการเปลี่ยนที่กระทบตัวเลข | metric_spec, kpi_dictionary, pipeline_spec, data_contract |
| 22 | `agents_md` [AGENTS.md](AGENTS.md) | `{{DATA_STEWARD}}` | กติกา agent/coding | pipeline_spec, data_governance, constraints, data_model_spec |
| 23 | `readme` [README.md](README.md) (ฉบับนี้) | `{{DATA_STEWARD}}` | index + quick start | stakeholders, pipeline_spec, runbook, testing_strategy |

หมายเหตุ: role ของ owner ที่ระบุเป็นข้อเสนอสำหรับ index นี้ (ตรวจกับ front-matter/ตารางของแต่ละเอกสารเมื่อ reconcile); ไฟล์ทั้ง 23 ฉบับมีอยู่แล้ว (สถานะ `draft`); REFERENCE_DATE = 2026-10-02 (overdue 3,531, max `days_overdue` 46) ค่า 2026-10-01 ถูก supersede (ดู [ANALYTICS_CHANGELOG.md](ANALYTICS_CHANGELOG.md))

## Reading Order ตามผู้อ่าน

| ผู้อ่าน | ลำดับ |
|---|---|
| Analytics engineer ใหม่ | README -> CONSTRAINTS -> STAKEHOLDERS -> PIPELINE_SPEC -> DATA_MODEL_SPEC -> METRIC_LOGIC -> TESTING_STRATEGY -> RUNBOOK -> AGENTS |
| Stakeholder / ผู้บริหาร (STK-01..05) | STAKEHOLDERS -> KPI_DICTIONARY -> METRIC_SPEC -> BUSINESS_GLOSSARY -> DASHBOARD_SPEC |
| Dashboard developer | VIZ_DESIGN_SPEC -> DASHBOARD_SPEC -> METRIC_LOGIC -> DATA_MODEL_SPEC -> TESTING_STRATEGY |
| Data steward / on-call | RUNBOOK -> PIPELINE_SPEC -> DATA_QUALITY -> SLA_FRESHNESS -> DATA_CONTRACT |
| Governance / DPO | DATA_GOVERNANCE -> DATA_CONTRACT -> CONSTRAINTS -> LINEAGE |
| AI / bonus | AI_MODEL_SPEC -> DATA_GOVERNANCE -> PIPELINE_SPEC (PL-02) |
