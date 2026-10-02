# Agent and Coding Rules

```yaml
doc_id: agents_md
filename: AGENTS.md
aliases: [CLAUDE.md]
version: 1.0.0
status: draft
depends_on: [pipeline_spec, data_governance, constraints, data_model_spec]
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

ไฟล์นี้โหลดเป็น standing context ทุก task `CLAUDE.md` = alias ของไฟล์นี้ (เนื้อหาเดียวกัน แก้ที่ `AGENTS.md` ที่เดียว) ไม่ซ้ำนิยามจากเอกสารอื่น — อ้างด้วย ID

## Project Overview

- **System Name:** Cybersecurity Project Action Dashboard
- **Purpose:** ตอบว่าแต่ละโครงการมี action item ทั้งหมด/เสร็จ/ค้าง/เลยกำหนดเท่าไร และ item ที่เลยกำหนดเป็นของใครกี่วัน (MET-01..MET-06 และ draft MET-07/MET-08 ใน METRIC_SPEC.md) จาก CSV รายสัปดาห์หลังประชุม
- **Stack Summary:** DuckDB (warehouse) + Plotly Dash/Dash AG Grid (BI) + SQL files ใต้ `sql/` รันโดย `src/ingest.py` (transform) + pytest
- **Onboarding Pointer:** quick start, การติดตั้ง และ document map อยู่ใน [README.md](README.md) (Doc Index ครบทั้ง 23 ฉบับ — ไฟล์ทุกฉบับมีแล้ว สถานะ `draft`) อ่านก่อนแก้ pipeline ครั้งแรก
- **สถานะ (2026-10-02):** `src/ingest.py`, `src/validation.py`, `src/metrics.py`, `src/ai/`, `sql/`, `dashboard/app.py` implement แล้วและมี pytest (ดู TESTING_STRATEGY) — ยังคงห้ามรายงานว่า "ผ่าน/ทำแล้ว" ถ้ายังไม่ได้รันจริง และห้ามอ้างว่าเรียก OpenRouter จริงแล้ว (ทดสอบด้วย mocked HTTP เท่านั้น) หรือตรวจ dark theme/colorblind/AG Grid ด้วยตาแล้ว (ยังไม่ได้ตรวจ)

## Tech Stack

ตรึงตาม CONSTRAINTS.md (agent ห้ามเปลี่ยน/เพิ่มเครื่องมือเอง ต้องมี change ที่ owner อนุมัติ)

| ชั้น | ค่า | อ้างอิง |
|---|---|---|
| Warehouse | DuckDB `data/cybersecurity.duckdb`; version = `null` (pin ใน `pyproject.toml`; owner `{{DATA_STEWARD}}`) | CON-01 |
| Transform | SQL ใต้ `sql/` รันโดย `src/ingest.py` — ไม่ใช้ dbt; Python version = `null` | CON-03 |
| BI | Plotly Dash + Dash AG Grid + Plotly charts (`dashboard/app.py`); เพิ่ม Altair เมื่อใช้จริงเท่านั้น; version = `null` | CON-02 |
| Test | pytest | CON-05 |

## Query & Modeling Conventions

- **SQL Style:** `snake_case`; ไฟล์ตามเลเยอร์ `sql/00_schema`, `10_staging`, `20_metrics`, `30_quality`; หนึ่ง metric ต่อหนึ่ง query/CTE ชื่อ query ตาม `Q-*` ใน METRIC_LOGIC.md; ใช้ ISO `YYYY-MM-DD` และ parameter (`run_id`, `reference_date`) ไม่ใช้ string concat
- **Metric Ownership Rule:** สูตรจริงอยู่ที่ METRIC_LOGIC.md (นิยามธุรกิจ = METRIC_SPEC.md) เท่านั้น; SQL metric อยู่ใน `sql/` / data-access layer เท่านั้น (CON-08); dashboard/model ที่คำนวณซ้ำเองคือข้อบกพร่อง
- **Reference Date:** ใช้ `reference_date` ที่ส่งผ่าน `--reference-date` และเก็บต่อ run (CON-06); iteration 1 = `2026-10-02` (ค่าคงที่ที่ผู้ใช้ยืนยัน; ไม่ใช่ `date.today()`) เปลี่ยนได้ผ่าน ANALYTICS_CHANGELOG.md เท่านั้น (breaking สำหรับ MET-04/MET-05); ค่าเดิม 2026-10-01 ถูก supersede ห้ามใช้; test fixture ใช้ `2026-09-15` (ต่างจาก REFERENCE_DATE โดยตั้งใจเพื่อจับ `date.today()` ที่ซ่อนอยู่) — ห้ามอ่านจาก `--reference-date` ใน test แทน fixture date
- **Project Filter:** ทุก `Q-*` รับ parameter `project_name` (NULL / 'All Projects' = ทุกโครงการ) และ restrict แถวจริง ไม่ใช่ highlight; reference date อ่านจาก `reference_date` ที่เก็บของ run ไม่ใช่จาก filter
- **Run versioning:** query ทุกตัวกรองด้วย latest successful `run_id` (ดู PIPELINE_SPEC.md)
- **Comment Language:** comment ใน SQL/Python เป็นภาษาอังกฤษ; เอกสาร/narrative เป็นภาษาไทย; identifier เป็นอังกฤษ

## Forbidden Patterns

| # | ห้าม | ให้ทำแทน |
|---|---|---|
| F1 | เรียก `date.today()` / `datetime.now()` / `current_date` ใน metric logic | รับ `reference_date` จาก `--reference-date` แล้วส่งเป็น parameter (CON-06) |
| F2 | นิยามหรือคัดลอกสูตร metric นอก METRIC_SPEC.md / METRIC_LOGIC.md หรือคำนวณซ้ำใน Dash callback/BI | เรียก query `Q-*` ที่ data-access layer และอ้าง `MET-*` |
| F3 | Hardcode threshold/ค่า calibrate (quality bound, freshness, retention, ceiling) หรือ **คิด KPI/threshold/severity ใหม่** | ปล่อย `null` พร้อมระบุ calibration source + owner role; severity ใช้เฉพาะ enum `rule_severity` (DATA_QUALITY.md) |
| F4 | ปล่อย column ข้อมูลส่วนบุคคลโดยไม่จัดชั้น หรือเพิ่ม column ใหม่ที่อาจมี PII | กำหนด `pdpa_classification` ใน DATA_MODEL_SPEC.md ก่อน merge (ค่า enum ดูที่นั่น) |
| F5 | ship pipeline/ตารางที่ไม่มี DATA_QUALITY.md check | เพิ่ม null-rate + range check อย่างน้อย (DQ-*/RI-*) พร้อม test |
| F6 | Commit credential, เก็บ `OPENAI_API_KEY` ใน DB (`executive_summaries`, `app_config`) หรือพิมพ์ลง log/commit; เรียก AI ผ่าน `aix` CLI/subprocess | อ่านจาก env `OPENAI_API_KEY` + `OPENAI_BASE_URL` (OpenRouter, model `anthropic/claude-sonnet-5` เป็น constant ในโค้ด ไม่ใช่ secret); เรียก chat-completions ตรงผ่าน HTTPS จาก Python (ไม่ใช้ `aix`); `.env` ไม่ commit; `.env.example` ใส่ placeholder ว่าง (CON-21) |
| F7 | Redeclare ค่า enum นอกเอกสารเจ้าของ | อ้างชื่อ enum; index ที่ BUSINESS_GLOSSARY.md Enumeration Registry |
| F8 | เปิด DuckDB เขียนพร้อมกันหลาย process (single-writer, CON-15) | รัน ingest ครั้งละหนึ่ง process; dashboard เปิด `read_only=True`; ถ้า DB ถูกล็อก ให้รันซ้ำหลัง process อื่นปิด ห้าม retry วนเอง |
| F9 | สร้าง metric/ฟีเจอร์ใน Do-Not-Build (plan.md §21, CON-09): risk/health/severity score, owner performance score, SLA compliance, on-time completion rate, average completion time, cycle time, forecast completion date, AI-generated risk rating | แสดงเฉพาะ MET-01..MET-08 (MET-07/MET-08 = draft, นับเท่านั้น ไม่มี threshold); ถ้าต้องการเพิ่ม ให้เสนอผ่าน KPI_DICTIONARY.md/METRIC_SPEC.md + ANALYTICS_CHANGELOG.md ให้ owner อนุมัติ |
| F10 | ให้ AI summary invent severity/impact/SLA หรือส่ง raw CSV/ตารางเต็ม/API key ออก provider | ส่งเฉพาะ aggregate + top-N overdue rows (`action_id`, `project_name`, `action_name`, `owner`, `due_date`, `days_overdue`; N = `null` ตั้งใน config); `owner` (Owner-NNN) ส่งได้ตามการตัดสินใจของผู้ใช้ iteration 1 — PDPA classification (GOV-OPEN-01) และ data residency ยัง open ที่ `{{DPO_OR_LEGAL}}` ห้ามอ้างว่าอนุมัติแล้ว; บันทึกลง `executive_summaries` |
| F11 | แก้ไฟล์ input, `silently drop` แถว หรือแก้ `owner`/`due_date`/`status` จาก dashboard (CON-07) | รายงาน finding ลง `data_quality_results`; `blocking` = ปฏิเสธทั้งไฟล์ |

## Doc Ownership & Change Rules

- **แก้ได้เอง:** โค้ดภายใต้ `src/`, `sql/`, `dashboard/`, `tests/` ตามสเปก; เอกสารเฉพาะที่ task ระบุ
- **ต้องมี owner อนุมัติ:** เปลี่ยน stack/version, นิยาม metric, enum, ตารางสคีมา, `REFERENCE_DATE`, การจัดชั้น PDPA — การเปลี่ยนนิยาม metric = breaking change ต้องมี entry ใน ANALYTICS_CHANGELOG.md พร้อม effective date
- **เจ้าของเอกสาร:** แก้นิยามที่เอกสาร canonical เท่านั้น (metric = METRIC_SPEC/LOGIC, quality = DATA_QUALITY, schema/enum = DATA_MODEL_SPEC); เอกสารอื่นอ้างด้วย ID ห้ามสำเนา; Glossary เป็น naming authority
- ห้ามแก้ `ddd/` spec และห้ามเพิ่ม DDD track อื่น (CON-10)

## Data Quality & Testing Rules

- **Coverage Rule:** traceability 100% — ทุก DQ-01..DQ-12, RI-01..RI-05, MET-01..MET-08 และทุกตารางมี test อย่างน้อยหนึ่งรายการ; line/branch % = `null` (owner `{{DATA_STEWARD}}`) ดู TESTING_STRATEGY.md
- **Quality Gate:** rule ระดับ `blocking` ตัวใด fail = run `failed`, deploy/merge ถูกบล็อก; CI tool = `null` จนกว่าเลือก — ระหว่างนี้ `pytest` ในเครื่องเป็น gate
- **Metric Validation:** metric ใหม่/ที่เปลี่ยนต้องผ่าน golden-dataset cross-check (`tests/fixtures/actions_small.csv`, T-M*; fixture date `2026-09-15`) ก่อน merge; ตัวเลขจาก sample (14,013 แถว ฯลฯ) ห้าม hardcode ใน dashboard/test เป็นค่าคาดหวังถาวร
- **คำสั่ง:** `python -m src.ingest --input <csv> --reference-date <YYYY-MM-DD>` · `pytest` · `python dashboard/app.py`

## PDPA Rules

กรอบ: PDPA (ประเทศไทย) ไม่ใช่ GDPR; การจัดชั้นเป็น provisional จนกว่า `{{DPO_OR_LEGAL}}` ตัดสิน (GOV-OPEN-01) — ใช้ Path A (ถือเป็น personal data) เป็น default

- **Named PII Columns:** `owner` (`raw_actions`, `stg_actions`) = `confidential`; `action_name` (`raw_actions`, `stg_actions`) = `confidential`; `summary_text` (`executive_summaries`) = `confidential`; `record_key`, `message` (`data_quality_results`) = `confidential` — ห้ามใส่ค่าเหล่านี้ลง log/error message/commit/ตัวอย่างโดยไม่จำเป็น
- **Erasure Path:** คำขอลบต้องไปถึง `stg_actions`/`raw_actions` ทุก `run_id`, `data_quality_results`, `executive_summaries`, export/Dash cache, AI provider context, archive/backup และ CSV ต้นทาง ตามลำดับใน DATA_GOVERNANCE.md (Erasure Mechanics); ถ้าตัวเลขเปลี่ยนให้บันทึก ANALYTICS_CHANGELOG.md และ reconcile DQ-10
- **Test Fixture Rule:** fixture/CI ใช้ข้อมูลสังเคราะห์ (`Owner-NNN` สมมติ) เท่านั้น ห้ามคัดลอกข้อมูลจริงจาก `src/tee_cybersecurity_actions_mock.csv` ที่ไม่ได้รับอนุญาตเข้า fixture/CI
