#! /bin/bash

peakScout peak2gene \
    --peak_file test/test_BED6.bed \
    --peak_type BED6 \
    --species test \
    --k 3 \
    --ref_dir test/test-reference \
    --output_name test_BED6 \
    --o test/results/ \
    --output_type csv

python3 test/compare_csv.py \
    --a test/results/test_BED6.csv \
    --e test/test_BED6_expected_results.csv
