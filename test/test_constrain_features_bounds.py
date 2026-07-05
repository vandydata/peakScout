import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
from process_features import constrain_features


def main():
    starts_sub = np.array([[1000, 1010], [2000, 2010], [3000, 3010], [5000, 5010]])
    ends_sub = np.array([1010, 2010, 3010, 5010])

    result = constrain_features(
        peak_start=2500,
        peak_end=2600,
        starts=starts_sub,
        ends=ends_sub,
        up_bound=600,
        down_bound=600,
    )

    expected = (0, 3, 1, 2)
    assert result == expected, f"expected {expected}, got {result}"
    print("test_constrain_features_bounds: PASSED")


if __name__ == "__main__":
    main()
