import argparse

import polars as pl


def main(args):
    df = pl.read_csv(args.csv)
    dist_cols = [c for c in df.columns if c.endswith("_dist2peak") or c.endswith("_dist2gene")]
    if not dist_cols:
        raise Exception(f"no dist columns found in {args.csv}")

    for col in dist_cols:
        dtype = df[col].dtype
        if dtype not in (pl.Int64, pl.Float64):
            raise Exception(
                f"column {col} has dtype {dtype}, expected a numeric dtype "
                "(regression: a missing-neighbor sentinel likely collapsed this "
                "column to a string dtype)"
            )

    print(f"check_dist_dtype: PASSED ({', '.join(dist_cols)} are numeric)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="peakScout: check dist columns stay numeric")
    parser.add_argument("--csv", type=str, required=True, help="Path to csv to check")
    main(parser.parse_args())
