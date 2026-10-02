# Testing Strategy

```yaml
doc_id: testing_strategy
filename: TESTING_STRATEGY.md
version: 1.0.0
status: draft
depends_on: [pipeline_spec, data_quality, metric_logic]
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

เอกสารนี้นิยามแผนทดสอบด้วย **pytest** (CON-05; ไม่ใช้ dbt) ครอบคลุม DQ rule ทุกข้อใน DATA_QUALITY.md และ query/metric ทุกตัว (MET-01..MET-08) ใน METRIC_LOGIC.md แยกชัดเจน: **data contract** = ข้อตกลงกับ producer (`data_contract`), **quality rule** = สิ่งที่ตรวจเมื่อไฟล์มาถึง (DATA_QUALITY.md), **test** = สิ่งที่รันใน CI กับ input ที่ทราบผล (เอกสารนี้) — test ที่ fail แปลว่าโค้ด/SQL ของเราผิด ไม่ใช่ producer

> **สถานะการยืนยัน (2026-10-02):** `tests/` มีอยู่และรันได้จริงด้วย `.venv/bin/pytest -q` — **ผ่าน 277 test ณ เวลาที่เขียน** (ตัวเลขเปลี่ยนได้ขณะมีการเพิ่ม test) และ `ruff` ผ่านตอนเริ่มรอบ reconcile (รัน `ruff check .` ซ้ำก่อนส่งมอบ) ไฟล์ test จริง: `test_validation.py`, `test_ingest.py`, `test_idempotency.py`, `test_metrics.py`, `test_reference_date.py`, `test_reconciliation.py` (T-X01/T-X02: CSV vs DuckDB บนไฟล์ sample), `test_hardening_ingest.py` (edge case ของไฟล์/DB/CLI), `test_ai_provider.py`, `test_ai_summary_service.py`, `test_ai_context_builder.py`, `test_ai_prompt_hardening.py`, `test_dashboard_components.py`, `test_dashboard_app.py` + helper อิสระ `tests/reference_calc.py` (T-F01/T-X01) และ `tests/reference_validation.py` (T-V15) ไม่มี `test_schema.py` / `test_dashboard_smoke.py` / `test_ai_summary.py` ตามที่เสนอไว้ตอนแรก — เนื้อหาอยู่ในไฟล์ข้างต้น (ดูหมายเหตุต่อหัวข้อ) **ยืนยันแล้ว:** ingest/validation/metrics/idempotency/reference-date/AI (mocked HTTP) ผ่าน test; dashboard ยืนยันผ่าน Flask test client (layout, callback, project filter) และ server จริงที่ `127.0.0.1:8050` (page load, callback) **ยืนยันเพิ่ม (manual, ไม่ใช่ pytest):** เรียก OpenRouter จริงสำเร็จ 2 ครั้ง (2026-10-02) ผ่านปุ่ม Generate; pytest/CI ยังใช้ mocked HTTP เท่านั้น **ยังไม่ยืนยัน/ยังไม่ได้ทำ:** EV-01..EV-05 กับ prompt v2, guardrail ของโมเดลอื่น; การตรวจด้วยตา — headless Chrome screenshot ถ่ายครั้งเดียว ส่วน dark theme, colorblind mode และ AG Grid **ไม่ได้ตรวจด้วยตา**; browser e2e (`dash.testing`) ไม่มี; line/branch coverage ไม่ได้วัด ค่าตัวเลขจากไฟล์ sample จริงที่ `REFERENCE_DATE = 2026-10-02` (ค่าคงที่ iteration 1 ที่ผู้ใช้ยืนยัน) รันซ้ำใน T-R08 (marker `sample`)

## กฎพื้นฐานของชุดทดสอบ

1. **Test reference date แยกจาก REFERENCE_DATE (D1/D2):** ค่าที่ใช้ใน fixture ของ test = `TEST_REFERENCE_DATE = 2026-09-15` — ค่าของ test เท่านั้น; `REFERENCE_DATE = 2026-10-02` (ค่าคงที่ iteration 1) ใช้เฉพาะ test ที่รันกับ sample CSV (T-R08, T-I02) และ T-R10 ทั้งสองค่าเก็บเป็นค่าคงที่แยกกันใน `tests/conftest.py` ห้ามใช้ค่าหนึ่งแทนอีกค่า — **เจตนาให้ `TEST_REFERENCE_DATE` ต่างจากทั้ง `REFERENCE_DATE` และวันของระบบ**
2. **ห้ามพึ่ง system clock:** ทุก test ส่ง `--reference-date`/พารามิเตอร์ชัดแจ้ง เหตุผลสำคัญ: ณ วันที่เขียนเอกสารนี้ (2026-10-02) วันที่ของระบบ **เท่ากับ** `REFERENCE_DATE` (บังเอิญ ไม่ถาวร) แต่ **ต่างจาก** `TEST_REFERENCE_DATE = 2026-09-15` ดังนั้น test บน golden fixture จะจับ bug `date.today()` ได้ทันที (วันนี้ fixture จะให้ overdue 8 แทน 5 — ดู T-R06) ส่วน test ที่รันที่ `REFERENCE_DATE` (T-R08, T-I02) **จับไม่ได้** ขณะวันของระบบยังเป็น 2026-10-02 จึงมี T-R09 ที่รันหลาย reference date ห่างจากทั้งวันปัจจุบันและ `REFERENCE_DATE` และ T-R07 ที่สแกนหา `date.today()` / `datetime.now()` / `current_date` ในโค้ด metric
3. **แยก DB ต่อ test:** ใช้ DuckDB ชั่วคราวใน `tmp_path` ไม่แตะ `data/cybersecurity.duckdb`
4. **Input ที่ผิดสร้างจากโค้ด:** sample CSV สะอาด (ไม่มี null/duplicate/วันที่ผิด) จึงพิสูจน์กรณี invalid ไม่ได้ — สร้างไฟล์ผิดโดยดัดแปลง golden fixture ใน `tmp_path`; fixture ที่ commit จริงตาม plan = `tests/fixtures/actions_small.csv`
5. **Pytest markers (ลงทะเบียนใน `pyproject.toml`):** `unit`, `integration`, `sample` (ใช้ `src/tee_cybersecurity_actions_mock.csv`) — `unit`/`integration` ถูกใส่ให้ test กำลังอยู่ระหว่างปรับ (รัน `pytest --markers` / `-m` เพื่อตรวจสถานะจริง); `e2e` (browser) **ไม่มี** — ไม่มี browser test

## Golden Fixture (`tests/fixtures/actions_small.csv`, 12 แถว)

ข้อมูลสมมติ (ไม่ใช่ข้อมูลองค์กร) ออกแบบให้ไม่มี tie ในการเรียง overdue และมีกรณีขอบครบ; `action_name` ของ A001 ใช้ข้อความไทยพร้อม branch tag เพื่อทดสอบ UTF-8

| action_id | project_name | owner | due_date | status | ที่ `TEST_REFERENCE_DATE` 2026-09-15: overdue / days |
|---|---|---|---|---|---|
| A001 | P01 - Alpha | Owner-001 | 2026-09-14 | todo | yes / 1 |
| A002 | P01 - Alpha | Owner-002 | 2026-09-15 | todo | no (due == ref) |
| A003 | P01 - Alpha | Owner-001 | 2026-09-16 | in_progress | no |
| A004 | P01 - Alpha | Owner-003 | 2026-08-01 | done | no (done) |
| A005 | P01 - Alpha | Owner-002 | 2026-09-05 | in_progress | yes / 10 |
| B001 | P02 - Beta | Owner-001 | 2026-09-20 | done | no |
| B002 | P02 - Beta | Owner-003 | 2026-07-18 | todo | yes / 59 |
| B003 | P02 - Beta | Owner-002 | 2026-09-12 | done | no (done) |
| B004 | P02 - Beta | Owner-003 | 2026-09-15 | in_progress | no (due == ref) |
| C001 | P03 - Gamma | Owner-001 | 2026-09-13 | todo | yes / 2 |
| C002 | P03 - Gamma | Owner-002 | 2026-07-18 | done | no (done) |
| C003 | P03 - Gamma | Owner-003 | 2026-09-12 | in_progress | yes / 3 |

**ผลคาดหวังที่ 2026-09-15** (ตรวจโดยรัน SQL ของ METRIC_LOGIC บน DuckDB กับแถวข้างบน) — Q-PORTFOLIO: total 12, completed 4, open 8, overdue 5, `open_not_overdue_actions` 3, `owners_with_overdue_actions` 3, `completion_rate` 1/3; max days_overdue 59

| project_name | total | completed | open | overdue | open_not_overdue | completion_rate |
|---|---|---|---|---|---|---|
| P01 - Alpha | 5 | 1 | 4 | 2 | 2 | 0.2 |
| P02 - Beta | 4 | 2 | 2 | 1 | 1 | 0.5 |
| P03 - Gamma | 3 | 1 | 2 | 2 | 0 | 1/3 |

`owners_with_overdue_actions` ต่อ scope (Q-PORTFOLIO + `project_name`): P01 = 2 (Owner-001, Owner-002), P02 = 1 (Owner-003), P03 = 2 (Owner-001, Owner-003), All = **3** — ไม่เท่าผลรวมต่อ project (5): ยืนยันว่า MET-07 ไม่ additive Portfolio `completion_rate` = 4/12 = 1/3 (ต่างจากค่าเฉลี่ยของอัตราต่อ project 0.3444 — ใช้พิสูจน์กฎ Aggregation ใน DATA_MODEL_SPEC) Q-OVERDUE-DETAIL เรียง: B002 (59), A005 (10), C003 (3), C001 (2), A001 (1) Q-BY-OWNER: Owner-001 = 2, Owner-003 = 2, Owner-002 = 1 (เสมอกันเรียงตาม `owner`)

**ผลคาดหวังที่ reference date อื่น (fixture เดียวกัน; ตรวจโดยรันแล้ว):**

| reference date | overdue | open_not_overdue | max days_overdue | owners_with_overdue | หมายเหตุ |
|---|---|---|---|---|---|
| 2026-09-14 | 4 (A005, B002, C001, C003) | 4 | 58 (B002) | 3 | A001 due == ref จึงไม่ overdue; P01 = 1, P02 = 1, P03 = 2 |
| 2026-09-15 | 5 | 3 | 59 | 3 | ค่า fixture หลัก |
| 2026-10-02 (= `REFERENCE_DATE` = วันของระบบตอนเขียน) | 8 (open ทุกแถว) | 0 | 76 (B002) | 3 | ใช้เป็น "คำตอบที่ผิดของ bug `date.today()`" |
| 2027-01-01 | 8 | 0 | 167 | 3 | |
| 2026-07-01 | 0 | 8 | n/a (ไม่มี overdue) | 0 | due ทุกแถว >= 2026-07-18 |

## Unit Tests (pytest + SQL assertions)

dbt ไม่ใช้ — เทียบเท่า schema test = SQL assertion ใน `sql/30_quality/` และ test ใน pytest

### Validation (`tests/test_validation.py`) — ทุก DQ rule มีอย่างน้อยหนึ่ง test

| Test ID | Rule | สถานการณ์ | ผลที่คาดหวัง |
|---|---|---|---|
| T-V01 | DQ-01 | header ขาดคอลัมน์ (เช่น ไม่มี `owner`) | finding `blocking`; run `failed`; ไม่มีแถวใน `raw_actions`/`stg_actions`; exit 1 |
| T-V02 | DQ-01 | มีคอลัมน์เกิน | finding `warning` ระบุชื่อ; โหลดสำเร็จ; คอลัมน์เกินไม่ถูกโหลด |
| T-V03 | DQ-02 | `action_id` ว่าง/เว้นวรรคล้วน | `blocking` พร้อม `source_row_number` |
| T-V04 | DQ-03 | `action_id` ซ้ำ 2 แถว | `blocking` หนึ่ง finding ต่อ id; ทั้งสองแถวถูกนับเป็น invalid |
| T-V05 | DQ-04 | `project_name` ว่าง | `blocking` |
| T-V06 | DQ-05 | `action_name` ว่าง | `blocking` |
| T-V07 | DQ-06 | `owner` ว่าง | `blocking` |
| T-V08 | DQ-07 | `due_date` ว่าง / `2026/10/01` / `2026-02-30` / `2026-1-5` / มีช่องว่างนำหน้า | `blocking` ทุกกรณี |
| T-V09 | DQ-08 | `status` ว่าง | `blocking` |
| T-V10 | DQ-09 | status ใหม่ (เช่น `blocked`) และรูปแบบต่างตัวพิมพ์ (`Done`) | `investigation`; โหลดสำเร็จ; ไม่ถูก map; ถูกนับเป็น open |
| T-V11 | DQ-10 | run ปกติ | `source_row_count = valid + invalid = COUNT(raw) = COUNT(stg)` |
| T-V12 | DQ-10 | inject ให้ stg ขาดแถว | `blocking`; rollback; run `failed` |
| T-V13 | DQ-02..08 | แถวเดียว fail หลาย rule | หลาย finding; `invalid_row_count` นับครั้งเดียว |
| T-V14 | ทุก blocking | ไฟล์มีแถวผิดผสมแถวดี | ทุกแถวผิดมี finding (`record_key`/`source_row_number`); **ไม่มีแถวหายเงียบ**; จำนวน finding ตรงกับที่ฝัง |
| T-V15 | ความเทียบเท่า | ชุดไฟล์ผิด DQ-01..DQ-12 | ผล SQL (`sql/30_quality/quality_checks.sql`, บรรทัดฐาน) = ผลของตัวประเมินอิสระใน Python (`tests/reference_validation.py`) — implementation จริงมีทางเดียว (SQL เรียกจาก `src/validation.py`) จึงเทียบกับ evaluator อิสระใน test |
| T-V16 | UTF-8/BOM | ไฟล์มี BOM และข้อความไทย | header อ่านถูก (ไม่มี `﻿action_id`); ข้อความไทยกลับมาตรงกับต้นฉบับ (อ่านด้วย `utf-8-sig`) |
| T-V17 | DQ-01 (duplicate header) | header มีชื่อคอลัมน์ซ้ำ (เช่น `owner,owner`) | finding `blocking` ต่อชื่อที่ซ้ำ (binding กำกวม จึงไม่รัน row-level check); ไฟล์ถูกปฏิเสธ (`test_duplicate_header_column_blocking` ใน `test_hardening_ingest.py`) |
| T-V18 | DQ-11 | แถวที่จำนวน field ไม่เท่า header (ขาด/เกิน เช่น comma ไม่ quote) | `blocking` ต่อแถว (`record_key` = source row); นับเป็น invalid; ไม่ drop field เงียบ ๆ (`test_short_row_blocking_not_dropped`, `test_overlong_row_extra_fields_flagged`) |
| T-V19 | DQ-12 | control character (เช่น NUL) ใน field | `warning`; ค่าถูกเก็บตามเดิม (`test_control_chars_warning_kept_as_is`) |

### SQL structural / flag assertions (จริงอยู่ใน `tests/test_ingest.py` — `test_s_structure`, `test_s06_*`, `test_s09_*`, `test_s_dq_check_names_and_severity_in_enum`; ไม่มี `test_schema.py`)

| Test ID | ตาราง | Assertion |
|---|---|---|
| T-S01 | `stg_actions` | `is_open = NOT is_completed` ทุกแถว |
| T-S02 | `stg_actions` | `is_overdue` -> `is_open` (ไม่มี done ที่ overdue) |
| T-S03 | `stg_actions` | `is_overdue` <=> `days_overdue > 0`; ไม่ overdue -> `days_overdue = 0` |
| T-S04 | `stg_actions` | PK (`run_id`, `action_id`) ไม่ซ้ำ (RI-05) |
| T-S05 | `stg_actions`/`raw_actions` | RI-01, RI-02 คืน 0 แถวหลัง ingest สำเร็จ |
| T-S06 | `ingestion_runs` | transition: `running` -> `succeeded`/`failed`; `completed_at` ไม่ NULL เมื่อจบ; run `running` ไม่เป็น latest successful run |
| T-S07 | `data_quality_results` | RI-03 คืน 0 แถว; `severity_class` อยู่ใน enum `rule_severity`; `check_name` อยู่ในชุดที่อนุญาต = `DQ-01..DQ-12` (รวม DQ-11 row shape, DQ-12 control character) |
| T-S08 | `app_config` / ทุกตาราง | ไม่มี column/ค่าที่เก็บ API key; (ถ้ามีตาราง) key ไม่เป็น secret (CON-21) |
| T-S09 | `executive_summaries` | RI-04 คืน 0 แถว; ชื่อ column ตรง plan.md §9.5 ทุกตัว |
| T-S10 | ทุกตาราง | ชื่อ column ใน DDL ตรง DATA_MODEL_SPEC (schema conformance) |

### Row count checks

T-S11: หลัง ingest golden fixture `raw_actions` และ `stg_actions` ต้องไม่ว่างและเท่ากับ 12 ไฟล์ header-only (0 แถว) — **ตัดสินแล้ว:** ปฏิเสธด้วย exit 2 ก่อนเขียน DB (ไม่สร้าง run) ทดสอบใน `test_header_only_exit2_no_db`, `test_i03b_*`; ไฟล์ว่าง/BOM-only ก็ exit 2

## Integration Tests (`tests/test_ingest.py`, `tests/test_idempotency.py`, `tests/test_hardening_ingest.py`)

รายการเพิ่มเติมที่ไม่มี ID แยก (อยู่ใน `test_hardening_ingest.py`): ขนาดไฟล์เกิน `INGEST_MAX_BYTES` (default 256 MiB) -> exit 2 ไม่เขียน DB; `source_file` เก็บเฉพาะ basename; ข้อความ error/finding ที่เก็บมีเฉพาะชนิด exception ไม่มี path/เนื้อหา; CRLF/LF/BOM/ไทย/newline ใน quoted field; whitespace ล้วน (รวม U+00A0, U+3000, U+200B, U+FEFF) นับว่าว่าง; DB ถูกล็อก/reader เปิดอยู่ -> exit 3; parametrized project_name ที่เป็น SQL-injection-like ผ่าน data access layer; ไฟล์ 140k แถว (ตรวจเวลา/หน่วยความจำ)


| Test ID | ชื่อ | สถานการณ์ | ผลที่คาดหวัง |
|---|---|---|---|
| T-I01 | end-to-end golden | `python -m src.ingest --input actions_small.csv --reference-date 2026-09-15` | run `succeeded`; row counts = 12/12/12; `reference_date` เก็บใน run; stg flags ตามตาราง golden |
| T-I02 | end-to-end sample (`sample`) | ingest `src/tee_cybersecurity_actions_mock.csv` ด้วย `REFERENCE_DATE` (`2026-10-02`) | ผ่าน validation; counts = 14,013; ตัวเลข informational ตรงกับ T-R08 |
| T-I03 | CLI args | ไม่ส่ง `--reference-date` / รูปแบบผิด / ไฟล์ไม่มี | exit 2; ไม่มีการเขียน DB; ไม่ fallback เป็น `date.today()` |
| T-I04 | failed run ไม่ใช่ latest | ingest ดี -> ingest ผิด | latest successful run ยังเป็นรอบดี; dashboard query ยังได้ค่ารอบดี |
| T-I05 | idempotency (A/B) | ingest ไฟล์เดิม + reference date เดิม สองครั้ง | no-op ครั้งที่สอง; มี succeeded run เดียว; จำนวนแถว raw/stg ไม่เพิ่ม; ตอบ `run_id` เดิม |
| T-I06 | ไฟล์เดิม ref date ต่าง | ingest golden ที่ `2026-09-15` แล้ว `2026-09-14` | 2 run; overdue 5 vs 4; ทั้งสอง run คงอยู่ไม่ถูกแก้ |
| T-I07 | re-run หลัง failed | ไฟล์ผิด -> แก้ไฟล์ -> รันใหม่ | สร้าง run ใหม่ `succeeded` (run `failed` ไม่นับเป็นซ้ำ) |
| T-I08 | atomicity | inject ข้อผิดพลาดที่ ST-06 | ไม่มีแถว raw/stg ค้างของ run นั้น (rollback); run `failed` |
| T-I09 | backfill (characterization) | โหลดไฟล์เก่าหลังไฟล์ใหม่ | บันทึกพฤติกรรมจริงของ "latest" (`max(run_id)`); ผลของ test นี้ใช้ตอบ METRIC_LOGIC Open Question 2 |
| T-I10 | DB ถูกล็อก | process อื่นถือไฟล์ DB | exit 3; ไม่ทิ้ง run `running` ค้างโดยไม่รู้ (หรือถูกบันทึกเป็น `failed` เมื่อทำได้) — พฤติกรรมตามที่ตัดสินใน PIPELINE_SPEC Open Question 3 |

## Metric Validation Tests (`tests/test_metrics.py`, `tests/test_reference_date.py`)

Unit test พิสูจน์ว่า SQL ทำตามที่เขียน; metric validation พิสูจน์ว่าตัวเลขตรงความจริง — ผ่านทุก unit test แล้วยังรายงานผิดได้ จึงต้องมีทั้งสองแบบ ทุก test ด้านล่างเรียก **SQL จริงของ METRIC_LOGIC.md** (Q-PORTFOLIO, Q-BY-PROJECT, Q-OVERDUE-DETAIL, Q-BY-OWNER ผ่าน data access layer `src/metrics.py`) ไม่ใช่สูตรที่เขียนซ้ำในเทสต์

### Golden dataset (`T-M*`)

| Test ID | Metric | Assertion (ที่ `TEST_REFERENCE_DATE`) |
|---|---|---|
| T-M01 | MET-01 | portfolio total = 12 |
| T-M02 | MET-02 | completed = 4 |
| T-M03 | MET-03 | open = 8 |
| T-M04 | MET-04 | overdue = 5 (A001, A005, B002, C001, C003) |
| T-M05 | MET-05 | `days_overdue` ต่อ action = {A001:1, A005:10, B002:59, C001:2, C003:3}; max = 59; ทุกค่า > 0 |
| T-M06 | MET-01..04 ต่อ project | ตรงตาราง golden (3 projects) |
| T-M07 | MET-06 | completion_rate ต่อ project = 0.2 / 0.5 / 1/3; portfolio = 1/3 (ไม่ใช่ค่าเฉลี่ยของอัตรา) — เปรียบเทียบด้วย `pytest.approx` (ค่า default ของไลบรารี ไม่ใช่ tolerance ที่ calibrate); จำนวนนับเทียบด้วยความเท่ากันแบบ integer |
| T-M08 | Q-OVERDUE-DETAIL | ลำดับ B002, A005, C003, C001, A001; คอลัมน์ครบ (`action_id, project_name, action_name, owner, due_date, status, days_overdue`) |
| T-M09 | Q-BY-OWNER | Owner-001=2, Owner-003=2, Owner-002=1; นับจำนวนเท่านั้น ไม่มี column score |
| T-M10 | filter (D3) | พารามิเตอร์ `project_name` ของ **ทุก Q-*** จำกัดแถว: Q-PORTFOLIO(`P02 - Beta`) = แถว P02 ของ Q-BY-PROJECT (total 4, completed 2, open 2, overdue 1, open_not_overdue 1, completion_rate 0.5, owners_with_overdue 1); Q-BY-PROJECT(`P02 - Beta`) = **1 แถว**; Q-OVERDUE-DETAIL(`P02 - Beta`) = [B002]; Q-BY-OWNER(`P02 - Beta`) = [Owner-003 = 1]; `NULL`/`All Projects` (หลัง data access layer แปลงเป็น `NULL`) = portfolio |
| T-M11 | invariant | ผลรวมของ Q-BY-PROJECT = Q-PORTFOLIO สำหรับ MET-01..04 และ MET-08; `open = total - completed`; `overdue <= open`; `open_not_overdue = open - overdue`; **MET-07 ไม่อยู่ในผลรวม** (ต่อ project 2+1+2 = 5 > portfolio 3) |
| T-M12 | empty scope | project ไม่มีอยู่ -> count = 0, `completion_rate` = 0, MET-07/MET-08 = 0, ไม่ error (Q-BY-PROJECT / Q-OVERDUE-DETAIL / Q-BY-OWNER = 0 แถว); ไม่มี succeeded run -> ผลว่าง (ไม่ crash) |
| T-M13 | MET-07 | `owners_with_overdue_actions` ที่ `TEST_REFERENCE_DATE`: All = 3; P01 = 2; P02 = 1; P03 = 2 (นับ DISTINCT owner เฉพาะแถว overdue; Owner-001 มี overdue 2 แถวนับ 1); ที่ `2026-07-01` = 0 |
| T-M14 | MET-08 | `open_not_overdue_actions` ที่ `TEST_REFERENCE_DATE`: All = 3 (A002, A003, B004); P01 = 2; P02 = 1; P03 = 0; = `open_actions - overdue_actions` ทุก scope; แถว `done` ไม่นับ |
| T-M15 | Q-PORTFOLIO completion_rate | Q-PORTFOLIO คืน `completion_rate` เอง (ไม่ต้องพึ่ง Q-BY-PROJECT): All = 1/3 (`pytest.approx`), P01 = 0.2, scope ว่าง = 0 (UI ต้องแสดง no-data ตาม `total_actions = 0`) |

### Formula consistency (`T-F*`)

T-F01: implement ตัวคำนวณอิสระใน Python ล้วนตามสูตรใน METRIC_SPEC.md (ไม่ใช้ DuckDB) แล้วเทียบกับผล SQL ของ METRIC_LOGIC สำหรับ golden fixture และ fixture สุ่มที่มี seed คงที่ — พิสูจน์ว่า SQL = สูตร (METRIC_SPEC Formula Reference)

### Reference date (`tests/test_reference_date.py`; plan.md §16)

| Test ID | Case (`reference_date = 2026-09-15` = `TEST_REFERENCE_DATE`) | ผล |
|---|---|---|
| T-R01 | `due_date = 2026-09-14`, `todo` | overdue = true, `days_overdue = 1` |
| T-R02 | `due_date = 2026-09-15`, `todo` | overdue = false (due == ref) |
| T-R03 | `due_date = 2026-09-16`, `todo` | overdue = false |
| T-R04 | `due_date = 2026-08-01`, `done` | overdue = false |
| T-R05 | `in_progress` due ก่อน ref | overdue = true (open ทั้ง `todo` และ `in_progress`) |
| T-R06 | golden fixture รันที่ `2026-09-15`, `2026-09-14` และ `2026-10-02` | ที่ 09-15: overdue 5, max days 59; ที่ 09-14: overdue 4, max 58, A001 ไม่ overdue; ที่ 10-02: overdue 8, max 76 — ทั้งสามผลต่างกัน (พิสูจน์ว่า reference date ขับตัวเลข) **เหตุผลด้านนาฬิกา:** วันของระบบตอนเขียน = 2026-10-02 = `REFERENCE_DATE` แต่ fixture ใช้ 09-15; ถ้า metric code แอบใช้ `date.today()` ผลของ fixture จะเป็น overdue 8 (ค่าของ 10-02) ไม่ใช่ 5 → test ล้มทันทีวันนี้ (ไม่ต้อง mock นาฬิกา) และเมื่อวันของระบบเลื่อนต่อไป ผลที่ผิดก็ยังต่างจากค่าคาดหวัง |
| T-R07 | static scan | ไม่พบ `date.today`, `datetime.now`, `datetime.today`, `current_date`, `now()` ใน `src/metrics.py`, `sql/10_staging/`, `sql/20_metrics/`, `dashboard/`; ใช้ allow-list ชัดเจนเฉพาะเวลา metadata (`started_at`, `completed_at`, `loaded_at`, `created_at`) |
| T-R08 | `sample` ที่ `REFERENCE_DATE` = `2026-10-02` | **informational (ตรวจโดยรันแล้ว):** overdue = 3,531; max `days_overdue` = 46; total 14,013; completed 8,597; open 5,416; open_not_overdue = 1,885; owners_with_overdue = 96 — ถ้า `REFERENCE_DATE` เปลี่ยน ให้คำนวณใหม่ด้วยตัวคำนวณอิสระ (T-F01) ไม่ใช่แก้ค่าด้วยมือ ค่าเดิมที่ `2026-10-01` (3,145 / 45) ถูกแทนที่ — บันทึกที่ ANALYTICS_CHANGELOG ไม่ใช่ expectation ของ test |
| T-R09 | parametrize reference date: `2026-07-01`, `2026-09-14`, `2026-09-15`, `2027-01-01` (+ sample CSV ที่ `2026-09-15`) | ผลทุกค่า = ตัวคำนวณอิสระ (T-F01) (fixture: overdue 0 / 4 / 5 / 8 ตามลำดับ); เหตุผล: ทุกค่าต่างจากทั้ง `REFERENCE_DATE` (2026-10-02) และวันของระบบตอนเขียน จึงจับ bug `date.today()` ที่ test ซึ่งรันที่ `REFERENCE_DATE` มองไม่เห็นขณะระบบยังเป็น 2026-10-02 (ห้ามใช้ 2026-10-02 เป็นค่าเดียวใน parametrize) |
| T-R10 | guard ค่าคงที่ | `REFERENCE_DATE` ใน `tests/conftest.py` = `2026-10-02` และ run ที่ ingest sample เก็บ `ingestion_runs.reference_date` = ค่านี้; ผลตรง T-R08; เมื่อจะเปลี่ยนค่า ต้องมี entry ใน ANALYTICS_CHANGELOG (breaking สำหรับ MET-04/MET-05) และคำนวณค่า informational ใหม่ด้วย T-F01 |

### Cross-system reconciliation และ row-level

- (ใน `tests/test_reconciliation.py`, marker `sample`) Source system = CSV: ตัวคำนวณอิสระ (Python `csv` + นิยามใน METRIC_SPEC) อ่านไฟล์ **โดยตรง** แล้วเทียบกับ DuckDB (T-X01)
- **Row-level ต้องใช้เมื่อ:** golden fixture (เทียบทุกแถว: `action_id -> is_completed, is_open, is_overdue, days_overdue`) และ sample CSV (T-X02: เทียบ checksum ของชุด (`action_id`, flags, `days_overdue`) เรียงตาม `action_id` — ทุกแถว ไม่ใช้ sampling) เพราะ error สองด้านที่หักล้างกันทำให้ยอดรวมตรงได้ ความคลาดเคลื่อนที่ยอมรับได้ = **0** สำหรับค่านับ/วัน (ผลเป็นการคำนวณแบบกำหนดแน่นอน ไม่ใช่การประมาณ)
- Backfill: T-I09

## Dashboard Acceptance Tests (`tests/test_dashboard_app.py`, `tests/test_dashboard_components.py`)

เขียนตาม plan.md §17 และหน้าที่นิยามใน DASHBOARD_SPEC.md (`DASH-01` Portfolio Overview, `DASH-02` Overdue Actions, `DASH-03` Executive Summary [bonus]; chart ID `CH-xx` อ้างจากเอกสารนั้น) วิธีทดสอบจริง: `create_app(db_path, provider)` ตัวจริงกับ DuckDB ใน `tmp_path` ผ่าน **Flask test client** (เรียก layout และ callback ผ่าน HTTP) + unit test ของ component/figure ใน `test_dashboard_components.py`; ไม่มี browser e2e (`dash.testing`) และ test ไม่ตรวจการแสดงผลด้วยตา (dark theme / colorblind / AG Grid ยังไม่ได้ตรวจด้วยตา — headless Chrome screenshot ถ่ายครั้งเดียว) เส้นทาง: `/` Portfolio Overview, `/overdue` Overdue Actions, `/executive-summary` (หน้าทั้งสามอยู่ใน `dashboard/app.py` ใน layout เดียว สลับด้วย `dcc.Location` + callback `show_page`)

| Test ID | ประเภท | Assertion |
|---|---|---|
| T-D01 | start | app สร้างได้ ไม่ throw |
| T-D02 | filter | ตัวเลือก project = `All Projects` + `DISTINCT project_name` ของ latest successful run (golden: 3 projects) |
| T-D03 | number match | KPI cards (`Total Actions`, `Completed`, `Open`, `Overdue`, `Completion Rate` (CH-05), `Owners with Overdue Actions` (CH-14 = MET-07), `Open (not overdue)` (CH-09 = MET-08)) ตอน All Projects = ผล Q-PORTFOLIO (ไม่นับแถวของ Q-BY-OWNER ใน UI) |
| T-D04 | filter (D3) | เลือก project (ส่ง `project_name` ให้ทุก Q-*) -> cards, chart data, project table (CH-11 เหลือ 1 แถว) และ overdue table **ถูกจำกัดแถว** (ไม่ใช่ highlight) สอดคล้องกัน และตรง Q-PORTFOLIO / Q-BY-PROJECT / Q-OVERDUE-DETAIL / Q-BY-OWNER ที่ filter เดียวกัน (golden: `P02 - Beta` -> total 4, overdue 1, overdue table = [B002]); เลือก `All Projects` -> `project_name = NULL`; `reference_date` ที่แสดงยังเป็นของ run ไม่เปลี่ยนตาม filter |
| T-D05 | table | overdue table มีคอลัมน์ Project, Action, Owner, Due Date, Days Overdue, Status; เรียงเริ่มต้น `Days Overdue DESC`; จำนวนแถว = overdue_actions |
| T-D06 | chart render | figure ของทุก chart สร้างได้ด้วยข้อมูล golden; chart type ต้องตรง VIZ_DESIGN_SPEC.md (chart_type_matrix) |
| T-D07 | no-data | project ไม่มีข้อมูล และ DB ยังไม่มี run สำเร็จ -> แสดงสถานะว่าง ไม่ crash (`completion_rate` 0 ต้องไม่ถูกแสดงเป็น 0% จริง) |
| T-D08 | provenance | header แสดง reference date, source file, loaded timestamp ของ latest run (provenance header ยังแสดง; แผง DQ/CH-12 ถูกถอดออกจากหน้าแล้ว ไม่ต้องทดสอบว่าแสดง) |
| T-D09 | naming | label ตรงตาราง "Label บน dashboard" ใน BUSINESS_GLOSSARY.md |
| T-D10 | read-only (CON-07) | โค้ดใน `dashboard/` ไม่มี `INSERT/UPDATE/DELETE` ต่อข้อมูล action; ไม่มี control แก้ owner/due_date/status ยกเว้นการเขียน `executive_summaries` ของ PL-02 |
| T-D11 | no hidden logic (CON-08) | สแกน `dashboard/` ไม่มีสูตร metric (`date_diff`, การเทียบ `due_date <`, `status != 'done'`) |

### AI Executive Summary (bonus; จริงอยู่ใน `tests/test_ai_provider.py`, `test_ai_summary_service.py`, `test_ai_context_builder.py`, `test_ai_prompt_hardening.py` และส่วน exec ของ `test_dashboard_app.py` — ใช้ mocked HTTP เท่านั้น **ไม่มี test ใดเรียก OpenRouter จริง (ไม่มี network ใน pytest)** — การเรียกจริงทำด้วยมือ 2 ครั้งเมื่อ 2026-10-02 ผ่าน callback Generate ของแอป ไม่ใช่ส่วนของ test suite; env ที่เกี่ยวข้อง = `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `AI_TIMEOUT_SECONDS`, `AI_TOP_N`; test ใช้ค่า dummy ผ่าน monkeypatch)

| Test ID | Assertion |
|---|---|
| T-A01 | generate (mock ตอบ 200) -> แถวใน `executive_summaries` มี `source_run_id`, `reference_date`, `provider='openrouter'`, `model_name='anthropic/claude-sonnet-5'`, `prompt_version`, `created_at`; ข้อความติด label draft; request ที่ส่งเป็น chat-completions ไปยัง `OPENAI_BASE_URL` ด้วย model slug นี้ |
| T-A02 | mock คืน HTTP error (401/403/404/429/5xx) หรือ timeout/connection error -> ไม่ insert แถวใหม่; มีข้อความอ่านเข้าใจได้ (ไม่มี stack trace/ค่า key); ไม่มี fake summary; ไม่ crash; dashboard core ยังทำงาน (parametrize ต่อ status code) |
| T-A03 | ไม่มี `OPENAI_API_KEY` หรือไม่มี `OPENAI_BASE_URL` (ทีละตัวและทั้งคู่) -> ปุ่ม Generate Draft disabled + ข้อความตั้งค่า; ไม่มี HTTP call; ไม่ crash; core dashboard ไม่กระทบ (AI-05) |
| T-A04 | context ที่ส่งใน request (ตรวจจาก mock) มาจาก DuckDB (ตรง Q-*): มี aggregates และ `top_overdue_actions` (ฟิลด์ `action_id, project_name, action_name, owner, due_date, days_overdue`; จำนวนไม่เกิน N) **รวม `owner`**; ไม่มี raw CSV/ตารางเต็ม และไม่มี API key; prompt มีคำสั่งห้าม invent risk/severity/impact/SLA และ clause ว่าค่าใน context เป็น untrusted data (GR-08; prompt `exec-summary-v2`, 5 ส่วน) (รายละเอียดที่ AI_MODEL_SPEC.md); field ข้อความอิสระ (`action_name`, `owner`, `project_name`) ถูกตัด control character และจำกัด 200 ตัวอักษร; `AI_TOP_N` default 10 (`test_ai_context_builder.py`, `test_ai_prompt_hardening.py`); `summary_id` ไม่ซ้ำเมื่อบันทึกซ้ำ (sequence `seq_summary_id`) |
| T-A05 | ไม่พบค่า `OPENAI_API_KEY` (ใช้ sentinel dummy) ในตาราง/แถวที่บันทึก/log output (caplog)/ไฟล์ใน repo; `.env` ไม่ถูก track; `.env.example` มี placeholder ว่างเท่านั้น (CON-21) |

## Test Automation and CI

| หัวข้อ | การตัดสิน |
|---|---|
| CI tool | `null` — plan.md ไม่ระบุ CI service (owner `{{DATA_STEWARD}}`); จนกว่ามี ใช้ `pytest` ในเครื่องเป็น gate ตาม Definition of Done (plan.md §27) |
| CI trigger (เมื่อมี) | ทุก push / pull request; ไม่มี test แบบ scheduled (ไม่มี pipeline ตามเวลา — PIPELINE_SPEC) |
| Deployment gate | test ใดใน marker `unit`, `integration` ล้ม = **block** (ไม่ merge/ไม่ส่งมอบ); `sample` ล้ม = block; `e2e` = ไม่ block เมื่อเปิดใช้แบบ optional (ตัดสินร่วมกับ owner) ; T-R10 (guard `REFERENCE_DATE`) เป็น gate |
| Test results reporting | ผล `pytest` (terminal / CI log); ช่องทางแจ้ง Slack/email = `null` (owner `{{DATA_STEWARD}}`) |
| Environment promotion | **ไม่มี dev/staging/production ที่นิยาม** — tier ที่ใช้: (1) test = DuckDB ชั่วคราว + golden/synthetic fixture; (2) local = sample CSV จริงของโปรเจกต์; production = `null` (ยังไม่มี; owner `{{PROJECT_SPONSOR}}`) การเปลี่ยน SQL/นิยาม metric ต้องผ่านทั้ง (1) และ (2) ก่อนใช้กับ DB ที่คนใช้อยู่ |
| Coverage expectation | **traceability 100%:** ทุก DQ rule (DQ-01..DQ-12, RI-01..RI-05) ทุก metric (MET-01..MET-08) และทุกตารางใน DATA_MODEL_SPEC มี test อย่างน้อยหนึ่งรายการ — เหตุผล: เกณฑ์ของ DDD และ plan §17/§25 (ตรวจตามตารางด้านล่าง) ส่วน **line/branch coverage เป็นเปอร์เซ็นต์ = `null`** (ไม่ได้วัด; owner `{{DATA_STEWARD}}`) ตาราง traceability ด้านล่างเป็น **แผนที่ตั้งใจ** — ยังไม่ได้ตรวจอัตโนมัติว่าทุก ID มี test จริง (รายการที่ปิดช่องว่างล่าสุด: T-S06/S09/S10/V15/I10/R10/X02 — ตรวจ `grep` ใน `tests/` ก่อนอ้างว่าครบ) |

### Coverage matrix

| รายการ | Test IDs |
|---|---|
| DQ-01 | T-V01, T-V02, T-V15 |
| DQ-02..DQ-08 | T-V03..T-V09, T-V13, T-V14 |
| DQ-09 | T-V10 |
| DQ-10 | T-V11, T-V12, T-I08 |
| ขนาดไฟล์/basename/exit code ของ ingest | `test_hardening_ingest.py` (ดูหัวข้อ Integration) |
| RI-01..RI-05 | T-S04, T-S05, T-S07, T-S09 |
| MET-01..MET-04 | T-M01..T-M04, T-M06, T-M10..T-M12, T-R01..T-R06 |
| MET-05 | T-M05, T-M08, T-R01, T-R06 |
| MET-06 | T-M07, T-M15 |
| MET-07 | T-M10, T-M11, T-M13, T-D03, T-R08 |
| MET-08 | T-M10, T-M11, T-M14, T-D03, T-R08 |
| `raw_actions` | T-V*, T-S05, T-I01 |
| `stg_actions` | T-S01..T-S05, T-M*, T-R* |
| `ingestion_runs` | T-S06, T-I01..T-I07 |
| `data_quality_results` | T-V14, T-S07 |
| `executive_summaries` | T-S09, T-A01..T-A05 |
| `app_config` | T-S08, T-S10 |
| DQ-01 (duplicate header), DQ-11, DQ-12 | T-V17, T-V18, T-V19, T-V15 |
| กฎ reference date (CON-06) | T-R07, T-R09, T-I03 |
| Idempotency (NFR-04) | T-I05..T-I07 |

## Open Questions

1. ~~`ASSIGNMENT_REFERENCE_DATE`~~ — **ตัดสินแล้ว (D1):** `REFERENCE_DATE = 2026-10-02` ค่าคงที่ iteration 1 (T-R08, T-I02, T-R10 อ้างค่านี้)
2. ~~พฤติกรรมของไฟล์ header-only~~ — **ตัดสินแล้ว:** exit 2 ก่อนเขียน DB (ไม่มี run; run ว่างจะไม่กลายเป็น latest successful run) มี test
3. เลือก CI service และช่องทางรายงานผล (`{{DATA_STEWARD}}`)
4. `e2e` browser test: ยังไม่มี — ตัดสินว่าจะเพิ่มหรือไม่ (ถ้าเพิ่ม ต้องตัดสินว่าเป็น gate หรือ optional)
