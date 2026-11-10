import unittest
class Checks(unittest.TestCase):
 def test_pass(self):
  for n in [1,2]:
   with self.subTest(n=n):self.assertGreater(n,0)
 def test_fail(self):
  for n in [1,2]:
   with self.subTest(n=n):self.assertEqual(n,1)
