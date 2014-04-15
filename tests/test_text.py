import unittest

from cartman import text, exceptions


class TextUnitTest(unittest.TestCase):

    def test_extract_statuses_nothing(self):
        raw_html = ""
        self.assertEquals(text.extract_statuses(raw_html), [])

    def test_extract_statuses_one(self):
        raw_html = """dewqwdqw eldqkwkwjd
        delwqdew q
        <input type="radio" stuff name="action" value="my_action" />
        dewklqjd lewkdjqwe dlkjhew
        """
        self.assertEquals(text.extract_statuses(raw_html), ["my_action"])

    def test_extract_statuses_multiple(self):
        raw_html = """dewqwdqw eldqkwkwjd
        delwqdew q
        <input type="radio" stuff name="action" value="my_action" />
        <input type="radio" stuff name="action" value="something" />
        <input type="radio" stuff name="action" value="else" />
        dewklqjd lewkdjqwe dlkjhew
        """
        self.assertEquals(text.extract_statuses(raw_html), [
            "my_action",
            "something",
            "else",
        ])

    def test_extract_timestamps_v0_none(self):
        raw_html = """dewqwlkjhew"""
        self.assertRaises(exceptions.FatalError, text.extract_timestamps_v0,
                          raw_html)

    def test_extract_timestamps_v1_none(self):
        raw_html = """dewqwlkjhew"""
        self.assertRaises(exceptions.FatalError, text.extract_timestamps_v1,
                          raw_html)

    def test_extract_timestamps_v0_one(self):
        raw_html = """dewqwlkjhew
        <input name="ts" value="123123" /> stuff"""
        timestamps = text.extract_timestamps_v0(raw_html)
        self.assertEquals(timestamps["ts"], "123123")

    def test_extract_timestamps_multiple(self):
        raw_html = """dewqwlkjhew
        <input name="ts" value="654321" /> stuff
        <input name="ts" value="123123" /> stuff"""
        timestamps = text.extract_timestamps_v0(raw_html)
        self.assertEquals(timestamps["ts"], "654321")

    def test_validate_id_None(self):
        self.assertRaises(exceptions.InvalidParameter, text.validate_id, None)

    def test_validate_id_str_bad_chr(self):
        self.assertRaises(exceptions.InvalidParameter, text.validate_id, "qwe")

    def test_validate_id_str_bad_flt(self):
        self.assertRaises(exceptions.InvalidParameter, text.validate_id, "1.2")

    def test_validate_id_str_good(self):
        self.assertEquals(text.validate_id("12"), 12)

    def test_fuzzy_find_no_options(self):
        self.assertEquals(text.fuzzy_find("meh", []), None)

    def test_fuzzy_find_bad_option(self):
        self.assertEquals(text.fuzzy_find("meh", ["bad"]), None)

    def test_fuzzy_find_same_option(self):
        self.assertEquals(text.fuzzy_find("meh", ["meh"]), "meh")

    def test_fuzzy_find_one_letter_diff(self):
        self.assertEquals(text.fuzzy_find("meh", ["meg"]), "meg")

    def test_fuzzy_find_two_one_match(self):
        self.assertEquals(text.fuzzy_find("meh", ["meg", "meh"]), "meh")

    def test_fuzzy_find_two_one_match(self):
        self.assertEquals(text.fuzzy_find("meh", ["megl", "mehl"]), "mehl")

    def test_fuzzy_find_two_one_match_re(self):
        self.assertEquals(text.fuzzy_find("meh", ["meh stuff", "mih stuff"]),
                          "meh stuff")

    def test_extract_properties_none(self):
        raw_html = """hemene, hemene"""
        self.assertEquals(text.extract_properties(raw_html), {})

    def test_extract_properties_found(self):
        raw_html = """hemene, hemene
        var properties={ "another": "one", "bites": ["the", "dust"] };
        var modes={};
        """
        self.assertEquals(text.extract_properties(raw_html), {
            "another": "one",
            "bites": [ "the", "dust" ]
        })

    def test_extract_properties_found_with_semicolon(self):
        raw_html = """hemene, hemene
        var properties={ "another": "one", "bites": ["the", "d;ust"] };
        var modes={};
        </script>Other; semi-colons; to make sure; we don't break.
        """
        self.assertEquals(text.extract_properties(raw_html), {
            "another": "one",
            "bites": [ "the", "d;ust" ]
        })
