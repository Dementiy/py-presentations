from typing import Annotated, Literal, TypeVar

import numpy as np
import numpy.typing as npt
from numba import config, njit  # type: ignore

config.DISABLE_JIT = False

T = TypeVar("T", bound=np.generic)

Array1D = Annotated[npt.NDArray[T], Literal["N"]]
Array2D = Annotated[npt.NDArray[T], Literal["N", "M"]]


@njit("f4[:,:](f4[:], f4[:])", cache=True)
def cost_matrix(x: Array1D[np.float32], y: Array1D[np.float32]) -> Array2D[np.float32]:
    cost: Array2D[np.float32] = np.zeros((len(x), len(y)), dtype=np.float32)
    for i in range(len(x)):
        for j in range(len(y)):
            cost[i, j] = (x[i] - y[j]) ** 2
    return np.sqrt(cost)


@njit("f4[:,:](f4[:,:])", cache=True)
def accumulated_cost_matrix(cost: Array2D[np.float32]) -> Array2D[np.float32]:
    n, m = cost.shape
    d = np.zeros_like(cost, dtype=np.float32)
    d[0, 0] = cost[0, 0]
    for i in range(1, n):
        d[i, 0] = d[i - 1, 0] + cost[i, 0]
    for i in range(1, m):
        d[0, i] = d[0, i - 1] + cost[0, i]
    for i in range(1, n):
        for j in range(1, m):
            d[i, j] = min(d[i - 1, j], d[i, j - 1], d[i - 1, j - 1]) + cost[i, j]
    return d


@njit("u4[:,:](f4[:,:])", cache=True)
def warping_path(d: Array2D[np.float32]) -> Array2D[np.uint32]:
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


@njit("u4[:,:](f4[:], f4[:])", cache=True)
def dtw_path(x: Array1D[np.float32], y: Array1D[np.float32]) -> Array2D[np.uint32]:
    cost = cost_matrix(x, y)
    d = accumulated_cost_matrix(cost)
    return warping_path(d)
