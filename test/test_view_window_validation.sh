#! /bin/bash

output=$(peakScout peak2gene \
    --peak_file test/test_MACS2.bed \
    --peak_type MACS2 \
    --species_genome mm10 \
    --k 3 \
    --view_window 1.0 \
    --ref_dir test/test-reference/test \
    --output_name test_view_window_invalid \
    --o test/results/ \
    --output_type csv 2>&1)
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "test_view_window_validation: FAILED (expected a non-zero exit for view_window=1.0)"
    exit 1
fi

if ! grep -q "view_window must be in \[0, 1)" <<< "$output"; then
    echo "test_view_window_validation: FAILED (expected validation error message not found)"
    echo "$output"
    exit 1
fi

if [ -f test/results/test_view_window_invalid.csv ]; then
    echo "test_view_window_validation: FAILED (should not have produced output)"
    exit 1
fi

echo "test_view_window_validation: PASSED"
