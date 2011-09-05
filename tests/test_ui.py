import unittest

from cartman import ui


class UiUnitTest(unittest.TestCase):

    def test_underline_empty(self):
        self.assertEquals(ui.underline(""), "")

    def test_underline_one(self):
        self.assertEquals(ui.underline("a"), "-")

    def test_underline_with_space(self):
        self.assertEquals(ui.underline("a bcd"), "-----")

    def test_title_empty(self):
        self.assertEquals(ui.title(""), "")

    def test_title_one(self):
        self.assertEquals(ui.title("a"), "a\n-")

    def test_title_with_space(self):
        self.assertEquals(ui.title("a bcd"), "a bcd\n-----")
