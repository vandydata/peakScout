#! /bin/bash

peakScout gene2peak \
    --gene_file test/test_genes.txt \
    --peak_file test/test_BED6.bed \
    --peak_type BED6 \
    --k 3 \
    --ref_dir test/test-reference/test \
    --output_name test_gene2peak_BED6 \
    --o test/results/ \
    --output_type csv

python3 test/compare_csv.py \
    --a test/results/test_gene2peak_BED6.csv \
    --e test/test_gene2peak_BED6_expected_results.csv
