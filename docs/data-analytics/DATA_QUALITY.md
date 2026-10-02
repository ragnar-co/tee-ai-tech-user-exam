# Data Quality Spec

```yaml
doc_id: data_quality
filename: DATA_QUALITY.md
version: 1.0.0
status: draft
depends_on: [data_model_spec, pipeline_spec]
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

เอกสารนี้เป็นเจ้าของ quality rule ทั้งหมด (DQ-01..DQ-10 ตาม plan.md §15 + DQ-11, DQ-12 ที่เพิ่มตอน hardening) ตรวจเมื่อไฟล์มาถึงและกำหนดว่า pipeline ตอบสนองอย่างไร ต่างจาก **data contract** (ข้อตกลงกับ producer — `data_contract`) และ **test** (รันใน CI กับ input ที่ทราบ — `testing_strategy`) ถ้า producer ผิดสัญญา rule ที่นี่จะจับได้ ส่วนถ้า SQL ของเราเองผิด test จะจับ

Freshness != completeness != correctness: เอกสารนี้ดูแล **completeness/validity/uniqueness** ของข้อมูลที่มาถึง; freshness = `sla_freshness`; correctness ของตัวเลข = TESTING_STRATEGY (metric validation)

> **สถานะการ implement/ยืนยัน (2026-10-02):** implement แล้วและมี test — `src/validation.py` + `sql/30_quality/quality_checks.sql` (SQL เป็น implementation เดียว; block ตั้งชื่อด้วย `-- name: DQ-xx`) ครอบคลุม DQ-01..DQ-12; DQ-10 ประเมินที่ ST-07 ใน `src/ingest.py` ทดสอบ SQL เทียบกับตัวประเมินอิสระใน Python (`tests/reference_validation.py`, T-V15) และ edge case ใน `tests/test_hardening_ingest.py` (ดู TESTING_STRATEGY) SQL ในเอกสารนี้คือความหมายบรรทัดฐาน — ของจริงใช้ regex unicode-whitespace สำหรับคำว่า "ว่าง" (ไม่ใช่ `trim()` อย่างเดียว; ดู Open Question 0) ผลบน sample CSV จริง: ไม่มี finding blocking (ไฟล์สะอาด); กรณี invalid ทั้งหมดพิสูจน์ด้วยไฟล์ที่สร้างใน test เท่านั้น

## Enum ที่เอกสารนี้เป็นเจ้าของ

### rule_severity (owner: DATA_QUALITY.md)

Reconcile กับ plan.md §9.4: การจัดระดับที่ใช้ใน code (`blocking` / `warning` / `investigation`) ถูกรับเป็นค่า canonical ของ enum นี้ column `data_quality_results.severity_class` เก็บค่าเหล่านี้ (DATA_MODEL_SPEC)

| value | พฤติกรรมของ pipeline | เทียบกับ template (error/warning) | Action |
|---|---|---|---|
| `blocking` | **ปฏิเสธทั้งไฟล์** (ไม่โหลด raw/stg หรือ rollback); run = `failed`; ไม่เป็น latest successful run | = `error` (blocks pipeline) | ผู้ส่ง/ผู้รัน แก้ไฟล์หรือ pipeline แล้วรันใหม่ |
| `warning` | โหลดต่อ; แสดงให้ผู้ใช้เห็น | = `warning` (alert only) | ตรวจทานตามสะดวก |
| `investigation` | โหลดต่อ; ต้องให้คนจัดประเภทก่อนเชื่อผลสรุป (ยังไม่มี business rule) | ส่วนขยายเฉพาะโปรเจกต์ (ระหว่าง warning กับ error) | `{{DATA_STEWARD}}` ตัดสินว่าเป็น status ใหม่ที่ถูกต้องหรือข้อมูลผิด แล้วอัปเดต enum `action_status` (DATA_MODEL_SPEC) ผ่านกระบวนการเปลี่ยนนิยาม |

## Null and Completeness Checks

### Relation ที่ใช้ใน assertion

`input_rows` = แถวข้อมูลของ CSV ที่ยังไม่แปลงชนิด (ทุกคอลัมน์ VARCHAR; รูปแบบเดียวกับ `raw_actions` + `source_row_number`); `input_columns(column_name)` = ชื่อ header ที่อ่านได้ (ตัด BOM) ค่า "ว่าง" = `IS NULL` หรือ `trim(x) = ''` Implementation ใน ST-04 (PIPELINE_SPEC) อาจรันเป็น SQL บน temp table หรือ Python ที่ให้ผลเทียบเท่า — TESTING_STRATEGY ต้องพิสูจน์ความเทียบเท่า

### Rule catalog (ทุก rule ใช้ตาราง `raw_actions` เป็นปลายทางของข้อมูลที่ตรวจ; finding บันทึกที่ `data_quality_results`)

| Rule | ชื่อ | ตาราง / column | ประเภท | Expected | Severity | Action เมื่อ fail |
|---|---|---|---|---|---|---|
| DQ-01 | required columns exist | `raw_actions` (header ของไฟล์) | schema / null | header มีครบ 6 คอลัมน์: `action_id, project_name, action_name, owner, due_date, status` (จับคู่ตามชื่อแบบตรงตัว ไม่สนลำดับ) | `blocking` (ขาดคอลัมน์ หรือ **ชื่อคอลัมน์ซ้ำใน header** — binding กำกวม จึงไม่รัน row-level check); `warning` (มีคอลัมน์เกิน — ไม่ถูกโหลด, รายงานชื่อ) | ขาด/ซ้ำ: ปฏิเสธไฟล์ + แจ้งเจ้าของสัญญา; เกิน: โหลดต่อและรายงาน (header อ่านแบบ UTF-8 + BOM ตัด BOM; ชื่อคอลัมน์ case-sensitive) |
| DQ-02 | `action_id` not null | `raw_actions.action_id` | null check | ไม่ว่าง | `blocking` | ปฏิเสธไฟล์; ระบุ `source_row_number` |
| DQ-03 | `action_id` unique within input | `raw_actions.action_id` | uniqueness | ไม่ซ้ำภายในไฟล์ (เทียบค่าตรงตัว ไม่ trim/ไม่เปลี่ยนตัวพิมพ์) | `blocking` | ปฏิเสธไฟล์; หนึ่ง finding ต่อ `action_id` ที่ซ้ำ |
| DQ-04 | `project_name` not null | `raw_actions.project_name` | null check | ไม่ว่าง | `blocking` | ปฏิเสธไฟล์ |
| DQ-05 | `action_name` not null | `raw_actions.action_name` | null check | ไม่ว่าง | `blocking` | ปฏิเสธไฟล์ |
| DQ-06 | `owner` not null | `raw_actions.owner` | null check | ไม่ว่าง | `blocking` | ปฏิเสธไฟล์ |
| DQ-07 | `due_date` parseable | `raw_actions.due_date_raw` | validity (format) | ไม่ว่าง ตรงรูปแบบ ISO `YYYY-MM-DD` และเป็นวันที่ปฏิทินที่มีจริง | `blocking` | ปฏิเสธไฟล์ |
| DQ-08 | `status` not null | `raw_actions.status` | null check | ไม่ว่าง | `blocking` | ปฏิเสธไฟล์ |
| DQ-09 | distinct status discovery | `raw_actions.status` | enum validation | ทุกค่า distinct อยู่ใน enum `action_status` (DATA_MODEL_SPEC) | `investigation` | โหลดต่อ; รายงานค่าใหม่; **ไม่ map ไป status อื่น**; ตามนิยาม metric ค่าใหม่จะถูกนับเป็น open จนกว่าจะตัดสิน |
| DQ-10 | source row count reconciles | `ingestion_runs`, `raw_actions`, `stg_actions` | reconciliation / volume | `source_row_count = valid_row_count + invalid_row_count` และใน run ที่ผ่านถึง ST-07: `valid_row_count = COUNT(raw_actions) = COUNT(stg_actions)` | `blocking` | rollback; run = `failed`; แจ้ง `{{DATA_STEWARD}}` (บ่งชี้ bug ของ pipeline ไม่ใช่ของ producer) |
| DQ-11 | row shape | แถวข้อมูลของ CSV | structure | จำนวน field ของแถว = จำนวนคอลัมน์ใน header (แถวที่ field เกิน/ขาด เช่น comma ไม่ครอบด้วย `"`, หรือบรรทัดว่าง) | `blocking` | ปฏิเสธไฟล์; ระบุ `source_row_number` (เพิ่มตอน hardening Phase 9) |
| DQ-12 | control characters | ทั้ง 6 field | validity | ไม่มี control character (NUL, `\x01`..`\x1f` ยกเว้น TAB/LF/CR, DEL) | `warning` | โหลดต่อ ค่าเก็บตามต้นทาง; ระบุ `source_row_number` (docs ไม่ได้กำหนด — เลือก warning ตอน hardening) |

DQ-09 เป็น rule ที่ระบุค่าผ่านชื่อ enum เท่านั้น (ค่าอยู่ที่ DATA_MODEL_SPEC) เพื่อไม่ให้นิยามซ้ำ

### SQL assertion (บรรทัดฐาน)

คืนแถว = fail (แต่ละแถวที่คืน = หนึ่ง finding)

```sql
-- DQ-01 (blocking): คอลัมน์ที่ขาด
SELECT c AS record_key FROM (VALUES ('action_id'),('project_name'),('action_name'),
                                    ('owner'),('due_date'),('status')) t(c)
WHERE c NOT IN (SELECT column_name FROM input_columns);
-- DQ-01 (warning): คอลัมน์เกิน
SELECT column_name AS record_key FROM input_columns
WHERE column_name NOT IN ('action_id','project_name','action_name','owner','due_date','status');

-- DQ-01 (blocking): ชื่อคอลัมน์ซ้ำ (บล็อก `DQ-01-duplicate`)
SELECT column_name AS record_key FROM input_columns GROUP BY column_name HAVING count(*) > 1;

-- DQ-11 (blocking): แถวที่จำนวน field <> จำนวนคอลัมน์ใน header
SELECT source_row_number FROM input_rows WHERE field_count <> (SELECT count(*) FROM input_columns);

-- DQ-12 (warning): control character ยกเว้น TAB/LF/CR ใน field ใดก็ได้ (ค่าถูกเก็บตามเดิม)
-- (regexp_matches บน concat ของทั้ง 6 field กับ '[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')

-- DQ-02 / 04 / 05 / 06 / 08 (blocking) — แทน <col> ด้วย action_id / project_name / action_name / owner / status
SELECT source_row_number FROM input_rows WHERE <col> IS NULL OR trim(<col>) = '';

-- DQ-03 (blocking)
SELECT action_id AS record_key, count(*) AS n, list(source_row_number) AS rows
FROM input_rows WHERE action_id IS NOT NULL AND trim(action_id) <> ''
GROUP BY action_id HAVING count(*) > 1;

-- DQ-07 (blocking) — ค่าว่างของ due_date ถือว่า parse ไม่ได้ (ไม่มี rule null แยกสำหรับคอลัมน์นี้)
SELECT source_row_number FROM input_rows
WHERE due_date_raw IS NULL OR trim(due_date_raw) = ''
   OR NOT regexp_matches(due_date_raw, '^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
   OR try_strptime(due_date_raw, '%Y-%m-%d') IS NULL;

-- DQ-09 (investigation) — <action_status values> = ค่าของ enum action_status
SELECT DISTINCT status AS record_key FROM input_rows
WHERE status IS NOT NULL AND trim(status) <> '' AND status NOT IN (<action_status values>);

-- DQ-10 (blocking) — :run_id = run ที่ถึง ST-07
SELECT i.run_id FROM ingestion_runs i
WHERE i.run_id = :run_id
  AND NOT ( i.source_row_count = i.valid_row_count + i.invalid_row_count
        AND i.valid_row_count = (SELECT count(*) FROM raw_actions r WHERE r.run_id = i.run_id)
        AND i.valid_row_count = (SELECT count(*) FROM stg_actions s WHERE s.run_id = i.run_id) );
```

(หมายเหตุ: คอลัมน์ `due_date` ของไฟล์ถูกเก็บเป็น `due_date_raw` ใน `input_rows`/`raw_actions`)

### กฎการนับ

- `invalid_row_count` = จำนวน `source_row_number` ที่ไม่ซ้ำกันซึ่ง fail rule `blocking` ระดับแถวอย่างน้อยหนึ่งข้อ (DQ-02..DQ-08 และ DQ-11; แถวที่ซ้ำตาม DQ-03 นับทุกแถวที่ใช้ `action_id` นั้น) — แถวเดียว fail หลายข้อ = นับครั้งเดียว แต่มี finding หลายรายการ
- DQ-12 เป็น `warning` — ไม่นับเป็น invalid
- DQ-01 (คอลัมน์ขาดหรือซ้ำ) ทำให้ไม่สามารถตรวจระดับแถวได้: `valid_row_count`/`invalid_row_count` = NULL (เป็นค่าที่ DATA_MODEL_SPEC อนุญาต) และ DQ-10 ไม่ถูกประเมิน
- ไฟล์อ่านไม่ได้ (ไม่มี run): ไม่ใช่ finding ใน DB — เป็น CLI error (PIPELINE_SPEC ST-02)

### Completeness Rate

- Required non-null fields: `action_id`, `project_name`, `action_name`, `owner`, `due_date`, `status` (ครบ 6)
- ความทนทาน (tolerance) ของ rule `blocking` = **0 แถว** — มาจาก plan.md §14 ("blocking errors -> reject ingest", "ห้ามทิ้งเงียบ ๆ") ไม่ใช่ค่าที่ calibrate จาก history การผ่อนเป็นเปอร์เซ็นต์ที่ยอมรับได้ = `null` (calibration source: ประวัติคุณภาพไฟล์หลายสัปดาห์ซึ่งยังไม่มี — sample ปัจจุบัน 14,013 แถวไม่มี null/duplicate เลย; owner `{{DATA_STEWARD}}` ร่วมกับ `{{PROJECT_SPONSOR}}`)
- Missing data pattern: การไม่มีไฟล์ประจำสัปดาห์ (ช่องว่างตามเวลา) เป็นเรื่อง freshness -> `sla_freshness` ไม่ใช่เอกสารนี้

## Range and Validity Checks

| ประเภท | การจัดการ |
|---|---|
| Numeric range | ไม่มี column ตัวเลขใน source; `days_overdue` ที่คำนวณได้ต้องเป็น `> 0` เมื่อ `is_overdue` และ `= 0` เมื่อไม่ใช่ — เป็น **invariant ของ metric** ตรวจใน TESTING_STRATEGY (metric validation) ไม่ใช่ DQ rule ใหม่ (รักษา DQ-01..10 ตาม plan) |
| Enum validation | DQ-09 (`status` เทียบ `action_status`) |
| Format validation | DQ-07 (`due_date` ISO) |
| Date range | **ไม่มีกฎช่วงวันที่** — `due_date` ในอนาคตเป็นเรื่องปกติ (งานที่ยังไม่ถึงกำหนด) ขอบเขตความสมเหตุสมผลของ `due_date` (เช่น ช่วงที่ยอมรับ) = `null`; ค่าที่สังเกตใน sample คือ `2026-07-18..2026-11-05` เป็นข้อมูลอ้างอิง ไม่ใช่ขอบเขต (calibration: ประวัติไฟล์หลายสัปดาห์; owner `{{DATA_STEWARD}}`) |
| Reference date | `--reference-date` ต้องเป็นวันที่ ISO ที่ถูกต้อง (ตรวจที่ CLI ก่อนเขียน DB — PIPELINE_SPEC); ไม่ใช่ rule ของข้อมูล source |

Severity + assertion + action ของแต่ละข้อมีในตาราง Rule catalog ด้านบน

## Referential Integrity Checks

โมเดลไม่มี dimension table (DATA_MODEL_SPEC) จึงไม่มี FK ไปยัง dimension และไม่มี cardinality N:M ให้ตรวจ; มีเพียงความสัมพันธ์ระหว่างตาราง run/fact ต่อไปนี้ เป็นกฎโครงสร้างเสริม (supplementary ไม่ได้อยู่ใน plan §15) `[DESIGN PROPOSAL]` ที่บังคับผ่าน test ใน CI (TESTING_STRATEGY) และ DDL ถ้า implement ได้

| Rule | Assertion (คืนแถว = fail) | Severity |
|---|---|---|
| RI-01 | `SELECT s.run_id FROM stg_actions s LEFT JOIN ingestion_runs i USING (run_id) WHERE i.run_id IS NULL OR i.status <> 'succeeded' GROUP BY s.run_id` (orphan / stg ของ run ที่ไม่สำเร็จ) | `blocking` |
| RI-02 | `SELECT run_id, action_id FROM stg_actions EXCEPT SELECT run_id, action_id FROM raw_actions` (stg ต้องมีที่มาใน raw) | `blocking` |
| RI-03 | `SELECT q.run_id FROM data_quality_results q LEFT JOIN ingestion_runs i USING (run_id) WHERE i.run_id IS NULL` | `blocking` |
| RI-04 | `SELECT e.summary_id FROM executive_summaries e LEFT JOIN ingestion_runs i ON i.run_id = e.source_run_id WHERE i.run_id IS NULL` (bonus) | `blocking` |
| RI-05 (cardinality) | `SELECT run_id, action_id FROM stg_actions GROUP BY 1,2 HAVING count(*) > 1` (grain ของ `stg_actions`) | `blocking` |

(ค่า `'succeeded'` อ้างจาก enum `ingestion_run_status`)

### Upstream Schema Drift

Producer ไม่ส่ง version ของ schema (CON-26 `unversioned`) กลไกตรวจ drift = **การตรวจทุก load ใน ST-04 ของ PIPELINE_SPEC โดยใช้ rule ในเอกสารนี้** (ไม่ใช้ shape hash ใน v1.0.0):

| Drift | Rule ที่จับ | การตอบสนอง |
|---|---|---|
| คอลัมน์หาย/เปลี่ยนชื่อ | DQ-01 (`blocking`) | halt, ไม่โหลดข้อมูลเข้า warehouse (ไม่มี raw/stg), แจ้งเจ้าของสัญญา (`{{DATA_STEWARD}}` ติดต่อ producer; ผู้รับผิดชอบฝั่ง producer = `null`) |
| คอลัมน์เพิ่ม | DQ-01 (`warning`) | โหลดต่อ รายงานชื่อคอลัมน์ใหม่; ไม่ใช้ค่านั้นจนกว่าสัญญาแก้ |
| รูปแบบ `due_date` เปลี่ยน | DQ-07 (`blocking`) | halt |
| ค่า `status` ใหม่ / ความหมายเปลี่ยนแบบใช้ค่าเดิม | DQ-09 (`investigation`) สำหรับค่าใหม่; **ความหมายที่เปลี่ยนโดยใช้ค่าเดิมตรวจไม่ได้ด้วย rule นี้** (ข้อจำกัดที่ทราบ) | ตรวจด้วย AN-01/AN-02 เมื่อ calibrate แล้ว |

(บันทึกสำหรับ `data_contract`: กลไก drift detection ที่ใช้ = DQ-01 + DQ-07 + DQ-09 ที่ ST-04 ของ PL-01)

## Anomaly Detection Rules

Anomaly rule ที่ตั้งตึงเกินจะเตือนจนไม่มีใครอ่าน ที่หลวมเกินจะเงียบตอนควรเตือน ค่า threshold ต้องมาจาก history จริง ปัจจุบันมี **sample เดียว (ไม่มี history หลายสัปดาห์)** จึงไม่มีค่า calibrate ใดได้ — ทุกค่าเป็น `null` (ไม่มีตัวเลขกลม ๆ ที่ไม่มีหลักฐาน) rule ที่ threshold เป็น `null` = **ไม่ทำงาน (inactive)**

| Rule | ประเภท | สิ่งที่วัด | Threshold | Severity (เมื่อเปิดใช้) | Calibration source | Owner |
|---|---|---|---|---|---|---|
| AN-01 | volume | `source_row_count` เปลี่ยนเทียบ run `succeeded` ก่อนหน้า (ร้อยละ) | `null` | `warning` | การกระจายของ `source_row_count` ข้ามหลายสัปดาห์ที่สะสมแล้ว | `{{DATA_STEWARD}}` |
| AN-02 | threshold-based | `overdue_actions` (MET-04) เปลี่ยนเทียบ run ก่อนหน้า | `null` | `investigation` | ประวัติ MET-04 ข้าม run ที่ `reference_date` ต่างกัน และการอนุมัติ KPI-02 | `{{KPI_OWNER_ROLE}}` |
| AN-03 | statistical | ค่าเกิน N ส่วนเบี่ยงเบนมาตรฐานของ rolling average ของ AN-01/AN-02 | N = `null`; window = `null` | `warning` | history ข้ามหลาย run (ต้องมีจำนวน run ขั้นต่ำที่ยังไม่ทราบ) | `{{DATA_STEWARD}}` |

หมายเหตุสำคัญ: การเปรียบเทียบข้าม run ขึ้นกับสมมติฐานว่าไฟล์รายสัปดาห์เปรียบเทียบกันได้ (ขอบเขต project/ช่วง due_date เดียวกัน) — ยังไม่ยืนยัน

**Alert configuration:** ช่องทางแจ้งเตือน = `null` (owner `{{DATA_STEWARD}}`; ตัดสินร่วมกับ `sla_freshness`); ระดับของ rule ใช้ค่าจาก enum `rule_severity` ข้างต้น

## Quality Dashboards

แสดงใน dashboard ผ่านข้อมูลของ `data_quality_results` และ `ingestion_runs` (plan.md §23 Phase 7); หน้า/chart จริงนิยามที่ `dashboard_spec` ไม่ซ้ำที่นี่

- **สิ่งที่แสดงขั้นต่ำ:** source file, run_id, `reference_date`, row counts (`source_row_count`, `valid_row_count`, `invalid_row_count`), รายการ finding จำแนกตาม `rule_severity` และ `check_name`
- **Severity distribution:** นับ finding ต่อ `severity_class` ต่อ run
- **Trend chart:** ต้องมี run หลายครั้งก่อนจึงมีความหมาย — ไม่กำหนดใน v1.0.0
- **Quality Score:** **ไม่นิยามตัวเลขรวม** ใน v1.0.0 (ค่า = `null`; owner `{{DATA_STEWARD}}`) เพราะไม่มีฐานเกณฑ์ที่ calibrate และ plan ห้ามสร้างคะแนนที่แต่งขึ้นเอง ใช้นับต่อ rule แทน หากภายหลังต้องการ score ให้ใช้องค์ประกอบต่อไปนี้ (timeliness แยกอยู่ที่ `sla_freshness` เพื่อไม่ให้ตัวเลขเดียวซ่อนการผิด freshness)

| Quality dimension | Rule ที่วัด |
|---|---|
| Completeness | DQ-01, DQ-02, DQ-04, DQ-05, DQ-06, DQ-08 |
| Validity | DQ-07, DQ-09 |
| Uniqueness | DQ-03, RI-05 |
| Consistency | DQ-10, RI-01..RI-04 |

## ความครอบคลุม (DDD validation)

| ตาราง (DATA_MODEL_SPEC) | Rule ที่คุ้มครอง |
|---|---|
| `raw_actions` | DQ-01..DQ-09, DQ-11, DQ-12 |
| `stg_actions` | DQ-10, RI-01, RI-02, RI-05 (และ invariant ของ metric ใน TESTING_STRATEGY) |
| `ingestion_runs` | DQ-10, RI-01, RI-03 |
| `data_quality_results` | RI-03 |
| `executive_summaries` | RI-04 |
| `app_config` | ไม่มี rule (ไม่มีข้อมูลธุรกิจ; ห้ามเก็บ secret — ตรวจใน TESTING_STRATEGY/GOVERNANCE) |

## การตัดสินใจเรื่องไฟล์ input ที่ตัดสินแล้ว (implemented + มี test)

| หัวข้อ | การตัดสินใจ |
|---|---|
| BOM | อ่านด้วย `utf-8-sig` — BOM ไม่ติดชื่อคอลัมน์แรก; ไฟล์ที่ไม่ใช่ UTF-8 ที่ถูกต้อง = exit 2 ไม่เขียน DB |
| ขนาดไฟล์ | เกิน `INGEST_MAX_BYTES` (default 256 MiB; env override) = ปฏิเสธ exit 2 ก่อนอ่าน/เขียน (operational guard ไม่ใช่ business rule) |
| `source_file` | เก็บเฉพาะ basename (ไม่เก็บ path เต็ม); idempotency ใช้ hash เนื้อหา ไม่ใช่ชื่อไฟล์ |
| ไฟล์ว่าง / BOM-only / header-only | exit 2 ไม่เขียน DB และไม่สร้าง run (run ว่างต้องไม่กลายเป็น latest successful run) |
| Exit code | 0 สำเร็จหรือ no-op; 1 ไฟล์ถูกปฏิเสธ (blocking finding / reconcile ล้มเหลว); 2 argument ผิด / อ่านไฟล์ไม่ได้ / เกินขนาด / header-only; 3 DB หรือระบบผิดพลาด (เช่น ถูกล็อก) |
| ข้อความ error | ข้อความที่เก็บใน `data_quality_results` และที่แสดง CLI สำหรับความล้มเหลวระหว่างโหลดมีเฉพาะ **ชนิดของ exception** (ไม่มี path, เนื้อหาแถว, owner/action_name) — สอดคล้องกฎ PDPA ใน AGENTS.md; ข้อความของ exit 2 ฝั่งอ่านไฟล์ก็อยู่ระหว่างปรับให้ตรงกฎนี้ (ตรวจ `src/ingest.py` ก่อนอ้าง) |
| Allowed `check_name` | `data_quality_results.check_name` ∈ `DQ-01..DQ-12` (test T-S07) |

## Open Questions

0. (hardening) "ว่าง" ใน DQ-02/04/05/06/07/08 = NULL หรือมีแต่ whitespace ทุกชนิด (TAB, LF, NBSP, U+3000, ZWSP, BOM ฯลฯ) ไม่ใช่เฉพาะ space; header ซ้ำชื่อ = `blocking` (DQ-01). ค่า `project_name`/`status`/`owner` ที่มี whitespace นำ/ท้าย **ไม่ถูก trim** (เก็บตามต้นทาง): `' todo '` = status ใหม่ (DQ-09 investigation), `'Proj '` = โปรเจกต์แยกต่างหากจาก `'Proj'`
1. Whitespace/ตัวพิมพ์ใน `action_id`/`status`: ปัจจุบันเทียบแบบตรงตัวไม่ normalize (อาจทำให้ `Done` ถูกจัดเป็น status ใหม่ใน DQ-09) — ต้องการ normalize หรือไม่?
2. อนุญาตให้ผ่อน `blocking` เป็น quarantine รายแถว (โหลดแถวที่ดีและรายงานแถวเสีย) หรือคงปฏิเสธทั้งไฟล์? (กระทบนิยาม `valid_row_count`)
3. มีคอลัมน์เกินแล้วควรเป็น `warning` หรือ `blocking`?
4. ขอบเขตความสมเหตุสมผลของ `due_date` และ threshold ของ AN-01..AN-03 (`{{DATA_STEWARD}}` เมื่อมี history)
