import numpy as np
from Cython.Build import cythonize
from setuptools import Extension, setup

# poetry run python setup.py build_ext --inplace
setup(
    ext_modules=cythonize(
        [
            Extension(
                "cydtw_v1",
                sources=["dtwimpls/cydtw_v1.pyx"],
                extra_compile_args=["-O3", "-ffast-math"],
            ),
            Extension(
                "cydtw_v2",
                sources=["dtwimpls/cydtw_v2.pyx"],
                extra_compile_args=["-O3", "-ffast-math"],
            ),
        ],
        annotate=True,
    ),
    include_dirs=[np.get_include()],
)
