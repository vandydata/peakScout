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
import xlsxwriter
import polars as pl

HEADER_COLORS = {
    "peak":  "#C6DCFF",
    "cre":   "#C6ECC6",
    "gene":  "#FFE0B2",
    "ucsc":  "#E8D5FF",
}

def _header_color(col_name: str) -> str:
    if col_name.startswith("cre_"):
        return HEADER_COLORS["cre"]
    if col_name.startswith("closest_"):
        return HEADER_COLORS["gene"]
    if col_name == "ucsc_genome_browser_urls":
        return HEADER_COLORS["ucsc"]
    return HEADER_COLORS["peak"]


def write_to_excel(output: pl.DataFrame, output_name: str, out_dir: str) -> None:
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    filepath = os.path.join(out_dir, output_name) + ".xlsx"
    workbook = xlsxwriter.Workbook(filepath)
    worksheet = workbook.add_worksheet("Sheet1")

    columns = output.columns

    # Build per-column header formats
    header_formats = []
    for col in columns:
        fmt = workbook.add_format({
            'bg_color': _header_color(col),
            'bold': True,
            'align': 'center',
            'border': 0,
        })
        header_formats.append(fmt)

    url_format = workbook.add_format({'color': '#0563C1', 'underline': True})

    # Compute column widths from data (vectorized via polars)
    col_widths = []
    for col in columns:
        max_data = output[col].cast(pl.Utf8).str.len_chars().max() or 0
        col_widths.append(max(len(col), int(max_data)) + 2)

    # Write headers
    for col_idx, (col, fmt, width) in enumerate(zip(columns, header_formats, col_widths)):
        worksheet.write(0, col_idx, col, fmt)
        worksheet.set_column(col_idx, col_idx, width)

    # Auto-filter on chr column if present
    if "chr" in columns:
        last_col_letter = xlsxwriter.utility.xl_col_to_name(len(columns) - 1)
        worksheet.autofilter(f"A1:{last_col_letter}1")

    # Determine url column index if present
    url_col_idx = columns.index("ucsc_genome_browser_urls") if "ucsc_genome_browser_urls" in columns else None

    # Get chr/start/end indices for URL display text
    chr_col_idx   = columns.index("chr")   if "chr"   in columns else None
    start_col_idx = columns.index("start") if "start" in columns else None
    end_col_idx   = columns.index("end")   if "end"   in columns else None

    # Write data rows
    for row_idx, row in enumerate(output.iter_rows(), start=1):
        for col_idx, value in enumerate(row):
            if col_idx == url_col_idx and value and str(value).startswith("http"):
                if chr_col_idx is not None and start_col_idx is not None and end_col_idx is not None:
                    display = f"Visualize {row[chr_col_idx]}:{row[start_col_idx]}-{row[end_col_idx]} in genome browser"
                else:
                    display = str(value)
                worksheet.write_url(row_idx, col_idx, str(value), url_format, display)
            else:
                worksheet.write(row_idx, col_idx, value)

    workbook.close()


def write_to_csv(output: pl.DataFrame, output_name: str, out_dir: str) -> None:
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    output.write_csv(os.path.join(out_dir, output_name) + ".csv")
