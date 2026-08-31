from __future__ import annotations

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

INK = RGBColor(24, 37, 48)
BLUE = RGBColor(0, 120, 212)
TEAL = RGBColor(0, 133, 119)
AMBER = RGBColor(230, 126, 34)
RED = RGBColor(196, 43, 28)
MIST = RGBColor(239, 245, 247)
WHITE = RGBColor(255, 255, 255)

SLIDES = [
    ("Schema drift without bulk export", ["A reusable Microsoft Fabric Eventhouse reference", "Stable typed tables, residual JSON, and reviewed promotion"]),
    ("The customer problem", ["IoT payloads evolve independently of analytics schemas", "Spark schema inference requires bulk reads from Eventhouse", "Concurrent connector reads can consume export capacity", "Drift approval pauses batches and creates operational buffers"]),
    ("Current data path", ["Event Hub to Eventhouse landing table", "Kusto Spark connector invokes the export path", "Spark infers, flattens, compares, and buffers", "Delta targets depend on watermarks and replay orchestration"]),
    ("Stable-schema principle", ["Project known fields explicitly", "Remove known keys from the telemetry bag", "Store the remainder as ResidualTelemetry", "A new key changes data, not the policy output schema"]),
    ("Target architecture", ["One raw table triggers source-specific update policies", "Ordinary typed tables remain available for OneLake mirroring", "A separate policy records unknown fields", "Routine telemetry stays inside Eventhouse"]),
    ("Per-record processing", ["Route by source type", "Cast known values to the target contract", "Preserve unknown values in a dynamic residual", "Record field path, observed type, sample, and event time"]),
    ("Arrays become child rows", ["Variable zone arrays do not become variable columns", "mv-expand emits one row per zone", "Original zone identity is retained", "Empty arrays intentionally emit no child rows"]),
    ("Drift review", ["Aggregate append-only observations by source and path", "Profile type stability, null rate, and cardinality", "Promote only fields with agreed semantics and ownership", "Keep sparse or unstable fields dynamic"]),
    ("Promotion and backfill", ["Add the physical column", "Revise and schema-check the stored function", "Monitor new ingestion", "Replay a bounded raw interval", "Deduplicate appended versions or migrate to a replacement table"]),
    ("OneLake role", ["Mirror ordinary Eventhouse tables for other Fabric engines", "Use mirrored Delta as a transitional Spark quick win", "Validate adaptive batching latency", "Adding columns is supported; renaming and type alteration are constrained"]),
    ("Production gates", ["Peak-load CPU and ingestion latency", "Target completeness and replay", "Malformed and type-conflicted values", "Array amplification", "Duplicate arrival window and materialized-view lookback"]),
    ("Recommended next steps", ["Deploy the demo in a disposable KQL database", "Replace demo contracts with production metadata", "Shadow one source type", "Benchmark at peak concurrency", "Cut over incrementally and retain raw replay coverage"]),
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


def add_textbox(slide, x, y, width, height, text, size=20, color=INK, bold=False):
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
    add_textbox(slide, 0.7, 0.45, 11.8, 0.6, title, 28, INK, True)
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(1.16), Inches(1.15), Inches(0.07))
    accent.fill.solid()
    accent.fill.fore_color.rgb = BLUE
    accent.line.fill.background()
    add_textbox(slide, 12.2, 0.5, 0.5, 0.4, f"{number:02}", 11, BLUE, True)


def add_bullets(slide, bullets):
    shape = slide.shapes.add_textbox(Inches(0.95), Inches(1.55), Inches(7.15), Inches(4.95))
    frame = shape.text_frame
    frame.clear()
    for index, bullet in enumerate(bullets):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = bullet
        paragraph.level = 0
        paragraph.font.name = "Aptos"
        paragraph.font.size = Pt(22)
        paragraph.font.color.rgb = INK
        paragraph.space_after = Pt(18)
        paragraph.text = f"•  {bullet}"


def add_visual(slide, number):
    panel = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.55), Inches(1.5), Inches(4.1), Inches(4.95))
    panel.fill.solid()
    panel.fill.fore_color.rgb = MIST
    panel.line.color.rgb = RGBColor(211, 224, 228)
    labels = {
        2: ("EXPORT", RED), 3: ("FIXED", BLUE), 4: ("NATIVE", TEAL),
        5: ("CAST", BLUE), 6: ("ROWS", TEAL), 7: ("REVIEW", AMBER),
        8: ("PROMOTE", AMBER), 9: ("DELTA", TEAL), 10: ("TEST", RED), 11: ("ADOPT", BLUE),
    }
    word, color = labels.get(number, ("EVENTHOUSE", BLUE))
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


def build_architecture_image():
    ARCHITECTURE_IMAGE.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1600, 900), "#f5f8f9")
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
        draw.line((start, end), fill="#5b6b73", width=6)
        draw.polygon([(end[0], end[1]), (end[0] - 18, end[1] - 10), (end[0] - 18, end[1] + 10)], fill="#5b6b73")
    draw.text((70, 65), "Eventhouse-native schema drift", font=font, fill="#182530")
    draw.text((70, 115), "Fixed target schemas • residual JSON • reviewed promotion", font=small, fill="#52646d")
    image.save(ARCHITECTURE_IMAGE)


def build_presentation():
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)
    for number, (title, bullets) in enumerate(SLIDES, 1):
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        background = slide.background.fill
        background.solid()
        background.fore_color.rgb = WHITE
        if number == 1:
            stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.22), presentation.slide_height)
            stripe.fill.solid()
            stripe.fill.fore_color.rgb = BLUE
            stripe.line.fill.background()
            add_textbox(slide, 0.9, 1.5, 11.5, 1.3, title, 38, INK, True)
            add_textbox(slide, 0.95, 3.15, 10.8, 1.3, "\n".join(bullets), 21, RGBColor(82, 100, 109))
            add_textbox(slide, 0.95, 6.45, 5.0, 0.4, "PUBLIC REFERENCE IMPLEMENTATION", 11, BLUE, True)
        else:
            add_header(slide, title, number)
            add_bullets(slide, bullets)
            add_visual(slide, number)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(OUTPUT)


if __name__ == "__main__":
    build_architecture_image()
    build_presentation()
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    print(f"wrote {ARCHITECTURE_IMAGE.relative_to(ROOT)}")
