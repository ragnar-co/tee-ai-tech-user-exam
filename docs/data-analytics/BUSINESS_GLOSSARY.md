# Business Glossary

```yaml
doc_id: business_glossary
filename: BUSINESS_GLOSSARY.md
version: 1.0.0
status: draft
depends_on: []
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

เอกสารนี้เป็น **naming authority**: ชื่อ metric (METRIC_SPEC), ชื่อ column (DATA_MODEL_SPEC) และ label บน dashboard ต้องตรงกับที่นี่ ถ้าไม่ตรง ให้แก้เอกสารอื่น

## Term Definitions

| Term (canonical name) | Official Definition | Common Misunderstanding | Authoritative Source |
|---|---|---|---|
| Action Item (`action`) | งานที่ได้รับมอบหมายจากการประชุมประจำสัปดาห์ หนึ่งแถวใน CSV = หนึ่ง action ระบุด้วย `action_id` | คิดว่าเป็น task ในระบบ workflow จริง — ที่นี่เป็นข้อมูลอ่านอย่างเดียว (read-only analytics) | plan.md §1, §3 |
| `action_id` | ตัวระบุ action ที่ต้อง unique ภายในไฟล์ input | คิดว่า unique ข้ามทุกสัปดาห์ — ยืนยันได้แค่ภายในไฟล์ (DQ-03); ข้าม run ไม่ทราบ | plan.md §15 |
| Project (`project_name`) | ชื่อโครงการรูปแบบ `Pxx - ชื่อ` ตามที่ปรากฏใน source ใช้เป็น key ตามเดิม | คิดว่า Pxx เป็นรหัสที่ระบบสร้างให้ — ใช้ค่าตามที่ source ให้ | plan.md §3 |
| Owner (`owner`) | ตัวระบุผู้รับผิดชอบ action ตาม source (pseudonymous `Owner-NNN`) | เป็นชื่อบุคคลจริง / บ่งชี้ผลงาน — เป็นเพียง ID ไม่ใช่คะแนนผลงาน | plan.md §3, §21 |
| Due Date (`due_date`) | วันครบกำหนดของ action รูปแบบ ISO `YYYY-MM-DD` เป็นวันที่ปฏิทิน ไม่มีเวลา | มีเวลา/timezone — ไม่มี | plan.md FR-02 |
| Status (`status`) | สถานะของ action ตามค่าที่ source ให้ ไม่ map ค่าใหม่เอง ค่าที่อนุญาตเป็นของ enum `action_status` (ดู Registry) | คิดว่า status ครบตาม workflow ทั่วไป — ห้าม invent enum นอก source | plan.md FR-02 |
| Reference Date (`reference_date`) | วันที่เดียวทั้งระบบที่ใช้คำนวณ overdue และ days_overdue ส่งผ่าน `--reference-date` เก็บต่อ run; ค่าปัจจุบัน `2026-10-02` = fixed constant for iteration 1 (เปลี่ยนผ่าน ANALYTICS_CHANGELOG เท่านั้น) | คือ "วันนี้" ของระบบ — ไม่ใช่; ห้ามใช้ `date.today()` | plan.md §2 |
| Completed Action | action ที่ `status = 'done'` (flag `is_completed`) | คิดว่าปิดตรงเวลา — ไม่ได้บอกว่าตรงเวลา (ไม่มี completion date ใน source) | plan.md §9.3, §20 |
| Open Action | action ที่ `status != 'done'` (flag `is_open`) — รวมสถานะที่ยังไม่เสร็จทั้งหมด ไม่ใช่เฉพาะ in-progress | คิดว่า open = in_progress อย่างเดียว | plan.md §20 |
| Overdue Action | open action ที่ `due_date < reference_date` (flag `is_overdue`); `due_date = reference_date` **ไม่ถือว่า overdue** | นับ done ที่ due ผ่านแล้ว หรือนับวัน due = reference | plan.md FR-05 |
| Days Overdue (`days_overdue`) | จำนวนวันปฏิทินจาก due_date ถึง reference_date เฉพาะ overdue action; ค่า > 0 | คิดว่านิยามสำหรับ non-overdue เป็น 0 ที่มีความหมาย — ใน `stg_actions` เก็บ 0 เป็นค่าเริ่มต้นเท่านั้น | plan.md FR-06 |
| `owners_with_overdue_actions` | จำนวน owner ที่ไม่ซ้ำซึ่งถือ overdue action อย่างน้อยหนึ่งรายการใน scope (MET-07, KPI-03) | คิดว่าเป็นจำนวนคนที่ผลงานไม่ดี — เป็นเพียงตัวนับภาระ follow-up ไม่ใช่คะแนนผลงาน | METRIC_SPEC.md |
| `open_not_overdue_actions` | Open Action ที่ยังไม่ overdue = `open_actions − overdue_actions` (MET-08, KPI-02) | คิดว่าเป็น in_progress — รวมทุกสถานะที่ไม่ใช่ done และ due_date >= reference_date | METRIC_SPEC.md |
| Project Filter (`project_name` parameter) | พารามิเตอร์ dimension ที่ทุก query/metric รับ (NULL / `All Projects` = ทั้งหมด) ใช้ **จำกัดแถว**; ไม่ใช่การ highlight และไม่ใช่ KPI ใหม่ | คิดว่า filter มีผลเฉพาะบางหน้า/บาง metric — มีผลกับทุก metric | plan.md; METRIC_SPEC.md |
| Completion Rate (`completion_rate`) | completed_actions / total_actions ใน scope เดียวกัน (optional) | คิดว่าเป็น on-time rate — ไม่ใช่ (ไม่มีวันที่เสร็จ) | plan.md FR-04 |
| Ingestion Run (`run_id`) | การโหลด CSV หนึ่งครั้งพร้อม metadata (source_hash, reference_date, row counts) | คิดว่าโหลดซ้ำจะทับข้อมูล — ใช้ run versioning (Strategy B) | plan.md §17 |
| Latest Successful Run | run ล่าสุดที่โหลดสำเร็จ ซึ่งเป็นตัวขับ dashboard | คิดว่าเป็น run ล่าสุดเสมอ — run ที่ล้มเหลวไม่นับ | plan.md §17 |
| Data Quality Finding | ผลตรวจ DQ ต่อ record/ไฟล์ บันทึกใน `data_quality_results`; ระดับ classification เป็นของ `rule_severity` | คิดว่าแถวผิดจะถูกตัดทิ้ง — ห้ามทิ้งเงียบ ๆ | plan.md §9.4, §15 |
| Executive Summary (draft) | ข้อความสรุปที่ AI สร้างจากข้อมูล DuckDB เป็น draft (bonus) ห้ามอ้าง severity/impact/SLA | คิดว่าเป็นการประเมินความเสี่ยง — ไม่ใช่ | plan.md §5 |
| KPI / Metric / Dimension | KPI = ผลลัพธ์ที่มีเจ้าของ (KPI_DICTIONARY); metric = ตัวเลขที่คำนวณ (METRIC_SPEC); dimension = สิ่งที่ใช้ซอย | เรียก metric ว่า KPI ก่อนมี owner/target อนุมัติ | plan.md §20 |
| Candidate KPI | KPI ที่นิยามแล้วแต่ยังไม่มี owner/target อนุมัติ (`target = null`) | คิดว่าเป็น target ทางการ | KPI_DICTIONARY.md |

### Label บน dashboard (naming authority)

| Concept | metric / column name | Dashboard label |
|---|---|---|
| total | `total_actions` | Total Actions |
| completed | `completed_actions` | Completed |
| open | `open_actions` | Open |
| overdue | `overdue_actions` | Overdue |
| days overdue | `days_overdue` | Days Overdue |
| completion rate | `completion_rate` | Completion Rate |
| owners with overdue | `owners_with_overdue_actions` | Owners with Overdue |
| open not overdue | `open_not_overdue_actions` | Open (Not Overdue) |

## Disputed Terms

หมายเหตุ: ไม่มีบันทึกข้อพิพาทจริงระหว่างทีมใน input; ต่อไปนี้คือ **ความกำกวมที่คาดว่าจะเกิด** (`[ASSUMPTION]`) ที่ plan.md ตัดสินไว้แล้ว — Official Resolution ยัง **ไม่ได้รับ approve** (approval date = `null`)

| Disputed Term | Competing Definitions | Official Resolution (ตาม plan.md) | Decision Owner |
|---|---|---|---|
| Overdue | (a) due_date <= วันนี้ (b) due_date < reference_date | (b): due == reference **ไม่ใช่** overdue; เฉพาะ open | `{{PROJECT_SPONSOR}}` — approval date `null` |
| Open vs In Progress | (a) open = in_progress (b) open = ไม่ใช่ done | (b) open = `status != 'done'` | `{{PROJECT_SPONSOR}}` — `null` |
| Today vs Reference Date | (a) ใช้วันที่ระบบ (b) ใช้ค่าเดียวที่ประกาศ | (b) `REFERENCE_DATE` เดียว เก็บต่อ run; ค่า 2026-10-02 ยืนยันแล้วสำหรับ iteration 1 | `{{PROJECT_SPONSOR}}` — `null` |
| Completion Rate vs On-time Rate | (a) สัดส่วน done (b) สัดส่วน done ตรงเวลา | (a) เท่านั้น; on-time rate ห้ามสร้าง (ไม่มีวันที่เสร็จ) | `{{PROJECT_SPONSOR}}` — `null` |

## Change Log

| Changed Term | Change Date | Old -> New | Reason |
|---|---|---|---|
| (เริ่มต้น v1.0.0 — ยังไม่มีการเปลี่ยนนิยาม) | - | - | - |

การเปลี่ยนนิยามหลัง metric ถูกรายงานแล้ว = breaking change ต้องบันทึกใน ANALYTICS_CHANGELOG

## Enumeration Registry

ดัชนี enum ที่โปรเจกต์นี้เป็นเจ้าของ — **ตารางนี้ไม่มีค่า enum** มีเฉพาะชื่อ enum กับเอกสารเจ้าของ ค่าจริงอยู่ในเอกสารเจ้าของเท่านั้น (ตรวจสอบรอบสองแล้ว: เอกสารเจ้าของทุกฉบับมีอยู่และนิยามค่า enum ของตนจริง)

| Enum | Owner doc ID | Owner file | สถานะเอกสารเจ้าของ |
|---|---|---|---|
| `data_literacy_level` | stakeholders | STAKEHOLDERS.md | defined |
| `data_need_priority` | stakeholders | STAKEHOLDERS.md | defined |
| `metric_status` | metric_spec | METRIC_SPEC.md | defined |
| `scd_type` | data_model_spec | DATA_MODEL_SPEC.md | defined |
| `pdpa_classification` | data_model_spec | DATA_MODEL_SPEC.md | defined |
| `action_status` (ค่าสถานะ action จาก source — เพิ่มเฉพาะโปรเจกต์) | data_model_spec | DATA_MODEL_SPEC.md | defined |
| `ingestion_run_status` (`ingestion_runs.status`) | data_model_spec | DATA_MODEL_SPEC.md | defined |
| `rule_severity` (รองรับการจัดระดับผลตรวจใน `data_quality_results`) | data_quality | DATA_QUALITY.md | defined |
| `chart_type` | viz_design_spec | VIZ_DESIGN_SPEC.md | defined |
| `complexity_level` | viz_design_spec | VIZ_DESIGN_SPEC.md | defined |
| `dataset_criticality` | sla_freshness | SLA_FRESHNESS.md | defined |
| `model_status` | ai_model_spec | AI_MODEL_SPEC.md | defined |
| `change_type` | analytics_changelog | ANALYTICS_CHANGELOG.md | defined |
| `work_item_status` | tasks | TASKS.md | defined |
| `incident_severity` | runbook | RUNBOOK.md | defined |

**Registry Rule:** ห้ามมีค่า enum ในตารางนี้ **Cross-Document Consistency:** เอกสารอื่นอ้างชื่อ enum + เอกสารเจ้าของ ไม่ประกาศค่าซ้ำ; เพิ่มค่าใหม่ที่เอกสารเจ้าของ แล้ว propagate ผ่าน registry; การจัดระดับผลตรวจใน plan.md §9.4 เป็น implementation classification ที่จะ reconcile เข้า `rule_severity` (DATA_QUALITY.md มีแล้ว)
