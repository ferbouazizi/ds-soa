"""Generate the 4 sample PDFs for the whole team (run once; they are already in samples/).

    python make_samples.py

Creates in samples/:
  sample_simple_table.pdf            one clean table, totals are CORRECT
  sample_two_column_table.pdf        two-column article layout + one table (totals correct)
  sample_wrong_total.pdf             one table whose Total row is deliberately WRONG
                                     (the harness must flag it: 1300 instead of 1250)
  sample_wrong_total_long_title.pdf  same table as above but with a long title.
                                     Observed on one Windows machine with Docling 2.151.1:
                                     Docling found 0 tables in this file (normal, OCR,
                                     accurate and OCR+accurate modes) while the file with
                                     the short title gave 1 table. The cause is not
                                     established. Kept as a real failure case: the harness
                                     must treat "0 tables found" as a failure.

Close these PDFs in any viewer before re-running this script (Windows locks open files).
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle,
                                FrameBreak)

OUT = Path("samples")
styles = getSampleStyleSheet()

HEADER = ["Item", "Q1", "Q2", "Q3", "Total"]


def sales_rows(wrong_total=False):
    rows = [
        ["Laptops", 120, 135, 150],
        ["Phones", 200, 180, 220],
        ["Tablets", 80, 95, 70],
    ]
    body = [r + [sum(r[1:])] for r in rows]
    totals = ["Total"] + [sum(r[i] for r in body) for i in range(1, 5)]
    if wrong_total:
        totals[4] += 50  # deliberate error for testing the harness
    return [HEADER] + body + [totals]


def make_table(data):
    t = Table(data, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]))
    return t


def simple(path, wrong_total=False, title="Annual Sales Report"):
    from reportlab.platypus import SimpleDocTemplate
    doc = SimpleDocTemplate(str(path), pagesize=A4)
    story = [
        Paragraph(title, styles["Title"]),
        Paragraph("Units sold per quarter, by product line.", styles["Normal"]),
        Spacer(1, 16),
        make_table(sales_rows(wrong_total)),
        Spacer(1, 16),
        Paragraph("Source: internal sales database.", styles["Italic"]),
    ]
    doc.build(story)


LOREM = (
    "Document intelligence converts unstructured files into structured data. "
    "Layout analysis detects titles, paragraphs and tables, and recovers the "
    "reading order so that text from two columns is not mixed together. "
) * 6


def two_column(path):
    doc = BaseDocTemplate(str(path), pagesize=A4)
    w, h = A4
    m = 40
    gap = 20
    colw = (w - 2 * m - gap) / 2
    top = h - 120
    left = Frame(m, 60, colw, top - 60, id="left")
    right = Frame(m + colw + gap, 60, colw, top - 60, id="right")
    head = Frame(m, top, w - 2 * m, 100, id="head")
    doc.addPageTemplates([PageTemplate(id="two", frames=[head, left, right])])
    story = [
        Paragraph("Quarterly Technology Review", styles["Title"]),
        FrameBreak(),
        Paragraph("1. Background", styles["Heading2"]),
        Paragraph(LOREM, styles["Normal"]),
        Spacer(1, 8),
        make_table(sales_rows()),
        Spacer(1, 8),
        Paragraph("2. Discussion", styles["Heading2"]),
        Paragraph(LOREM, styles["Normal"]),
    ]
    doc.build(story)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    simple(OUT / "sample_simple_table.pdf")
    two_column(OUT / "sample_two_column_table.pdf")
    simple(OUT / "sample_wrong_total.pdf", wrong_total=True)
    simple(OUT / "sample_wrong_total_long_title.pdf", wrong_total=True,
           title="Annual Sales Report (contains an error)")
    for p in sorted(OUT.glob("*.pdf")):
        print("created", p)
