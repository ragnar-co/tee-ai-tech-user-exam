# SLA / Freshness Spec

```yaml
doc_id: sla_freshness
filename: SLA_FRESHNESS.md
version: 1.0.0
status: draft
depends_on: [pipeline_spec]
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

เอกสารนี้เป็นเจ้าของ **freshness SLA** ของ pipeline/dataset/dashboard และ enum `dataset_criticality` ตัวเลขทุกตัว (tolerance, latency, threshold, ความถี่ alert, เวลา escalate) = `null` พร้อม calibration source และ owner — ไม่มีค่าที่ plan.md หรือ producer กำหนดไว้ จึงไม่ตั้งค่าเอง Stage/Pipeline ID อ้างตาม PIPELINE_SPEC.md (`pipeline_spec`) ฝั่ง producer (DC-SLA-01..04) อยู่ที่ DATA_CONTRACT.md (`data_contract`) ไม่ซ้ำที่นี่

> **สถานะ (2026-10-02):** pipeline PL-01 implement แล้ว (รันด้วยมือ on-demand) แต่ **ไม่มี scheduler และไม่มี monitoring/alert ใด ๆ รันอยู่** — ข้อกำหนด FR-*/AL-* ทั้งหมดยังเป็น design ที่ไม่มีกลไกตรวจจริง (dashboard แสดง reference date/loaded timestamp ให้คนดูเอง). ไม่มี SLA compliance metric (CON-09 — ห้ามสร้าง); เอกสารนี้ระบุ "ข้อกำหนดความสด" ไม่ใช่ตัวชี้วัดผลงานของใคร

## Freshness Requirements per Dataset

**Freshness ≠ Completeness ≠ Correctness:** freshness = ข้อมูลมาถึงตรงเวลาไหม (เอกสารนี้); completeness = แถวที่ควรมีครบไหม (DATA_QUALITY.md `data_quality`, DC-SLA-04); correctness = ตัวเลขที่คำนวณถูกไหม (TESTING_STRATEGY.md metric validation) dashboard สดและครบแต่ผิดได้ ทั้งสามต้องมี alert คนละตัวและเจ้าของคนละคน — ตารางด้านล่างครอบคลุมเฉพาะ freshness

### Enum `dataset_criticality` (owner: SLA_FRESHNESS.md)

| value | ความหมาย |
|---|---|
| `P0` | business-critical — ผู้ใช้ตัดสินใจจากข้อมูลนี้ในการประชุมประจำสัปดาห์ |
| `P1` | informational สำคัญ — ใช้ตรวจย้อนรอย/วินิจฉัย |
| `P2` | informational — มีก็ดี (bonus) |

### Freshness SLA Register

Cadence: **weekly หลังการประชุม** (`DC-SLA-01`, STAKEHOLDERS Freshness requirement) ไม่มี source timestamp ใน CSV; เวลาที่วัดได้มีเพียง `ingestion_runs.started_at / completed_at` (ฝั่ง ingest) และ `reference_date` (ต่อ run) ดังนั้น "อายุข้อมูล" วัดจาก `completed_at` ของ latest successful run เท่านั้น ไม่ใช่เวลาที่ producer สร้างข้อมูล

| SLA ID | Dataset / Pipeline | Refresh frequency | `dataset_criticality` | Dashboard ที่พึ่ง (placeholder) | Escalation contact |
|---|---|---|---|---|---|
| FR-01 | PL-01 `csv_ingest` -> latest successful run (`ingestion_runs` status `succeeded`) | weekly หลังประชุม (ผู้รัน manual; cron = `null` ตาม PIPELINE_SPEC Schedule) | `P0` | `DASH-01`, `DASH-02` | `{{DATA_STEWARD}}` |
| FR-02 | `stg_actions` (PL-01 ST-06; แหล่ง Q-PORTFOLIO / Q-BY-PROJECT / Q-OVERDUE-DETAIL / Q-BY-OWNER) | ตาม FR-01 (เขียนใน transaction เดียวกับ run) | `P0` | `DASH-01`, `DASH-02` | `{{DATA_STEWARD}}` |
| FR-03 | `raw_actions` (PL-01 ST-05) | ตาม FR-01 | `P1` | ไม่มี (ใช้ reconcile DQ-10 และตรวจย้อนรอย) | `{{DATA_STEWARD}}` |
| FR-04 | `ingestion_runs` + `data_quality_results` (ST-03/ST-04/ST-08) | ตาม FR-01 (รวม run `failed`) | `P1` | `DASH-01` (ถ้าแสดง run_id / reference_date) | `{{DATA_STEWARD}}` |
| FR-05 | PL-02 `executive_summary_generate` -> `executive_summaries` (bonus) | on-demand ไม่มี cron (`n/a`); ต้องอ้าง `source_run_id` = latest successful run | `P2` | `DASH-03` | `{{DATA_STEWARD}}` |

หมายเหตุ: ทุก pipeline ใน PIPELINE_SPEC (PL-01, PL-02) มี entry; Q-* เป็น read path ไม่ใช่ pipeline เขียน จึงรับความสดผ่าน FR-02 ID ของ dashboard อ้างตาม DASHBOARD_SPEC.md: `DASH-01` Portfolio Overview, `DASH-02` Overdue Actions, `DASH-03` Executive Summary (bonus)

**Staleness ของ dashboard:** dashboard ต้องแสดงสิ่งที่พิสูจน์ความสดได้ — `run_id`, `reference_date`, `completed_at` ของ latest successful run (ข้อมูลมีอยู่ใน `ingestion_runs`) เพื่อให้ผู้ใช้เห็นว่าตัวเลขมาจากสัปดาห์ใด รูปแบบการแสดง = DASHBOARD_SPEC

## Delay Tolerance Matrix

| SLA ID | Delay tolerance | Measurement window | Business impact of delay |
|---|---|---|---|
| FR-01 | `null` | จากเวลา CSV พร้อม/ประชุมจบ (`DC-SLA-02` latency) ถึง `ingestion_runs.completed_at` ของ run `succeeded` | ที่ประชุมถัดไปใช้ตัวเลขของสัปดาห์ก่อน; การตัดสินใจ follow-up overdue อิงข้อมูลเก่า (overdue คำนวณจาก `reference_date` ของ run นั้น ไม่เปลี่ยนตามเวลาจริง) |
| FR-02 | `null` | ตาม FR-01 | ตัวเลข `overdue_actions` / `days_overdue` บน dashboard ล้าหลังความจริง — ไม่มีการเตือนผู้ใช้ถ้าไม่แสดง `reference_date` |
| FR-03 | `null` | ตาม FR-01 | ไม่กระทบผู้ใช้ปลายทางโดยตรง; ตรวจย้อนรอย/reconcile ทำไม่ได้จนกว่าจะโหลด |
| FR-04 | `null` | ตาม FR-01 | ไม่เห็นเหตุผลที่ run ล้มเหลว (run `failed` ไม่เป็น latest successful run) |
| FR-05 | `null` | จาก `completed_at` ของ source run ถึง `executive_summaries.created_at`-เทียบเท่า (ชื่อคอลัมน์ตาม DATA_MODEL_SPEC) | summary อ้าง run เก่ากว่า latest — ต้อง label draft และแสดง `source_run_id` |

Calibration (ทุก tolerance ข้างบน): source = ข้อตกลงเรื่องวัน/เวลาส่ง CSV หลังประชุมกับ `{{MEETING_CHAIR}}` และ `{{PRODUCER_TEAMS}}` (DC-SLA-01/02) บวกประสบการณ์จริงหลายรอบ; owner = `{{DATA_STEWARD}}` (ผู้เห็นชอบ `{{MEETING_CHAIR}}`) ห้ามใช้ค่าจาก mock CSV (มีไฟล์เดียว ไม่มี timestamp)

## Alert Rules

ตรวจ "ไม่สด" 2 แบบ ที่ต่างกันที่เจ้าของ: (A) **ไม่มี run ใหม่ภายใน tolerance** (CSV ไม่มาหรือไม่ถูกรัน) และ (B) **run ล่าสุด `failed`** (CSV ถูกปฏิเสธ/reconcile ไม่ตรง) — (B) มีสาเหตุที่ PIPELINE_SPEC Error Handling อยู่แล้ว; alert ที่นี่ไม่แทนที่ DQ finding

| Alert ID | เงื่อนไข | SLA | Alert threshold | Alert channel | Alert frequency (ถ้ายังไม่ resolved) |
|---|---|---|---|---|---|
| AL-01 | (A) อายุของ latest successful run (`now - completed_at`) เกิน tolerance | FR-01, FR-02 | `null` | `null` | `null` |
| AL-02 | (B) run ล่าสุดของสัปดาห์ = `failed` (`ingestion_run_status`; exit code 1/3) | FR-01, FR-04 | พบ 1 run ที่ `failed` ที่ยังไม่มี run `succeeded` ตามหลัง `[DESIGN PROPOSAL]` | `null` (ขั้นต่ำที่ออกแบบไว้ = exit code + stderr/stdout + แถว `failed`; ตาม PIPELINE_SPEC Failure alert) | `null` |
| AL-03 | ไม่มี run `succeeded` เลย (dashboard ว่าง) | FR-01 | พบเงื่อนไข ณ เวลาเปิด dashboard `[DESIGN PROPOSAL]` | ข้อความบน dashboard | n/a (แสดงต่อเนื่อง) |
| AL-04 | PL-02: summary อ้าง `source_run_id` ที่ไม่ใช่ latest | FR-05 | `null` | label บน UI | n/a |

- Calibration ของ threshold/ช่องทาง/ความถี่: source = ข้อตกลง tolerance (Delay Tolerance Matrix) และเครื่องมือแจ้งเตือนที่องค์กรมี (ปัจจุบันไม่มี scheduler/monitoring/on-call — ไม่มี "page" จริง); owner = `{{DATA_STEWARD}}`
- Alert ต้องแยกจาก completeness (DATA_QUALITY) และ correctness (TESTING_STRATEGY): AL-01..AL-04 ห้ามถูกใช้แทน DQ finding หรือผลทดสอบ metric
- ไม่มี "alert threshold = เมื่อใดเรียก on-call": ไม่มีรายชื่อ on-call; ใช้ role placeholder ด้านล่าง

## Escalation Procedures

ขั้นตอนลงมือจริงอยู่ที่ RUNBOOK.md; ที่นี่เป็นเจ้าของเฉพาะ "เมื่อไรต้อง escalate และใครรับ"

| ลำดับ | ผู้รับ (role placeholder) | Contact | Trigger | Escalation timeline |
|---|---|---|---|---|
| L1 First Responder | `{{DATA_STEWARD}}` (STK-06; ผู้รัน `src.ingest`) | `null` (ช่องทางติดต่อ ยังไม่กำหนด) | AL-01 / AL-02 | -- |
| L2 | `{{MEETING_CHAIR}}` (STK-01) และ `{{PRODUCER_TEAMS}}` ถ้าสาเหตุคือ CSV ไม่มา/ถูกปฏิเสธ | `null` | L1 ยัง unresolved เกิน `null` นาที | `null` |
| L3 Management notification | `{{CYBERSECURITY_PROGRAM_OFFICE}}` ผู้รับผิดชอบโครงการ (รายชื่อ = `null`) | `null` | unresolved จนเลยการประชุมรอบถัดไป หรือเกิน `null` | `null` |

- Calibration: เวลา escalate/เกณฑ์แจ้ง management — source = tolerance ที่ตกลงและรอบประชุมจริง; owner = `{{DATA_STEWARD}}` ร่วม `{{MEETING_CHAIR}}` ผู้รับ L2/L3 ต้องยืนยันก่อนเปลี่ยนสถานะเป็น approved
- การแก้ไขที่ต้องอาศัย producer (CSV ผิด) = ประสานผ่านสัญญา `data_contract`; การเปลี่ยนตัวเลข/นิยามที่เกิดจากการ re-run = ANALYTICS_CHANGELOG
- Operational counterpart (RUNBOOK.md มีอยู่แล้ว): RUNBOOK ควรครอบคลุม scenario ที่ผูกกับ AL-01 (ไม่มี run ใหม่), AL-02 (run `failed`), AL-03 (ไม่มี run สำเร็จ) ตามที่ PIPELINE_SPEC ระบุแล้ว (scenario 1, 4)

## Open Questions

1. วัน/เวลา/ช่องทางที่ CSV ถูกส่งหลังประชุม (`{{MEETING_CHAIR}}`, `{{PRODUCER_TEAMS}}`) -> delay tolerance FR-01..FR-05
2. มีเครื่องมือ monitoring/แจ้งเตือน/on-call จริงหรือไม่ (ไม่มี scheduler ใน CON-03/04) -> ช่องทางและความถี่ alert; `{{DATA_STEWARD}}`
3. ผู้รับ L2/L3 และเวลา escalation (`{{MEETING_CHAIR}}`, `{{CYBERSECURITY_PROGRAM_OFFICE}}`)
4. ID dashboard ยืนยันแล้วกับ DASHBOARD_SPEC (`DASH-01`, `DASH-02`, `DASH-03`); ให้ dashboard แสดง `run_id`/`reference_date`/`completed_at`
5. ยืนยัน enum `dataset_criticality` P0/P1/P2 และการจัดระดับ FR-01..FR-05; อัปเดตสถานะใน BUSINESS_GLOSSARY Enumeration Registry (ตอนนี้ `pending`)
