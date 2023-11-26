import random
import unittest
from cProfile import Profile
from pstats import SortKey, Stats

from lilvali import validate, validator
from lilvali.errors import *


def prof_tests_main():
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir="path_to_your_tests_directory"
    )  # Adjust the path as needed
    runner = unittest.TextTestRunner()
    runner.run(suite)


def prof_main():
    @validator(base=int)
    def has_c_or_int(arg):
        return True if "c" in arg else False

    @validate
    def f[T: (int, float)](x: has_c_or_int, y: T) -> int | float:
        if isinstance(x, str):
            x = int(x.split("=")[1])
        return x + y if random.random() < 0.5 else x - y

    S = 0
    for i in range(100000):
        S = f(
            S if random.random() < 0.5 else f"c={S}", 1 if random.random() < 0.5 else -1
        )


def main():
    profiler = Profile()

    profiler.runcall(prof_main)
    profiler.create_stats()
    stats = Stats(profiler)

    stats.strip_dirs()
    stats.sort_stats(SortKey.CALLS)
    stats.print_stats()
    stats.dump_stats("lilvali_profiling.prof")


if __name__ == "__main__":
    main()
