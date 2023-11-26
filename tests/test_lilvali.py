import unittest, logging

from lilvali.validate import validate
from lilvali.errors import *


log = logging.getLogger(__name__)


class TestLilvali(unittest.TestCase):
    def test_modes(self):
        @validate(config={"performance": True})
        def performance_func[T](a: list[T]) -> T:
            return a[0]

        self.assertEqual(performance_func([1, 2, 3]), 1)
        with self.assertRaises(ValidationError):
            performance_func(5)

        # should work because performance mode:
        self.assertEqual(performance_func([1, 2, 3.0]), 1)

        with self.assertRaises(TypeError):

            @validate(config="bad config")
            def bad_config_func(a: int) -> int:  # pragma: no cover
                return a

        # tuple check is also disabled with performance mode
        @validate(config={"performance": True})
        def tuple_func(a: tuple[int, str]) -> str:
            return a[1]

        self.assertEqual(tuple_func((1, "a")), "a")
        with self.assertRaises(ValidationError):
            tuple_func((1, 2))

        @validate(config={"performance": True})
        def dict_func(a: dict[int, str]) -> str:
            return a[1]

        self.assertEqual(dict_func({1: "a"}), "a")
        with self.assertRaises(ValidationError):
            dict_func({1: 2})
