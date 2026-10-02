# Constraints

```yaml
doc_id: constraints
filename: CONSTRAINTS.md
version: 1.0.0
status: draft
depends_on: []
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

เอกสารนี้ระบุข้อจำกัดที่ต้องเป็นจริง **ก่อน launch** ทุกข้อต้องตรวจสอบได้ (ค่าตัวเลข, มาตรฐานที่ระบุชื่อ หรือ yes/no) ค่าใดที่ยังไม่ผ่านการ calibrate = `null` พร้อม calibration owner ไม่มีการเดาค่า เนื้อหา retention / access control / ceiling ค่าใช้จ่ายรายเดือนเป็นของ DATA_GOVERNANCE ไม่ซ้ำที่นี่

## Platform & Tooling Constraints

| ID | Constraint | ค่า / เงื่อนไขที่ตรวจสอบได้ | แหล่งที่มา |
|---|---|---|---|
| CON-01 | Mandatory Warehouse | DuckDB, ไฟล์ `data/cybersecurity.duckdb`; version pin = `null` (calibration source: `pyproject.toml` ที่จะสร้างใน Phase 1; owner: `{{DATA_STEWARD}}`) | plan.md §0, §3 |
| CON-02 | BI Tool & Licensing | Plotly Dash + Dash AG Grid + Plotly charts; seat limit: ไม่มี named-seat licensing ที่ทราบ `[ASSUMPTION — ยืนยันว่าใช้ community/open-source tier]`; Altair เพิ่มได้เมื่อใช้จริงเท่านั้น | plan.md §0 |
| CON-03 | Transform Tool | SQL files ใต้ `sql/` รันโดย `src/ingest.py` (ไม่ใช้ dbt); version pin ของ Python = `null` (owner: `{{DATA_STEWARD}}`) | plan.md §0, §8 |
| CON-04 | Required Connectors | ไม่มี connector ภายนอก; รับ CSV UTF-8 ผ่าน CLI (`--input`) เป็นช่องทางหลักที่ต้องทำงานเสมอ; upload ผ่าน Dash เป็น bonus | plan.md FR-01 |
| CON-05 | Test Tool | pytest | plan.md §0 |
| CON-06 | Single Reference Date | metric logic ห้ามเรียก `date.today()` / `datetime.now().date()`; ใช้ `REFERENCE_DATE` ค่าเดียวผ่าน `--reference-date` เก็บต่อ run; ค่าปัจจุบัน `2026-10-02` = fixed constant for iteration 1; เปลี่ยนผ่าน ANALYTICS_CHANGELOG เท่านั้น (breaking สำหรับ MET-04/MET-05) | plan.md §2 |
| CON-07 | Read-only Analytics (MVP) | dashboard ไม่แก้ owner / due_date / status; yes/no ตรวจได้ที่ smoke test | plan.md NFR-02 |
| CON-08 | No Hidden Metric Logic | สูตร metric อยู่ใน SQL/data access layer เท่านั้น ไม่เขียนซ้ำใน Dash callbacks | plan.md NFR-03 |
| CON-09 | Do-Not-Build | ห้ามสร้าง risk score, health score, severity score, owner performance score, SLA compliance, on-time rate, cycle time, forecast, AI risk rating (source ไม่มีข้อมูล) | plan.md §21 |
| CON-10 | Single DDD track | ใช้ `ddd-data-analytics` v2.8.0 เท่านั้น ห้ามเพิ่ม track อื่นแม้ทำ bonus AI | plan.md §0 |

## Scale Constraints

**GIST:** threshold ทุกค่าในเอกสารอื่นต้องกำหนดขนาดจากตัวเลขในหัวข้อนี้ ไม่ใช่ปริมาณวันนี้

| ID | Constraint | ค่า |
|---|---|---|
| CON-11 | ปริมาณปัจจุบันของ fact table ที่โตเร็วที่สุด (`raw_actions` / `stg_actions`) | 14,013 แถวต่อ run ใน sample (12 projects, 96 owners) — ค่าที่สังเกตได้ ไม่ใช่ projection |
| CON-12 | Projected rows ที่ 1 ปี | `null` — calibration source: จำนวน action ต่อสัปดาห์และจำนวนรอบ ingest ที่เก็บไว้ (run versioning ทำให้แถวสะสมต่อ run); owner: `{{PROJECT_SPONSOR}}` |
| CON-13 | Projected rows ที่ 3 ปี | `null` — source/owner เดียวกับ CON-12 |
| CON-14 | Source API rate limits | ไม่มี (แหล่งข้อมูลเป็นไฟล์ CSV ไม่ใช่ API) — N/A |
| CON-15 | Warehouse concurrency / connection quotas | DuckDB เป็น embedded; ข้อจำกัดเชิงเทคโนโลยี: ผู้เขียน (ingest) หนึ่ง process ต่อไฟล์ DB — ต้องไม่รัน ingest พร้อมกันหลายตัว; ค่า concurrent reader ที่รองรับ = `null` (calibration: load test, owner `{{DATA_STEWARD}}`) |
| CON-16 | จำนวนผู้ใช้พร้อมกัน (concurrent dashboard users) | `null` (calibration source: จำนวน STK-01..06 จริง; owner `{{PROJECT_SPONSOR}}`) |

## Compliance & Residency Constraints

อ้างอิงกรอบ **PDPA (ประเทศไทย)** — ไม่ใช่ GDPR

| ID | Constraint | ค่า |
|---|---|---|
| CON-17 | Data Residency | `null` — ภูมิภาค/ประเทศที่ข้อมูลต้องอยู่ ยังไม่ได้ระบุ; owner: `{{DPO_OR_LEGAL}}`. หมายเหตุเชิงข้อเท็จจริง: DuckDB อยู่ในเครื่อง/ไฟล์ที่ deploy; หากเปิดใช้ AI provider ภายนอก (bonus) context ที่ส่งออกอาจข้ามพรมแดน -> ต้องตัดสินก่อนเปิดใช้ |
| CON-18 | Legal Basis for Collection (PDPA) | `null` ต่อประเภทข้อมูล — ข้อมูลที่ ingest: `owner` (pseudonymous `Owner-NNN`; ไม่ทราบว่ามี mapping กับบุคคลจริงหรือไม่), `action_name` (ข้อความไทยอิสระ มี branch tag `/ สาขา BR-nnn`; ต้องจัดประเภทว่าเป็น personal data หรือไม่); owner: `{{DPO_OR_LEGAL}}`; การจัดประเภทเป็นของ DATA_MODEL_SPEC (`pdpa_classification`) |
| CON-19 | Industry Standards | `null` — ไม่มีมาตรฐาน (เช่น ISO 27001) ที่ระบุว่าบังคับ; owner: `{{DPO_OR_LEGAL}}` |
| CON-20 | Scope Boundary | retention, access control, การลบข้อมูลตามคำขอ PDPA = DATA_GOVERNANCE |
| CON-21 | AI Provider Credential | API key ห้าม commit และห้ามเก็บใน DB; ใช้ env `OPENAI_API_KEY` (secret) และ `OPENAI_BASE_URL` เท่านั้น (model slug เป็นค่าคงที่ ไม่ใช่ secret) (ตรวจได้: ไม่มีค่าใน repo / ตาราง `executive_summaries` / log) |

## Project Budget & Timeline

| ID | Constraint | ค่า |
|---|---|---|
| CON-22 | Delivery Budget Ceiling (ครั้งเดียว) | `null` — ไม่มีงบระบุใน plan; calibration source: ข้อตกลงของ `{{PROJECT_SPONSOR}}`; owner: `{{PROJECT_SPONSOR}}` |
| CON-23 | Go-Live Date | `null` — ไม่มีวันที่ระบุ; owner: `{{PROJECT_SPONSOR}}` |
| CON-24 | Phased Rollout | ลำดับตาม plan.md §28 (ไม่ใช่ commitment ด้านวันที่): (1) core metrics + validation + DuckDB ingest, (2) Dash Overview + project filter (พารามิเตอร์ `project_name` ของทุก query) + Overdue Detail, (3) data quality display + hardening + README, (4) bonus AI Executive Summary; core ต้องผ่านก่อนเริ่ม AI |
| CON-25 | Pending central requirement | รายการเอกสาร DDD ขั้นต่ำตาม "เงื่อนไขกลาง" = unknown; ห้ามเดา (plan.md §18, §29) |

## Integration Constraints

| ID | Source | Contract Stability | API Compatibility |
|---|---|---|---|
| CON-26 | Weekly Action Item CSV (`src/tee_cybersecurity_actions_mock.csv`) — required for launch | `unversioned` — schema ยืนยันจาก sample เท่านั้น: `action_id, project_name, action_name, owner, due_date, status`; ไม่มี producer-side version; รายละเอียดสัญญา = DATA_CONTRACT.md | CSV UTF-8, `due_date` ISO `YYYY-MM-DD`; ไม่มี API |
| CON-27 | AI provider (bonus เท่านั้น) | ผู้ใช้ตัดสินใจแล้ว (iteration 1): provider = OpenRouter (OpenAI-compatible HTTP API), model = `anthropic/claude-sonnet-5` (ค่าคงที่ในโค้ด/config ไม่ใช่ secret). งบประมาณ/เพดานค่า API = `null` (owner `{{PROJECT_SPONSOR}}`). การส่ง context ผ่านห่วงโซ่ OpenRouter -> Anthropic ยังเป็นรายการเปิดด้าน PDPA/data residency ของ `{{DPO_OR_LEGAL}}` (CON-17, GOV-AI-01) — ไม่มีการอนุมัติ | abstraction `ExecutiveSummaryProvider.generate(context: dict) -> str`; เรียก chat-completions ตรงผ่าน HTTPS (ไลบรารี httpx หรือ openai SDK = รายละเอียด implementation ที่ยังเปิด); config ผ่าน env `OPENAI_API_KEY` / `OPENAI_BASE_URL` |

ข้อสังเกต: ไม่มี timestamp จาก source — เวลาโหลดมาจากระบบ ingest เท่านั้น (`started_at`/`loaded_at`)

## Open Questions

1. `REFERENCE_DATE` = 2026-10-02 ยืนยันแล้วสำหรับ iteration 1; ถ้าโจทย์ประกาศค่าอื่น ต้องเปลี่ยนผ่าน ANALYTICS_CHANGELOG
2. Budget, go-live, residency, legal basis, ปริมาณโตรายปี (CON-12/13/17/18/22/23)
3. การส่ง context ออกนอกองค์กรผ่าน OpenRouter -> Anthropic (PDPA classification ของ `owner`/`action_name`, data residency, DPA) — `{{DPO_OR_LEGAL}}`; งบ/เพดานค่า API — `{{PROJECT_SPONSOR}}`
