use ndarray::{Array2, s};
use numpy::ndarray::ArrayView1;
use numpy::PyReadonlyArray1;
use numpy::{IntoPyArray, PyArray2};
use pyo3::prelude::*;

fn cost_matrix(x: ArrayView1<'_, f32>, y: ArrayView1<'_, f32>) -> Array2<f32> {
    let n = x.len();
    let m = y.len();
    let mut cost = Array2::zeros((n, m));
    for i in 0..n {
        for j in 0..m {
            cost[[i, j]] = f32::sqrt((x[i] - y[j]) * (x[i] - y[j]));
        }
    }
    cost
}

fn accumulated_cost_matrix(cost: Array2<f32>) -> Array2<f32> {
    let shape: &[usize] = cost.shape();
    let n = shape[0];
    let m = shape[1];
    let mut d = Array2::zeros((n, m));
    d[[0, 0]] = cost[[0, 0]];
    for i in 1..n {
        d[[i, 0]] = d[[i - 1, 0]] + cost[[i, 0]];
    }
    for i in 1..m {
        d[[0, i]] = d[[0, i - 1]] + cost[[0, i]];
    }
    for i in 1..n {
        for j in 1..m {
            d[[i, j]] =
                f32::min(f32::min(d[[i - 1, j]], d[[i, j - 1]]), d[[i - 1, j - 1]]) + cost[[i, j]]
        }
    }
    d
}

fn warping_path(d: Array2<f32>) -> Array2<u32> {
    let shape = d.shape();
    let n = shape[0];
    let m = shape[1];
    let mut i = n - 1;
    let mut j = m - 1;
    let mut k = 0;

    let mut path = Array2::zeros((n + m, 2));
    path[[k, 0]] = i;
    path[[k, 1]] = j;

    while i > 0 || j > 0 {
        k += 1;

        if i > 0 {
            if j > 0 {
                if d[[i - 1, j]] < d[[i - 1, j - 1]] {
                    if d[[i - 1, j]] < d[[i, j - 1]] {
                        path[[k, 0]] = i - 1;
                        path[[k, 1]] = j;
                        i -= 1;
                    } else {
                        path[[k, 0]] = i;
                        path[[k, 1]] = j - 1;
                        j -= 1;
                    }
                } else {
                    if d[[i - 1, j - 1]] < d[[i, j - 1]] {
                        path[[k, 0]] = i - 1;
                        path[[k, 1]] = j - 1;
                        i -= 1;
                        j -= 1;
                    } else {
                        path[[k, 0]] = i;
                        path[[k, 1]] = j - 1;
                        j -= 1
                    }
                }
            } else {
                path[[k, 0]] = i - 1;
                path[[k, 1]] = j;
                i -= 1;
            }
        } else {
            path[[k, 0]] = i;
            path[[k, 1]] = j - 1;
            j -= 1;
        }
    }

    path.slice(s![..k+1;-1,..]).mapv(|x| x as u32).to_owned()
}

#[pymodule]
fn rudtw<'py>(_py: Python<'py>, m: &'py PyModule) -> PyResult<()> {
    // m.add_function(wrap_pyfunction!(dtw_path, m)?)?;
    #[pyfn(m)]
    #[pyo3(name = "dtw_path")]
    fn dtw_path<'py>(
        py: Python<'py>,
        x: PyReadonlyArray1<f32>,
        y: PyReadonlyArray1<f32>,
    ) -> &'py PyArray2<u32> {
        let xx = x.as_array();
        let yy = y.as_array();
        let cost = cost_matrix(xx, yy);
        let d = accumulated_cost_matrix(cost);
        let path = warping_path(d);
        path.into_pyarray(py)
    }

    Ok(())
}
