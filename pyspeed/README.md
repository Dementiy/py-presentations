Сборка mypyc:

```
poetry run mypyc dtwimpls/mypyc_dtw.py
```

Сборка Cython (so-файлы должны в итоге лежать в папке dtwimpls):

```
poetry run python setup.py build_ext --inplace
```

Сборка rust-биндингов:

```
poetry run maturin develop
```

