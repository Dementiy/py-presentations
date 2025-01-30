## О чем доклад?

- Профилирование (отладка)
- Тесты производительности (performance testing)
- Методы оптимизации решения

## Чего в докладе нет?

- Профилирование сервиса целиком ([OpenTelemetry](https://github.com/open-telemetry/opentelemetry-python), [Prometheus](https://github.com/prometheus/prometheus))
- Нагрузочное тестирование ([locustio](https://github.com/locustio/locust)/[molotov](https://github.com/tarekziade/molotov))
- Профилирования взаимодействия с БД ([SQLAlchemy code profiling](https://docs.sqlalchemy.org/en/20/faq/performance.html#code-profiling) и [query timing](https://github.com/sqlalchemy/sqlalchemy/wiki/Profiling))
- Профилирование асинхронного кода ([yappi](https://github.com/sumerc/yappi))
- Будущее профилирования с [perf](https://docs.python.org/3/howto/perf_profiling.html) и [eBPF]()

## Что такое профилирование?

> [Profiling](https://en.wikipedia.org/wiki/Profiling_(computer_programming)) is a form of dynamic program analysis that measures, for example, the space (memory) or time complexity of a program, the usage of particular instructions, or the frequency and duration of function calls. Most commonly, profiling information serves to aid program optimization, and more specifically, performance engineering.

## Классификация профилировщиков

Профилировщики:
  - локальные (примеры: [cProfile](https://docs.python.org/3/library/profile.html#module-cProfile)/[line_profiler](https://github.com/pyutils/line_profiler), [tracemalloc](https://docs.python.org/3/library/tracemalloc.html)/[memory_profiler](https://github.com/pythonprofilers/memory_profiler))
  - удаленные (примеры: [pyspy](https://github.com/benfred/py-spy), [memray](https://github.com/bloomberg/memray))

По методу сборка метрик:
  - основанные на трассировке (детерминированные профилировщики) - записывают информацию о каждом вызове функции и о выполнении каждой строки кода (в случае профилировщиков линий, line profilers) (примеры: [cProfile](https://docs.python.org/3/library/profile.html#module-cProfile), [line_profiler](https://github.com/pyutils/line_profiler))
  - основанные на сэмплировании (статистические профилировщики) - сохраняют информацию о стеке вызовов через заданные промежутки времени (примеры: [pyinstrument](https://github.com/joerick/pyinstrument?tab=readme-ov-file), [pyspy](https://github.com/benfred/py-spy))

Может показаться, что профилирование на основе сэмплирования является менее точным, но, так как профилировщик снимает активность каждые несколько миллисекунд в течении продолжительного периода времени, то итоговая статистика будет корректной, кроме того такого рода профилировщики оказывают меньшее влияние на быстродействие самой программы.

По виду цели профилирования:
  - профилирование CPU (примеры: [pyspy](https://github.com/benfred/py-spy))
  - профилирование памяти (примеры: [memray](https://github.com/bloomberg/memray))
  - профилирование IO (диск, сеть)

## Задача

[cbor](https://github.com/agronholm/cbor2) ([MessagePack](https://github.com/msgpack/msgpack-python), [bson](https://pypi.org/project/bson-py/)):

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


## Smoke-профилирование

```python
import cbor2
import numpy as np
import numpy.typing as npt

from line_profiler import profile as lprofile
from memory_profiler import profile as mprofile

from serializers import arrays_hook, encode_arrays

MB = 1024 * 1024


def lst_as_arr(decoder, value):
    if value.get("lst"):
        return {"lst": np.array(value["lst"], dtype=np.float32)}
    return value


def generate_array(n: int) -> npt.NDArray[np.float32]:
    return np.random.random(n).astype(np.float32)


def pack_array(arr: np.ndarray) -> bytes:
    return cbor2.dumps({"arr": arr}, default=encode_arrays)


def pack_list(lst: list[float]) -> bytes:
    return cbor2.dumps({"lst": lst})


def unpack_list(blob: bytes) -> dict[str, npt.NDArray[np.float32]]:
    return cbor2.loads(blob, object_hook=lst_as_arr)


def unpack_array(blob: bytes) -> dict[str, npt.NDArray[np.float32]]:
    return cbor2.loads(blob, tag_hook=arrays_hook)


def main() -> None:
    n = 100 * MB // 4
    arr: npt.NDArray[np.float32] = generate_array(n)
    packed: bytes = pack_array(arr)
    lst: list[float] = arr.tolist()
    packed_lst: bytes = pack_list(lst)
    # del arr

    unpacked: dict[str, npt.NDArray[np.float32]] = unpack_array(packed)
    assert unpacked["arr"].dtype == np.float32
    assert unpacked["arr"].size == n
    # del packed
    # del unpacked

    unpacked_lst: dict[str, npt.NDArray[np.float32]] = unpack_list(packed_lst)
    assert unpacked_lst["lst"].dtype == np.float32
    assert unpacked_lst["lst"].size == n
    # del packed_lst
    # del unpacked_lst


if __name__ == "__main__":
    main()
```


Профилирование времени выполнения для массива размером 10MB:
```
Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    37                                           @lprofile
    38                                           def main() -> None:
    39         1       1286.0   1286.0      0.0      n = 10 * MB // 4
    40         1   61679435.0    6e+07      6.0      arr = generate_array(n)
    41         1   11086375.0    1e+07      1.1      packed = pack_array(arr)
    42         1   70455019.0    7e+07      6.9      lst = arr.tolist()
    43         1  306854311.0    3e+08     30.1      packed_lst = pack_list(lst)
    45                                           
    46         1   77537587.0    8e+07      7.6      unpacked = unpack_array(packed)
    47         1       3454.0   3454.0      0.0      assert unpacked["arr"].dtype == np.float32
    48         1       1257.0   1257.0      0.0      assert unpacked["arr"].size == n
    51                                           
    52         1  492499446.0    5e+08     48.3      unpacked_lst = unpack_list(packed_lst)
    53         1       8221.0   8221.0      0.0      assert unpacked_lst["lst"].dtype == np.float32
    54         1       2142.0   2142.0      0.0      assert unpacked_lst["lst"].size == n
```

Профилирование памяти для массива размером 10MB (backend="psutil"):
```
Line #    Mem usage    Increment  Occurrences   Line Contents
=============================================================
    37     34.5 MiB     34.5 MiB           1   @mprofile
    38                                         def main() -> None:
    39     34.5 MiB      0.0 MiB           1       n = 10 * MB // 4
    40     48.2 MiB     13.7 MiB           1       arr = generate_array(n)
    41     78.1 MiB     29.9 MiB           1       packed = pack_array(arr)
    42    158.2 MiB     80.2 MiB           1       lst = arr.tolist()
    43    180.9 MiB     22.7 MiB           1       packed_lst = pack_list(lst)
    45
    46    210.8 MiB     29.9 MiB           1       unpacked = unpack_array(packed)
    47    210.8 MiB      0.0 MiB           1       assert unpacked["arr"].dtype == np.float32
    48    210.8 MiB      0.0 MiB           1       assert unpacked["arr"].size == n
    51
    52    211.5 MiB      0.6 MiB           1       unpacked_lst = unpack_list(packed_lst)
    53    211.5 MiB      0.0 MiB           1       assert unpacked_lst["lst"].dtype == np.float32
    54    211.5 MiB      0.0 MiB           1       assert unpacked_lst["lst"].size == n
```

Профилирование памяти для массива размером 10MB (backend="tracemalloc"):
```
Line #    Mem usage    Increment  Occurrences   Line Contents
=============================================================
    37      0.0 MiB      0.0 MiB           1   @mprofile(backend="tracemalloc")
    38                                         def main() -> None:
    39      0.0 MiB      0.0 MiB           1       n = 10 * MB // 4
    40     10.0 MiB     10.0 MiB           1       arr = generate_array(n)
    41     20.0 MiB     10.0 MiB           1       packed = pack_array(arr)
    42    100.0 MiB     80.0 MiB           1       lst = arr.tolist()
    43    122.5 MiB     22.5 MiB           1       packed_lst = pack_list(lst)
    45                                         
    46    132.5 MiB     10.0 MiB           1       unpacked = unpack_array(packed)
    47    132.5 MiB     -0.0 MiB           1       assert unpacked["arr"].dtype == np.float32
    48    132.5 MiB      0.0 MiB           1       assert unpacked["arr"].size == n
    51                                         
    52    142.5 MiB     10.0 MiB           1       unpacked_lst = unpack_list(packed_lst)
    53    142.5 MiB     -0.0 MiB           1       assert unpacked_lst["lst"].dtype == np.float32
    54    142.5 MiB     -0.0 MiB           1       assert unpacked_lst["lst"].size == n
```

Профилирование времени выполнения для массива размером 100MB:
```
Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    37                                           @lprofile
    38                                           def main() -> None:
    39         1        937.0    937.0      0.0      n = 100 * MB // 4
    40         1  590029844.0    6e+08      1.3      arr = generate_array(n)
    41         1  113149187.0    1e+08      0.2      packed = pack_array(arr)
    42         1 1733905905.0    2e+09      3.7      lst = arr.tolist()
    43         1 3834665568.0    4e+09      8.3      packed_lst = pack_list(lst)
    45                                           
    46         1        3e+10    3e+10     74.8      unpacked = unpack_array(packed)
    47         1       3783.0   3783.0      0.0      assert unpacked["arr"].dtype == np.float32
    48         1       1009.0   1009.0      0.0      assert unpacked["arr"].size == n
    51                                           
    52         1 5383246536.0    5e+09     11.6      unpacked_lst = unpack_list(packed_lst)
    53         1      13624.0  13624.0      0.0      assert unpacked_lst["lst"].dtype == np.float32
    54         1       3247.0   3247.0      0.0      assert unpacked_lst["lst"].size == n
```

Профилирование памяти для массива размером 100MB (backend="psutil"):
```
Line #    Mem usage    Increment  Occurrences   Line Contents
=============================================================
    37     34.4 MiB     34.4 MiB           1   @mprofile
    38                                         def main() -> None:
    39     34.4 MiB      0.0 MiB           1       n = 100 * MB // 4
    40    138.2 MiB    103.8 MiB           1       arr = generate_array(n)
    41    238.2 MiB    100.0 MiB           1       packed = pack_array(arr)
    42   1241.4 MiB   1003.1 MiB           1       lst = arr.tolist()
    43   1465.2 MiB    223.8 MiB           1       packed_lst = pack_list(lst)
    45                                         
    46   1553.2 MiB     88.0 MiB           1       unpacked = unpack_array(packed)
    47   1553.2 MiB      0.0 MiB           1       assert unpacked["arr"].dtype == np.float32
    48   1553.2 MiB      0.0 MiB           1       assert unpacked["arr"].size == n
    51                                         
    52   1685.9 MiB    132.7 MiB           1       unpacked_lst = unpack_list(packed_lst)
    53   1685.9 MiB      0.0 MiB           1       assert unpacked_lst["lst"].dtype == np.float32
    54   1685.9 MiB      0.0 MiB           1       assert unpacked_lst["lst"].size == n
```

Профилирование памяти для массива размером 100MB (backend="tracemalloc"):
```
Line #    Mem usage    Increment  Occurrences   Line Contents
=============================================================
    37      0.0 MiB      0.0 MiB           1   @mprofile(backend="tracemalloc")
    38                                         def main() -> None:
    39      0.0 MiB      0.0 MiB           1       n = 100 * MB // 4
    40    100.0 MiB    100.0 MiB           1       arr = generate_array(n)
    41    200.0 MiB    100.0 MiB           1       packed = pack_array(arr)
    42   1000.0 MiB    800.0 MiB           1       lst = arr.tolist()
    43   1225.0 MiB    225.0 MiB           1       packed_lst = pack_list(lst)
    45                                         
    46   1325.0 MiB    100.0 MiB           1       unpacked = unpack_array(packed)
    47   1325.0 MiB     -0.0 MiB           1       assert unpacked["arr"].dtype == np.float32
    48   1325.0 MiB      0.0 MiB           1       assert unpacked["arr"].size == n
    51                                         
    52   1425.0 MiB    100.0 MiB           1       unpacked_lst = unpack_list(packed_lst)
    53   1425.0 MiB     -0.0 MiB           1       assert unpacked_lst["lst"].dtype == np.float32
    54   1425.0 MiB     -0.0 MiB           1       assert unpacked_lst["lst"].size == n
```

## Бенчмарки

Прежде чем начинать что-то оптимизировать надо написать бенчмарки (тесты производительности), например, с помощью:
  - [pytest-benchmark](https://github.com/ionelmc/pytest-benchmark) - для оценки производительности CPU-bound задач
  - [pytest-pystack](https://github.com/bloomberg/pytest-pystack) - для контроля времени выполнения функций
  - [pytest-memray](https://github.com/bloomberg/pytest-memray) - для оценки потребления памяти

Конфигурирование:

```ini
[tool.pytest.ini_options]
python_files = ["test_*.py", "bench_*.py"]
python_functions = ["test_*", "bench_*"]
addopts = "--benchmark-skip --benchmark-columns=mean,rounds --benchmark-min-rounds=5"
pystack_threshold=5
pystack_output_file="./pystack.log"
pystack_args="--native"
```

Пример:

```python
# ...

MB = 1024 * 1024
N = 40
N_ITEMS = N * MB // np.dtype(np.float32).itemsize


@pytest.fixture
def random_array() -> Array1D[np.float32]:
    return np.random.random(N_ITEMS).astype(np.float32)


@pytest.fixture
def random_list(random_array: Array1D[np.float32]) -> list[float]:
    return random_array.tolist()


@pytest.fixture
def packed_list(random_list: list[float) -> bytes:
    return cbor2.dumps({"values": random_list})


@pytest.fixture
def packed_array(random_array: Array1D[np.float32]) -> bytes:
    return cbor2.dumps({"values": random_array}, default=encode_arrays)


def object_hook(decoder, value) -> Any:
    if value.get("values"):
        values = np.array(value["values"], dtype=np.float32)
        return {"values": values}
    return value


def unpack_list(blob: bytes) -> dict[str, Array1D[np.float32]]:
    return cbor2.loads(blob, object_hook=object_hook)


def unpack_array(blob: bytes) -> dict[str, Array1D[np.float32]]:
    return cbor2.loads(blob, tag_hook=arrays_hook)


def unpack_array_fixed_loads(blob: bytes) -> dict[str, Array1D[np.float32]]:
    return loads(blob)


@pytest.mark.benchmark(group="Deserialize cbor-object to numpy array")
@pytest.mark.limit_memory(f"{2 * N + 5} MB")
def bench_unpack_list(benchmark, packed_list):
    result = benchmark(unpack_list, packed_list)
    assert result["values"].size == N
    assert result["values"].dtype is np.dtype(np.float32)


@pytest.mark.benchmark(group="Deserialize cbor-object to numpy array")
@pytest.mark.limit_memory(f"{N + 5} MB")
def bench_unpack_array(benchmark, packed_array):
    result = benchmark(unpack_array, packed_array)
    assert result["values"].size == N
    assert result["values"].dtype is np.dtype(np.float32)


@pytest.mark.benchmark(group="Deserialize cbor-object to numpy array")
@pytest.mark.limit_memory(f"{N + 5} MB")
def bench_unpack_array_fixed_loads(benchmark, packed_array):
    result = benchmark(unpack_array_fixed_loads, packed_array)
    assert result["values"].size == N
    assert result["values"].dtype is np.dtype(np.float32)
```

Запуск бенчмарков:

```sh
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
uv run pytest --benchmark-only --memray tests
```

```
============================================================================ test session starts ============================================================================
platform linux -- Python 3.11.10, pytest-8.3.4, pluggy-1.5.0
benchmark: 5.1.0 (defaults: timer=time.perf_counter disable_gc=False min_rounds=2 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /home/Dmitry.Sorokin/Projects/experimets/profiling
configfile: pyproject.toml
plugins: benchmark-5.1.0, memray-1.7.0, pystack-1.0.2
collected 3 items                                                                                                                                                           

tests/bench_cbor.py M

**** PYSTACK  -- bench_unpack_array ***
...

Traceback for thread 3679897 (pytest) [Has the GIL] (most recent call last):
    ...
    (Python) File "/home/Dmitry.Sorokin/Projects/experimets/profiling/tests/bench_cbor.py", line 44, in unpack_array
        return cbor2.loads(blob, tag_hook=arrays_hook)
    (C) File "???", line 0, in cfunction_call (/home/Dmitry.Sorokin/.local/share/uv/python/cpython-3.11.10-linux-x86_64-gnu/lib/libpython3.11.so.1.0)
    (C) File "source/module.c", line 367, in CBOR2_loads (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/_cbor2.cpython-311-x86_64-linux-gnu.so)
    (C) File "source/module.c", line 318, in CBOR2_load (inlined) (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/_cbor2.cpython-311-x86_64-linux-gnu.so)
    (C) File "source/decoder.c", line 2059, in CBORDecoder_decode (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/_cbor2.cpython-311-x86_64-linux-gnu.so)
    (C) File "source/decoder.c", line 2039, in decode (inlined) (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/_cbor2.cpython-311-x86_64-linux-gnu.so)
    (C) File "source/decoder.c", line 1106, in decode_map (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/_cbor2.cpython-311-x86_64-linux-gnu.so)
    (C) File "source/decoder.c", line 2040, in decode.constprop.1 (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/_cbor2.cpython-311-x86_64-linux-gnu.so)
    (C) File "source/decoder.c", line 1182, in decode_semantic (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/_cbor2.cpython-311-x86_64-linux-gnu.so)
    (C) File "source/decoder.c", line 2036, in decode.constprop.1 (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/_cbor2.cpython-311-x86_64-linux-gnu.so)
    (C) File "source/decoder.c", line 709, in decode_bytestring (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/_cbor2.cpython-311-x86_64-linux-gnu.so)
    (C) File "source/decoder.c", line 613, in decode_definite_long_bytestring (inlined) (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/_cbor2.cpython-311-x86_64-linux-gnu.so)
    (C) File "???", line 0, in PyByteArray_Concat (/home/Dmitry.Sorokin/.local/share/uv/python/cpython-3.11.10-linux-x86_64-gnu/lib/libpython3.11.so.1.0)
    (C) File "../sysdeps/x86_64/multiarch/memmove-vec-unaligned-erms.S", line 536, in __memmove_avx_unaligned_erms (/usr/lib/x86_64-linux-gnu/libc-2.28.so)

**** PYSTACK  ***

M.                                                                                                                                               [100%]

================================================================================= FAILURES ==================================================================================
_____________________________________________________________________________ bench_unpack_list _____________________________________________________________________________
Test was limited to 85.0MiB but allocated 448.0MiB
----------------------------------------------------------------------------- memray-max-memory -----------------------------------------------------------------------------
List of allocations:
    - 40.0MiB allocated here:
        object_hook:/home/Dmitry.Sorokin/Projects/experimets/profiling/tests/bench_cbor.py:34
        ...
    - 2.0MiB allocated here:
        unpack_list:/home/Dmitry.Sorokin/Projects/experimets/profiling/tests/bench_cbor.py:40
        ...
    - 1.2KiB allocated here:
        _raw:/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/pytest_benchmark/fixture.py:180
        ...
    - 1.0MiB allocated here:
        unpack_list:/home/Dmitry.Sorokin/Projects/experimets/profiling/tests/bench_cbor.py:40
        ...
    - 405.0MiB allocated here:
        unpack_list:/home/Dmitry.Sorokin/Projects/experimets/profiling/tests/bench_cbor.py:40
        ...
    - 1.1KiB allocated here:
        __call__:/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/pytest_benchmark/fixture.py:156
    - 586.0B allocated here:
        _calibrate_timer:/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/pytest_benchmark/fixture.py:318
        ...
____________________________________________________________________________ bench_unpack_array _____________________________________________________________________________
Test was limited to 45.0MiB but allocated 80.0MiB
----------------------------------------------------------------------------- memray-max-memory -----------------------------------------------------------------------------
List of allocations:
    - 852.0B allocated here:
        _feed:/home/Dmitry.Sorokin/.local/share/uv/python/cpython-3.11.10-linux-x86_64-gnu/lib/python3.11/multiprocessing/queues.py:233
        ...
    - 670.0B allocated here:
        wait:/home/Dmitry.Sorokin/.local/share/uv/python/cpython-3.11.10-linux-x86_64-gnu/lib/python3.11/threading.py:337
        ...
    - 80.0MiB allocated here:
        unpack_array:/home/Dmitry.Sorokin/Projects/experimets/profiling/tests/bench_cbor.py:44
        ...
    - 32.0B allocated here:
        wait:/home/Dmitry.Sorokin/.local/share/uv/python/cpython-3.11.10-linux-x86_64-gnu/lib/python3.11/threading.py:320
        ...

=============================================================================== MEMRAY REPORT ===============================================================================
Allocation results for tests/bench_cbor.py::bench_unpack_list at the high watermark

	📦 Total memory allocated: 448.0MiB
	📏 Total allocations: 11
	📊 Histogram of allocation sizes: |█ ▂▂▄|
	🥇 Biggest allocating functions:
		- unpack_list:/home/Dmitry.Sorokin/Projects/experimets/profiling/tests/bench_cbor.py:40 -> 405.0MiB
		- object_hook:/home/Dmitry.Sorokin/Projects/experimets/profiling/tests/bench_cbor.py:34 -> 40.0MiB
		- unpack_list:/home/Dmitry.Sorokin/Projects/experimets/profiling/tests/bench_cbor.py:40 -> 2.0MiB
		- unpack_list:/home/Dmitry.Sorokin/Projects/experimets/profiling/tests/bench_cbor.py:40 -> 1.0MiB


Allocation results for tests/bench_cbor.py::bench_unpack_array at the high watermark

	📦 Total memory allocated: 80.0MiB
	📏 Total allocations: 5
	📊 Histogram of allocation sizes: |▂█   |
	🥇 Biggest allocating functions:
		- unpack_array:/home/Dmitry.Sorokin/Projects/experimets/profiling/tests/bench_cbor.py:44 -> 80.0MiB
		- _feed:/home/Dmitry.Sorokin/.local/share/uv/python/cpython-3.11.10-linux-x86_64-gnu/lib/python3.11/multiprocessing/queues.py:233 -> 852.0B
		- wait:/home/Dmitry.Sorokin/.local/share/uv/python/cpython-3.11.10-linux-x86_64-gnu/lib/python3.11/threading.py:337 -> 670.0B
		- wait:/home/Dmitry.Sorokin/.local/share/uv/python/cpython-3.11.10-linux-x86_64-gnu/lib/python3.11/threading.py:320 -> 32.0B


Allocation results for tests/bench_cbor.py::bench_unpack_array_fixed_loads at the high watermark

	📦 Total memory allocated: 40.0MiB
	📏 Total allocations: 7
	📊 Histogram of allocation sizes: |█    |
	🥇 Biggest allocating functions:
		- read:/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/cbor2/_decoder.py:200 -> 40.0MiB
		- _decode:/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/cbor2/_decoder.py:221 -> 1.1KiB
		- _decode:/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/cbor2/_decoder.py:221 -> 626.0B
		- update:/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/pytest_benchmark/stats.py:45 -> 608.0B



- benchmark 'Deserialize cbor-object to numpy array': 3 tests -
Name (time in ms)                        Mean            Rounds
---------------------------------------------------------------
bench_unpack_array_fixed_loads        14.6016 (1.0)          67
bench_unpack_list                    932.0782 (63.83)         2
bench_unpack_array                 2,330.7831 (159.62)        2
---------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
========================================================================== short test summary info ==========================================================================
MEMORY PROBLEMS tests/bench_cbor.py::bench_unpack_list
MEMORY PROBLEMS tests/bench_cbor.py::bench_unpack_array
======================================================================= 2 failed, 1 passed in 18.57s ========================================================================
```

В случае `unpack_array` мы ждем завершения декодирования байтовой строки [decode_definite_long_bytestring](https://github.com/agronholm/cbor2/blob/master/source/decoder.c#L595):

```c
static PyObject *
decode_definite_long_bytestring(CBORDecoderObject *self, Py_ssize_t length)
{
    PyObject *buffer = NULL;
    Py_ssize_t left = length;
    while (left) {
        Py_ssize_t chunk_length = left <= 65536 ? left : 65536;
        PyObject *chunk = fp_read_object(self, chunk_length);
        if (!chunk) {
            goto error;
        }

        if (!PyBytes_CheckExact(chunk)) {
            Py_DECREF(chunk);
            goto error;
        }

        if (buffer) {
            PyObject *new_buffer = PyByteArray_Concat(buffer, chunk);
            Py_DECREF(chunk);
            if (!new_buffer)
                goto error;

            if (new_buffer != buffer) {
                Py_DECREF(buffer);
                buffer = new_buffer;
            }
        } else {
            buffer = PyByteArray_FromObject(chunk);
            Py_DECREF(chunk);
            if (!buffer)
                goto error;
        }
        left -= chunk_length;
    }

    PyObject *ret = NULL;
    if (buffer) {
        ret = PyBytes_FromObject(buffer);
        Py_DECREF(buffer);

        if (ret && string_namespace_add(self, ret, length) == -1) {
            Py_DECREF(ret);
            ret = NULL;
        }
    }
    return ret;
error:
    Py_XDECREF(buffer);
    return NULL;
}
```


## Профилирование памяти

В CPython существует [три домена для аллокации](https://docs.python.org/3/c-api/memory.html#allocator-domains):

> - Raw domain: intended for allocating memory for general-purpose memory buffers where the allocation must go to the system allocator or where the allocator can operate without the GIL. The memory is requested directly from the system. See Raw Memory Interface.
>
> - “Mem” domain: intended for allocating memory for Python buffers and general-purpose memory buffers where the allocation must be performed with the GIL held. The memory is taken from the Python private heap. See Memory Interface.
>
> - Object domain: intended for allocating memory for Python objects. The memory is taken from the Python private heap. See Object allocators.

[tracemalloc](https://github.com/python/cpython/blob/7907203bc07387ff2d8e2bcc15d7b8dd3a1ce687/Python/tracemalloc.c#L793) ([PEP 454](https://peps.python.org/pep-0454/)) - [Victor Stinner](https://github.com/vstinner), Maintain Python upstream (python.org) and downstream (RHEL, Fedora) for Red Hat:

```c
int
_PyTraceMalloc_Start(int max_nframe)
{
    // ...

    PyMemAllocatorEx alloc;
    alloc.malloc = tracemalloc_raw_malloc;
    alloc.calloc = tracemalloc_raw_calloc;
    alloc.realloc = tracemalloc_raw_realloc;
    alloc.free = tracemalloc_free;

    alloc.ctx = &allocators.raw;
    PyMem_GetAllocator(PYMEM_DOMAIN_RAW, &allocators.raw);
    PyMem_SetAllocator(PYMEM_DOMAIN_RAW, &alloc);

    alloc.malloc = tracemalloc_malloc_gil;
    alloc.calloc = tracemalloc_calloc_gil;
    alloc.realloc = tracemalloc_realloc_gil;
    alloc.free = tracemalloc_free;

    alloc.ctx = &allocators.mem;
    PyMem_GetAllocator(PYMEM_DOMAIN_MEM, &allocators.mem);
    PyMem_SetAllocator(PYMEM_DOMAIN_MEM, &alloc);

    alloc.ctx = &allocators.obj;
    PyMem_GetAllocator(PYMEM_DOMAIN_OBJ, &allocators.obj);
    PyMem_SetAllocator(PYMEM_DOMAIN_OBJ, &alloc);

    // ...
}
```

[memray](https://github.com/bloomberg/memray/blob/b9541903c48e01b29e0a4d1cac98ca881fbacbf6/src/memray/_memray/tracking_api.cpp#L544) - [Pablo Galindo Salgado](https://github.com/pablogsal), Python core developer, Steering Council member and release manager of Python 3.10 and 3.11:

```c
Tracker::Tracker(
        std::unique_ptr<RecordWriter> record_writer,
        bool native_traces,
        unsigned int memory_interval,
        bool follow_fork,
        bool trace_python_allocators)
: d_writer(std::move(record_writer))
, d_unwind_native_frames(native_traces)
, d_memory_interval(memory_interval)
, d_follow_fork(follow_fork)
, d_trace_python_allocators(trace_python_allocators)
{
    // ...

    PythonStackTracker::s_native_tracking_enabled = native_traces;
    PythonStackTracker::installProfileHooks();
    if (d_trace_python_allocators) {
        registerPymallocHooks();
    }
    d_background_thread = std::make_unique<BackgroundThread>(d_writer, memory_interval);
    d_background_thread->start();

    d_patcher.overwrite_symbols();
}

// ...
bool
Tracker::BackgroundThread::captureMemorySnapshot()
{
    auto now = timeElapsed();
    size_t rss = getRSS();
    if (rss == 0) {
        std::cerr << "Failed to detect RSS, deactivating tracking" << std::endl;
        Tracker::deactivate();
        return false;
    }

    std::lock_guard<std::mutex> lock(*s_mutex);
    if (!d_writer->writeRecord(MemoryRecord{now, rss})) {
        std::cerr << "Failed to write output, deactivating tracking" << std::endl;
        Tracker::deactivate();
        return false;
    }

    return true;
}

// ...
void
Tracker::registerPymallocHooks() const noexcept
{
    assert(d_trace_python_allocators);
    PyMemAllocatorEx alloc;

    PyMem_GetAllocator(PYMEM_DOMAIN_RAW, &alloc);
    if (alloc.free == &intercept::pymalloc_free) {
        // Nothing to do; our hooks are already installed.
        return;
    }

    alloc.malloc = intercept::pymalloc_malloc;
    alloc.calloc = intercept::pymalloc_calloc;
    alloc.realloc = intercept::pymalloc_realloc;
    alloc.free = intercept::pymalloc_free;
    PyMem_GetAllocator(PYMEM_DOMAIN_RAW, &s_orig_pymalloc_allocators.raw);
    PyMem_GetAllocator(PYMEM_DOMAIN_MEM, &s_orig_pymalloc_allocators.mem);
    PyMem_GetAllocator(PYMEM_DOMAIN_OBJ, &s_orig_pymalloc_allocators.obj);
    alloc.ctx = &s_orig_pymalloc_allocators.raw;
    PyMem_SetAllocator(PYMEM_DOMAIN_RAW, &alloc);
    alloc.ctx = &s_orig_pymalloc_allocators.mem;
    PyMem_SetAllocator(PYMEM_DOMAIN_MEM, &alloc);
    alloc.ctx = &s_orig_pymalloc_allocators.obj;
    PyMem_SetAllocator(PYMEM_DOMAIN_OBJ, &alloc);
}
```

## Профилирование IO

```python
import math

import h5py
import numpy as np
import numpy.typing as npt
import pytest

DATA_H5_FILE = "data.h5"
N = 1_000_000
M = 1_000
MB = 1024 ** 2


@pytest.fixture(scope="session")
def create_raw_h5() -> None:
    data = np.empty((N, M), order="C", dtype=np.float32)
    np.random.default_rng().standard_normal(size=(N, M), dtype=np.float32, out=data)

    with h5py.File(DATA_H5_FILE, mode="w") as h5file:
        h5file.create_dataset(
            "data",
            shape=(N, M),
            dtype=np.float32,
            chunks=(N, 10),
            data=data,
        )


def read_h5_1mb_chunk() -> npt.NDArray[np.float32]:
    with h5py.File(DATA_H5_FILE, rdcc_nbytes=MB) as h5file:
        dset = h5file["data"]
        data = dset[:]
    return data


def read_h5_40mb_chunk() -> npt.NDArray[np.float32]:
    with h5py.File(DATA_H5_FILE) as h5file:
        dset = h5file["data"]
        chunk_size_mb = math.ceil(dset.chunks[0] * dset.chunks[1] * 4 / 1024 / 1024)
    with h5py.File(DATA_H5_FILE, rdcc_nbytes=MB * chunk_size_mb) as h5file:
        dset = h5file["data"]
        data = dset[:]
    return data


@pytest.mark.benchmark(group="Read raw h5-file")
def bench_read_h5_1mb_chunk(benchmark, create_raw_h5):
    benchmark(read_h5_1mb_chunk)


@pytest.mark.benchmark(group="Read raw h5-file")
def bench_read_h5_40mb_chunk(benchmark, create_raw_h5):
    benchmark(read_h5)
```

```
============================================================================ test session starts ============================================================================
platform linux -- Python 3.11.10, pytest-8.3.4, pluggy-1.5.0
benchmark: 5.1.0 (defaults: timer=time.perf_counter disable_gc=False min_rounds=2 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /home/Dmitry.Sorokin/Projects/experimets/profiling
configfile: pyproject.toml
plugins: benchmark-5.1.0, memray-1.7.0, pystack-1.0.2
collected 2 items                                                                                                                                                           

bench_hdf5_slow_reads.py 

**** PYSTACK  -- bench_read_h5_1mb_chunk ***
...

Traceback for thread 1338569 (pytest) [] (most recent call last):
    ...
    (Python) File "/home/Dmitry.Sorokin/Projects/experimets/profiling/bench_hdf5_slow_reads.py", line 30, in read_h5_1mb_chunk
        data = dset[:]
    (C) File "???", line 0, in slot_mp_subscript (/home/Dmitry.Sorokin/.local/share/uv/python/cpython-3.11.10-linux-x86_64-gnu/lib/libpython3.11.so.1.0)
    (C) File "/project/h5py/_objects.c", line 6326, in __pyx_pw_4h5py_8_objects_9with_phil_1wrapper (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py/_objects.cpython-311-x86_64-linux-gnu.so)
    (C) File "/project/h5py/_objects.c", line 6415, in __pyx_pf_4h5py_8_objects_9with_phil_wrapper (inlined) (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py/_objects.cpython-311-x86_64-linux-gnu.so)
    (C) File "/project/h5py/_objects.c", line 14290, in __Pyx_PyObject_Call (inlined) (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py/_objects.cpython-311-x86_64-linux-gnu.so)
    (Python) File "/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py/_hl/dataset.py", line 781, in __getitem__
        return self._fast_reader.read(args)
    (C) File "/project/h5py/_selector.c", line 11741, in __pyx_pw_4h5py_9_selector_6Reader_3read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py/_selector.cpython-311-x86_64-linux-gnu.so)
    (C) File "/project/h5py/_selector.c", line 11944, in __pyx_pf_4h5py_9_selector_6Reader_2read (inlined) (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py/_selector.cpython-311-x86_64-linux-gnu.so)
    (C) File "/project/h5py/defs.c", line 11148, in __pyx_f_4h5py_4defs_H5Dread (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py/defs.cpython-311-x86_64-linux-gnu.so)
    (C) File "???", line 0, in H5Dread (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5D__read_api_common.constprop.0 (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5VL_dataset_read_direct (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5VL__native_dataset_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5D__read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5D__chunk_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5D__select_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5D__select_io (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5D__contig_readvv (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5VM_opvv (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5D__contig_readvv_sieve_cb (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5F_shared_block_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5PB_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5F__accum_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5FD_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5FD__sec2_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "../sysdeps/unix/sysv/linux/pread64.c", line 27, in __pread64 (/usr/lib/x86_64-linux-gnu/libpthread-2.28.so)
    (C) File "../sysdeps/unix/sysv/linux/pread64.c", line 29, in __libc_pread64 (inlined) (/usr/lib/x86_64-linux-gnu/libpthread-2.28.so)

**** PYSTACK  ***

.

**** PYSTACK  -- bench_read_h5_40mb_chunk ***
...

Traceback for thread 1338569 (pytest) [] (most recent call last):
    ...
    (Python) File "/home/Dmitry.Sorokin/Projects/experimets/profiling/bench_hdf5_slow_reads.py", line 40, in read_h5_40mb_chunk
        data = dset[:]
    (C) File "???", line 0, in slot_mp_subscript (/home/Dmitry.Sorokin/.local/share/uv/python/cpython-3.11.10-linux-x86_64-gnu/lib/libpython3.11.so.1.0)
    (C) File "/project/h5py/_objects.c", line 6326, in __pyx_pw_4h5py_8_objects_9with_phil_1wrapper (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py/_objects.cpython-311-x86_64-linux-gnu.so)
    (C) File "/project/h5py/_objects.c", line 6415, in __pyx_pf_4h5py_8_objects_9with_phil_wrapper (inlined) (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py/_objects.cpython-311-x86_64-linux-gnu.so)
    (C) File "/project/h5py/_objects.c", line 14290, in __Pyx_PyObject_Call (inlined) (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py/_objects.cpython-311-x86_64-linux-gnu.so)
    (Python) File "/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py/_hl/dataset.py", line 781, in __getitem__
        return self._fast_reader.read(args)
    (C) File "/project/h5py/_selector.c", line 11741, in __pyx_pw_4h5py_9_selector_6Reader_3read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py/_selector.cpython-311-x86_64-linux-gnu.so)
    (C) File "/project/h5py/_selector.c", line 11944, in __pyx_pf_4h5py_9_selector_6Reader_2read (inlined) (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py/_selector.cpython-311-x86_64-linux-gnu.so)
    (C) File "/project/h5py/defs.c", line 11148, in __pyx_f_4h5py_4defs_H5Dread (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py/defs.cpython-311-x86_64-linux-gnu.so)
    (C) File "???", line 0, in H5Dread (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5D__read_api_common.constprop.0 (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5VL_dataset_read_direct (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5VL__native_dataset_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5D__read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5D__chunk_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5D__chunk_lock.constprop.0 (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5F_shared_block_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5PB_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5F__accum_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5FD_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "???", line 0, in H5FD__sec2_read (/home/Dmitry.Sorokin/Projects/experimets/profiling/.venv/lib/python3.11/site-packages/h5py.libs/libhdf5-a6e30693.so.310.4.0)
    (C) File "../sysdeps/unix/sysv/linux/pread64.c", line 27, in __pread64 (/usr/lib/x86_64-linux-gnu/libpthread-2.28.so)
    (C) File "../sysdeps/unix/sysv/linux/pread64.c", line 29, in __libc_pread64 (inlined) (/usr/lib/x86_64-linux-gnu/libpthread-2.28.so)

**** PYSTACK  ***

.                                                                                                                                           [100%]


-------------------------- benchmark 'Read raw h5-file': 2 tests --------------------------
Name (time in s)                Min               Mean                Max            Rounds
-------------------------------------------------------------------------------------------
bench_read_h5_40mb_chunk     5.5408 (1.0)       5.7123 (1.0)       5.8838 (1.0)           2
bench_read_h5_1mb_chunk     45.3277 (8.18)     46.1399 (8.08)     46.9522 (7.98)          2
-------------------------------------------------------------------------------------------
======================================================================= 2 passed in 227.29s (0:03:47) =======================================================================
```

[strace](https://www.strace.io):
```
. venv/bin/activate
strace -e trace=pread64 -o pread_trace.txt python examples/hdf5_ex.py
```

`read_h5_1mb_chunk`:
```
...
pread64(4, "A\345m\275\10\7\363?1l\235=\"\26)?\32\323\314\276q-}?\0252I?\327\3315?"..., 40, 17696) = 40
pread64(4, "0\367\307\275\312\222<?\260f\255\276\237\373\301=~\321\261\277\270\333\37?\231\"\16\277Q\0013?"..., 40, 17736) = 40
pread64(4, "\2734\323>\tM\241?\272\226A\274\332\323@\277\277*\205\277'd\345\276aC\1@\16WR>"..., 40, 17776) = 40
pread64(4, "\200\32\216>\235\236\232\276@\350\342\277\256\267\205\277\1773=?F\301\17?\373q\325?\322\265\233>"..., 40, 17816) = 40
pread64(4, "\253'\364\276\305\220(>,4\342\275\334\7\235?\331e\20\300\234\343\327\277\334\345\"?\377\332\r\277"..., 40, 17856) = 40
...
```

`read_h5_40mb_chunk`:
```
...
pread64(4, "\351\245\224\277\213\362~\276)q\363?.\247C\277Z\314\21?\2239\257\277\334\236I?^\203\24\276"..., 40000000, 4016) = 40000000
...
pread64(4, "\325\4\220\276\35/\364?\203\270\241\277\3532Y\276\212\236\5?\356\f\244?\266\205\330>\251\16\236\277"..., 40000000, 40004016) = 40000000
...
pread64(4, ".e\24\277+\347\21\277\324\364\5\300\217\27\353\276\"\333^?\254\266J?\277\34\207\276\34\256\326\277"..., 40000000, 80004016) = 40000000
...
```

GitHub Issue: [Confusion with rdcc_nbytes](https://github.com/h5py/h5py/issues/2526)


## Очистка кэша перед тестами

Linux:

```
sync; echo 3 > /proc/sys/vm/drop_caches
```

Mac OS:

```
sync && sudo purge
```

Windows:

```
rammap.exe -Et
```


## Влияние сборщика мусора на производительность

[Как сократить время ответа в 2 раза, добавив одну строку кода.](https://habr.com/ru/companies/okko/articles/853406/)

> Что всё-таки происходит? У питониста всегда два главных виновника — GIL и сборка мусора. У нас синхронные эндпоинты на Flask, в приложении нет большого количества тредов. Неужели блокировка главного треда, где записывается спан, занимает столько времени из-за GIL и выполнения кода в другом треде? Мы посчитали это маловероятным, ведь в Python по умолчанию переключение между тредами занимает 5мс, а «дырка» у нас аж на 50 мс. Поэтому для начала решили проверить гипотезу о сборщике мусора.

```python
from dataclasses import dataclass


@dataclass
class Film:
    film_id: int
    weight: float
    actors: list[str]


def get_films_from_db(films_count: int) -> list[Film]:
    films_list = [
        Film(
            film_id=idx,
            weight=0.0,
            actors=["Tom Hanks", "Brad Pitt", "Leonardo DiCaprio"],
        )
        for idx in range(films_count)
    ]
    return films_list


def main() -> None:
    films_list = get_films_from_db(films_count=1_000_000)


if __name__ == "__main__":
    main()
```

```
austinp -i 10ms -g python examples/okko.py
```

```
...
🐍 Python version: 3.11.10

P3022646;T0:3022646;native@40107a:_start:42;native@728fa72e009b:__libc_start_main:235;native@728fa78beb73:Py_BytesMain:67;native@728fa78be673:Py_RunMain:2035;native@728fa789f21c:_PyRun_AnyFileObject:60;native@728fa789ec67:_PyRun_SimpleFileObject:327;native@728fa789d524:run_mod:148;native@728fa7856215:PyEval_EvalCode:549;/home/Dmitry.Sorokin/Projects/experimets/profiling/examples/okko.py:<module>:32;/home/Dmitry.Sorokin/Projects/experimets/profiling/examples/okko.py:main:24;/home/Dmitry.Sorokin/Projects/experimets/profiling/examples/okko.py:get_films_from_db:12;/home/Dmitry.Sorokin/Projects/experimets/profiling/examples/okko.py:get_films_from_db.<locals>.<listcomp>:13;native@728fa775646d:_PyObject_MakeTpCall:125;native@728fa77c3495:type_call:69;native@728fa77bfde8:object_new:72;native@728fa77c3179:PyType_GenericAlloc:9;native@728fa77c3157:_PyType_AllocNoTrack:199;native@728fa78c14f3:_PyObject_GC_Link:211;native@728fa78c0b93:gc_collect_main:4467;:GC: 84

...

P3022646;T0:3022646;native@40107a:_start:42;native@728fa72e009b:__libc_start_main:235;native@728fa78beb73:Py_BytesMain:67;native@728fa78be214:Py_RunMain:144;native@728fa78981b0:Py_FinalizeEx:144;native@728fa78954d2:finalize_modules:690;native@728fa78c1136:_PyGC_CollectNoFail:54;native@728fa78c03bc:gc_collect_main:0;native@728fa78bf076:visit_decref:0;:GC: 10226

# duration: 1375391
# gc: 572082

Statistics
⌛ Sampling duration : 1.38 s
🗑️  Garbage collector : 0.57 s (41.59 %)
⏱️  Frame sampling (min/avg/max) : 1015/2591/4119 μs
🐢 Long sampling rate : 0/108 (0.00 %) samples took longer than the sampling interval to collect
💀 Error rate : 0/108 (0.00 %) invalid samples
```

Изменим пороги у GC:

```python
if __name__ == "__main__":
    import gc
    gc.set_threshold(10_000, 50, 20)
    main()
```

```
...
Statistics
⌛ Sampling duration : 0.95 s
🗑️  Garbage collector : 0.12 s (12.90 %)
⏱️  Frame sampling (min/avg/max) : 1260/2703/11045 μs
🐢 Long sampling rate : 1/74 (1.35 %) samples took longer than the sampling interval to collect
💀 Error rate : 0/74 (0.00 %) invalid samples
```

Если GC отключить:

```
Statistics
⌛ Sampling duration : 0.84 s
🗑️  Garbage collector : 0.01 s (1.21 %)
⏱️  Frame sampling (min/avg/max) : 1257/3165/16468 μs
🐢 Long sampling rate : 1/63 (1.59 %) samples took longer than the sampling interval to collect
💀 Error rate : 0/63 (0.00 %) invalid samples
```

В py-spy была попытка добавить учет [GC](https://github.com/benfred/py-spy/pull/515).

## Профилирование основанное на трассировке

### [sys.settrace](https://docs.python.org/3/library/sys.html#sys.settrace) и [sys.setprofile](https://docs.python.org/3/library/sys.html#sys.setprofile) (< 3.12)

[Guido van Rossum](https://gvanrossum.github.io/) (автор более современной версии [Fred Drake](https://github.com/freddrake)).

[sys.settrace](https://docs.python.org/3/library/sys.html#sys.settrace) позволяет указать функцию (callback), которая будет вызываться виртуальной машиной CPython каждый раз при наступлении одного из следующих событий:

  - вызове и завершении работы функции
  - выполнении строки кода
  - возбуждении исключения
  - выполнении одной инструкции байткода

Функция обратного вызова (callback) принимает три аргумента:

  - текуший стек-фрейм (frame)
  - строковое название события (event): call, return, line, exception, opcode
  - значение аргумента специфичное для произошедшего события (arg):
    - при выходе из функции (return) - значение, которое будет возвращено из функции
    - в случае возбуждения исключения (exception) - кортеж значений (exception, value, traceback)

Пример:

```python
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path
from types import FrameType
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from _typeshed import TraceFunction


def tracer(frame: FrameType, event: str, arg: Any) -> Optional[TraceFunction]:
    # frame.f_trace_opcodes = True
    co = frame.f_code
    func_name = co.co_name
    line_no = frame.f_lineno
    filename = os.path.basename(co.co_filename)
    indent = " " * len(traceback.extract_stack(frame))
    match event:
        case "call":
            print(f"{indent}Calling {func_name}() on line {line_no} of {filename}")
        case "line":
            print(f"{indent}Executing line {line_no} in func {func_name}")
        case "return":
            print(f"{indent}{func_name}() => {arg}")
        case "exception":
            exc_type, exc_value, _ = arg
            exc_name = exc_type.__name__
            print(
                f'{indent}Tracing exception: {exc_name} "{exc_value}" on line {line_no} of {func_name}'
            )
    return tracer


def foo(n):
    result = 0
    for _ in range(n):
        result += 1
    return result


def bar(n):
    return foo(n)


def baz(n):
    return bar(n)


def main() -> None:
    sys.settrace(tracer)
    baz(5)
    sys.settrace(None)


if __name__ == "__main__":
    main()
```

```
   Calling baz() on line 47 of settrace_ex.py
   Executing line 48 in func baz
    Calling bar() on line 43 of settrace_ex.py
    Executing line 44 in func bar
     Calling foo() on line 36 of settrace_ex.py
     Executing line 37 in func foo
     Executing line 38 in func foo
     Executing line 39 in func foo
     Executing line 38 in func foo
     Executing line 39 in func foo
     Executing line 38 in func foo
     Executing line 39 in func foo
     Executing line 38 in func foo
     Executing line 39 in func foo
     Executing line 38 in func foo
     Executing line 39 in func foo
     Executing line 38 in func foo
     Executing line 40 in func foo
     foo() => 5
    bar() => 5
   baz() => 5
```

Примеры использования `sys.settrace` можно найти в таких модулях как [line_profiler](https://github.com/pyutils/line_profiler/blob/a646bf0f9ab3d15264a1be14d0d4ee6894966f6a/line_profiler/_line_profiler.pyx#L309), [pdb](https://github.com/python/cpython/blob/004f9fd1f22643100aa8163cc9f7bcde7df54973/Lib/bdb.py#L389) или [coverage](https://github.com/nedbat/coveragepy/blob/master/coverage/pytracer.py#L311).

[sys.setprofile](https://docs.python.org/3/library/sys.html#sys.setprofile) позволяет указать функцию, которая будет вызываться виртуальной машиной каждый раз при вызове и завершении работы python (call, return) или C-функций (c_call, c_return):

```python
def profiler(frame: FrameType, event: str, arg: Any) -> Optional[TraceFunction]:
    co = frame.f_code
    func_name = co.co_name
    line_no = frame.f_lineno
    filename = os.path.basename(co.co_filename)
    indent = " " * len(traceback.extract_stack(frame))
    match event:
        case "call":
            print(f"{indent}Calling {func_name}() on line {line_no} of {filename}")
        case "c_call":
            print(f"{indent}Calling C-func {arg}() on line {line_no} of {filename}")
        case "return":
            print(f"{indent}{func_name}() => {arg}")
        case "c_return":
            print(f"{indent}Returning from C-func {arg}()")
    return profiler
```

Примером использования является [PyInstrument]().

Как устроен трейсинг в CPython 3.11:

```c
PyObject* _Py_HOT_FUNCTION
_PyEval_EvalFrameDefault(PyThreadState *tstate, _PyInterpreterFrame *frame, int throwflag)
{
    // ...

    dispatch_opcode:
        switch (opcode) {
        // ...

        TARGET(NOP) {
            DISPATCH();
        }

        TARGET(RETURN_VALUE) {
            // ...
            TRACE_FUNCTION_EXIT();
            // ...
            return retval;
        }

#if USE_COMPUTED_GOTOS
        TARGET_DO_TRACING:
#else
        case DO_TRACING:
#endif
    {
        assert(cframe.use_tracing);
        assert(tstate->tracing == 0);
        if (INSTR_OFFSET() >= frame->f_code->_co_firsttraceable) {
            int instr_prev = _PyInterpreterFrame_LASTI(frame);
            frame->prev_instr = next_instr;
            TRACING_NEXTOPARG();
            if (opcode == RESUME) {
                if (oparg < 2) {
                    CHECK_EVAL_BREAKER();
                }
                /* Call tracing */
                TRACE_FUNCTION_ENTRY();
                DTRACE_FUNCTION_ENTRY();
            }
            else {
                /* line-by-line tracing support */
                if (PyDTrace_LINE_ENABLED()) {
                    maybe_dtrace_line(frame, &tstate->trace_info, instr_prev);
                }

                if (cframe.use_tracing &&
                    tstate->c_tracefunc != NULL && !tstate->tracing) {
                    int err;
                    /* see maybe_call_line_trace()
                    for expository comments */
                    _PyFrame_SetStackPointer(frame, stack_pointer);

                    err = maybe_call_line_trace(tstate->c_tracefunc,
                                                tstate->c_traceobj,
                                                tstate, frame, instr_prev);
                    // Reload possibly changed frame fields:
                    stack_pointer = _PyFrame_GetStackPointer(frame);
                    frame->stacktop = -1;
                    // next_instr is only reloaded if tracing *does not* raise.
                    // This is consistent with the behavior of older Python
                    // versions. If a trace function sets a new f_lineno and
                    // *then* raises, we use the *old* location when searching
                    // for an exception handler, displaying the traceback, and
                    // so on:
                    if (err) {
                        // next_instr wasn't incremented at the start of this
                        // instruction. Increment it before handling the error,
                        // so that it looks the same as a "normal" instruction:
                        next_instr++;
                        goto error;
                    }
                    // Reload next_instr. Don't increment it, though, since
                    // we're going to re-dispatch to the "true" instruction now:
                    next_instr = frame->prev_instr;
                }
            }
        }
        TRACING_NEXTOPARG();
        PRE_DISPATCH_GOTO();
        DISPATCH_GOTO();
    }
```

Дополнительный [комментарий](https://github.com/python/cpython/issues/96636#issuecomment-1241330947) по диспатчингу.

Для многопоточных приложений следует использовать одноименные функции из модуля threading: [threading.settrace](https://docs.python.org/3/library/threading.html#threading.settrace) и [threading.setprofile](https://docs.python.org/3/library/threading.html#threading.setprofile).
Что делать в случае multiprocessing? Для каждого процесса запускать отдельно трассировку, как, например, это происходит в проекте [coverage](https://github.com/nedbat/coveragepy/blob/master/coverage/multiproc.py#L76).

### [sys.monitoring](https://docs.python.org/3/library/sys.monitoring.html) (>= 3.12)

[Mark Shannon](https://github.com/markshannon) - Python core develeoper ([Faster CPython](https://github.com/faster-cpython/ideas)), автор PEPов: [Specializing Adaptive Interpreter](https://peps.python.org/pep-0659/), [Vectorcall: a fast calling protocol for CPython](https://peps.python.org/pep-0590/), [Key-Sharing Dictionary](https://peps.python.org/pep-0412/) и др.:

```python
import inspect
import os
import sys
from pathlib import Path
from types import CodeType, FrameType
from typing import Any

sysmon = sys.monitoring
events = sys.monitoring.events
myid = 2


def callers_frame() -> FrameType:
    return inspect.currentframe().f_back.f_back  # type: ignore[union-attr,return-value]


def py_start(code: CodeType, instruction_offset: int) -> None:
    func_name = code.co_name
    filename = os.path.basename(code.co_filename)
    frame = callers_frame()
    indent = " " * len(traceback.extract_stack(frame))
    print(f"{indent}Calling {func_name}() on line {frame.f_lineno} of {filename}")


def py_return(code: CodeType, instruction_offset: int, retval: Any) -> None:
    func_name = code.co_name
    frame = callers_frame()
    indent = " " * len(traceback.extract_stack(frame))
    print(f"{indent}{func_name}() => {retval}")


def line(code: CodeType, line_number: int) -> None:
    func_name = code.co_name
    frame = callers_frame()
    indent = " " * len(traceback.extract_stack(frame))
    print(f"{indent}Executing line {line_number} in func {func_name}")

# ...

def main() -> None:
    sysmon.use_tool_id(myid, "tracer")
    sysmon.set_events(myid, events.PY_START | events.PY_RETURN | events.LINE)
    sysmon.register_callback(myid, events.PY_START, py_start)
    sysmon.register_callback(myid, events.PY_RETURN, py_return)
    sysmon.register_callback(myid, events.LINE, line)

    # ...

    sysmon.set_events(myid, 0)
    sysmon.free_tool_id(myid)


if __name__ == "__main__":
    main()
```

```
  Executing line 61 in func main
   Calling baz() on line 50 of sysmon_ex.py
   Executing line 51 in func baz
    Calling bar() on line 46 of sysmon_ex.py
    Executing line 47 in func bar
     Calling foo() on line 39 of sysmon_ex.py
     Executing line 40 in func foo
     Executing line 41 in func foo
     Executing line 42 in func foo
     Executing line 41 in func foo
     Executing line 42 in func foo
     Executing line 41 in func foo
     Executing line 42 in func foo
     Executing line 41 in func foo
     Executing line 42 in func foo
     Executing line 41 in func foo
     Executing line 42 in func foo
     Executing line 41 in func foo
     Executing line 43 in func foo
     foo() => 5
    bar() => 5
   baz() => 5
  Executing line 63 in func main
```

[PEP-669](https://peps.python.org/pep-0669/):

> The proposed implementation of this PEP will be built on top of the quickening step of CPython 3.11, as described in PEP 659. Instrumentation works in much the same way as quickening, bytecodes are replaced with instrumented ones as needed.
>
> For example, if the CALL event is turned on, then all call instructions will be replaced with a INSTRUMENTED_CALL instruction.

[CPython 3.13](https://github.com/python/cpython/blob/c57ef49337c6720a76c5f2203d07d6d6d64f421f/Python/generated_cases.c.h#L3210):
```c
        TARGET(INSTRUMENTED_CALL) {
            _Py_CODEUNIT *this_instr = frame->instr_ptr = next_instr;
            (void)this_instr;
            next_instr += 4;
            INSTRUCTION_STATS(INSTRUMENTED_CALL);
            /* Skip 3 cache entries */
            int is_meth = PEEK(oparg + 1) != NULL;
            int total_args = oparg + is_meth;
            PyObject *function = PEEK(oparg + 2);
            PyObject *arg = total_args == 0 ?
            &_PyInstrumentation_MISSING : PEEK(total_args);
            int err = _Py_call_instrumentation_2args(
                tstate, PY_MONITORING_EVENT_CALL,
                frame, this_instr, function, arg);
            if (err) goto error;
            PAUSE_ADAPTIVE_COUNTER(this_instr[1].counter);
            GO_TO_INSTRUCTION(CALL);
        }
```

Примером использования является [coverage](https://github.com/nedbat/coveragepy/blob/master/coverage/sysmon.py#L226).

## Профилирование основанное на сэмплировании

Пример:

```python
import atexit
import signal
import traceback
from collections import defaultdict
from types import FrameType
from typing import DefaultDict

INTERVAL = 0.005
stats: DefaultDict[str, int] = defaultdict(int)


def on_sample(signum: int, frame: FrameType | None) -> None:
    stack = traceback.extract_stack(frame)
    formatted_stack = ";".join(line.line or "" for line in stack)
    stats[formatted_stack] += 1


def start_sampling(interval: float = INTERVAL) -> None:
    signal.signal(signal.SIGPROF, on_sample)
    signal.setitimer(signal.ITIMER_PROF, interval, interval)
    atexit.register(lambda: signal.setitimer(signal.ITIMER_PROF, 0))


def print_stats() -> None:
    stack_count = [f"{stack} {count}" for stack, count in stats.items()]
    print("\n".join(stack_count))


def func() -> None:
    x = 1
    for _ in range(10_000_000):
        x = x**3


def main() -> None:
    start_sampling()
    func()
    print_stats()


if __name__ == "__main__":
    main()
```

Примерами сэмплирующих профилировщиков являются [PyInstrument](https://github.com/joerick/pyinstrument/tree/main) и [Scalene](https://github.com/plasma-umass/scalene/tree/master). В [PyInstrument](https://github.com/joerick/pyinstrument/tree/main) механизм сэмплирования построен на вызовах метода [sys.setprofile](https://github.com/joerick/pyinstrument/blob/1ca09623a71caa45d1bb39de216987665c019ff1/pyinstrument/low_level/stat_profile_python.py#L96).


## Удаленное профилирование

[libunwind-examples](https://github.com/daniel-thompson/libunwind-examples):

```c
#include <sys/ptrace.h>
#include <stdio.h>
#include <stdlib.h>

#include <libunwind-ptrace.h>

#include "die.h"

int main(int argc, char **argv)
{
	if (argc != 2)
		die("USAGE: unwind-pid <pid>\n");

	unw_addr_space_t as = unw_create_addr_space(&_UPT_accessors, 0);

	pid_t pid = atoi(argv[1]);
	if (ptrace(PTRACE_ATTACH, pid, 0, 0) != 0)
		die("ERROR: cannot attach to %d\n", pid);

	void *context = _UPT_create(pid);
	unw_cursor_t cursor;
	if (unw_init_remote(&cursor, as, context) != 0)
		die("ERROR: cannot initialize cursor for remote unwinding\n");

	do {
		unw_word_t offset, pc;
		char sym[4096];
		if (unw_get_reg(&cursor, UNW_REG_IP, &pc))
			die("ERROR: cannot read program counter\n");

		printf("0x%lx: ", pc);

		if (unw_get_proc_name(&cursor, sym, sizeof(sym), &offset) == 0)
			printf("(%s+0x%lx)\n", sym, offset);
		else
			printf("-- no symbol name found\n");
	} while (unw_step(&cursor) > 0);

	_UPT_destroy(context);
	(void) ptrace(PTRACE_DETACH, pid, 0, 0);

	return 0;
}
```

```
$ ./unwind-pid 2104394 
0x710d39e18980: (__nss_passwd_lookup+0x25a30)
0x710d3a46bde6: (PyByteArray_Concat+0xd6)
0x710d3b7a398b: (decode_bytestring+0x8b)
0x710d3b7a47a5: (decode.constprop.1+0xe5)
0x710d3b7a40b1: (decode_semantic+0xf1)
0x710d3b7a4775: (decode.constprop.1+0xb5)
0x710d3b7a54e4: (decode_map+0x154)
0x710d3b7a602d: (CBORDecoder_decode+0x12d)
0x710d3b7aee88: (CBOR2_loads+0x1a8)
0x710d3a37a199: (cfunction_call+0x39)
0x710d3a3eaefe: (_PyEval_EvalFrameDefault+0x35ace)
0x710d3a4df5ed: (_PyEval_Vector+0x1dd)
0x710d3a4df3cf: (PyEval_EvalCode+0x11f)
0x710d3a512d10: (run_mod+0x90)
0x710d3a284af2: (pyrun_file+0x82)
0x710d3a284610: (_PyRun_SimpleFileObject+0x110)
0x710d3a283fec: (_PyRun_AnyFileObject+0xac)
0x710d3a28f159: (pymain_run_file_obj+0xd9)
0x710d3a28ec80: (pymain_run_file+0x50)
0x710d3a51fe31: (Py_RunMain+0x681)
0x710d3a28f4f7: (Py_BytesMain+0x27)
0x710d39ce009b: (__libc_start_main+0xeb)
0x55591ba1208e: (_start+0x29)
```

Примером использования является py-spy (автор [Ben Frederickson](https://github.com/benfred)).

## Профилирование numba

На текущий момент [нет](https://github.com/numba/numba/issues/5028) профилировщиков для numba 🤬, кроме сэмплирующего профилировщика [Profila](https://github.com/pythonspeed/profila). Который работает следующим образом:
- запускается отдельный процесс с отладчиком GDB, с которым общение происходит с помощью интерфейса GDB/MI (версии 3).
- взаимодействие с MI осуществляется в асинхронном режиме (`-gdb-set mi-async`)
- запускается python-процесс (из под отладчика)
- производится периодическое сэмплирование процесса, для этого процесс прерывается (`-exec-interrupt`) и затем получаем текущий стек ([`-stack-list-frames`](https://www.sourceware.org/gdb/current/onlinedocs/gdb.html/GDB_002fMI-Stack-Manipulation.html)), которым обновляется статитика по сэмплируемому процессу, наконец процесс возобновляет работу.


```sh
uv run python -m profila annotate -- dtwimpls/nbdtw.py
```

```sh
**Total samples:** 188 (46.8% non-Numba samples, 6.9% bad samples)

.../experimets/profiling/dtwimpls/nbdtw.py (lines 17 to 104):

  3.2% |     cost: Array2D[np.float32] = np.zeros((len(x), len(y)), dtype=np.float32)
       |     for i in range(len(x)):
  0.5% |         for j in range(len(y)):
  3.2% |             cost[i, j] = (x[i] - y[j]) ** 2
  3.2% |     return np.sqrt(cost)
       | 
       | 
       | @njit("f4[:,:](f4[:,:])", cache=True)
       | def accumulated_cost_matrix(cost: Array2D[np.float32]) -> Array2D[np.float32]:
       |     n, m = cost.shape
       |     d = np.zeros_like(cost, dtype=np.float32)
       |     d[0, 0] = cost[0, 0]
       |     for i in range(1, n):
       |         d[i, 0] = d[i - 1, 0] + cost[i, 0]
       |     for i in range(1, m):
       |         d[0, i] = d[0, i - 1] + cost[0, i]
       |     for i in range(1, n):
  1.6% |         for j in range(1, m):
 26.1% |             d[i, j] = min(d[i - 1, j], d[i, j - 1], d[i - 1, j - 1]) + cost[i, j]
       |     return d
      ...
       | 
       | @njit(cache=True)
       | def main() -> None:
       |     x, y = generate_signals(10000)
       |     cost = cost_matrix(x, y)
       |     d = accumulated_cost_matrix(cost)
       |     path = warping_path(d)
  1.1% |     return path

../numba/np/arrayobj.py (lines 4448 to 4448):

  7.4% |         _zero_fill_array_method(self)
```
