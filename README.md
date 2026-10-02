# Cybersecurity Project Action Dashboard

แอปรับไฟล์ CSV ของ Action Items หลังประชุมประจำสัปดาห์ → ตรวจสอบข้อมูล → เก็บใน **DuckDB** → แสดงจำนวนงานทั้งหมด / งานเสร็จ / งานเลยกำหนดแยกตามโครงการ พร้อมรายการงานเลยกำหนดที่ระบุผู้รับผิดชอบและจำนวนวันที่ล่าช้า ผู้ใช้เลือกดูรายโครงการได้ (Plotly Dash)

โบนัส: สร้างร่าง **Executive Summary** จากข้อมูลใน DB ด้วย LLM (OpenRouter) บันทึกลง DB และแสดงบนแอป

> **สถานะ (2026-10-02):** implement ครบทั้ง core และ bonus และผ่าน `pytest` (277 passed, `ruff` สะอาด ณ เวลาที่เขียน) — ดูตาราง [สถานะ](#สถานะการพัฒนา) และ [ข้อจำกัดที่ทราบ](#ข้อจำกัดที่ทราบ) ก่อนใช้งาน การเรียก OpenRouter จริง **ทดสอบสำเร็จแล้ว 2 ครั้ง** (2026-10-02, ผ่าน callback ของแอป) แต่ยังไม่ได้ประเมินคุณภาพร่างอย่างเป็นทางการ

## วันที่อ้างอิง (Reference Date)

ทุกตัวเลข "เลยกำหนด" คำนวณจาก **`2026-10-02`** (ค่าคงที่ที่ตกลงสำหรับ iteration แรก) ส่งผ่าน `--reference-date` และเก็บไว้ต่อ run ใน DuckDB — **ไม่ใช้วันที่ของระบบ**

> โจทย์ต้นฉบับที่ได้รับไม่ได้ระบุวันที่ จึงเป็นสมมติฐานที่ต้องยืนยัน ถ้าโจทย์ระบุวันอื่น ให้ ingest ใหม่ด้วย `--reference-date` นั้น (ตัวเลข overdue จะเปลี่ยน)

## วิธีรัน

### ทางเลือก A — Docker (ยืนยันแล้ว: Docker 29.8.1 / Compose v5.5.1)

```bash
docker compose up --build        # แล้วเปิด http://localhost:8050  (เปลี่ยนพอร์ตฝั่ง host ด้วย HOST_PORT)
docker compose down -v           # ล้างข้อมูล (volume duckdb-data)
```

- image `python:3.12-slim` สอง stage (~495 MB), รันเป็น non-root `appuser` (1001), `gunicorn` 1 worker + 4 threads, `HEALTHCHECK` ที่ `/_dash-layout`
- `docker/entrypoint.sh` รัน `python -m src.ingest` **ทุกครั้งที่ start** (idempotent): start แรก = run_id 1 `succeeded` 14,013 แถว; restart = `noop` ข้อมูลคงอยู่ใน named volume `duckdb-data`; ingest ล้มเหลว = container หยุด (ไม่เสิร์ฟข้อมูลค้าง)
- env ที่ส่งจาก shell หรือไฟล์ `.env` ในเครื่อง: `REFERENCE_DATE` (default `2026-10-02`), `OPENAI_API_KEY` (ว่าง = AI ปิด), `OPENAI_BASE_URL`
- **ข้อควรระวัง:** Compose ส่งต่อ `OPENAI_API_KEY` จาก shell ถ้าตั้งไว้ — `export` เฉพาะเมื่ออยากเปิด AI การกด Generate จะส่งข้อมูลสรุปและแถวงานเลยกำหนด (รวม `owner`/`action_name`) ไปที่ OpenRouter และอาจมีค่าใช้จ่าย
- ใช้ CSV ของตัวเอง: mount ไฟล์แล้วตั้ง `INGEST_INPUT` (ตัวอย่างในคอมเมนต์ของ `docker-compose.yml`)
- ยืนยันในคอนเทนเนอร์แล้ว: `/`, `/overdue`, `/executive-summary` = 200; All Projects 14,013 / 8,597 / 5,416 / overdue 3,531; P01 1,168 / 816 / 352 / 202; รันเป็น `appuser`; สถานะ healthy; ไม่มี key ใน image history; ไม่มี `OPENAI_API_KEY` -> `is_configured()` เป็น False พร้อมข้อความไทย **ยังไม่ได้ตรวจ:** quirk เรื่อง ownership ของ volume บน Windows/Mac, `read_only` rootfs, multi-arch build

### ทางเลือก B — รันในเครื่อง

```bash
# 1) ติดตั้ง
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"            # หรือ: uv venv && uv pip install -e ".[dev]"   (extra "prod" = gunicorn)

# 2) สร้างฐานข้อมูลจาก CSV (สร้างใหม่ได้เสมอ; ingest ไฟล์เดิม+วันที่เดิมซ้ำ = no-op)
python -m src.ingest \
  --input src/tee_cybersecurity_actions_mock.csv \
  --reference-date 2026-10-02

# 3) ทดสอบ
pytest -q

# 4) เปิด dashboard  ->  http://127.0.0.1:8050
python dashboard/app.py
```

ไฟล์ DB: `data/cybersecurity.duckdb` (สร้างตอน ingest; ไม่ commit) หน้า: `/` Portfolio Overview, `/overdue` Overdue Actions, `/executive-summary` (bonus)

**Exit code ของ ingest:** `0` สำเร็จ/no-op; `1` ไฟล์ถูกปฏิเสธ (blocking finding หรือ reconcile ล้มเหลว); `2` argument ผิด / อ่านไฟล์ไม่ได้ / ไฟล์เกิน `INGEST_MAX_BYTES` / ไฟล์ว่างหรือ header-only (ไม่เขียน DB); `3` DB/ระบบผิดพลาด (เช่น DB ถูกล็อก)

**ตัวแปร environment ที่โค้ดอ่าน** (ค่า default เป็นค่าที่โค้ดเลือกเอง ไม่ได้ calibrate):

| ตัวแปร | default | ใช้ที่ |
|---|---|---|
| `INGEST_MAX_BYTES` | 256 MiB | ingest — เพดานขนาดไฟล์ input |
| `DASH_DB_PATH` | `data/cybersecurity.duckdb` | dashboard — ไฟล์ DuckDB |
| `DASH_HOST` / `DASH_PORT` | `127.0.0.1` / `8050` | dashboard |
| `DASH_DEBUG` | ปิด | dashboard (`1`/`true` = เปิด debug) |
| `OPENAI_API_KEY`, `OPENAI_BASE_URL` | ว่าง / — | AI summary (ดูด้านล่าง) |
| `AI_TIMEOUT_SECONDS` | 60 | AI summary — timeout ของ HTTP |
| `AI_TOP_N` | 10 | AI summary — จำนวนแถว overdue ที่ส่งให้โมเดล |

### AI Executive Summary (โบนัส)

ตั้งค่าใน environment (ดู `.env.example`; **ห้าม commit ค่าจริง**):

| ตัวแปร | ความหมาย |
|---|---|
| `OPENAI_API_KEY` | OpenRouter API key |
| `OPENAI_BASE_URL` | เช่น `https://openrouter.ai/api/v1` |

โมเดลคือ `anthropic/claude-sonnet-5` (ค่าคงที่ในโค้ด) เรียก HTTPS ตรงด้วย `httpx` ไม่ใช้ CLI อื่น prompt = `exec-summary-v2` (ผลลัพธ์ 5 ส่วน; มี clause ว่าค่าใน context เป็น untrusted data; ฟิลด์ข้อความอิสระตัด control character และจำกัด 200 ตัวอักษร) ถ้าไม่ตั้งค่า ปุ่ม Generate Draft จะถูกปิดพร้อมข้อความ และ dashboard หลักยังใช้ได้ปกติ ถ้า AI ล้มเหลวจะแสดง error และไม่บันทึกสรุปปลอม

> **ผลการทดสอบจริง (2026-10-02):** เรียก OpenRouter ด้วย key จริงผ่าน callback ของแอป (DB สำเนา, ข้อมูลตัวอย่าง) สำเร็จ 2 ครั้ง — All Projects และ `P01 - Network VA` ใช้เวลา ~21–25 วินาทีต่อครั้ง ได้ร่างภาษาไทย 5 ส่วน บันทึกลง `executive_summaries` (provider `openrouter`, model `anthropic/claude-sonnet-5`, prompt `exec-summary-v2`) และแสดงซ้ำหลังโหลดหน้า ตัวเลขที่ตรวจเทียบกับ DB ตรงกัน (เช่น P03 open 809 / overdue 611) ยังไม่ได้: ประเมินคุณภาพ draft อย่างเป็นทางการ (EV-01..EV-05) และการบันทึก audit `ai_context_send` ลง DB (ตอนนี้เป็น log เท่านั้น) ข้อสังเกต: ข้อความบางช่วงใช้ชื่อฟิลด์ดิบ (เช่น `action_name` แทน "รายการ")

ข้อมูลที่ส่งออกไปยังผู้ให้บริการ: ค่ารวมและแถวงานเลยกำหนดแบบ top-N (รวม `owner` และ `action_name` — เป็น user decision ไม่ใช่การอนุมัติจาก DPO/Legal) — ไม่ส่ง CSV ดิบ ตารางเต็ม หรือ key ประเด็น PDPA / data residency ของการส่งนี้ยังเป็น open item (ดู `docs/data-analytics/DATA_GOVERNANCE.md`)

## นิยามตัวเลข

| ตัวเลข | นิยาม |
|---|---|
| `total_actions` | จำนวน action ทั้งหมดใน scope ที่เลือก |
| `completed_actions` | `status = 'done'` |
| `open_actions` | `status != 'done'` |
| `overdue_actions` | open **และ** `due_date < reference_date` (วันที่เท่ากันยัง **ไม่** เลยกำหนด) |
| `days_overdue` | `date_diff('day', due_date, reference_date)` เฉพาะงานที่ overdue |

สูตรทั้งหมดอยู่ใน SQL (`sql/20_metrics/`) ไม่เขียนซ้ำใน Dash callbacks ตัวกรองโครงการจำกัดแถวของทุก query

## โครงสร้าง

```text
src/                CLI ingest, validation, data-access (metrics), AI (src/ai/)
  tee_cybersecurity_actions_mock.csv   ข้อมูลตัวอย่าง (14,013 แถว, 12 โครงการ)
sql/                schema, staging, metric queries (q_*.sql), quality checks
dashboard/          Dash app: app.py (3 หน้าอยู่ในไฟล์นี้), components/, viz_theme.py (pages/ ว่าง)
tests/              pytest + fixtures (fixture reference date 2026-09-15)
Dockerfile, docker-compose.yml, .dockerignore, docker/entrypoint.sh   (ดูหัวข้อ Docker)
docs/data-analytics/  เอกสาร DDD 23 ฉบับ (เกณฑ์ที่โค้ดต้องตาม) — เริ่มที่ README.md
ddd/                DDD JSON templates (อ่านอย่างเดียว)
plan.md             แผนงานฉบับสรุป
```

## เหตุผลการเลือก

- **DuckDB:** ไฟล์เดียว ไม่ต้องมีเซิร์ฟเวอร์ query แบบวิเคราะห์เร็ว rebuild จาก CSV ได้
- **DDD `ddd-data-analytics` v2.8.0:** งานนี้คือชั้นวิเคราะห์ (validate → store → metric → dashboard) ไม่ใช่การออกแบบแอป workflow ใหม่
- **Run versioning:** แต่ละ ingest มี `run_id` dashboard อ่าน run ล่าสุดที่สำเร็จ → ตรวจย้อนกลับได้

## สถานะการพัฒนา

| ส่วน | สถานะ | ยืนยันด้วย |
|---|---|---|
| Bootstrap (`pyproject.toml`, `.env.example`, venv) | เสร็จ | `pip install -e ".[dev]"` |
| SQL + validation (DQ-01..DQ-12) + ingest + metrics | เสร็จ | pytest (รวม golden fixture, reference-date, idempotency, hardening ~133 test, reconcile CSV vs DuckDB) และ ingest sample จริง 14,013 แถว |
| AI provider (OpenRouter) + บันทึกสรุป | เสร็จ | mocked HTTP ใน pytest + **เรียกจริงสำเร็จ 2 ครั้ง (2026-10-02)** ผ่าน callback ของแอป; ยังไม่มี EV-01..05 |
| Dashboard (`dashboard/app.py`, 3 หน้า) | เสร็จ | Flask test client, server จริง `127.0.0.1:8050` (page load, callback, project filter), และในคอนเทนเนอร์ |
| Docker / Compose | เสร็จ | build + run + healthcheck + ตัวเลขตรงในคอนเทนเนอร์ (Docker 29.8.1) |
| ตัวเลขจริง @ `2026-10-02` | ยืนยัน | total 14,013 / completed 8,597 / open 5,416 / overdue 3,531 / open_not_overdue 1,885 / owners_with_overdue 96 / max days_overdue 46 / 12 โครงการ; P01 = 1,168 / 816 / 352 / 202 |
| ชุดทดสอบ | `pytest -q`: 277 passed, `ruff check .` สะอาด (ณ เวลาที่เขียน; รันซ้ำเพื่อยืนยัน) | ไม่มี CI, ไม่มี browser e2e, ไม่ได้วัด coverage |
| ตรวจด้วยตา (visual) | **บางส่วน** | headless Chrome screenshot ครั้งเดียว — **dark theme, colorblind mode, AG Grid ยังไม่ได้ตรวจด้วยตา** |

## ข้อจำกัดที่ทราบ

- วันอ้างอิง 2026-10-02 เป็นสมมติฐาน (ดูด้านบน) — ถ้าโจทย์ระบุวันอื่นต้อง ingest ใหม่และตัวเลข overdue จะเปลี่ยน
- OpenRouter: เรียกจริงสำเร็จแล้ว แต่ยังไม่ได้ประเมินคุณภาพอย่างเป็นทางการ (EV-01..EV-05) สำหรับ prompt v2; latency ~21–25 วินาที (timeout ค่าเริ่มต้น 60 วินาที); prompt injection ถูก **บรรเทา ไม่ได้กำจัด** (ดู AI_MODEL_SPEC "Security review note"); audit event เป็น log เท่านั้น; PDPA/data residency ของการส่ง `owner`/`action_name` ยังเป็น open item
- `app_config` ถูกเขียนตอน ingest แต่ไม่มีโค้ดอ่าน (แหล่งความจริงคือ `ingestion_runs.reference_date`)
- ค่าหลายตัวตั้งใจเป็น `null` ในเอกสาร (เช่น threshold, งบ, SLA) — ยังไม่กำหนดและไม่แต่งค่า; ค่า default ของ `AI_TOP_N`/`AI_TIMEOUT_SECONDS`/`INGEST_MAX_BYTES` เป็นค่าที่โค้ดเลือกเอง
- ไม่มี authentication (DuckDB ไม่มี role/row-level security ในตัว) ไม่มี scheduler/monitoring/CI
- Docker: ยังไม่ได้ตรวจ ownership ของ volume บน Windows/Mac, `read_only` rootfs, multi-arch
- Dashboard เป็น read-only ไม่แก้ owner / due_date / status
