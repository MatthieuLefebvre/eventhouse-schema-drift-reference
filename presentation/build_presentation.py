from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "presentation" / "eventhouse-schema-drift-reference.pptx"
ARCHITECTURE_IMAGE = ROOT / "docs" / "images" / "target-architecture.png"

BACKGROUND = RGBColor(14, 22, 29)
INK = RGBColor(8, 15, 20)
TEXT = RGBColor(235, 242, 244)
MUTED = RGBColor(170, 190, 198)
PANEL = RGBColor(27, 41, 50)
PANEL_BORDER = RGBColor(60, 82, 92)
BLUE = RGBColor(0, 120, 212)
TEAL = RGBColor(0, 133, 119)
AMBER = RGBColor(230, 126, 34)
RED = RGBColor(196, 43, 28)
WHITE = RGBColor(255, 255, 255)

SLIDES = [
    {"title": "Move schema drift from Spark to Eventhouse", "bullets": ["A step-by-step customer demo", "Prove stable schemas, preserved drift, and governed promotion"]},
    {"title": "Start with today's Spark journey", "bullets": ["Telemetry lands in Eventhouse", "A notebook exports the batch through the Kusto connector", "Spark infers JSON, flattens, compares schemas, and manages buffers", "Delta writes require watermarks and merge orchestration"], "visual": "spark"},
    {"title": "Why the current loop is less efficient", "bullets": ["Routine processing moves data out of its serving engine", "Every run pays Spark startup and JSON inference cost", "Parallel bulk reads compete for export capacity", "Buffers, watermarks, and merge jobs increase operational state"], "visual": "cost"},
    {"title": "What the demo builds instead", "bullets": ["Raw ingestion remains the replay point", "Update policies create stable typed tables", "Unknown values remain in residual JSON", "A drift policy creates review evidence", "Arrays become child rows"], "visual": "architecture"},
    {"title": "Meet the message we will follow", "bullets": ["Controller 01 reports normal operating values", "The producer adds serviceCountdownHours: 120", "The target table does not have that column yet", "Success means preserving 120 without breaking typed ingestion"], "code": '"sourceType":"controller",\n"schemaVersion":2,\n"telemetry": {\n  "controllerStatus":"running",\n  "engineHours":1251.0,\n  "fuelConsumption":8.2,\n  "serviceCountdownHours":120\n}'},
    {"title": "Step 1: raw mapping loses nothing", "bullets": ["Stable envelope values become columns", "DropMappedFields keeps the remaining payload", "No landing-table alteration is needed"], "code": 'SourceType     controller\nSchemaVersion  2\nRawRecord      {\n "payload":{"telemetry":{\n  ...,\n  "serviceCountdownHours":120\n }}}'},
    {"title": "Step 2: typed row stays predictable", "bullets": ["Explicit casts produce the approved columns", "bag_remove_keys moves the new key to residual JSON", "Existing consumers see the same table schema"], "code": 'ControllerStatus  running\nEngineHours       1251.0\nFuelConsumption   8.2\nResidualTelemetry {\n "serviceCountdownHours":120\n}'},
    {"title": "Step 3: policies process it automatically", "bullets": ["The typed policy writes the controller row", "The drift policy examines the same raw message", "No scheduled connector export or watermark is required"], "code": '{"Source":"RawTelemetry",\n "Query":"TransformControllerTelemetry()",\n "IsTransactional":false}\n\nRaw row  →  typed row\n         →  drift evidence'},
    {"title": "Step 4: drift becomes review evidence", "bullets": ["bag_keys discovers serviceCountdownHours", "gettype records long and a sample value of 120", "Known processing continues while the field is reviewed"], "code": 'SourceType    controller\nFieldPath     serviceCountdownHours\nObservedType  long\nSampleValue   120\n\nbag_keys + mv-expand\n+ set_has_element + gettype'},
    {"title": "A second example: two zones become rows", "bullets": ["One cooling-unit message contains zones 1 and 2", "mv-expand produces two stable child rows", "An empty zones array produces zero child rows"], "code": 'Device      Zone  Mode     Return  Setpoint\ncooling-01  1     cool     2.8     2.0\ncooling-01  2     defrost  5.1     4.0\n\n| mv-expand Zone=Zones'},
    {"title": "Step 5: promote the reviewed field", "bullets": ["Add ServiceCountdownHours:real", "Revise and schema-check the stored function", "Replay only the approved interval", "The residual bag is now empty for this message"], "code": 'BEFORE\nResidual {"serviceCountdownHours":120}\n\nAFTER\nServiceCountdownHours  120.0\nResidual               {}\n\n.alter-merge + .set-or-append'},
    {"title": "Alert only when action is needed", "bullets": ["Aggregate repeated observations instead of alerting per message", "Example threshold: 10 observations in 15 minutes", "Send field, type, sample, assets, and first/last seen", "Create or update one review ticket per source and field"], "code": 'controller\nserviceCountdownHours\nType       long\nSample     120\nAssets     47\nEvents     8,212\n\n→ Teams  → DATA-1842'},
    {"title": "People make the promotion decision", "bullets": ["Data operations confirms ingestion health", "Source owner confirms the release", "Domain owner defines meaning and unit", "Data engineer profiles quality and usage", "Platform engineer submits tested KQL", "Consumer owner and approver authorize deployment"], "visual": "review"},
    {"title": "The engineer sees one operational view", "bullets": ["Ingestion rate and raw-to-target gap", "New fields and drift trend", "Type-conversion failures", "Residual governance backlog", "Array row amplification", "Alert evaluation runs even when the dashboard is closed"], "visual": "dashboard"},
    {"title": "Review produces one of three outcomes", "bullets": ["Promote: PR, approvals, deploy, monitor, bounded backfill", "Keep dynamic: record rationale and suppress duplicate tickets", "Reject: quarantine or ask the producer to fix its contract", "Never let drift detection alter production schemas automatically"], "visual": "decision"},
    {"title": "Adopt with evidence, not promises", "bullets": ["Shadow one source type first", "Benchmark policy CPU, ingestion latency, and array amplification", "Validate failure monitoring and bounded replay", "Measure duplicate arrivals before choosing a lookback", "Retire Spark bulk reads only after completeness gates pass"], "visual": "adopt"},
]


def load_font(size: int):
    candidates = (
        "arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def add_textbox(slide, x, y, width, height, text, size=20, color=TEXT, bold=False):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(width), Inches(height))
    frame = shape.text_frame
    frame.clear()
    paragraph = frame.paragraphs[0]
    paragraph.text = text
    paragraph.font.name = "Aptos"
    paragraph.font.size = Pt(size)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = color
    return shape


def add_header(slide, title, number):
    add_textbox(slide, 0.7, 0.45, 11.8, 0.6, title, 28, TEXT, True)
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(1.16), Inches(1.15), Inches(0.07))
    accent.fill.solid()
    accent.fill.fore_color.rgb = BLUE
    accent.line.fill.background()
    add_textbox(slide, 12.2, 0.5, 0.5, 0.4, f"{number:02}", 11, BLUE, True)


def add_bullets(slide, bullets):
    shape = slide.shapes.add_textbox(Inches(0.95), Inches(1.55), Inches(7.0), Inches(4.95))
    frame = shape.text_frame
    frame.clear()
    for index, bullet in enumerate(bullets):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = bullet
        paragraph.level = 0
        paragraph.font.name = "Aptos"
        paragraph.font.size = Pt(20 if len(bullets) > 5 else 22)
        paragraph.font.color.rgb = TEXT
        paragraph.space_after = Pt(18)
        paragraph.text = f"•  {bullet}"


def add_code(slide, code):
    panel = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.25), Inches(1.55), Inches(4.45), Inches(4.8))
    panel.fill.solid()
    panel.fill.fore_color.rgb = INK
    panel.line.color.rgb = PANEL_BORDER
    frame = panel.text_frame
    frame.clear()
    frame.margin_left = Inches(0.25)
    frame.margin_right = Inches(0.2)
    frame.margin_top = Inches(0.25)
    paragraph = frame.paragraphs[0]
    paragraph.text = code
    paragraph.font.name = "Cascadia Mono"
    paragraph.font.size = Pt(14)
    paragraph.font.color.rgb = RGBColor(220, 238, 241)


def add_visual(slide, visual):
    panel = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.55), Inches(1.5), Inches(4.1), Inches(4.95))
    panel.fill.solid()
    panel.fill.fore_color.rgb = PANEL
    panel.line.color.rgb = PANEL_BORDER
    labels = {
        "spark": ("EXPORT → SPARK", RED),
        "cost": ("MOVE + INFER + MERGE", AMBER),
        "journey": ("BUILD → PROVE → PROMOTE", BLUE),
        "proof": ("DRIFT SURVIVES", TEAL),
        "review": ("PROFILE → APPROVE", AMBER),
        "dashboard": ("OPERATIONS VIEW", TEAL),
        "decision": ("3 DECISIONS", BLUE),
        "adopt": ("SHADOW → BENCHMARK", BLUE),
    }
    word, color = labels.get(visual, ("EVENTHOUSE", BLUE))
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.15), Inches(3.1), Inches(2.9), Inches(1.15))
    badge.fill.solid()
    badge.fill.fore_color.rgb = color
    badge.line.fill.background()
    frame = badge.text_frame
    frame.clear()
    paragraph = frame.paragraphs[0]
    paragraph.text = word
    paragraph.alignment = PP_ALIGN.CENTER
    paragraph.font.name = "Aptos Display"
    paragraph.font.size = Pt(20)
    paragraph.font.bold = True
    paragraph.font.color.rgb = WHITE


def add_architecture(slide):
    slide.shapes.add_picture(str(ARCHITECTURE_IMAGE), Inches(8.15), Inches(1.45), width=Inches(4.65), height=Inches(3.95))
    add_textbox(slide, 8.25, 5.65, 4.35, 0.55, "No routine telemetry export", 17, TEAL, True)


def build_architecture_image():
    ARCHITECTURE_IMAGE.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1600, 900), "#0e161d")
    draw = ImageDraw.Draw(image)
    font = load_font(31)
    small = load_font(24)
    boxes = [
        ((70, 350, 300, 500), "Event Hub", "#0078d4"),
        ((370, 350, 640, 500), "RawTelemetry", "#182530"),
        ((720, 100, 1050, 250), "Typed policies", "#008577"),
        ((720, 375, 1050, 525), "Zone policy", "#008577"),
        ((720, 650, 1050, 800), "Drift policy", "#e67e22"),
        ((1130, 100, 1510, 250), "Typed tables", "#0078d4"),
        ((1130, 375, 1510, 525), "Child rows", "#0078d4"),
        ((1130, 650, 1510, 800), "Drift observations", "#e67e22"),
    ]
    for (left, top, right, bottom), label, color in boxes:
        draw.rounded_rectangle((left, top, right, bottom), radius=12, fill=color)
        text_box = draw.textbbox((0, 0), label, font=font)
        draw.text(((left + right - text_box[2]) / 2, (top + bottom - text_box[3]) / 2), label, font=font, fill="white")
    arrows = [((300, 425), (370, 425)), ((640, 425), (720, 175)), ((640, 425), (720, 450)), ((640, 425), (720, 725)), ((1050, 175), (1130, 175)), ((1050, 450), (1130, 450)), ((1050, 725), (1130, 725))]
    for start, end in arrows:
        draw.line((start, end), fill="#9bb0b8", width=6)
        draw.polygon([(end[0], end[1]), (end[0] - 18, end[1] - 10), (end[0] - 18, end[1] + 10)], fill="#9bb0b8")
    draw.text((70, 65), "Eventhouse-native schema drift", font=font, fill="#ebf2f4")
    draw.text((70, 115), "Fixed target schemas • residual JSON • reviewed promotion", font=small, fill="#aabeC6")
    image.save(ARCHITECTURE_IMAGE)


def build_presentation(output: Path = OUTPUT):
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)
    for number, content in enumerate(SLIDES, 1):
        title = content["title"]
        bullets = content["bullets"]
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        background = slide.background.fill
        background.solid()
        background.fore_color.rgb = BACKGROUND
        if number == 1:
            stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.22), presentation.slide_height)
            stripe.fill.solid()
            stripe.fill.fore_color.rgb = BLUE
            stripe.line.fill.background()
            add_textbox(slide, 0.9, 1.5, 11.5, 1.3, title, 38, TEXT, True)
            add_textbox(slide, 0.95, 3.15, 10.8, 1.3, "\n".join(bullets), 21, MUTED)
            add_textbox(slide, 0.95, 6.45, 5.0, 0.4, "PUBLIC REFERENCE IMPLEMENTATION", 11, BLUE, True)
        else:
            add_header(slide, title, number)
            add_bullets(slide, bullets)
            if "code" in content:
                add_code(slide, content["code"])
            elif content.get("visual") == "architecture":
                add_architecture(slide)
            else:
                add_visual(slide, content.get("visual"))
    output.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the customer demo presentation.")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    arguments = parser.parse_args()
    build_architecture_image()
    build_presentation(arguments.output)
    print(f"wrote {arguments.output}")
    print(f"wrote {ARCHITECTURE_IMAGE.relative_to(ROOT)}")
