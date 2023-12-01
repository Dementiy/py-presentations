# pylint: disable = no-name-in-module,no-member,c-extension-no-member
import pytest
import rudtw  # type: ignore

import dtwimpls.cydtw_v1  # type: ignore
import dtwimpls.cydtw_v2  # type: ignore
from dtwimpls.mypyc_dtw import dtw_path as mypyc_dtw_path
from dtwimpls.nbdtw import dtw_path as nb_dtw_path
from dtwimpls.npdtw import dtw_path_v1 as np_dtw_path_v1
from dtwimpls.npdtw import dtw_path_v2 as np_dtw_path_v2
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


@pytest.mark.skip()
@pytest.mark.benchmark(group="DTW benchmarks")
def bench_np_dtw_v1(benchmark, xy):
    x, y = xy
    benchmark(np_dtw_path_v1, x=x, y=y)


@pytest.mark.benchmark(group="DTW benchmarks")
def bench_np_dtw_v2(benchmark, xy):
    x, y = xy
    benchmark(np_dtw_path_v2, x=x, y=y)


@pytest.mark.benchmark(group="DTW benchmarks")
def bench_cy_dtw_v1(benchmark, xy):
    x, y = xy
    benchmark(dtwimpls.cydtw_v1.dtw_path, x=x, y=y)


@pytest.mark.benchmark(group="DTW benchmarks")
def bench_cy_dtw_v2(benchmark, xy):
    x, y = xy
    benchmark(dtwimpls.cydtw_v2.dtw_path, x=x, y=y)


@pytest.mark.benchmark(group="DTW benchmarks")
def bench_nb_dtw(benchmark, xy):
    x, y = xy
    benchmark(nb_dtw_path, x=x, y=y)


@pytest.mark.benchmark(group="DTW benchmarks")
def bench_ru_dtw_v1(benchmark, xy):
    x, y = xy
    benchmark(rudtw.dtw_path, x=x, y=y)
