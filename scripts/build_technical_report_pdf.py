#!/usr/bin/env python3
"""Build the review PDF for the GuardianSim Track 3 technical report."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

AMD_RED = colors.HexColor("#ED1C24")
INK = colors.HexColor("#161616")
MUTED = colors.HexColor("#626262")
LIGHT = colors.HexColor("#F4F4F4")
GREEN = colors.HexColor("#2E7D32")
ORANGE = colors.HexColor("#EF6C00")


def ascii_text(value: str) -> str:
    """Normalize punctuation that is unreliable in base PDF fonts."""

    replacements = {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2192": "->",
        "\u00b0": " degrees",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    return value


def inline_markup(value: str) -> str:
    value = ascii_text(value.strip())
    value = re.sub(r"<(https?://[^>]+)>", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", value)
    escaped = html.escape(value)
    escaped = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    return escaped


def architecture_drawing(width: float) -> Drawing:
    height = 45 * mm
    drawing = Drawing(width, height)
    box_width = 37 * mm
    box_height = 14 * mm
    gap = (width - 4 * box_width) / 3
    y_top = 29 * mm
    labels = [
        ("Nominal action", ORANGE),
        ("Counterfactuals", AMD_RED),
        ("Radeon rollouts", AMD_RED),
        ("Safety certificate", GREEN),
    ]
    x_positions = []
    for index, (label, color) in enumerate(labels):
        x = index * (box_width + gap)
        x_positions.append(x)
        drawing.add(Rect(x, y_top, box_width, box_height, 3 * mm, 3 * mm,
                         fillColor=colors.white, strokeColor=color,
                         strokeWidth=1.5))
        drawing.add(String(x + box_width / 2, y_top + 8.2 * mm, label,
                           textAnchor="middle", fontName="Helvetica-Bold",
                           fontSize=8, fillColor=INK))
        if index < len(labels) - 1:
            x1 = x + box_width
            x2 = x + box_width + gap
            drawing.add(Line(x1, y_top + box_height / 2, x2,
                             y_top + box_height / 2,
                             strokeColor=MUTED, strokeWidth=1.2))
            drawing.add(Line(x2 - 2 * mm, y_top + box_height / 2 + 1.5 * mm,
                             x2, y_top + box_height / 2,
                             strokeColor=MUTED, strokeWidth=1.2))
            drawing.add(Line(x2 - 2 * mm, y_top + box_height / 2 - 1.5 * mm,
                             x2, y_top + box_height / 2,
                             strokeColor=MUTED, strokeWidth=1.2))
    lower_y = 1 * mm
    lower = [
        (x_positions[1], "Same snapshot"),
        (x_positions[2], "Physical metrics"),
        (x_positions[3], "Execute or safe-stop"),
    ]
    for x, label in lower:
        drawing.add(Rect(x, lower_y, box_width, 11 * mm, 2 * mm, 2 * mm,
                         fillColor=LIGHT, strokeColor=colors.HexColor("#B0B0B0")))
        drawing.add(String(x + box_width / 2, lower_y + 6.3 * mm, label,
                           textAnchor="middle", fontName="Helvetica",
                           fontSize=7.5, fillColor=INK))
    drawing.add(Line(x_positions[1] + box_width / 2, y_top,
                     x_positions[1] + box_width / 2, lower_y + 11 * mm,
                     strokeColor=MUTED))
    drawing.add(Line(x_positions[2] + box_width / 2, y_top,
                     x_positions[2] + box_width / 2, lower_y + 11 * mm,
                     strokeColor=MUTED))
    drawing.add(Line(x_positions[3] + box_width / 2, y_top,
                     x_positions[3] + box_width / 2, lower_y + 11 * mm,
                     strokeColor=MUTED))
    return drawing


class DraftBanner(Flowable):
    def __init__(self, width: float):
        super().__init__()
        self.width = width
        self.height = 11 * mm

    def draw(self) -> None:
        self.canv.setFillColor(colors.HexColor("#FFF3E0"))
        self.canv.roundRect(0, 0, self.width, self.height, 2 * mm, fill=1,
                            stroke=0)
        self.canv.setFillColor(ORANGE)
        self.canv.setFont("Helvetica-Bold", 9)
        self.canv.drawCentredString(
            self.width / 2,
            3.7 * mm,
            "REVIEW DRAFT - team attribution and Luma rules sign-off pending",
        )


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=8 * mm,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=MUTED,
            spaceAfter=3 * mm,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=INK,
            spaceBefore=7 * mm,
            spaceAfter=3 * mm,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=AMD_RED,
            spaceBefore=5 * mm,
            spaceAfter=2 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.3,
            leading=13.2,
            textColor=INK,
            spaceAfter=2.2 * mm,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.1,
            leading=12.5,
            leftIndent=7 * mm,
            firstLineIndent=0,
            bulletIndent=2 * mm,
            textColor=INK,
            spaceAfter=1.2 * mm,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=9.3,
            leading=13.2,
            leftIndent=7 * mm,
            rightIndent=7 * mm,
            borderColor=AMD_RED,
            borderWidth=1.5,
            borderPadding=(2 * mm, 3 * mm, 2 * mm, 4 * mm),
            backColor=LIGHT,
            textColor=INK,
            spaceAfter=3 * mm,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.3,
            leading=9.5,
            leftIndent=4 * mm,
            rightIndent=4 * mm,
            backColor=LIGHT,
            borderPadding=3 * mm,
            spaceAfter=3 * mm,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=MUTED,
        ),
    }


def parse_table(lines: list[str], style_map: dict[str, ParagraphStyle]) -> Table:
    rows: list[list[Paragraph]] = []
    for index, line in enumerate(lines):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if index == 1 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if index == 0:
            cell_style = ParagraphStyle(
                "TableHeader",
                parent=style_map["small"],
                textColor=colors.white,
                fontName="Helvetica-Bold",
            )
        else:
            cell_style = style_map["small"]
        cells = [
            "Pending owner verification"
            if "FULL NAME" in cell
            else "To be completed before final export"
            if "System design, implementation" in cell
            else cell
            for cell in cells
        ]
        rows.append([
            Paragraph(inline_markup(cell), cell_style)
            for cell in cells
        ])
    column_count = len(rows[0])
    usable = 170 * mm
    if column_count == 4:
        widths = [58 * mm, 35 * mm, 35 * mm, 42 * mm]
    elif column_count == 2:
        widths = [45 * mm, 125 * mm]
    else:
        widths = [usable / column_count] * column_count
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C8C8C8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.2 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.2 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 1.8 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8 * mm),
    ]))
    return table


def bullet_row(
    marker: str,
    text: str,
    style_map: dict[str, ParagraphStyle],
) -> Table:
    marker_style = ParagraphStyle(
        "BulletMarker",
        parent=style_map["bullet"],
        leftIndent=0,
        rightIndent=0,
        alignment=TA_CENTER,
    )
    text_style = ParagraphStyle(
        "BulletBody",
        parent=style_map["bullet"],
        leftIndent=0,
        rightIndent=0,
        firstLineIndent=0,
    )
    table = Table(
        [[
            Paragraph(html.escape(marker), marker_style),
            Paragraph(inline_markup(text), text_style),
        ]],
        colWidths=[7 * mm, 163 * mm],
        hAlign="LEFT",
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def markdown_story(source: Path) -> list[Flowable]:
    style_map = styles()
    lines = source.read_text(encoding="utf-8").splitlines()
    story: list[Flowable] = []

    title = ascii_text(lines[0].removeprefix("# ").strip())
    story.extend([
        Spacer(1, 18 * mm),
        Paragraph("GUARDIANSIM", ParagraphStyle(
            "Kicker", parent=style_map["subtitle"], textColor=AMD_RED,
            fontName="Helvetica-Bold", fontSize=10, leading=12,
        )),
        Paragraph(html.escape(title), style_map["title"]),
        Paragraph(
            "Track 3 - Physical AI Challenge<br/>"
            "AMD Radeon Cloud / ROCm / Genesis simulation",
            style_map["subtitle"],
        ),
        Spacer(1, 12 * mm),
        DraftBanner(170 * mm),
        Spacer(1, 13 * mm),
        Paragraph(
            "<b>Project repository</b><br/>"
            "github.com/nvm-star-max/GuardianSim",
            style_map["body"],
        ),
        Paragraph(
            "<b>Team attribution</b><br/>"
            "Pending owner verification before final export",
            style_map["body"],
        ),
        Spacer(1, 30 * mm),
        Paragraph(
            "Counterfactual safety certification for robot manipulation on "
            "AMD Radeon GPUs",
            ParagraphStyle(
                "CoverStatement", parent=style_map["body"], fontSize=14,
                leading=19, textColor=INK,
            ),
        ),
        PageBreak(),
    ])

    index = 1
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            text = " ".join(part.strip() for part in paragraph_lines)
            story.append(Paragraph(inline_markup(text), style_map["body"]))
            paragraph_lines.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if (
            stripped.startswith("**Track:**")
            or stripped.startswith("**Project repository:**")
            or stripped.startswith("**Team:**")
            or stripped.startswith("**Members:**")
        ):
            index += 1
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            language = stripped.removeprefix("```").strip()
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if language == "mermaid":
                story.append(architecture_drawing(170 * mm))
            else:
                story.append(Paragraph(
                    html.escape(ascii_text("\n".join(code_lines))).replace("\n", "<br/>"),
                    style_map["code"],
                ))
            index += 1
            continue
        if stripped.startswith("|") and index + 1 < len(lines):
            flush_paragraph()
            table_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            story.extend([parse_table(table_lines, style_map), Spacer(1, 3 * mm)])
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[3:]), style_map["h1"]))
            index += 1
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[4:]), style_map["h2"]))
            index += 1
            continue
        if stripped.startswith("> "):
            flush_paragraph()
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip().removeprefix(">").strip())
                index += 1
            quote = " ".join(quote_lines)
            if quote.startswith("**Submission blocker:**"):
                quote = (
                    "Submission blocker: verified team names and contributions "
                    "must be added before final export."
                )
            story.append(Paragraph(inline_markup(quote), style_map["quote"]))
            continue
        if re.match(r"^\d+\.\s+", stripped) or stripped.startswith("- "):
            flush_paragraph()
            match = re.match(r"^(\d+\.|-)\s+(.+)", stripped)
            assert match is not None
            marker, bullet_text = match.groups()
            index += 1
            continuation: list[str] = []
            while (
                index < len(lines)
                and lines[index].strip()
                and lines[index][0].isspace()
            ):
                continuation.append(lines[index].strip())
                index += 1
            if continuation:
                bullet_text = " ".join([bullet_text, *continuation])
            story.append(bullet_row(marker, bullet_text, style_map))
            continue
        paragraph_lines.append(stripped)
        index += 1

    flush_paragraph()
    return story


def page_header_footer(canvas, document) -> None:  # noqa: ANN001
    canvas.saveState()
    if document.page == 1:
        canvas.restoreState()
        return
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#D8D8D8"))
    canvas.setLineWidth(0.4)
    canvas.line(20 * mm, height - 14 * mm, width - 20 * mm, height - 14 * mm)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(AMD_RED)
    canvas.drawString(20 * mm, height - 10.5 * mm, "GUARDIANSIM")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(width - 20 * mm, height - 10.5 * mm,
                           "Track 3 Technical Report - Review Draft")
    canvas.line(20 * mm, 14 * mm, width - 20 * mm, 14 * mm)
    canvas.drawString(20 * mm, 9.5 * mm,
                      "Genesis simulation on AMD Radeon Cloud")
    canvas.drawRightString(width - 20 * mm, 9.5 * mm,
                           f"Page {document.page}")
    canvas.restoreState()


def build(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    document = BaseDocTemplate(
        str(destination),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=19 * mm,
        title="GuardianSim Track 3 Technical Report",
        author="GuardianSim team",
        subject="AMD Radeon Hackathon 2026 Track 3 submission review draft",
    )
    frame = Frame(
        document.leftMargin,
        document.bottomMargin,
        document.width,
        document.height,
        id="content",
    )
    document.addPageTemplates([
        PageTemplate(id="report", frames=[frame], onPage=page_header_footer)
    ])
    document.build(markdown_story(source))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("docs/submission/TECHNICAL_REPORT.md"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/pdf/GuardianSim-Technical-Report-DRAFT.pdf"),
    )
    args = parser.parse_args()
    build(args.source, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
