# Data Contract

```yaml
doc_id: data_contract
filename: DATA_CONTRACT.md
version: 1.0.0
status: draft
depends_on: [data_model_spec]
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

เอกสารนี้คือ **ข้อตกลงกับ producer** ว่าจะส่งอะไรมา (fields, types, nullability, ค่าที่อนุญาต, format, ความถี่, การเปลี่ยนแปลง) — ไม่ใช่ quality rule (ตรวจเมื่อข้อมูลมาถึงและ pipeline ตอบสนองอย่างไร = DATA_QUALITY.md) และไม่ใช่ test (TESTING_STRATEGY.md) ตาราง/column ภายใน warehouse เป็นของ DATA_MODEL_SPEC.md

> **สถานะ:** สัญญานี้ **ยังไม่มีผู้ลงนามฝั่ง producer** — CON-26 ระบุว่า CSV เป็น `unversioned` และ schema ยืนยันจาก sample เท่านั้น เนื้อหาด้านล่างจึงเป็น *ข้อเสนอที่อิงจาก sample* (`[PROPOSED]`) จนกว่า `{{PRODUCER_TEAMS}}` และ `{{CONTRACT_OWNER}}` ยืนยัน

## Contract Overview

### Contract Parties

| บทบาท | ผู้รับผิดชอบ | หมายเหตุ |
|---|---|---|
| Producer | `{{PRODUCER_TEAMS}}` — ทีมที่ส่ง Weekly Action Item CSV หลังการประชุม | ไม่ทราบจำนวนทีม/ผู้ส่งต่อสัปดาห์ (`null`, source: `{{PROJECT_SPONSOR}}`) |
| Consumer | Data team ผู้ดูแล `src/ingest.py` → `{{DATA_STEWARD}}` | ใช้ข้อมูลผ่าน DuckDB ให้ dashboard (และ AI summary ที่เป็น bonus) |
| Contract owner | `{{CONTRACT_OWNER}}` | อนุมัติการเปลี่ยนแปลง contract (ยังไม่ได้ระบุผู้ถือบทบาท) |

### Contract Scope

| Contract ID | Interface | อยู่ใน scope | Table ปลายทาง (DATA_MODEL_SPEC) |
|---|---|---|---|
| DC-01 | Weekly Action Item CSV (`src/tee_cybersecurity_actions_mock.csv` เป็นตัวอย่าง) | ใช่ | `raw_actions` -> `stg_actions` |

ไม่อยู่ใน scope: ตาราง control/audit (`ingestion_runs`, `data_quality_results`, `executive_summaries`, `app_config`) — ระบบ ingest สร้างเอง ไม่ใช่ข้อมูลจาก producer **Events: N/A** — ไม่มี event stream หรือ API (CON-04, CON-14); ดูหัวข้อ Upstream Event Contract

### Contract Version

| รายการ | ค่า |
|---|---|
| Contract Version | `1.0.0` (SemVer; ใช้กับเอกสารทั้งฉบับ) |
| `csv_schema_version` (DC-01) | `1.0.0` — กำหนดโดยเอกสารนี้ เพราะ producer ไม่ส่ง version เอง (CON-26); ไม่ใช่ตัวเดียวกับ Contract Version |
| Effective date | `null` — calibration source: วันที่ producer ยืนยัน; owner: `{{CONTRACT_OWNER}}` |

## Schema Definitions

Interface DC-01 — ไฟล์ CSV 1 ไฟล์ต่อ 1 การส่ง; 1 แถวข้อมูล = 1 action item; ชื่อ field เป็น snake_case ตรงกับ header จริง และตรงกับ `raw_actions`/`stg_actions` ใน DATA_MODEL_SPEC (ไม่นิยาม column ซ้ำที่นี่)

| Field | Data type (source) | Warehouse type | Nullable | Allowed values / รูปแบบ | ตัวอย่างจาก sample |
|---|---|---|---|---|---|
| `action_id` | STRING | `VARCHAR` | no | ไม่ว่าง; unique ภายในไฟล์; รูปแบบที่สังเกต `A` + 6 หลัก (pattern เป็น *observed* ไม่ใช่ข้อบังคับ) | `A007953` |
| `project_name` | STRING | `VARCHAR` | no | ไม่ว่าง; รูปแบบที่สังเกต `Pxx - ชื่อ`; ชุดโครงการไม่ถูก enumerate (ดู DC-FLD-02) | `P09 - Incident Response Readiness` |
| `action_name` | STRING (UTF-8, ข้อความไทยอิสระ) | `VARCHAR` | no | ไม่ว่าง; ข้อความอิสระ มี branch tag `/ สาขา BR-nnn` ใน sample | `ทบทวนขั้นตอนเก็บหลักฐานเหตุการณ์ / สาขา BR-166` |
| `owner` | STRING | `VARCHAR` | no | ไม่ว่าง; ต้องเป็น pseudonymous ID (รูปแบบ observed `Owner-NNN`) — **ห้ามส่งชื่อ/อีเมลจริง** | `Owner-069` |
| `due_date` | DATE (ข้อความ ISO 8601) | `DATE` | no | `YYYY-MM-DD` เท่านั้น ไม่มีเวลา/timezone | `2026-08-25` |
| `status` | STRING | `VARCHAR` | no | ค่าตาม enum **`action_status`** (owner: DATA_MODEL_SPEC.md) — ห้ามนิยามซ้ำที่นี่ | `done` |

Field IDs: DC-FLD-01 `action_id` · DC-FLD-02 `project_name` · DC-FLD-03 `action_name` · DC-FLD-04 `owner` · DC-FLD-05 `due_date` · DC-FLD-06 `status`

ข้อกำหนดโครงสร้างไฟล์ `[PROPOSED]`:

- Header แถวแรก ต้องมีครบ 6 ชื่อข้างต้น ตรงตัว (case-sensitive); consumer ผูกคอลัมน์ด้วย **ชื่อ** ไม่ใช่ลำดับ
- ชื่อคอลัมน์ซ้ำใน header = ไฟล์ถูกปฏิเสธ (DQ-01 blocking); แถวที่จำนวน field ไม่เท่า header = blocking (DQ-11); control character = warning (DQ-12)
- การเข้ารหัส: UTF-8 (BOM ได้); ขนาดไฟล์สูงสุดที่ consumer รับ = `INGEST_MAX_BYTES` (default 256 MiB, operational guard — เกิน = ปฏิเสธ exit 2); ไฟล์ว่าง / header-only (ไม่มีแถวข้อมูล) = ปฏิเสธ exit 2 ไม่สร้าง run; consumer เก็บเฉพาะ **basename** ของไฟล์เป็น `source_file` (ข้อ implement นี้ยืนยันด้วย test แล้ว แต่ยังไม่มี producer ลงนาม)
- Column เกินจาก 6 ตัว = additive (ดู Breaking Change Policy) — consumer ไม่นำเข้าจนกว่าจะถูก onboard ผ่านการเปลี่ยน contract
- `action_id` ที่ซ้ำข้ามสัปดาห์: ยังไม่ทราบว่า `action_id` คงที่ข้าม run หรือไม่ (BUSINESS_GLOSSARY) — contract รับประกันเฉพาะ uniqueness ภายในไฟล์

**ผูกกับ enum `action_status`:** ค่าสามค่าใน enum สังเกตจาก sample ไม่ใช่ค่าที่ producer เคยรับรอง (DATA_MODEL_SPEC) — การลงนาม contract นี้คือการที่ producer รับรองว่าจะส่งเฉพาะค่าใน enum ปัจจุบัน; ค่าใหม่ = breaking change (ดูด้านล่าง)

## SLA Commitments

Producer เป็นผู้ส่งไฟล์ ไม่ใช่ service — จึงไม่มี uptime ของ producer และไม่มี event timestamp จาก source ค่าทุกตัวต่อไปนี้ยังไม่มีการสอบเทียบ จึงเป็น `null`

| SLA ID | รายการ | ค่า | Calibration source | Owner |
|---|---|---|---|---|
| DC-SLA-01 | Delivery cadence | weekly หลังการประชุม (ตาม plan; วัน/เวลาที่ตกลง = `null`) | ตารางประชุมจริงของ `{{PRODUCER_TEAMS}}` | `{{PRODUCER_TEAMS}}` |
| DC-SLA-02 | Latency — ไฟล์ต้องถึงภายในกี่ชั่วโมงหลังประชุมจบ | `null` | ข้อตกลงกับ producer; ไม่มี timestamp ใน CSV ให้วัดย้อนหลัง | `{{CONTRACT_OWNER}}` |
| DC-SLA-03 | Availability | **N/A** สำหรับ producer (ไม่มี service); ฝั่ง consumer: ความพร้อมของ dashboard = นอก scope สัญญา (ดู SLA_FRESHNESS.md ถ้ามี) | - | - |
| DC-SLA-04 | Completeness — ร้อยละแถวที่ต้องครบ | `null` | baseline จากหลาย run จริง (sample ปัจจุบัน 14,013 แถว ไม่มีค่าว่าง แต่เป็น mock และ run เดียว) | `{{DATA_STEWARD}}` |

กฎการตรวจ/ปฏิกิริยา (reject, warn) ของ completeness อยู่ที่ DATA_QUALITY.md (`data_quality`) ที่นี่เก็บเฉพาะตัวเลขที่ producer ผูกพัน

## Breaking Change Policy

**Breaking ≠ Additive** (เส้นแบ่งประกาศล่วงหน้า):

| ชนิดการเปลี่ยน | จัดเป็น |
|---|---|
| เพิ่ม column ที่ไม่บังคับ (consumer เดิมไม่พัง) | Additive |
| เปลี่ยน type, รูปแบบวันที่, encoding หรือ delimiter | Breaking |
| rename หรือลบ field / drop column | Breaking |
| เปลี่ยนความหมายของค่าเดิม (เช่น `in_progress` หมายถึงอย่างอื่น) | Breaking |
| **เพิ่มค่าใหม่เข้า enum `action_status`** (consumer switch บน `status`; ค่าไม่รู้จักจะถูกนับเป็น open โดยเงียบ — DATA_MODEL_SPEC) | Breaking |
| เปลี่ยน nullability ของ field ที่ required เป็น nullable | Breaking |

- **Notice period:** อย่างน้อย **14 วัน** ก่อนวัน effective `[PROPOSED — ค่าขั้นต่ำของ template DDD; ยังไม่ได้รับการยืนยันจาก producer]` Additive: แจ้งก่อนส่งครั้งแรกที่มี field ใหม่ (ระยะเวลา = `null`, owner `{{CONTRACT_OWNER}}`)
- **Migration procedure:** (1) producer แจ้งพร้อมตัวอย่างไฟล์ใหม่ (2) consumer ประเมินผลกระทบ (LINEAGE.md ถ้ามี) และอัปเดต DATA_MODEL_SPEC / enum ก่อน (3) ผ่านการทดสอบกับไฟล์ตัวอย่าง (TESTING_STRATEGY.md) (4) เพิ่ม contract version และบันทึก ANALYTICS_CHANGELOG.md (5) producer เริ่มส่งรูปแบบใหม่ ณ วัน effective; deadline ของ migration และช่วง dual-format = `null` (owner `{{CONTRACT_OWNER}}`)
- **Versioning strategy:** SemVer บน Contract Version — MAJOR = breaking, MINOR = additive, PATCH = แก้ถ้อยคำ; `csv_schema_version` เปลี่ยนตาม MAJOR/MINOR เช่นกัน ไม่ใช้ namespace v1/v2 เพราะมี interface เดียว; การเปลี่ยน metric definition ที่ตามมาเป็นเรื่องของ ANALYTICS_CHANGELOG.md
- **เมื่อ producer ละเมิดโดยไม่แจ้ง:** pipeline ตอบสนองตาม DATA_QUALITY.md (ไฟล์ที่ผิด contract ต้องแยกแยะได้จากความผิดพลาดของ transformation เอง)

## Required Fields

| Table | Required (non-nullable) | Optional |
|---|---|---|
| DC-01 (CSV) | ทั้ง 6 field: `action_id`, `project_name`, `action_name`, `owner`, `due_date`, `status` | ไม่มี |

- **Default values:** **ไม่มี** — producer ต้องส่งค่าจริงเสมอ; consumer จะไม่เติมค่าแทน field ที่ขาด (ไม่ใช้ default ที่คิดขึ้น เพราะจะเปลี่ยนผลของ metric โดยเงียบ) ข้อความว่าง/ช่องว่างล้วนถือเป็น "ไม่ได้ส่งค่า"
- **Validation rules:** การตรวจ required fields ก่อน ingestion นิยามที่ DATA_QUALITY.md เท่านั้น (ID ที่เกี่ยวข้องใน DATA_MODEL_SPEC/plan: DQ-01..DQ-08) — ไม่ทำซ้ำที่นี่

## Data Type Constraints

| หัวข้อ | ข้อกำหนด |
|---|---|
| Type mapping | CSV เป็นข้อความทั้งหมด: โหลดเข้า `raw_actions` เป็น `VARCHAR` (`due_date` -> `due_date_raw`) แล้วแปลงเป็นชนิดของ `stg_actions` ตาม DATA_MODEL_SPEC (`due_date` -> `DATE`; ชนิดอื่นคงเป็น `VARCHAR`) |
| Precision | ไม่มี numeric field ใน contract — N/A |
| Date format | ISO 8601 `YYYY-MM-DD` ไม่มีเวลา/timezone (CON-26) |
| Encoding | UTF-8 (ข้อความไทยต้องไม่เสียรูป); ไม่ใช่ TIS-620/Windows-874 |
| File format | CSV คั่นด้วย comma, header 1 แถว, ครอบ field ด้วย `"` ตามกติกา RFC 4180 เมื่อมี comma/ขึ้นบรรทัดใหม่ในค่า (sample ทุกแถวมี 6 fields พอดี) |
| BOM | sample ไม่มี BOM; การยอมรับ UTF-8 BOM = **รับ** (implement แล้ว: `utf-8-sig`; T-V16); ขนาดไฟล์สูงสุดเป็น guard เชิงปฏิบัติการ `INGEST_MAX_BYTES` (default 256 MiB, เกิน = exit 2) |
| Max length | `null` ต่อ field — calibration: producer + `{{DATA_STEWARD}}`; ค่าสูงสุดที่สังเกตใน sample (ข้อมูลประกอบ ไม่ใช่ข้อจำกัด): `action_id` 7, `project_name` 33, `action_name` 58, `owner` 9, `due_date` 10, `status` 11 ตัวอักษร |
| Allowed characters | ข้อความ UTF-8 ทั่วไป; `owner` ห้ามเป็นข้อมูลระบุตัวบุคคลโดยตรง (PDPA — การจัดประเภทและกฎเป็นของ DATA_MODEL_SPEC / DATA_GOVERNANCE.md) |

## Upstream Event Contract (Product Events)

**N/A — ไม่มี event producer** ระบบนี้รับ batch file (CSV รายสัปดาห์) ไม่ใช่ event stream; ไม่มี web-app `TRACKING_PLAN.md` ต้นทางและไม่ใช้ integration `consumes: TRACKING_PLAN.md` (optional ตามสเปค) ดังนั้นไม่มี `event_name` ให้อ้างและไม่ list ค่า enum ใด ๆ ที่นี่

หลักการของ section นี้ (producer ไม่ส่ง version เอง จึงต้องกำหนด version ที่ฝั่ง consumer และตรวจจับ drift เอง) ยังใช้กับ DC-01 ได้ในรูปของ file schema:

| Interface | ชื่อ event | `csv_schema_version` | Run แรกที่รับเข้า |
|---|---|---|---|
| DC-01 Weekly Action Item CSV | N/A (ไม่ใช่ event) | `1.0.0` | `null` — `ingestion_runs` implement แล้ว (run ที่ sample ถูกบันทึกได้) แต่ baseline ต้องมีหลาย run จริงจาก producer; ยังเป็น mock run เดียว |

**Schema-drift detection (สอดคล้องกับ PIPELINE_SPEC.md ST-04 และ DATA_QUALITY.md):** เนื่องจาก CSV ไม่มี version ในตัว การตรวจจับการเปลี่ยนรูปร่างไฟล์ต้องทำที่ฝั่ง consumer โดยเทียบ header ที่มาถึงกับรายการ field ใน DC-FLD-01..06 (ชื่อขาด/เกิน/เปลี่ยน) และเฝ้าดูค่า `status` ที่ไม่อยู่ใน enum `action_status` (DQ-01, DQ-09 ตามชื่อใน plan.md §15) กลไกที่เลือกจริง, ระดับความรุนแรง และการแจ้งเตือน = DATA_QUALITY.md (`data_quality`) และการลงมือใน `src/ingest.py` = PIPELINE_SPEC.md (`pipeline_spec`) — เอกสารนี้ไม่นิยามกฎซ้ำ

## Contract Coverage Check (DDD validation)

- ทุก interface ใน scope (DC-01) มี schema, required fields, data types: ผ่าน
- SLA ทุกตัวเป็นค่าที่สอบเทียบแล้วหรือ `null` พร้อม owner: ผ่าน (ทั้งหมด `null`/N/A)
- Breaking change policy ระบุ notice period และ migration procedure: ผ่าน (14 วัน = proposed)
- Upstream Event Contract: N/A อย่างตรงไปตรงมา; ระบุกลไก drift detection เป็น expectation

## Open Questions

1. ใครคือ `{{PRODUCER_TEAMS}}` / `{{CONTRACT_OWNER}}` และ producer ยอมรับ contract นี้หรือไม่ (effective date)
2. Producer รับรอง enum `action_status` ทั้งสามค่าหรือไม่ และมีสถานะอื่น (เช่น cancelled/blocked) ที่อาจโผล่หรือไม่
3. วัน/เวลาส่งและ latency SLA (DC-SLA-01/02) และ completeness baseline (DC-SLA-04)
4. Notice period 14 วันและ migration deadline ยอมรับได้หรือไม่
5. ยอมรับ UTF-8 BOM, max length ต่อ field; `action_id` คงที่ข้ามสัปดาห์หรือไม่ (ผลต่อการเปรียบเทียบ cross-run)
6. `owner` เป็น pseudonym จริงหรือไม่ และมี mapping กลับไปยังบุคคลหรือไม่ (`{{DPO_OR_LEGAL}}`, CON-18)
