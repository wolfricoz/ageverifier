import random
import unittest

from databases.transactions.StaffTransactions import StaffDbTransactions
from databases.current import create_bot_database, drop_bot_database


class TestStaffDbTransactions(unittest.TestCase):

    def setUp(self):
        create_bot_database()
        self.st = StaffDbTransactions()
        self.uid = random.randint(2**6, 2**8)

    def tearDown(self):
        drop_bot_database()

    def test_add_and_get_staff(self):
        added = self.st.add(self.uid, "Admin")
        self.assertIsNotNone(added)
        self.assertEqual(added.uid, self.uid)
        self.assertEqual(added.role, "admin")  # role stored as lowercase

        fetched = self.st.get(self.uid)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.uid, self.uid)

    def test_add_duplicate_returns_none(self):
        self.st.add(self.uid, "Admin")
        second_add = self.st.add(self.uid, "Moderator")
        self.assertIsNone(second_add)  # Should refuse duplicate add

    def test_get_all_returns_list_of_staff(self):
        self.st.add(self.uid, "Admin")
        uid2 = random.randint(2**6, 2**8)
        self.st.add(uid2, "Moderator")

        all_staff = self.st.get_all()
        self.assertTrue(any(staff.uid == self.uid for staff in all_staff))
        self.assertTrue(any(staff.uid == uid2 for staff in all_staff))
        self.assertTrue(all(hasattr(staff, "uid") and hasattr(staff, "role") for staff in all_staff))

    def test_delete_existing_staff(self):
        self.st.add(self.uid, "Admin")
        result = self.st.delete(self.uid)
        self.assertTrue(result)

        # Confirm deletion
        self.assertIsNone(self.st.get(self.uid))

    def test_delete_nonexistent_returns_false(self):
        result = self.st.delete(9999999999)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
