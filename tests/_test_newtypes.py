import unittest
from typing import NewType
from lilvali import validate, ValidationError

# Define NewTypes
UserId = NewType("UserId", int)
AdminId = NewType("AdminId", UserId)


class TestNewTypeValidation(unittest.TestCase):
    def test_new_type_validation(self):
        @validate
        def get_user_name(user_id: UserId) -> str:
            return f"User{user_id}"

        valid_user_id = UserId(123)
        self.assertEqual(get_user_name(valid_user_id), "User123")

        # Even though AdminId is technically an int, it should not be interchangeable with UserId
        valid_admin_id = AdminId(456)
        with self.assertRaises(ValidationError):
            get_user_name(valid_admin_id)

        # Directly passing an int should fail validation
        with self.assertRaises(ValidationError):
            get_user_name(789)

    def test_new_type_derived_validation(self):
        @validate
        def get_admin_name(admin_id: AdminId) -> str:
            return f"Admin{admin_id}"

        valid_admin_id = AdminId(456)
        self.assertEqual(get_admin_name(valid_admin_id), "Admin456")

        # Passing a UserId to an AdminId should fail, even though AdminId is derived from UserId
        valid_user_id = UserId(123)
        with self.assertRaises(ValidationError):
            get_admin_name(valid_user_id)

        # Directly passing an int should fail validation
        with self.assertRaises(ValidationError):
            get_admin_name(789)

    def test_new_type_in_complex_structures(self):
        @validate
        def get_user_info(user_ids: list[UserId]) -> str:
            return ", ".join(f"User{uid}" for uid in user_ids)

        valid_user_ids = [UserId(123), UserId(456)]
        self.assertEqual(get_user_info(valid_user_ids), "User123, User456")

        # List containing an int instead of UserId should fail
        with self.assertRaises(ValidationError):
            get_user_info([123, UserId(456)])

        # List containing an AdminId should fail even though it's based on UserId
        valid_admin_id = AdminId(789)
        with self.assertRaises(ValidationError):
            get_user_info([valid_user_id, valid_admin_id])


if __name__ == "__main__":
    unittest.main()
