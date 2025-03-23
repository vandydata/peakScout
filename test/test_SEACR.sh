#! /bin/bash

peakScout peak2gene \
    --peak_file test/test_SEACR.bed \
    --peak_type SEACR \
    --species test \
    --k 3 \
    --ref_dir test/test-reference \
    --output_name test_SEACR \
    --o test/results/ \
    --output_type csv

python3 test/compare_csv.py \
    --a test/results/test_SEACR.csv \
    --e test/test_SEACR_expected_results.csv
