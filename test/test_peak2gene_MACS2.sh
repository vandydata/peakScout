#! /bin/bash

peakScout peak2gene \
    --peak_file test/test_MACS2.bed \
    --peak_type MACS2 \
    --species test \
    --k 3 \
    --ref_dir test/test-reference \
    --output_name test_peak2gene_MACS2 \
    --o test/results/ \
    --output_type csv

python3 test/compare_csv.py \
    --a test/results/test_peak2gene_MACS2.csv \
    --e test/test_peak2gene_MACS2_expected_results.csv
