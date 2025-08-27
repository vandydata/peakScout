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

import pandas as pd
import polars as pl
import os
from process_features import get_nearest_features, decompose_features
from process_input import process_peaks
from write_output import write_to_csv, write_to_excel


def peak2gene(
    peak_file: str,
    peak_type: str,
    num_features: int,
    ref_dir: str,
    output_name: str,
    out_dir: str,
    output_type: str,
    species_genome: str = None,
    option: str = "native_peak_boundaries",
    boundary: int = None,
    up_bound: int = None,
    down_bound: int = None,
    consensus: bool = False,
    drop_columns: bool = False,
    view_window: float = 0.2,
) -> None:
    """
    Find the nearest genes for a given list of peaks.

    Parameters:
    peak_file (str): Path to the peak file.
    peak_type (str): Type of peak caller used to generate peak file (e.g. MACS2, SEACR, BED6).
    num_features (int): Number of nearest features to find.
    ref_dir (str): Directory containing decomposed reference data.
    output_name (str): Name for output file.
    out_dir (str): Directory to output file.
    output_type (str): Output type (csv file or xlsx file).
    species_genome (str): Species of the reference genome.
    option (str): Option for defining start and end positions of peaks.
    boundary (int): Boundary for artificial peak boundary option. None if other options.
    up_bound (int): Maximum allowed distance between peak and upstream feature.
    down_bound (int): Maximum allowed distance between peak and downstream feature.
    consensus (bool): Whether to use consensus peaks. Default False.
    drop_columns (bool): Whether to drop unnecessary columns from the original file. Default False.
    view_window (float): Proportion of the peak region in entire genome browser window. Default 0.2.

    Returns:
    None

    Outputs:
    Excel sheet containing peak data, the nearest k genes for each peak, and the distance
    between those genes and the peak.
    """

    peaks = process_peaks(peak_file, peak_type, option, boundary, consensus)
    decomposed_peaks = decompose_features(peaks)
    output = find_nearest(
        decomposed_peaks,
        species_genome,
        num_features,
        ref_dir,
        up_bound,
        down_bound,
        drop_columns,
        view_window,
    )
    if output_type == "xlsx":
        write_to_excel(output, output_name, out_dir)
    elif output_type == "csv":
        write_to_csv(output, output_name, out_dir)
    else:
        raise ValueError("Invalid output type")


def find_nearest(
    decomposed_peaks: dict,
    species_genome: str,
    num_features: int,
    ref_dir: str,
    up_bound: int,
    down_bound: int,
    drop_columns: bool,
    view_window: float,
) -> pd.DataFrame:
    """
    Find the nearest genes for a given list of peaks. Place these in a Pandas DataFrame.

    Parameters:
    decomposed_peaks (dict): Dictionary containing keys with chromosome number
                             mapped to Polars DataFrames with peaks on that chromosome.
    species_genome (str): Species of the reference genome.
    num_features (int): Number of nearest features to find.
    ref_dir (str): Directory containing decomposed reference data.
    up_bound (int): Maximum allowed distance between peak and upstream feature.
    down_bound (int): Maximum allowed distance between peak and downstream feature.
    drop_columns (bool): Whether to drop unnecessary columns from the original file.
    view_window (float): Proportion of the peak region in entire genome browser window.

    Returns:
    output (pd.DataFrame): Pandas DataFrame containing peak data, the nearest k genes for each peak,
    and the distance between those genes and the peak.

    Outputs:
    None
    """
    output = pl.DataFrame()
    for key in decomposed_peaks.keys():
        try:
            starts = pl.read_csv(os.path.join(ref_dir, "gene", key) + "_start.csv")
            ends = pl.read_csv(os.path.join(ref_dir, "gene", key) + "_end.csv")
            output = pl.concat(
                [
                    output,
                    get_nearest_features(
                        decomposed_peaks[key],
                        "gene_name",
                        starts,
                        ends,
                        up_bound,
                        down_bound,
                        num_features,
                        drop_columns,
                        species_genome,
                        view_window,
                    ),
                ]
            )
        except Exception as e:
            print(e)
            print(
                f"Warning: could not find feature information for chromosome {key}. \
                  Results for these peaks are not included in the output."
            )

    output = output.to_pandas()
    output = output.sort_values(by=["chr", "start"])

    return output
