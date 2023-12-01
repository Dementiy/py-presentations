# pylint: disable = no-name-in-module,no-member,c-extension-no-member
import pytest

from dtwimpls.mypyc_dtw import dtw_path as mypyc_dtw_path
from dtwimpls.pydtw import dtw_path as py_dtw_path

# poetry run pytest --benchmark-only


@pytest.mark.benchmark(group="DTW benchmarks")
def bench_py_dtw(benchmark, xy):
    x, y = xy
    benchmark(py_dtw_path, x=x.tolist(), y=y.tolist())


@pytest.mark.benchmark(group="DTW benchmarks")
def bench_mypyc_dtw(benchmark, xy):
    x, y = xy
    benchmark(mypyc_dtw_path, x=x.tolist(), y=y.tolist())
