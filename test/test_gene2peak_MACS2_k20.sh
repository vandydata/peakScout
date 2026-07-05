#! /bin/bash

peakScout gene2peak \
    --gene_file test/test_genes.txt \
    --peak_file test/test_MACS2.bed \
    --peak_type MACS2 \
    --k 20 \
    --ref_dir test/test-reference/test \
    --output_name test_gene2peak_MACS2_k20 \
    --o test/results/ \
    --output_type csv

python3 test/compare_csv.py \
    --a test/results/test_gene2peak_MACS2_k20.csv \
    --e test/test_gene2peak_MACS2_k20_expected_results.csv
