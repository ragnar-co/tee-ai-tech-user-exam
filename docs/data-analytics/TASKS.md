# Task Breakdown

```yaml
doc_id: tasks
filename: TASKS.md
version: 1.0.0
status: draft
depends_on: [kpi_dictionary, pipeline_spec]
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

เอกสารนี้แตก KPI-01..03 (KPI_DICTIONARY.md), MET-01..08 (METRIC_SPEC.md; MET-07/MET-08 = draft) และ PL-01/PL-02 (PIPELINE_SPEC.md) เป็น task ที่ลงมือได้ ลำดับอิง plan.md §23 (Phase 1-10) และ §28 ไม่นิยามสูตร/กฎ DQ/layout ซ้ำ (อ้างด้วย ID) และ **ไม่กำหนดวันที่หรืองบ**

> **สถานะ (2026-10-02, ตรวจกับโค้ดจริง):** task ส่วนใหญ่ลงมือแล้ว — `work_item_status` ในตาราง Assignments สะท้อนความจริง `done` ในที่นี้ = มี code + ผ่าน pytest (ดู TESTING_STRATEGY) **แต่ยังไม่ครบ DoD ข้อ 1 ตามตัวอักษร:** repo ยังไม่มี commit/merge และไม่มี human code review อิสระ จึงอย่าอ่าน `done` ว่า "reviewed/merged" ข้อที่ยังไม่ยืนยัน: การเรียก OpenRouter จริง, การตรวจด้วยตาของ dark theme/colorblind/AG Grid (ทำให้ TSK-12/13 = `in_progress`) KPI ทั้งสามเป็น candidate (ยังไม่อนุมัติ) จึงถือเป็น P0 ตามเกณฑ์ "ต้องส่งเพื่อให้ MVP ตอบ requirement" `[ASSUMPTION]` ไม่ใช่ลำดับความสำคัญที่ผู้ถือผลประโยชน์อนุมัติ

## Task Breakdown

Pri: P0 = core MVP; P1 = optional/bonus. Upstream = KPI/metric/pipeline/query ที่ task รับใช้

| Task ID | Description | Upstream Reference | Pri |
|---|---|---|---|
| TSK-01 | บันทึก `REFERENCE_DATE` = 2026-10-02 (ค่าคงที่ iteration 1 ที่ผู้ใช้ยืนยัน; supersede 2026-10-01 — ดู ANALYTICS_CHANGELOG.md) เป็นค่าคงที่ใน `src/settings.py` (ไม่ใช่ CLI default — PIPELINE_SPEC บังคับให้ส่ง `--reference-date` ทุกครั้ง ไม่มี default) ที่เปลี่ยนผ่าน changelog เท่านั้น และบังคับกฎ "ห้าม `date.today()`" (CON-06) | MET-04, MET-05; KPI-02, KPI-03 | P0 |
| TSK-02 | Bootstrap repo: `pyproject.toml`, dependency (duckdb, dash, plotly, dash-ag-grid, pytest), `.env.example` | CON-01..05 | P0 |
| TSK-03 | Validator ตาม DATA_QUALITY (`src/validation.py`, `quality_checks.sql`) DQ-01..DQ-09 (+ DQ-11, DQ-12 และ DQ-01 duplicate header ที่เพิ่มตอน hardening) + validation result model | PL-01 ST-04; ทุก MET (ป้องกันข้อมูลผิดเข้า) | P0 |
| TSK-04 | Schema DDL `sql/00_schema/create_tables.sql` ตาม DATA_MODEL_SPEC | PL-01 ST-01 | P0 |
| TSK-05 | PL-01 `csv_ingest`: hash/idempotency, register run, load `raw_actions`, finalize (ST-02,03,05,08) + CLI args | PL-01 | P0 |
| TSK-06 | Build `stg_actions` (`sql/10_staging/stg_actions.sql`: flags, `days_overdue`) ตาม METRIC_LOGIC | MET-02..05; KPI-01, KPI-02 | P0 |
| TSK-07 | Reconcile DQ-10 (ST-07) และ persist `reference_date` ต่อ run | MET-01; KPI-01 | P0 |
| TSK-08 | Metric queries Q-PORTFOLIO, Q-BY-PROJECT, Q-OVERDUE-DETAIL, Q-BY-OWNER — ทุกตัวรับ parameter `project_name` (NULL/'All Projects' = ทั้งหมด; restrict แถว; Q-BY-PROJECT + project = 1 แถว; reference date อ่านจาก run ไม่ใช่ filter); Q-PORTFOLIO คืน `completion_rate` ด้วย | MET-01..05; KPI-01, KPI-02, KPI-03 | P0 |
| TSK-09 | `completion_rate` (MET-06) ใน Q-PORTFOLIO/Q-BY-PROJECT (กฎหารศูนย์ตาม METRIC_SPEC) | MET-06; KPI-01 | P1 |
| TSK-20 | MET-07 `owners_with_overdue_actions` และ MET-08 `open_not_overdue_actions` (draft; นับเท่านั้น ไม่มี threshold) ตาม METRIC_SPEC/METRIC_LOGIC + test | MET-07, MET-08; KPI-02, KPI-03 | P0 |
| TSK-21 | Test fixture `tests/fixtures/actions_small.csv` ที่ fixture date = 2026-09-15 (ต่างจาก REFERENCE_DATE เพื่อจับ `date.today()`): due 09-14 todo = overdue (days_overdue 1); due 09-15 todo และ 09-16 todo = ไม่ overdue; due 2026-08-01 done = ไม่ overdue; ข้อมูลสังเคราะห์เท่านั้น | MET-04, MET-05; TESTING_STRATEGY (T-M*, T-R*) | P0 |
| TSK-10 | Metric golden tests + reference-date tests (due == ref ไม่ overdue; ผลรวมโครงการ = portfolio; project filter restrict แถว) | MET-01..08 | P0 |
| TSK-11 | Dash app shell + project dropdown + แสดง reference date + latest successful run | KPI-01, KPI-02 | P0 |
| TSK-12 | Overview (DASH-01): KPI cards + by-project chart + project table + `project_name` filter callbacks (ส่งเป็น parameter ให้ทุก Q-*) | MET-01..05, MET-08; KPI-01, KPI-02 | P0 |
| TSK-13 | Overdue detail AG Grid (owner, due_date, days_overdue, sorting, project filter) + optional overdue-by-owner chart (DASH-02) | MET-04, MET-05, MET-07, Q-OVERDUE-DETAIL, Q-BY-OWNER; KPI-02, KPI-03 | P0 |
| TSK-14 | Data quality display (validation summary, row counts, findings, source file/run) | DQ-01..DQ-12; PL-01 | P0 |
| TSK-15 | Hardening: idempotency, latest-run handling, empty state, bad filter, DB lock (CON-15), smoke test, lint | PL-01; ทุก KPI | P0 |
| TSK-16 | README + reference-date declaration + known limitations + metric definitions (ลิงก์ METRIC_SPEC) | KPI-01..03 | P0 |
| TSK-17 | PL-02 `executive_summary_generate`: OpenRouter client (OpenAI-compatible chat-completions ตรงผ่าน HTTPS; ไม่ใช้ `aix`; library = `httpx` (implement แล้ว)), อ่าน env `OPENAI_API_KEY`/`OPENAI_BASE_URL`, model constant `anthropic/claude-sonnet-5`, `.env.example` (placeholder ว่าง), context จาก Q-* (aggregate + top-N overdue rows; N = env `AI_TOP_N` default 10), prompt version, guard (ไม่ใส่ severity/impact/SLA), save (`provider='openrouter'`), failure handling (timeout/rate-limit/HTTP error), mocked-HTTP tests | PL-02; อ่าน MET-01..05 | P1 |
| TSK-18 | Dash page Executive Summary (draft label, ปิดปุ่มพร้อมข้อความตั้งค่าเมื่อไม่มี `OPENAI_API_KEY` หรือ `OPENAI_BASE_URL`; core dashboard ไม่กระทบ) | PL-02 ST-21..25 | P1 |
| TSK-19 | Formal minimum DDD docs เมื่อทราบ central requirement (CON-25) | — | P1 |

**P0 coverage:** KPI-01 -> TSK-06,07,08,10,12; KPI-02 -> TSK-01,06,08,12,13,20; KPI-03 -> TSK-08,13,20; MET-07/08 -> TSK-20,21; MET-01 -> TSK-07,08; MET-02/03 -> TSK-06,08; MET-04/05 -> TSK-01,06,08,13; PL-01 -> TSK-04,05,06,07; PL-02 -> TSK-17,18 (bonus)

## Task Sequence and Dependencies

ลำดับ: TSK-01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08 -> 20 -> 21 -> 10 -> 11 -> 12 -> 13 -> 14 -> 15 -> 16 -> bonus (17, 18) -> 19 (plan §28: อย่าเริ่มจาก AI/visual polish ก่อน core metrics ผ่าน test)

| Task | depends_on[] | ทำคู่ขนานได้กับ |
|---|---|---|
| TSK-01 | — | TSK-02 |
| TSK-02 | — | TSK-01 |
| TSK-03 | TSK-02 | TSK-04 |
| TSK-04 | TSK-02 | TSK-03 |
| TSK-05 | TSK-01, TSK-03, TSK-04 | — |
| TSK-06 | TSK-04, TSK-05 | — |
| TSK-07 | TSK-06 | — |
| TSK-08 | TSK-06 | TSK-07 |
| TSK-09 | TSK-08 | TSK-10 |
| TSK-20 | TSK-06, TSK-08 | TSK-09, TSK-21 |
| TSK-21 | TSK-02 | TSK-03, TSK-04, TSK-20 |
| TSK-10 | TSK-07, TSK-08, TSK-20, TSK-21 | TSK-09, TSK-11 |
| TSK-11 | TSK-02, TSK-08 | TSK-10 |
| TSK-12 | TSK-10, TSK-11 | TSK-13 (หลัง shell) |
| TSK-13 | TSK-10, TSK-11 | TSK-12, TSK-14 |
| TSK-14 | TSK-07, TSK-11 | TSK-12, TSK-13 |
| TSK-15 | TSK-12, TSK-13, TSK-14 | — |
| TSK-16 | TSK-15 | TSK-17 |
| TSK-17 | TSK-08, TSK-15 | TSK-16 |
| TSK-18 | TSK-17, TSK-11 | — |
| TSK-19 | `null` — ขึ้นกับ central requirement (ยังไม่ทราบ) | — |

หมายเหตุ: ไม่มี cross-pipeline dependency ที่ PL-02 -> PL-01 นอกจากต้องมี run `succeeded` (PIPELINE_SPEC); วิจัย/ออกแบบ chart ให้ตรง VIZ_DESIGN_SPEC (ผู้ใช้หลัก literacy `basic`: KPI card, bar chart, ตาราง)

## Definition of Done

task ถือว่า `done` เมื่อผ่านทุกข้อที่เกี่ยวข้อง (ข้อที่ไม่เกี่ยวข้องระบุ N/A พร้อมเหตุผล):

1. **Code Complete** — merge และ review แล้ว ตามข้อกำหนดใน AGENTS.md (`agents_md`); ไม่มี logic ของ metric นอก SQL/data access layer (CON-08); ไม่มี `date.today()` ใน metric logic (CON-06); ไม่มี secret ใน repo (CON-21)
2. **Tests Pass** — test ที่ TESTING_STRATEGY.md (`testing_strategy`) กำหนดสำหรับ task นั้นผ่านทั้งหมด (pytest); task ที่แตะ metric ต้องมี golden/reference-date test; ห้ามระบุว่า "ผ่าน" ถ้ายังไม่เคยรัน
3. **Acceptance Criteria** — metric ตรงกับนิยามใน METRIC_SPEC.md/METRIC_LOGIC.md และ dashboard ตรงกับ DASHBOARD_SPEC.md (`dashboard_spec`); ตัวเลขเทียบกับ SQL ได้ (reconcile); ค่าสังเกต reference ใน KPI_DICTIONARY (total 14,013; overdue 3,531, max days_overdue 46 @ REFERENCE_DATE 2026-10-02) — fixture ทดสอบใช้ 2026-09-15 ใช้ตรวจ ไม่ hardcode
4. **Do-Not-Build check** — ไม่เพิ่ม risk/health/owner performance score, SLA compliance, on-time rate, cycle time, forecast (CON-09)

DoD เฉพาะ task: TSK-05 = "ไฟล์ผิดไม่ถูก ingest เงียบ ๆ; รันซ้ำไฟล์+reference date เดิม = no-op"; TSK-13 = "ทุกแถว overdue ที่แสดง reconcile กับ Q-OVERDUE-DETAIL"; TSK-17 = "ล้มเหลว -> ไม่มี fake summary, core dashboard ทำงานต่อ" (ยืนยันด้วย mock)

## Assignments and Estimates

ไม่มีข้อมูลคน/ทีม/ประมาณการจากผู้ให้ requirement จึง **ไม่กำหนดตัวเลขเอง** (ไม่มีวัน คน หรือ point ที่เดา)

| Task | Owner | Estimated Effort | Status (`work_item_status`) | หลักฐาน / หมายเหตุ |
|---|---|---|---|---|
| TSK-01 | `{{DATA_STEWARD}}` (ค่า REFERENCE_DATE ผู้ใช้ยืนยันแล้ว; เปลี่ยนต้องอนุมัติโดย `{{PROJECT_SPONSOR}}`) | `null` | `done` | `src/settings.py`; T-R07/T-R10 |
| TSK-02 | `{{DATA_ENGINEER}}` | `null` | `done` | `pyproject.toml`, `.env.example`, `.venv` |
| TSK-03 | `{{DATA_ENGINEER}}` | `null` | `done` | DQ-01..DQ-12 ใน `src/validation.py` + `quality_checks.sql`; T-V* |
| TSK-04 | `{{DATA_ENGINEER}}` | `null` | `done` | `sql/00_schema/create_tables.sql`; T-S* |
| TSK-05 | `{{DATA_ENGINEER}}` | `null` | `done` | `src/ingest.py`; T-I*, idempotency, `test_hardening_ingest.py` |
| TSK-06 | `{{DATA_ENGINEER}}` | `null` | `done` | `sql/10_staging/stg_actions.sql` |
| TSK-07 | `{{DATA_ENGINEER}}` | `null` | `done` | ST-07 reconcile (DQ-10) + `ingestion_runs.reference_date`; (`app_config` เขียนแต่ไม่อ่าน) |
| TSK-08 | `{{DATA_ENGINEER}}` | `null` | `done` | `sql/20_metrics/q_*.sql` + `src/metrics.py`; T-M* |
| TSK-09 | `{{DATA_ENGINEER}}` | `null` | `done` | `completion_rate` ใน Q-PORTFOLIO/Q-BY-PROJECT; T-M07/M15 |
| TSK-10 | `{{DATA_ENGINEER}}` | `null` | `done` | `test_metrics.py`, `test_reference_date.py`, `test_reconciliation.py` |
| TSK-20 | `{{DATA_ENGINEER}}` | `null` | `done` | MET-07/MET-08; T-M13/M14 |
| TSK-21 | `{{DATA_ENGINEER}}` | `null` | `done` | `tests/fixtures/actions_small.csv` |
| TSK-11 | `{{DASHBOARD_DEVELOPER}}` | `null` | `done` | `dashboard/app.py` (3 routes, project dropdown, header); Flask test client + server จริง |
| TSK-12 | `{{DASHBOARD_DEVELOPER}}` | `null` | `in_progress` | โค้ด+test ครบ; การตรวจด้วยตา: screenshot ครั้งเดียว ยังไม่ตรวจ dark theme / colorblind |
| TSK-13 | `{{DASHBOARD_DEVELOPER}}` | `null` | `in_progress` | โค้ด+test (grid reconcile กับ metrics) ครบ; AG Grid ยังไม่ตรวจด้วยตา |
| TSK-14 | `{{DASHBOARD_DEVELOPER}}` | `null` | `done` | แผง CH-12 (`cards.dq_panel`); ไม่แสดง `record_key`/`message` |
| TSK-15 | `{{DATA_ENGINEER}}` + `{{DASHBOARD_DEVELOPER}}` | `null` | `done` | idempotency, latest-run, empty state, bad filter, DB lock (exit 3), ruff สะอาด ณ เวลาที่เขียน; ยังไม่มี browser e2e/CI |
| TSK-16 | `{{DATA_STEWARD}}` | `null` | `done` | root `README.md` อัปเดตตามความจริง (รอบ reconcile 2026-10-02) รวมหัวข้อ Docker (`Dockerfile`, `docker-compose.yml`, `docker/entrypoint.sh` — ยืนยันบน Docker 29.8.1; นอก task เดิม เป็นงานเสริม) |
| TSK-17 | `{{DATA_ENGINEER}}` | `null` | `done` | `src/ai/*` (httpx, prompt `exec-summary-v2`, caps, `seq_summary_id`); **mocked HTTP เท่านั้น — ไม่เคยเรียก OpenRouter จริง**; open: PDPA/residency, guardrail ของ workspace |
| TSK-18 | `{{DATA_ENGINEER}}` | `null` | `done` | หน้า `/executive-summary`; ปุ่มปิดเมื่อไม่มี env; ทดสอบด้วย mock |
| TSK-19 | `{{PROJECT_MANAGER}}` | `null` | `done` | แทนด้วยเอกสาร 23 ฉบับใน `docs/data-analytics/` (plan §18 เลิกใช้ประเด็น minimum list); central requirement จริงยังไม่ทราบ และไม่มี independent review ของเอกสาร |

Estimated Effort = `null` ทุกแถว — calibration source: การประเมินของทีมพัฒนาหลังกำหนดขนาด/ทักษะ และ delivery budget/go-live (CON-22, CON-23 = `null`); owner: `{{PROJECT_MANAGER}}` หน่วย (วัน/point) = `null` จนทีมตกลง

### Enum: `work_item_status` (owner: TASKS.md)

enum นี้นิยามที่เอกสารนี้ที่เดียว; เอกสารอื่นอ้างด้วยชื่อ และลงทะเบียนชื่อใน Enumeration Registry ของ BUSINESS_GLOSSARY.md (`business_glossary`) เท่านั้น เป็นคนละ enum กับสถานะของ entity ใน data model (เช่น `status` ของ action, `ingestion_run_status`)

| ค่า | ความหมาย |
|---|---|
| `not_started` | ยังไม่เริ่มลงมือ |
| `in_progress` | กำลังทำ (มีผู้รับงานแล้ว) |
| `done` | ผ่านทุกข้อของ Definition of Done |

(ตรงกับ "not started / in progress / done" ใน spec; ไม่มีค่า blocked — ถ้าต้องการ ให้เพิ่มผ่านการเปลี่ยนเวอร์ชันของเอกสารนี้)

## Open Questions

1. ทีม/คนที่รับผิดชอบจริงและหน่วย/ขนาดประมาณการ (แทน role placeholder)
2. KPI owner/target (KPI-01..03 ยัง candidate; ผลต่อความเป็น P0)
3. Central minimum DDD requirement (TSK-19) และ open item ของ TSK-17: PDPA classification ของ `owner`/`action_name` + data residency (OpenRouter -> Anthropic) รอ `{{DPO_OR_LEGAL}}`, และ guardrail ของ OpenRouter workspace (อนุญาตเฉพาะ `anthropic/claude-sonnet-5` — ยังไม่ยืนยันกับ key ของโปรเจกต์นี้)
