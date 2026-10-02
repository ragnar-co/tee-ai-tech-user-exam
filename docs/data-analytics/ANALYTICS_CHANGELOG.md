# Analytics Changelog

```yaml
doc_id: analytics_changelog
filename: ANALYTICS_CHANGELOG.md
version: 1.0.0
status: draft
depends_on: [metric_spec, kpi_dictionary, pipeline_spec, data_contract]
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
doc_created: 2026-10-02
```

เอกสารนี้เป็น audit trail ของการเปลี่ยนแปลงระบบ analytics เพื่อป้องกัน "silent metric change" (สูตรเปลี่ยนโดยไม่แจ้ง ตัวเลขบน dashboard ต่างกัน ทีมเสียความเชื่อมั่น) ทุกการเปลี่ยน `metric_spec`, `kpi_dictionary`, `metric_logic` ต้องบันทึกที่นี่ ส่วน lineage/impact analysis เป็นของ LINEAGE.md

**หมายเหตุวันที่ (สำคัญ):** วันที่ในตารางด้านล่าง = **วันที่สร้างเอกสาร (doc creation date) 2026-10-02** ไม่ใช่ effective date ของข้อมูลหรือของ production `REFERENCE_DATE = 2026-10-02` เป็น **data parameter** (ค่าคงที่ iteration 1 ที่ผู้ใช้ยืนยัน) ไม่ใช่วันที่ใน changelog ระบบยังอยู่ขั้น design (ยังไม่มี `src/ingest.py`, `sql/`) จึง **ยังไม่มีประวัติการเปลี่ยนแปลงจริง** — รายการด้านล่างคือการบันทึกเริ่มต้น (initial baseline) เท่านั้น ไม่มีการแต่งประวัติย้อนหลัง

## Enum ที่เอกสารนี้เป็นเจ้าของ

### change_type (owner: ANALYTICS_CHANGELOG.md)

| value | ความหมาย |
|---|---|
| `metric definition` | นิยาม/สูตรของ metric (METRIC_SPEC.md, METRIC_LOGIC.md) |
| `KPI target` | owner/target/นิยามของ KPI (KPI_DICTIONARY.md) |
| `pipeline logic` | logic, schedule, source, config ของ pipeline (PIPELINE_SPEC.md) |
| `dashboard` | layout/chart ของ dashboard |
| `data contract` | contract กับ producer (DATA_CONTRACT.md) |

เอกสารอื่นอ้างชื่อ `change_type` ไม่ประกาศซ้ำ รายการย่อย "Pipeline Change Detail" (new source / schedule change / logic update) เป็นรายละเอียดภายในรายการ `pipeline logic` ไม่ใช่ค่าของ enum นี้

## Entry Schema

ทุกรายการต้องมี: `date`, `change_type`, `changed_item`, `before_value`, `after_value`, `reason`, `approved_by`, `breaking_change` (boolean) — รายการ breaking ต้องอ้าง Breaking Change Policy ใน DATA_CONTRACT.md (SemVer: MAJOR = breaking; notice 14 วัน `[PROPOSED]`)

`approved_by`: ยังไม่มีผู้อนุมัติที่กำหนดตัวบุคคล ใช้ role placeholder เท่านั้น — `{{KPI_OWNER_ROLE}}` (KPI/metric), `{{CONTRACT_OWNER}}` (contract), `{{DATA_STEWARD}}` (pipeline) ค่า `null` = ยังไม่ได้รับอนุมัติ

## Change Policy

1. **การเปลี่ยนนิยาม metric เป็น breaking change** การ restate ตัวเลขที่รายงานไปแล้วไม่ใช่ bug fix ต้องมี changelog entry, effective date ที่ระบุ, และการตัดสินว่า restate history หรือเก็บนิยามเก่าคู่กัน (ดู Restatement Policy ใน METRIC_LOGIC.md)
2. Metric ที่ `draft` (ทั้งหมดตอนนี้) แก้ได้โดยบันทึก entry แต่ breaking flag จะบังคับใช้เต็มเมื่อ `metric_status = certified` (enum ใน METRIC_SPEC.md)
3. การเปลี่ยน metric ต้อง align ข้ามทีม (consumer: STK ใน STAKEHOLDERS.md); การเปลี่ยน pipeline/infrastructure เป็นเรื่อง operational แยกส่วน
4. การเปลี่ยน `REFERENCE_DATE` (ที่ยืนยันแล้ว) หรือ enum `action_status` กระทบตัวเลข MET-04/MET-05 โดยตรง -> บันทึกทุกครั้ง

## Metric Definition Changes

| Date (doc creation) | change_type | changed_item | before_value | after_value | reason | approved_by | breaking_change |
|---|---|---|---|---|---|---|---|
| 2026-10-02 | `metric definition` | MET-01 `total_actions` | n/a (ไม่เคยมี) | `COUNT(*)` v1.0.0, `draft` | initial baseline | `null` (รอ `{{KPI_OWNER_ROLE}}`) | false |
| 2026-10-02 | `metric definition` | MET-02 `completed_actions` | n/a | `status = 'done'` v1.0.0, `draft` | initial baseline | `null` | false |
| 2026-10-02 | `metric definition` | MET-03 `open_actions` | n/a | `status != 'done'` v1.0.0, `draft` | initial baseline | `null` | false |
| 2026-10-02 | `metric definition` | MET-04 `overdue_actions` | n/a | open AND `due_date < reference_date` (วันเท่ากันไม่นับ) v1.0.0, `draft` | initial baseline | `null` | false |
| 2026-10-02 | `metric definition` | MET-05 `days_overdue` | n/a | `date_diff('day', due_date, reference_date)` เมื่อ overdue v1.0.0, `draft` | initial baseline | `null` | false |
| 2026-10-02 | `metric definition` | MET-06 `completion_rate` (optional) | n/a | `completed_actions / total_actions` (0 ถ้า total = 0) v1.0.0, `draft` | initial baseline | `null` | false |

### Recorded Decision: REFERENCE_DATE (fixed constant, user-confirmed, iteration 1)

รายการนี้ **supersede** ค่า derived เดิม `2026-10-01` (ดู Superseded Record ด้านล่าง)

| field | ค่า |
|---|---|
| date | 2026-10-02 (วันที่บันทึกการตัดสินใจ) |
| change_type | `metric definition` (กระทบ MET-04, MET-05, MET-07, MET-08) |
| changed_item | `REFERENCE_DATE` |
| before_value | `2026-10-01` (derived จากหลักฐาน CSV; ยังไม่ยืนยัน; overdue 3,145, max `days_overdue` 45) |
| after_value | `2026-10-02` — ค่าคงที่ (fixed constant) สำหรับ iteration 1 ที่ผู้ใช้ยืนยัน ไม่ใช่ `date.today()`; overdue 3,531, max `days_overdue` 46 (total 14,013 / completed 8,597 / open 5,416 ไม่เปลี่ยน) |
| reason | ผู้ใช้ยืนยันวันอ้างอิงของ iteration 1; metric ที่ขึ้นกับเวลาต้องไม่ใช้ `date.today()` ส่งผ่าน `--reference-date` และเก็บต่อ run; test fixture ใช้ 2026-09-15 (ต่างจาก REFERENCE_DATE โดยตั้งใจเพื่อจับ `date.today()` ที่ซ่อนอยู่) |
| approved_by | user-confirmed (ผู้ใช้ยืนยัน; role approver `{{KPI_OWNER_ROLE}}` ยังไม่กำหนดตัวบุคคล) |
| breaking_change | false (ยังไม่เคยรายงานตัวเลขออกไป); ค่านี้เปลี่ยนได้ผ่าน changelog entry เท่านั้น — การเปลี่ยนครั้งถัดไป = breaking สำหรับ MET-04/MET-05 ต้องมีการตัดสิน restate/คู่กัน |
| Delivering Task | TSK-01, TSK-21 (TASKS.md) |

**Superseded (historical, ไม่ใช่ค่า normative):** `2026-10-01` -> overdue 3,145; max `days_overdue` 45 — เก็บไว้เพื่อ reconcile เท่านั้น ห้ามใช้เป็นค่าอ้างอิง/expected ใหม่; ค่าอ้างอิงที่ 2026-10-02 (informational ไม่ใช่ target): overdue 3,531; max `days_overdue` 46

### Draft Metric / Query Additions (doc date 2026-10-02)

| Date (doc date) | change_type | changed_item | before_value | after_value | reason | approved_by | breaking_change |
|---|---|---|---|---|---|---|---|
| 2026-10-02 | `metric definition` | MET-07 `owners_with_overdue_actions` | n/a | `COUNT(DISTINCT owner)` บนแถว overdue; parent KPI-03; ป้อน CH-14; `draft` นับเท่านั้น ไม่มี threshold | รองรับคำถาม "owner กี่คนมี item overdue" โดยไม่สร้าง owner performance score (CON-09) | `null` (รอ `{{KPI_OWNER_ROLE}}`) | false |
| 2026-10-02 | `metric definition` | MET-08 `open_not_overdue_actions` | n/a | `open_actions - overdue_actions` (status != 'done' AND NOT overdue); parent KPI-02; ป้อน CH-09 (un-deferred); `draft` | ให้ CH-09 มี metric รองรับ แยก open ที่ยังไม่เลยกำหนดออกจาก overdue | `null` | false |
| 2026-10-02 | `metric definition` | ทุก query (Q-PORTFOLIO, Q-BY-PROJECT, Q-OVERDUE-DETAIL, Q-BY-OWNER) — parameter `project_name` | ไม่มี project filter ที่นิยามต่อ query | รับ `project_name` optional (NULL/'All Projects' = ทั้งหมด) และ restrict แถวจริง (ไม่ใช่ highlight); Q-BY-PROJECT + project = 1 แถว; reference date อ่านจาก `reference_date` ที่เก็บของ run | ให้ตัวกรองโครงการทำงานสม่ำเสมอทุกหน้า | `null` | false |
| 2026-10-02 | `metric definition` | Q-PORTFOLIO — คืน `completion_rate` (MET-06) | Q-PORTFOLIO ไม่คืน `completion_rate` | Q-PORTFOLIO คืน `completion_rate` ด้วย (กฎหารศูนย์ตาม METRIC_SPEC) | ให้ CH-05 มี query รองรับ | `null` | false |

Delivering Task: MET-07/MET-08 -> TSK-20; project filter -> TSK-08, TSK-12, TSK-13; `completion_rate` ใน Q-PORTFOLIO -> TSK-08, TSK-09 (TASKS.md) การเพิ่มทั้งหมดนี้เป็น `draft` ก่อนมี release จึง `breaking_change = false`

## KPI Target Changes

| Date | KPI Changed | Old Target | New Target | Effective Date | Reason | approved_by | breaking_change |
|---|---|---|---|---|---|---|---|
| 2026-10-02 | KPI-01 Action Completion | n/a | `null` (candidate) | `null` | initial baseline: ยังไม่มี target ที่อนุมัติ | `null` | false |
| 2026-10-02 | KPI-02 Overdue Action Backlog | n/a | `null` (candidate) | `null` | เช่นเดียวกัน | `null` | false |
| 2026-10-02 | KPI-03 Owner Overdue Follow-up Load | n/a | `null` (candidate) | `null` | เช่นเดียวกัน | `null` | false |

ยังไม่มีการเปลี่ยน target จริง; เมื่อ `{{PROJECT_SPONSOR}}` อนุมัติ target/owner ให้เพิ่ม entry (`null` -> ค่าอนุมัติ) พร้อม effective date `change_type = KPI target`

## Pipeline Changes

| Date | Pipeline Changed | Pipeline Change Detail | Before vs After | Impact | Delivering Task | approved_by | breaking_change |
|---|---|---|---|---|---|---|---|
| 2026-10-02 | PL-01 `csv_ingest` | initial design (new pipeline) | n/a -> v1.0.0 (design ตอนบันทึก; ต่อมา implement แล้ว — ดูรายการ hardening ด้านล่าง) | `ingestion_runs`, `raw_actions`, `stg_actions`, `data_quality_results`; dashboard ทั้งหมดอ่านผ่าน latest successful run | TSK-04, TSK-05, TSK-06, TSK-07 (TASKS.md) | `null` (`{{DATA_STEWARD}}`) | false |
| 2026-10-02 | PL-02 `executive_summary_generate` (bonus) | initial design (new pipeline) | n/a -> v1.0.0 (design) | `executive_summaries` | TSK-17, TSK-18 (TASKS.md) | `null` | false |
| 2026-10-02 | PL-02 `executive_summary_generate` (bonus) — change_type `pipeline logic`, **user decision** | provider/model/env | provider ไม่ระบุ, env `AI_PROVIDER`/`AI_MODEL`/`AI_API_KEY` -> OpenRouter (OpenAI-compatible HTTPS, ไม่ใช้ `aix`), model `anthropic/claude-sonnet-5` (constant), env `OPENAI_API_KEY` + `OPENAI_BASE_URL`; `executive_summaries.provider='openrouter'`; ส่ง `owner` (Owner-NNN) ใน top-N overdue rows ได้ (N = `null`) | DASH-03, `executive_summaries`; GOV-OPEN-01 (PDPA ของ `owner`/`action_name`) และ data residency (OpenRouter -> Anthropic) **ยัง open** ที่ `{{DPO_OR_LEGAL}}` ไม่มีการอนุมัติ DPO/legal; guardrail ของ OpenRouter workspace ยังไม่ยืนยัน | TSK-17, TSK-18 | ผู้ใช้ (project owner) ตัดสินใจ; DPO/legal `null` | false |

**Hardening / implementation entries (2026-10-02; change_type ตาม enum; approved_by = `null` — ยังไม่มีผู้อนุมัติที่เป็นบุคคล):**

| Date | change_type | changed_item | before_value | after_value | Delivering Task | approved_by | breaking_change |
|---|---|---|---|---|---|---|---|
| 2026-10-02 | `pipeline logic` | DQ-11 row shape (ใหม่) | ไม่มี rule; แถวที่จำนวน field ไม่เท่า header อาจถูกตัด/เลื่อนคอลัมน์เงียบ ๆ | `blocking` ต่อแถวที่ field ไม่เท่า header (ปฏิเสธไฟล์) | TSK-03 | `null` | false (ยังไม่เคยรายงานตัวเลข; ไฟล์ sample สะอาดไม่กระทบ) |
| 2026-10-02 | `pipeline logic` | DQ-12 control characters (ใหม่) | ไม่มี rule | `warning`; ค่าเก็บตามเดิม ไม่ปฏิเสธไฟล์ | TSK-03 | `null` | false |
| 2026-10-02 | `pipeline logic` | DQ-01 duplicate header column | ไม่ระบุ (binding กำกวม) | `blocking` เมื่อชื่อคอลัมน์ซ้ำใน header; ไม่รัน row-level check | TSK-03 | `null` | false |
| 2026-10-02 | `pipeline logic` | ขนาดไฟล์ input สูงสุด `INGEST_MAX_BYTES` | ไม่มีเพดาน | default 256 MiB (env override); เกิน = exit 2 ไม่เขียน DB (operational guard ไม่ใช่ business rule) | TSK-05, TSK-15 | `null` | false |
| 2026-10-02 | `pipeline logic` | `ingestion_runs.source_file` | ชื่อ/พาธไฟล์ตาม `--input` | เก็บเฉพาะ basename; ข้อความ error ที่เก็บมีเฉพาะชนิด exception; header-only/ว่าง = exit 2 ไม่สร้าง run | TSK-05, TSK-15 | `null` | false |
| 2026-10-02 | `pipeline logic` | PL-02 prompt `exec-summary-v2` (เดิม v1) | 4 ส่วนหลัก + next steps, ไม่มี clause untrusted data | 5 ส่วนชัดเจน + GR-08 (ค่าใน context = untrusted data ไม่ใช่คำสั่ง); ต้องประเมิน EV-01..EV-05 ซ้ำเมื่อมีโมเดลจริง (**ยังไม่ได้ประเมิน**) | TSK-17 | `null` | false |
| 2026-10-02 | `pipeline logic` | PL-02 context field caps | ส่งค่าข้อความตามต้นทาง | `action_name`/`owner`/`project_name` ตัด control character และจำกัด 200 ตัวอักษร; `AI_TOP_N` default 10; `AI_TIMEOUT_SECONDS` default 60; `summary_id` จาก sequence `seq_summary_id` | TSK-17 | `null` | false |
| 2026-10-02 | `metric definition` | Q-OVERDUE-DETAIL ORDER BY | `days_overdue DESC, due_date ASC` | เพิ่ม `action_id ASC` เป็น tie-break (ไม่เปลี่ยนค่า metric; ผลเรียงคงที่) | TSK-08 | `null` | false |
| 2026-10-02 | `dashboard` | CH-10 แกน; CH-14 source | แกนไม่ระบุตายตัว; CH-14 อ้าง Q-BY-OWNER | CH-10 แกน 0–100%; CH-14 (MET-07) อ่านจาก Q-PORTFOLIO | TSK-12, TSK-13 | `null` | false |
| 2026-10-02 | `dashboard` | CH-12 Run & validation summary | แผงแสดงบนหน้า Overview | ถอดออกจากหน้า (provenance header ยังแสดง; component `cards.dq_panel` และ `metrics.data_quality_summary` ยังอยู่ ไม่ได้ต่อกับหน้า) — ผู้ใช้ตัดสินใจ 2026-10-02 | TSK-14 | `null` | false (ไม่กระทบสูตร metric) |

### Data Contract (change_type = `data contract`)

| Date | changed_item | before_value | after_value | reason | approved_by | breaking_change |
|---|---|---|---|---|---|---|
| 2026-10-02 | DC-01 file-level rules: BOM ได้, header ซ้ำ = reject, field ไม่เท่า header = reject, ขนาดเกิน `INGEST_MAX_BYTES` = reject, header-only = reject | ไม่ระบุ | เพิ่มในส่วน "ข้อกำหนดโครงสร้างไฟล์" ของ DATA_CONTRACT (implement + test แล้ว; producer ยังไม่ลงนาม) | hardening | `null` | false |
| 2026-10-02 | DC-01 Weekly Action Item CSV | n/a | Contract Version `1.0.0`, `csv_schema_version` `1.0.0`; Effective date = `null` (รอ producer ยืนยัน) | initial baseline | `null` (`{{CONTRACT_OWNER}}`) | false |

## Breaking Changes Log

**ยังไม่มี breaking change ที่เกิดขึ้นจริง** (ไม่มีนิยามที่ certified และยังไม่มี release) — ตารางนี้เป็นเทมเพลตสำหรับรายการในอนาคต อ้าง Breaking Change Policy ใน DATA_CONTRACT.md

| Date | Breaking Change | Affected Consumers | Migration Guide | Deadline |
|---|---|---|---|---|
| — | (ไม่มี) | — | — | — |

เมื่อเกิด breaking change รายการต้องระบุ consumer ที่กระทบจากเอกสารเหล่านี้ (ทุกฉบับมีแล้ว): `dashboard_spec` (dashboard/chart), `report_spec` (รายงาน), `ai_model_spec` (AI Executive Summary context — PL-02 อ่านผล Q-PORTFOLIO/Q-BY-PROJECT/Q-OVERDUE-DETAIL) และ `pipeline_spec`; Deadline ของ migration = `null` (owner `{{CONTRACT_OWNER}}`; notice ขั้นต่ำ 14 วัน `[PROPOSED]`)

ตัวอย่างสิ่งที่จัดเป็น breaking (ตาม policy ไม่ใช่เหตุการณ์จริง): เพิ่มค่าใหม่ใน enum `action_status`, เปลี่ยนสูตร `overdue_actions` เป็น `<=`, rename column, เปลี่ยนรูปแบบ `due_date`

## Open Questions

1. ผู้อนุมัติ (`approved_by`) ของ metric/KPI/contract คือใคร — จนกว่าจะกำหนด ทุก entry เป็น `null`
2. effective date ของ contract
3. Delivering Task ID: อ้าง TASKS.md แล้ว; ปรับเมื่อ task เปลี่ยน
