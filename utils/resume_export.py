from io import BytesIO
from xml.sax.saxutils import escape
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


NAVY = "17365D"
BLUE = "2F5597"
GRAY = "555555"


def _safe(value, limit=500):
    return str(value or "").strip()[:limit]


def _pdf_text(value):
    """Use Helvetica for Latin runs so CID-font letter spacing stays natural."""
    escaped = escape(_safe(value, 2000))
    return re.sub(
        r"([\x20-\x7E]+)",
        lambda match: f'<font name="Helvetica">{match.group(1)}</font>',
        escaped,
    )


def _set_run_font(run, size=9.5, bold=False, color="111111", language="zh"):
    latin_font = "Arial"
    east_asia_font = "Microsoft YaHei" if language == "zh" else "Arial"
    run.font.name = east_asia_font
    fonts = run._element.get_or_add_rPr().rFonts
    fonts.set(qn("w:eastAsia"), east_asia_font)
    fonts.set(qn("w:ascii"), latin_font)
    fonts.set(qn("w:hAnsi"), latin_font)
    run.font.size = Pt(size)
    run.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def _add_bottom_border(paragraph):
    ppr = paragraph._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), BLUE)
    pbdr.append(bottom)
    ppr.append(pbdr)


def _resume_density(resume):
    text = " ".join([
        _safe(resume.get("summary"), 2000),
        *[
            _safe(value, 1000)
            for section in resume.get("sections", [])
            for entry in section.get("entries", [])
            for value in [entry.get("heading"), entry.get("date"), *entry.get("bullets", [])]
        ],
    ])
    bullets = sum(
        len(entry.get("bullets", []))
        for section in resume.get("sections", [])
        for entry in section.get("entries", [])
    )
    return len(text) + bullets * 75


def build_docx_bytes(resume: dict, language="zh", one_page=False) -> bytes:
    """Build an ATS-friendly A4 DOCX from validated resume content."""
    doc = Document()
    section = doc.sections[0]
    compact = bool(one_page)
    if language == "en":
        section.page_width = Inches(8.5)
        section.page_height = Inches(11)
        margin = 0.38 if compact else 0.48
        section.top_margin = Inches(margin)
        section.bottom_margin = Inches(margin)
        section.left_margin = Inches(0.62)
        section.right_margin = Inches(0.62)
    else:
        section.page_width = Cm(21)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(0.7 if compact else 1.1)
        section.bottom_margin = Cm(0.7 if compact else 1.0)
        section.left_margin = Cm(1.15 if compact else 1.45)
        section.right_margin = Cm(1.15 if compact else 1.45)

    normal = doc.styles["Normal"]
    base_font = "Arial" if language == "en" else "Microsoft YaHei"
    normal.font.name = base_font
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), base_font)
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
    normal.font.size = Pt(8.3 if compact else 9.0 if language == "en" else 9.5)
    normal.paragraph_format.space_after = Pt(0.5 if compact else 0.8 if language == "en" else 1.5)
    normal.paragraph_format.line_spacing = 1.0 if compact or language == "en" else 1.08

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER if language == "en" else WD_ALIGN_PARAGRAPH.LEFT
    title.paragraph_format.space_after = Pt(0 if language == "en" else 1)
    _set_run_font(title.add_run(_safe(resume.get("name"), 80)), 20 if compact else 22 if language == "en" else 20, True, NAVY, language)

    contact = doc.add_paragraph()
    contact.alignment = WD_ALIGN_PARAGRAPH.CENTER if language == "en" else WD_ALIGN_PARAGRAPH.LEFT
    contact.paragraph_format.space_after = Pt(0 if language == "en" else 1)
    _set_run_font(contact.add_run(_safe(resume.get("contact"))), 8.5 if language == "en" else 9.2, False, GRAY, language)

    target = doc.add_paragraph()
    target.alignment = WD_ALIGN_PARAGRAPH.CENTER if language == "en" else WD_ALIGN_PARAGRAPH.LEFT
    target.paragraph_format.space_after = Pt(4 if language == "en" else 4)
    target_label = "Target Role" if language == "en" else "求职方向"
    target_text = _safe(resume.get('target_role'), 120).upper() if language == "en" else _safe(resume.get('target_role'), 120)
    _set_run_font(target.add_run(f"{target_label}: {target_text}"), 8.7 if language == "en" else 9.7, True, BLUE, language)

    summary = _safe(resume.get("summary"), 1000)
    if summary:
        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(2 if language == "en" else 3)
        heading.paragraph_format.space_after = Pt(1 if language == "en" else 2)
        _set_run_font(heading.add_run("Professional Summary" if language == "en" else "个人概述"), 11.5, True, NAVY, language)
        _add_bottom_border(heading)
        body = doc.add_paragraph()
        body.paragraph_format.space_after = Pt(1 if language == "en" else 2)
        body.paragraph_format.line_spacing = 1.0 if language == "en" else 1.08
        _set_run_font(body.add_run(summary), 8.3 if compact else 8.9 if language == "en" else 9.5, language=language)

    for section_data in resume.get("sections", []):
        section_title = _safe(section_data.get("title"), 80)
        if not section_title:
            continue
        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(3 if language == "en" else 4)
        heading.paragraph_format.space_after = Pt(1 if language == "en" else 2)
        heading.paragraph_format.keep_with_next = True
        display_title = section_title.upper() if language == "en" else section_title
        _set_run_font(heading.add_run(display_title), 10.0 if compact else 10.2 if language == "en" else 11.5, True, NAVY, language)
        _add_bottom_border(heading)
        for entry in section_data.get("entries", []):
            row = doc.add_table(rows=1, cols=2)
            row.autofit = False
            row.columns[0].width = Inches(5.8) if language == "en" else Cm(14.4)
            row.columns[1].width = Inches(1.4) if language == "en" else Cm(3.4)
            row.cell(0, 0).width = Inches(5.8) if language == "en" else Cm(14.4)
            row.cell(0, 1).width = Inches(1.4) if language == "en" else Cm(3.4)
            left = row.cell(0, 0).paragraphs[0]
            left.paragraph_format.space_after = Pt(0)
            _set_run_font(left.add_run(_safe(entry.get("heading"), 250)), 8.6 if compact else 9.1 if language == "en" else 9.7, True, language=language)
            right = row.cell(0, 1).paragraphs[0]
            right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            right.paragraph_format.space_after = Pt(0)
            _set_run_font(right.add_run(_safe(entry.get("date"), 80)), 8.0 if compact else 8.5 if language == "en" else 9.0, False, GRAY, language)
            for bullet in entry.get("bullets", []):
                text = _safe(bullet, 600)
                if not text:
                    continue
                paragraph = doc.add_paragraph(style="List Bullet")
                paragraph.paragraph_format.left_indent = Cm(0.48)
                paragraph.paragraph_format.first_line_indent = Cm(-0.28)
                paragraph.paragraph_format.space_after = Pt(0 if compact or language == "en" else 1)
                paragraph.paragraph_format.line_spacing = 1.0 if compact or language == "en" else 1.06
                _set_run_font(paragraph.add_run(text), 8.2 if compact else 8.8 if language == "en" else 9.2, language=language)

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def build_pdf_bytes(resume: dict, language="zh", one_page=False) -> bytes:
    """Build a searchable Chinese A4 PDF with CJK/Latin font fallback."""
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    compact = bool(one_page)
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=LETTER if language == "en" else A4,
        leftMargin=(15.5 if language == "en" else 11.5 if compact else 14.5) * mm,
        rightMargin=(15.5 if language == "en" else 11.5 if compact else 14.5) * mm,
        topMargin=(9.5 if compact else 11) * mm,
        bottomMargin=(9.5 if compact else 11) * mm,
        title=_safe(resume.get("name"), 80) + " 定制简历",
    )
    base = ParagraphStyle(
        "ResumeBody", fontName="Helvetica" if language == "en" else "STSong-Light",
        fontSize=8.2 if compact else 8.9 if language == "en" else 9.2,
        leading=9.6 if compact else 10.8 if language == "en" else 12.2,
        textColor=colors.HexColor("#172033"), alignment=TA_LEFT,
        wordWrap="CJK", spaceAfter=0.7 if language == "en" else 1.5,
    )
    title_style = ParagraphStyle(
        "ResumeTitle", parent=base, fontSize=22 if language == "en" else 20, leading=24,
        textColor=colors.HexColor("#17365D"), spaceAfter=1, alignment=TA_CENTER if language == "en" else TA_LEFT,
    )
    contact_style = ParagraphStyle(
        "ResumeContact", parent=base, fontSize=8.3 if language == "en" else 9, leading=10,
        textColor=colors.HexColor("#555555"), spaceAfter=1, alignment=TA_CENTER if language == "en" else TA_LEFT,
    )
    target_style = ParagraphStyle(
        "ResumeTarget", parent=base, fontSize=8.5 if language == "en" else 9.5, leading=10.5,
        textColor=colors.HexColor("#2F5597"), spaceAfter=4, alignment=TA_CENTER if language == "en" else TA_LEFT,
    )
    section_style = ParagraphStyle(
        "ResumeSection", parent=base, fontSize=10 if compact else 10.2 if language == "en" else 11.5, leading=12,
        textColor=colors.HexColor("#17365D"), spaceBefore=3 if compact or language == "en" else 5, spaceAfter=1.5 if compact or language == "en" else 3,
        borderWidth=0, borderPadding=0,
    )
    role_style = ParagraphStyle(
        "ResumeRole", parent=base, fontSize=8.4 if compact else 9 if language == "en" else 9.6,
        leading=10 if compact or language == "en" else 12, textColor=colors.HexColor("#111111"), spaceBefore=0, spaceAfter=0,
    )
    bullet_style = ParagraphStyle(
        "ResumeBullet", parent=base, leftIndent=9, firstLineIndent=-7,
        fontSize=8.1 if compact else 8.7 if language == "en" else 9.1,
        leading=9.5 if compact else 10.5 if language == "en" else 12, spaceAfter=0.5 if compact or language == "en" else 1,
    )

    story = [
        Paragraph(_pdf_text(_safe(resume.get("name"), 80)), title_style),
        Paragraph(_pdf_text(_safe(resume.get("contact"))), contact_style),
        Paragraph(_pdf_text(("Target Role: " if language == "en" else "求职方向：") + _safe(resume.get("target_role"), 120)), target_style),
    ]
    summary = _safe(resume.get("summary"), 1000)
    if summary:
        story.append(Paragraph(_pdf_text("PROFESSIONAL SUMMARY" if language == "en" else "个人概述"), section_style))
        if language == "en":
            story.append(HRFlowable(width="100%", thickness=0.7, color=colors.HexColor("#2F5597"), spaceBefore=0, spaceAfter=2))
        story.append(Paragraph(_pdf_text(summary), base))

    for section_data in resume.get("sections", []):
        section_title = _safe(section_data.get("title"), 80)
        if not section_title:
            continue
        story.append(Paragraph(_pdf_text(section_title.upper() if language == "en" else section_title), section_style))
        if language == "en":
            story.append(HRFlowable(width="100%", thickness=0.7, color=colors.HexColor("#2F5597"), spaceBefore=0, spaceAfter=2))
        for entry in section_data.get("entries", []):
            heading = _safe(entry.get("heading"), 250)
            date = _safe(entry.get("date"), 80)
            if language == "en":
                date_style = ParagraphStyle("ResumeDate", parent=role_style, alignment=TA_RIGHT, textColor=colors.HexColor("#555555"))
                role_row = Table(
                    [[Paragraph(f"<b>{_pdf_text(heading)}</b>", role_style), Paragraph(_pdf_text(date), date_style)]],
                    colWidths=[document.width * 0.78, document.width * 0.22],
                )
                role_row.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
                ]))
                block = [role_row]
            else:
                role_line = f"<b>{_pdf_text(heading)}</b>" + (f"　{_pdf_text(date)}" if date else "")
                block = [Paragraph(role_line, role_style)]
            for bullet in entry.get("bullets", []):
                text = _safe(bullet, 600)
                if text:
                    block.append(Paragraph(_pdf_text("- " + text), bullet_style))
            story.append(KeepTogether(block))

    document.build(story)
    return buffer.getvalue()
