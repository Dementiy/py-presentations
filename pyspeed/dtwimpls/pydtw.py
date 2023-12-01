# pylint: disable=consider-using-enumerate,invalid-name
from math import sqrt
from typing import TypeAlias, TypeVar

T = TypeVar("T", int, float)

Array1D: TypeAlias = list[T]
Array2D: TypeAlias = list[list[T]]


def cost_matrix(x: Array1D[float], y: Array1D[float], sqrt=sqrt) -> Array2D[float]:
    m, n = len(x), len(y)
    cost: Array2D[float] = [[0.0] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            cost[i][j] = sqrt((x[i] - y[j]) ** 2)
    return cost


def accumulated_cost_matrix(cost: Array2D[float]) -> Array2D[float]:
    n, m = len(cost), len(cost[0])
    d: Array2D[float] = [[0.0] * m for _ in range(n)]
    d[0][0] = cost[0][0]
    for i in range(1, n):
        d[i][0] = d[i - 1][0] + cost[i][0]
    for i in range(1, m):
        d[0][i] = d[0][i - 1] + cost[0][i]
    for i in range(1, n):
        for j in range(1, m):
            d[i][j] = min(d[i - 1][j], d[i][j - 1], d[i - 1][j - 1]) + cost[i][j]
    return d


def warping_path(d: Array2D[float]) -> list[tuple[int, int]]:
    n, m = len(d), len(d[0])
    i, j = n - 1, m - 1
    path: list[tuple[int, int]] = [(i, j)]

    while i > 0 or j > 0:
        if i > 0:
            if j > 0:
                if d[i - 1][j] < d[i - 1][j - 1]:
                    if d[i - 1][j] < d[i][j - 1]:
                        path.append((i - 1, j))
                        i -= 1
                    else:
                        path.append((i, j - 1))
                        j -= 1
                else:
                    if d[i - 1][j - 1] < d[i][j - 1]:
                        path.append((i - 1, j - 1))
                        i -= 1
                        j -= 1
                    else:
                        path.append((i, j - 1))
                        j -= 1
            else:
                path.append((i - 1, j))
                i -= 1
        else:
            path.append((i, j - 1))
            j -= 1

    return path[::-1]


def dtw_path(x: Array1D[float], y: Array1D[float]) -> list[tuple[int, int]]:
    cost = cost_matrix(x, y)
    d = accumulated_cost_matrix(cost)
    return warping_path(d)


def generate_signals(n: int = 5000) -> tuple[Array1D[float], Array1D[float]]:
    import numpy as np

    rng = np.random.default_rng()
    x = np.arange(n) / n
    x = np.sin(2 * np.pi * x)
    y = x + rng.standard_normal(len(x))
    return x.astype(np.float32).tolist(), y.astype(np.float32).tolist()


def examples() -> None:
    import numpy as np

    # x = np.array([1, 3, 9, 2, 1], dtype=np.float32)
    # y = np.array([2, 0, 0, 8, 7, 2], dtype=np.float32)
    # x = np.array([1, 2, 3, 4, 5], dtype=np.float32)
    # y = np.array([2, 3, 4], dtype=np.float32)

    x = np.array([3, 1, 2, 2, 1], dtype=np.float32)
    y = np.array([2, 0, 0, 3, 3, 1, 0], dtype=np.float32)

    cost = cost_matrix(x.tolist(), y.tolist())
    print(cost)
    d = accumulated_cost_matrix(cost)
    print(d)
    path = warping_path(d)
    print(path)


def use_timeit() -> None:
    from timeit import timeit

    print(
        timeit(
            "dtw_path(x, y)",
            setup="x, y = generate_signals(1000)",
            globals=globals(),
            number=5,
        )
    )


def use_c_profile() -> None:
    import cProfile
    import pstats
    from pstats import SortKey

    cProfile.run("x, y = generate_signals(2000); dtw_path(x, y)", "dtw_path.cprof")
    p = pstats.Stats("dtw_path.cprof")
    p.strip_dirs().sort_stats(SortKey.CUMULATIVE).print_stats(10)


def use_line_profiler() -> None:
    from line_profiler import LineProfiler

    profiler = LineProfiler()

    profiler.add_function(cost_matrix)
    profiler.add_function(accumulated_cost_matrix)
    profiler.add_function(warping_path)
    profiled_func = profiler(dtw_path)

    x, y = generate_signals(1000)
    profiled_func(x, y)
    profiler.print_stats(output_unit=0.001)


def use_memory_profiler() -> None:
    # poetry run python -m memory_profiler dtw/pydtw.py
    x, y = generate_signals(1000)
    cost = cost_matrix(x, y)
    d = accumulated_cost_matrix(cost)
    _ = warping_path(d)


def pep_659() -> None:
    # https://peps.python.org/pep-0659/
    import dis

    dis.dis(cost_matrix)
    x = [3.0, 1, 2, 2, 1]
    y = [2.0, 0, 0, 3, 3, 1, 0]
    _ = cost_matrix(x, y)
    dis.dis(cost_matrix)


if __name__ == "__main__":
    # examples()
    # use_timeit()
    # use_c_profile()
    # use_line_profiler()
    # use_memory_profiler()
    pep_659()
