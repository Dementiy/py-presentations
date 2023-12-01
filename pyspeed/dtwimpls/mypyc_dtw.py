# pylint: disable=consider-using-enumerate,invalid-name
from math import sqrt
from typing import TypeAlias, TypeVar

T = TypeVar("T", int, float)

Array1D: TypeAlias = list[T]
Array2D: TypeAlias = list[list[T]]


def cost_matrix(x: Array1D[float], y: Array1D[float]) -> Array2D[float]:
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
