# Visualization Design Spec

```yaml
doc_id: viz_design_spec
filename: VIZ_DESIGN_SPEC.md
version: 1.0.0
status: draft
depends_on: [stakeholders, metric_spec]
also_references: [dashboard_spec]
generated_from: ddd-data-analytics v2.8.0
project: Cybersecurity Project Action Dashboard
```

เอกสารนี้เป็นแหล่งอ้างอิงเดียว (canonical) ของ **chart type, สี/ฟอนต์, interaction และ accessibility** ของทุก dashboard; DASHBOARD_SPEC.md (มีแล้ว) ต้องเลือก chart ตาม `chart_type_matrix` และ import `viz_theme.py` จากบล็อกโค้ดด้านล่างเท่านั้น Metric ID (MET-xx) ตาม METRIC_SPEC.md, Stakeholder ID (STK-xx) และ enum `data_literacy_level` ตาม STAKEHOLDERS.md — ไม่นิยามซ้ำ

เครื่องมือ: Plotly (หลัก), Dash AG Grid (ตาราง), Vega-Altair (ทางเลือก, ใช้กับ prototype/EDA เท่านั้น ต้องใช้ token สีชุดเดียวกัน) ไม่ผูกกับชื่อองค์กรใด

> หมายเหตุหลักฐาน: `references/data-to-viz/*.md` ไม่อยู่ใน repo แต่พบที่ `/mnt/wslg/distro/home/teera/tech-user-session/ddd/references/data-to-viz/` — ตรวจ barplot/donut/line/heatmap แล้ว สอดคล้องกับ anti-patterns (เรียงแท่งตามค่า, ไม่ใช้ barplot กับหลายค่าต่อกลุ่ม, heatmap ต้อง normalize/เลือกสีให้เหมาะ, line แกน y ไม่จำเป็นต้องเริ่มที่ 0 ส่วน bar ต้องเริ่มที่ 0) ไฟล์ treemap/sankey/violin/choropleth/scatter/histogram ยังไม่ได้ตรวจ (ไม่มี chart เหล่านี้ใน v1)

## Enum ที่เอกสารนี้เป็นเจ้าของ

### complexity_level (owner: VIZ_DESIGN_SPEC.md)

| value | ความหมาย | ตัวอย่าง chart |
|---|---|---|
| `basic` | อ่านค่าตรงจากความยาว/ตำแหน่ง/ตัวเลข ไม่ต้องตีความรูปแบบ | KPI card, bar (single series), line, table |
| `intermediate` | ต้องเปรียบเทียบหลายมิติหรืออ่านรูปแบบ | stacked/grouped bar, heatmap, scatter, crosshair |
| `advanced` | ต้องเข้าใจ encoding ที่ซับซ้อนหรือเปลี่ยนตามเวลา | animated, multi-axis, custom |

ลำดับ: `basic` < `intermediate` < `advanced` (ค่าตรงกับลำดับของ `data_literacy_level`)

### chart_type (owner: VIZ_DESIGN_SPEC.md)

| value | complexity_level | หมายเหตุ |
|---|---|---|
| `kpi_card` | basic | ค่าเดี่ยว + label + reference date |
| `bar` | basic | แท่งเดียว series เดียว เรียงลำดับ (แนวนอนเมื่อ label ยาว) |
| `line` | basic | time-series เมื่อมีจุดเวลาตั้งแต่ 2 จุดขึ้นไปจริงเท่านั้น |
| `table` | basic | Dash AG Grid |
| `stacked_bar` | intermediate | ส่วนประกอบ part-to-whole ต่อ category |
| `grouped_bar` | intermediate | เปรียบเทียบหลาย series ต่อ category |
| `heatmap` | intermediate | 2 categorical dimension × count |
| `scatter` | intermediate | ความสัมพันธ์ 2 measure |
| `donut` | basic (จำกัดใช้) | ใช้ได้เฉพาะเงื่อนไขใน CT-05 |
| `multi_axis` | advanced | **ไม่ใช้ใน v1** (ดู Anti-patterns) |
| `animated` | advanced | **ไม่ใช้ใน v1** |

## Chart Type Matrix

### Metric Type Classification

| MT ID | Metric type | Metric (จาก METRIC_SPEC) |
|---|---|---|
| MT-01 | single value (scope เดียว) | MET-01, MET-02, MET-03, MET-04, MET-06, MET-07 ที่ระดับ portfolio/project |
| MT-02 | categorical count | MET-01..MET-04, MET-08 ซอยด้วย `project_name` / `owner` / `status` |
| MT-03 | proportion / ratio | MET-06 `completion_rate` (ต่อ project); ส่วนประกอบ completed (MET-02) / open non-overdue (MET-08) / overdue (MET-04) |
| MT-04 | ranking (per-record measure) | MET-05 `days_overdue` ต่อ overdue action; MET-04 ต่อ `owner` เรียงลำดับ |
| MT-05 | time-series | MET-04 ซอยตาม `due_date` (กระจายวันครบกำหนด, ไม่ใช่ trend ข้าม run) — trend ข้าม run = **ไม่นิยามใน v1** |

ทุก metric (MET-01..08) ถูกจัดเข้าอย่างน้อยหนึ่ง MT; ไม่มี metric ที่ไม่มี chart

### Matrix (canonical — DASHBOARD_SPEC ต้องตามตารางนี้)

| CT ID | Metric type | chart_type แนะนำ | Grain / ตัวแปรตาม grain | Anti-patterns (ห้าม) | min literacy |
|---|---|---|---|---|---|
| CT-01 | MT-01 | `kpi_card` | 1 scope ต่อ run; แสดง `reference_date` และ run_id ใกล้การ์ด; **ไม่มี** ลูกศร trend/สีเขียว-แดงจนกว่ามี target อนุมัติ (target = `null`) | gauge/speedometer; สีแดงโดยไม่มี threshold | basic |
| CT-02 | MT-02 (ต่อ `project_name`, 12 รายการ) | `bar` แนวนอน เรียงจากมากไปน้อย; ต้องการแยกส่วนประกอบ → `stacked_bar` | grain = project; ต่อ `owner` (96 รายการ) → แสดง top-N + table ไม่ใช่ bar ครบ 96 แท่ง (N = `null`, owner `{{DASHBOARD_DEVELOPER}}`) | pie/donut กับ >3 ส่วน; 3D; แกน y ไม่เริ่มที่ 0; เรียงตามตัวอักษรโดยไม่จำเป็น | basic (`bar`); intermediate (`stacked_bar`) |
| CT-03 | MT-03 (`completion_rate`) | `bar` (0-100% แกนคงที่) | grain = project | line เชื่อมระหว่าง project (category ไม่มีลำดับ); pie ต่อ project ทีละใบ | basic |
| CT-04 | MT-04 (`days_overdue`, `overdue_actions` ต่อ owner) | `table` เรียง `days_overdue` DESC (ค่าเริ่มต้น); ranking ต่อ owner → `bar` แนวนอน | grain = 1 overdue action (table) / 1 owner (bar) | โครงสร้าง leaderboard/score ที่ implied ผลงานบุคคล (plan ห้าม owner performance score); ตัดทอนแกนเพื่อขยายความต่าง | basic |
| CT-05 | MT-03 (part-to-whole) | `donut` เฉพาะ ≤3 ส่วน, scope เดียว, ผลรวม = 100%, มีตัวเลข/ % กำกับ; มิฉะนั้นใช้ `stacked_bar` หรือ `bar` | grain = 1 scope | donut กับหลาย scope เปรียบเทียบกัน; ส่วนเล็กจนอ่านมุมไม่ได้ | basic |
| CT-06 | MT-05 (due_date distribution) | `bar` ตามวัน/สัปดาห์; `line` เฉพาะ daily ต่อเนื่อง | daily → `line`; weekly/monthly → `bar` (grouped_bar เมื่อเทียบ series) | pie; รวม bucket จนซ่อน overdue ที่เลยมาแล้ว | basic |
| CT-07 | MT-02 สองมิติ (`project_name` × `owner` count) | `heatmap` (optional) | grain = project × owner | ใช้ rainbow colormap; ใช้กับ audience basic | intermediate |
| CT-08 | multi-measure | — (`scatter`, `multi_axis`, `animated` **ไม่อนุญาตใน v1**: ไม่มี metric ที่ต้องการ และห้ามสร้าง risk/health/performance score) | — | dual-axis ที่ผสมหน่วยต่างกัน | advanced (ถ้าอนาคตมี metric รองรับ) |
| CT-09 | MT-02 + MT-03 หลายคอลัมน์ต่อ project (project summary table: Total / Completed / Open / Overdue / Completion Rate; MET-01..04, MET-06) | `table` (Dash AG Grid) 1 แถวต่อ `project_name`; sort ค่าเริ่มต้น = ตาม project; มีค่าตัวเลขตรงทุกเซลล์ (เป็น data-table alternative ของ CT-02/CT-03 ด้วย) | grain = project (12 รายการ) | คอลัมน์ rank/score; สี alert ในเซลล์เมื่อ threshold = `null`; รวมเซลล์เป็น % โดยไม่มีตัวเลขดิบ | basic |

หมายเหตุ Page 1: plan.md §11 อนุญาต grouped/stacked bar หรือแยก chart "Total / Completed / Overdue by Project" แต่ stacked/grouped = `intermediate` และ STK-01 (primary, `basic`) → เวอร์ชันแสดงผลค่าเริ่มต้นต้องเป็นชุด `bar` ธรรมดา (CT-02) และ `stacked_bar` เป็น view ทางเลือกสำหรับ STK-02/03 ภายใต้ Gate Rule

## Color & Theme Spec

### Primary Palette (data series — light / dark, hex)

| token | light | dark | ใช้กับ |
|---|---|---|---|
| series_1 | `#0072B2` | `#56B4E9` | series หลัก / completed |
| series_2 | `#C24E00` | `#FF8A4C` | overdue |
| series_3 | `#B87800` | `#F0B429` | open (ยังไม่เลยกำหนด) |
| series_4 | `#007A5A` | `#2EC4A0` | series เสริม |
| series_5 | `#8E4A9E` | `#C792EA` | series เสริม |
| series_6 | `#5F6B7A` | `#9AA5B1` | neutral / other |

ตรวจ contrast (คำนวณแล้วเมื่อสร้างเอกสาร): light บนพื้น `#FFFFFF` ทุกสี ≥ 3.67:1; dark บนพื้น `#121417` ทุกสี ≥ 7.37:1; ข้อความ `#1B1F24` บน `#FFFFFF` = 16.56:1, `#E6EAF0` บน `#121417` = 15.28:1

### Semantic Colors

| semantic | light | dark | ความหมาย |
|---|---|---|---|
| positive | `#007A5A` | `#2EC4A0` | ดีขึ้น/บรรลุ (ใช้เมื่อมี target อนุมัติเท่านั้น) |
| alert | `#B42318` | `#FF6B5E` | เกิน threshold / overdue วิกฤต (threshold = `null` → ยังไม่ใช้เป็น alert) |
| warning | `#B87800` | `#F0B429` | ใกล้ threshold |
| neutral | `#5F6B7A` | `#9AA5B1` | ข้อมูลทั่วไป |

กฎ: สีอ้างผ่านชื่อ semantic role ของ chart (`completed`, `open_non_overdue`, `overdue`) ไม่ผูกกับค่า enum `action_status` (นิยามที่ DATA_MODEL_SPEC) และ **ห้ามใช้สีเป็นช่องทางเดียวในการสื่อความหมาย** (ต้องมี label/ข้อความ/pattern ประกอบ)

### Font Rules

| ส่วน | family | size (px) | weight |
|---|---|---|---|
| chart title | system sans (รองรับ Thai) | 16 | 600 |
| axis label / legend | เหมือนกัน | 12 | 400 |
| tick label | เหมือนกัน | 11 | 400 |
| tooltip | เหมือนกัน | 12 | 400 (ชื่อ metric 600) |
| annotation | เหมือนกัน | 11 | 400 |
| KPI value | เหมือนกัน | 28 | 700 |

ตัวเลขใช้ tabular figures และ format ด้วย thousands separator

### viz_theme code block (คัดลอกเป็น `viz_theme.py` ตรง ๆ)

```python
"""viz_theme.py - shared visualization theme (source: VIZ_DESIGN_SPEC.md v1.0.0)."""

COLOR_PALETTE = {
    "light": {
        "background": "#FFFFFF",
        "text": "#1B1F24",
        "text_muted": "#4B5563",
        "grid": "#E3E7EC",
        "series": ["#0072B2", "#C24E00", "#B87800", "#007A5A", "#8E4A9E", "#5F6B7A"],
        "semantic": {"positive": "#007A5A", "alert": "#B42318",
                     "warning": "#B87800", "neutral": "#5F6B7A"},
        "roles": {"completed": "#0072B2", "open_non_overdue": "#B87800",
                  "overdue": "#C24E00"},
    },
    "dark": {
        "background": "#121417",
        "text": "#E6EAF0",
        "text_muted": "#A7B0BC",
        "grid": "#2A2F36",
        "series": ["#56B4E9", "#FF8A4C", "#F0B429", "#2EC4A0", "#C792EA", "#9AA5B1"],
        "semantic": {"positive": "#2EC4A0", "alert": "#FF6B5E",
                     "warning": "#F0B429", "neutral": "#9AA5B1"},
        "roles": {"completed": "#56B4E9", "open_non_overdue": "#F0B429",
                  "overdue": "#FF8A4C"},
    },
    # colorblind-safe variant: blue / grey / vermillion differ in hue AND lightness
    "cvd_light": {
        "background": "#FFFFFF",
        "text": "#1B1F24",
        "text_muted": "#4B5563",
        "grid": "#E3E7EC",
        "series": ["#0072B2", "#C24E00", "#5F6B7A", "#B87800", "#8E4A9E", "#007A5A"],
        "semantic": {"positive": "#0072B2", "alert": "#C24E00",
                     "warning": "#5F6B7A", "neutral": "#5F6B7A"},
        "roles": {"completed": "#0072B2", "open_non_overdue": "#5F6B7A",
                  "overdue": "#C24E00"},
    },
    "cvd_dark": {
        "background": "#121417",
        "text": "#E6EAF0",
        "text_muted": "#A7B0BC",
        "grid": "#2A2F36",
        "series": ["#56B4E9", "#FF8A4C", "#9AA5B1", "#F0B429", "#C792EA", "#2EC4A0"],
        "semantic": {"positive": "#56B4E9", "alert": "#FF8A4C",
                     "warning": "#9AA5B1", "neutral": "#9AA5B1"},
        "roles": {"completed": "#56B4E9", "open_non_overdue": "#9AA5B1",
                  "overdue": "#FF8A4C"},
    },
}

FONT_RULES = {
    "family": ("system-ui, -apple-system, 'Segoe UI', 'Noto Sans Thai', "
               "'Sarabun', Roboto, Arial, sans-serif"),
    "title": {"size": 16, "weight": 600},
    "axis": {"size": 12, "weight": 400},
    "tick": {"size": 11, "weight": 400},
    "tooltip": {"size": 12, "weight": 400, "name_weight": 600},
    "annotation": {"size": 11, "weight": 400},
    "kpi_value": {"size": 28, "weight": 700},
}

CHART_DEFAULTS = {
    "margin": {"l": 56, "r": 24, "t": 48, "b": 48},
    "bar_gap": 0.25,
    "y_axis_zero_based": True,          # bar charts must start at 0
    "number_format": ",d",              # thousands separator
    "percent_format": ".1%",
    "transition_ms": 0,                 # no animation on data refresh (see Interaction Spec)
    "load_transition_ms": 300,
    "reduced_motion_ms": 0,
    "hovermode": "closest",
    "show_legend_max_series": 6,
}


def get_palette(mode="light", colorblind=False):
    """Return palette dict. mode: 'light' | 'dark'."""
    key = ("cvd_" if colorblind else "") + mode
    return COLOR_PALETTE[key]


def plotly_layout(mode="light", colorblind=False):
    """Return a dict usable as plotly Figure.update_layout(**plotly_layout())."""
    p = get_palette(mode, colorblind)
    return {
        "paper_bgcolor": p["background"],
        "plot_bgcolor": p["background"],
        "colorway": p["series"],
        "font": {"family": FONT_RULES["family"], "size": FONT_RULES["axis"]["size"],
                 "color": p["text"]},
        "title": {"font": {"size": FONT_RULES["title"]["size"], "color": p["text"]}},
        "margin": CHART_DEFAULTS["margin"],
        "hovermode": CHART_DEFAULTS["hovermode"],
        "xaxis": {"gridcolor": p["grid"], "tickfont": {"size": FONT_RULES["tick"]["size"]}},
        "yaxis": {"gridcolor": p["grid"], "tickfont": {"size": FONT_RULES["tick"]["size"]},
                  "rangemode": "tozero" if CHART_DEFAULTS["y_axis_zero_based"] else "normal"},
        "transition": {"duration": CHART_DEFAULTS["transition_ms"]},
    }
```

Vega-Altair (ถ้าใช้) ต้องอ่านค่าจาก `COLOR_PALETTE` เดียวกัน ห้ามกำหนดสีซ้ำ

## Interaction Spec

### Tooltip Format

รูปแบบมาตรฐาน: `{metric label} : {value} {unit}` / `{dimension}: {value}` / `Reference date: {reference_date}` — label ยึด BUSINESS_GLOSSARY; unit = "รายการ" (count), "วัน" (`days_overdue`), "%" (rate) `% change` และ period-over-period = **ไม่แสดงใน v1** (ไม่มีนิยาม trend ข้าม run)

| chart_type | tooltip เนื้อหา | Drill-down / click-through target |
|---|---|---|
| `kpi_card` | label, value, reference_date, run_id | ไป Overdue Actions page (เมื่อ MET-04) หรือ project table; ใน scope filter เดิม |
| `bar` | dimension, metric label, value, สัดส่วนเทียบ total ของ scope | ตั้ง global Project filter = แท่งที่คลิก (project) / กรอง Overdue Actions ด้วย `owner` (แท่ง owner) |
| `stacked_bar` / `grouped_bar` | dimension + ทุก series ของ category นั้น + total | เหมือน `bar`; คลิก segment overdue → Overdue Actions กรอง project |
| `line` | จุดเวลา, metric label, value, unit | กรอง table ตามช่วงวันที่ที่คลิก |
| `table` | ไม่ใช้ tooltip ทับ; cell ที่ตัดข้อความแสดงค่าเต็มใน tooltip | คลิกแถว = เลือกแถว (ไม่ link ออก); ไม่มี external link |
| `donut` | ชื่อส่วน, value, % | กรอง table ตาม role ที่คลิก |
| `heatmap` | แถว, คอลัมน์, count | กรอง table ด้วยคู่ project × owner |
| `scatter`, `multi_axis`, `animated` | ไม่ใช้ใน v1 (กำหนดเมื่อ chart ถูกอนุมัติ) | `null` |

ชื่อหน้า/ID ปลายทางกำหนดที่ DASHBOARD_SPEC.md: Portfolio Overview = `DASH-01`, Overdue Actions = `DASH-02`, Executive Summary (bonus, draft) = `DASH-03`

### Crosshair Behavior

crosshair/spike line = `intermediate` — ใช้เฉพาะ `line` ที่มีจุดเวลา ≥ 2 จุด และเฉพาะ audience ที่ผ่าน Gate Rule; ไม่ใช้กับ bar/table/kpi_card; cross-chart sync เปิดได้เมื่อหลาย line chart ใช้แกนเวลาเดียวกัน (ค่าเริ่มต้นปิด) เนื่องจาก v1 ไม่มี time-series ข้าม run จึงยังไม่มี crosshair ใช้งานจริง

### Animation Rules

| สถานการณ์ | กฎ |
|---|---|
| Page load | fade/ease-out ได้ ≤ 300 ms (`load_transition_ms`) |
| Data refresh (เปลี่ยน filter / run ใหม่) | ไม่ animate (`transition_ms = 0`) เพื่อไม่ให้ผู้ใช้เข้าใจผิดว่าตัวเลขกำลังเปลี่ยนตามเวลา |
| `prefers-reduced-motion` | ปิดทั้งหมด |
| animated chart | `advanced` เท่านั้น; ไม่ใช้ใน v1 |

easing = `cubic-bezier(0.2, 0, 0, 1)` (ease-out)

## Accessibility Guidelines

- **Contrast (WCAG 2.1 AA):** ข้อความปกติ ≥ 4.5:1; large text และ UI component/graphical object ≥ 3:1 — ทุกสีใน palette ผ่านตามตัวเลขข้างบน; ข้อความใน bar ต้องตรวจเป็นคู่ต่อสี (text on fill) ก่อนใช้
- **Colorblind-safe:** ใช้ `cvd_light` / `cvd_dark` (สลับด้วย toggle; ค่าเริ่มต้น = ตามการตั้งค่าผู้ใช้ `null` จนกว่าตัดสิน) แยก hue และ lightness สำหรับ completed / open / overdue; เสริมด้วย direct label หรือ pattern เสมอ ทั้ง protanopia/deuteranopia/tritanopia — การตรวจด้วย simulator **ยังไม่ได้ทำ** (owner `{{DASHBOARD_DEVELOPER}}`)
- **Screen reader:** ทุก chart มี `aria-label` รูปแบบ "{chart title}: {summary}. Reference date {date}" และ alt text สรุปข้อสังเกตหลักจากข้อมูลจริง (ห้ามฝังตัวเลขตายตัว สร้างจากข้อมูล); ทุก chart มีทางเลือกเป็น data table (AG Grid หรือ `<table>` ซ่อนได้); KPI card ใช้ `role="status"` สำหรับการอัปเดต
- **Keyboard:** Tab เข้า chart/ตาราง; Enter = drill-down; ลูกศรซ้าย/ขวา = เลื่อนระหว่างแท่งและแสดง tooltip; Esc = ปิด tooltip; focus indicator มองเห็นชัด (≥ 3:1); AG Grid ใช้ keyboard navigation ของ AG Grid

## Data Literacy Guard Rails

**GIST:** chart ที่ซับซ้อนเกินระดับผู้อ่านไม่ได้แค่อ่านยาก แต่ทำให้ตัดสินใจผิด เพราะผู้อ่านจะตีความสิ่งที่คุ้นเคยที่สุดในภาพแทนสิ่งที่ภาพบอกจริง — guard rail นี้เป็นเรื่องความถูกต้อง ไม่ใช่ความสวยงาม

### Complexity Levels

นิยามค่า enum `complexity_level` อยู่ด้านบนของเอกสารนี้ (owner)

### Literacy Mapping

| Stakeholder | data_literacy_level (STAKEHOLDERS.md) | max `complexity_level` | chart_type ที่อนุญาต |
|---|---|---|---|
| STK-01, STK-04 | basic | basic | `kpi_card`, `bar`, `line`, `table`, `donut` (CT-05) |
| STK-02, STK-03, STK-05 | intermediate | intermediate | basic + `stacked_bar`, `grouped_bar`, `heatmap`, `scatter`, crosshair |
| STK-06 | advanced | advanced | ทุก chart_type (ไม่มีใช้ใน v1 สำหรับ `multi_axis`, `animated`) |

หมายเหตุ: ระดับ literacy ทั้งหมดเป็น `[ASSUMPTION]` ตาม STAKEHOLDERS.md — ถ้าถูกปรับ ตารางนี้ต้องปรับตาม

### Gate Rule

ห้ามใช้ `complexity_level` สูงกว่า `data_literacy_level` ของ target audience ของ chart นั้น กรณีหน้า/ chart มีหลายกลุ่ม: ใช้ระดับต่ำสุดของกลุ่ม **primary** (ตาม METRIC_SPEC "Primary consumer") เป็นค่าเริ่มต้น และให้ view ที่ซับซ้อนกว่าเป็นตัวเลือกที่ผู้ใช้เปิดเอง (ระบุ min literacy ในหัว chart) Page ที่ primary = STK-01/STK-04 ⇒ `basic`

### Override Process

การ override ต้องมี (1) การลงนามจาก stakeholder เจ้าของ audience (`{{MEETING_CHAIR}}` หรือผู้แทน) (2) แผน training สำหรับ audience นั้น (3) บันทึกใน ANALYTICS_CHANGELOG.md พร้อมวันที่มีผล ผู้อนุมัติสุดท้าย = `{{PROJECT_SPONSOR}}`; ระยะเวลา training = `null` (calibration: ตกลงกับ stakeholder; owner `{{DATA_STEWARD}}`)

## Open Questions

1. ย้าย/คัดลอก `references/data-to-viz/` เข้า repo เพื่อให้ตรวจซ้ำได้ (ปัจจุบันอยู่นอก repo)
2. Page 1 ค่าเริ่มต้นของ STK-01 (basic) = `bar` ธรรมดา ตกลงหรือไม่ แทน stacked bar ใน plan.md §11
3. จำนวน top-N owner ใน bar (CT-02) และ default colorblind toggle = `null` — owner `{{DASHBOARD_DEVELOPER}}`
4. Trend ข้าม run (MT-05 line, % change) ต้องการหรือไม่ — ถ้าต้องการต้องเพิ่ม metric ใน METRIC_SPEC ก่อน
5. (ปิดแล้ว) ID dashboard ปลายทาง drill-down = DASH-01/02/03 ตาม DASHBOARD_SPEC.md
