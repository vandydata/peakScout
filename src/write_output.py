# ------------------------------------------------------------------------------
#                        __   _____                  __
#      ____  ___  ____ _/ /__/ ___/_________  __  __/ /_
#     / __ \/ _ \/ __ `/ //_/\__ \/ ___/ __ \/ / / / __/
#    / /_/ /  __/ /_/ / ,<  ___/ / /__/ /_/ / /_/ / /_
#   / .___/\___/\__,_/_/|_|/____/\___/\____/\__,_/\__/
#  /_/
#
# Copyrigh 2025 GNU AFFERO GENERAL PUBLIC LICENSE
# Alexander L. Lin, Lana A. Cartailler, Jean-Philippe Cartailler
# https://github.com/vandydata/peakScout
#
# ------------------------------------------------------------------------------

import os
import re
import xlsxwriter
import polars as pl

HEADER_COLORS = {
    "peak":  "#D9D9D9",
    "cre":   "#C4D79B",
    "gene":  "#FCD5B4",
    "ucsc":  "#B8CCE4",
}

ROW_COLORS = {
    "peak":  "#F2F2F2",
    "cre":   "#EBF1DE",
    "gene":  "#FDE9D9",
    "ucsc":  "#DCE6F1",
}

GRID_BORDER_COLOR = "#404040"

def _col_category(col_name: str) -> str:
    if col_name.startswith("cre_"):
        return "cre"
    if re.match(r"^(gene|peak)\d+_", col_name):
        return "gene"
    if col_name == "ucsc_gb_url":
        return "ucsc"
    return "peak"


def write_to_excel(output: pl.DataFrame, output_name: str, out_dir: str) -> None:
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    filepath = os.path.join(out_dir, output_name) + ".xlsx"
    workbook = xlsxwriter.Workbook(filepath)
    worksheet = workbook.add_worksheet("Sheet1")

    columns = output.columns

    categories = [_col_category(col) for col in columns]

    # Build per-column header formats
    header_formats = []
    for cat in categories:
        fmt = workbook.add_format({
            'bg_color': HEADER_COLORS[cat],
            'bold': True,
            'align': 'center',
            'border': 1,
            'border_color': GRID_BORDER_COLOR,
            'rotation': 45,
        })
        header_formats.append(fmt)

    # Build per-column data (row) formats; float columns get 2-decimal display
    is_float_col = [output[col].dtype in (pl.Float32, pl.Float64) for col in columns]

    data_formats = []
    url_formats = []
    for cat, is_float in zip(categories, is_float_col):
        data_fmt_dict = {
            'bg_color': ROW_COLORS[cat],
            'align': 'center',
            'border': 1,
            'border_color': GRID_BORDER_COLOR,
        }
        if is_float:
            data_fmt_dict['num_format'] = '0.00'
        data_formats.append(workbook.add_format(data_fmt_dict))
        url_formats.append(workbook.add_format({
            'bg_color': ROW_COLORS[cat],
            'color': '#0563C1',
            'underline': True,
            'align': 'center',
            'border': 1,
            'border_color': GRID_BORDER_COLOR,
        }))

    # Determine url column index if present
    url_col_idx = columns.index("ucsc_gb_url") if "ucsc_gb_url" in columns else None
    url_display_text = "View peak and gene(s) in genome browser"

    # Compute column widths from data only (header is rotated, needs no horizontal room).
    # The url column is sized off its display text, not the underlying URL string.
    col_widths = []
    for col_idx, col in enumerate(columns):
        if col_idx == url_col_idx:
            col_widths.append(len(url_display_text) + 2)
            continue
        max_data = output[col].cast(pl.Utf8).str.len_chars().max() or 0
        col_widths.append(max(int(max_data), 1) + 2)

    # Write headers
    for col_idx, (col, fmt, width) in enumerate(zip(columns, header_formats, col_widths)):
        worksheet.write(0, col_idx, col, fmt)
        worksheet.set_column(col_idx, col_idx, width)

    worksheet.freeze_panes(1, 0)

    # Auto-filter on chr column if present
    if "chr" in columns:
        last_col_letter = xlsxwriter.utility.xl_col_to_name(len(columns) - 1)
        worksheet.autofilter(f"A1:{last_col_letter}1")

    for col_idx, col in enumerate(columns):
        col_data = output[col].to_list()
        if col_idx == url_col_idx:
            for row_idx, value in enumerate(col_data, start=1):
                if value and str(value).startswith("http"):
                    worksheet.write_url(row_idx, col_idx, str(value), url_formats[col_idx], url_display_text)
                else:
                    worksheet.write(row_idx, col_idx, value, data_formats[col_idx])
        else:
            worksheet.write_column(1, col_idx, col_data, data_formats[col_idx])

    workbook.close()


def write_to_csv(output: pl.DataFrame, output_name: str, out_dir: str) -> None:
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    output.write_csv(os.path.join(out_dir, output_name) + ".csv")
