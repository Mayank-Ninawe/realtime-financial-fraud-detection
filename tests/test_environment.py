"""Basic environment and dependency checks."""

import pandas as pd
import numpy as np

def test_pandas_import():
    assert pd.__version__

def test_numpy_import():
    assert np.__version__
