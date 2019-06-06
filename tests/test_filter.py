import unittest
from postgrest.filters import Filter

class TestFilters(unittest.TestCase):
    def assertEncoding(self, value, expected, top_level=False):
        self.assertEqual(Filter(value).prepare_query(top_level), expected)

    def test_encoding(self):
        self.assertEncoding(None, "null")
        self.assertEncoding(False, "false")
        self.assertEncoding(True, "true")
        self.assertEncoding("foo", "foo", True)
        self.assertEncoding("foo", "%22foo%22")
        self.assertEncoding('with"double quote', 'with%22double%20quote', True)
        self.assertEncoding('with"double quote', '%22with%5C%22double%20quote%22')
        self.assertEncoding('double quote at end"', 'double%20quote%20at%20end%22', True)
        self.assertEncoding('double quote at end"', '%22double%20quote%20at%20end%5C%22%22')
        self.assertEncoding('slash at end\\', 'slash%20at%20end%5C', True)
        self.assertEncoding('slash at end\\', '%22slash%20at%20end%5C%5C%22')

if __name__ == '__main__':
    unittest.main()
