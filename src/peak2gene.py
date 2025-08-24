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
    species: str,
    num_features: int,
    ref_dir: str,
    output_name: str,
    out_dir: str,
    output_type: str,
    option: str = "native_peak_boundaries",
    boundary: int = None,
    up_bound: int = None,
    down_bound: int = None,
    consensus: bool = False,
    preserve: bool = False,
) -> None:
    """
    Find the nearest genes for a given list of peaks.

    Parameters:
    peak_file (str): Path to the peak file.
    peak_type (str): Type of peak caller used to generate peak file (e.g. MACS2, SEACR, BED6).
    species (str): Species of the reference genome.
    num_features (int): Number of nearest features to find.
    ref_dir (str): Directory containing decomposed reference data.
    output_name (str): Name for output file.
    out_dir (str): Directory to output file.
    output_type (str): Output type (csv file or xlsx file).
    option (str): Option for defining start and end positions of peaks.
    boundary (int): Boundary for artificial peak boundary option. None if other options.
    up_bound (int): Maximum allowed distance between peak and upstream feature.
    down_bound (int): Maximum allowed distance between peak and downstream feature.
    consnsesus (bool): Whether to use consensus peaks.
    preserve (bool): Whether to preserve the original file columns.

    Returns:
    None

    Outputs:
    Excel sheet containing peak data, the nearest k genes for each peak, and the distance
    between those genes and the peak.
    """

    peaks = process_peaks(peak_file, peak_type, option, boundary, consensus)
    decomposed_peaks = decompose_features(peaks)
    output = find_nearest(
        decomposed_peaks, species, num_features, ref_dir, up_bound, down_bound, preserve
    )
    if output_type == "xlsx":
        write_to_excel(output, output_name, out_dir)
    elif output_type == "csv":
        write_to_csv(output, output_name, out_dir)
    else:
        raise ValueError("Invalid output type")


def find_nearest(
    decomposed_peaks: dict,
    species: str,
    num_features: int,
    ref_dir: str,
    up_bound: int,
    down_bound: int,
    preserve: bool,
) -> pd.DataFrame:
    """
    Find the nearest genes for a given list of peaks. Place these in a Pandas DataFrame.

    Parameters:
    decomposed_peaks (dict): Dictionary containing keys with chromosome number
                             mapped to Polars DataFrames with peaks on that chromosome.
    species (str): Species of the reference genome.
    num_features (int): Number of nearest features to find.
    ref_dir (str): Directory containing decomposed reference data.
    up_bound (int): Maximum allowed distance between peak and upstream feature.
    down_bound (int): Maximum allowed distance between peak and downstream feature.

    Returns:
    output (pd.DataFrame): Pandas DataFrame containing peak data, the nearest k genes for each peak,
    and the distance between those genes and the peak.

    Outputs:
    None
    """

    output = pl.DataFrame()
    for key in decomposed_peaks.keys():
        try:
            starts = pl.read_csv(
                os.path.join(ref_dir, species, "gene", key) + "_start.csv"
            )
            ends = pl.read_csv(os.path.join(ref_dir, species, "gene", key) + "_end.csv")
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
                        preserve,
                    ),
                ]
            )
        except:
            print(
                f"Warning: could not find feature information for chromosome {key}. \
                  Results for these peaks are not included in the output."
            )

    output = output.to_pandas()
    output = output.sort_values(by=["chr", "start"])

    return output
