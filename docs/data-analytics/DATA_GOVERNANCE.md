# Data Governance Spec

```yaml
doc_id: data_governance
filename: DATA_GOVERNANCE.md
version: 1.0.0
status: draft
depends_on: [data_model_spec, data_contract, kpi_dictionary]
also_references: [stakeholders, constraints, business_glossary, pipeline_spec]
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

เอกสารนี้กำหนดกรอบ governance ของ DuckDB (`data/cybersecurity.duckdb`) ภายใต้ **PDPA (ประเทศไทย)** ไม่ใช่ GDPR ค่าที่ต้อง calibrate (retention, cost ceiling, query guard rail, erasure SLA, audit retention) เป็น `null` พร้อม calibration source และ owner ไม่มีการเดาตัวเลข ผู้ถือบทบาทเป็น role placeholder `{{...}}` ไม่มีชื่อบุคคล

> **สถานะ (2026-10-02):** DB จริงมีแล้ว (สร้างโดย ingest; ไม่ commit) และมีข้อเท็จจริงด้านความปลอดภัยที่ตรวจโดยอ่านโค้ด/test (ดู AI_MODEL_SPEC "Security review note"; audit `ai_context_send` เป็น log เท่านั้น ยังไม่ persist) แต่ยังไม่มีผู้ถือบทบาทที่ได้รับการแต่งตั้ง — ทุกบทบาทด้านล่างเป็น `[ASSUMPTION]` / `[DESIGN PROPOSAL]` รอ `{{PROJECT_SPONSOR}}` ยืนยัน ข้อจำกัดทางเทคนิค: DuckDB เป็น embedded ไม่มี user/role/RLS/column-masking ในตัว (ต่างจาก warehouse แบบ server) จึงต้องบังคับสิทธิ์ที่ชั้น **ไฟล์ + data access layer** และห้ามอ้างว่ามี GRANT ระดับ role

Enum ที่ใช้: `pdpa_classification` (owner: DATA_MODEL_SPEC.md), `ingestion_run_status`, `action_status` — อ้างชื่อเท่านั้น ไม่ประกาศค่าซ้ำ เอกสารนี้ไม่เป็นเจ้าของ enum ใด

## Open Decision (ต้องเคลียร์ก่อนใช้งานจริง): การจัดประเภท `owner` / `action_name`

**GOV-OPEN-01** — การตัดสินว่า `owner` (`Owner-NNN`) และ `action_name` (ข้อความไทยอิสระ + branch tag) เป็น personal data ตาม PDPA หรือไม่ เป็นของ `{{DPO_OR_LEGAL}}` (CON-18, DATA_MODEL_SPEC §PDPA) **เอกสารนี้ไม่ตัดสิน** แต่กำหนดทางปฏิบัติแบบระมัดระวังไว้ทั้งสองทาง และตั้งค่า default ปฏิบัติตาม Path A จนกว่าจะมีคำตัดสิน (Path A ใช้กับการจัดเก็บ/export/การแสดงผล) **ข้อยกเว้นเฉพาะ AI context:** ผู้ใช้ตัดสินใจ (iteration 1) ให้ส่ง `owner` (pseudonymous `Owner-NNN`) ไปยัง AI ได้ — เป็นการตัดสินใจของผู้ใช้ ไม่ใช่การอนุมัติจาก `{{DPO_OR_LEGAL}}`; คำถาม PDPA classification ของ `owner`/`action_name` และ data residency/ผู้ประมวลผลบุคคลที่สาม (OpenRouter -> Anthropic) ยังเปิดอยู่

| | Path A — ถือเป็น personal data (default ระหว่างรอ) | Path B — ไม่ใช่ personal data (ต้องมีคำตัดสินเป็นลายลักษณ์อักษรจาก `{{DPO_OR_LEGAL}}`) |
|---|---|---|
| Classification | `confidential` (ตรงกับ provisional ใน DATA_MODEL_SPEC) | `internal` |
| Masking นอก role ที่ได้รับสิทธิ์ | ใช่ (ดู Column Masking) | ไม่บังคับ แต่ยังแนะนำให้คง pseudonym |
| Erasure / retention / audit | บังคับทั้งหมดตามหัวข้อด้านล่าง | retention ยังใช้ business justification; erasure ไม่บังคับตาม PDPA แต่ยังต้องลบได้ถ้า `{{DPO_OR_LEGAL}}` สั่ง |
| Context ที่ส่ง AI provider | ส่ง `Owner-NNN` ได้ตามการตัดสินใจของผู้ใช้ (GOV-AI-01; ยังไม่มีการอนุมัติ DPO/legal) | ขอบเขตตาม GOV-AI-01 |
| Legal basis | ต้องกำหนดโดย `{{DPO_OR_LEGAL}}` (CON-18 = `null` ปัจจุบัน) | ไม่ต้อง |

เงื่อนไขที่ต้องตรวจเพิ่ม: มี mapping `Owner-NNN` -> บุคคลจริงนอกระบบนี้หรือไม่ (ถ้ามีและผู้ใช้ข้อมูลเข้าถึงได้ ยังถือว่า re-identifiable) และ `action_name` มีชื่อบุคคลหรือไม่ (ยังไม่ได้สุ่มตรวจเนื้อหา)

## Data Ownership Matrix

Data Owner = ทีมที่รับผิดชอบ quality ของ dataset; Data Steward = ผู้ดูแลรายวัน; ทุกตำแหน่งเป็น role placeholder (`[ASSUMPTION]`, ยังไม่มีผู้ถือบทบาท)

| Gov ID | Dataset (ตารางใน DATA_MODEL_SPEC) | Data Owner (team) | Data Steward | Escalation Contact | KPI ที่พึ่งพา |
|---|---|---|---|---|---|
| GOV-OWN-01 | Weekly Action Item CSV (source, DC-01) | `{{PRODUCER_TEAMS}}` (ตาม DATA_CONTRACT) | `{{CONTRACT_OWNER}}` | `{{PROJECT_SPONSOR}}` | KPI-01..03 |
| GOV-OWN-02 | `raw_actions` | `{{ANALYTICS_TEAM}}` (STK-06) | `{{DATA_STEWARD}}` | `{{PROJECT_SPONSOR}}` | - |
| GOV-OWN-03 | `stg_actions` | `{{ANALYTICS_TEAM}}` | `{{DATA_STEWARD}}` | `{{PROJECT_SPONSOR}}` | KPI-01, KPI-02, KPI-03 |
| GOV-OWN-04 | `ingestion_runs` | `{{ANALYTICS_TEAM}}` | `{{DATA_STEWARD}}` | `{{PROJECT_SPONSOR}}` | - (เลือก latest successful run) |
| GOV-OWN-05 | `data_quality_results` | `{{ANALYTICS_TEAM}}` | `{{DATA_STEWARD}}` | `{{PROJECT_SPONSOR}}` | - |
| GOV-OWN-06 | `executive_summaries` (bonus) | `{{ANALYTICS_TEAM}}` | `{{DATA_STEWARD}}` | `{{DPO_OR_LEGAL}}` (กรณีเนื้อหา/การส่งออกข้อมูล) | - |
| GOV-OWN-07 | `app_config` | `{{ANALYTICS_TEAM}}` | `{{DATA_STEWARD}}` | `{{PROJECT_SPONSOR}}` | - |

หมายเหตุ: KPI-01..03 เป็น **candidate** (KPI_DICTIONARY — owner/target ยังไม่อนุมัติ) การเป็น Data Owner ของ `stg_actions` จึงไม่ใช่การเป็น KPI owner ผู้รับผิดชอบความถูกต้องของตัวเลข KPI = `{{KPI_OWNER_ROLE}}` ตาม KPI_DICTIONARY ไม่ซ้ำที่นี่ DQ rule และ SLA ความสด อยู่ที่ DATA_QUALITY.md / SLA_FRESHNESS.md

## Access Control Policy

**GIST (GOV-ACC-01):** access control ที่บังคับเฉพาะใน Dash คือประตูล็อกข้างเดียว — ใครเปิดไฟล์ `data/cybersecurity.duckdb` หรือ CSV ต้นทางตรง ๆ ข้ามไปได้ทั้งหมด ดังนั้นการบังคับต้องอยู่ที่ชั้นข้อมูล: (1) สิทธิ์ไฟล์ของ OS บน DuckDB + CSV + backup, (2) data access layer ที่เป็นทางเดียวที่ dashboard ใช้ (read-only connection, `read_only=True`; สอดคล้อง CON-07, CON-08), (3) Dash ทำหน้าที่ presentation เท่านั้น

### Role Definitions

Role map จาก STAKEHOLDERS.md (ไม่สร้าง persona ใหม่); ROLE-07 เป็นบัญชีระบบ ไม่ใช่คน

| Role ID | STK | Role (placeholder) | คำอธิบายสิทธิ์ |
|---|---|---|---|
| ROLE-01 | STK-01 | `{{MEETING_CHAIR}}` | ดู dashboard ระดับ portfolio ผ่าน Dash |
| ROLE-02 | STK-02 | `{{PROJECT_MANAGER}}` | ดู dashboard ทุกโครงการหรือเฉพาะโครงการของตน (ดู Row-level) |
| ROLE-03 | STK-03 | `{{SECURITY_TEAM_LEAD}}` | ดู dashboard + รายการ overdue ราย owner + Executive Summary draft (bonus) |
| ROLE-04 | STK-04 | `{{ACTION_OWNER}}` | ดู overdue ของตนเอง (ขอบเขต = `null` ดู Row-level) |
| ROLE-05 | STK-05 | `{{AUDITOR_OR_EXEC}}` | ดู dashboard + Executive Summary + ตรวจย้อนรอย `run_id`; read-only ต่อ audit |
| ROLE-06 | STK-06 | `{{DATA_STEWARD}}` | ผู้รัน `src/ingest.py`, query DuckDB ตรง, ผู้ถือสิทธิ์ ingest และ erasure |
| ROLE-07 | - | ingest/service process | เขียน `raw_actions`/`stg_actions`/`ingestion_runs`/`data_quality_results`/`executive_summaries`; ผู้เขียนเดียวต่อไฟล์ DB (CON-15) |

### Role x Dataset Matrix

ค่า: `R` = อ่านผ่านแอป (aggregate/รายการตามที่ dashboard แสดง) · `Rm` = อ่านแบบ mask ตาม Column Masking · `Rx` = query ตรงบน DuckDB · `W` = เขียน · `-` = ไม่มีสิทธิ์ · `null` = รอการตัดสิน

| Dataset | ROLE-01 | ROLE-02 | ROLE-03 | ROLE-04 | ROLE-05 | ROLE-06 | ROLE-07 |
|---|---|---|---|---|---|---|---|
| `stg_actions` | R | R | R | `null` (own-rows หรือ portfolio) | R | Rx | W |
| `raw_actions` | - | - | - | - | - | Rx | W |
| `ingestion_runs` | R (เฉพาะ run_id, reference_date ที่แสดงบน UI) | R | R | R | R | Rx | W |
| `data_quality_results` | - | - | R (สรุป) | - | R (สรุป) | Rx | W |
| `executive_summaries` | - | - | R | - | R | Rx | W |
| `app_config` | - | - | - | - | - | Rx | W |

ROLE-01..05 ไม่มีสิทธิ์ `Rx` ทุกกรณี (ไม่เปิดไฟล์ DB/CSV) ความสอดคล้องกับ DATA_CONTRACT: ไม่มี SLA ที่ยืนยัน (DC-SLA-01..04 เป็น `null`/N/A) จึงไม่มีสัญญาด้านเวลาที่ role ใดอ้างได้ — สิทธิ์ของทุก role อ่านจาก **latest successful run** เท่านั้น (STAKEHOLDERS §Freshness)

### Sensitive Data Access

ขอสิทธิ์ column ระดับ `confidential` แบบไม่ mask (เช่น `owner`, `action_name` ดิบ): (1) ผู้ขอระบุ role + เหตุผล + ระยะเวลา (2) `{{DATA_STEWARD}}` ตรวจความจำเป็น (3) `{{DPO_OR_LEGAL}}` อนุมัติ (ผู้อนุมัติจริงยังไม่ได้แต่งตั้ง) (4) บันทึกใน access request log (ดู Audit) (5) สิทธิ์หมดอายุเมื่อครบกำหนด — ระยะเวลาสูงสุด = `null` (source: `{{DPO_OR_LEGAL}}`; owner: `{{DPO_OR_LEGAL}}`)

### Row-level Security

| ประเด็น | ข้อกำหนด |
|---|---|
| ROLE-01/03/05 | เห็นทุกแถวของ latest successful run |
| ROLE-02 | ทุกโครงการ vs เฉพาะ `project_name` ของตน = `null` (STAKEHOLDERS Q2; owner `{{PROJECT_SPONSOR}}`) |
| ROLE-04 | เห็นเฉพาะ `owner` ของตนเอง vs ทั้ง portfolio = `null` (owner `{{PROJECT_SPONSOR}}` + `{{DPO_OR_LEGAL}}`) |
| ชั้นที่บังคับ (ถ้าเลือก scope จำกัด) | **data access layer** (parameterized query ที่ผูกกับตัวตนผู้ใช้ ไม่รับ filter จาก client) — ไม่ใช่ filter ของ Dash เพียงอย่างเดียว; DuckDB ไม่มี policy ในฐานข้อมูล จึงเป็น `[DESIGN PROPOSAL]` และต้องไม่เปิด role เหล่านี้ให้เข้าไฟล์ตรง |
| ตัวตนผู้ใช้ (authN) | ยังไม่มี authentication ใน plan (read-only MVP) — แหล่งตัวตนและการ map user -> `Owner-NNN` = `null` (owner `{{DATA_STEWARD}}`); **จนกว่าจะมี authN การบังคับ row-level ใช้ไม่ได้จริง** |
| การทดสอบข้ามกลุ่ม | ทดสอบด้วย pytest: ผู้ใช้ A ที่มี scope A ต้องได้ 0 แถวของ scope B ผ่านทุก query ใน data access layer และต้องไม่สามารถเพิ่ม parameter เพื่อข้าม scope (TESTING_STRATEGY.md เป็นเจ้าของ test case) |

### Column Masking

อิง `pdpa_classification` ใน DATA_MODEL_SPEC.md; ชั้นที่ mask = data access layer (view/query ที่ dashboard ใช้) **และ** export — mask ใน UI อย่างเดียวไม่นับ

| Column | Classification | ROLE-06 | ROLE-03 | ROLE-01/02/05 | ROLE-04 |
|---|---|---|---|---|---|
| `owner` | `confidential` (Path A) | ดิบ | ดิบ (จำเป็นต่อ KPI-03 follow-up) `[ASSUMPTION]` | `null` — masking vs ดิบ ตัดสินโดย `{{DPO_OR_LEGAL}}` | ของตน; อื่น `null` |
| `action_name` | `confidential` (Path A) | ดิบ | ดิบ `[ASSUMPTION]` | ดิบ ถ้าไม่พบชื่อบุคคลจากการตรวจเนื้อหา; มิฉะนั้น `null` | `null` |
| `record_key`, `message` (`data_quality_results`) | `confidential` (inherit) | ดิบ | ไม่มีสิทธิ์/สรุป | ไม่มีสิทธิ์/สรุป | - |
| `summary_text` | `confidential` (inherit) | ดิบ | ดิบ | ดิบ | - |

วิธี mask ที่อนุญาต (ดูหัวข้อถัดไป) ใช้กับ export (CSV/AG Grid download) ด้วย — Dash AG Grid export ต้องผ่าน masking เดียวกับที่แสดง

## PDPA and PII Classification

Classification ต่อทุกตารางใน DATA_MODEL_SPEC (ค่า = `pdpa_classification`; ยัง **provisional** ภายใต้ GOV-OPEN-01) ไม่มีข้อมูลลูกค้า ไม่มี sensitive personal data ตามที่ทราบ จึงไม่มี column `restricted`/`public`

| Gov ID | Table | PII / potential PII columns | Classification ระดับ column | Classification ระดับตาราง (สูงสุด) |
|---|---|---|---|---|
| GOV-PII-01 | `raw_actions` | `owner`, `action_name` | `confidential` ทั้งสอง (Path A); ที่เหลือ `internal` | `confidential` |
| GOV-PII-02 | `stg_actions` | `owner`, `action_name` | เช่นเดียวกัน | `confidential` |
| GOV-PII-03 | `ingestion_runs` | `source_file` (ชื่อไฟล์ อาจมีชื่อบุคคลถ้าตั้งชื่อไม่ดี — ตรวจตอน implement) | `internal` | `internal` |
| GOV-PII-04 | `data_quality_results` | `record_key`, `message` (อาจมีค่าจาก `owner`/`action_name`) | `confidential` (inherit; ลดการใส่ค่า) | `confidential` |
| GOV-PII-05 | `executive_summaries` | `summary_text` (สร้างจากข้อมูลที่รวม `owner`) | `confidential` (inherit) | `confidential` |
| GOV-PII-06 | `app_config` | ไม่มี | `internal` | `internal` |

พื้นที่อื่นที่ personal data อาจอยู่ (ต้องอยู่ในขอบเขต erasure): ไฟล์ CSV ต้นทาง, ไฟล์ DuckDB และ backup/copy, export จาก AG Grid, cache ของ Dash, context ที่ส่ง AI provider (GOV-AI-01) และ log (ห้ามพิมพ์ค่า `owner`/`action_name` ลง log เกินจำเป็น)

### Masking / Anonymization (Path A)

| วิธี | ใช้กับ | หมายเหตุ |
|---|---|---|
| คง pseudonym `Owner-NNN` | `owner` ใน view สำหรับ non-privileged | **ไม่ใช่ anonymization** — เป็น pseudonymization เท่านั้น เพราะ mapping กลับอาจมีอยู่ที่อื่น (ไม่ทราบ) |
| แทนที่ด้วย token (เช่น hash พร้อม salt ที่เก็บแยก) | `owner` ในกรณี `null`/mask | ชนิดอัลกอริทึม/การจัดการ salt = `null` (owner `{{DATA_STEWARD}}` + `{{DPO_OR_LEGAL}}`) |
| ตัด/ปิดข้อความ | `action_name` ที่พบชื่อบุคคล | วิธีตรวจ (manual sample vs rule) = `null` (owner `{{DATA_STEWARD}}`) |
| ไม่ใส่ค่าใน `message` | `data_quality_results` | ใช้ `source_row_number`/`action_id` แทน (สอดคล้อง DATA_MODEL_SPEC) |

### Legal Basis

ไม่กำหนดฐานใหม่ที่นี่ อ้าง **CON-18**: legal basis ต่อประเภทข้อมูล = `null` (owner `{{DPO_OR_LEGAL}}`) — มี 1 ฐานต่อ 1 ประเภท PII ครอบคลุมตั้งแต่เก็บถึง retain:

| ประเภทข้อมูล | Legal basis |
|---|---|
| `owner` | อ้าง CON-18 = `null` (ขึ้นกับ GOV-OPEN-01) |
| `action_name` | อ้าง CON-18 = `null` |
| Data residency | อ้าง CON-17 = `null` |

เมื่อ CONSTRAINTS.md ระบุฐานแล้ว ให้อัปเดตที่นั่นก่อน แล้วค่อยแก้ตารางนี้ (reconcile รอบสอง)

### GOV-AI-01 — AI Executive Summary (bonus): ข้อมูลที่ออกนอกระบบ

บันทึกเป็นรายการ governance ไม่ใช่การอนุมัติ: PL-02 ส่ง structured context จาก DuckDB ไปยัง AI provider ภายนอก (OpenRouter, model `anthropic/claude-sonnet-5` — CON-27; ห่วงโซ่ผู้ประมวลผล OpenRouter -> Anthropic)

| ประเด็น | ข้อกำหนด |
|---|---|
| สิ่งที่ **อนุญาตให้ออก** (การตัดสินใจของผู้ใช้ iteration 1; ไม่ใช่การอนุมัติ DPO/legal) | `reference_date`, aggregate ระดับ portfolio (`total_actions`, `completed_actions`, `open_actions`, `overdue_actions`), aggregate รายโครงการ (`project_name` + counts), และแถว `top_overdue_actions` แบบจำกัด top-N ที่มี field `action_id`, `project_name`, `action_name`, `owner`, `due_date`, `days_overdue` (N = `null`: calibration — ตั้งใน config, owner `{{DATA_STEWARD}}` + `{{DPO_OR_LEGAL}}`; PIPELINE_SPEC ST-22) |
| สิ่งที่ **ห้ามออก** | raw CSV ทั้งไฟล์, ตารางเต็ม (`raw_actions`, `stg_actions`), `data_quality_results`, `OPENAI_API_KEY`, ค่า path/ชื่อไฟล์ |
| `owner` และ `action_name` ใน context | **ผู้ใช้ตัดสินใจให้ส่งได้** (เฉพาะแถว top-N ข้างต้น) เพื่อให้ AI ระบุผู้รับผิดชอบติดตามได้; PDPA classification ของทั้งสอง field ยังเปิด (GOV-OPEN-01) และ Path A ยังคงใช้กับการจัดเก็บ/export/log (ห้ามพิมพ์ค่าลง log) |
| การอนุมัติ | ยังไม่มี — **ไม่มีการอนุมัติจาก `{{DPO_OR_LEGAL}}` สำหรับการส่งออก** (มีเพียงการตัดสินใจของผู้ใช้) ระบบต้องปิดปุ่ม Generate พร้อมข้อความตั้งค่า ถ้าไม่มี `OPENAI_API_KEY` หรือ `OPENAI_BASE_URL` ตาม PIPELINE_SPEC |
| Credential | `OPENAI_API_KEY` (และ `OPENAI_BASE_URL`) อยู่ใน env เท่านั้น ห้าม commit ห้ามเก็บใน DB รวม `executive_summaries`/`app_config` ห้ามพิมพ์ลง log (CON-21) |
| ข้ามพรมแดน / ผู้ประมวลผลบุคคลที่สาม | ห่วงโซ่ OpenRouter -> Anthropic: ผลต่อ PDPA/data residency ยังไม่ได้ตัดสิน (CON-17 = `null`) — **รายการเปิด** owner `{{DPO_OR_LEGAL}}`; ไม่มีการอ้างว่าได้รับอนุมัติ |
| สัญญากับ provider (DPA, การไม่นำไปเทรน, retention ฝั่ง provider) | `null` — ยังไม่ได้ตรวจสอบเงื่อนไขของ OpenRouter และ Anthropic; owner `{{DPO_OR_LEGAL}}` (AI_MODEL_SPEC.md เป็นเจ้าของ prompt/ข้อกำหนดโมเดล) |
| ผลลัพธ์ที่บันทึก | `summary_text` เป็น `confidential` (inherit) อยู่ในขอบเขต retention/erasure; ต้องไม่เติม severity/impact/SLA ที่ source ไม่มี |
| Audit | บันทึกทุกครั้งที่ส่ง: `source_run_id`, `provider`, `model_name`, `prompt_version` (มีใน `executive_summaries`) + รายชื่อ field ที่ส่ง |

## Data Retention Policy

กฎของแบบเอกสาร: ทุก retention = ตัวเลข + เหตุผลทางกฎหมาย/ธุรกิจ หรือ `null` + owner ที่ calibrate ใน plan **ไม่มีระบุ retention** จึงเป็น `null` ทั้งหมด; แถวเพิ่มต่อทุก run (run versioning) ทำให้ข้อมูลสะสม — ปริมาณ projection (CON-12/13) = `null`

| Gov ID | Dataset | Retention (เดือน) | Justification / Calibration source | Calibration owner | ปลายทางเมื่อหมดอายุ |
|---|---|---|---|---|---|
| GOV-RET-01 | CSV ต้นทาง | `null` | ข้อกำหนดกฎหมาย/ธุรกิจ (ไม่ระบุใน plan) | `{{DPO_OR_LEGAL}}` | `null` (archive vs delete) |
| GOV-RET-02 | `raw_actions` | `null` | ความต้องการ audit/reconcile (DQ-10) ต่อกี่ run | `{{DPO_OR_LEGAL}}` + `{{DATA_STEWARD}}` | `null` |
| GOV-RET-03 | `stg_actions` | `null` | จำนวน run ที่ต้อง trace ได้ (STK-05) | `{{AUDIT_OWNER}}` + `{{DPO_OR_LEGAL}}` | `null` |
| GOV-RET-04 | `ingestion_runs` | `null` | ต้องคงอย่างน้อยเท่าที่ยังมีข้อมูล run ที่อ้างถึง (FK) | `{{DATA_STEWARD}}` | `null` |
| GOV-RET-05 | `data_quality_results` | `null` | ความต้องการ audit | `{{DATA_STEWARD}}` | `null` |
| GOV-RET-06 | `executive_summaries` | `null` | การใช้งานหลัง draft + ขอบเขต PDPA | `{{DPO_OR_LEGAL}}` | `null` |
| GOV-RET-07 | `app_config` | n/a (config ไม่มี personal data) | - | - | เก็บตลอดอายุระบบ |
| GOV-RET-08 | Audit log (ดู Audit) | `null` | ฐานกฎหมายของ log | `{{AUDIT_OWNER}}` + `{{DPO_OR_LEGAL}}` | `null` |

### Deletion Procedure (หลังหมดอายุ) `[DESIGN PROPOSAL]`

1. job ที่ `{{DATA_STEWARD}}` เป็นเจ้าของเลือก `run_id` ที่เกิน retention (ต้องไม่ใช่ latest successful run)
2. ลบตามลำดับ FK: `data_quality_results` -> `stg_actions` -> `raw_actions` -> `executive_summaries` (ที่ `source_run_id` นั้น) -> `ingestion_runs`
3. DuckDB ไม่คืนพื้นที่ทันที — ต้อง rebuild ไฟล์ (เช่น export/import หรือ `CHECKPOINT` ตามผลทดสอบ) เพื่อไม่ให้ข้อมูลที่ลบค้างในไฟล์/backup วิธีที่ยืนยันแล้ว = `null` (owner `{{DATA_STEWARD}}`)
4. ลบ CSV ต้นทาง/สำเนา/backup ที่ผูกกับ run ด้วย
5. บันทึกหลักฐาน (ดู Erasure Mechanics)

### Archival Policy

มีการ archive ไป cold storage หรือไม่ = `null` (decision: `{{DPO_OR_LEGAL}}` + `{{PROJECT_SPONSOR}}`) ถ้า archive ต้องอยู่ในขอบเขต erasure และ access control เดียวกับต้นทาง; ไม่มี cold storage ที่นิยามใน plan จึงยังไม่มีตำแหน่ง archive

### Erasure Mechanics (PDPA)

| ข้อ | ข้อกำหนด |
|---|---|
| ระยะเวลาตอบสนอง (SLA) | `null` — calibration source: ข้อกำหนด PDPA/นโยบายองค์กรที่ `{{DPO_OR_LEGAL}}` ยืนยัน (ไม่ระบุตัวเลขเอง); owner `{{DPO_OR_LEGAL}}` |
| ใช้เมื่อ | Path A เท่านั้น (หรือเมื่อ `{{DPO_OR_LEGAL}}` สั่ง) |
| การระบุข้อมูลของ data subject | ค้นด้วย `owner` (และ mapping ภายนอกถ้ามี) ในทุกตาราง — การค้นใน `action_name` เป็นข้อความอิสระ = `null` วิธี (owner `{{DATA_STEWARD}}`) |
| ลำดับการลบ | (1) `stg_actions` / `raw_actions` ทุก `run_id` -> (2) `data_quality_results` (`record_key`/`message`) -> (3) `executive_summaries.summary_text` ที่สร้างจากข้อมูลนั้น -> (4) export/ไฟล์ดาวน์โหลดและ Dash cache -> (5) AI provider context ที่ส่งไปแล้ว (ขึ้นกับสัญญา provider = `null`) -> (6) archive/cold storage/backup -> (7) CSV ต้นทางและสำเนา; ปัญหา: การลบเฉพาะบางแถวใน run ที่ผ่านแล้วทำให้ตัวเลขเปลี่ยน — ต้องบันทึก ANALYTICS_CHANGELOG.md และ reconcile DQ-10 |
| Alternative | แทนที่ `owner` เป็น token anonymous ใน raw/stg แทนการลบแถว — ใช้ได้ต่อเมื่อ `{{DPO_OR_LEGAL}}` ยืนยันว่าผลลัพธ์ไม่ใช่ personal data อีกต่อไป และไม่มี mapping กลับ |
| หลักฐานการลบ | erasure record: request id, วันรับ/วันเสร็จ, ตารางและ `run_id` ที่ดำเนินการ, จำนวนแถวก่อน/หลัง, ผู้ดำเนินการ, ผู้ตรวจสอบ — **ห้ามเก็บค่า personal data ที่ลบแล้วในหลักฐาน** ที่เก็บ + retention ของหลักฐาน = `null` (owner `{{DPO_OR_LEGAL}}`) |
| ถือว่าเสร็จเมื่อ | ทุกจุดในลำดับด้านบนเสร็จ ไม่ใช่เฉพาะตารางต้นทาง |

## Audit Requirements

DuckDB ไม่มี query audit log ในตัว — ต้องบันทึกที่ data access layer / wrapper ของ ROLE-06 และ application log ข้อจำกัด: การ query ตรงด้วย DuckDB CLI โดยเปิดไฟล์เอง **ข้าม log ได้** จึงต้องควบคุมที่สิทธิ์ไฟล์ (GOV-ACC-01) และจำกัด `Rx` ให้ ROLE-06 เท่านั้น

| Gov ID | ข้อกำหนด | รายละเอียด |
|---|---|---|
| GOV-AUD-01 Access Logging | log ทุก query ที่แตะ column `confidential` (`owner`, `action_name`, `summary_text`, `record_key`, `message`) และทุกการ export | ผ่าน data access layer; ครอบคลุม ROLE-02..06 |
| GOV-AUD-02 Change Logging | log ทุก update/delete ของ record และทุกการรัน ingest | ingest เป็น insert-per-run (ไม่แก้ run เก่า) — `ingestion_runs` + `data_quality_results` เป็น audit ของ ingest อยู่แล้ว; delete/erasure/แก้ `app_config` ต้องมี log เพิ่ม |
| GOV-AUD-03 Review Cadence | ความถี่ = `null` (calibration source: ความเสี่ยงและนโยบาย; owner `{{AUDIT_OWNER}}`) |
| GOV-AUD-04 Reviewer | `{{AUDIT_OWNER}}` (ผู้ถือบทบาทยังไม่ระบุ; ไม่ควรเป็น ROLE-06 ซึ่งเป็นผู้เข้าถึงข้อมูลเอง) — log ที่ไม่มีผู้ review ถือว่าไม่ผ่านเงื่อนไขของเอกสารนี้ |
| GOV-AUD-05 Retention | `null` — ดู GOV-RET-08 |

### Audit Log Schema `[DESIGN PROPOSAL]`

| Field | ชนิด (intended) | คำอธิบาย |
|---|---|---|
| `audit_id` | BIGINT | PK |
| `event_time` | TIMESTAMP | เวลาระบบ (timezone convention = `null`, owner `{{DATA_STEWARD}}`) |
| `actor_id` | VARCHAR | ตัวตนผู้ใช้/ROLE-07 (แหล่งตัวตนยังไม่มี — ดู Row-level) |
| `role_id` | VARCHAR | ROLE-01..07 |
| `event_type` | VARCHAR | query / export / change / erasure / ai_context_send |
| `dataset` | VARCHAR | ชื่อตาราง |
| `run_id` | BIGINT | run ที่ถูกเข้าถึง (ถ้ามี) |
| `query_ref` | VARCHAR | ชื่อ query ที่ลงทะเบียน (เช่น Q-PORTFOLIO) หรือ hash ของ SQL — ไม่เก็บค่า parameter ที่เป็น PII |
| `columns_accessed` | VARCHAR | รายการ column |
| `row_count` | INTEGER | จำนวนแถวที่คืน |

Audit log ตัวเองมี classification `internal` ถ้าไม่เก็บค่า PII (กฎด้านบน) ตารางนี้ยังไม่อยู่ใน DATA_MODEL_SPEC.md — ต้องเพิ่มเมื่อยืนยัน (reconcile รอบสอง)

## Cost Governance

DuckDB เป็น embedded/local ไม่มีค่า compute แบบ per-query จาก warehouse; ค่าใช้จ่ายที่ทราบได้มีเพียง host/storage ของที่ deploy และ **ค่า API ของ AI provider (bonus)** (OpenRouter / `anthropic/claude-sonnet-5` — CON-27; ราคา/เพดานยัง `null`) ค่าใช้จ่ายระหว่างปฏิบัติการ (เอกสารนี้) แยกจาก delivery budget ครั้งเดียว (CON-22) และวัน go-live (CON-23) ใน CONSTRAINTS.md

| Gov ID | หัวข้อ | ค่า | Calibration source | Owner |
|---|---|---|---|---|
| GOV-COST-01 | Monthly cost budget (host + storage + AI API) | `null` | ราคา hosting จริง + ปริมาณเรียก AI | **Budget owner: `{{PROJECT_SPONSOR}}`** `[ASSUMPTION]` |
| GOV-COST-02 | Cost dashboard | `[DESIGN PROPOSAL]` ตาม metric ที่วัดได้จริง: ขนาดไฟล์ DuckDB, จำนวนแถวต่อ run, จำนวนครั้ง/โทเคนของ AI call (ต้องเพิ่ม field ให้บันทึก) — ยังไม่มี dashboard ใน DASHBOARD_SPEC | - | `{{DATA_STEWARD}}` |
| GOV-COST-03 | Alert threshold — warning | `null` | สัดส่วนของ GOV-COST-01 เมื่อกำหนดงบ | `{{PROJECT_SPONSOR}}` |
| GOV-COST-04 | Alert threshold — critical | `null` | เช่นเดียวกัน | `{{PROJECT_SPONSOR}}` |
| GOV-COST-05 | Query guard rails (ต่อ role: max runtime, max rows, max memory, kill runaway) | `null` ทุกค่า | load test บนข้อมูลจริง (CON-15/16) | `{{DATA_STEWARD}}` |
| GOV-COST-06 | AI call limit (ต่อวัน/เดือน) | `null` | ราคา provider ที่เลือก | `{{PROJECT_SPONSOR}}` |
| GOV-COST-07 | Cost attribution | ต่อ pipeline: PL-01 (ingest) vs PL-02 (AI summary, ค่าที่แยกได้จริงเพราะเป็น on-demand และมี row ใน `executive_summaries`); ต่อ team/dataset: `null` เพราะระบบไม่มี billing แยกทีม | - | `{{DATA_STEWARD}}` |

**เมื่อเกิน threshold:** warning -> แจ้ง `{{DATA_STEWARD}}` และ budget owner ตรวจหา top spender (ตาม GOV-COST-07); critical -> budget owner ตัดสินใจระงับ PL-02 (AI) ก่อน — core dashboard และ PL-01 ต้องไม่ถูกปิดโดยค่า AI (plan AI-05); ช่องทางแจ้งเตือนและเวลาตอบสนอง = `null` (owner `{{DATA_STEWARD}}`) ผู้อนุมัติการเกินงบ = budget owner

## Reconcile ที่ต้องทำรอบสอง

| เอกสาร | ความคาดหวัง |
|---|---|
| DATA_MODEL_SPEC.md | เพิ่มตาราง audit log (ถ้ายืนยัน) พร้อม classification; ปรับ classification ตามผล GOV-OPEN-01 |
| DATA_QUALITY.md / SLA_FRESHNESS.md | DQ ไม่ซ้ำกับ GOV; ความสดเป็นของ SLA_FRESHNESS |
| PIPELINE_SPEC.md | credential/least privilege อ้าง GOV-ACC-01 และ GOV-AI-01 |
| AI_MODEL_SPEC.md | ขอบเขต context ตาม GOV-AI-01 |
| BUSINESS_GLOSSARY.md | ไม่มี enum ใหม่จากเอกสารนี้ |
| TESTING_STRATEGY.md | test การข้ามสิทธิ์ row-level และการ mask ใน export |

## Open Questions

1. (GOV-OPEN-01) `owner` / `action_name` เป็น personal data หรือไม่ และมี mapping Owner-NNN -> บุคคลจริงหรือไม่ — `{{DPO_OR_LEGAL}}`
2. Legal basis (CON-18), data residency (CON-17), และการประมวลผลโดยบุคคลที่สาม OpenRouter -> Anthropic สำหรับ context ที่มี `owner`/`action_name` (GOV-AI-01; ผู้ใช้ตัดสินใจให้ส่งแล้ว แต่ยังไม่มีคำตัดสิน DPO/legal) — `{{DPO_OR_LEGAL}}`
3. Retention ทุก dataset (GOV-RET-01..08), นโยบาย archive, และ SLA การตอบคำขอลบ — `{{DPO_OR_LEGAL}}` + `{{AUDIT_OWNER}}`
4. ROLE-02/04 เห็นเฉพาะส่วนของตนหรือทั้งหมด และ authentication/แหล่งตัวตนผู้ใช้ — `{{PROJECT_SPONSOR}}` + `{{DATA_STEWARD}}`
5. ใครคือ Data Owner/Steward, `{{AUDIT_OWNER}}`, budget owner จริง และ budget/threshold/guard rail (GOV-COST-01..06) — `{{PROJECT_SPONSOR}}`
