# pylint: disable=consider-using-enumerate,invalid-name
from typing import Annotated, Literal, TypeVar

import numpy as np
import numpy.typing as npt

T = TypeVar("T", bound=np.generic)

Array1D = Annotated[npt.NDArray[T], Literal["N"]]
Array2D = Annotated[npt.NDArray[T], Literal["N", "M"]]


def cost_matrix_iter(
    x: Array1D[np.float32], y: Array1D[np.float32]
) -> Array2D[np.float32]:
    # NOTE: col-wise vs row-wise
    cost: Array2D[np.float32] = np.zeros((len(x), len(y)), dtype=np.float32)
    for i in range(len(x)):
        for j in range(len(y)):
            cost[i, j] = (x[i] - y[j]) ** 2
    return np.sqrt(cost)


def cost_matrix_vec(
    x: Array1D[np.float32], y: Array1D[np.float32]
) -> Array2D[np.float32]:
    diff = x[:, np.newaxis] - y[np.newaxis, :]
    return np.sqrt(diff * diff)


# def cost_matrix_vec2(x: Array1D[np.float32], y: Array1D[np.float32]) -> Array2D[np.float32]:
#     # x = x.reshape(-1, 1)
#     # y = y.reshape(-1, 1)
#     x2 = (x * x)[:, np.newaxis]
#     y2 = (y * y)[np.newaxis, :]
#     xy = x.reshape(-1, 1) @ y.reshape(-1, 1).T
#     return np.abs(x2 + y2 - 2 * xy)


def accumulated_cost_matrix(cost: Array2D[np.float32]) -> Array2D[np.float32]:
    n, m = cost.shape
    d = np.zeros_like(cost, dtype=np.float32)
    d[0, 0] = cost[0, 0]
    for i in range(1, n):
        d[i, 0] = d[i - 1, 0] + cost[i, 0]
    for i in range(1, m):
        d[0, i] = d[0, i - 1] + cost[0, i]
    # d[1:, 0] = np.cumsum(d[:-1, 0] + cost[1:, 0])
    # d[0, 1:] = np.cumsum(d[0, :-1] + cost[0, 1:])

    # ii, jj = np.mgrid[1:n, 1:m]
    # for i, j in np.c_[ii.ravel(), jj.ravel()]:
    for i in range(1, n):
        for j in range(1, m):
            d[i, j] = min(d[i - 1, j], d[i, j - 1], d[i - 1, j - 1]) + cost[i, j]
    return d


def warping_path(d: Array2D[np.float32]) -> Array1D[np.uint32]:
    n, m = d.shape
    i, j = n - 1, m - 1
    k = 0
    path = np.empty((n + m, 2), dtype=np.uint32)
    path[k, 0] = i
    path[k, 1] = j

    while i > 0 or j > 0:
        k += 1

        if i > 0:
            if j > 0:
                if d[i - 1, j] < d[i - 1, j - 1]:
                    if d[i - 1, j] < d[i, j - 1]:
                        path[k, 0] = i - 1
                        path[k, 1] = j
                        i -= 1
                    else:
                        path[k, 0] = i
                        path[k, 1] = j - 1
                        j -= 1
                else:
                    if d[i - 1, j - 1] < d[i, j - 1]:
                        path[k, 0] = i - 1
                        path[k, 1] = j - 1
                        i -= 1
                        j -= 1
                    else:
                        path[k, 0] = i
                        path[k, 1] = j - 1
                        j -= 1
            else:
                path[k, 0] = i - 1
                path[k, 1] = j
                i -= 1
        else:
            path[k, 0] = i
            path[k, 1] = j - 1
            j -= 1

    return path[: k + 1][::-1]


def dtw_path_v1(x: Array1D[np.float32], y: Array1D[np.float32]) -> Array1D[np.uint32]:
    cost = cost_matrix_iter(x, y)
    d = accumulated_cost_matrix(cost)
    return warping_path(d)


def dtw_path_v2(x: Array1D[np.float32], y: Array1D[np.float32]) -> Array1D[np.uint32]:
    cost = cost_matrix_vec(x, y)
    d = accumulated_cost_matrix(cost)
    return warping_path(d)


def generate_signals(n: int = 5000) -> tuple[Array1D[np.float32], Array1D[np.float32]]:
    rng = np.random.default_rng()
    x = np.arange(n) / n
    x = np.sin(2 * np.pi * x)
    y = x + rng.standard_normal(len(x))
    return x.astype(np.float32), y.astype(np.float32)


def examples() -> None:
    # x = np.array([1, 3, 9, 2, 1], dtype=np.float32)
    # y = np.array([2, 0, 0, 8, 7, 2], dtype=np.float32)

    # x = np.array([1, 2, 3, 4, 5], dtype=np.float32)
    # y = np.array([2, 3, 4], dtype=np.float32)

    x = np.array([3, 1, 2, 2, 1], dtype=np.float32)
    y = np.array([2, 0, 0, 3, 3, 1, 0], dtype=np.float32)

    cost = cost_matrix_vec(x, y)
    print(cost)
    d = accumulated_cost_matrix(cost)
    print(d)
    path = warping_path(d)
    print(path)


def use_timeit() -> None:
    from timeit import timeit

    print(
        timeit(
            "dtw_path_v2(x, y)",
            setup="x, y = generate_signals(1000)",
            globals=globals(),
            number=5,
        )
    )


if __name__ == "__main__":
    examples()
