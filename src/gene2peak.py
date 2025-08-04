import pandas as pd
import polars as pl
from process_features import get_nearest_features, decompose_features
from process_input import process_peaks, process_genes
from write_output import write_to_csv, write_to_excel


def gene2peak(
    peak_file: str,
    peak_type: str,
    gene_file: str,
    species: str,
    num_features: int,
    ref_dir: str,
    output_name: str,
    out_dir: str,
    output_type: str,
    option: str = "native_peak_boundaries",
    boundary: int = None,
    consensus: bool = False,
) -> None:
    """
    Find the nearest peaks for a given list of genes.

    Parameters:
    peak_file (str): Path to the peak file.
    peak_type (str): Type of peak caller used to generate peak file (e.g. MACS2, SEACR, BED6).
    gene_file (str): Path to the gene file.
    species (str): Species of the reference genome.
    num_features (int): Number of nearest features to find.
    ref_dir (str): Directory containing decomposed reference data.
    output_name (str): Name for output file.
    out_dir (str): Directory to output file.
    output_type (str): Output type (csv file or xlsx file).
    option (str): Option for defining start and end positions of peaks.
    boundary (int): Boundary for artificial peak boundary option. None if other options.
    consensus (bool): Whether to use consensus peaks.

    Returns:
    None

    Outputs:
    Excel sheet containing gene data, the nearest k peaks for each gene, and the distance
    between those peaks and the gene.
    """

    peaks = process_peaks(peak_file, peak_type, option, boundary, consensus)
    genes = process_genes(gene_file, species, ref_dir)

    decomposed_peaks = decompose_features(peaks)
    decomposed_genes = decompose_features(genes)

    output = find_nearest(decomposed_peaks, decomposed_genes, num_features)

    if output_type == "xlsx":
        write_to_excel(output, output_name, out_dir)
    elif output_type == "csv":
        write_to_csv(output, output_name, out_dir)
    else:
        raise ValueError("Invalid output type")


def find_nearest(
    decomposed_peaks: dict, decomposed_genes: dict, num_features: int
) -> pd.DataFrame:
    """
    Find the nearest peaks for a given list of genes. Place these in a Pandas DataFrame.

    Parameters:
    decomposed_peaks (dict): Dictionary containing keys with chromosome number
                             mapped to Polars DataFrames with peaks on that chromosome.
    decomposed_genes (dict): Dictionary containing keys with chromosome number
                             mapped to Polars DataFrames with genes on that chromosome.
    num_features (int): Number of nearest features to find.

    Returns:
    output (pd.DataFrame): Pandas DataFrame containing gene data, the nearest k peaks for each gene,
    and the distance between those peaks and the gene.

    Outputs:
    None
    """

    output = pl.DataFrame()

    for key in decomposed_genes.keys():
        if key in decomposed_peaks.keys():
            starts = decomposed_peaks[key].select(["name", "start", "end"])
            ends = decomposed_peaks[key].select(["name", "end"])
        else:
            starts = pl.DataFrame({}, schema=["name", "start", "end"])
            ends = pl.DataFrame({}, schema=["name", "end"])
        output = pl.concat(
            [
                output,
                get_nearest_features(
                    decomposed_genes[key],
                    "name",
                    starts,
                    ends,
                    None,
                    None,
                    num_features,
                    False,
                ),
            ]
        )

    output = output.to_pandas()
    output = output.sort_values(by=["chr", "name"])

    return output
