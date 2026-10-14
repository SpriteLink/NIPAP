"""Prefix AVP search parsing and SQL expansion, without a database."""

import unittest
from nipap.backend import Nipap
from nipap.errors import NipapInputError, NipapNoSuchOperatorError
from nipap.smart_parsing import PrefixSmartParser, VrfSmartParser


class AvpSearchTest(unittest.TestCase):
    def setUp(self):
        self.parser = PrefixSmartParser()
        self.backend = Nipap.__new__(Nipap)

    def test_key_only(self):
        success, query = self.parser.parse("avp.site")
        self.assertTrue(success)
        self.assertEqual(query["operator"], "avp_exists")
        sql, values = self.backend._expand_prefix_query(query, "p1")
        self.assertEqual(sql.strip(), "(p1.avps ? %s)")
        self.assertEqual(values, ["site"])

    def test_values_and_quoted_spaces(self):
        for text, value in [
            ("avp.site=stockholm", "stockholm"),
            ('avp.site="Stockholm office"', "Stockholm office"),
            ('avp.site=""', ""),
        ]:
            with self.subTest(text=text):
                success, query = self.parser.parse(text)
                self.assertTrue(success)
                sql, values = self.backend._expand_prefix_query(query)
                self.assertEqual(sql.strip(), "(inp.avps -> %s) = %s")
                self.assertEqual(values, ["site", value])

    def test_not_equals_and_boolean_combinations(self):
        success, query = self.parser.parse(
            "avp.site!=stockholm AND avp.owner OR avp.site=uppsala"
        )
        self.assertTrue(success)
        sql, values = self.backend._expand_prefix_query(query)
        self.assertIn("AND", sql)
        self.assertIn("OR", sql)
        self.assertIn("!=", sql)
        self.assertEqual(
            values,
            ["site", "stockholm", "owner", "site", "uppsala"],
        )

    def test_key_and_value_are_bound_parameters(self):
        key = "site') OR TRUE --"
        value = "x' OR TRUE --"
        sql, values = self.backend._expand_prefix_query(
            {"operator": "equals", "val1": "avp." + key, "val2": value}
        )
        self.assertNotIn(key, sql)
        self.assertNotIn(value, sql)
        self.assertEqual(values, [key, value])

    def test_invalid_operators_and_empty_keys(self):
        for text in ("avp.=x", "avp.site>stockholm", "avp.site~stockholm"):
            with self.subTest(text=text):
                self.assertFalse(self.parser.parse(text)[0])
        for operator, key, value in [
            ("=", "", "x"),
            ("=", "site", None),
            ("avp_exists", "site", False),
        ]:
            with self.assertRaises(NipapInputError):
                self.backend._expand_prefix_query(
                    {"operator": operator, "val1": "avp." + key, "val2": value}
                )
        with self.assertRaises(NipapNoSuchOperatorError):
            self.backend._expand_prefix_query(
                {"operator": "contains", "val1": "avp.site", "val2": "x"}
            )

    def test_quoted_key_is_free_text_and_other_objects_unchanged(self):
        success, query = self.parser.parse('"avp.site"')
        self.assertTrue(success)
        self.assertNotEqual(query["operator"], "avp_exists")
        self.assertFalse(VrfSmartParser().parse("avp.site=stockholm")[0])


if __name__ == "__main__":
    unittest.main()
