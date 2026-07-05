#! /bin/bash

peakScout peak2gene \
    --peak_file test/test_MACS2.bed \
    --peak_type MACS2 \
    --species_genome mm10 \
    --k 3 \
    --up_bound 50000 \
    --down_bound 50000 \
    --ref_dir test/test-reference/test \
    --output_name test_peak2gene_MACS2_bounds \
    --o test/results/ \
    --output_type csv

python3 test/compare_csv.py \
    --a test/results/test_peak2gene_MACS2_bounds.csv \
    --e test/test_peak2gene_MACS2_bounds_expected_results.csv

python3 test/check_dist_dtype.py --csv test/results/test_peak2gene_MACS2_bounds.csv
