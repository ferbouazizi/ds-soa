# Inspector

`streamlit run inspector/app.py` (or `run_inspector.bat`). Reads `output/<doc_id>/<doc_id>.docling.json`
and the source PDF named in `summary.json`.

* left: rendered page with layout boxes coloured by label and numbered in reading order;
* right: tables of the page, checksum verdict, CSV / JSON per table and one Excel workbook per document.

Logic lives in `engine/boxes.py` (boxes, reading order) and `inspector/overlay.py` (drawing); both are tested
without Docling. Limit: only PDFs can be drawn; DOCX/images have no page geometry in the same form.
