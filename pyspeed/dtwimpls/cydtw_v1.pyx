#cython: language_level=3

import numpy as np
cimport numpy as cnp
cimport cython

cnp.import_array()


@cython.boundscheck(False)
@cython.wraparound(False)
cdef cnp.ndarray[cnp.float32_t, ndim=2] cost_matrix(cnp.ndarray[cnp.float32_t, ndim=1] x, cnp.ndarray[cnp.float32_t, ndim=1] y):
    cdef cnp.ndarray[cnp.float32_t, ndim=2] cost = np.zeros((len(x), len(y)), dtype=np.float32)
    cdef int i
    cdef int j

    for i in range(len(x)):
        for j in range(len(y)):
            cost[i, j] = (x[i] - y[j]) ** 2
    return np.sqrt(cost)


# cdef cnp.ndarray[cnp.float32_t, ndim=2] cost_matrix(cnp.ndarray[cnp.float32_t, ndim=1] x, cnp.ndarray[cnp.float32_t, ndim=1] y):
#     diff = x[:, np.newaxis] - y[np.newaxis, :]
#     return np.sqrt(diff * diff)


@cython.boundscheck(False)
@cython.wraparound(False)
cdef cnp.ndarray[cnp.float32_t, ndim=2] accumulated_cost_matrix(cnp.ndarray[cnp.float32_t, ndim=2] cost):
    cdef int n = cost.shape[0]
    cdef int m = cost.shape[1]
    cdef cnp.ndarray[cnp.float32_t, ndim=2] d = np.zeros(shape=(n, m), dtype=np.float32)
    cdef int i
    cdef int j

    d[0, 0] = cost[0, 0]
    for i in range(1, n):
        d[i, 0] = d[i - 1, 0] + cost[i, 0]
    for i in range(1, m):
        d[0, i] = d[0, i - 1] + cost[0, i]
    for i in range(1, n):
        for j in range(1, m):
            d[i, j] = min(d[i - 1, j], d[i, j - 1], d[i - 1, j - 1]) + cost[i, j]
    return d


@cython.boundscheck(False)
@cython.wraparound(False)
cdef cnp.ndarray[cnp.uint32_t, ndim=2] warping_path(cnp.ndarray[cnp.float32_t, ndim=2] d):
    cdef int n = d.shape[0]
    cdef int m = d.shape[1]
    cdef int i = n - 1
    cdef int j = m - 1
    cdef int k = 0
    cdef cnp.ndarray[cnp.uint32_t, ndim=2] path = np.empty((n + m, 2), dtype=np.uint32)
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


@cython.boundscheck(False)
@cython.wraparound(False)
def dtw_path(cnp.ndarray[cnp.float32_t, ndim=1] x, cnp.ndarray[cnp.float32_t, ndim=1] y):
    cdef cnp.ndarray[cnp.float32_t, ndim=2] cost = cost_matrix(x, y)
    cdef cnp.ndarray[cnp.float32_t, ndim=2] d = accumulated_cost_matrix(cost)
    return warping_path(d)
