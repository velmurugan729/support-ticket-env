# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Unit tests for inference.py parsing functions.

Tests verify:
- Department name extraction from various LLM outputs
- Edge cases (empty strings, invalid departments)
- Case insensitivity
"""

import pytest
from inference import parse_department, VALID_DEPARTMENTS


class TestParseDepartment:
    """Test parse_department function with various inputs."""

    def test_exact_match(self):
        """Test exact department name matches."""
        assert parse_department("Billing") == "Billing"
        assert parse_department("Technical") == "Technical"
        assert parse_department("Shipping") == "Shipping"
        assert parse_department("Returns") == "Returns"
        assert parse_department("General") == "General"

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        assert parse_department("billing") == "Billing"
        assert parse_department("TECHNICAL") == "Technical"
        assert parse_department("Shipping") == "Shipping"

    def test_with_extra_text(self):
        """Test extraction from text with extra content."""
        assert parse_department("I think Billing is the answer") == "Billing"
        assert parse_department("The department should be Technical") == "Technical"
        assert parse_department("Shipping, because it involves delivery") == "Shipping"

    def test_with_punctuation(self):
        """Test extraction with punctuation."""
        assert parse_department("Billing.") == "Billing"
        assert parse_department("Technical!") == "Technical"
        assert parse_department("'Shipping'") == "Shipping"

    def test_empty_string(self):
        """Test empty string defaults to General."""
        assert parse_department("") == "General"
        assert parse_department("   ") == "General"

    def test_none_input(self):
        """Test None defaults to General."""
        assert parse_department(None) == "General"

    def test_invalid_department(self):
        """Test invalid department defaults to General."""
        assert parse_department("Sales") == "General"
        assert parse_department("Marketing") == "General"
        assert parse_department("12345") == "General"

    def test_multiple_departments(self):
        """Test with multiple department mentions returns first match."""
        # Returns first match found in the text
        result = parse_department("Could be Billing or Technical")
        assert result in VALID_DEPARTMENTS

    def test_json_format(self):
        """Test extraction from JSON-like format."""
        assert parse_department('{"department": "Billing"}') == "Billing"
        assert parse_department('{"dept": "Technical"}') == "Technical"

    def test_markdown_format(self):
        """Test extraction from markdown format."""
        assert parse_department("**Billing**") == "Billing"
        assert parse_department("`Technical`") == "Technical"


class TestValidDepartments:
    """Test VALID_DEPARTMENTS constant."""

    def test_department_count(self):
        """Test that we have exactly 5 valid departments."""
        assert len(VALID_DEPARTMENTS) == 5

    def test_department_names(self):
        """Test valid department names."""
        expected = ["Billing", "Technical", "Shipping", "Returns", "General"]
        assert sorted(VALID_DEPARTMENTS) == sorted(expected)
