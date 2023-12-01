# cython: language_level=3

import numpy as np
cimport numpy as cnp
cimport cython
from cython.parallel import prange
from libc.math cimport sqrt
from libc.stdlib cimport calloc, malloc, free

cnp.import_array()


@cython.boundscheck(False)
@cython.wraparound(False)
cdef float* cost_matrix(const cnp.float32_t[::1] x, const cnp.float32_t[::1] y, int n, int m) noexcept:
    cdef:
        float* cost = <float *>malloc((n * m) * sizeof(float))
        int i
        int j
        float diff

    # export LDFLAGS="-L/opt/homebrew/opt/libomp/lib"
    # export CPPFLAGS="-I/opt/homebrew/opt/libomp/include"
    for i in range(n):
        for j in range(m):
            diff = x[i] - y[j]
            cost[i * m + j] = sqrt(diff * diff)
    return cost


@cython.boundscheck(False)
@cython.wraparound(False)
cdef float* accumulated_cost_matrix(const float* cost, int n, int m) noexcept:
    cdef:
        float* d = <float *>calloc((n * m), sizeof(float))
        int i
        int j

    d[0] = cost[0]
    for i in range(1, n):
        d[i * m] = d[(i - 1) * m] + cost[i * m]

    for i in range(1, m):
        d[i] = d[i - 1] + cost[i]

    for i in range(1, n):
        for j in range(1, m):
            if d[(i - 1) * m + j] <= d[i * m + j - 1] and d[(i - 1) * m + j] <= d[(i - 1) * m + j - 1]:
                d[i * m + j] = d[(i - 1) * m + j] + cost[i * m + j]
            elif d[i * m + j - 1] <= d[(i - 1) * m + j - 1]:
                d[i * m + j] = d[i * m + j - 1] + cost[i * m + j]
            else:
                d[i * m + j] = d[(i - 1) * m + j - 1] + cost[i * m + j]
    return d


@cython.boundscheck(False)
@cython.wraparound(False)
cdef int* warping_path(const float* d, int n, int m, int *k) noexcept:
    cdef:
        int i = n - 1
        int j = m - 1
        int* path = <int *>calloc((n + m) * 2, sizeof(int))

    path[k[0] * 2] = i
    path[k[0] * 2 + 1] = j

    while i > 0 or j > 0:
        k[0] += 1

        if i > 0:
            if j > 0:
                if d[(i - 1) * m + j] < d[(i - 1) * m + j - 1]:
                    if d[(i - 1) * m + j] < d[i * m + j - 1]:
                        path[k[0] * 2] = i - 1
                        path[k[0] * 2 + 1] = j
                        i -= 1
                    else:
                        path[k[0] * 2] = i
                        path[k[0] * 2 + 1] = j - 1
                        j -= 1
                else:
                    if d[(i - 1) * m + j - 1] < d[i * m + j - 1]:
                        path[k[0] * 2] = i - 1
                        path[k[0] * 2 + 1] = j - 1
                        i -= 1
                        j -= 1
                    else:
                        path[k[0] * 2] = i
                        path[k[0] * 2 + 1] = j - 1
                        j -= 1
            else:
                path[k[0] * 2] = i - 1
                path[k[0] * 2 + 1] = j
                i -= 1
        else:
            path[k[0] * 2] = i
            path[k[0] * 2 + 1] = j - 1
            j -= 1

    return path


@cython.boundscheck(False)
@cython.wraparound(False)
def dtw_path(cnp.ndarray[cnp.float32_t, ndim=1] x, cnp.ndarray[cnp.float32_t, ndim=1] y):
    cdef cnp.float32_t[::1] x_v
    cdef cnp.float32_t[::1] y_v

    cdef int n = x.shape[0]
    cdef int m = y.shape[0]

    x_v = x
    y_v = y

    cdef float* cost = cost_matrix(x_v, y_v, n, m)
    cdef float* d = accumulated_cost_matrix(cost, n, m)
    cdef int k = 0
    cdef int* path = warping_path(d, n, m, &k)

    cdef cnp.ndarray[cnp.uint32_t, ndim=2] ret = np.empty((k + 1, 2), dtype=np.uint32)
    cdef int i
    for i in range(k + 1):
        ret[i, 0] = path[2 * i]
        ret[i, 1] = path[2 * i + 1]

    free(cost)
    free(d)
    free(path)

    return ret[::-1]
