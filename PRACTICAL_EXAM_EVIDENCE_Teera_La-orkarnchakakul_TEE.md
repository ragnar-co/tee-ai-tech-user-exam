# รายงานหลักฐานงานสอบ Practical — Teera La-orkarnchakakul (TEE)

> ไฟล์นี้ **สร้างหลังสอบ** (AFTER_EXAM) เพื่อรวบรวมหลักฐานให้กรรมการ ไม่ใช่ส่วนหนึ่งของงานที่ส่งสอบ ตอนสร้างและตรวจรายงานยัง **ไม่ได้ commit/push**; ภายหลังผู้สอบสั่งให้ commit และ push ไฟล์นี้เป็น commit แยกต่างหากต่อจาก `829d0b4` (commit นั้นไม่ได้อยู่ในรายการ commit ของหัวข้อ B และไม่อาจอ้างตัวเองด้วย SHA ในไฟล์นี้ได้)
> รายงานนี้ไม่ให้คะแนน ไม่ตัดสินผ่าน–ตก และไม่เสนอแนวทางพัฒนา
> สถานะหลักฐาน: **VERIFIED** (หลักฐานรองรับตรง ๆ) · **REPORTED** (มีผู้กล่าว/รายงานแต่ไม่มีหลักฐานตรง) · **INFERRED** (อนุมาน ระบุเหตุผล) · **UNKNOWN** (ข้อมูลไม่พอ)
> ช่วงเวลา: **DURING_EXAM / AFTER_EXAM / TIME_UNKNOWN** — เนื่องจากไม่ทราบเวลาเริ่ม–หมดเวลาสอบ (ดู A.4) หลักฐานเกือบทั้งหมดจึงเป็น **TIME_UNKNOWN** แม้จะมี timestamp ในตัวเอง

---

## A. ข้อมูลผู้สอบและขอบเขตหลักฐาน

### A.1 ผู้สอบและงาน
| รายการ | ค่า | สถานะ | Evidence |
|---|---|---|---|
| ชื่อผู้สอบ | Teera La-orkarnchakakul (TEE) | REPORTED (ผู้สอบแจ้งใน session); ชื่อ git user = `TEE` VERIFIED | E090, E001 |
| ตำแหน่ง | ไม่ทราบ — ไม่มีหลักฐานในบริบท | UNKNOWN | — |
| โจทย์ | "Cybersecurity Project Action Dashboard": รับ CSV → ตรวจสอบ → เก็บ SQLite3/DuckDB → แสดงงานทั้งหมด/เสร็จ/เลยกำหนดแยกโครงการ + รายการเลยกำหนดพร้อมผู้รับผิดชอบและจำนวนวันล่าช้า + เลือกดูรายโครงการ + ใช้ "วันที่อ้างอิงตามโจทย์"; โบนัส: AI workflow ร่าง Executive Summary จากข้อมูลใน DB บันทึกและแสดงบนแอป | VERIFIED (ข้อความโจทย์ที่ผู้สอบวางใน session) | E080 |
| วันที่อ้างอิงในข้อความโจทย์ | **ไม่ปรากฏ** ในข้อความที่วาง | VERIFIED (ไม่พบ) | E080 |
| DDD ที่เลือก | `ddd-data-analytics` v2.8.0 | VERIFIED | E010 |
| เครื่องมือ | Claude Code (CLI) ใช้โมเดล Sonnet 5.5; subagents หลายตัว (ไม่ได้นับจำนวน); Python 3.12 + uv/.venv; DuckDB; Dash/Plotly/AG Grid; pytest/ruff; Docker Desktop; git; Chrome headless (ถ่ายภาพหน้าจอ) | VERIFIED จาก tool outputs ใน session | E083, E040 |
| Repo | `https://github.com/ragnar-co/tee-ai-tech-user-exam.git` (branch `main`) | VERIFIED | E005 |
| URL แอป (Coolify) | `https://cybersec-dashboard.cyber1.ragnar-ai.dev` (ปรากฏในภาพ 502) | VERIFIED ว่ามี URL; สถานะใช้งาน UNKNOWN | E072 |

### A.2 แหล่งหลักฐานที่เข้าถึงได้
1. บทสนทนาและผล tool calls ใน session นี้ (ตามที่อยู่ใน context ขณะรวบรวม — ไม่รับประกันว่าครบทุกช่วงของงานก่อนหน้า session นี้)
2. repo ในเครื่อง (`/home/teera/AI-Tech-user-Exam`) และ Git history ในเครื่อง (2 commits)
3. รายงานผลของ subagents (เป็น REPORTED เว้นแต่ผมตรวจซ้ำเองใน session ซึ่งระบุไว้)

### A.3 แหล่งที่ขาด / ข้อจำกัดของ session
- **ไม่มี** หลักฐานฝั่ง Coolify นอกจากภาพ 502 และข้อความที่ผู้สอบวาง: ไม่มี deployment ID, commit ที่ deploy, log หรือสถานะ (E072–E075)
- ไม่มีเวลาเริ่ม–หมดเวลาสอบ และไม่มีการระบุว่า commit ใดคือฉบับที่ส่งสอบ
- `plan.md`, `ddd/*.json` และ `src/tee_cybersecurity_actions_mock.csv` **มีอยู่ก่อนเริ่ม session นี้** (E006) ไม่ทราบว่าใครสร้างหรือเมื่อไร (UNKNOWN)
- ไม่มี timestamp ของการ push (ผลคำสั่ง push ไม่แสดงเวลา)
- ไม่มียอด token/quota ที่ตีความได้ (E082)
- รายงานนี้ **ไม่รัน** test/app/build ซ้ำ ผลทดสอบทั้งหมดมาจาก tool outputs ที่เกิดขึ้นแล้วใน session

### A.4 เวลา
| รายการ | ค่า | สถานะ |
|---|---|---|
| เริ่มรวบรวมหลักฐาน | 2026-10-02 12:07:02 +07 (05:07:02 UTC) | VERIFIED (E001) |
| เวลาเริ่ม/หมดเวลาสอบ | ไม่ทราบ — ไม่มีหลักฐาน | UNKNOWN |
| commit ที่ส่งสอบ | ไม่ทราบ — ไม่มีหลักฐานระบุ | UNKNOWN |
| ผู้สอบแจ้งว่า "งานสอบสิ้นสุดแล้ว" | ในข้อความที่สั่งทำรายงานนี้ (ไม่ระบุเวลา) | REPORTED (E090) |

---

## B. สภาพงานที่พบ

**สภาพที่พบตอนรวบรวม (ก่อนสร้างรายงาน)** — VERIFIED [E001]
- repo root `/home/teera/AI-Tech-user-Exam`, branch `main`
- HEAD = `829d0b408430ae17d4565316ed4d41632f364db4`; `origin/main` (remote-tracking ในเครื่อง) = ค่าเดียวกัน
- `git status --porcelain -b --untracked-files=all`: ไม่มี staged/unstaged/untracked (working tree สะอาด)
- หลังสร้างรายงานนี้ จะมี untracked 1 ไฟล์คือรายงานนี้

**สภาพที่ยืนยันได้เมื่อหมดเวลาสอบ:** UNKNOWN (ไม่ทราบเวลาหมดเวลา และไม่ทราบ commit ที่ส่ง) — ห้ามถือว่า HEAD ปัจจุบันเท่ากับฉบับที่ส่งสอบ

**งานที่อยู่ใน commit** [E002–E004]
| Commit | เวลา (committer) | เนื้อหา |
|---|---|---|
| `412dd1e` | 2026-10-02T11:41:46+07:00 | เพิ่ม 96 ไฟล์ (~70,497 บรรทัด): โค้ด, SQL, tests, Dockerfile/compose, README, `plan.md`, `ddd/*.json` (10 ไฟล์), `docs/data-analytics/*.md` (23 ไฟล์) |
| `829d0b4` | 2026-10-02T11:52:55+07:00 | แก้ 14 ไฟล์ (+40/−38): เอา "(draft)" ออกจากเมนู, CSS สี label, ถอดแผง CH-12 ออกจากหน้า Overview, อัปเดตเอกสาร/README ว่าเรียก OpenRouter จริงสำเร็จ, แก้ test |

**งานที่ยังไม่ commit ตอนรวบรวม:** ไม่มี [E001]
**ไฟล์ที่ไม่ทราบที่มา:** `plan.md`, `ddd/ddd-*.json` (10 ไฟล์; ตอนเริ่ม session อยู่ที่ root ของ repo แล้วถูกย้ายเข้า `ddd/` ใน session), `src/tee_cybersecurity_actions_mock.csv` — เป็น untracked อยู่ก่อนเริ่ม session [E006] ไม่ทราบผู้สร้าง/เวลา
**หมายเหตุ:** ข้อความ commit `412dd1e` ระบุว่า "no real OpenRouter call has been made" ขณะที่ commit `829d0b4` ระบุว่าเรียกจริงสำเร็จแล้ว — เป็นลำดับเหตุการณ์ที่เปลี่ยนไประหว่าง 2 commit ไม่ใช่ข้อขัดแย้งของข้อมูลชุดเดียวกัน (E003, E004, E051)

---

## C. ลำดับการทำงาน

ไม่มี timestamp ของแต่ละขั้นในบทสนทนา ใช้ลำดับก่อน–หลังจาก session; เวลาจริงระบุเฉพาะที่พบใน output ("เวลาที่พบ")

| # | เวลา/ช่วง | สิ่งที่ทำ | ผู้ดำเนินการที่ยืนยันได้ | ผลที่พบ | Evidence |
|---|---|---|---|---|---|
| 1 | เริ่ม session (ไม่ทราบเวลา) | ผู้สอบสั่งวิเคราะห์ `plan.md`; AI อ่านและวิเคราะห์ (ชี้ช่องว่าง: reference date ไม่ระบุ, schema ไม่สอดคล้อง ฯลฯ) | AI (วิเคราะห์) / ผู้สอบ (สั่ง) | มีรายงานวิเคราะห์ใน session | E006, E010 |
| 2 | ถัดมา | ผู้สอบระบุตำแหน่ง CSV (`/src`) และ DDD; AI profile CSV (14,013 แถว, 12 โครงการ, 96 owner, ไม่มี dup/null) และแก้ `plan.md` | AI | profile ตรงกับ CSV จริง (ผล tool call) | E030 |
| 3 | ถัดมา | จัดโฟลเดอร์ (`ddd/`, `data/`, `docs/data-analytics/`) | AI | โฟลเดอร์ถูกสร้าง/ย้ายไฟล์ | E002 |
| 4 | ถัดมา | ตัดสินวันที่อ้างอิง: AI อนุมาน 2026-10-01 จากข้อมูล → ผู้สอบเลือก **2026-10-02 ล็อกเป็นค่าคงที่ iteration แรก** | ผู้สอบ (ตัดสิน) | บันทึกใน `plan.md` | E010, E081 |
| 5 | ถัดมา | ผู้สอบสั่งทำ **ทุกเอกสาร** ใน `ddd-data-analytics-v2.8.0.json` (ไม่รอ "เงื่อนไขกลาง"); AI แตก subagents เขียนเอกสาร 23 ฉบับตามลำดับ dependency เป็นระลอก แล้ว reconcile | ผู้สอบ (สั่ง) / subagents (เขียน) | มี 23 ไฟล์ใน `docs/data-analytics/` (~42,159 คำ) | E011–E013, E081 |
| 6 | ถัดมา | ตัดสินเรื่อง AI: OpenRouter + `anthropic/claude-sonnet-5`, ใช้เฉพาะ `OPENAI_API_KEY`/`OPENAI_BASE_URL` (ไม่ใช้ `aix`), ส่ง `owner` ได้ | ผู้สอบ | แก้ plan/เอกสารตาม | E024, E081 |
| 7 | ถัดมา | Implement: bootstrap (`pyproject.toml`, `.venv`) → core (SQL/validation/ingest/metrics) → UI components → AI provider → wiring `dashboard/app.py` | AI + subagents | pytest ผ่านตามลำดับ (127 → 160 → 260/277) | E020–E026, E030–E035 |
| 8 | ถัดมา | ตรวจเพิ่มแบบขนาน: security review, audit เอกสารเทียบโค้ด, hardening ingest (133 tests) แล้วแก้บั๊ก/ช่องว่าง | subagents (รายงาน) | บั๊ก ingest ถูกแก้ตามรายงาน | E037, E038 |
| 9 | ถัดมา | เขียน README + `.gitignore`; สร้าง Dockerfile/compose | AI | ไฟล์อยู่ใน commit | E025, E027 |
| 10 | ถัดมา | ผู้สอบเปิด Docker Desktop; AI build/run/ตรวจใน container | AI | healthy, 3 หน้า 200, ตัวเลขตรง | E040–E047 |
| 11 | ~11:2x–11:3x +07 | รันแอปให้ผู้สอบใช้ (`localhost:8050`) | AI | 3 หน้า 200 | E042, E047 |
| 12 | 11:41:46 +07 | **commit `412dd1e`** และ push ตามคำสั่งผู้สอบ (เวลา push ไม่ทราบ) | AI (ตามคำสั่ง) | `[new branch] main -> main` | E003, E060 |
| 13 | หลังจากนั้น | ผู้สอบส่งภาพหน้าจอ (ป้าย draft, สี label มืด, แผง Run & validation) และสั่งแก้ + "ใช้งานได้จริง"; AI ทดสอบเรียก OpenRouter จริง 2 ครั้ง, แก้ UI, อัปเดตเอกสาร | ผู้สอบ (สั่ง) / AI | ดู E050–E052, E070–E071 | — |
| 14 | 11:52:55 +07 | **commit `829d0b4`** + push | AI (ตามคำสั่ง) | `412dd1e..829d0b4 main -> main` | E004, E060 |
| 15 | หลังจากนั้น | ผู้สอบถามเรื่อง env บน Coolify; ผู้สอบส่งภาพ 502 (04:56:00 UTC = 11:56:00 +07); AI แนะนำการไล่สาเหตุโดยไม่มีสิทธิ์เข้าถึง Coolify | ผู้สอบ/AI | สาเหตุจริงยังไม่ยืนยัน | E072–E074 |
| 16 | หลังจากนั้น | ผู้สอบถามว่าข้อความ "ยังไม่ได้ตั้งค่า OPENAI_API_KEY…" ต้องตั้งใน Coolify ใช่หรือไม่ (ชี้ว่าเห็นแอปทำงานอยู่) | ผู้สอบ | AI ตอบ: ใช่ | E073 |
| 17 | 12:07:02 +07 | เริ่มรวบรวมหลักฐาน (AFTER_EXAM) | AI | รายงานนี้ | E001, E090 |

---

## D. คำสั่งและเครื่องมือที่ใช้

### D.1 คำสั่งที่มีหลักฐานว่า execute แล้ว (สรุป — ไม่ใช่ทุกคำสั่งตามลำดับจริง)
| # | คำสั่ง/tool | จุดประสงค์ที่มีหลักฐาน | ผล/exit code ที่พบ | ช่วงเวลา | Evidence |
|---|---|---|---|---|---|
| 1 | `Read plan.md` | อ่านแผน | ได้เนื้อหาไฟล์ | TIME_UNKNOWN | E010 |
| 2 | `python3` สคริปต์นับ/profile CSV | ตรวจข้อมูลจริง | 14,013 แถว; done 8,597 / in_progress 3,326 / todo 2,090; 12 โครงการ; 96 owner; due 2026-07-18..2026-11-05 | TIME_UNKNOWN | E030 |
| 3 | `python3` สคริปต์ใน `ddd-data-analytics-v2.8.0.json` | อ่านเอกสาร/dependency 23 ฉบับ | ได้ generation_order และ depends_on | TIME_UNKNOWN | E012 |
| 4 | `uv venv .venv` + `uv pip install -e ".[dev]"` | bootstrap | `imports ok duckdb 1.5.6, dash 4.4.1, dash_ag_grid 35.3.0` | TIME_UNKNOWN | E030 |
| 5 | `.venv/bin/pytest -q` (หลายครั้ง) | รันชุดทดสอบ | ดู H.2 | TIME_UNKNOWN | E030–E035 |
| 6 | `.venv/bin/ruff check .` | lint | `All checks passed!` (ครั้งที่ระบุใน H.2) | TIME_UNKNOWN | E030–E035 |
| 7 | `python -m src.ingest --input src/tee_cybersecurity_actions_mock.csv --reference-date 2026-10-02` | ingest ข้อมูลจริง | `status: noop` (รอบซ้ำ) / `status: succeeded` (DB ใหม่), exit 0 | TIME_UNKNOWN | E032, E048 |
| 8 | `python dashboard/app.py` / entrypoint + `curl` | เปิดแอปในเครื่องและตรวจ | `/`, `/overdue`, `/executive-summary` = 200 | TIME_UNKNOWN | E031, E048 |
| 9 | `docker compose build/up/exec/restart/down` | ทดสอบ container | build สำเร็จ, `healthy`, restart → noop | TIME_UNKNOWN | E041–E046 |
| 10 | `python` สคริปต์เรียก `OpenRouterProvider` + callback ของแอป | ทดสอบ AI จริง | OK 21.1 s; callback 25.4 s / 24.6 s | TIME_UNKNOWN | E050, E051 |
| 11 | `git add -A && git commit` (2 ครั้ง) | บันทึกงาน | `412dd1e`, `829d0b4` | 11:41:46 / 11:52:55 +07 | E002–E004 |
| 12 | `git push -u origin main` / `git push origin main` | ส่งขึ้น GitHub | `[new branch] main -> main`; `412dd1e..829d0b4 main -> main` | เวลา push UNKNOWN | E060 |
| 13 | `git ls-remote --heads origin` | ตรวจ remote | ว่างเปล่า (ก่อน push แรก); แสดง `refs/heads/main` หลัง push | TIME_UNKNOWN | E061 |
| 14 | `google-chrome --headless ... --screenshot` | ตรวจหน้าจอ | ได้ภาพ (โหมดสว่าง); ไม่ได้ตรวจโหมดมืด | TIME_UNKNOWN | E047 |
| 15 | `docker version`, `docker history`, `grep` pattern key | ตรวจ docker/ความลับ | client/server 29.8.1; ไม่พบ key ใน history/ไฟล์ | TIME_UNKNOWN | E040, E046, E035 |

### D.2 คำสั่งที่เพียงเสนอหรือกล่าวถึง (ไม่มีหลักฐาน execute)
- การ deploy บน Coolify (Ports Exposes 8050, env vars, persistent storage `/app/data`, แก้ `entrypoint.sh` ให้ chown) — เป็นคำแนะนำ ไม่มีหลักฐานว่าทำหรือไม่ (E074)
- `docker compose down -v`, `coolify` CLI (ไม่มีติดตั้ง: `coolify not found`)

### D.3 คำสั่งอ่านอย่างเดียวที่ใช้รวบรวมรายงานนี้ (AFTER_EXAM)
`date`, `pwd`, `git rev-parse`, `git branch --show-current`, `git status --porcelain=v1 -b`, `git diff --cached --stat`, `git diff --stat`, `git remote -v` (ปกปิดรหัส), `git config user.name`, `git log --format`, `git show --stat`, `git ls-files | wc -l`, `rg -n/-c/-o`, `sed -n`, `wc -w` และ `Write` สร้างไฟล์รายงานนี้ **ไม่รัน** test/app/build/commit/push

---

## E. การตัดสินใจและการใช้ AI

### E.1 การตัดสินใจ (จากข้อความของผู้สอบใน session — VERIFIED ว่าผู้สอบกล่าว) [E081]
| เรื่อง | การตัดสินใจ | เหตุผลที่ปรากฏในหลักฐาน |
|---|---|---|
| DDD | ใช้ `ddd-data-analytics` v2.8.0 เพียงตัวเดียว และสร้าง **ทุก** เอกสาร (23 ฉบับ) | คำสั่งผู้สอบ: ไม่ต้องสนใจ "เงื่อนไขกลาง" ทำทุกเอกสารใน JSON; ต้อง implement อิงตาม DDD "ไม่งั้นจะออกมามั่ว" |
| DB | DuckDB | `plan.md` §0 (E010) — เหตุผลระบุใน plan |
| วันที่อ้างอิง | 2026-10-02 ล็อกเป็นค่าคงที่ใน iteration แรก (ไม่ใช้ `date.today()`) | โจทย์ให้ "ใช้วันที่อ้างอิงตามโจทย์" แต่ข้อความโจทย์ไม่มีวันที่ (E080); ผู้สอบเลือก "แบบที่ 1: ล็อกเป็นวันที่คงที่ = วันนี้" |
| AI provider | OpenRouter, `anthropic/claude-sonnet-5`, env `OPENAI_API_KEY`/`OPENAI_BASE_URL`, ไม่ใช้ `aix`, **ส่ง `owner` ได้** | คำสั่งผู้สอบโดยตรง (ไม่มีเหตุผลเพิ่มในข้อความ) |
| การแสดงผล | เอา "(draft)" ออกจากเมนู; ถอดแผง "Run & validation summary" (CH-12) | คำสั่งผู้สอบ (ภาพ E070, E071); ไม่ระบุเหตุผล |
| ส่งมอบ | commit + push เข้า `main`; README; `.gitignore`; Dockerfile/compose | คำสั่งผู้สอบ |
| ตัดออก/ไม่ทำ | metric ที่ไม่มีข้อมูลรองรับ (risk score, SLA ฯลฯ — `plan.md` §21), authentication, CI, scheduler | ระบุเป็นข้อจำกัดใน README (E027) |

### E.2 การใช้ AI
- AI (Claude Code + subagents) เป็นผู้เขียนโค้ด/เอกสารส่วนใหญ่ตามที่ปรากฏใน session และมีบรรทัด `Co-Authored-By: Claude Sonnet 5.5` ใน commit ทั้งสอง (E003, E004)
- **หลักฐานที่ผู้สอบตรวจ/ปรับ output ของ AI:** (1) ตั้งคำถามเชิงเหตุผลหลายข้อ เช่น ทำไมต้องใช้ reference date, ทำไมเขียนว่า draft, แอปใช้ได้จริงหรือยัง; (2) ตัดสินเลือกทางเลือกที่ AI เสนอและแก้ทิศทาง (ไม่ใช้ `aix`, ส่ง owner ได้, ล็อกวันที่); (3) ส่งภาพหน้าจอชี้จุดที่ต้องแก้ (E070, E071) — เป็นหลักฐานว่าผู้สอบดูผลลัพธ์จริง **ไม่สรุป** ว่าเข้าใจโค้ดหรือไม่
- **Token/quota:** ไม่มีหลักฐานที่ตีความได้ → UNKNOWN (E082)

---

## F. ปัญหาและสิ่งที่ติด

| ปัญหา | อาการ/error ที่พบ | วิธีที่ลอง | ผลที่ยืนยันได้ | ยังไม่ทราบ/ค้าง | Evidence |
|---|---|---|---|---|---|
| วันที่อ้างอิงไม่อยู่ในโจทย์ | ข้อความโจทย์ไม่มีวันที่ | AI อนุมาน 2026-10-01 จากข้อมูล (done สูงสุด 2026-09-30) → ผู้สอบเลือก 2026-10-02 | ล็อก 2026-10-02 ทั้งโค้ด/เอกสาร | วันที่ที่ถูกต้องตามต้นฉบับโจทย์: UNKNOWN | E080, E010, E081 |
| เอกสาร/แผนขัดกัน | รายงาน reconcile พบ: filter ต้อง restrict ไม่ใช่ highlight, ขาด MET-07/08, ชื่อ env เก่า ฯลฯ | สั่ง agent แก้แบบแบ่งไฟล์ | grep ภายหลังไม่พบชื่อ env เก่า/วันที่เก่า (ยกเว้นหมายเหตุ superseded) | ไม่ได้อ่านเอกสารครบทุกบรรทัด (ตรวจแบบ pattern) | E013, E036 |
| `rm -f <glob>` zsh error | `no matches found` ทำให้ chain คำสั่งหยุด | รันซ้ำแบบไม่ใช้ glob | ingest ลง DB ชั่วคราวสำเร็จ | — | E048 |
| `pkill -f` ฆ่า shell ตัวเอง | `Exit code 144` | ตรวจด้วย `curl` ว่าพอร์ตปิด | `000` (ไม่มี server เหลือ) | — | E048 |
| Docker ไม่พร้อมใน WSL | `docker could not be found in this WSL 2 distro` | ผู้สอบเปิด Docker Desktop | `docker version` ได้ 29.8.1 | — | E040 |
| Multi-line field ทำให้ ingest ล้ม (security review) | `exit 3`, run `failed` | hardening agent เปลี่ยนวิธีโหลด CSV | ตามรายงาน: แก้แล้ว + test | ไม่ได้ตรวจซ้ำด้วยตนเองเป็นรายกรณี | E037, E038 |
| test ล้มชั่วคราว | `test_whitespace_only_fields_blocking` ล้มขณะ agent แก้ไฟล์ | รอ agent จบ | รอบถัดมา 260/277 passed | — | E032, E033 |
| ตัวอักษร Theme/Colour-blind มองไม่เห็นในโหมดมืด | ภาพของผู้สอบ (E070) | เพิ่ม `color: var(--text)` | ภาพโหมดสว่างอ่านได้ | **โหมดมืดยังไม่ได้ตรวจด้วยตา** | E047, E070 |
| ข้อความเอกสารล้าสมัยหลังทดสอบ AI จริง | เอกสารยังเขียน "ไม่เคยเรียกจริง" | agent แก้ 17 จุด + ผม grep | README/AI_MODEL_SPEC ตรงกับผลทดสอบ | บางไฟล์อ่านเฉพาะบรรทัดที่ grep | E028, E051 |
| **502 บน Coolify** | Cloudflare "Bad gateway Error code 502" ที่ `cybersec-dashboard.cyber1.ragnar-ai.dev` เวลา 2026-10-02 04:56:00 UTC | AI ไม่มีสิทธิ์เข้าถึง Coolify (`coolify not found`) จึงเสนอรายการตรวจ (port 8050, volume permission, health, build pack) | **ไม่ทราบว่าแก้แล้วหรือไม่ / สาเหตุจริง** — ข้อความผู้สอบภายหลังบ่งชี้ว่าเห็นแอปตอบ (INFERRED) แต่ไม่มีภาพ/log ยืนยัน | สาเหตุ, วิธีแก้ที่ผู้สอบใช้, commit ที่ deploy: UNKNOWN | E072–E074 |

---

## G. งานที่ส่งมอบ

### G.1 เส้นทางข้อมูล CSV → DB → ผลลัพธ์
`src/tee_cybersecurity_actions_mock.csv` → `python -m src.ingest` (`src/ingest.py`, validation `src/validation.py` + `sql/30_quality/quality_checks.sql`, DQ-01..12; exit 0/1/2/3) → DuckDB `data/cybersecurity.duckdb` (ตาราง `ingestion_runs`, `raw_actions`, `stg_actions`, `data_quality_results`, `executive_summaries`, `app_config`; run versioning, ingest ซ้ำไฟล์+วันเดิม = no-op) → `src/metrics.py` (อ่านแบบ read-only, ตัวกรอง `project`) → Dash `dashboard/app.py` (3 หน้า: `/`, `/overdue`, `/executive-summary`) [E020–E023]

### G.2 ฟังก์ชันหลัก (พบ implementation)
- นิยาม overdue ใน SQL: `status != 'done' AND due_date < reference_date`; `days_overdue = date_diff('day', due_date, reference_date)` — `sql/10_staging/stg_actions.sql:16-20` [E020]
- API `get_run_info / list_projects / portfolio / by_project / overdue_detail / by_owner / data_quality_summary` — `src/metrics.py:74-117` [E022]
- ตัวกรองโครงการ (dropdown) + KPI cards + กราฟ + ตารางสรุป + AG Grid งานเลยกำหนด (project, action, owner, due date, days overdue, status) + หน้า Executive Summary [E023, E026]
- เอกสาร DDD 23 ฉบับ ใน `docs/data-analytics/` (~42,159 คำ) [E011]
- Docker: `Dockerfile` (python:3.12-slim 2 stage, `USER appuser`, `EXPOSE 8050`, `HEALTHCHECK`, entrypoint ingest → gunicorn), `docker-compose.yml` (named volume `duckdb-data` → `/app/data`) [E025]

### G.3 พบ implementation vs มีหลักฐานใช้งานสำเร็จ
| ส่วน | พบ implementation | หลักฐานใช้งานสำเร็จ (เมื่อไรไม่ทราบ) |
|---|---|---|
| ingest + DuckDB | VERIFIED (โค้ด/SQL) | VERIFIED: ingest ข้อมูลจริง `succeeded`/`noop`, ตัวเลขตรง (E030, E032) |
| metrics/ตัวกรอง | VERIFIED | VERIFIED: All Projects 14,013/8,597/5,416/overdue 3,531; P01 1,168/816/352/202 (E030, E043) |
| Dashboard | VERIFIED | VERIFIED: 3 หน้า 200 ในเครื่องและใน container; ผ่าน callback (ตามรายงาน wiring agent: REPORTED) |
| Docker | VERIFIED | VERIFIED: build + healthy + restart noop (E041–E046) |
| AI Executive Summary | VERIFIED | VERIFIED: เรียกจริงสำเร็จ 2 ครั้ง บันทึก+แสดงซ้ำได้ (E050, E051) |
| Deploy Coolify | ไม่มี config Coolify ใน repo (E075) | UNKNOWN (E072–E074) |

### G.4 Persistence ที่พบ
`docker-compose.yml` กำหนด volume `duckdb-data` ที่ `/app/data` (E025); `data/*.duckdb` ถูก ignore ไม่อยู่ใน Git; การตั้ง persistent storage บน Coolify: UNKNOWN

### G.5 ข้อจำกัดที่พบ (ไม่ได้ทดลองใหม่) [E027, E028]
วันอ้างอิง 2026-10-02 เป็นสมมติฐาน · ไม่มี authentication · การเรียก OpenRouter ทดสอบแบบ manual เพียงสองครั้ง ยังไม่ประเมินคุณภาพอย่างเป็นทางการ (EV-01..05) · audit `ai_context_send` เป็น log เท่านั้น · โหมดมืด/colorblind/AG Grid ยังไม่ตรวจด้วยตา · ไม่มี CI/browser e2e · PDPA/data residency เป็น open item

---

## H. หลักฐาน Test / Validation

### H.1 Test code (พบในโค้ด — ไม่ใช่ผลรัน) [E026]
จำนวน `def test_` เชิงสถิตต่อไฟล์ (ไม่เท่ากับจำนวนที่รัน เพราะ parametrize): `test_hardening_ingest` 48 · `test_dashboard_app` 22 · `test_dashboard_components` 19 · `test_ingest` 16 · `test_metrics` 14 · `test_validation` 13 · `test_ai_provider` 11 · `test_ai_summary_service` 9 · `test_reference_date` 8 · `test_ai_context_builder` 4 · `test_ai_prompt_hardening` 4 · `test_idempotency` 3 · `test_reconciliation` 2

### H.2 ผลรันจริงที่ปรากฏเป็น tool output ใน session (VERIFIED ว่ามี output; เวลาเทียบกับช่วงสอบ: TIME_UNKNOWN)
| # | คำสั่ง | ผล | ลำดับเทียบ commit | Evidence |
|---|---|---|---|---|
| 1 | `.venv/bin/pytest -q` | `127 passed in 18.77s`; ruff `All checks passed!`; metrics: 14013 / 8597 / 5416 / 3531 | ก่อน `412dd1e` | E030 |
| 2 | `pytest -q --ignore=tests/test_hardening_ingest.py` | `160 passed in 41.22s`; ruff (dashboard, src/ai, 2 test files) ผ่าน | ก่อน `412dd1e` | E031 |
| 3 | `pytest -q` | `260 passed in 61.11s`; ruff ผ่าน; ingest `noop` | ก่อน `412dd1e` | E032 |
| 4 | `pytest -q` | `277 passed in 74.06s`; ruff ผ่าน | ก่อน `412dd1e` | E033 |
| 5 | `pytest -q` (หลังถอด CH-12) | `277 passed in 71.02s`; ruff ผ่าน | ก่อน `829d0b4` | E034 |
| 6 | `pytest -q` (ก่อน commit รอบ 2) | `277 passed in 65.31s`; ruff ผ่าน; สแกน secret ในไฟล์ที่เปลี่ยน = 0 | ก่อน `829d0b4` | E035 |

### H.3 กรณีทดสอบ / expected vs actual ที่พบ
| กรณี | expected | actual | สถานะ |
|---|---|---|---|
| reconcile ข้อมูลจริง @2026-10-02 | total 14,013 · done 8,597 · open 5,416 · overdue 3,531 · max days 46 · open_not_overdue 1,885 · owners_with_overdue 96 | ตรงทุกค่า (E030/E032; E043 สำหรับ container) | VERIFIED |
| ตัวกรอง P01 | 1,168 / 816 / 352 / 202 | ตรง (E043, E030 query P01) | VERIFIED |
| ชื่อโครงการไม่มีอยู่ | ผลเป็น 0 ไม่ error | `portfolio("nope")` คืน 0 ทั้งหมด | VERIFIED (E030) |
| ingest ซ้ำ | no-op, `run_id` เดิม | `status: noop`, `run_id: 1` | VERIFIED (E032, E044) |
| golden fixture 12 แถว @2026-09-15 | overdue 5, max days 59 (ในเอกสาร TESTING_STRATEGY) | ผ่านใน pytest ตามรายงาน test agent | REPORTED (ผ่านใน suite ที่รันจริง E033) |
| hardening ไฟล์ผิดรูปแบบ (BOM, CRLF, multi-line, whitespace, วันที่เสีย ฯลฯ) | reject/flag ตามเอกสาร | ผ่านใน suite (133 tests ตามรายงาน) | REPORTED + suite pass (E033) |
| 140k แถว | — | ingest 1.7 s, RSS ~353 MB | REPORTED (E037) |
| AI ด้วย HTTP mock | success/401/403/404/429/5xx/timeout/ไม่มี env → ไม่บันทึก/ไม่ crash | ผ่านใน suite | VERIFIED เป็นส่วนของ pass count |

**หมายเหตุ:** ไม่มี CI, ไม่มี browser e2e, ไม่วัด coverage (E027); ไม่ได้รันซ้ำตอนรวบรวม

---

## I. หลักฐาน Repo และ Coolify

| หัวข้อ | หลักฐาน | สถานะ |
|---|---|---|
| URL repo | `https://github.com/ragnar-co/tee-ai-tech-user-exam.git` | VERIFIED (E005) |
| Commit SHA | `412dd1e0118f11439d9046c8530dcfd1b15e8a4e` (11:41:46 +07); `829d0b408430ae17d4565316ed4d41632f364db4` (11:52:55 +07) | VERIFIED (E002) |
| หลักฐาน push | output ใน session: `* [new branch] main -> main` (รอบแรก, remote ว่างก่อนหน้า: `git ls-remote --heads origin` ไม่มีผล) และ `412dd1e..829d0b4 main -> main`; `git status -sb` = `main...origin/main`; ปัจจุบัน `origin/main` ในเครื่อง = HEAD | VERIFIED ว่า push สำเร็จใน session; **เวลา push: UNKNOWN** (E060, E061, E001) |
| push ทันเวลา | ไม่ทราบเวลาสอบ และไม่มี timestamp push; remote-tracking branch ในเครื่องไม่ยืนยันเวลา | UNKNOWN |
| Coolify deployment ID | ไม่พบ | UNKNOWN |
| commit ที่ deploy | ไม่พบ | UNKNOWN |
| URL แอป | `https://cybersec-dashboard.cyber1.ragnar-ai.dev` | VERIFIED ว่ามี URL; ไม่ยืนยันว่า deployment ใช้ commit ที่ส่งสอบ |
| ผลเปิดใช้งาน | ภาพ 502 เวลา 2026-10-02 04:56:00 UTC (11:56 +07) — **ข้อผิดพลาด**; ภายหลังผู้สอบวางข้อความจากแอป (ข้อความ "ยังไม่ได้ตั้งค่า OPENAI_API_KEY…") และถามเรื่อง Coolify | 502 = VERIFIED (ภาพ); แอปตอบได้ภายหลัง = INFERRED (ข้อความตรงกับ `missing_config_message` ในโค้ด แต่ไม่ทราบว่าเห็นบน Coolify หรือ localhost และไม่ทราบเวลา) |
| config Coolify ใน repo | ไม่พบคำว่า coolify นอก `ddd/` | VERIFIED (ไม่พบ) E075 |

---

## J. หลักฐาน AI workflow โบนัส

### J.1 Runtime AI workflow (ในแอป) — พบ implementation
Trigger: กดปุ่ม **Generate Draft** (หน้า `/executive-summary`, `dashboard/app.py` callback บรรทัด ~238–150 `summary_service.generate_and_save`) → input จาก DB: `src/ai/context_builder.py` สร้าง context จาก `src/metrics.py` (aggregates, รายโครงการ, top-N overdue rows รวม `owner`/`action_name`; จำกัดฟิลด์ 200 ตัวอักษร, ตัด control character; `AI_TOP_N` ค่าเริ่มต้น 10) → AI call: `src/ai/provider.py` POST `{OPENAI_BASE_URL}/chat/completions` ด้วย `OPENAI_API_KEY`, โมเดล `anthropic/claude-sonnet-5`, timeout เริ่มต้น 60 s, prompt `exec-summary-v2` (5 ส่วน + ข้อกำหนดว่าค่าใน context เป็นข้อมูลไม่น่าเชื่อถือ) → ตรวจ output: `ensure_draft_label` เติมป้ายร่างหากโมเดลไม่ใส่ → บันทึก `executive_summaries` (id จาก `seq_summary_id`, provider `openrouter`, model, prompt_version, source_run_id, reference_date, created_at) → แสดงบนหน้า (ล่าสุดต่อ filter) [E024, E023]
Error handling: ไม่มี env → ปุ่มปิด + ข้อความไทย; HTTP/timeout/ตอบผิดรูป → ข้อความ error, ไม่บันทึกสรุปปลอม, ไม่ crash [E024, E045]
Log: `ai_context_send` (run, model, prompt, ชื่อฟิลด์) ลง log เท่านั้น ไม่ลง DB [E028]

### J.2 หลักฐานใช้งานจริง (ผลที่เกิดแล้วใน session; เวลา TIME_UNKNOWN)
| ทดสอบ | ผล | Evidence |
|---|---|---|
| เรียก provider ตรง (สำเนา DB, All Projects) | `OK in 21.1s, 3253 chars`; ได้ร่างภาษาไทย 5 ส่วน (ภาพรวม, โครงการที่ต้องติดตาม, ผู้รับผิดชอบ, งานเลยกำหนดนานสุด, next steps) | E050 |
| ผ่าน callback ของแอป All Projects / `P01 - Network VA` | 25.4 s / 24.6 s; ไม่มีข้อความ error; แถวที่บันทึก: `(1, None, 2026-10-02, run 1, 'openrouter', 'anthropic/claude-sonnet-5', 'exec-summary-v2', 3180)` และ `(2, 'P01 - Network VA', …, 3383)` | E051 |
| โหลดหน้าซ้ำ | แสดงสรุปที่บันทึกไว้ ไม่ขึ้น "ยังไม่มีสรุป" | E051 |
| เทียบตัวเลขในร่างกับ DB | P03 open 809 / overdue 611; P08 757 / 566; P09 109 / 47; top overdue A000017 Owner-033 46 วัน — ตรง | E052 |
| ข้อสังเกตคุณภาพ | โมเดลเขียน "14,013 action_name" แทน "รายการ" (หลุดชื่อฟิลด์ดิบ) | E050 |

ยังไม่มีหลักฐาน: การประเมินคุณภาพอย่างเป็นทางการ (EV-01..05) สำหรับ prompt v2; การทดสอบ AI บน Coolify — UNKNOWN
**แยกจากการใช้ Claude Code ช่วยเขียนโค้ด** (E.2): J นี้คือ workflow ที่ผู้ใช้แอปเรียกใช้ตอน runtime

---

## K. ตารางหลักฐานตามเกณฑ์สอบ

| หัวข้อ | หลักฐานที่รองรับ | Evidence | สถานะหลักฐาน | สิ่งที่ยังยืนยันไม่ได้ |
|---|---|---|---|---|
| ประโยชน์และฟังก์ชันหลัก | ตัวเลขรวม/ต่อโครงการ/overdue พร้อม owner และ days_overdue ตรงกับข้อมูลจริง; ตัวกรองโครงการ; 3 หน้า | E020–E023, E030, E043 | VERIFIED (ทำงานใน session) | ทำงานบน Coolify; ความตรงกับวันอ้างอิงของโจทย์ต้นฉบับ |
| การใช้ DDD | เลือก ddd-data-analytics v2.8.0; เอกสาร 23 ฉบับครบ; รอบ reconcile; โค้ดอิงชื่อ/ตาราง/สูตรจากเอกสาร | E010–E013, E011 | VERIFIED (พบเอกสารครบ); ความสอดคล้องกับโค้ด REPORTED (audit agent) | อ่านครบทุกบรรทัด; "เอกสารขั้นต่ำ" ตามเงื่อนไขกลาง: UNKNOWN |
| ฐานข้อมูลและ persistence | DuckDB `data/cybersecurity.duckdb`; ตาราง 6 ตาราง; run versioning/idempotent; volume `duckdb-data` ใน compose | E021, E025, E044 | VERIFIED | persistent storage บน Coolify |
| Test / Validation | pytest 277 passed (รอบล่าสุดก่อน commit 2); ruff ผ่าน; DQ-01..12; reconcile CSV vs DuckDB | E026, E033–E035 | VERIFIED (ผลรันใน session) | ผลที่ commit `412dd1e` ตอนนั้นเป็นอย่างไร (รันก่อน commit แต่ไม่ได้รันที่ commit นั้นโดยตรง); ไม่มี CI |
| Push repo และ Coolify deployment | push สำเร็จ 2 ครั้ง; commit time 11:41:46 / 11:52:55 +07; ภาพ 502 | E002–E005, E060, E072 | push = VERIFIED; deploy = UNKNOWN | เวลา push; deployment ID; commit ที่ deploy; แอปบน Coolify ใช้งานได้หรือไม่ |
| การใช้งานและส่งมอบ | README (วิธีรัน/Docker/env/ข้อจำกัด); `.env.example`; รันได้ด้วย `docker compose up --build` | E027, E041–E047 | VERIFIED (ในเครื่อง) | การใช้งานโดยผู้ตรวจ; บน Coolify |
| AI workflow โบนัส | trigger → DB → OpenRouter → บันทึก → แสดงผล; error handling; เรียกจริง 2 ครั้ง | E023, E024, E050–E052 | VERIFIED (ในเครื่อง/สำเนา DB) | บน Coolify; คุณภาพเชิงประเมิน (EV) |

### เงื่อนไขบังคับ
| เงื่อนไข | หลักฐาน | สถานะ |
|---|---|---|
| ฟังก์ชันหลักใช้ได้ | ผลใน session (ในเครื่อง + container) E030, E043, E047 | VERIFIED (ใน session) — บน deploy จริง UNKNOWN |
| ใช้ DB จริง | DuckDB ไฟล์จริง, ingest/query จริง E032, E043 | VERIFIED |
| มี Test/Validation ผ่าน | pytest 277 passed + ruff ผ่าน (รอบ E035) | VERIFIED (เวลาเทียบช่วงสอบ UNKNOWN) |
| push ทันเวลา | push สำเร็จ แต่ไม่ทราบเวลา push/เวลาสอบ | UNKNOWN |
| deploy เปิดใช้ทันเวลา | ไม่มี deployment record; มีภาพ 502 และข้อความผู้สอบ | UNKNOWN |

---

## L. Evidence Index

> `[S]` = ผลคำสั่ง/ข้อความใน session นี้ · `[F]` = ไฟล์ใน repo (path:บรรทัด) · `[G]` = Git ในเครื่อง · ค่าลับถูกปกปิดหรือไม่ถูกคัดลอก

| ID | แหล่ง/ตำแหน่ง | Excerpt สั้น | เวลา | ข้อเท็จจริงที่รองรับ |
|---|---|---|---|---|
| E001 | [S] ผลคำสั่งอ่านอย่างเดียวตอนเริ่มรวบรวม | `2026-10-02 12:07:02 +07`; branch `main`; HEAD `829d0b4…`; `## main...origin/main` (ไม่มีรายการ) | AFTER_EXAM | สภาพก่อนสร้างรายงาน; tree สะอาด; HEAD = origin/main (ในเครื่อง) |
| E002 | [G] `git log` | 2 commits ผู้เขียน `TEE` (อีเมล [REDACTED]) | TIME_UNKNOWN เทียบช่วงสอบ | commit และเวลา |
| E003 | [G] `git show --stat 412dd1e` | `96 files changed, 70497 insertions(+)`; ข้อความมี "no real OpenRouter call has been made" | 11:41:46 +07 | เนื้อหา commit แรก |
| E004 | [G] `git show --stat 829d0b4` | `14 files changed, 40 insertions(+), 38 deletions(-)` | 11:52:55 +07 | เนื้อหา commit ที่สอง |
| E005 | [G] `git remote -v` | `origin https://github.com/ragnar-co/tee-ai-tech-user-exam.git` | — | URL repo |
| E006 | [S] gitStatus ณ เริ่ม session (system context) | untracked: `ddd-*.json` ×10, `plan.md`, `src/` ; "Recent commits:" ว่าง | ต้น session (เวลา UNKNOWN) | ไฟล์เหล่านี้มีก่อน session; ไม่มี commit เดิม |
| E007 | [S] `ls -la` รอบแรก | mtime `ddd-*.json` "2 Oct 10:16", `plan.md` "2 Oct 10:31", CSV "1 Oct 20:42" | mtime (ไม่ใช่หลักฐานเด็ดขาด) | เบาะแสเท่านั้น |
| E010 | [F] `plan.md:5-7,86,1106` | "ใช้ ddd-data-analytics เพียงตัวเดียว"; "REFERENCE_DATE = 2026-10-02 … ผู้ใช้ยืนยัน, iteration แรก" | TIME_UNKNOWN | การเลือก DDD/DB/วันอ้างอิง |
| E011 | [F] `docs/data-analytics/` (23 ไฟล์), `wc -w` | ~42,159 คำ | TIME_UNKNOWN | เอกสาร DDD ครบ |
| E012 | [S] ผลอ่าน `ddd-data-analytics-v2.8.0.json` | `generation_order`: stakeholders … readme (23) + depends_on | TIME_UNKNOWN | ลำดับเอกสารตาม template |
| E013 | [S] task-notification ของ subagents | รายงานการเขียน/ reconcile เอกสารเป็นระลอก | TIME_UNKNOWN | ผู้เขียนเอกสาร = subagents (REPORTED) |
| E020 | [F] `sql/10_staging/stg_actions.sql:16-20` | `status != 'done' AND due_date < reference_date`; `date_diff('day', due_date, reference_date)` | — | นิยาม overdue |
| E021 | [F] `src/ingest.py:3,27,161,181` | `python -m src.ingest --input … --reference-date …`; `EXIT_OK…EXIT_SYSTEM = 0,1,2,3`; `noop`/`succeeded` | — | CLI ingest, idempotency |
| E022 | [F] `src/metrics.py:74-117` | `get_run_info, list_projects, portfolio, by_project, overdue_detail, by_owner, data_quality_summary` | — | data-access layer |
| E023 | [F] `dashboard/app.py:39-41,148,188,238,255` | routes `/`, `/overdue`, `/executive-summary`; `generate_and_save`; `server = app.server` | — | โครงสร้างแอป |
| E024 | [F] `src/ai/provider.py:1,8-9,25-27` | `PROVIDER_NAME="openrouter"`, `MODEL_NAME="anthropic/claude-sonnet-5"`, `DEFAULT_TIMEOUT_SECONDS=60.0` | — | provider AI |
| E025 | [F] `Dockerfile:8,16,39,41,44,47`; `docker-compose.yml:9-18,30-31` | `USER appuser`, `EXPOSE 8050`, `HEALTHCHECK`; volume `duckdb-data:/app/data` | — | container/persistence |
| E026 | [F] `tests/test_*.py` (`rg -c '^def test_'`) | จำนวนสถิตต่อไฟล์ (H.1) | — | มี test code |
| E027 | [F] `README.md:7,20,27,77` | สถานะ, `docker compose up --build`, คำเตือน key, "ผลการทดสอบจริง (2026-10-02)" | — | เอกสารส่งมอบ/ข้อจำกัด |
| E028 | [F] `docs/data-analytics/AI_MODEL_SPEC.md:18`, `TESTING_STRATEGY.md:15` | สถานะ implement/ยืนยัน; "ผ่าน 277 test ณ เวลาที่เขียน" | — | คำกล่าวในเอกสาร (REPORTED) |
| E029 | [F] `DASHBOARD_SPEC.md:68`, `TASKS.md:109`, `tests/test_dashboard_app.py:237` | "ถอดออกจากหน้า — ผู้ใช้ตัดสินใจ 2026-10-02"; `assert find(tree, IDS.DQ_PANEL) is None` | — | การถอด CH-12 |
| E030 | [S] pytest/ruff/metrics รอบแรก | `127 passed in 18.77s`; `All checks passed!`; `14013 8597 5416 3531`; `1168 816 352 202`; `portfolio("nope")` = 0 | TIME_UNKNOWN | ผลรัน + ตัวเลขจริง |
| E031 | [S] `pytest --ignore=…hardening` + curl port 8771 | `160 passed in 41.22s`; `index=200 overdue page=200 exec page=200`; layout มี 2026-10-02 | TIME_UNKNOWN | ผลรัน + แอปตอบ |
| E032 | [S] pytest/ruff/ingest รอบที่ 3 | `260 passed in 61.11s`; `status: noop` | TIME_UNKNOWN | ผลรัน + idempotency |
| E033 | [S] pytest รอบตรวจ README | `277 passed in 74.06s`; `All checks passed!` | TIME_UNKNOWN | ผลรัน |
| E034 | [S] pytest หลังถอด CH-12 | `277 passed in 71.02s` | TIME_UNKNOWN | ผลรัน |
| E035 | [S] pytest ก่อน commit รอบ 2 + สแกน secret | `277 passed in 65.31s`; ไฟล์ที่เปลี่ยนที่มีค่า env key = 0 | TIME_UNKNOWN | ผลรัน + ไม่พบ key |
| E036 | [S] รายงาน agent แกนหลัก | "ingest exit 0; second ingest no-op; 14,013…; 0 duplicate pairs" | TIME_UNKNOWN | REPORTED (ผมตรวจซ้ำบางส่วน E030) |
| E037 | [S] รายงาน agent hardening | "133 tests; 8 bug fixes; 140k rows 1.7 s, RSS ~353 MB" | TIME_UNKNOWN | REPORTED |
| E038 | [S] รายงาน security review และ audit | ไม่พบ Critical/High; Medium: multi-line CSV, prompt injection | TIME_UNKNOWN | REPORTED |
| E040 | [S] ผล `docker version` | `client=29.8.1 server=29.8.1`; compose v5.5.1; ก่อนหน้า: `docker could not be found in this WSL 2 distro` | TIME_UNKNOWN | Docker พร้อมหลังผู้สอบเปิด Docker Desktop |
| E041 | [S] `docker compose build` | `Image cybersecurity-action-dashboard:latest Built` | TIME_UNKNOWN | build สำเร็จ |
| E042 | [S] `docker compose up -d` | `Up 18 seconds (healthy)`; log `status: succeeded`, `Listening at: http://0.0.0.0:8050`; หน้า `/ /overdue /executive-summary` = 200 | log 2026-10-02 04:35:34 +0000 | container ทำงาน |
| E043 | [S] `docker compose exec` | user `appuser`; `14013 8597 5416 3531`; P01 `1168 816 352 202` | TIME_UNKNOWN | ตัวเลขใน container |
| E044 | [S] restart | `status: noop … nothing written`; `Up 12 seconds (healthy)` | TIME_UNKNOWN | ข้อมูลคงอยู่/idempotent |
| E045 | [S] `run -e OPENAI_API_KEY=` | `no key -> configured: False` + ข้อความไทย | TIME_UNKNOWN | AI ปิดเมื่อไม่มี key |
| E046 | [S] `docker compose down`, `image ls`, `history` | volume `ai-tech-user-exam_duckdb-data` คงอยู่; image `495MB`; ค้นหา key ใน history = 0 | TIME_UNKNOWN | ไม่มี key ใน image |
| E047 | [S] `up -d --build` รอบหลังแก้ UI + ภาพ headless | `Up 6 seconds (healthy)`; ภาพ `/executive-summary` และ `/` (โหมดสว่าง) เมนู "Executive Summary" | TIME_UNKNOWN | UI หลังแก้ |
| E048 | [S] รัน `docker/entrypoint.sh` บนเครื่อง (พอร์ต 8772) | `run_id: 1 status: succeeded`; gunicorn `Listening at: http://127.0.0.1:8772`; `layout=200` | log 2026-10-02 11:33:51 +0700 | entrypoint ทำงาน |
| E050 | [S] เรียก `OpenRouterProvider.generate` | `OK in 21.1s, 3253 chars` (เนื้อหาร่างอยู่ใน session) | TIME_UNKNOWN | AI จริงสำเร็จ |
| E051 | [S] เรียก callback `exec-loading` ผ่าน Flask client | `All Projects 25.4s`, `P01 24.6s`; แถว `(1, None, …, 'openrouter', 'anthropic/claude-sonnet-5', 'exec-summary-v2', 3180)`, `(2, 'P01 - Network VA', …, 3383)`; reload แสดงสรุป | TIME_UNKNOWN | บันทึก+แสดงผล |
| E052 | [S] query DuckDB สำเนา | `P03 (809, 611)`, `P08 (757, 566)`, `P09 (109, 47)`; `A000017 Owner-033 46` | TIME_UNKNOWN | ตัวเลขในร่างตรง DB |
| E060 | [S] ผล `git push` | `* [new branch] main -> main`; `412dd1e..829d0b4 main -> main` | เวลา push UNKNOWN | push สำเร็จ |
| E061 | [S] `git ls-remote --heads origin` | ว่างเปล่า (ก่อน push); `412dd1e… refs/heads/main` (หลัง push แรก) | TIME_UNKNOWN | สถานะ remote ณ ตอนนั้น |
| E070 | [S] ภาพ #4 จากผู้สอบ | หน้า Executive Summary: เมนู "Executive Summary (draft)", ตัวอักษร Theme สีเข้มบนพื้นเข้ม | TIME_UNKNOWN | ปัญหาที่ผู้สอบเห็น |
| E071 | [S] ภาพ #5 จากผู้สอบ | แผง "Run & validation summary" | TIME_UNKNOWN | แผงที่ผู้สอบสั่งถอด |
| E072 | [S] ภาพ #6 จากผู้สอบ | Cloudflare "Bad gateway Error code 502", `cybersec-dashboard.cyber1.ragnar-ai.dev`, `2026-10-02 04:56:00 UTC` | 04:56:00 UTC (11:56 +07); เทียบช่วงสอบ UNKNOWN | ข้อผิดพลาดบน URL ที่ deploy |
| E073 | [S] ข้อความผู้สอบ | วางข้อความ "ยังไม่ได้ตั้งค่า OPENAI_API_KEY และ OPENAI_BASE_URL จึงสร้าง AI Summary ไม่ได้…" และถามว่าต้องตั้งใน Coolify | TIME_UNKNOWN | INFERRED ว่าแอปตอบได้ ณ จุดหนึ่ง |
| E074 | [S] `which coolify` | `coolify not found` | TIME_UNKNOWN | AI ไม่มีสิทธิ์ตรวจ Coolify |
| E075 | [F] `rg -n -i coolify --glob '!ddd/**' .` | ไม่พบผล | AFTER_EXAM | ไม่มี config Coolify ใน repo |
| E080 | [S] pasted_content แรก (ข้อความโจทย์) | "…ใช้วันที่อ้างอิงตามโจทย์เพื่อให้ผลตรวจสอบตรงกัน" (ไม่มีวันที่) | ต้น session | โจทย์/วันอ้างอิงไม่ระบุ |
| E081 | [S] ข้อความผู้สอบหลายข้อความ | ตัวอย่าง: "ทำทุกเอกสาร…"; "เอาแบบที่ 1 ก่อนใน iterate แรก"; "ใช้แค่ OPENAI_API_KEY, OPENAI_BASE_URL, anthropic/claude-sonnet-5 ไม่เกี่ยวกับ aix"; "ส่งได้"; "เอา (draft) ออก…"; "ถ้าแก้ไขเสร็จแล้ว ให้ git commit และ git push เข้า main" | TIME_UNKNOWN | การตัดสินใจ/คำสั่งของผู้สอบ |
| E082 | [S] ตัวนับ `<total_tokens>` ที่ harness แสดง | 15,000,000 ตอนเริ่ม → ~14.99 ล้าน | — | **UNKNOWN** ความหมายไม่ระบุ ไม่ใช้เป็นยอดใช้ |
| E083 | [S] ข้อมูลสภาพแวดล้อมใน system context | Claude Code; โมเดล Sonnet 5.5 | — | เครื่องมือที่ใช้ |
| E090 | [S] ข้อความสั่งทำรายงาน | "ทำเลย ชื่อผู้สอบ Teera La-orkarnchakakul (TEE) เอาไฟล์ไว้ใน repo นี้นะ"; ข้อความระบุ "งานสอบ Practical สิ้นสุดแล้ว" | AFTER_EXAM | ชื่อผู้สอบ, ที่เก็บไฟล์, งานสอบสิ้นสุดแล้ว (REPORTED) |

### ข้อมูลที่กรรมการต้องตรวจเพิ่ม
1. เวลาเริ่ม–หมดเวลาสอบ และ commit ที่ส่งสอบ (ไม่มีในหลักฐานนี้)
2. เวลา push จริงบน GitHub (เช่น จากหน้า commit/push log ของ remote)
3. Deployment record บน Coolify: deployment ID, commit ที่ deploy, เวลา, log, สถานะหลังเจอ 502
4. สถานะ persistent storage (volume `/app/data`) และ env vars ที่ตั้งบน Coolify
5. วันที่อ้างอิงที่ถูกต้องตามต้นฉบับโจทย์ (ตัวเลข overdue 3,531 ขึ้นกับ 2026-10-02)
6. ผู้สร้างและเวลาของ `plan.md`, `ddd/*.json`, CSV ที่มีอยู่ก่อน session
7. ผลการประเมินคุณภาพร่าง AI เชิงทางการ (EV-01..05) และการตรวจหน้าจอโหมดมืด/AG Grid ด้วยตา

---

### บันทึกการตรวจรายงานก่อนส่ง
- ข้อสรุปสำคัญอ้าง Evidence ID ที่มีใน Index (E001–E090 ตามที่ใช้)
- แยกคำกล่าว (REPORTED) ออกจากผลที่ยืนยันได้ (VERIFIED) และแยกช่วง AFTER_EXAM (การรวบรวม) ออกจากหลักฐานที่ TIME_UNKNOWN
- ไม่คัดลอกค่า API key, `.env` หรือ environment; อีเมลผู้เขียน commit ถูกปกปิด; ไม่ใช้ข้อมูลส่วนบุคคลอื่น
- ระหว่างรวบรวม สร้างไฟล์เพียงไฟล์นี้ ไม่แก้ไฟล์อื่น/Git state และไม่รันคำสั่งที่เปลี่ยนสถานะ (การ commit/push ไฟล์นี้เกิดภายหลังตามคำสั่งผู้สอบ)
- ข้อมูลที่ขัดกัน: ข้อความ commit `412dd1e` ("ยังไม่เคยเรียก OpenRouter จริง") vs `829d0b4`/E050–E051 (เรียกจริงแล้ว) — แสดงทั้งสองฝั่งตามลำดับเหตุการณ์
