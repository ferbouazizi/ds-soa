"""Bounding-box inspector (Streamlit).

    streamlit run inspector/app.py

Left: the rendered PDF page with Docling's layout boxes (numbered in reading order).
Right: the tables of that page with their checksum verdict, and CSV / Excel / JSON downloads.

Two ways to load a document:
  * pick one already converted by `python -m engine.convert` (folder `output/`, or DOCLING_OUTPUT_DIR);
  * upload a PDF: it is converted on the spot (needs Docling installed).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from engine.boxes import boxes_for_page, label_counts, load_boxes  # noqa: E402
from engine.export import (  # noqa: E402
    table_to_csv_bytes, table_to_json_bytes, tables_to_xlsx_bytes,
)
from harness.checks import validate_table  # noqa: E402
from harness.models import TableResult  # noqa: E402
from inspector.overlay import color_for, draw_boxes, render_page  # noqa: E402

SCALE = 1.5

st.set_page_config(page_title="Docling inspector", layout="wide")
st.title("Docling bounding-box inspector")

root = Path(st.sidebar.text_input("Output folder", os.getenv("DOCLING_OUTPUT_DIR", "output")))
upload = st.sidebar.file_uploader("...or upload a PDF to convert", type=["pdf"])

if upload is not None:
    try:
        from engine.convert import SUPPORTED_SUFFIXES  # noqa: F401
        from api.convert import convert_file

        work = Path(tempfile.mkdtemp(prefix="inspector_"))
        pdf_file = work / upload.name
        pdf_file.write_bytes(upload.getbuffer())
        with st.spinner("Docling is converting (first run downloads the models)..."):
            summary = convert_file(pdf_file, root)
        st.sidebar.success(f"{summary['status']}: {summary['n_tables']} table(s)")
    except Exception as exc:  # noqa: BLE001
        st.sidebar.error(f"Conversion failed: {exc}")

docs = sorted(p.parent.name for p in root.glob("*/summary.json")) if root.exists() else []
if not docs:
    st.info(f"No converted document in `{root}`. Run `python -m engine.convert samples --out output` "
            "or upload a PDF.")
    st.stop()

doc_id = st.sidebar.selectbox("Document", docs)
folder = root / doc_id
summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
docling_json = folder / f"{doc_id}.docling.json"
source = Path(summary.get("source", ""))

st.sidebar.write(f"Status: **{summary.get('status')}**, tables: **{summary.get('n_tables')}**")
if not docling_json.exists():
    st.warning("This document has no .docling.json (conversion failed or demo data): no boxes to show.")
    st.stop()
if not source.exists() or source.suffix.lower() != ".pdf":
    st.warning(f"Source PDF not found at `{source}`: boxes can only be drawn on a PDF.")
    st.stop()

boxes = load_boxes(docling_json)
pages = sorted({b.page for b in boxes})
if not pages:
    st.warning("Docling found no layout items in this document.")
    st.stop()

page = st.sidebar.selectbox("Page", pages)
counts = label_counts(boxes_for_page(boxes, page))
labels = set(st.sidebar.multiselect("Layout labels shown", list(counts), default=list(counts)))
show_order = st.sidebar.checkbox("Number boxes in reading order", True)

left, right = st.columns([3, 2])
with left:
    page_boxes = boxes_for_page(boxes, page, labels)
    image = draw_boxes(render_page(source, page, SCALE), page_boxes, SCALE, show_order)
    st.image(image, caption=f"{doc_id} - page {page}: {len(page_boxes)} boxes", use_container_width=True)
    st.markdown(" ".join(f"<span style='color:{color_for(k)}'>■ {k} ({v})</span>" for k, v in counts.items()),
                unsafe_allow_html=True)
    with st.expander("Reading order (text of each box)"):
        for b in page_boxes:
            st.text(f"{b.order + 1:>3}  {b.label:<15} {b.text[:90]}")

tables = []
for path in sorted((folder / "tables").glob("*.json")):
    tables.append(json.loads(path.read_text(encoding="utf-8")))

with right:
    st.subheader("Tables")
    if tables:
        st.download_button("All tables (Excel)", tables_to_xlsx_bytes(tables),
                           f"{doc_id}_tables.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    for table in [t for t in tables if t["page"] == page] or []:
        report = validate_table(TableResult.model_validate(table))
        st.markdown(f"**{table['table_id']}**: " + ("✅ PASS" if report.passed else "❌ FLAGGED"))
        for failure in report.failures:
            st.caption(f"{failure.code.value}: {failure.message}")
        st.dataframe(pd.DataFrame(table["rows"], columns=table["columns"]), use_container_width=True)
        c1, c2 = st.columns(2)
        c1.download_button("CSV", table_to_csv_bytes(table), f"{table['table_id']}.csv", "text/csv",
                           key=f"csv_{table['table_id']}")
        c2.download_button("JSON", table_to_json_bytes(table), f"{table['table_id']}.json",
                           "application/json", key=f"json_{table['table_id']}")
    if not any(t["page"] == page for t in tables):
        st.caption("No table on this page.")
