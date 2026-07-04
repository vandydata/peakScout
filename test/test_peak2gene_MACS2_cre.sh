#! /bin/bash

peakScout peak2gene \
    --peak_file test/test_MACS2.bed \
    --peak_type MACS2 \
    --species_genome mm10 \
    --k 3 \
    --ref_dir test/test-reference/test \
    --use_cre \
    --output_name test_peak2gene_MACS2_cre \
    --o test/results/ \
    --output_type csv

python3 test/compare_csv.py \
    --a test/results/test_peak2gene_MACS2_cre.csv \
    --e test/test_peak2gene_MACS2_cre_expected_results.csv
