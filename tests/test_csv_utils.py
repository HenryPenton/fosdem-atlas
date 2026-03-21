"""Unit tests for the shared CSV sanitisation utility."""

import pytest

from src.adapters.csv_utils import sanitise_csv_value


class TestSanitiseCsvValue:
    @pytest.mark.parametrize("trigger", ["=SUM(1+1)", "+cmd", "-cmd", "@SUM"])
    def test_formula_trigger_characters_are_prefixed(self, trigger: str) -> None:
        result = sanitise_csv_value(trigger)
        assert isinstance(result, str)
        assert result.startswith("\t")
        assert result[1:] == trigger

    def test_html_tags_are_stripped(self) -> None:
        result = sanitise_csv_value("<em>bold</em> and <a href='x'>link</a>")
        assert result == "bold and link"

    def test_html_stripped_before_formula_check(self) -> None:
        # A value whose formula character only appears after HTML is stripped
        # should still be prefixed correctly.
        result = sanitise_csv_value("<b>=evil</b>")
        assert isinstance(result, str)
        assert result == "\t=evil"

    def test_plain_string_unchanged(self) -> None:
        assert sanitise_csv_value("hello world") == "hello world"

    def test_integer_unchanged(self) -> None:
        assert sanitise_csv_value(42) == 42

    def test_float_unchanged(self) -> None:
        assert sanitise_csv_value(3.14) == 3.14

    def test_empty_string_unchanged(self) -> None:
        assert sanitise_csv_value("") == ""
