"""Export contract tables (engine/contract.py format) to CSV, JSON and one Excel workbook."""
from __future__ import annotations

import io
import json
import re

import pandas as pd


def table_to_dataframe(table: dict) -> pd.DataFrame:
    return pd.DataFrame(table["rows"], columns=table["columns"])


def table_to_csv_bytes(table: dict) -> bytes:
    return table_to_dataframe(table).to_csv(index=False).encode("utf-8-sig")  # utf-8-sig: Excel-friendly


def table_to_json_bytes(table: dict) -> bytes:
    return json.dumps(table, ensure_ascii=False, indent=2).encode("utf-8")


def _sheet_name(name: str, used: set[str]) -> str:
    base = re.sub(r"[\[\]:*?/\\]", "_", name)[:31] or "table"
    candidate, n = base, 2
    while candidate.lower() in used:  # Excel sheet names: unique, max 31 chars
        suffix = f"_{n}"
        candidate = base[: 31 - len(suffix)] + suffix
        n += 1
    used.add(candidate.lower())
    return candidate


def tables_to_xlsx_bytes(tables: list[dict]) -> bytes:
    """One sheet per table. Numeric cells stay numeric; an empty list gives a 'no tables' sheet."""
    buffer = io.BytesIO()
    used: set[str] = set()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        if not tables:
            pd.DataFrame({"info": ["no tables"]}).to_excel(writer, sheet_name="no_tables", index=False)
        for table in tables:
            name = _sheet_name(table.get("table_id", "table"), used)
            table_to_dataframe(table).to_excel(writer, sheet_name=name, index=False)
    return buffer.getvalue()
