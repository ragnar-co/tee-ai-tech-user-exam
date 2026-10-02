# Runbook / Incident Response

```yaml
doc_id: runbook
filename: RUNBOOK.md
version: 1.0.0
status: draft
depends_on: [pipeline_spec, sla_freshness, data_quality]
also_references: [data_governance, data_model_spec, testing_strategy, constraints]
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

เอกสารนี้เป็นคู่มือ on-call สำหรับ PL-01 `csv_ingest` / PL-02 `executive_summary_generate` และ dashboard ไม่ซ้ำนิยาม rule/SLA/alert ที่เป็นของ DATA_QUALITY.md (DQ-/AN-), SLA_FRESHNESS.md (FR-/AL-) และ PIPELINE_SPEC.md (PL-/ST-) — อ้างด้วย ID เท่านั้น

> **สถานะการยืนยัน (2026-10-02):** `src/ingest.py`, `src/validation.py`, `dashboard/app.py`, `sql/` และ `tests/` มีแล้ว **ยืนยันด้วย test/การรันจริง:** คำสั่ง ingest/pytest/dashboard; exit code 0/1/2/3 (รวมไฟล์เกิน `INGEST_MAX_BYTES`, header-only = 2, DB ถูกล็อก = 3); rerun/idempotency (RB rerun); failed run ไม่เป็น latest; ไม่มี run สำเร็จ -> dashboard แสดง empty state; AI ล้มเหลว/ไม่ตั้ง key -> ปุ่มปิดหรือแสดง error ไม่บันทึก (ด้วย mocked HTTP) **ยังไม่เคย dry-run/ยืนยัน:** ขั้นตอน backup/restore (JOB-RET-01..04), การลบ summary (RB-07 rollback ด้วยมือ), escalation/incident process, scheduler/monitoring/on-call (ไม่มี), การเรียก OpenRouter จริง — ขั้นตอนเหล่านี้ยังเป็น design

## Enum ที่เอกสารนี้เป็นเจ้าของ

### incident_severity (owner: RUNBOOK.md)

สเกลความรุนแรงของ **เหตุ** — แยกจาก `dataset_criticality` (owner: SLA_FRESHNESS.md; ความสำคัญของ dataset) และ `rule_severity` (owner: DATA_QUALITY.md; ระดับ finding ต่อ rule) ห้ามสลับกัน: finding `blocking` ไม่ได้แปลว่า SEV1 โดยอัตโนมัติ

| value | ความหมาย | เกณฑ์จัดระดับ (เชิงคุณภาพ) |
|---|---|---|
| `SEV1` | วิกฤต | ตัวเลขผิดที่ผู้ใช้อาจนำไปตัดสินใจแล้ว (correctness) หรือข้อมูล personal data รั่ว/ลบไม่ครบ หรือ dashboard ใช้งานไม่ได้ในช่วงที่ประชุมต้องใช้ |
| `SEV2` | ใหญ่ | ข้อมูลของ `dataset_criticality` = `P0` ไม่สดตาม tolerance หรือ run ล่าสุด `failed` และไม่มีทางแก้ก่อนรอบประชุม |
| `SEV3` | เล็ก | กระทบเฉพาะ `P1`/`P2` (เช่น PL-02 bonus) หรือมี workaround ชัดเจนและ dashboard ยังแสดง latest successful run ถูกต้อง |

หมายเหตุ: ไม่มี time-to-respond ผูกกับค่าเหล่านี้จนกว่าจะ calibrate (ดู Escalation Contacts) ไม่มีตารางเทียบ `P0/P1/P2` ของ template กับ SEV ในเอกสารนี้ — คำว่า P0/P1/P2 ในเอกสารนี้หมายถึง `dataset_criticality` เท่านั้น

## Common Failure Scenarios

ข้อเท็จจริงของระบบที่ทุก scenario พึ่ง: dashboard อ่านจาก **latest successful run** เท่านั้น run ที่ `failed` ไม่มีแถวใน `stg_actions` และไม่กระทบ dashboard (PIPELINE_SPEC ST-03/ST-08); ingest เป็น **single writer** ของไฟล์ DuckDB และ dashboard เปิดแบบ **read-only** (CON-07, CON-15); ไม่มี source timestamp (วัดได้เฉพาะ `ingestion_runs.started_at/completed_at` และ `reference_date`)

คำสั่งที่ใช้ (รันและยืนยันแล้วในเครื่องพัฒนา; ทางเลือก Docker: `docker compose up --build` — entrypoint รัน ingest ทุก start แบบ idempotent, ingest ล้มเหลว = container หยุด, ล้างข้อมูลด้วย `docker compose down -v`; ยืนยันบน Docker 29.8.1 เท่านั้น ยังไม่ตรวจ Windows/Mac volume ownership, read_only rootfs, multi-arch):

```bash
python -m src.ingest --input src/tee_cybersecurity_actions_mock.csv --reference-date 2026-10-02
pytest
python dashboard/app.py
```

`2026-10-02` คือ REFERENCE_DATE (ค่าคงที่ที่ผู้ใช้ยืนยันสำหรับ iteration 1; เปลี่ยนได้ผ่าน ANALYTICS_CHANGELOG.md เท่านั้น; ค่าเดิม 2026-10-01 ถูก supersede; test fixture ใช้ 2026-09-15 ซึ่งต่างจาก REFERENCE_DATE โดยตั้งใจ) — ในการ rerun จริงใช้ `--reference-date` ของรอบนั้นเสมอ ไม่ใช้ `date.today()` (CON-06)

Exit code (PIPELINE_SPEC `[DESIGN PROPOSAL]`): `0` สำเร็จ/no-op, `1` ถูกปฏิเสธเพราะ `blocking` หรือ DQ-10, `2` argument/ไฟล์อ่านไม่ได้, `3` DB/ระบบผิดพลาด

### RB-01 Pipeline ไม่รันหรือรันไม่จบตามกำหนด

| หัวข้อ | รายละเอียด |
|---|---|
| Trigger | AL-02 (run ล่าสุดของสัปดาห์ = `failed`, exit 1/3); หรือ `ingestion_runs` มีแถว `running` ค้างโดย `completed_at` เป็น NULL; หรือผู้รันแจ้งว่า command ไม่จบ (ไม่มี scheduler จึงไม่มี alert อัตโนมัติ) |
| Severity | `SEV2` ถ้ากระทบ FR-01/FR-02 (`P0`) ก่อนรอบประชุม; ไม่เช่นนั้น `SEV3` |
| First response (15 นาทีแรก) | 1) เปิด triage checklist ด้านล่าง 2) อ่าน stdout/stderr + exit code 3) query `ingestion_runs` ล่าสุด (`run_id`, `status`, `started_at`, `completed_at`) 4) ยืนยันว่า dashboard ยังแสดง run `succeeded` ก่อนหน้า (ไม่ใช่ข้อมูลว่าง) 5) แจ้ง L1 ตาม Escalation Contacts |
| Root cause checklist | exit code อะไร -> `2` ไฟล์/argument/รูปแบบ `--reference-date` ผิด; `3` DB ล็อก (RB-06) พื้นที่ดิสก์ สิทธิ์ไฟล์ DB; `1` ดู RB-04; process ถูก kill กลางทาง (แถว `running` ค้าง); เป็นข้อผิดพลาด permanent หรือ transient (PIPELINE_SPEC Error Handling) |
| Recovery | แก้สาเหตุแล้ว rerun ตามหัวข้อ Pipeline Rerun; ไม่มี automatic retry ใน v1.0.0 |
| Rollback | ไม่ต้อง rollback ข้อมูล: transaction ST-05..ST-07 ถูก rollback เมื่อล้มเหลว และ run `failed` ไม่เป็น latest successful run; แถว `running` ค้างให้ปิดตามหัวข้อ Rollback Procedure (ข้อ A). จุดที่ย้อนกลับไม่ได้: ไม่มี ในสถานการณ์นี้ |

### RB-02 Data freshness SLA breached

| หัวข้อ | รายละเอียด |
|---|---|
| Trigger | AL-01 (อายุ latest successful run เกิน tolerance) — tolerance ของ FR-01..FR-05, threshold, ช่องทาง = `null` ใน SLA_FRESHNESS (owner `{{DATA_STEWARD}}`) ดังนั้น **ยังไม่มีเงื่อนไขอัตโนมัติ** trigger จริงในตอนนี้ = ผู้ใช้/`{{MEETING_CHAIR}}` แจ้ง หรือ `{{DATA_STEWARD}}` เห็นว่า `completed_at` เก่าเมื่อเทียบกับรอบประชุม; หรือ AL-04 (summary อ้าง run ที่ไม่ใช่ latest) |
| Severity | `SEV2` ถ้า FR-01/FR-02 (`P0`) ไม่สดและที่ประชุมกำลังจะใช้; `SEV3` ถ้า FR-03..FR-05 |
| First response | 1) แยก 2 แบบตาม SLA_FRESHNESS: (A) ไม่มี run ใหม่ — CSV ไม่มา/ไม่ถูกรัน หรือ (B) run ล่าสุด `failed` -> ไป RB-01/RB-04 2) ตรวจว่า CSV รอบนี้มาถึงหรือยัง (triage Step 4) 3) ยืนยันว่า dashboard แสดง `run_id`/`reference_date`/`completed_at` เพื่อให้ผู้ใช้รู้อายุข้อมูล 4) แจ้ง `{{MEETING_CHAIR}}` ว่าตัวเลขที่เห็นคือของ run ใด |
| Root cause checklist | CSV ยังไม่ถูกส่งจาก `{{PRODUCER_TEAMS}}` (DC-SLA-01/02); ผู้รันยังไม่ได้รัน; run `failed`; ผู้ใช้ดู dashboard ที่ค้าง cache/ยังเปิด process เก่า; `--reference-date` ที่ใส่ผิดทำให้ตัวเลข overdue ไม่ตรงรอบ |
| Recovery | ถ้า CSV ไม่มา: ขอจาก producer ตามสัญญา `data_contract` แล้วรัน PL-01; ถ้ามาแล้วแต่ไม่ได้รัน: รัน; หลังสำเร็จ verify ตามหัวข้อ Verification |
| Rollback | ไม่มี (การโหลด run ใหม่ไม่ทับ run เก่า — run versioning) ถ้า run ใหม่ผิด ให้ดู Rollback Procedure ข้อ B |

### RB-03 ตรวจพบค่า metric ผิดปกติ (anomaly)

| หัวข้อ | รายละเอียด |
|---|---|
| Trigger | AN-01 (volume), AN-02 (`overdue_actions` / MET-04 เปลี่ยนเทียบ run ก่อนหน้า), AN-03 (statistical) ใน DATA_QUALITY.md — threshold ของทุกกฎ = `null` (calibrate จาก history หลายสัปดาห์ที่ยังไม่มี; owner `{{DATA_STEWARD}}` / `{{KPI_OWNER_ROLE}}`) จึง **ยังไม่มี trigger อัตโนมัติ**: trigger ปัจจุบันคือคนสังเกตเห็นว่าตัวเลขบน dashboard ไม่น่าเป็นไปได้ หรือ finding ระดับ `investigation` (DQ-09) |
| Severity | `SEV1` ถ้าตัวเลขที่ผิดถูกรายงานในที่ประชุมไปแล้ว; `SEV2` ถ้ายังไม่ถูกใช้; `SEV3` ถ้าอธิบายได้ว่าเป็นการเปลี่ยนจริงของข้อมูล |
| First response | 1) อย่าสรุปว่า pipeline เสีย — แยก *ข้อมูลเปลี่ยนจริง* ออกจาก *คำนวณผิด* 2) เทียบ `source_row_count`, `valid_row_count` ของ run ล่าสุดกับ run `succeeded` ก่อนหน้า 3) ตรวจ `reference_date` ของสอง run (MET-04 เปลี่ยนตามวันที่อ้างอิงแม้ไฟล์เดิม — ไม่ใช่ความผิดปกติ) 4) ตรวจ DQ-09 ว่ามีค่า `status` ใหม่ (ไม่ถูกนับเป็น done/open ตามนิยาม) 5) แจ้ง `{{KPI_OWNER_ROLE}}` |
| Root cause checklist | ขอบเขตไฟล์เปลี่ยน (project/ช่วง `due_date` ต่าง — ข้อสมมติของ AN-xx ยังไม่ยืนยัน); `reference_date` ต่างกัน; ค่า `status` ใหม่; ไฟล์ถูกตัด/ซ้ำ (DQ-03, DQ-10); นิยาม metric เปลี่ยน (ดู ANALYTICS_CHANGELOG); บั๊กใน SQL ของ METRIC_LOGIC (รัน `pytest` ส่วน metric validation ของ TESTING_STRATEGY) |
| Recovery | ถ้าข้อมูลเปลี่ยนจริง: ปิดเหตุ บันทึกคำอธิบาย; ถ้าไฟล์ผิด: ขอไฟล์ใหม่จาก producer แล้ว rerun (run ใหม่กลายเป็น latest); ถ้า SQL/โค้ดผิด: แก้ + เพิ่ม test + บันทึก ANALYTICS_CHANGELOG ก่อน rerun (การแก้นิยามเป็น breaking change — ต้องมี effective date และตัดสินใจ restate ประวัติหรือไม่) |
| Rollback | แก้โค้ดแล้วแย่ลง: git revert ของ commit นั้นแล้ว rerun ด้วย `--reference-date` เดิม (จะเป็น run ใหม่เพราะ `source_hash` + `reference_date` ที่ผ่านแล้วอาจ no-op — ดู Pipeline Rerun ข้อสังเกต); ตัวเลขที่รายงานไปแล้วย้อนไม่ได้ ต้องแจ้งผู้ใช้และบันทึกใน ANALYTICS_CHANGELOG |

### RB-04 Data quality check ล้มเหลว

| หัวข้อ | รายละเอียด |
|---|---|
| Trigger | finding ใน `data_quality_results` ตาม `rule_severity` (owner DATA_QUALITY.md): `blocking` (DQ-01..DQ-08, DQ-10) = run `failed` exit 1; `investigation` (DQ-09) / `warning` = โหลดต่อ |
| Severity | `blocking` ของ DQ-01..DQ-08 (ไฟล์ผิด): `SEV3` ถ้ามีเวลาขอไฟล์ใหม่ก่อนประชุม, `SEV2` ถ้าไม่มี; DQ-10 ไม่ตรง = บั๊กใน pipeline: `SEV2`; DQ-09 ค่า status ใหม่: `SEV3` |
| First response | 1) query `data_quality_results` ของ `run_id` ที่ fail จัดกลุ่มตาม rule/`rule_severity` 2) ดู `source_row_number`/`record_key` 3) ตัดสินแหล่ง: ไฟล์ producer (DQ-01..DQ-08) หรือ pipeline เอง (DQ-10) — เป็นคนละเจ้าของ 4) ห้ามแก้ไฟล์ต้นทางเอง/ห้ามทำให้ rule หลวมเพื่อให้ผ่าน |
| Root cause checklist | header เปลี่ยน/คอลัมน์ขาด (schema drift, DQ-01); `action_id` ว่าง/ซ้ำ (DQ-02/03); วันที่ผิดรูปแบบ (DQ-07); encoding/BOM; DQ-10: `source_row_count` ≠ `COUNT(raw_actions)` ≠ `COUNT(stg_actions)` — ตรวจ ST-05/ST-06 และ transaction |
| Recovery | DQ-01..DQ-08: แจ้ง `{{PRODUCER_TEAMS}}` ผ่านสัญญา `data_contract` ให้ส่งไฟล์ใหม่ แล้วรัน PL-01 ใหม่ (run `failed` ไม่ถูกนับใน idempotency check); DQ-10: แก้บั๊ก เพิ่ม test แล้ว rerun; DQ-09: ให้ `{{DATA_STEWARD}}` จัดประเภทค่าใหม่และบันทึก ANALYTICS_CHANGELOG ถ้าต้องเปลี่ยนนิยาม — **ไม่ map ไป status อื่นเอง** |
| Rollback | ไม่มีแถวใน stg ของ run `failed` จึงไม่มีอะไรต้อง rollback; ห้ามลบ run `failed` (เป็นหลักฐาน audit) จนกว่า retention ที่ calibrate แล้วอนุญาต |

### RB-05 Dashboard แสดงข้อมูลเก่าหรือว่าง

| หัวข้อ | รายละเอียด |
|---|---|
| Trigger | AL-03 (ไม่มี run `succeeded` เลย — ข้อความบน dashboard); หรือผู้ใช้แจ้งว่า `run_id`/`reference_date`/`completed_at` ที่แสดงไม่ตรงกับที่คาด; หรือหน้าจอว่าง/error |
| Severity | `SEV2` ถ้าช่วงที่ประชุมต้องใช้ (FR-01/FR-02, `P0`); `SEV1` ถ้าแสดงตัวเลขผิดโดยไม่เตือน; `SEV3` ถ้ากระทบเฉพาะ widget bonus |
| First response | 1) query `ingestion_runs` ว่ามี `succeeded` หรือไม่ และ latest คือ run ใด 2) เทียบกับค่าที่ dashboard แสดง 3) ตรวจว่า process `python dashboard/app.py` ยังทำงาน และเปิด DB แบบ read-only 4) ตรวจว่าไม่มี ingest ถือไฟล์ค้างอยู่ (RB-06) |
| Root cause checklist | ไม่เคยมี run สำเร็จ / run สำเร็จล่าสุดเก่า (RB-02); dashboard เปิดไฟล์ DB ผิด path หรือค้าง connection เก่า; query path (Q-PORTFOLIO / Q-BY-PROJECT / Q-OVERDUE-DETAIL / Q-BY-OWNER) error; สิทธิ์ไฟล์ DB; cache ของ Dash |
| Recovery | restart `python dashboard/app.py` (อ่านสถานะล่าสุด); ถ้าไม่มี run สำเร็จ ให้รัน PL-01; verify ตาม Verification |
| Rollback | restart dashboard ไม่เปลี่ยนข้อมูล จึงย้อนได้เสมอ; ถ้าแก้โค้ด dashboard แล้วแย่ลง ให้ git revert และ restart |

### RB-06 ไฟล์ DuckDB ถูกล็อก (ingest กับ dashboard ชนกัน)

| หัวข้อ | รายละเอียด |
|---|---|
| Trigger | PL-01 ล้มด้วย exit 3 พร้อมข้อความ lock/ไม่สามารถเปิดไฟล์; หรือ dashboard เปิดไม่ได้ขณะ ingest รัน (CON-15; PIPELINE_SPEC Concurrency) |
| Severity | `SEV3` ปกติ (transient); `SEV2` ถ้าบล็อก ingest ที่จำเป็นก่อนประชุม |
| First response | หา process ที่ถือไฟล์ `data/cybersecurity.duckdb` (เช่น dashboard, DuckDB CLI, ingest ซ้อน); ยืนยันว่ามี writer เพียงหนึ่งเดียว; อย่าลบไฟล์ `.wal` เอง |
| Root cause checklist | ingest สองตัวรันพร้อมกัน; dashboard/CLI เปิดด้วยโหมดเขียน; process ค้างจาก run ก่อน; วิธีจัดการที่ตกลงไว้ยังไม่มี (PIPELINE_SPEC Open Question 3) |
| Recovery | ปิด process ที่ถือไฟล์ (หรือหยุด dashboard ชั่วคราว) แล้ว rerun PL-01 — ผู้ใช้ dashboard ได้รับแจ้งว่าหยุดชั่วคราว; จากนั้น start dashboard ใหม่ (read-only) |
| Rollback | ถ้า ingest ถูก kill กลางทาง ให้ดู RB-01 (transaction rollback; แถว `running` ค้างปิดตาม Rollback Procedure ข้อ A) — การ kill ระหว่าง checkpoint ของ DuckDB ให้ตรวจความสมบูรณ์ของไฟล์ก่อนรันต่อ (ถ้าเสีย ใช้ Warehouse Backup + Restore) |

### RB-07 AI provider ล้มเหลว (PL-02, bonus)

| หัวข้อ | รายละเอียด |
|---|---|
| Trigger | ผู้ใช้กด Generate Draft แล้วได้ error (timeout / HTTP 401/403/404/429 / 5xx); ปุ่ม Generate Draft ถูกปิดเพราะไม่มี `OPENAI_API_KEY` หรือ `OPENAI_BASE_URL` |
| Severity | `SEV3` (bonus; `P2`; core dashboard และ PL-01 ต้องไม่ได้รับผลกระทบ — plan AI-05) |
| First response | ยืนยันว่า core dashboard ยังทำงาน (fallback: core ไม่ได้รับผลกระทบ ใช้งานต่อได้โดยไม่มี AI summary); อ่านข้อความ error; ตรวจว่า `OPENAI_API_KEY` และ `OPENAI_BASE_URL` (เช่น `https://openrouter.ai/api/v1`) ถูกตั้งใน process (ตรวจแค่ว่ามีค่า — ห้ามพิมพ์ค่า `OPENAI_API_KEY` ลง log/ticket) |
| Root cause checklist | ตามรหัส HTTP ของ OpenRouter: **401/403** = key ผิด/หมดอายุ หรือ **guardrail ของ workspace บล็อก model** (อนุญาตเฉพาะ `anthropic/claude-sonnet-5` — ยังไม่ยืนยันกับ key นี้; ตรวจว่า model slug ตรงและ workspace อนุญาต); **404** = `OPENAI_BASE_URL` หรือ model slug ผิด; **429** = rate limit/โควตา (transient); **timeout/5xx** = transient; ตรวจด้วยว่าการส่ง `owner` ใน context ยังเป็นไปตามการตัดสินใจ iteration 1 และคำถามเปิด GOV-OPEN-01 / data residency ยังอยู่กับ `{{DPO_OR_LEGAL}}` (ไม่ใช่การอนุมัติ) |
| Recovery | transient (429/timeout/5xx): กด Generate ใหม่; permanent (401/403/404): `{{DATA_STEWARD}}` แก้ key/base URL/สิทธิ์ workspace; **ห้ามสร้าง fake summary**; ไม่ insert `executive_summaries` เมื่อล้มเหลว |
| Rollback | summary ที่ถูกบันทึกแล้วแต่ผิด (เช่น มี severity/impact/SLA ที่ source ไม่มี) ให้ลบแถวนั้นผ่าน Retention/Erasure procedure และเปิด incident `SEV2` ถ้าถูกนำไปใช้ |

## Triage Checklist

ทำตามลำดับเมื่อได้รับ alert หรือรายงาน ใช้เวลาไม่เกินช่วง first response (เวลาที่ใช้จริงต่อ severity = `null`, ดู Escalation Contacts)

- [ ] **Step 1 — Pipeline status:** query `ingestion_runs` ล่าสุดเรียงตาม `started_at`: `status` (`running`/`succeeded`/`failed`), `completed_at`, row counts; ดู exit code จากผู้รัน (PIPELINE_SPEC ST-08)
- [ ] **Step 2 — Data freshness:** `completed_at` + `reference_date` ของ latest successful run เทียบกับรอบประชุมล่าสุด (FR-01/FR-02; tolerance = `null` -> ใช้วิจารณญาณ ห้ามอ้างตัวเลขที่ไม่มี) ตัดสินว่าเป็น (A) ไม่มี run ใหม่ หรือ (B) run `failed`
- [ ] **Step 3 — Quality rules:** `data_quality_results` ของ `run_id` นั้น จัดกลุ่มตาม rule + `rule_severity` (DQ-01..DQ-12); มี `blocking` หรือไม่; DQ-10 ผ่านหรือไม่; AN-01..AN-03 (ถ้าเปิดใช้)
- [ ] **Step 4 — Source system:** CSV รอบนี้มาถึงหรือยัง ไฟล์ตรง header/encoding ที่สัญญาหรือไม่ producer แจ้งเปลี่ยนอะไรหรือไม่ (ไม่มี API/event source — เช็คที่ไฟล์เท่านั้น); ไฟล์ DuckDB ถูกถือโดย process อื่นหรือไม่
- [ ] **Step 5 — เลือก scenario และ severity:** เทียบกับ RB-01..RB-07 กำหนด `incident_severity` แล้วเริ่ม incident log (เวลาเริ่ม, ผู้รับเรื่อง, `run_id` ที่เกี่ยวข้อง) — ห้ามใส่ค่า `owner`/`action_name` ดิบลงใน ticket/log เกินจำเป็น (DATA_GOVERNANCE)

## Recovery Procedures

สถานะต่อขั้นตอน: **Pipeline Rerun / ingest ซ้ำ / failed run** = ยืนยันด้วย test (`test_idempotency.py`, `test_hardening_ingest.py`); **Backup/Restore, Retention job, การลบ draft summary** = ยังเป็น design ไม่เคย dry-run

### Pipeline Rerun

1. แก้สาเหตุก่อน (ดู scenario) — การ rerun สาเหตุ permanent ให้ผลเดิม
2. ตรวจว่าไม่มี process ที่ถือไฟล์ DB (single writer)
3. `python -m src.ingest --input <csv> --reference-date <YYYY-MM-DD>` (ตัวอย่างในโปรเจกต์: `src/tee_cybersecurity_actions_mock.csv`, `2026-10-02` — ค่าคงที่ iteration 1)
4. ผลที่คาดหวัง: run `succeeded` ใหม่ (exit 0) หรือ no-op คืน `run_id` เดิมถ้ามี run `succeeded` ที่ (`source_hash`, `reference_date`) เดียวกัน (ST-02) run `failed` ไม่นับ จึง rerun ปลอดภัย
5. ข้อสังเกต: ไฟล์เดิม + `reference_date` ต่าง = run ใหม่ (ตัวเลข overdue ต่างได้โดยไม่ใช่บั๊ก); เมื่อต้องบังคับให้เกิด run ใหม่จากไฟล์/วันที่เดิมที่เคยสำเร็จ (เช่น หลังแก้ SQL) — **ยังไม่มีกลไกใน design** (ไม่มี `--force`) เป็น open question ข้อ 2 ของ PIPELINE_SPEC; ห้ามแก้ `ingestion_runs` ด้วยมือเป็นทางลัด

### Data Backfill

- โหลดไฟล์รายสัปดาห์ย้อนหลังด้วย `--reference-date` ของแต่ละไฟล์ — แต่ละไฟล์ = run ของตัวเอง โหลดเรียงจากเก่าไปใหม่ **ไฟล์สุดท้ายที่โหลดจะกลายเป็น latest** จึงต้องโหลดไฟล์ล่าสุดเป็นรายการสุดท้าย (หรือโหลดซ้ำอีกครั้ง — ไฟล์เดิม + `reference_date` เดิม = no-op จึงไม่ช่วย; ลำดับการ "latest" นิยามที่ DATA_MODEL_SPEC/METRIC_LOGIC — ตรวจก่อนทำ)
- ช่วงย้อนหลังสูงสุด/ค่าใช้จ่าย = `null` (PIPELINE_SPEC Load Strategy; owner `{{DATA_STEWARD}}`)
- backfill ที่เปลี่ยนตัวเลขที่เคยรายงาน ต้องบันทึก ANALYTICS_CHANGELOG ก่อน

### Rollback Procedure

เพราะใช้ run versioning การ "rollback" ส่วนใหญ่คือการให้ run ที่ดีเป็น latest ไม่ใช่การย้อนข้อมูล

- **A. run ค้าง `running`:** ยืนยันว่าไม่มี process ingest ทำงานอยู่ แล้วปิด run เป็น `failed` พร้อม `completed_at` — ผ่านคำสั่ง/สคริปต์ที่ implement ภายหลัง (ยังไม่มี; ห้ามแก้ตารางด้วยมือโดยไม่มี erasure/change log ตาม GOV-AUD-02)
- **B. run `succeeded` แต่ข้อมูลผิด (bad data เข้า production):** ทางเลือกตามลำดับความปลอดภัย: (1) ขอไฟล์ที่ถูกต้องและโหลดเป็น run ใหม่ — run ใหม่เป็น latest แทน; (2) ถ้าต้องถอน run ผิดออกจริง ให้ใช้ลำดับลบตาม DATA_GOVERNANCE Deletion Procedure (`data_quality_results` -> `stg_actions` -> `raw_actions` -> `executive_summaries` -> `ingestion_runs`) หลัง **สำรองไฟล์ DB** — ห้ามลบ latest successful run ที่ยังถูกต้อง
- **จุดที่ย้อนกลับไม่ได้ (ระบุล่วงหน้า):** การลบ run ที่ commit แล้ว (ย้อนได้เฉพาะถ้ามี backup ก่อนลบ); ตัวเลขที่ถูกรายงานในที่ประชุมแล้ว; การลบตาม PDPA erasure; ข้อความที่ส่งไป AI provider แล้ว
- ทุก rollback ที่เปลี่ยนตัวเลข -> บันทึก ANALYTICS_CHANGELOG (effective date + restate หรือไม่)

### Verification

ก่อนปิด incident ต้องผ่านทั้งหมด (เมื่อ implement แล้ว):

1. `ingestion_runs`: run ที่เกี่ยวข้อง `status='succeeded'`, `completed_at` ไม่เป็น NULL
2. DQ-10: `source_row_count = valid_row_count = COUNT(raw_actions) = COUNT(stg_actions)` ของ run; ไม่มี `blocking` ค้าง
3. Invariant: Q-BY-PROJECT รวมกัน = Q-PORTFOLIO (PIPELINE_SPEC ST-07)
4. `pytest` ผ่าน (โดยเฉพาะ metric validation ของ TESTING_STRATEGY) ถ้ามีการแก้โค้ด
5. `python dashboard/app.py` เปิดได้แบบ read-only และแสดง `run_id`/`reference_date`/`completed_at` ของ run ใหม่
6. ตัวเลขชุดตัวอย่างตรงกับการ query ตรงจาก DuckDB (จำนวนอ้างอิงของ sample: 14,013 แถว, done 8,597 / in_progress 3,326 / todo 2,090 — ใช้ได้เฉพาะกับไฟล์ mock นี้ ; ค่า overdue ที่ 3,145 คำนวณที่ 2026-10-01 ใช้กับ 2026-10-02 ไม่ได้ ต้องคำนวณใหม่จากข้อมูลจริง)

### Warehouse Backup + Restore Drill

- **วิธี backup (design):** DuckDB เป็นไฟล์เดียว (`data/cybersecurity.duckdb`) — สำรองโดยคัดลอกไฟล์ขณะไม่มี writer (หลัง ingest จบ/หยุด dashboard) หรือ `EXPORT DATABASE` ไปยังโฟลเดอร์ที่มีสิทธิ์ไฟล์เดียวกับต้นทาง (GOV-ACC-01) — วิธีที่เลือก/ตำแหน่ง/ความถี่ backup = `null` (owner `{{DATA_STEWARD}}`)
- **ทางเลือกสำรองข้อมูลโดยธรรมชาติ:** CSV ต้นทางยังโหลดซ้ำได้ (ต้องเก็บไฟล์) — การ rebuild จาก CSV ทุกไฟล์ที่ผ่านมาคือทางกู้คืนขั้นสุดท้าย ถ้ายังเก็บไว้ (retention ของ CSV = `null`, GOV-RET-01)
- **Restore (design):** หยุด dashboard และ ingest -> ย้ายไฟล์เสียไปเก็บ -> คัดลอก backup กลับ (หรือ `IMPORT DATABASE`) -> เปิดอ่านแบบ read-only -> Verification ข้อ 1-3
- **RTO / RPO:** `null` — calibration source: เวลาที่ที่ประชุมรอได้ และจำนวนสัปดาห์ข้อมูลที่ยอมสูญเสียได้ (ตกลงกับ `{{MEETING_CHAIR}}`); owner `{{PROJECT_SPONSOR}}` (ตัดสิน) + `{{DATA_STEWARD}}` (วัดผล)
- **ความถี่ drill:** `null` (owner `{{DATA_STEWARD}}`) **ยังไม่เคยซ้อม** — ผลการ drill เทียบ RTO/RPO ยังไม่มี; backup ที่ยังไม่เคย restore = validity ไม่ทราบ; บันทึกผล drill ทุกครั้งในแม่แบบ Post-Incident Review (ประเภท `drill`)
- **PDPA:** backup เป็นพื้นที่ที่ personal data อาจอยู่ ต้องอยู่ในขอบเขต erasure (ดู Retention Enforcement)

## Escalation Contacts

บทบาทและเวลาเป็นไปตามที่ SLA_FRESHNESS.md กำหนด (L1/L2/L3) ไม่สร้างใหม่ — ตารางนี้แปลงเป็น on-call สำหรับ incident ผู้ถือบทบาทจริงยังไม่ได้แต่งตั้ง (DATA_GOVERNANCE)

| ระดับ | Role (placeholder) | Contact | เงื่อนไขเรียก | Owner ของการกำหนดค่า |
|---|---|---|---|---|
| Primary on-call | `{{DATA_STEWARD}}` (ผู้รัน `src.ingest`) | `null` | alert/รายงานทุก scenario | `{{PROJECT_SPONSOR}}` |
| Secondary on-call | `null` (ยังไม่มีผู้สำรอง — ต้องแต่งตั้ง) | `null` | Primary ไม่ตอบภายใน `null` นาที (template แนะนำ 30 นาที — **ยังไม่รับเป็นค่า** จนกว่า owner ยืนยัน) | `{{PROJECT_SPONSOR}}` |
| L2 | `{{MEETING_CHAIR}}`, `{{PRODUCER_TEAMS}}` (ถ้าสาเหตุคือ CSV) | `null` | L1 ไม่ resolved เกิน `null` | `{{DATA_STEWARD}}` + `{{MEETING_CHAIR}}` |
| L3 | `{{CYBERSECURITY_PROGRAM_OFFICE}}` | `null` | ไม่ resolved จนเลยรอบประชุมถัดไป หรือเกิน `null` | `{{PROJECT_SPONSOR}}` |
| ด้านข้อมูลส่วนบุคคล | `{{DPO_OR_LEGAL}}` | `null` | สงสัยข้อมูลรั่ว, คำขอลบ, ข้อมูล personal ใน log/ticket | `{{DPO_OR_LEGAL}}` |
| ตัวเลข/นิยาม KPI | `{{KPI_OWNER_ROLE}}` | `null` | RB-03 | KPI_DICTIONARY |

### Response Time SLA ต่อ `incident_severity`

| Severity | Time to acknowledge | Time to update | Time to resolve target | Calibration source / owner |
|---|---|---|---|---|
| `SEV1` | `null` | `null` | `null` | ค่าที่ตกลงกับ `{{MEETING_CHAIR}}` + ความสามารถของทีมจริง; owner `{{PROJECT_SPONSOR}}` |
| `SEV2` | `null` | `null` | `null` | เช่นเดียวกัน |
| `SEV3` | `null` | `null` | `null` | เช่นเดียวกัน |

เหตุผลที่เป็น `null`: ไม่มี scheduler, ไม่มี monitoring, ไม่มี on-call จริง และไม่มีรายชื่อ (SLA_FRESHNESS Alert Rules) — ค่า 15/30 นาทีใน template เป็นตัวอย่าง ไม่ใช่ข้อตกลง ช่องทางแจ้งเตือน = `null` (ขั้นต่ำที่ออกแบบ: exit code + stdout/stderr + แถว `failed`) ห้ามใช้ AL-01..AL-04 แทน DQ finding หรือผลทดสอบ (freshness ≠ completeness ≠ correctness)

## Post-Incident Review

ทำภายใน `null` วัน (calibrate; owner `{{DATA_STEWARD}}`) สำหรับ `SEV1`/`SEV2` และ drill; แบบ blameless — เน้นระบบ ไม่ระบุตัวบุคคล ห้ามใส่ค่า personal data ดิบ

```markdown
## PIR-<YYYYMMDD>-<n>  (incident_severity: SEVx | ประเภท: incident / drill)

### Incident Summary
- เกิดอะไร / ตรวจพบเมื่อไร / แก้เสร็จเมื่อไร (เวลา + timezone convention ตาม DATA_MODEL_SPEC)
- Scenario: RB-0x; run_id ที่เกี่ยวข้อง; reference_date
- ผลกระทบ: dashboard/ตัวเลขที่เกี่ยวข้อง; ผู้ใช้ที่เห็นข้อมูลผิดหรือเก่า; ถูกนำไปใช้ในที่ประชุมหรือไม่
- ตรวจพบโดย: alert (AL-xx / AN-xx) หรือคนแจ้ง

### Timeline
| เวลา | เหตุการณ์ | ผู้ดำเนินการ (role) |

### Root Cause
- สาเหตุที่แท้จริง (ไม่ใช่อาการ); เป็น source/contract, pipeline, dashboard, หรือ process
- ทำไมไม่ถูกจับก่อน (rule/alert ที่ขาดหรือยังเป็น null)

### Detection & Response Assessment
- เวลาจริงเทียบ Response Time SLA (ยัง `null` -> บันทึกค่าจริงเพื่อใช้ calibrate)

### Action Items
| # | การป้องกัน | Owner (role) | กำหนด | อ้างอิง (test / DQ- / AL- / changelog) |

### Doc/Changelog Impact
- ต้องเพิ่ม/แก้ rule, threshold, test, หรือบันทึก ANALYTICS_CHANGELOG (นิยามหรือตัวเลขเปลี่ยน) หรือไม่
```

Action item ที่เป็นการปรับ threshold ต้องย้ายไปแก้ค่าใน doc เจ้าของ (DATA_QUALITY.md / SLA_FRESHNESS.md) ไม่ใส่ค่าที่นี่

## Retention Enforcement & Archival

เอกสารนี้เป็นเจ้าของ **ขั้นตอนปฏิบัติ** เท่านั้น นโยบาย/ค่า retention เป็นของ DATA_GOVERNANCE.md (GOV-RET-01..08) ซึ่งทุกค่าเป็น `null` (owner `{{DPO_OR_LEGAL}}` และอื่น ๆ) — **จนกว่าจะมีค่า ไม่ต้องเปิดใช้ job purge ใด ๆ และห้ามลบข้อมูลตามค่าเดา** job ด้านล่างเป็น design ที่ยังไม่มีโค้ด (`[DESIGN PROPOSAL]`)

### Scheduled purge/archive jobs

| Job | บังคับ retention ของ | ทำอะไร (ตาม DATA_GOVERNANCE Deletion Procedure) | Schedule | Owner |
|---|---|---|---|---|
| JOB-RET-01 `purge_expired_runs` | GOV-RET-02 `raw_actions`, GOV-RET-03 `stg_actions`, GOV-RET-04 `ingestion_runs`, GOV-RET-05 `data_quality_results`, GOV-RET-06 `executive_summaries` | เลือก `run_id` ที่เกิน retention (ต้องไม่ใช่ latest successful run); ลบตามลำดับ FK: `data_quality_results` -> `stg_actions` -> `raw_actions` -> `executive_summaries` -> `ingestion_runs`; ทำใน transaction; บันทึก row count | `null` (ไม่มี scheduler — เริ่มเป็นรันด้วยมือโดย Primary on-call) | `{{DATA_STEWARD}}` |
| JOB-RET-02 `compact_db_file` | ทุกตารางข้างต้น | DuckDB ไม่คืนพื้นที่ทันที — rebuild ไฟล์ (export/import หรือ `CHECKPOINT` ตามผลทดสอบ; วิธียืนยันแล้ว = `null`) เพื่อไม่ให้ข้อมูลที่ลบค้างในไฟล์/backup | หลัง JOB-RET-01 | `{{DATA_STEWARD}}` |
| JOB-RET-03 `purge_source_csv` | GOV-RET-01 CSV ต้นทาง (และสำเนา/backup ที่ผูกกับ run) | ลบ/archive ไฟล์ตามปลายทางเมื่อหมดอายุ (`null` — archive vs delete) | พร้อม JOB-RET-01 | `{{DATA_STEWARD}}` |
| JOB-RET-04 `purge_audit_log` | GOV-RET-08 audit log | ลบ/archive log ที่หมดอายุ | `null` | `{{AUDIT_OWNER}}` |
| (ไม่มี job) | GOV-RET-07 `app_config` | ไม่มี personal data — เก็บตลอดอายุระบบ | n/a | - |

ทุก job ต้อง: (1) dry-run แสดงรายการที่จะลบก่อน (2) สำรองไฟล์ DB ก่อนลบครั้งแรก/ทุกครั้งจนกว่า restore drill จะผ่าน (3) ใช้ writer เดียว (หยุด dashboard) (4) บันทึกใน change log (GOV-AUD-02) **ไม่มี rollback หลัง commit** นอกจากย้อนจาก backup — ระบุให้ผู้อนุมัติทราบก่อนรัน

### Archival path

มี cold storage หรือไม่ = `null` (decision: `{{DPO_OR_LEGAL}}` + `{{PROJECT_SPONSOR}}`; DATA_GOVERNANCE Archival Policy) ปัจจุบัน **ไม่มี archive** — ปลายทางเมื่อหมดอายุที่เป็นไปได้คือ delete เท่านั้น ถ้าตัดสินใจให้มี archive:

| หัวข้อ | ค่า |
|---|---|
| Format | `null` (ข้อเสนอ: Parquet จาก DuckDB `COPY ... TO`, `[DESIGN PROPOSAL]` — ต้อง owner ยืนยัน) |
| Location | `null` (ต้องอยู่ภายใต้ access control และ residency เดียวกัน — CON-17 = `null`) |
| Restore | คัดลอกไฟล์ archive กลับ -> `COPY`/`read_parquet` เข้าตารางชั่วคราว ตรวจกับ DQ-10 และ schema ปัจจุบัน -> ห้ามเขียนทับ latest successful run -> บันทึก access log (GOV-AUD-01) ขั้นตอนที่ทดสอบแล้ว = ยังไม่มี |
| Erasure | archive ทุกชิ้นต้องอยู่ในขอบเขต PDPA erasure ด้านล่าง; ต้องมี index ว่า archive ใดมี `run_id` ใด เพื่อให้ลบได้ |

### Monitoring

ไม่มี monitoring ในระบบ (ไม่มี scheduler/alert tooling) — ที่ตั้งใจ (ช่องทาง/ผู้รับ = `null`, owner `{{DATA_STEWARD}}`):

- purge/compact job ล้มเหลว: exit code != 0 หรือ transaction rollback -> เปิดเหตุ `SEV3` (หรือ `SEV2` ถ้าเลยกำหนดลบตาม PDPA)
- volume ผิดปกติ: จำนวนแถวที่ลบต่อ job เทียบกับที่ dry-run ระบุ ต้องตรงกัน; ถ้าต่างหรือลบ `run_id` ที่เป็น latest successful -> หยุดทันที, `SEV1`; threshold เชิงปริมาณ = `null` (ต้องมี history)
- ตรวจหลังลบ: DQ-10 ของ run ที่เหลือยังผ่าน และ dashboard ยังแสดง latest successful run
- จำนวนแถวสะสมต่อ run โตเร็ว (CON-11 = 14,013 แถวต่อ run ใน sample; CON-12/13 = `null`) — ใช้เป็นสัญญาณให้ calibrate retention

### PDPA erasure request

กรอบ: **PDPA (ประเทศไทย)** ไม่ใช่ GDPR; การจัดประเภท `owner`/`action_name` เป็น personal data ยังไม่ตัดสิน (GOV-OPEN-01, `{{DPO_OR_LEGAL}}`) ใช้ Path A (ระมัดระวัง) จนกว่าจะมีคำตัดสิน SLA การตอบ = `null` (owner `{{DPO_OR_LEGAL}}`) ขั้นตอน (ลำดับตาม DATA_GOVERNANCE Erasure Mechanics):

1. รับคำขอ -> เปิด erasure record (request id, วันรับ) — **ไม่เก็บค่า personal data ที่ลบแล้ว** ในหลักฐาน; แจ้ง `{{DPO_OR_LEGAL}}`
2. ระบุข้อมูลของ data subject: ค้นด้วย `owner` ในทุกตารางและทุก `run_id`; การค้นใน `action_name` (ข้อความอิสระ) = `null` วิธี (owner `{{DATA_STEWARD}}`)
3. หยุด dashboard (single writer) และ **สำรองไฟล์ DB** (backup ที่สร้างตอนนี้เองก็ต้องถูกลบ/ทำซ้ำหลังลบ)
4. ลบตามลำดับ: `stg_actions`/`raw_actions` ทุก `run_id` -> `data_quality_results` (`record_key`/`message`) -> `executive_summaries.summary_text` ที่สร้างจากข้อมูลนั้น -> export/ไฟล์ดาวน์โหลดและ Dash cache -> AI provider context ที่ส่งไปแล้ว (ขึ้นกับสัญญา provider = `null`) -> **archive/cold storage/backup** -> CSV ต้นทางและสำเนา
5. rebuild ไฟล์ DB (JOB-RET-02) เพื่อไม่ให้ข้อมูลค้างในไฟล์; ตรวจว่า backup/archive ทุกชุดที่เคยสร้างถูกจัดการ — **จุดที่ย้อนกลับไม่ได้**
6. ผลข้างเคียง: ตัวเลขของ run เก่าเปลี่ยน — บันทึก ANALYTICS_CHANGELOG และ reconcile DQ-10 (ทางเลือก: แทน `owner` ด้วย token ได้เมื่อ `{{DPO_OR_LEGAL}}` ยืนยันว่าไม่ใช่ personal data อีกต่อไป)
7. ปิด erasure record: วันเสร็จ, ตาราง/`run_id`, จำนวนแถวก่อน/หลัง, ผู้ดำเนินการ, ผู้ตรวจสอบ; ที่เก็บและ retention ของหลักฐาน = `null` (owner `{{DPO_OR_LEGAL}}`)
8. ทำ PIR เป็น `SEV1` ถ้าพบว่าข้อมูลยังเหลือในพื้นที่ใดพื้นที่หนึ่ง

## Open Questions

1. ผู้ถือบทบาท Primary/Secondary on-call จริง, ช่องทางติดต่อ, และเวลา response ต่อ `incident_severity` — `{{PROJECT_SPONSOR}}`
2. กลไกบังคับสร้าง run ใหม่จากไฟล์ + `reference_date` เดิม (ไม่มี `--force` ใน design) และคำสั่งปิด run `running` ค้าง — เจ้าของ PIPELINE_SPEC (`{{DATA_STEWARD}}`)
3. วิธีป้องกันการชนกันของไฟล์ DuckDB ระหว่าง ingest กับ dashboard (PIPELINE_SPEC Open Question 3)
4. ค่า RTO/RPO, ความถี่ backup/drill, ตำแหน่งและวิธี backup — `{{PROJECT_SPONSOR}}` + `{{DATA_STEWARD}}`
5. ค่า retention GOV-RET-01..08, นโยบาย archive และ SLA คำขอลบ — `{{DPO_OR_LEGAL}}`, `{{AUDIT_OWNER}}`
6. ยืนยัน enum `incident_severity` (SEV1/SEV2/SEV3) และอัปเดตสถานะใน BUSINESS_GLOSSARY Enumeration Registry (ปัจจุบัน `pending`)
7. dry-run scenario RB-01..RB-07 และ JOB-RET-01..04 ที่ยังไม่ได้ยืนยัน (ดูแบนเนอร์สถานะด้านบน) แล้วบันทึกผลที่นี่ — ตอนนี้ส่วนที่ยืนยันแล้วคือที่ครอบด้วย test เท่านั้น
