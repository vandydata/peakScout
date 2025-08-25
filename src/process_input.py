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

import polars as pl
import os


def process_peaks(
    file_path: str, peak_type: str, option: str, boundary: int, consensus: bool
) -> pl.DataFrame:
    """
    Read in peak data and create a Polars DataFrame to hold the data.

    Parameters:
    file_path (str): Path to the peak file.
    peak_type (str): Type of peak caller used to generate peak file (e.g. MACS2, SEACR, BED6).
    option (str): Option for defining start and end positions of peaks.
    boundary (int): Boundary for artificial peak boundary option. None if other options.
    consensus (bool): Whether to use consensus peaks.

    Returns:
    peaks (pl.DataFrame): Polars DataFrame containing all relevant peak data
                          from the input file.

    Outputs:
    None
    """

    if peak_type == "MACS2" and "xls" in file_path and not consensus:
        peaks = read_input_MACS2_xls(file_path)
    elif peak_type == "MACS2" and "bed" in file_path and not consensus:
        peaks = read_input_MACS2_bed(file_path)
    elif peak_type == "MACS2" and "narrowPeak" in file_path and not consensus:
        peaks = read_input_MACS2_bed(file_path)
    elif peak_type == "MACS2" and "bed" in file_path and consensus:
        peaks = read_input_MACS2_bed_consensus(file_path)
    elif peak_type == "SEACR" and not consensus:
        peaks = read_input_SEACR(file_path)
    elif peak_type == "BED6" and not consensus:
        peaks = read_input_BED6(file_path)
    else:
        raise TypeError("Invalid peak type")

    if "bed" in file_path:
        peaks = peaks.with_columns(pl.col("start") + 1)
        peaks = peaks.with_columns(pl.col("end") + 1)

    peaks = edit_peaks(peaks, option, boundary)
    return peaks


def read_input_MACS2_xls(file_path: str) -> pl.DataFrame:
    """
    Read in MACS2 peak data in Excel format.

    Parameters:
    file_path (str): Path to the peak file.

    Returns:
    peaks (pl.DataFrame): Polars DataFrame containing all relevant peak data
                          from the input file.

    Outputs:
    None
    """
    peaks = pl.read_csv(file_path, separator="\t", skip_rows=22)
    peaks = peaks.rename(
        {"-log10(pvalue)": "neg_log10_pvalue", "-log10(qvalue)": "neg_log10_qvalue"}
    )

    return peaks


def read_input_MACS2_bed(file_path: str) -> pl.DataFrame:
    """
    Read in MACS2 peak data in bed format.

    Parameters:
    file_path (str): Path to the peak file.

    Returns:
    peaks (pl.DataFrame): Polars DataFrame containing all relevant peak data
                          from the input file.

    Outputs:
    None
    """
    col_names = [
        "chr",
        "start",
        "end",
        "name",
        "score",
        "strand",
        "signal",
        "pvalue",
        "qvalue",
        "peak",
    ]
    peaks = pl.read_csv(file_path, has_header=False, separator="\t")

    rename_columns = {f"column_{i+1}": col_names[i] for i in range(peaks.width)}
    peaks = peaks.rename(dict(rename_columns))

    return peaks


def read_input_MACS2_bed_consensus(file_path: str) -> pl.DataFrame:
    """
    Read in MACS2 peak data in bed format.

    Parameters:
    file_path (str): Path to the peak file.

    Returns:
    peaks (pl.DataFrame): Polars DataFrame containing all relevant peak data
                          from the input file.

    Outputs:
    None
    """
    col_names = [
        "chr",
        "start",
        "end",
        "peak_starts",
        "peak_ends",
        "peak_names",
        "scores",
        "peak_lengths",
        "abs_summits",
        "pileups",
        "pvalues",
        "fold_enrichments",
        "qvalues",
        "strands",
        "source_files",
        "num_peaks",
        "avg_score",
        "avg_pileup",
        "avg_pvalue",
        "avg_fold_enrichment",
        "avg_qvalue",
    ]

    peaks = pl.read_csv(file_path, has_header=False, separator="\t", skip_rows=24)

    rename_columns = {f"column_{i+1}": col_names[i] for i in range(peaks.width)}
    peaks = peaks.rename(dict(rename_columns))

    rename_name_column = {"peak_names": "name"}
    peaks = peaks.rename(rename_name_column)

    return peaks


def read_input_SEACR(file_path: str) -> pl.DataFrame:
    """
    Read in SEACR peak data in bed format.

    Parameters:
    file_path (str): Path to the peak file.

    Returns:
    peaks (pl.DataFrame): Polars DataFrame containing all relevant peak data
                          from the input file.

    Outputs:
    None
    """
    col_names = ["chr", "start", "end", "name", "max_signal", "region"]
    peaks = pl.read_csv(file_path, has_header=False, separator="\t")

    rename_columns = {f"column_{i+1}": col_names[i] for i in range(peaks.width)}
    peaks = peaks.rename(dict(rename_columns))

    return peaks


def read_input_BED6(file_path: str) -> pl.DataFrame:
    """
    Read in BED6 format peak data (chrom, start, end, name, score, strand).

    Parameters:
    file_path (str): Path to the peak file.

    Returns:
    peaks (pl.DataFrame): Polars DataFrame containing all relevant peak data
                          from the input file.

    Outputs:
    None
    """
    col_names = ["chr", "start", "end", "name", "score", "strand"]
    peaks = pl.read_csv(file_path, has_header=False, separator="\t")

    rename_columns = {f"column_{i+1}": col_names[i] for i in range(min(peaks.width, 6))}
    peaks = peaks.rename(dict(rename_columns))

    return peaks


def edit_peaks(peaks: pl.DataFrame, option: str, boundary: int) -> pl.DataFrame:
    """
    Edit peak start and end positions based on option.

    Parameters:
    peaks (pl.DataFrame): Polars DataFrame containing relevant peak information.
    option (str): Option for defining start and end positions of peaks.
    boundary (int): Boundary for artificial peak boundary option. None if other options.

    Returns:
    peaks (pl.DataFrame): Polars DataFrame containing all relevant peak data
                          from the input file with edited start and end positions.

    Outputs:
    None
    """

    if option == "peak_summit":
        peaks.drop_in_place("start")
        peaks.with_columns((peaks.col("abs_summit")).alias("start"))
        peaks.drop_in_place("end")
        peaks.with_columns((peaks.col("abs_summit")).alias("end"))
    elif option == "artifical_peak_boundaries" and boundary is not None:
        peaks.drop_in_place("start")
        peaks.with_columns((peaks.col("abs_summit") - boundary).alias("start"))
        peaks.drop_in_place("end")
        peaks.with_columns((peaks.col("abs_summit") + boundary).alias("end"))
    elif option == "native_peak_boundaries":
        pass
    else:
        raise ValueError("Invalid peak start/end option")

    return peaks


def process_genes(file_path: str, species: str, ref_dir: str) -> pl.DataFrame:
    genes = pl.read_csv(file_path, has_header=False).to_numpy()[:, 0].tolist()
    gene_df = pl.DataFrame()
    for csv in os.listdir(os.path.join(ref_dir, species, "gene")):
        cur = pl.read_csv(os.path.join(ref_dir, species, "gene", csv))
        for gene in genes:
            if gene in cur.select(["gene_name"]).to_numpy():
                gene_df = pl.concat([gene_df, cur.filter(pl.col("gene_name") == gene)])
                genes.remove(gene)

    if genes:
        raise ValueError(genes[0] + " is not a valid gene.")

    gene_df = gene_df.rename({"gene_name": "name"})

    return gene_df
