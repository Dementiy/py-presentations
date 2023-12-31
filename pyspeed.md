# Ускорение кода на Python

<img width="500" alt="" src="https://github.com/Dementiy/presentations/assets/4396325/1db9d566-f83f-4e78-a927-e163803aeb39">

<!--
# Что почитать?
<img src="https://github.com/Dementiy/notes/assets/4396325/79fb949f-361e-44e1-83e4-8ac67d0a3d37" alt="image" width="300" height="auto">
<img src="https://github.com/Dementiy/notes/assets/4396325/4ccb0c72-3b9f-46bb-a024-909e440e23a2" alt="image" width="300" height="auto">
-->

# Чего нет в докладе?

- Потоков и GIL
- Процессов
- Распределенных (грид) вычислений (dispy / dask / ray и т.п.)
- Асинхронного программирования
- Вычислений на GPU
- ...

<img width="500" alt="" src="https://github.com/Dementiy/presentations/assets/4396325/b0008a04-1cad-4024-a6c6-07e6b9a1563a">

# Метрики и методологии

<img src="https://github.com/Dementiy/notes/assets/4396325/f480dd6a-8359-480f-80c4-1992f64962f9" alt="image" width="300" height="auto">

# Тесты производительности

Прежде чем начинать что-то оптимизировать надо написать бенчмарки (тесты производительности), например, с помощью [pytest-benchmark](https://github.com/ionelmc/pytest-benchmark).

```sh
poetry add pytest-benchmark
```

```toml
[tool.pytest.ini_options]
python_files = ["test_*.py", "bench_*.py"]
python_functions = ["test_*", "bench_*"]
addopts = "--benchmark-skip --benchmark-columns=mean,rounds --benchmark-min-rounds=5"
```

```python
# bench_dtw.py
@pytest.mark.benchmark(group="DTW benchmarks")
def bench_py_dtw(benchmark, xy):
    x, y = xy
    benchmark(py_dtw_path, x=x.tolist(), y=y.tolist())

@pytest.mark.benchmark(group="DTW benchmarks")
def bench_mypyc_dtw(benchmark, xy):
    x, y = xy
    benchmark(mypyc_dtw_path, x=x.tolist(), y=y.tolist())

@pytest.mark.benchmark(group="DTW benchmarks")
def bench_np_dtw_v1(benchmark, xy):
    x, y = xy
    benchmark(np_dtw_path_v1, x=x, y=y)
```

# Инструменты профилирования

 - [timeit](https://docs.python.org/3/library/timeit.html)
 - [cProfile](https://docs.python.org/3/library/profile.html) (pstats, snakeviz, ...)
 - [line_profiler](https://github.com/pyutils/line_profiler) (`LINE_PROFILE=1`)
 - [tracemalloc](https://docs.python.org/3/library/tracemalloc.html)
 - [memory_profiler](https://github.com/pythonprofilers/memory_profiler)
 - [py-spy](https://github.com/benfred/py-spy)
 - ...

# Классы проблем

 - IO-Bound
   - Диск
   - Сеть
 - CPU-Bound
   - Неверный выбор структур данных
   - Высокая алгоритмическая сложность текущего решения
   - Решение не использует более одного ядра процессора
   - Уперлись в производительность языка
   - ...

# Хранение сейсмических данных

<img src="https://github.com/Dementiy/notes/assets/4396325/3fa8c950-e5d5-42de-8fe1-a168f7863c2e" alt="image" width="500" height="auto">

# Сейсмический куб

<img src="https://github.com/Dementiy/notes/assets/4396325/9b8e4c4d-bcfe-465a-8622-655a43f6220c" alt="image" width="500" height="auto">

# SEGY

<img src="https://github.com/Dementiy/notes/assets/4396325/4a950bb0-8c5a-477e-866e-183495d44362" alt="image" width="500" height="auto">

# Паттерны доступа к данным

<img src="https://github.com/Dementiy/notes/assets/4396325/9b8e4c4d-bcfe-465a-8622-655a43f6220c" alt="image" width="500" height="auto">
<img src="https://github.com/Dementiy/notes/assets/4396325/8e1217f1-789d-4065-b9f5-d8dea2c480b8" alt="image" width="500" height="auto">

# [HDF5](https://github.com/h5py/h5py)

- Датасеты - многомерные массивы
- Атрибуты - мета-данные (ключ-значение)
- Группы - контейнеры, которые содержат датасеты и другие группы

```python
import h5py

with h5py.File(path, mode="w") as h5file:
    sl_grp = h5file.require_group("Cube")
    sl_grp.create_dateset("ilines", shape=(....), dtype=np.float32, compression="lzf", chunks=(...))
    sl_grp.create_dateset("hlines", shape=(....), dtype=np.float32, compression="lzf", chunks=(...))

    meta_grp = h5file.require_group("Meta")
    meta_grp.create_dataset("coordinates", ...)
    meta_grp.attrs["min_value"] = ...
    meta_grp.attrs["max_value"] = ...
    ...

    ilines = h5file["Cube/ilines"][:3]
```

# [Очистка кэша перед тестами](https://stackoverflow.com/questions/28845524/echo-3-proc-sys-vm-drop-caches-on-mac-osx)

```sh
# Linux
sync; echo 3 > /proc/sys/vm/drop_caches

# Mac OS
sync && sudo purge

# Windows
rammap.exe -Et
```

# Бинарные форматы данных для передачи по сети

<img src="https://github.com/Dementiy/notes/assets/4396325/d3e904c5-ecd7-49a1-be7d-3aa4a25c2f18" alt="image" width="500" height="auto">
<img width="500" alt="" src="https://github.com/Dementiy/notes/assets/4396325/e0ffce79-5fcb-40d6-ae15-4e51fc5a7bc4">

# [BSON](https://pypi.org/project/bson-py/)/[CBOR](https://github.com/agronholm/cbor2)

```json
{
  "coordinates": {
    "d588f1d2-...": {
      "3e4d3934-...": np.array([...])
    }
  },
  "intersections": [
    {
      "survey1": "d588f1d2-...",  "survey2": "6d632fba-...",
      "profile1": "3e4d3934-...", "profile2": "d0988737-...",
      "x": 541403.375, "y": 6720827.0,
      "t11": 219, "t11x": 541384.0, "t11y": 6720796.0,
      "t12": 220, "t12x": 541404.0, "t12y": 6720828.0,
      "t21": 547, "t21x": 541397.0, "t21y": 6720827.0,
      "t22": 548, "t22x": 541435.0, "t22y": 6720827.0,
    }
  ],
  "traces": {
    "d588f1d2-...": {
      "3e4d3934-...": {
        "индекс_трассы": np.array([...])
      }
    }
  }
}
```

# Выбор структуры данных
<img width="350" alt="" src="https://github.com/Dementiy/presentations/assets/4396325/a551b86d-5f89-4216-b7c3-6613bde49280"><img width="500" alt="" src="https://opendsa-server.cs.vt.edu/ODSA/Books/CS3/html/_images/KDtree.png">


# Выбор алгоритма

<img width="500" alt="" src="https://github.com/Dementiy/notes/assets/4396325/fee9481c-c0e1-4f8a-8478-3052b85332bb">
<img width="500 " alt="" src="https://github.com/Dementiy/notes/assets/4396325/7ce0ddcc-fde9-4519-a8ee-e75b1388af3d">

# Оптимизация работы с интерпретатором

- Использование микро-оптимизаций
- [PEP 659 – Specializing Adaptive Interpreter](https://peps.python.org/pep-0659/)
- [Динамическое генерирование байт-кода](http://webcache.googleusercontent.com/search?q=cache:DdYSe6ZU54kJ:https://medium.com/@yonatanzunger/advanced-python-achieving-high-performance-with-code-generation-796b177ec79&client=safari&sca_esv=580550388&hl=ru&gl=ru&strip=1&vwsrc=0)
- В [3.13](https://github.com/brandtbucher/cpython/tree/justin) будет JIT


# Dynamic Time Warping

<img width="231" alt="" src="https://github.com/Dementiy/notes/assets/4396325/7a1c80b5-a206-474a-babc-3110ca2e321c">
<img width="500" alt="" src="https://github.com/Dementiy/notes/assets/4396325/46ddd4e5-2bcb-423f-8a09-953559b239d9">
<img width="500" alt="" src="https://github.com/Dementiy/presentations/assets/4396325/6a48051d-cd3b-40e2-8f5d-293271f9c955">

# Numpy

- Компактное хранение массивов данных
- Возможность использовать широкий диапазон типов
- Использование отображений (view) (arr.base для получения ссылки на исходный массив)
- Векторизация вычислений
- Использование универсальных функций (ufuncs)
- Buffer protocol
- memoryview
- np.shares_memory
- ...

<img width="500" alt="" src="https://github.com/Dementiy/notes/assets/4396325/133a1998-8306-4b2b-a84d-438fa6fe1e2d">


# Cython

> Cython is an optimising static compiler for both the Python programming language and the extended Cython programming language (based on Pyrex). It makes writing C extensions for Python as easy as Python itself.

<img width="500" alt="" src="https://github.com/Dementiy/notes/assets/4396325/2a98352b-fdc0-4cb3-859f-e6caf47e5378">


- Высокая скорость
- Есть интерфейс к CPython C API
- Мы в мире С/С++ (указатели, ручное управление памятью и т.п.)
- Отсутсвие инструментов (менеджер зависимостей, поддержка редакторами, поддержка статическими анализаторами)

<!-- <img width="500" alt="" src="https://nin-jin.github.io/slides/fibers/react-only.gif"> -->

# Numba

> Numba translates Python functions to optimized machine code at runtime using the industry-standard LLVM compiler library. Numba-compiled numerical algorithms in Python can approach the speeds of C or FORTRAN.

<img width="500" alt="" src="https://github.com/Dementiy/presentations/assets/4396325/98d3361a-ce1f-43be-afe4-df6ea5d7d7d2">

<!--
# [Есть что добавить или поправить?](https://github.com/nin-jin/slides/blob/master/ui-kit/readme.md#есть-что-добавить-или-поправить)

![](https://habrastorage.org/webt/y3/gb/is/y3gbisydqnoyr5qwwmscn0gwmqq.gif)

- Дмитрий, как обычно, разобрал все по-полочкам. Мне очень понравился получившиеся подходы и техники. Хорошая визуализация. Из минусов подачи - слишком сухо что-ли. Дмитрий сразу прыгает с места в карьер. Но наверное если бы обьяснял, то контента было бы раза в 2 меньше.
- К сожалению уснул на второй половине. Хотелось бы рассказ пободрее. Не увлекает.
- Пожалуйста, хоть чуть-чуть привлекайте дизайнеров для создания презентаций, очень тяжело смотреть потому что банально ничего не видно. Ну и немножечко нудно... Хотя тема и правда важная.
- Вот это обязательно посмотрю.
-->
