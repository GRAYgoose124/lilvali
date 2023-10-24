from cProfile import Profile
from pstats import SortKey, Stats
import random

from lilvali import validate, validator, ValidationError


def prof_main():
    @validator(base=int)
    def has_c_or_int(arg):
        return True if "c" in arg else False    
    
    @validate
    def f[T: (int, float)](x: has_c_or_int, y: T) -> int | float:
        return x + y if random.random() < 0.5 else x - y
    
    S=0
    for i in range(100000):
        S = f(S, 1 if random.random() < 0.5 else -1)


def main():
    profiler = Profile()

    profiler.runcall(prof_main)
    profiler.create_stats()
    stats = Stats(profiler)

    stats.strip_dirs()
    stats.sort_stats(SortKey.CALLS)
    stats.print_stats()
    stats.dump_stats('lilvali_profiling.prof')


if __name__ == '__main__':
    main()
