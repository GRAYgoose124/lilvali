""" unittest to check validation of NewTypes, which should just be the same as the basic types they are based on."""
import logging
import os
import unittest
from typing import NewType
from lilvali import validate, validator, ValidationError


class TestValidateNewTypes(unittest.TestCase):
    def test_validate_newtype(self):
        """Test that validation of newtypes is the same as the base type."""

        @validate
        def validate_int(value: int):
            return value > 0

        NT = NewType("Int", int)

        @validate
        def validate_newtype(value: NT):
            return value > 0

        self.assertEqual(validate_int(1), validate_newtype(1))

        with self.assertRaises(ValidationError):
            validate_newtype(1.0)
