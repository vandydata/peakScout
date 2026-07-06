# ------------------------------------------------------------------------------
#                        __   _____                  __
#      ____  ___  ____ _/ /__/ ___/_________  __  __/ /_
#     / __ \/ _ \/ __ `/ //_/\__ \/ ___/ __ \/ / / / __/
#    / /_/ /  __/ /_/ / ,<  ___/ / /__/ /_/ / /_/ / /_
#   / .___/\___/\__,_/_/|_|/____/\___/\____/\__,_/\__/
#  /_/
#
# Copyright 2025 GNU AFFERO GENERAL PUBLIC LICENSE
# Alexander L. Lin, Lana A. Cartailler, Jean-Philippe Cartailler
# https://github.com/vandydata/peakScout
#
# ------------------------------------------------------------------------------

import os
import urllib.request

ENCODE_CRE_URLS = {
    "hg38": "https://downloads.wenglab.org/Registry-V4/GRCh38-cCREs.bed",
    "mm10": "https://downloads.wenglab.org/Registry-V4/mm10-cCREs.bed",
}


def get_cre(species: str, ref_dir: str) -> None:
    """
    Download ENCODE cCREs for a supported species and save to the reference directory.

    Parameters:
    species (str): Genome assembly identifier (e.g. hg38, mm10).
    ref_dir (str): Parent reference directory (same as used with decompose).

    Returns:
    None

    Outputs:
    BED file at ref_dir/species/cre/{species}-cre.bed
    """
    if species not in ENCODE_CRE_URLS:
        supported = ", ".join(sorted(ENCODE_CRE_URLS.keys()))
        raise ValueError(
            f"No built-in CRE source for '{species}'. "
            f"Built-in support: {supported}. "
            f"For other species, download a CRE BED file manually and pass it with --cre_file."
        )

    url = ENCODE_CRE_URLS[species]
    out_dir = os.path.join(ref_dir, species, "cre")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{species}-cre.bed")

    print(f"Downloading ENCODE cCREs for {species} from {url} ...")
    urllib.request.urlretrieve(url, out_path)
    print(f"Saved to {out_path}")
