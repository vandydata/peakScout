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
import numpy as np


def get_nearest_features(
    roi: pl.DataFrame,
    feature: str,
    starts: pl.DataFrame,
    ends: pl.DataFrame,
    up_bound: int,
    down_bound: int,
    k: int,
    drop_columns: bool,
    species_genome: str,
    view_window: float = 0.2,
) -> pl.DataFrame:
    """
    Determine the nearest k features to each peak in roi using the reference
    starts and ends.

    Parameters:
    roi (pl.DataFrame): Polars DataFrame containing peaks and relevant information.
    feature (str): The feature of interest.
    starts (pl.DataFrame): Polars DataFrame of reference features sorted by start position.
    ends (pl.DataFrame): Polars DataFrame of reference features sorted by end position.
    up_bound (int): Maximum allowed distance between peak and upstream feature.
    down_bound (int): Maximum allowed distance between peak and downstream feature.
    k (int): Number of nearest features to collect.
    drop_columns (bool): Whether to drop unnecessary columns from the original file.
    species_genome (str): Species of the reference genome.
    view_window (float): Proportion of the peak region in entire genome browser window.

    Returns:
    return_roi (pl.DataFrame): Polars DataFrame containing peak information, the
    nearest k features to that peak, and the distances between those k features
    and the peak.

    Outputs:
    None
    """

    starts_sub = starts.select(["start", "end"]).to_numpy()
    ends_sub = ends.select("end").to_numpy().flatten()
    assert len(starts_sub) == len(ends_sub)

    start_features = starts.select(feature).to_numpy().flatten()
    end_features = ends.select(feature).to_numpy().flatten()

    if drop_columns:
        return_roi = roi.select(["name", "chr", "start", "end"]).clone()
    else:
        return_roi = roi.clone()

    index = 0

    overlap_features = []
    overlap_index = 0

    features_to_add, dists_to_add = gen_init(k)

    for peak in return_roi.iter_rows(named=True):
        peak_start = peak["start"]
        peak_end = peak["end"]

        c_starts_sub, c_ends_sub, c_start_features, c_end_features = constrain_features(
            peak_start,
            peak_end,
            starts_sub,
            ends_sub,
            start_features,
            end_features,
            up_bound,
            down_bound,
        )

        assert len(c_start_features) == len(c_starts_sub)
        assert len(c_end_features) == len(c_ends_sub)

        overlap_features, overlap_index = find_overlaps(
            peak_start, peak_end, c_starts_sub, overlap_features, overlap_index
        )

        i = k
        overlap_ctr = 0

        while overlap_ctr < len(overlap_features) and i > 0:
            update_to_add(
                features_to_add,
                dists_to_add,
                c_start_features,
                0,
                k - i + 1,
                overlap_features[overlap_ctr],
            )
            overlap_ctr += 1
            i -= 1

        ds_index = overlap_index
        us_index = len(c_end_features) - 1

        while i > 0 and us_index > -1 and ds_index < len(c_start_features):
            ds_dist = max(0, c_starts_sub[ds_index][0] - peak_end)
            us_dist = max(0, peak_start - c_ends_sub[us_index])

            if ds_dist == 0:
                ds_index += 1
                continue

            if us_dist == 0:
                us_index -= 1
                continue

            if ds_dist < us_dist:
                update_to_add(
                    features_to_add,
                    dists_to_add,
                    c_start_features,
                    ds_dist,
                    k - i + 1,
                    ds_index,
                )
                ds_index += 1
            else:
                update_to_add(
                    features_to_add,
                    dists_to_add,
                    c_end_features,
                    -1 * us_dist,
                    k - i + 1,
                    us_index,
                )
                us_index -= 1

            i -= 1

        if i > 0 and us_index < 0:
            while i > 0 and ds_index < len(c_start_features):
                ds_dist = c_starts_sub[ds_index][0] - peak_end
                ds_dist = max(0, ds_dist)
                update_to_add(
                    features_to_add,
                    dists_to_add,
                    c_start_features,
                    ds_dist,
                    k - i + 1,
                    ds_index,
                )
                ds_index += 1
                i -= 1
        elif i > 0 and ds_index >= len(c_start_features):
            while i > 0 and us_index > -1:
                us_dist = peak_start - c_ends_sub[us_index]
                us_dist = max(0, us_dist)
                update_to_add(
                    features_to_add,
                    dists_to_add,
                    c_end_features,
                    -1 * us_dist,
                    k - i + 1,
                    us_index,
                )
                us_index -= 1
                i -= 1

        while i > 0:
            features_to_add[k - i + 1].append("N/A")
            dists_to_add[k - i + 1].append("N/A")
            i -= 1

        index += 1

    return gen_return_roi(
        return_roi,
        feature,
        features_to_add,
        dists_to_add,
        k,
        species_genome,
        view_window,
    )


def constrain_features(
    peak_start: int,
    peak_end: int,
    starts: np.ndarray,
    ends: np.ndarray,
    start_features: np.ndarray,
    end_features: np.ndarray,
    up_bound: int,
    down_bound: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Constrain the reference start and ends features contain only valid features --
    those within down_bound/up_bound distance of the peak and those on one
    particular side of the peak.

    Parameters:
    peak_start (int): Start position of peak.
    peak_end (int): End position of peak.
    starts (np.ndarray): NumPy array of start positions of reference features.
    ends (np.ndarray): NumPy array of end positions of reference features.
    start_features (np.ndarray): NumPy array of reference features sorted by start position.
    end_features (np.ndarray): NumPy array of reference features sorted by end position.
    up_bound (int): Maximum allowed distance between peak and upstream feature.
    down_bound (int): Maximum allowed distance between peak and downstream feature.

    Returns:
    c_starts (np.ndarray): NumPy array containing constrained start positions of reference features.
    c_ends (np.ndarray): NumPy array containing constrained end positions of reference features.
    c_start_features (np.ndarray): NumPy array containing constrained reference features sorted by start position.
    c_end_features (np.ndarray): NumPy array containing constrained reference features sorted by end position.

    Outputs:
    None
    """
    if down_bound is not None:
        ds_upper = starts.searchsorted(peak_end + down_bound, side="right")
    else:
        ds_upper = len(starts)

    if up_bound is not None:
        us_lower = ends.searchsorted(peak_start - up_bound, side="left")
    else:
        us_lower = 0

    ds_lower = 0
    us_upper = ends.searchsorted(peak_end, side="right")

    c_starts = starts[ds_lower:ds_upper]
    c_ends = ends[us_lower:us_upper]

    c_start_features = start_features[ds_lower:ds_upper]
    c_end_features = end_features[us_lower:us_upper]

    return c_starts, c_ends, c_start_features, c_end_features


def check_overlap(
    peak_start: int, peak_end: int, starts: np.ndarray, index: int
) -> bool:
    """
    Determine if the feature at the given index overlaps with the peak.

    Parameters:
    peak_start (int): Start position of peak.
    peak_end (int): End position of peak.
    starts (np.ndarray): NumPy array of start positions of reference features.
    index (int): Index of the feature in question.

    Returns:
    True if the feature overlaps the peak; false otherwise.

    Outputs:
    None
    """
    return (starts[index][0] <= peak_start and starts[index][1] >= peak_start) or (
        starts[index][0] <= peak_end and starts[index][1] >= peak_end
    )


def find_overlaps(
    peak_start: int,
    peak_end: int,
    starts: np.ndarray,
    overlap_features: list,
    overlap_index: int,
) -> tuple[list, int]:
    """
    Find the indicies of genes that overlap with the peak.

    Parameters:
    peak_start (int): Start position of peak.
    peak_end (int): End position of peak.
    starts (np.ndarray): NumPy array of start positions of reference features.
    overlap_features (list): A list of overlapping features from the previous peak. If this
                             is the first peak, this list is empty.
    overlap_index (int): The index of the first feature in starts that begins after the previous peak ends.
                         If this is the first peak, this integer is 0.

    Returns:
    overlap_features (list): A list of overlapping features for the given peak.
    overlap_index (int): Index of the first feature in starts that begins after the current peak ends.

    Outputs:
    None
    """
    for gene in overlap_features:
        if not check_overlap(peak_start, peak_end, starts, gene):
            overlap_features.remove(gene)

    while len(starts) > overlap_index and starts[overlap_index][0] <= peak_end:
        if check_overlap(peak_start, peak_end, starts, overlap_index):
            overlap_features.append(overlap_index)
        overlap_index += 1

    return overlap_features, overlap_index


def gen_return_roi(
    return_roi: pl.DataFrame,
    feature: str,
    features_to_add: dict,
    dists_to_add: dict,
    k: int,
    species_genome: str,
    view_window: float = 0.2,
) -> pl.DataFrame:
    """
    Generates Polars DataFrame containing peak information, the nearest k features to that peak,
    and the distances between those k features and the peak.

    Parameters:
    return_roi (pl.DataFrame): Skeleton for return Polars DataFrame with all necessary columns.
    feature (str): Feature in question.
    features_to_add (dict): Dictionary that maps integer n with a list of the nth closest feature.
    dists_to_add (dict): Dictionary that maps integer n with a list of the distance between the peak
                         and the nth closest feature.
    k (int): Number of closest features to determine.
    species_genome (str): Species of the reference genome.
    view_window (float): Proportion of the peak region in entire genome browser window.

    Returns:
    return_roi (pl.DataFrame): Polars DataFrame containing peak information, the nearest k features to that peak,
    and the distances between those k features and the peak.

    Outputs:
    None
    """
    for i in range(1, k + 1):
        return_roi = return_roi.with_columns(
            [
                pl.Series("closest_" + feature + "_" + str(i), features_to_add[i]),
                pl.Series(
                    "closest_" + feature + "_" + str(i) + "_dist", dists_to_add[i]
                ),
            ]
        )

    if species_genome:
        species_genome_col = get_ucsc_browser_urls(
            species_genome, return_roi, view_window
        )
        return_roi = return_roi.with_columns(
            pl.Series("ucsc_genome_browser_urls", species_genome_col)
        )

    return return_roi


def get_ucsc_browser_urls(
    species_genome: str, df: pl.DataFrame, view_window: float = 0.2
) -> list:
    """
    Generates UCSC Genome Browser URLs for each peak in the DataFrame.

    Parameters:
    species_genome (str): Species of the reference genome.
    df (pl.DataFrame): Polars DataFrame containing peak information.

    Returns:
    urls (list): List of UCSC Genome Browser URLs for each peak.

    Outputs:
    None
    """
    base_url = (
        "https://genome.ucsc.edu/cgi-bin/hgTracks?db=" + species_genome + "&position="
    )
    highlight = "&highlight="
    urls = []

    for row in df.iter_rows(named=True):
        chr = row["chr"]
        start = row["start"]
        end = row["end"]
        peak_length = end - start
        window_start = max(1, int(start - peak_length / ((1 - view_window) / 2)))
        window_end = int(end + peak_length / ((1 - view_window) / 2))
        url = f"{base_url}chr{chr}:{window_start}-{window_end}{highlight}chr{chr}:{start}-{end}"
        urls.append(url)

    return urls


def gen_init(k: int) -> tuple[dict, dict]:
    """
    Generates dictionaries to add to Polars DataFrame skeleton for nearest feature information.

    Parameters:
    k (int): Number of nearest features to determine.

    Returns:
    features_to_add (dict): Dictionary that maps integer n with a list of the nth closest feature.
    dists_to_add (dict): Dictionary that maps integer n with a list of the distance between the peak
                         and the nth closest feature.

    Outputs:
    None
    """
    features_to_add = {}
    dists_to_add = {}
    for i in range(1, k + 1):
        features_to_add[i] = []
        dists_to_add[i] = []

    return features_to_add, dists_to_add


def update_to_add(
    add_features: dict,
    add_dists: dict,
    features: np.ndarray,
    dist: int,
    add_index: int,
    feature_index: int,
) -> None:
    """
    Adds a feature and its distance from a peak to given dictionaries.

    Parameters:
    add_features (dict): Dictionary that maps integer n with a list of the nth closest feature.
    add_dists (dict): Dictionary that maps integer n with a list of the distance between the peak
                         and the nth closest feature.
    features (np.ndarray): NumPy array containing list of features.
    dist (int): Distance to add to dictionary.
    add_index (int): Index of peak for updating.
    feature_index (int): Index of feature.

    Returns:
    None

    Outputs:
    Updates add_features and add_dists to contain the newest feature and dist.
    """
    add_features[add_index].append(features[feature_index])
    add_dists[add_index].append(str(dist))


def decompose_features(features: pl.DataFrame) -> dict:
    """
    Decompose features by chromosome.

    Parameters:
    features (pl.DataFrame): Polars DataFrame containing feature information.

    Returns:
    decomposed_features (dict): Dictionary containing keys with chromosome number
                                mapped to Polars DataFrames with features on that chromosome.

    Outputs:
    None
    """

    decomposed_feat = {
        "chr" + str(name[0]) if "chr" not in str(name[0]) else str(name[0]): group
        for name, group in features.group_by(["chr"])
    }
    for key in decomposed_feat:
        decomposed_feat[key] = decomposed_feat[key].sort("start")

    return decomposed_feat
