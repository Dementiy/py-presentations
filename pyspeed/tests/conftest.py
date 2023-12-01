import numpy as np
import pytest


@pytest.fixture
def xy():
    rng = np.random.default_rng()
    n = 1000
    x = np.arange(n) / n
    x = np.sin(2 * np.pi * x)
    y = x + rng.standard_normal(len(x))
    return x.astype(np.float32), y.astype(np.float32)
