#! /bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

export PATH="$PATH:$PROJECT_ROOT/src"

bash "$SCRIPT_DIR/remove_previous.sh"
bash "$SCRIPT_DIR/test_decomp.sh"
bash "$SCRIPT_DIR/test_peak2gene_MACS2.sh"
bash "$SCRIPT_DIR/test_peak2gene_SEACR.sh"
bash "$SCRIPT_DIR/test_peak2gene_BED6.sh"
bash "$SCRIPT_DIR/test_peak2gene_MACS2_cre.sh"
bash "$SCRIPT_DIR/test_gene2peak_MACS2.sh"
bash "$SCRIPT_DIR/test_gene2peak_SEACR.sh"
bash "$SCRIPT_DIR/test_gene2peak_BED6.sh"

echo "ALL TESTS PASSED"
