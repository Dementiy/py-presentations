# pylint: disable = no-name-in-module,no-member,c-extension-no-member
from itertools import combinations

import numpy.testing as npt
import rudtw  # type: ignore

import dtwimpls.cydtw_v1  # type: ignore
import dtwimpls.cydtw_v2  # type: ignore
from dtwimpls.mypyc_dtw import dtw_path as mypyc_dtw_path
from dtwimpls.nbdtw import dtw_path as nb_dtw_path
from dtwimpls.npdtw import dtw_path_v1 as np_dtw_path_v1
from dtwimpls.npdtw import dtw_path_v2 as np_dtw_path_v2
from dtwimpls.pydtw import dtw_path as py_dtw_path

# poetry run pytest --benchmark-skip --tb=no


def test_all_equal(subtests, xy):
    x, y = xy
    p1 = py_dtw_path(x.tolist(), y.tolist())
    p2 = mypyc_dtw_path(x.tolist(), y.tolist())
    p3 = np_dtw_path_v1(x, y)
    p4 = np_dtw_path_v2(x, y)
    p5 = dtwimpls.cydtw_v1.dtw_path(x, y)
    p6 = dtwimpls.cydtw_v2.dtw_path(x, y)
    p7 = nb_dtw_path(x, y)
    p8 = rudtw.dtw_path(x, y)

    ps = [
        ("py", p1),
        ("mypyc", p2),
        ("np_v1", p3),
        ("np_v2", p4),
        ("cy_v1", p5),
        ("cy_v2", p6),
        ("numba", p7),
        ("rust", p8),
    ]
    for (pi_label, pi), (pj_label, pj) in combinations(ps, 2):
        with subtests.test(msg=f"{pi_label} == {pj_label}"):
            npt.assert_array_equal(pi, pj, err_msg=f"{pi_label} != {pj_label}")
